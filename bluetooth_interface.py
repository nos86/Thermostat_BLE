import bluetooth # pylint: disable=import-error
import ubinascii # pylint: disable=import-error
import time
from micropython import const # pylint: disable=import-error

bt = bluetooth.BLE()

IRQ_CENTRAL_CONNECT                 = const(1 << 0)
IRQ_CENTRAL_DISCONNECT              = const(1 << 1)
IRQ_GATTS_WRITE                     = const(1 << 2)
IRQ_GATTS_READ_REQUEST              = const(1 << 3)
IRQ_SCAN_RESULT                     = const(1 << 4)
IRQ_SCAN_COMPLETE                   = const(1 << 5)
IRQ_PERIPHERAL_CONNECT              = const(1 << 6)
IRQ_PERIPHERAL_DISCONNECT           = const(1 << 7)
IRQ_GATTC_SERVICE_RESULT            = const(1 << 8)
IRQ_GATTC_CHARACTERISTIC_RESULT     = const(1 << 9)
IRQ_GATTC_DESCRIPTOR_RESULT         = const(1 << 10)
IRQ_GATTC_READ_RESULT               = const(1 << 11)
IRQ_GATTC_WRITE_STATUS              = const(1 << 12)
IRQ_GATTC_NOTIFY                    = const(1 << 13)
IRQ_GATTC_INDICATE                  = const(1 << 14)

class BluetoothManager:
    def __init__(self):
        bt.irq(self.bt_irq)
        bt.active(True)
        self.devices = {}

    def start(self):
        bt.gap_scan(0, 11500, 11250)

    def stop(self):
        bt.gap_scan(None)

    def addDevice(self, mac, callback):
        if mac in self.devices.keys():
            return
        self.devices[mac] = callback

    def bt_irq(self, event, data):
        if event == IRQ_SCAN_RESULT:
            # A single scan result.
            addr_type, addr, connectable, rssi, adv_data = data
            for mac, callback in self.devices.items():
                if addr == mac:
                    callback(mac, adv_data, rssi)
                    return  

class DiscoverableBluetooth(BluetoothManager):
    def bt_irq(self, event, data):
        addr_type, addr, connectable, rssi, adv_data = data
        if addr not in self.devices.keys():
            self.devices[addr] = rssi
            print("New device found: {} - rssi: {}".format(addr, rssi))