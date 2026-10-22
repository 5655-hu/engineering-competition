from collections import deque
from datetime import datetime

NORMAL_LOW = 10
NORMAL_HIGH = 40
WINDOW_MINUTES = 10

history_queue = deque(maxlen=WINDOW_MINUTES)


def judge_station(stock: int) -> str:
    if stock < NORMAL_LOW:
        return "缺车"
    if stock > NORMAL_HIGH:
        return "堆积"
    return "正常"


def calc_trend(hist: deque) -> float:
    if len(hist) < 2:
        return 0.0
    
    t0, s0 = hist[0]
    t1, s1 = hist[-1]
    dt_minutes = (t1 - t0).total_seconds() / 60.0
    
    if dt_minutes <= 0:
        return 0.0
    return (s1 - s0) / dt_minutes


if __name__ == "__main__":
    test_stock_seq = [8, 7, 6, 35, 38, 42, 45, 48, 50]
    
    for stock in test_stock_seq:
        current_time = datetime.now()
        history_queue.append((current_time, stock))
        
        status = judge_station(stock)
        rate = calc_trend(history_queue)
        
        print(f"存量 {stock:>3} 辆 | 状态 {status} | 近10分钟速率 {rate:+.2f} 辆/分")

