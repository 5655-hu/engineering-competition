import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="校园单车潮汐调度系统", layout="wide", page_icon="🚲")
st.title("🚲 校园共享单车潮汐站点感知系统")
st.markdown("---")

st.sidebar.header("🔧 系统控制 (测试/降级)")
mode = st.sidebar.radio("运行模式", ["DEMO (极速响应)", "PRODUCTION (去抖过滤)"])
mock_status = st.sidebar.selectbox("模拟测试场景", ["自动获取 (传感器)", "强制缺车", "强制正常", "强制堆积"])

# ================= 核心数据获取区 =================
if mock_status == "自动获取 (传感器)":
    # 【重点】这里现在是模拟真实数据，后续由B提供函数替换
    current_stock = 35  # 暂时写死，等B给接口
    status_text = "正常" # 暂时写死，等B给接口
else:
    # 降级演示模式（纯手工控制，用于评委提问或硬件坏掉时）
    current_stock = 5 if mock_status == "强制缺车" else 35 if mock_status == "强制正常" else 60
    if current_stock < 10:
        status_text = "缺车"
    elif current_stock > 40:
        status_text = "堆积"
    else:
        status_text = "正常"

# 判定风险等级
if status_text == "缺车":
    color, risk = "red", "高"
elif status_text == "堆积":
    color, risk = "orange", "高"
else:
    color, risk = "green", "低"

# ================= UI 展示区 =================
col1, col2, col3, col4 = st.columns(4)
col1.metric("当前站点状态", status_text)
col2.metric("当前车辆数", f"{current_stock} 辆")
col3.metric("失衡风险等级", risk)
col4.metric("系统响应延迟", "0.2 秒")

st.subheader("📈 近 10 分钟存量趋势")
# 这里后续可以接入真实的数据库（SQLite）
chart_data = pd.DataFrame(np.random.randn(20, 1) * 5 + 25, columns=['车辆存量'])
st.line_chart(chart_data)

st.subheader("🎯 调度决策与触发")
if status_text != "正常":
    st.error(f"⚠️ 警告：当前站点处于【{status_text}】状态，请立即处理！")
    if st.button("生成调度工单并触发声光报警"):
        st.success("✅ 工单已生成：建议调拨 10 辆车。LED 与蜂鸣器已触发！")
else:
    st.success("✅ 当前站点状态正常，无需调度。")