# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import micropython as mp # pylint: disable=import-error
import system as sys
import secret

if __name__ == "__main__":
    import machine # pylint: disable=import-error
    sys.reset_cause = machine.reset_cause()
    sys.print_reset_cause()
    
    import network # pylint: disable=import-error
    sys.wlan0 = network.WLAN(network.STA_IF)
    sys.wlan0.active(True)
    sys.wlan0.connect(secret.WIFI_SSID, secret.WIFI_PASS)
    from app import app