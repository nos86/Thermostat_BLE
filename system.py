import network
import ntptime
import utime

from thermostat import Thermostat

iface = network.WLAN(network.STA_IF)
iface.active(True)
iface.connect("Musux_IoT", "#maibanale")
utime.sleep(5)
try:
    ntptime.settime()
except:
    print("Unable to retrieve local time")

t = Thermostat()

