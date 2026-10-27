from collections import deque

class TrendPredictor:
    def __init__(self, window_size=20, warn_rate=2.0):
        """
        存量趋势预判与预警
        :param window_size: 计算变化率的历史数据窗口大小
        :param warn_rate: 预警触发速率阈值，单位：存量/秒，速率超过该值触发预警
        """
        self.window_size = window_size
        self.warn_rate = warn_rate
        self.history = deque(maxlen=window_size)  # 存 (时间戳, 存量值)

    def update(self, stock):
        """输入当前存量，输出预警状态"""
        import time
        now = time.time()
        self.history.append((now, stock))

        # 数据不足时不预警
        if len(self.history) < self.window_size // 2:
            return "正常"

        # 计算存量变化速率（单位时间内的存量变化量）
        t_start, s_start = self.history[0]
        t_end, s_end = self.history[-1]
        delta_time = t_end - t_start
        if delta_time <= 0:
            return "正常"
        
        rate = (s_end - s_start) / delta_time  # 正值：存量增加，正向堆积；负值：存量减少，缺车

        # 触发预警
        if rate > self.warn_rate:
            return "即将堆积"
        elif rate < -self.warn_rate:
            return "即将缺车"
        else:
            return "正常"
