import serial
import time

class UARTUtil:
    @staticmethod
    def open_port(port='/dev/ttyS0', baudrate=9600, timeout=1):
        return serial.Serial(port, baudrate, timeout=timeout)

    @staticmethod
    def send_data(ser, data):
        if isinstance(data, str):
            data += '\n'
            data = data.encode('ascii')
        ser.write(data)

    @staticmethod
    def receive_data(ser, size=64):
        return ser.read(size).decode('ascii', errors='ignore')

    @staticmethod
    def send_and_receive(ser, baudrate=9600, data='', timeout=1, response_size=64, delay=0.1):
            if isinstance(data, str):
                data += '\n'  # <-- Adjust for your device
                data = data.encode('ascii')  # <-- Use 'ascii' if ascii causes issues
            ser.reset_input_buffer()
            ser.write(data)
            return ser.read(response_size).decode('ascii', errors='ignore')  # or 'utf-8'
