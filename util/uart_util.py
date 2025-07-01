import serial
import time

class UARTUtil:
    @staticmethod
    def open_port(port=None, baudrate=9600, timeout=1):
        if port is None:
            # Try common ACM ports
            for p in ['/dev/ttyACM0', '/dev/ttyACM1']:
                try:
                    return serial.Serial(p, baudrate, timeout=timeout)
                except serial.SerialException:
                    continue
            raise serial.SerialException("No available /dev/ttyACM0 or /dev/ttyACM1 port found.")
        return serial.Serial(port, baudrate, timeout=timeout)

    @staticmethod
    def send_data(ser, data):
        if isinstance(data, str):
            data += '\n'
            data = data.encode('utf-8')
        ser.write(data)
        ser.flush()
        time.sleep(0.2)

    @staticmethod
    def receive_data(ser, size=64):
        return ser.read(size).decode('utf-8', errors='ignore')

    @staticmethod
    def send_and_receive(ser, baudrate=9600, data='', timeout=1, response_size=64, delay=0.1):
        if isinstance(data, str):
            data += '\n'
            data = data.encode('utf-8')
        ser.write(data)
        ser.flush()
        time.sleep(0.2)
        return ser.read(response_size).decode('utf-8', errors='ignore')
