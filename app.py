import machine # pylint: disable=import-error
import ntptime # pylint: disable=import-error
import utime # pylint: disable=import-error
import json

import system as sys

import nextion
from thermostat import MultiSensorLogic
from thermostat.interface import Thermostat

driver = nextion.Driver(timer=machine.Timer(1), timeout=300)
with open("nextion.json", "r") as fp:
    driver.loadPages(json.loads(fp.read()))

timeout = 0
print("Trying to connect to network..", end='.')
while((sys.wlan0.isconnected()==False) and (timeout<5000)):
    utime.sleep_ms(200)
    timeout += 200
    print(".", end="")
print("failed" if timeout >= 5000 else "OK")

try:
    ntptime.settime()
except:
    print("Unable to retrieve local time")

global app
app = Thermostat(driver)

app.nextion.uart.debug_send=False
app.nextion.uart.debug_receive=Falseapp.nextion.uart.debug_uart_receive = False