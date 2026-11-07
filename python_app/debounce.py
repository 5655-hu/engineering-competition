CONFIG = {
    "MODE": "DEMO",  # DEMO / PRODUCTION
    "BLIND_MAX": 2.0,       # 盲区上限，单位cm
    "OVER_RANGE_MIN": 400,  # 超量程下限，单位cm
    "DEMO_THRESHOLD": 1,    # DEMO模式防抖次数
    "PROD_THRESHOLD": 3,    # PRODUCTION模式防抖次数
    "STOCK_EMPTY": 10,      # 缺车判定阈值（存量小于该值）
    "STOCK_FULL": 40,       # 堆积进入阈值（存量大于该值触发堆积）
    "STOCK_FULL_EXIT": 35,  # 堆积退出阈值（存量小于该值恢复正常，形成滞回）
    "DIST_ZERO_STOCK": 40,  # 0辆车对应的基准距离，单位cm
    "DIST_TO_STOCK_COEF": 1.5,  # 距离转存量系数
    "SERIAL_PORT": "COM3",
    "SERIAL_BAUD": 9600
}


class DebounceFilter:
    def __init__(self):
        self.last_status = "正常"
        self.counter = 0
        self.threshold = CONFIG["DEMO_THRESHOLD"] if CONFIG["MODE"] == "DEMO" else CONFIG["PROD_THRESHOLD"]

    def is_blind(self, dist):
        """判断是否为盲区/超量程"""
        return dist <= CONFIG["BLIND_MAX"] or dist >= CONFIG["OVER_RANGE_MIN"]

    def filter(self, raw_status):
        """
        输入原始判定状态，输出防抖后的最终状态
        双重防抖：滞回区间保持 + 连续计数确认
        """
        # 滞回区间内返回None，直接保持上一状态，不触发计数
        if raw_status is None:
            self.counter = 0
            return self.last_status

        # 状态未变化，重置计数器
        if raw_status == self.last_status:
            self.counter = 0
            return self.last_status

        # 状态变化时，计数防抖，连续命中才切换
        self.counter += 1
        if self.counter >= self.threshold:
            self.last_status = raw_status
            self.counter = 0
        
        return self.last_status
