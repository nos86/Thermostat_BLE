import utime # pylint: disable=import-error
import json
from bluetooth_interface import BluetoothManager

from .thermometer import xiaomi
from .core import MultiSensorLogic
from .scheduler import Scheduler

class xiaomiOnNextion(xiaomi):
    def __init__(self, mac, t_comp, h_comp, b_comp, online_comp):
        super().__init__(mac)
        self.t_comp = t_comp
        self.h_comp = h_comp
        self.b_comp = b_comp
        self.online_comp = online_comp
        self.online_comp.set(1)

    def decode_advertising(self, adv_data):
        super().decode_advertising(adv_data)
        self.t_comp.set(int(self.temperature * 10) if self.temperature else 0)
        self.h_comp.set(int(self.humidity * 10)if self.humidity else 0)
        self.b_comp.set(self.battery if self.battery else 0)

class Thermostat:
    BEDROOM_SENSOR_NO = 0
    BATHROOM_SENSOR_NO = 1
    def __init__(self, nextion_driver, schedule_path ="/programs.json", bedroom_mac = b'Le\xa8\xdd\xd4L', bathroom_mac = b'X-41\xac\x9f'):
        self.nextion = nextion_driver
        self.label = {
            "date" : self.nextion.getComponentByPath("overview.date"),
            "time" : self.nextion.getComponentByPath("overview.time"),
            "target" : self.nextion.getComponentByPath("overview.target"),
            "endtime" : self.nextion.getComponentByPath("overview.endtime"),
            "override" : self.nextion.getComponentByPath("overview.override"),
            "outside_temperature": self.nextion.getComponentByPath("overview.out_temp"),
            "outside_humidity": self.nextion.getComponentByPath("overview.out_hum"),
            "heater": self.nextion.getComponentByPath("overview.heater"),
            "program": self.nextion.getComponentByPath("overview.program")
        }
        #Variable initialization
        self.__override_temperature = None
        self.__override_next_time = None
        self.__current_setpoint = None
        self.__next_schedule_time = None
        self.__last_date_update = 0
        self.schedule = {}
        with open(schedule_path, 'r') as fp:
            temp = json.load(fp)
        for mode in ['home', 'away', 'vacation']:
            self.schedule[mode] = Scheduler(mode, temp[mode]) #FIXME: setup working day
            self.nextion.register_listener("overview.prg_{}".format(mode), lambda x, mode=mode: self.set_mode(mode))
        self.logic = MultiSensorLogic(self.__set_relay_callback, 0.5, minTimeOn=0, numberOfSensors=2)

        self.bluetooth = BluetoothManager()
        
        self.bedroom  = xiaomiOnNextion(bedroom_mac
                                    , self.nextion.getComponentByPath("bedroom.temperature")
                                    , self.nextion.getComponentByPath("bedroom.humidity")
                                    , self.nextion.getComponentByPath("bedroom.battery")
                                    , self.nextion.getComponentByPath("bedroom.online"))
        self.bluetooth.addDevice(self.bedroom.mac, lambda adv, rssi: self.bt_irq(self.bedroom, adv, rssi))

        self.bathroom = xiaomiOnNextion(bathroom_mac
                                    , self.nextion.getComponentByPath("bathroom.temperature")
                                    , self.nextion.getComponentByPath("bathroom.humidity")
                                    , self.nextion.getComponentByPath("bathroom.battery")
                                    , self.nextion.getComponentByPath("bathroom.online")) 
        self.bluetooth.addDevice(self.bathroom.mac, lambda adv, rssi: self.bt_irq(self.bathroom, adv, rssi))

        #self.timer = machine.Timer(0).init(period=1000, mode=machine.Timer.PERIODIC, self.timer_irq))

        self.set_mode('home')
        self.bluetooth.start()

    def __set_relay_callback(self, value):
        self.label['heater'].set(1 if value else 0)

    def set_mode(self, mode):
        self.__current_mode = mode
        self.label['program'].set(0 if mode=="home" else (1 if mode=="away" else 2))
        self.update_setpoints(force=True)

    def periodic_update(self):
        (_, mo, dd, hr, mn, _, wd, _) = utime.localtime()
        weekday = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'][wd]
        self.label['time'].set("{:02d}:{:02d}".format(hr, mn))
        self.label['date'].set("{:02d}/{:02d} {}".format(dd, mo, weekday))
        self.update_setpoints()
        self.label['endtime'].set("FINO ALLE {}:{}".format(int(self.__next_schedule_time/60), self.__next_schedule_time%60))
        self.label['target'].set(10*self.__current_setpoint)
        self.logic.periodic_check()

    def displayScheduler(self):
        pass

    def extend_setpoint_to_next(self):
        _, next_time, _ = self.schedule[self.__current_mode].getSetpoint(time=self.__next_schedule_time)
        self.set_override(self.__current_setpoint, next_time)

    def anticipate_next_setpoint(self):
        _, next_time, next_temperature = self.schedule[self.__current_mode].getSetpoint()
        self.set_override(next_temperature, next_time)

    def set_override_for_duration(self, temperature, duration):
        time = self.__getTime() + duration
        time -= 1440 if time > 1440 else 0
        self.set_override(temperature, time)

    def set_override(self, temperature, next_time):
        self.__override_temperature = temperature
        self.__override_next_time = next_time
        self.update_setpoints()
    
    def clear_override(self):
        self.set_override(None, None)

    def __getTime(self):
        (_,_,_,hr, mn, _,_,_) = utime.localtime()
        return hr * 60 + mn

    def update_setpoints(self, force = False):
        if self.__override_temperature is not None and self.__getTime() == self.__override_next_time:
            self.clear_override()
        elif self.__override_temperature is not None:
            current_setpoint = self.__override_temperature
            next_time = self.__override_next_time
        else:
            current_setpoint, next_time, _ = self.schedule[self.__current_mode].getSetpoint()
        if(current_setpoint.value != self.__current_setpoint) or (next_time != self.__next_schedule_time) or force:
            self.__current_setpoint = current_setpoint.value
            self.__next_schedule_time = next_time
            self.periodic_update()
            return True
        else:
            return False

    def timer_irq(self):
        pass

    def bt_irq(self, obj, adv_message, rssi):
        if isinstance(obj, xiaomiOnNextion):
            obj.decode_advertising(adv_message)
            obj.rssi = rssi
            self.logic.setCurrentTemperature(obj.temperature, self.BEDROOM_SENSOR_NO if obj == self.bedroom else self.BATHROOM_SENSOR_NO)

