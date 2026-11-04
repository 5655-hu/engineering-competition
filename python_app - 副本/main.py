import sys
import time
import csv
from sensor_layer import SimSensor, SerialSensor
from debounce import DebounceFilter, CONFIG
from judge import judge_station
from filter import DistanceFilter
from trend_warning import TrendPredictor

def dist_to_stock(dist):
    return max(0, int((CONFIG["DIST_ZERO_STOCK"] - dist) * CONFIG["DIST_TO_STOCK_COEF"]))

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else None
    if port:
        sensor = SerialSensor(port, CONFIG["SERIAL_BAUD"])
        sensor_type = "真实串口"
    else:
        sensor = SimSensor()
        sensor_type = "模拟数据"
    
    debounce = DebounceFilter()
    # 距离滤波：窗口大小5，限幅5cm，盲区和超量程阈值与配置统一
    dist_filter = DistanceFilter(
        window_size=5, 
        max_delta=5.0,
        blind_max=CONFIG["BLIND_MAX"],
        over_min=CONFIG["OVER_RANGE_MIN"]
    )
    # 趋势预警：窗口20个点，速率阈值2
    trend_predictor = TrendPredictor(window_size=20, warn_rate=2.0)
    
    log_file = open("test_log.csv", "w", newline="", encoding="utf-8")
    writer = csv.writer(log_file)
    writer.writerow(["时间", "原始距离cm", "滤波后距离cm", "估算存量", "最终状态", "预警状态", "备注"])

    print(f"测试启动 | 模式: {CONFIG['MODE']} | 传感器: {sensor_type} | 滤波: 已启用 | 预警: 已启用")
    print("-" * 80)
    try:
        while True:
            raw_dist = sensor.read()
            if raw_dist is None:
                continue
            
            # 第一级：原始距离做两级滤波
            dist = dist_filter.update(raw_dist)
            ts = time.strftime("%H:%M:%S")
            remark = ""
            warn_status = "正常"

            if debounce.is_blind(dist):
                remark = "盲区/超量程"
                status = debounce.last_status
                stock = "-"
            else:
                stock = dist_to_stock(dist)
                raw_status = judge_station(stock)
                status = debounce.filter(raw_status)
                # 第二级：存量趋势预警
                warn_status = trend_predictor.update(stock)

            line = f"{ts} | 原始:{raw_dist:>5.1f}cm | 滤波:{dist:>5.1f}cm | 存量:{stock:>3} | 状态:{status:>4} | 预警:{warn_status}"
            if remark:
                line += f" | {remark}"
            print(line)
            writer.writerow([ts, raw_dist, dist, stock, status, warn_status, remark])
            time.sleep(0.2)
    except KeyboardInterrupt:
        log_file.close()
        print("\n测试结束，日志已保存")

if __name__ == "__main__":
    main()
