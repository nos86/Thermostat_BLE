import utime  # pylint: disable=import-error
import btree  # pylint: disable=import-error
import machine  # pylint: disable=import-error
import urequests  # pylint: disable=import-error
import json
import micropython as mp # pylint: disable=import-error

from bluetooth_interface import BluetoothManager
import secret

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

    def __init__(self, nextion_driver, schedule_path="/programs.json", setting_path="/app_setting.db", bedroom_mac=b'Le\xa8\xdd\xd4L', bathroom_mac=b'X-41\xac\x9f'):
        self.nextion = nextion_driver
        self.schedule_path = schedule_path
        self.last_weather_update = 0
        self.label = {
            "date": self.nextion.getComponentByPath("overview.date"),
            "time": self.nextion.getComponentByPath("overview.time"),
            "target": self.nextion.getComponentByPath("overview.target"),
            "endtime": self.nextion.getComponentByPath("overview.endtime"),
            "override": self.nextion.getComponentByPath("overview.override"),
            "outside_temperature": self.nextion.getComponentByPath("overview.out_temp"),
            "outside_humidity": self.nextion.getComponentByPath("overview.out_hum"),
            "heater": self.nextion.getComponentByPath("overview.heater"),
            "program": self.nextion.getComponentByPath("overview.program")
        }
        # Load settings
        try:
            self.setting_file = open(setting_path, "r+b")
            self.settings = btree.open(self.setting_file)
        except OSError:
            self.setting_file = open(setting_path, "w+b")
            self.settings = btree.open(self.setting_file)
            self.__initialize_settings()

        self.schedule = Scheduler(schedule_path,
                                  t_high_comp=self.nextion.getComponentByPath(
                                      "setpoints.t_high"),
                                  t_med_comp=self.nextion.getComponentByPath(
                                      "setpoints.t_med"),
                                  t_low_comp=self.nextion.getComponentByPath(
                                      "setpoints.t_low"),
                                  mode=self.settings[b'mode'].decode())
        for mode in ['home', 'away', 'vacation']:
            self.nextion.register_listener("overview.prg_{}".format(
                mode), lambda x, mode=mode: self.set_mode(mode))
        self.nextion.register_listener(
            "setpoints.confirm", lambda x : mp.schedule(self.updateTemperatureSetpoints, x))

        self.logic = MultiSensorLogic(lambda value: self.label['heater'].set(
            1 if value else 0), 0.5, minTimeOn=0, numberOfSensors=2)

        self.bluetooth = BluetoothManager()
        self.bedroom = xiaomiOnNextion(bedroom_mac, self.nextion.getComponentByPath("bedroom.temperature"), self.nextion.getComponentByPath(
            "bedroom.humidity"), self.nextion.getComponentByPath("bedroom.battery"), self.nextion.getComponentByPath("bedroom.online"))
        self.bluetooth.addDevice(self.bedroom.mac, self.bt_irq)
        self.bathroom = xiaomiOnNextion(bathroom_mac, self.nextion.getComponentByPath("bathroom.temperature"), self.nextion.getComponentByPath(
            "bathroom.humidity"), self.nextion.getComponentByPath("bathroom.battery"), self.nextion.getComponentByPath("bathroom.online"))
        self.bluetooth.addDevice(self.bathroom.mac, self.bt_irq)
        self.bluetooth.start()

        self.periodical_checks()
        self.timer = machine.Timer(0)
        self.timer.init(period=60000, mode=machine.Timer.PERIODIC, callback=self.periodical_checks)

    def updateTemperatureSetpoints(self, x=None):
        self.schedule.updateSetpoints()
        self.periodical_checks()

    def __initialize_settings(self):
        self.set_mode("home", is_starting=True)

    def updateWeatherTemperature(self):
        if utime.time()-self.last_weather_update < 3600:
            return
        try:
            data = urequests.get("http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={appid}".format(
                city=secret.CITY, appid=secret.OPENWEATHERMAP)).json()
            self.label['outside_temperature'].set(int(data['main']['temp']*10))
            self.label['outside_temperature'].set(
                int(data['main']['humidity']))
            self.last_weather_update = utime.time()
        except:
            pass
        return

    def set_mode(self, mode=None, is_starting=False):
        if mode and self.schedule.isModeChanged(mode):
            self.settings[b'mode'] = mode.encode()
            self.settings.flush()
            self.schedule.load(mode)
            self.label['program'].set(
                0 if mode == "home" else (1 if mode == "away" else 2))
        if is_starting == False:
            self.periodical_checks()

    def periodical_checks(self, *nargs, **kwargs):
        (_, mo, dd, hr, mn, _, wd, _) = utime.localtime()
        (current_setpoint, next_time, _) = self.schedule.getSetpoint()
        self.updateWeatherTemperature()
        self.logic.setSetpoint(current_setpoint.value)
        weekday = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'][wd]
        self.label['time'].set("{:02d}:{:02d}".format(hr, mn))
        self.label['date'].set("{:02d}/{:02d} {}".format(dd, mo, weekday))
        self.label['target'].set(int(10*current_setpoint.value))
        self.label['endtime'].set("FINO ALLE {:02d}:{:02d}".format(
            int(next_time/60), next_time % 60))

    def bt_irq(self, mac, adv_message, rssi):
        if mac == self.bathroom.mac:
            obj = self.bathroom
        elif mac == self.bedroom.mac:
            obj = self.bedroom
        else:
            # FIXME: remove after debug and optimize inline if above
            print("Unable to find the MAC")
            return
        obj.decode_advertising(adv_message)
        obj.rssi = rssi
        self.logic.setCurrentTemperature(
            obj.temperature, self.BEDROOM_SENSOR_NO if obj == self.bedroom else self.BATHROOM_SENSOR_NO)

    def __getTime(self):
        (_, _, _, hr, mn, _, _, _) = utime.localtime()
        return hr * 60 + mn
