import machine
import utime

class HeatingRelay:
    def __init__(self, gxComponent, setpoint, deltaT, pin=18, minTimeOn=30):
        self.component = gxComponent
        self.setpoint = setpoint
        self.deltaT = deltaT
        self.minTimeOn = minTimeOn
        self.pin = machine.Pin(pin, machine.Pin.OPEN_DRAIN)
        self.__setState(False)

    def __setState(self, active):
        self.state = active
        self.pin.value(active==False)
        self.lastActivation = utime.time()
        self.component.set(1 if self.state else 0)

    def isMinimumOnTimeElapsed(self):
        return (utime.time()-self.lastActivation)/60 > self.minTimeOn

    def setCurrentTemperature(self, value):
        self.current = value
        if self.state == False and self.current < self.setpoint - self.deltaT/2:
            self.__setState(True)
        elif self.isMinimumOnTimeElapsed and self.current > self.setpoint + self.deltaT/2:
            self.__setState(False)
    
    def updateSetpoint(self, value):
        self.setpoint = value
        self.setCurrentTemperature(self.current)







    def bt_irq(self, obj, adv_message, rssi):
        if isinstance(obj, xiaomiOnNextion):
            obj.decode_advertising(adv_message)
            obj.rssi = rssi