class DistanceFilter:
    def __init__(self, window_size=5, max_delta=5.0, blind_max=2.0, over_min=400):
        """
        两级测距滤波：限幅逐步逼近 + 滑动均值滤波
        异常值（盲区/超量程）不更新基准，避免污染正常数据
        :param window_size: 滑动均值窗口大小
        :param max_delta: 单帧最大允许变化量，逐步逼近真实值
        :param blind_max: 盲区上限
        :param over_min: 超量程下限
        """
        self.window_size = window_size
        self.max_delta = max_delta
        self.blind_max = blind_max
        self.over_min = over_min
        self.history = []
        self.last_valid_value = None

    def _is_abnormal(self, dist):
        """判断是否为异常值（盲区/超量程）"""
        return dist <= self.blind_max or dist >= self.over_min

    def update(self, raw_dist):
        """输入原始距离，输出滤波后距离"""
        if raw_dist is None:
            return self.last_valid_value

        # 异常值直接返回，不更新基准，不污染历史
        if self._is_abnormal(raw_dist):
            return raw_dist

        # 第一级：限幅逐步逼近，过滤单帧跳点，同时跟上真实变化
        if self.last_valid_value is not None:
            delta = raw_dist - self.last_valid_value
            if abs(delta) > self.max_delta:
                # 向新值方向移动最大步长，逐步逼近
                raw_dist = self.last_valid_value + (self.max_delta if delta > 0 else -self.max_delta)

        # 第二级：滑动均值滤波，抑制随机噪声
        self.history.append(raw_dist)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        
        filtered = sum(self.history) / len(self.history)
        self.last_valid_value = filtered
        return filtered
