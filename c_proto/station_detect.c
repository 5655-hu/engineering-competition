#include <stdio.h>

// 站点状态判定：缺车、正常、拥堵
int check_station_status(int bike_count, int total_slots) {
    double ratio = (double)bike_count / total_slots;
    if (ratio < 0.2) return -1;  // 缺车
    if (ratio > 0.8) return 1;   // 拥堵
    return 0;                     // 正常
}

int main() {
    int bikes = 5;
    int slots = 30;
    int status = check_station_status(bikes, slots);
    
    printf("站点车辆: %d/%d\n", bikes, slots);
    if (status == -1) printf("状态: 缺车\n");
    else if (status == 1) printf("状态: 拥堵\n");
    else printf("状态: 正常\n");
    
    return 0;
}
