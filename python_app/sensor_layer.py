import random
import serial

class SimSensor:
    def read(self):
        if random.random() < 0.15:
            # 15%概率生成盲区/超量程数据，测试容错
            return round(random.choice([0.5, 420]), 1)
        else:
            # 正常范围：10~50cm，贴近真实沙盘场景
            return round(random.uniform(10, 50), 1)

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
