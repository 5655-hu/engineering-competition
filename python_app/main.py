import time
import csv
from sensor_layer import SimSensor
from debounce import DebounceFilter, CONFIG
from judge import judge_station

DIST_TO_STOCK_COEF = 1.5
DIST_ZERO_STOCK = 40

def dist_to_stock(dist):
    return max(0, int((DIST_ZERO_STOCK - dist) * DIST_TO_STOCK_COEF))

def main():
    sensor = SimSensor()
    filter = DebounceFilter()
    log_file = open("test_log.csv", "w", newline="", encoding="utf-8")
    writer = csv.writer(log_file)
    writer.writerow(["时间", "距离cm", "估算存量", "最终状态", "备注"])

    print(f"测试启动 | 模式: {CONFIG['MODE']} | 传感器: 模拟")
    try:
        while True:
            dist = sensor.read()
            if dist is None:
                continue
            ts = time.strftime("%H:%M:%S")
            remark = ""

            if filter.is_blind(dist):
                remark = "盲区/超量程"
                status = filter.last_status
                stock = "-"
            else:
                stock = dist_to_stock(dist)
                raw_status = judge_station(stock)
                status = filter.filter(raw_status)

            line = f"{ts} | {dist:>5.1f}cm | 存量:{stock:>3} | {status:>4}"
            if remark:
                line += f" | {remark}"
            print(line)
            writer.writerow([ts, dist, stock, status, remark])
            time.sleep(0.5)
    except KeyboardInterrupt:
        log_file.close()
        print("\n测试结束，日志已保存")

if __name__ == "__main__":
    main()
