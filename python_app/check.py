import serial

ser = serial.Serial('COM8', 9600, timeout=1)  # Windows 用 'COM3' 等
while True:
    line = ser.readline().decode('utf-8').strip()
    if not line:
        continue
    if ',' not in line:
        continue
    voltage, ts = line.split(',')
    print(f"v: {float(voltage):.3f} V, time: {ts}")