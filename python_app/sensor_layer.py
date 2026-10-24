import random
import serial

class SimSensor:
    def __init__(self):
        self.weights = [0.5, 0.3, 0.1, 0.1]

    def read(self):
        scenario = random.choices(["normal", "parked", "blind", "out_range"], weights=self.weights)[0]
        if scenario == "normal":
            return round(random.uniform(25, 45), 1)
        elif scenario == "parked":
            return round(random.uniform(5, 18), 1)
        elif scenario == "blind":
            return round(random.uniform(0, 1.9), 1)
        else:
            return round(random.uniform(401, 500), 1)

class SerialSensor:
    def __init__(self, port="COM3", baud=9600):
        self.ser = serial.Serial(port, baud, timeout=1)

    def read(self):
        if self.ser.in_waiting:
            line = self.ser.readline().decode("utf-8", "ignore").strip()
            try:
                return float(line)
            except ValueError:
                return None
        return None
