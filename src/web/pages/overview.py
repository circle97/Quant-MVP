# -*- coding: utf-8 -*-
"""
总览页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time

from src.web.components.data_fetcher import get_real_portfolio_data, get_real_positions, get_real_trades
from src.web.components.charts import create_fund_chart, create_tickers_table, create_positions_table, create_trades_table

def show_overview():
    """显示总览页面"""
    st.title("Quant-MVP 系统总览")
    
    # 添加配置面板
    with st.expander("总览配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 图表配置
            chart_visibility = st.checkbox("显示图表", value=True)
            auto_refresh = st.checkbox("自动刷新数据", value=False)
            refresh_interval = st.slider("刷新间隔（秒）", min_value=1, max_value=30, value=5) if auto_refresh else 0
        
        with col2:
            # 模拟数据参数
            st.markdown("### 模拟数据参数")
            seed = st.number_input("随机种子", min_value=0, max_value=1000, value=42)
            market_trend = st.slider("市场趋势强度", min_value=-1.0, max_value=1.0, value=0.2, step=0.1)
            volatility = st.slider("波动率", min_value=0.001, max_value=0.05, value=0.01, step=0.001)
    
    # 设置随机种子
    np.random.seed(seed)
    
    # 系统状态栏
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.info("系统状态: 运行中")
    with col2:
        # 生成动态投资组合数据
        base_data = get_real_portfolio_data()
        total_value = base_data['total_value'] * (1 + market_trend + np.random.normal(0, volatility))
        total_return = (total_value - 100000.0) / 100000.0
        daily_return = np.random.normal(market_trend / 252, volatility)
        
        st.markdown(f"### 资金: ¥{total_value:,.2f} | 总收益率: {total_return:.2%} | 当日收益: {daily_return:.2%}")
    with col3:
        st.markdown(f"**更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")
    
    # 初始化会话状态用于存储图表数据
    if 'chart_data' not in st.session_state:
        # 初始资金曲线数据
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        # 生成带有趋势的资金曲线
        trend = np.linspace(0, market_trend, len(dates))
        noise = np.cumsum(np.random.normal(0, volatility, len(dates)))
        values = 100000.0 * (1 + trend + noise)
        st.session_state.chart_data = pd.DataFrame({'date': dates, 'value': values})
    
    # 初始化刷新时间
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = 0
    
    # 检查是否需要更新图表数据
    if auto_refresh and time.time() - st.session_state.last_refresh > refresh_interval:
        # 生成新的数据点并添加到现有数据中
        last_date = st.session_state.chart_data['date'].iloc[-1]
        new_date = last_date + timedelta(days=1)
        last_value = st.session_state.chart_data['value'].iloc[-1]
        new_value = last_value * (1 + market_trend / 252 + np.random.normal(0, volatility))
        
        new_row = pd.DataFrame({'date': [new_date], 'value': [new_value]})
        st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_row], ignore_index=True)
        
        # 保留最近30天的数据
        st.session_state.chart_data = st.session_state.chart_data.tail(30)
        
        # 更新刷新时间
        st.session_state.last_refresh = time.time()
    
    if chart_visibility:
        # 第一行：策略表现图表 + 实时行情
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("策略表现图表")
            st.markdown("#### 投资组合资金曲线")
            st.markdown("该图表展示了投资组合过去30天的资金变化情况，反映了整体策略的盈利能力。")
            create_fund_chart(st.session_state.chart_data)
        
        with col2:
            st.subheader("实时行情")
            st.markdown("#### 主要股票行情")
            st.markdown("展示了市场上主要股票的实时价格、涨跌额和涨跌幅，帮助您了解市场整体情况。")
            create_tickers_table()
        
        # 第二行：当前持仓 + 最近交易
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("当前持仓")
            st.markdown("#### 持仓详情")
            st.markdown("展示了当前投资组合的所有持仓，包括股票代码、持仓数量、平均成本、当前价格、市值和盈亏情况。")
            create_positions_table()
        
        with col2:
            st.subheader("最近交易")
            st.markdown("#### 交易记录")
            st.markdown("展示了最近的交易记录，包括交易时间、股票代码、交易方向、数量、价格和金额。")
            create_trades_table()
