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
    def receive_line(ser):
        """
        Read one line from the serial port, decode, and strip newline chars.
        """
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        return line

    @staticmethod
    def send_and_receive_line(ser, data='', delay=0.2):
        """
        Send data and then read one line of response.
        """
        if isinstance(data, str):
            data += '\n'
            data = data.encode('utf-8')
        ser.write(data)
        ser.flush()
        time.sleep(delay)
        return UARTUtil.receive_line(ser)
