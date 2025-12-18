# -*- coding: utf-8 -*-
"""
策略表现页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.web.components.data_fetcher import get_real_positions

def show_strategy_performance():
    """显示策略表现页面"""
    st.title("策略表现监控")
    
    # 添加配置面板
    with st.expander("策略配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 策略选择
            strategy_list = ["双均线策略", "RSI策略", "MACD策略"]
            selected_strategy = st.selectbox("选择策略", strategy_list)
            
            # 时间范围选择
            time_range = st.radio(
                "时间范围",
                ["最近7天", "最近30天", "最近90天", "最近1年"],
                horizontal=True
            )
        
        with col2:
            # 可配置参数
            st.markdown("### 策略参数")
            
            if selected_strategy == "双均线策略":
                short_window = st.slider("短期均线周期", min_value=5, max_value=50, value=20)
                long_window = st.slider("长期均线周期", min_value=20, max_value=200, value=60)
            elif selected_strategy == "RSI策略":
                rsi_period = st.slider("RSI周期", min_value=5, max_value=30, value=14)
                rsi_overbought = st.slider("超买阈值", min_value=60, max_value=90, value=70)
                rsi_oversold = st.slider("超卖阈值", min_value=10, max_value=40, value=30)
            elif selected_strategy == "MACD策略":
                macd_fast = st.slider("快速EMA周期", min_value=5, max_value=30, value=12)
                macd_slow = st.slider("慢速EMA周期", min_value=10, max_value=50, value=26)
                macd_signal = st.slider("信号线周期", min_value=5, max_value=20, value=9)
        
        # 数据生成参数
        st.markdown("### 模拟数据参数")
        col1, col2 = st.columns(2)
        with col1:
            seed = st.number_input("随机种子", min_value=0, max_value=1000, value=42)
        with col2:
            volatility = st.slider("收益率波动率", min_value=0.001, max_value=0.05, value=0.01, step=0.001)
    
    # 根据时间范围生成数据
    if time_range == "最近7天":
        days = 7
    elif time_range == "最近30天":
        days = 30
    elif time_range == "最近90天":
        days = 90
    else:
        days = 365
    
    # 使用用户配置的随机种子和波动率生成模拟数据
    np.random.seed(seed)
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
    strategy_returns = np.random.normal(0, volatility, len(dates))
    benchmark_returns = np.random.normal(0, volatility * 0.8, len(dates))
    
    df = pd.DataFrame({
        'date': dates,
        '策略收益率': (1 + strategy_returns).cumprod() - 1,
        '基准收益率': (1 + benchmark_returns).cumprod() - 1
    })
    
    # 第一行：策略收益率图表
    st.subheader("策略收益率对比")
    st.markdown("#### 累计收益率曲线")
    st.markdown("展示了所选策略与基准收益率的累计收益对比，帮助您评估策略的超额收益能力。")
    
    fig = px.line(df, x='date', y=['策略收益率', '基准收益率'], title=f'{selected_strategy} vs 基准收益率')
    fig.update_layout(height=400, margin=dict(t=30, b=0, l=0, r=0))
    fig.update_yaxes(tickformat='.1%')
    fig.update_traces(hovertemplate='日期: %{x}<br>收益率: %{y:.2%}')
    st.plotly_chart(fig, width='stretch')
    
    # 第二行：策略绩效指标
    st.subheader("策略绩效指标")
    st.markdown("#### 核心绩效指标")
    st.markdown("展示了策略的核心绩效指标，包括年化收益率、夏普比率、最大回撤等，帮助您全面评估策略表现。")
    
    # 计算绩效指标
    total_strategy_return = df['策略收益率'].iloc[-1]
    total_benchmark_return = df['基准收益率'].iloc[-1]
    
    # 计算年化收益率
    annualized_strategy_return = (1 + total_strategy_return) ** (365 / days) - 1
    annualized_benchmark_return = (1 + total_benchmark_return) ** (365 / days) - 1
    
    # 计算夏普比率（假设无风险利率为0）
    sharpe_ratio = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252) if np.std(strategy_returns) != 0 else 0
    
    # 计算最大回撤
    def calculate_max_drawdown(returns):
        cumulative = (1 + returns).cumprod()
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak
        return drawdown.min()
    
    max_drawdown = calculate_max_drawdown(strategy_returns)
    
    # 模拟绩效指标
    performance_metrics = {
        "年化收益率": annualized_strategy_return * 100,
        "基准年化收益率": annualized_benchmark_return * 100,
        "夏普比率": sharpe_ratio,
        "最大回撤": max_drawdown * 100,
        "胜率": np.mean(strategy_returns > 0) * 100,
        "盈亏比": np.abs(np.mean(strategy_returns[strategy_returns > 0])) / np.abs(np.mean(strategy_returns[strategy_returns < 0])) if np.mean(strategy_returns[strategy_returns < 0]) != 0 else 0,
        "交易次数": int(np.random.uniform(10, 50))
    }
    
    # 组织绩效指标为三列布局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("年化收益率", f"{performance_metrics.get('年化收益率', 12.5):.2f}%")
        st.metric("基准年化收益率", f"{performance_metrics.get('基准年化收益率', 10.0):.2f}%")
    
    with col2:
        st.metric("夏普比率", f"{performance_metrics.get('夏普比率', 1.85):.2f}")
        st.metric("最大回撤", f"{performance_metrics.get('最大回撤', -8.2):.2f}%")
    
    with col3:
        st.metric("胜率", f"{performance_metrics.get('胜率', 58.3):.1f}%")
        st.metric("盈亏比", f"{performance_metrics.get('盈亏比', 1.42):.2f}")
    
    # 第三行：策略表现细节
    st.subheader("策略表现细节")
    
    # 策略收益分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 收益分布")
        st.markdown("展示了策略的日收益率分布情况，帮助您了解策略的收益风险特征。")
        # 生成模拟的日收益率分布
        daily_returns = np.random.normal(0, volatility, 1000)
        fig = px.histogram(daily_returns, title="日收益率分布", nbins=50)
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_xaxes(tickformat='.1%')
        fig.update_yaxes(title="频数")
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("#### 月度收益")
        st.markdown("展示了策略在过去12个月的月度收益率表现，帮助您了解策略的季节性特征。")
        # 生成模拟的月度收益数据
        months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
        monthly_returns = np.random.normal(annualized_strategy_return / 12, volatility * 2, 12)
        
        fig = px.bar(x=months, y=monthly_returns, title="月度收益率")
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_yaxes(tickformat='.1%')
        fig.update_traces(hovertemplate='月份: %{x}<br>收益率: %{y:.2%}')
        st.plotly_chart(fig, width='stretch')
    
    # 第四行：策略持仓分布
    st.subheader("策略持仓分布")
    st.markdown("#### 持仓占比分布")
    st.markdown("展示了策略当前的持仓分布情况，帮助您了解策略的行业和个股集中度。")
    
    # 获取持仓数据
    positions = get_real_positions()
    if positions:
        # 计算持仓占比
        total_value = sum(pos['market_value'] for pos in positions)
        pie_data = [pos['market_value'] for pos in positions]
        pie_labels = [f"{pos['symbol']} ({pos['name']})" for pos in positions]
        
        fig = px.pie(values=pie_data, names=pie_labels, title="持仓分布")
        fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_traces(textinfo='label+percent', hovertemplate='%{label}<br>市值: ¥%{value:,.2f}<br>占比: %{percent}')
        st.plotly_chart(fig, width='stretch')
    else:
        # 模拟持仓数据
        pie_data = [35, 25, 20, 15, 5]
        pie_labels = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        
        fig = px.pie(values=pie_data, names=pie_labels, title="模拟持仓分布")
        fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')
