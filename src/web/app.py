# -*- coding: utf-8 -*-
"""
Quant-MVP 监控面板主应用
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

# 设置页面配置
st.set_page_config(
    page_title="Quant-MVP 监控面板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入页面模块
from src.web.pages.overview import show_overview
from src.web.pages.portfolio import show_portfolio
from src.web.pages.strategy_performance import show_strategy_performance
from src.web.pages.strategy_comparison import show_strategy_comparison
from src.web.pages.risk_monitoring import show_risk_monitoring
from src.web.pages.trading_records import show_trading_records
from src.web.pages.system_status import show_system_status

# 导入侧边栏组件
from src.web.components.sidebar import sidebar

# 选择页面
page = sidebar()

# 根据选择显示不同页面
if page == "总览":
    show_overview()
elif page == "投资组合":
    show_portfolio()
elif page == "策略表现":
    show_strategy_performance()
elif page == "策略对比":
    show_strategy_comparison()
elif page == "风险监控":
    show_risk_monitoring()
elif page == "交易记录":
    show_trading_records()
elif page == "系统状态":
    show_system_status()

# 手动刷新按钮
if st.sidebar.button("刷新数据"):
    st.rerun()
