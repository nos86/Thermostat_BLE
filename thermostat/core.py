import machine # pylint: disable=import-error
import utime # pylint: disable=import-error

class SensorLogic:
    def __init__(self, stateCallback=None, hysteresis=0.5, pin=18, minTimeOn=30):
        self.stateCallback = stateCallback
        self.setpoint = None
        self.current = None
        self.state = False
        self.hysteresis = hysteresis
        self.minTimeOn = minTimeOn
        self.lastActivation = utime.time()
        self.lastReading = utime.time()
        self.pin = machine.Pin(pin, machine.Pin.OPEN_DRAIN)
        self.lastActivation = utime.time()
        self.state = False
        self.pin.value(True)

    def setCurrentTemperature(self, value, ignoreMinTime=False):
        self.current = value
        if (self.setpoint is None) or (self.current is None):
            return
        if self.isReadingUpdated() == False:
            self.__setState(False)
        elif self.state == False and self.current < self.setpoint - self.hysteresis:
            self.__setState(True)
        elif self.isMinimumOnTimeElapsed and self.current > self.setpoint + self.hysteresis:
            self.__setState(False)
    
    def setSetpoint(self, value):
        self.setpoint = value
        self.setCurrentTemperature(self.current, ignoreMinTime=True)

    def __setState(self, active):
        if self.isReadingUpdated() == False:
            active = False
        if self.state != active:
            self.state = active
            self.pin.value(active==False)
            self.lastActivation = utime.time()
            if self.stateCallback:
                self.stateCallback(self.state)

    def isReadingUpdated(self):
        return utime.time()-self.lastReading < 300

    def isMinimumOnTimeElapsed(self):
        return (self.durationOfCurrentActivation() >= self.minTimeOn) or self.state==False

    def durationOfCurrentActivation(self):
        if self.state:
            return (utime.time()-self.lastActivation)/60
        else:
            return 0

class MultiSensorLogic(SensorLogic):
    def __init__(self, stateCallback=None, hysteresis=0.5, pin=18, minTimeOn=30, numberOfSensors=2):
        super().__init__(stateCallback, hysteresis, pin=pin, minTimeOn=minTimeOn)
        self.lastReading = [utime.time()] * numberOfSensors
        self.reading = [None] * numberOfSensors #New variable that handles multi-sensors
        self.numberOfSensors = numberOfSensors

    def setCurrentTemperature(self, value, sensor_id = -1, ignoreMinTime=False):
        if sensor_id > -1:
            self.reading[sensor_id] = value
            self.lastReading[sensor_id] = utime.time()
            reads = [self.reading[id] for id in range(self.numberOfSensors) if self.reading[id] is not None and self.isReadingUpdated(id)]
            if len(reads)==0:
                return self.setpoint #FIXME: potential bug
            value = sum(reads)/len(reads)
        return super().setCurrentTemperature(value, ignoreMinTime=ignoreMinTime)

    def isReadingUpdated(self, sensor_id=-1):
        if sensor_id > -1:
            time = self.lastReading[sensor_id]
            return False if time is None else utime.time() - time < 300
        else:
            return any([self.isReadingUpdated(sensor_id) for sensor_id in range(self.numberOfSensors)])
        