import utime
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
    def __init__(self, nextion_driver, schedule_path ="/programs.json", bedroom_mac = b'Le\xa8\xdd\xd4L', bathroom_mac = b'0000'):
        self.nextion = nextion_driver
        self.label = {
            "date" : self.nextion.getComponentByPath("overview.date"),
            "time" : self.nextion.getComponentByPath("overview.time"),
            "target" : self.nextion.getComponentByPath("overview.target"),
            "endtime" : self.nextion.getComponentByPath("overview.endtime"),
            "override" : self.nextion.getComponentByPath("overview.override"),
            "outside_temperature": self.nextion.getComponentByPath("overview.out_temp"),
            "outside_humidity": self.nextion.getComponentByPath("overview.out_hum"),
            "program": self.nextion.getComponentByPath("overview.program")
        }
        #Variable initialization
        self.__override = False
        self.__current_setpoint = None
        self.__next_schedule_time = None
        self.__last_date_update = 0
        self.schedule = {}
        with open(schedule_path, 'r') as fp:
            temp = json.load(fp)
        for mode in ['home', 'away', 'vacation']:
            self.schedule[mode] = Scheduler(mode, temp[mode]) #FIXME: setup working day
        self.nextion.register_listener("overview.prg_home".format(mode), lambda x: self.set_mode("home"))
        self.nextion.register_listener("overview.prg_away".format(mode), lambda x: self.set_mode("away"))
        self.nextion.register_listener("overview.prg_vacation".format(mode), lambda x: self.set_mode("vacation"))

        self.relay = HeatingRelay(self.nextion.getComponentByPath("overview.heater"), 25.0, 0.5, minTimeOn=0)

        self.bluetooth = BluetoothManager()
        
        self.bedroom  = xiaomiOnNextion(b'Le\xa8\xdd\xd4L'
                                    , self.nextion.getComponentByPath("bedroom.temperature")
                                    , self.nextion.getComponentByPath("bedroom.humidity")
                                    , self.nextion.getComponentByPath("bedroom.battery")
                                    , self.nextion.getComponentByPath("bedroom.online"))
        self.bluetooth.addDevice(self.bedroom.mac, lambda adv, rssi: self.bt_irq(self.bedroom, adv, rssi))

        #self.bathroom = xiaomiOnNextion(b'Le\xa8\xdd\xd4L' #TODO: use new MAC
        #                            , self.nextion.getComponentByPath("bathroom.temperature")
        #                            , self.nextion.getComponentByPath("bathroom.humidity")
        #                            , self.nextion.getComponentByPath("bathroom.battery")
        #                            , self.nextion.getComponentByPath("bathroom.online")) 
        #self.bluetooth.addDevice(self.bathroom.mac, lambda adv, rssi: self.bt_irq(self.bathroom, adv, rssi))

        #self.timer = machine.Timer(0).init(period=1000, mode=machine.Timer.PERIODIC, self.timer_irq))

        self.set_mode('home')
        #self.bluetooth.start()

    def set_mode(self, mode):
        self.__current_mode = mode
        self.label['program'].set(0 if mode=="home" else (1 if mode=="away" else 2))
        self.updateSetpoints(force=True)

    def periodicUpdate(self):
        (_, mo, dd, hr, mn, _, wd, _) = utime.localtime()
        weekday = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'][wd]
        self.label['time'].set("{:02d}:{:02d}".format(hr, mn))
        self.label['date'].set("{:02d}/{:02d} {}".format(dd, mo, weekday))
        self.label['endtime'].set("fino alle {}:{}".format(int(self.__next_schedule_time/60), self.__next_schedule_time%60))
        self.label['target'].set(10*self.__current_setpoint)

    def updateSetpoints(self, force = False):
        current_setpoint, next_time, _ = self.schedule[self.__current_mode].getSetpoint()
        if(current_setpoint.value != self.__current_setpoint) or (next_time != self.__next_schedule_time) or force:
            self.__current_setpoint = current_setpoint.value
            self.__next_schedule_time = next_time
            self.periodicUpdate()
            return True
        else:
            return False
    
     
    def timer_irq(self):
        pass

    def bt_irq(self, obj, adv_message, rssi):
        if isinstance(obj, xiaomiOnNextion):
            obj.decode_advertising(adv_message)
            obj.rssi = rssi