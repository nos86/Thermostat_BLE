# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import system as sys

if __name__ == "__main__":
    import machine # pylint: disable=import-error
    sys.reset_cause = machine.reset_cause()
    sys.print_reset_cause()
    
    import network # pylint: disable=import-error
    sys.wlan0 = network.WLAN(network.STA_IF)
    sys.wlan0.active(True)
    sys.wlan0.connect('FASTWEB-1-4gF4Ljn4Cm1t', "tUX97mzzrK")

