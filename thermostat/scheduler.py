import utime # pylint: disable=import-error
import json

class Setpoint:
    def __init__(self, value, component=None):
        self.component = component
        self.set(value)
    
    def set(self, value):
        self.value = float(value)
        if self.component:
            self.component.set(int(10*self.value))

    def updateFromDisplay(self):
        self.value = float(self.component.get())/10


    def __str__(self):
        return "{:.1f}".format(self.value)
    
    def __repr__(self):
        return "{:.1f} degC".format(self.value)

class Scheduler:
    def __init__(self, schedule_path, t_high_comp, t_med_comp, t_low_comp, mode=None):
        self.schedule_path = schedule_path
        self.components = {'t_high': t_high_comp, 't_med':t_med_comp, 't_low': t_low_comp}
        if mode:
            self.load(mode)
    
    def updateSetpoints(self):
        utime.sleep_ms(100)
        for setpoint in [self.t_high, self.t_med, self.t_low]:
            setpoint.updateFromDisplay()

    def load(self, mode):
        #FIXME: handle case where file is missing or it is corrupted
        self.mode = mode
        self.override = False
        with open(self.schedule_path, 'r') as fp:
            schedule_struct = json.load(fp)
        data = schedule_struct[mode]
        if data:
            self.t_low = Setpoint(data['temperature']['low'], self.components['t_low'])
            self.t_med = Setpoint(data['temperature']['medium'], self.components['t_med'])
            self.t_high = Setpoint(data['temperature']['high'], self.components['t_high'])

            self.schedule_working_days = {}
            for time, temp in data['timing']['working'].items():
                time = int(time)
                if time < 0 or time >=1440:
                    pass
                self.schedule_working_days[time] = self.t_low if temp=="low" else (self.t_high if temp=="high" else self.t_med)
            if len(self.schedule_working_days)==0:
                self.schedule_working_days[0] = self.t_low
            
            self.schedule_holidays = {}
            for time, temp in data['timing']['holiday'].items():
                time = int(time)
                if time < 0 or time >=1440:
                    pass
                self.schedule_holidays[time] = self.t_low if temp=="low" else (self.t_high if temp=="high" else self.t_med)
            if len(self.schedule_holidays)==0:
                self.schedule_holidays[0] = self.t_low
        else:
            self.t_low = Setpoint(16)
            self.t_med = Setpoint(18)
            self.t_high = Setpoint(20)
            self.schedule_working_days = {0:self.t_low}
            self.schedule_holidays = {0:self.t_low}

        self.is_yesterday_working = True
        self.is_today_working = True
        self.is_tomorrow_working = True

    def isModeChanged(self, new_mode):
        return new_mode != self.mode

    def getSetpoint(self, time=None):
        if time is None:
            time = self.__getTime()
        yesterday_program = self.schedule_working_days if self.is_today_working else self.schedule_holidays
        today_program = self.schedule_working_days if self.is_today_working else self.schedule_holidays
        tomorrow_program = self.schedule_working_days if self.is_tomorrow_working else self.schedule_holidays
        
        sps = list(filter(lambda t:t<=time, today_program.keys()))
        if len(sps)==0:
            current_temperature = yesterday_program[max(yesterday_program.keys())]
            next_time = min(today_program.keys())
            next_temperature = today_program[next_time]
        else:
            current_temperature = today_program[max(sps)]
            time = list(filter(lambda t:t>time, today_program.keys()))
            if len(time)==0:
                next_time = min(tomorrow_program.keys())
                next_temperature = tomorrow_program[next_time]
            else:
                next_time = min(time)
                next_temperature = today_program[next_time]
        return current_temperature, next_time, next_temperature

    def displayScheduling(self, holiday=False):
        schedule = self.schedule_holidays if holiday else self.schedule_working_days
        schedule_time = list(schedule.keys()).sort()
        data = [schedule[schedule_time[-1]]] * 24
        for t in schedule_time:
            pass

    def moveToNextDay(self, is_tomorrow_working=True):
        self.is_yesterday_working = self.is_today_working
        self.is_today_working = self.is_tomorrow_working
        self.is_tomorrow_working = is_tomorrow_working
    
    def overrideToday(self, is_working):
        self.is_today_working = is_working

    def overrideTomorrow(self, is_working):
        self.is_tomorrow_working = is_working

    def dump(self):
        data = {
            'temperature':{
                'low': self.t_low.value,
                'medium': self.t_med.value,
                'high': self.t_high.value
            },
            'timing':{
                'working':{},
                'holiday':{}
            }
        }
        for time, temp in self.schedule_working_days.items():
            data['timing']['working'][str(time)] = "low" if temp==self.t_low else ("high" if temp==self.t_high else "medium")

        for time, temp in self.schedule_holidays.items():
            data['timing']['holiday'][str(time)] = "low" if temp==self.t_low else ("high" if temp==self.t_high else "medium")
        return data

    @classmethod
    def getTimeString(cls, time):
        return "{:02d}:{:02d}".format(int(time/60), time%60)

    def __getTime(self):
        (_,_,_,hr, mn, _,_,_) = utime.localtime()
        return hr * 60 + mn
