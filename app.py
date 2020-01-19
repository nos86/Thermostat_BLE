import machine # pylint: disable=import-error
import ntptime # pylint: disable=import-error
import utime # pylint: disable=import-error
import json

import system as sys

import nextion
from thermostat import MultiSensorLogic
from thermostat.interface import Thermostat

driver = nextion.Driver(timer=machine.Timer(1))
with open("nextion.json", "r") as fp:
    driver.loadPages(json.loads(fp.read()))

timeout = 0
while((sys.wlan0.isconnected()==False) or (timeout>5000)):
    utime.sleep_ms(200)
    timeout += 0.2

try:
    ntptime.settime()
except:
    print("Unable to retrieve local time")

t = Thermostat(driver)

