import serial
import time

ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)
time.sleep(2)

# Send test string
test_string = "ping\n"
ser.write(test_string.encode())

print("Sent:", test_string.strip())

# Wait for a response
while(True):
    response = ser.read(len(test_string))
    if response.decode() == test_string:
        print("Received:", response.decode().strip())
        break