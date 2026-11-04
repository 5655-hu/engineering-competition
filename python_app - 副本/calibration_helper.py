def calc_params(dist_0, dist_1, dist_3):
    """
    输入标定实测距离（单位cm），自动计算换算参数
    :param dist_0: 0辆车时的稳定距离
    :param dist_1: 1辆车时的稳定距离
    :param dist_3: 3辆车时的稳定距离
    """
    # 基准零点：0辆车对应的距离
    zero_stock_dist = dist_0
    
    # 用两个点拟合系数，取平均值
    coef_1 = 1 / (dist_0 - dist_1)
    coef_3 = 3 / (dist_0 - dist_3)
    avg_coef = round((coef_1 + coef_3) / 2, 2)
    
    # 推荐状态阈值（按总容量60%为堆积，20%为缺车）
    full_stock = round((dist_0 - dist_3) * avg_coef * 0.7)
    empty_stock = round((dist_0 - dist_3) * avg_coef * 0.2)
    
    print("===== 标定结果（直接复制到 debounce.py CONFIG 中）=====")
    print(f'"DIST_ZERO_STOCK": {zero_stock_dist},')
    print(f'"DIST_TO_STOCK_COEF": {avg_coef},')
    print(f'"STOCK_EMPTY": {empty_stock},')
    print(f'"STOCK_FULL": {full_stock},')
    print(f'"STOCK_FULL_EXIT": {max(0, full_stock - 5)},')
    print("=" * 50)
    print(f"验证：1辆车估算存量 = {round((zero_stock_dist - dist_1) * avg_coef)}")
    print(f"验证：3辆车估算存量 = {round((zero_stock_dist - dist_3) * avg_coef)}")


# ========== 标定实验时在这里填实测值，运行即可 ==========
if __name__ == "__main__":
    # 示例值，标定的时候换成实际测量的距离
    DIST_0_CAR = 40.0
    DIST_1_CAR = 32.5
    DIST_3_CAR = 20.0
    
    calc_params(DIST_0_CAR, DIST_1_CAR, DIST_3_CAR)
