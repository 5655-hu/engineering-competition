import random
from filter import DistanceFilter
from debounce import DebounceFilter, CONFIG
from judge import judge_station

def generate_test_data(length=500):
    """生成带噪声、跳点的模拟测距数据，模拟真实硬件场景"""
    data = []
    base_dist = 35.0
    for i in range(length):
        # 基础场景切换
        if i < 100:
            base_dist = 35.0
        elif i < 200:
            base_dist = 25.0  # 进入堆积区间
        elif i < 300:
            base_dist = 37.0  # 临界值附近抖动
        else:
            base_dist = 45.0  # 恢复正常
        
        # 叠加随机噪声
        noise = random.uniform(-1.5, 1.5)
        dist = base_dist + noise
        
        # 随机插入突发跳点
        if random.random() < 0.03:
            dist += random.choice([-10, 10])
        
        data.append(dist)
    return data

def run_test():
    data = generate_test_data()
    dist_filter = DistanceFilter(
        window_size=5, 
        max_delta=5.0,
        blind_max=CONFIG["BLIND_MAX"],
        over_min=CONFIG["OVER_RANGE_MIN"]
    )
    debounce = DebounceFilter()
    
    raw_status_list = []
    filtered_status_list = []
    
    for dist in data:
        # 无滤波无防抖的原始判定
        stock = max(0, int((CONFIG["DIST_ZERO_STOCK"] - dist) * CONFIG["DIST_TO_STOCK_COEF"]))
        raw_status = judge_station(stock)
        raw_status_list.append(raw_status)
        
        # 经过滤波+防抖的判定
        filtered_dist = dist_filter.update(dist)
        stock_f = max(0, int((CONFIG["DIST_ZERO_STOCK"] - filtered_dist) * CONFIG["DIST_TO_STOCK_COEF"]))
        filtered_status = debounce.filter(judge_station(stock_f))
        filtered_status_list.append(filtered_status)
    
    # 统计状态切换次数，切换越多说明抖动越严重
    raw_switches = sum(1 for i in range(1, len(raw_status_list)) if raw_status_list[i] != raw_status_list[i-1])
    filtered_switches = sum(1 for i in range(1, len(filtered_status_list)) if filtered_status_list[i] != filtered_status_list[i-1])
    
    print("===== 算法效果量化测试 =====")
    print(f"测试数据点数: {len(data)}")
    print(f"原始判定状态切换次数: {raw_switches} 次")
    print(f"滤波+防抖后切换次数: {filtered_switches} 次")
    if raw_switches > 0:
        print(f"抖动抑制率: {round((1 - filtered_switches/raw_switches)*100, 1)}%")
    print("=" * 30)
    print("结论: 状态切换次数越少，系统越稳定，临界闪烁越少")

if __name__ == "__main__":
    run_test()
