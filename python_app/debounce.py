CONFIG = {
    "MODE": "DEMO",
    "DEMO_DEBOUNCE": 1,
    "PROD_DEBOUNCE": 3,
    "BLIND_MAX": 2,
    "RANGE_MAX": 400,
}

class DebounceFilter:
    def __init__(self):
        self.count = 0
        self.last_status = "正常"
        self.threshold = CONFIG["DEMO_DEBOUNCE"] if CONFIG["MODE"] == "DEMO" else CONFIG["PROD_DEBOUNCE"]

    def is_blind(self, dist):
        return dist <= CONFIG["BLIND_MAX"] or dist > CONFIG["RANGE_MAX"]

    def filter(self, current_status):
        if current_status == "堆积":
            self.count += 1
            if self.count >= self.threshold:
                self.last_status = "堆积"
        else:
            self.count = 0
            self.last_status = "正常"
        return self.last_status
