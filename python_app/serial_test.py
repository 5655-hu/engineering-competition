import serial
import time

ser = serial.Serial("COM3", 9600, timeout=1)
time.sleep(2)

print("串口单测启动")
while True:
    if ser.in_waiting:
        line = ser.readline().decode("utf-8", "ignore").strip()
        try:
            dist = float(line)
            print(f"距离: {dist:.1f} cm")
        except ValueError:
            continue
