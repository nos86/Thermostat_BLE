import nextion
import machine

from thermometer import xiaomiOnNextion
from bluetooth_interface import BluetoothManager

class Thermostat:
    def __init__(self, nextion):
        self.bluetooth = BluetoothManager()
        self.nextion = nextion
        self.bedroom  = xiaomiOnNextion(b'Le\xa8\xdd\xd4L'
                                    , nextion.getComponentByPath("bedroom.temperature")
                                    , nextion.getComponentByPath("bedroom.humidity")
                                    , nextion.getComponentByPath("bedroom.battery")
                                    , nextion.getComponentByPath("bedroom.online"))
        self.bluetooth.addDevice(self.bedroom.mac, lambda adv, rssi: self.bt_irq(self.bedroom, adv, rssi))

        #self.bathroom = xiaomiOnNextion(b'Le\xa8\xdd\xd4L' #TODO: use new MAC
        #                            , nextion.getComponentByPath("bathroom.temperature")
        #                            , nextion.getComponentByPath("bathroom.humidity")
        #                            , nextion.getComponentByPath("bathroom.battery")
        #                            , nextion.getComponentByPath("bathroom.online")) 
        #self.bluetooth.addDevice(self.bathroom.mac, lambda adv, rssi: self.bt_irq(self.bathroom, adv, rssi))

        #self.timer = machine.Timer(0).init(period=1000, mode=machine.Timer.PERIODIC, callback)self.timer_irq)
        self.bluetooth.start()

    def timer_irq(self):
        pass

    def bt_irq(self, obj, adv_message, rssi):
        if isinstance(obj, xiaomiOnNextion):
            obj.decode_advertising(adv_message)
            obj.rssi = rssi