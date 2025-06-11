import serial
import time

class UARTUtil:
    @staticmethod
    def open_port(port='/dev/ttyS0', baudrate=9600, timeout=1):
        return serial.Serial(port, baudrate, timeout=timeout)

    def _send_data(ser, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        ser.write(data)

    @staticmethod
    def send_data(port='/dev/ttyS0', baudrate=9600, data='', timeout=1, response_size=64, delay=0.1):
        with UARTUtil.open_port(port, baudrate, timeout) as ser:
            UARTUtil.send_data(ser, data)


    @staticmethod
    def receive_data(ser, size=64):
        return ser.read(size).decode('utf-8', errors='ignore')

    @staticmethod
    def send_and_receive(port='/dev/ttyS0', baudrate=9600, data='', timeout=1, response_size=64, delay=0.1):
        with UARTUtil.open_port(port, baudrate, timeout) as ser:
            UARTUtil.send_data(ser, data)
            time.sleep(delay)
            return UARTUtil.receive_data(ser, response_size)