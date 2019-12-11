import ubinascii
import time

class xiaomi:
    def __init__(self, mac):
        if isinstance(mac, bytes):
            if len(mac) != 6:
                raise ValueError("MAC must be 6 bytes")
            self.mac = mac
        elif isinstance(mac, str):
            if len(mac) != 17:
                raise ValueError("MAC must be xx:xx:xx:xx:xx:xx")
            self.mac = b"".join([bytes([int(n,16)]) for n in mac.split(":")])
        self.temperature = None
        self.humidity = None
        self.battery = None
        self.rssi = 0
        self.last_message = time.ticks_ms()

    def setRSSI(self, value):
        self.rssi = value

    def getReadableMAC(self):
        return ubinascii.hexlify(self.mac,':').decode()

    def getTimeSinceLastUpdate(self):
        return time.ticks_diff(time.ticks_ms(), self.last_message)/1000

    def decode_advertising(self, adv_data):
        n = adv_data[11]
        if adv_data[18] == 0x0D: # Temperature&Humidity
            self.temperature = (adv_data[21] + adv_data[22] * 256) / 10
            self.humidity = (adv_data[23] + adv_data[24] * 256) / 10
        elif adv_data[18] == 0x06: #Humidity only
            self.humidity = (adv_data[21] + adv_data[22] * 256) / 10
        elif adv_data[18] == 0x04: #Temperature only
            self.temperature = (adv_data[21] + adv_data[22] * 256) / 10
        elif adv_data[18] == 0x0A:
            self.battery = adv_data[21]
        else:
            adv_data = ubinascii.hexlify(adv_data).decode()
            adv_data = " ".join([adv_data[2*i:2*i+2] for i in range(0, int(len(adv_data)/2))])
            return False
        self.last_message = time.ticks_ms()
        return True

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