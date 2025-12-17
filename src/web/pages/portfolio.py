# -*- coding: utf-8 -*-
"""
投资组合页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.web.components.data_fetcher import get_real_portfolio_data, get_real_positions

def show_portfolio():
    """显示投资组合页面"""
    st.title("投资组合管理")
    
    # 添加配置面板
    with st.expander("投资组合配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 初始资金配置
            initial_capital = st.number_input("初始资金", min_value=10000.0, max_value=1000000.0, value=100000.0, step=10000.0)
            
            # 现金比例配置
            cash_ratio = st.slider("现金持有比例", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        
        with col2:
            # 模拟数据参数
            st.markdown("### 模拟数据参数")
            seed = st.number_input("随机种子", min_value=0, max_value=1000, value=42)
            market_trend = st.slider("市场趋势强度", min_value=-1.0, max_value=1.0, value=0.2, step=0.1)
            volatility = st.slider("波动率", min_value=0.001, max_value=0.05, value=0.01, step=0.001)
    
    # 设置随机种子
    np.random.seed(seed)
    
    # 投资组合概况
    st.subheader("投资组合概况")
    st.markdown("#### 资金分配")
    st.markdown("展示了投资组合的资金分布情况，包括总资产、可用现金和持仓市值。")
    
    # 获取基础投资组合数据
    base_data = get_real_portfolio_data()
    
    # 根据配置生成动态数据
    position_value = initial_capital * (1 - cash_ratio) * (1 + market_trend + np.random.normal(0, volatility))
    cash = initial_capital * cash_ratio * (1 + np.random.normal(0, volatility))
    total_value = position_value + cash
    total_return = (total_value - initial_capital) / initial_capital
    daily_return = np.random.normal(market_trend / 252, volatility)
    
    portfolio_data = {
        "total_value": total_value,
        "cash": cash,
        "position_value": position_value,
        "daily_return": daily_return,
        "total_return": total_return
    }
    
    # 创建资金分布饼图
    fund_distribution = pd.DataFrame({
        '类别': ['可用现金', '持仓市值'],
        '金额': [portfolio_data['cash'], portfolio_data['position_value']]
    })
    
    fig = px.pie(fund_distribution, values='金额', names='类别', title='资金分布', 
                color_discrete_sequence=['#3498db', '#2ecc71'])
    fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
    fig.update_traces(textinfo='value+percent', texttemplate='¥%{value:.2f} (%{percent:.1%})')
    st.plotly_chart(fig, width='stretch')
    
    # 投资组合关键指标
    st.subheader("投资组合关键指标")
    st.markdown("#### 绩效指标")
    st.markdown("展示了投资组合的核心绩效指标，包括总收益率、当日收益和风险水平。")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总资产", f"¥{portfolio_data['total_value']:,.2f}")
    with col2:
        st.metric("总收益率", f"{portfolio_data['total_return']:.2%}")
    with col3:
        st.metric("当日收益", f"{portfolio_data['daily_return']:.2%}")
    
    # 持仓详情
    st.subheader("持仓详情")
    st.markdown("#### 持仓列表")
    st.markdown("展示了当前投资组合的所有持仓详情，包括股票代码、名称、持仓数量、平均成本、当前价格、市值和盈亏情况。")
    
    # 获取基础持仓数据
    base_positions = get_real_positions()
    
    # 生成动态持仓数据
    positions = []
    for pos in base_positions:
        # 应用市场趋势和波动率
        price_change = market_trend + np.random.normal(0, volatility)
        current_price = pos['avg_price'] * (1 + price_change)
        pnl = (current_price - pos['avg_price']) * pos['quantity']
        pnl_ratio = pnl / (pos['avg_price'] * pos['quantity']) if pos['avg_price'] * pos['quantity'] != 0 else 0
        market_value = current_price * pos['quantity']
        
        # 按比例调整市值以匹配目标持仓总市值
        adjusted_quantity = int(pos['quantity'] * (position_value / sum(p['market_value'] for p in base_positions)))
        adjusted_market_value = current_price * adjusted_quantity
        adjusted_pnl = (current_price - pos['avg_price']) * adjusted_quantity
        adjusted_pnl_ratio = adjusted_pnl / (pos['avg_price'] * adjusted_quantity) if pos['avg_price'] * adjusted_quantity != 0 else 0
        
        positions.append({
            "symbol": pos["symbol"],
            "name": pos["name"],
            "quantity": adjusted_quantity,
            "avg_price": pos["avg_price"],
            "current_price": current_price,
            "market_value": adjusted_market_value,
            "pnl": adjusted_pnl,
            "pnl_ratio": adjusted_pnl_ratio
        })
    
    positions_df = pd.DataFrame(positions)
    
    # 调整显示列和格式
    positions_df = positions_df[[
        'symbol', 'name', 'quantity', 'avg_price', 'current_price', 'market_value', 'pnl', 'pnl_ratio'
    ]]
    
    # 格式化数据
    positions_df['avg_price'] = positions_df['avg_price'].map('¥{:.2f}'.format)
    positions_df['current_price'] = positions_df['current_price'].map('¥{:.2f}'.format)
    positions_df['market_value'] = positions_df['market_value'].map('¥{:.2f}'.format)
    positions_df['pnl'] = positions_df['pnl'].map('¥{:.2f}'.format)
    positions_df['pnl_ratio'] = positions_df['pnl_ratio'].map('{:.2%}'.format)
    
    # 设置涨跌颜色
    def color_negative_red(val):
        try:
            num_val = float(val.replace('%', '').replace('¥', ''))
            color = 'red' if num_val < 0 else 'green'
            return f'color: {color}'
        except (ValueError, AttributeError):
            return ''
    
    # 使用map替代applymap以避免警告
    styled_df = positions_df.style.map(color_negative_red, subset=['pnl', 'pnl_ratio'])
    st.dataframe(styled_df, width='stretch', height=400)
    
    # 持仓分布
    st.subheader("持仓分布")
    st.markdown("#### 持仓占比")
    st.markdown("展示了各持仓股票在投资组合中的占比情况，帮助您了解投资组合的集中度。")
    
    if positions:
        # 计算持仓占比
        total_value = sum(float(pos['market_value'].replace('¥', '').replace(',', '')) for pos in positions_df.to_dict('records'))
        pie_data = [float(pos['market_value'].replace('¥', '').replace(',', '')) for pos in positions_df.to_dict('records')]
        pie_labels = [f"{pos['symbol']} ({pos['name']})" for pos in positions_df.to_dict('records')]
        
        fig = px.pie(values=pie_data, names=pie_labels, title="持仓分布")
        fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_traces(textinfo='label+percent')
        st.plotly_chart(fig, width='stretch')
