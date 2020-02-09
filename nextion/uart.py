import machine # pylint: disable=import-error
import ubinascii # pylint: disable=import-error

class UART(machine.UART):
    debug=False
    background_listener=False
    ERRORS = {
        b'\x00' : "Invalid instruction",
        # 0x01 : "Successful execution of instruction",
        b'\x02' : "Component ID invalid",
        b'\x03' : "Page ID invalid",
        b'\x04' : "Picture ID invalid",
        b'\x05' : "Font ID invalid",
        b'\x11' : "Baud rate setting invalid",
        b'\x12' : "Curve control ID number or channel number is invalid",
        b'\x1a' : "Variable name invalid",
        b'\x1b' : "Variable operation invalid",
        b'\x1c' : "Failed to assign",
        b'\x1d' : "Operate EEPROM failed",
        b'\x1e' : "Parameter quantity invalid",
        b'\x1f' : "IO operation failed",
        b'\x20' : "Undefined escape characters",
        b'\x23' : "Too long variable name",
    }

    def set_background_listener(self, timer, callback):
        self.timer = timer.init(period=100, mode=machine.Timer.PERIODIC, callback=self.check_incoming_data)
        self.background_listener = True
        self.callback = callback

    def check_incoming_data(self, event):
        try:
            if self.background_listener == False:
                return
            if self.any():
                data = self._read_internal()
                if data:
                    self.callback(data)
        except Exception as e: 
            print("UART::check_data failed: {}".format(e))

    @staticmethod
    def get_nx_error_message(err_code_char):
        return UART.ERRORS[err_code_char]

    def setDebug(self, active=True):
        self.debug = active

    def flush(self):
        if self.any()>0:
            super().read(self.any())
        return True

    def set(self, key, value, read_feedback=True):
        self.flush()
        if isinstance(value,str):
            message = key + '="' + str(value) + '"'
        else:
            message = key + '=' + str(value)
        return self.write(message, read_feedback=read_feedback)

    def write(self, message, read_feedback=False, check_return=True):
        message = message.encode()
        message += b"\xFF\xFF\xFF"
        self.background_listener = False
        self.flush()
        super().write(message)
        if read_feedback:
            data =  self.read(check_return=check_return)
        else:
            data =  None
        self.background_listener = True
        return data

    def read(self, check_return=True):
        bytes_buf = self._read_internal()
        if not bytes_buf:
            raise ValueError("No response from hardware!")

        if not check_return:
            return bytes_buf

        fbyte = bytes_buf[0]
        if fbyte in self.ERRORS:
            raise ValueError("Response Error: {} -> {}".format(
                self.get_nx_error_message(fbyte),
                bytes_buf
                ))
        #TODO: check if switch cases below are really usefull
        if fbyte == 0x01:
            return bytes_buf
        elif fbyte == 0x65:  # Touch event return data
            pass
        elif fbyte == 0x66:  # Current page ID number returns
            pass
        elif fbyte == 0x67:  # Touch coordinate data returns
            pass
        elif fbyte == 0x68:  # Touch Event in sleep mode
            pass
        elif fbyte == 0x70:  # String variable data returns
            strb = "".join([chr(b) for b in bytes_buf])
            return strb
        elif fbyte == 0x71:  # Numeric variable data returns
            print("Numeric data:", bytes_buf)
            pass
        elif fbyte == 0x86:  # Device automatically enters into sleep mode
            pass
        elif fbyte == 0x87:  # Device automatically wake up
            pass
        elif fbyte == 0x88:  # System successful start up
            pass
        elif fbyte == 0x89:  # Start SD card upgrade
            pass
        elif fbyte == 0xfd:  # Data transparent transmit finished
            pass
        else:
            raise ValueError("Response Error with unknown code: {}".format(bytes_buf))

    def readSuper(self, len):
        return super().read(len)

    def _read_internal(self):
        bytes_buf = []
        count = 0
        init = True
        while self.any()>0 or init:
            init = False
            read_char = super().read(1)
            bytes_buf.append(read_char)
            if read_char == b'\xff':
                count += 1
            else:
                count = 0
            if count == 3:
                if self.debug:
                    message= " ".join([ubinascii.hexlify(b).decode() for b in bytes_buf[:-3]])
                    print("Received data: {}".format(message))
                return bytes_buf[:-3]
        return None

