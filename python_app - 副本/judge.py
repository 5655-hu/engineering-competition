from debounce import CONFIG

def judge_station(stock):
    """
    滞回双阈值三态判定
    - 缺车：单阈值判定
    - 堆积：双阈值滞回，进入和退出用不同阈值
    - 滞回区间内返回None，由防抖层保持上一状态
    """
    # 缺车判定
    if stock < CONFIG["STOCK_EMPTY"]:
        return "缺车"
    
    # 堆积滞回判定
    if stock > CONFIG["STOCK_FULL"]:
        return "堆积"
    elif stock < CONFIG["STOCK_FULL_EXIT"]:
        return "正常"
    else:
        # 落在滞回区间，保持上一状态
        return None
