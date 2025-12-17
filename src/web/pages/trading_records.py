# -*- coding: utf-8 -*-
"""
交易记录页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.web.components.data_fetcher import get_real_order_history, get_real_trades

def show_trading_records():
    """显示交易记录页面"""
    st.title("交易记录")
    
    # 添加配置面板
    with st.expander("交易记录配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 显示配置
            record_count = st.slider("显示记录数量", min_value=5, max_value=50, value=20)
            
            # 时间范围过滤
            time_filter = st.selectbox("时间范围", ["所有时间", "最近7天", "最近30天", "最近90天"])
            
            # 交易类型过滤
            trade_type = st.multiselect("交易类型", ["买入", "卖出"], default=["买入", "卖出"])
        
        with col2:
            # 模拟数据参数
            st.markdown("### 模拟数据参数")
            seed = st.number_input("随机种子", min_value=0, max_value=1000, value=42)
            trade_frequency = st.slider("交易频率", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
    
    # 设置随机种子
    np.random.seed(seed)
    
    # 订单历史
    st.subheader("订单历史")
    st.markdown("#### 所有订单记录")
    st.markdown("展示了所有订单的详细信息，包括订单ID、股票代码、订单类型、方向、数量、价格和状态。")
    
    # 获取基础订单数据
    base_orders = get_real_order_history()
    
    # 生成动态订单数据
    orders = []
    for i in range(int(len(base_orders) * trade_frequency)):
        base_order = base_orders[i % len(base_orders)].copy()
        
        # 随机调整订单数量和价格
        quantity_multiplier = np.random.uniform(0.5, 2.0)
        price_multiplier = np.random.uniform(0.95, 1.05)
        
        base_order["quantity"] = int(base_order["quantity"] * quantity_multiplier)
        base_order["price"] = base_order["price"] * price_multiplier
        
        # 随机订单状态
        statuses = ["FILLED", "PARTIALLY_FILLED", "PENDING", "CANCELLED"]
        base_order["status"] = np.random.choice(statuses, p=[0.6, 0.2, 0.1, 0.1])
        
        orders.append(base_order)
    
    orders_df = pd.DataFrame(orders)
    
    # 为订单状态添加颜色
    def color_order_status(val):
        if val == "FILLED":
            return 'background-color: #d4edda; color: #155724'  # 已成交
        elif val == "PARTIALLY_FILLED":
            return 'background-color: #fff3cd; color: #856404'  # 部分成交
        elif val == "PENDING":
            return 'background-color: #cce7ff; color: #004085'  # 待成交
        else:
            return 'background-color: #f8d7da; color: #721c24'  # 其他状态
    
    # 使用map替代applymap以避免警告
    styled_orders = orders_df.style.map(color_order_status, subset=['status'])
    st.dataframe(styled_orders, width='stretch', height=300)
    
    # 成交记录
    st.subheader("成交记录")
    st.markdown("#### 已成交交易")
    st.markdown("展示了所有已成交的交易记录，包括交易时间、股票代码、交易方向、数量、价格和金额。")
    
    # 获取基础交易数据
    base_trades = get_real_trades()
    
    # 生成动态交易数据
    trades = []
    trade_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META", "BABA"]
    
    for i in range(int(len(base_trades) * trade_frequency * 2)):
        # 随机生成交易记录
        trade_time = datetime.now() - timedelta(days=np.random.randint(0, 90), hours=np.random.randint(0, 24))
        symbol = np.random.choice(trade_symbols)
        action = np.random.choice(["买入", "卖出"])
        quantity = np.random.randint(10, 1000)
        price = np.random.uniform(50, 500)
        amount = quantity * price
        
        trades.append({
            "time": trade_time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "amount": amount
        })
    
    trades_df = pd.DataFrame(trades)
    
    # 过滤交易记录
    if time_filter != "所有时间":
        if time_filter == "最近7天":
            cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif time_filter == "最近30天":
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        else:  # 最近90天
            cutoff_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        trades_df = trades_df[trades_df["time"] >= cutoff_date]
    
    if trade_type:
        trades_df = trades_df[trades_df["action"].isin(trade_type)]
    
    # 限制显示数量
    trades_df = trades_df.head(record_count)
    
    # 为交易方向添加颜色
    def color_trade_action(val):
        if val == "买入":
            return 'background-color: #d4edda; color: #155724'  # 买入绿色
        elif val == "卖出":
            return 'background-color: #f8d7da; color: #721c24'  # 卖出红色
        else:
            return ''
    
    # 使用map替代applymap以避免警告
    styled_trades = trades_df.style.map(color_trade_action, subset=['action'])
    st.dataframe(styled_trades, width='stretch', height=300)
    
    # 交易统计
    st.subheader("交易统计")
    st.markdown("#### 交易分析")
    st.markdown("展示了交易的统计信息，包括交易次数、总成交额、买入和卖出的次数及金额。")
    
    # 计算交易统计
    if not trades_df.empty:
        # 总交易次数
        total_trades = len(trades_df)
        
        # 买入和卖出次数
        buy_trades = len(trades_df[trades_df['action'] == '买入'])
        sell_trades = len(trades_df[trades_df['action'] == '卖出'])
        
        # 总成交额
        total_amount = trades_df['amount'].sum()
        
        # 买入和卖出金额
        buy_amount = trades_df[trades_df['action'] == '买入']['amount'].sum()
        sell_amount = trades_df[trades_df['action'] == '卖出']['amount'].sum()
        
        # 统计数据展示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总交易次数", total_trades)
            st.metric("买入次数", buy_trades)
            st.metric("卖出次数", sell_trades)
        
        with col2:
            st.metric("总成交额", f"¥{total_amount:,.2f}")
            st.metric("买入金额", f"¥{buy_amount:,.2f}")
            st.metric("卖出金额", f"¥{sell_amount:,.2f}")
        
        with col3:
            # 交易频率统计
            trade_dates = pd.to_datetime(trades_df['time']).dt.date
            daily_trades = trade_dates.value_counts().sort_index()
            
            if len(daily_trades) > 0:
                st.metric("平均每日交易次数", f"{daily_trades.mean():.1f}")
                st.metric("最多每日交易次数", daily_trades.max())
                st.metric("最少每日交易次数", daily_trades.min())
    
    # 交易金额分布
    st.subheader("交易金额分布")
    st.markdown("#### 交易金额区间统计")
    st.markdown("展示了交易金额在不同区间的分布情况，帮助您了解交易规模的分布特征。")
    
    if not trades_df.empty:
        # 提取交易金额
        trade_amounts = trades_df['amount'].tolist()
        
        # 创建金额区间
        bins = [0, 1000, 5000, 10000, 50000, 100000, float('inf')]
        labels = ['0-1k', '1k-5k', '5k-10k', '10k-50k', '50k-100k', '100k+']
        
        # 分类统计
        amount_dist = pd.cut(trade_amounts, bins=bins, labels=labels, right=False)
        amount_counts = amount_dist.value_counts().sort_index()
        
        # 创建分布图表
        fig = px.bar(x=amount_counts.index, y=amount_counts.values, title="交易金额分布")
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_xaxes(title="金额区间")
        fig.update_yaxes(title="交易次数")
        fig.update_traces(hovertemplate='金额区间: %{x}<br>交易次数: %{y}')
        st.plotly_chart(fig, width='stretch')
