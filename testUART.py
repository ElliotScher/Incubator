import serial
import time

ser = serial.Serial('/dev/serial0', 9600, timeout=1)
time.sleep(2)

# Send test string
test_string = "ping\n"
ser.write(test_string.encode())

# Wait for a response
time.sleep(0.1)
response = ser.read(len(test_string))

print("Sent:", test_string.strip())
print("Received:", response.decode().strip())