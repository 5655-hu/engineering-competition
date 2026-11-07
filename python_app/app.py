import streamlit as st
import pandas as pd
import numpy as np
import time
import random
import requests
from urllib.parse import quote
import datetime

# 导入队友写的模块
from sensor_layer import SimSensor
from debounce import DebounceFilter, CONFIG
from judge import judge_station

# 队友写的距离转存量函数
def dist_to_stock(dist):
    return max(0, int((CONFIG["DIST_ZERO_STOCK"] - dist) * CONFIG["DIST_TO_STOCK_COEF"]))
# ================= 站点数据配置 =================
STATIONS = {
    "一食堂站点": {"lat": 20.0085, "lon": 110.4685, "base_stock": 45},
    "图书馆站点": {"lat": 20.0070, "lon": 110.4710, "base_stock": 20},
    "教学楼站点": {"lat": 20.0055, "lon": 110.4650, "base_stock": 30}
}
# 1. 页面配置
st.set_page_config(page_title="校园单车潮汐调度系统", layout="wide", page_icon="🚲")
st.title("🚲 校园共享单车潮汐站点感知系统")
st.markdown("---")

# 2. 侧边栏控制区
st.sidebar.header("⚙️ 系统控制 (测试/降级)")
mode = st.sidebar.radio("运行模式", ["DEMO (极速响应)", "PRODUCTION (去抖过滤)"])
mock_status = st.sidebar.selectbox("模拟测试场景", ["自动获取 (传感器)", "强制缺车", "强制正常", "强制堆积", "模拟盲区/断连"])
# 实时天气获取函数（带30分钟缓存）
@st.cache_data(ttl=1800)
def fetch_real_weather(city_name):
    try:
        url = f"https://wttr.in/{quote(city_name)}?format=j1&lang=zh"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        desc = data["current_condition"][0]["lang_zh"][0]["value"]
        
        if "晴" in desc or "Sunny" in desc or "Clear" in desc:
            return "☀️ 晴天"
        elif "雨" in desc or "rain" in desc or "Rain" in desc or "shower" in desc:
            return "🌧️ 雨天"
        elif "雪" in desc or "Snow" in desc or "snow" in desc:
            return "❄️ 雪天"
        elif "风" in desc or "Wind" in desc or "wind" in desc:
            return "💨 大风"
        elif "阴" in desc or "云" in desc or "Cloudy" in desc or "Overcast" in desc:
            return "☁️ 阴天"
        else:
            return f"⛅ {desc}"
            
    except Exception:
        return "☀️ 晴天 (离线兜底)"
# 侧边栏添加天气选择框
weather_options = ["🌍 自动获取实时天气", "☀️ 晴天", "🌧️ 雨天", "☁️ 阴天", "💨 大风"]
weather_choice = st.sidebar.selectbox("天气模式选择", weather_options)

# 判断用户选了什么
if weather_choice == "🌍 自动获取实时天气":
    weather = fetch_real_weather("海口")  # 可以改成你们所在的城市
    st.sidebar.success(f"当前真实天气：{weather}")
else:
    weather = weather_choice
    st.sidebar.info(f"当前手动设定：{weather}")
 # 多站点切换
station_name = st.sidebar.selectbox("选择监测站点", list(STATIONS.keys()))

# 早晚高峰判定
now_hour = datetime.datetime.now().hour
if 7 <= now_hour <= 9:
    peak_text = "🚨 早高峰 (上课时段)"
    peak_weight = 1.3
elif 17 <= now_hour <= 19:
    peak_text = "🚨 晚高峰 (下课/饭点)"
    peak_weight = 1.3
else:
    peak_text = "🟢 平峰期"
    peak_weight = 1.0
st.sidebar.info(f"当前时段：{peak_text}")   
# ================= 3. 核心数据获取区 =================
base_stock = STATIONS[station_name]["base_stock"]
current_stock = base_stock
status_text = "正常"

if mock_status == "自动获取 (传感器)":
    if "sensor" not in st.session_state:
        st.session_state.sensor = SimSensor()
    if "filter" not in st.session_state:
        st.session_state.filter = DebounceFilter()
        
    dist = st.session_state.sensor.read()
    
    if dist is None or st.session_state.filter.is_blind(dist):
        current_stock = -1
        status_text = "异常/盲区"
    else:
        stock = dist_to_stock(dist)
        raw_status = judge_station(stock)
        final_status = st.session_state.filter.filter(raw_status)
        current_stock = stock
        status_text = final_status

elif mock_status == "模拟盲区/断连":
    current_stock = -1 
    status_text = "异常/断连"
    
else:
    if mock_status == "强制缺车":
        current_stock = 5
    elif mock_status == "强制堆积":
        current_stock = 55
    else:
        current_stock = base_stock

# 【重点】应用早晚高峰权重判定
if current_stock != -1:
    if current_stock < 10 * peak_weight:
        status_text = "缺车"
    elif current_stock > 45 * peak_weight:
        status_text = "堆积"
    else:
        status_text = "正常"

# ================= 4. 风险等级判定 =================
if status_text == "缺车":
    color, risk = "🔴", "高"
elif status_text == "堆积":
    color, risk = "🟠", "高"
elif status_text in ["异常/断连", "异常/盲区"]:
    color, risk = "⚫", "未知"
else:
    color, risk = "🟢", "低"

# ================= 5. UI 展示区 =================
col1, col2, col3, col4 = st.columns(4)
col1.metric("当前站点状态", f"{color} {status_text}")

if current_stock == -1:
    col2.metric("当前车辆数", "--- 辆")
else:
    col2.metric("当前车辆数", f"{current_stock} 辆")
    
col3.metric("失衡风险等级", risk)

delay = "0.2 秒" if mode == "DEMO (极速响应)" else "0.8 秒 (去抖中)"
col4.metric("当前天气 / 延迟", f"{weather} / {delay}")

# 报警提示横幅
if status_text == "缺车":
    st.error("🚨 警告：当前站点车辆严重不足，请调度！")
elif status_text == "堆积":
    st.warning("⚠️ 预警：当前站点车辆堆积过多，请清理！")
elif status_text in ["异常/断连", "异常/盲区"]:
    st.info("ℹ️ 提示：传感器信号丢失或处于盲区，请检查硬件！")
else:
    st.success("✅ 当前站点运行平稳。")

# ================= 6. 调度方案展示区 =================
st.subheader("🚚 智能调度方案建议")
if status_text == "缺车":
    # 【核心优化】如果是雨雪恶劣天气，降低调度优先级
    if "雨" in weather or "雪" in weather:
        st.warning(f"💡 调度方案：当前为 {weather}，骑行需求大幅降低。虽然站点缺车，但系统判定无需跨站紧急调拨，建议暂缓调度并做好车辆防护。")
    else:
        # 晴天或阴天，执行正常的联合支援算法
        target_stock = STATIONS[station_name]["base_stock"]
        need_cars = target_stock - current_stock
        
        donation_plan = []
        total_got = 0
        
        # 遍历其他所有站点
        for name, info in STATIONS.items():
            if name == station_name:
                continue # 跳过自己
                
            # 模拟获取其他站点的实时库存
            other_stock = info["base_stock"] + random.randint(-5, 15)
            
            # 【核心】每个站点的专属生命线 = 它自己的 base_stock
            safe_line = info["base_stock"] 
            
            # 富余量：只有高出它自己底线的部分，才能拿出来支援
            available = other_stock - safe_line
            
            if available > 0:
                # 按需提取，不能超过缺口
                take_amount = min(available, need_cars - total_got)
                take_amount = int(take_amount)
                
                if take_amount > 0:
                    donation_plan.append(f"**{name}**({take_amount}辆)")
                    total_got += take_amount
            
            if total_got >= need_cars:
                break
                
        # 生成建议
        if total_got >= need_cars:
            plan_str = " + ".join(donation_plan)
            st.info(f"💡 调度方案：启动多点联合支援！需从 {plan_str} 调入，共计 **{need_cars} 辆**。（系统已测算，各支援站点调出后，依然绝对保有自身原有的基准库存，不影响正常使用）")
        elif total_got > 0:
            plan_str = " + ".join(donation_plan)
            st.warning(f"💡 调度方案：周边站点余量有限。需从 {plan_str} 先调入 **{total_got} 辆**。剩余缺口 **{need_cars - total_got} 辆** 需联系中心仓库派车！")
        else:
            st.error("💡 调度方案：周边所有站点均处于自身基准线或以下，无法跨站调拨。请直接联系中心仓库紧急派车！")
        
elif status_text == "堆积":
    overflow_cars = current_stock - 35
    st.warning(f"💡 调度方案：需将多余的 **{overflow_cars} 辆** 单车调出至其他站点。")
elif status_text in ["异常/断连", "异常/盲区"]:
    st.error("💡 调度方案：硬件异常，无法生成调度建议，请先排查传感器。")
else:
    st.success("💡 调度方案：当前站点供需平衡，暂无调度需求。")

# ================= 7. 天气影响调度建议 =================
if weather == "🌧️ 雨天" or weather == "❄️ 雪天":
    st.info(f"🌦️ 天气预警：当前为 {weather}，骑行需求将大幅降低，建议暂停向该站点调入车辆，并做好车辆防雨雪保护。")
elif weather == "☀️ 晴天":
    st.success(f"🌞 天气预警：当前为 {weather}，适宜骑行，请保持正常调度频率。")
elif weather == "💨 大风":
    st.warning(f"🌬️ 天气预警：当前为 {weather}，存在安全隐患，建议减少调度并检查车辆停放稳固情况。")

# ================= 8. 图表区 =================
st.subheader("📈 近 10 分钟存量趋势")
now = datetime.datetime.now()
times = [(now - datetime.timedelta(minutes=i)).strftime('%H:%M') for i in range(9, -1, -1)]

if current_stock == -1:
    y_data = [np.nan] * 10  # 异常状态折线断开
else:
    y_data = [max(0, current_stock + np.random.randint(-6, 7)) for _ in range(9)]
    y_data.append(current_stock)

chart_data = pd.DataFrame({'车辆存量': y_data}, index=times)
st.line_chart(chart_data, color="#29b5e8")

# ================= 8. 多站点高德地图展示 =================
import streamlit.components.v1 as components
import json

st.markdown("---")
st.subheader("🗺️ 多站点全局分布地图")

try:
    with open("map.html", "r", encoding="utf-8") as f:
        html_data = f.read()
    
    map_data_list = []
    for name, info in STATIONS.items():
        stock_val = current_stock if name == station_name else info["base_stock"]
        display_val = stock_val if stock_val != -1 else "异常"
        map_data_list.append({
            "name": name,
            "position": [info["lon"], info["lat"]],
            "bikeNum": display_val
        })
    
    # 保证中文直接输出，不转义成 \uXXXX
    data_json = json.dumps(map_data_list, ensure_ascii=False)
    
    # 找到 html 里的空数组或者默认数据，直接精准替换！
    # 只要你的 map.html 里写了 var stationList = []; 就能完美替换
    html_data = html_data.replace("var stationList = [];", f"var stationList = {data_json};")

    components.html(html_data, height=500)
    
except FileNotFoundError:
    st.error("⚠️ 找不到 map.html 文件，请确认它和 app.py 是否在同一个文件夹里！")

# ================= 11. 导出调度报表 =================
st.markdown("---")
st.subheader("📄 数据导出区")

report_data = pd.DataFrame({
    "站点名称": [station_name],
    "当前时段": [peak_text],
    "天气状况": [weather],
    "当前车辆数": [current_stock if current_stock != -1 else "异常"],
    "站点状态": [status_text],
    "生成时间": [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
})

# 转换为 CSV 并编码，防止 Excel 打开乱码
csv = report_data.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📥 点击下载当前站点调度报表 (CSV)",
    data=csv,
    file_name=f'{station_name}_调度报表.csv',
    mime='text/csv',
)

# ================= 9. 自动刷新逻辑 =================
if mock_status == "自动获取 (传感器)":
    time.sleep(2)
    st.rerun()