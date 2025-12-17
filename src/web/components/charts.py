# -*- coding: utf-8 -*-
"""
图表组件
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def create_fund_chart(chart_data):
    """创建资金曲线图表"""
    fig = px.line(chart_data, x='date', y='value', title='投资组合资金曲线')
    fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
    fig.update_traces(hovertemplate='日期: %{x}<br>资金: ¥%{y:,.2f}')
    fig.update_yaxes(tickformat='¥,.2f')
    st.plotly_chart(fig, width='stretch')

def create_tickers_table():
    """创建实时行情表格"""
    tickers = [
        {"symbol": "AAPL", "name": "苹果", "price": 176.25, "change": 0.43, "change_pct": 0.24},
        {"symbol": "MSFT", "name": "微软", "price": 376.50, "change": -0.75, "change_pct": -0.20},
        {"symbol": "GOOGL", "name": "谷歌", "price": 143.75, "change": 0.88, "change_pct": 0.62},
        {"symbol": "TSLA", "name": "特斯拉", "price": 252.75, "change": 3.50, "change_pct": 1.41},
        {"symbol": "AMZN", "name": "亚马逊", "price": 156.30, "change": 1.20, "change_pct": 0.77},
        {"symbol": "NVDA", "name": "英伟达", "price": 495.80, "change": 8.50, "change_pct": 1.74}
    ]
    
    tickers_df = pd.DataFrame(tickers)
    
    # 设置涨跌颜色
    def color_negative_red(val):
        # 检查值是否为负数
        try:
            num_val = float(val.replace('%', '').replace('¥', ''))
            color = 'red' if num_val < 0 else 'green'
            return f'color: {color}'
        except (ValueError, AttributeError):
            return ''
    
    # 格式化数据
    tickers_df['price'] = tickers_df['price'].map('¥{:.2f}'.format)
    tickers_df['change'] = tickers_df['change'].map('¥{:.2f}'.format)
    tickers_df['change_pct'] = tickers_df['change_pct'].map('{:.2%}'.format)
    
    styled_df = tickers_df.style.map(color_negative_red, subset=['change', 'change_pct'])
    st.dataframe(styled_df, width='stretch', height=300)

def create_positions_table():
    """创建持仓表格"""
    from src.web.components.data_fetcher import get_real_positions
    
    positions = get_real_positions()
    positions_df = pd.DataFrame(positions)
    
    # 调整显示列和格式
    positions_df = positions_df[[
        'symbol', 'name', 'quantity', 'current_price', 'market_value', 'pnl', 'pnl_ratio'
    ]]
    
    # 格式化数据
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
    
    styled_positions = positions_df.style.map(color_negative_red, subset=['pnl', 'pnl_ratio'])
    st.dataframe(styled_positions, width='stretch', height=250)

def create_trades_table():
    """创建交易表格"""
    from src.web.components.data_fetcher import get_real_trades
    
    recent_trades = get_real_trades()
    trades_df = pd.DataFrame(recent_trades)
    
    # 格式化数据
    trades_df['price'] = trades_df['price'].map('¥{:.2f}'.format)
    trades_df['amount'] = trades_df['amount'].map('¥{:.2f}'.format)
    
    # 设置涨跌颜色
    def color_negative_red(val):
        try:
            num_val = float(val.replace('%', '').replace('¥', ''))
            color = 'red' if num_val < 0 else 'green'
            return f'color: {color}'
        except (ValueError, AttributeError):
            return ''
    
    styled_trades = trades_df.style.map(color_negative_red, subset=['amount'])
    st.dataframe(styled_trades, width='stretch', height=250)
