#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略模拟结果可视化图表
10年历史数据策略回测模拟可视化
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, List, Tuple

# 设置页面配置
st.set_page_config(
    page_title="金融策略模拟结果可视化",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 模拟策略回测数据生成函数
def generate_backtest_data(symbol: str = "^GSPC", years: int = 10) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    生成10年历史数据和模拟交易记录
    
    Args:
        symbol: 股票代码
        years: 历史数据年限
        
    Returns:
        data: 包含价格和策略净值的DataFrame
        trades: 交易记录列表
    """
    # 获取当前日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    # 下载历史数据
    data = yf.download(symbol, start=start_date, end=end_date)
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    
    # 计算策略信号（简单的双均线策略）
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    
    # 生成交易信号
    data['Signal'] = 0
    data['Signal'][50:] = np.where(data['MA50'][50:] > data['MA200'][50:], 1, 0)
    data['Position'] = data['Signal'].diff()
    
    # 模拟交易记录
    trades = []
    position = 0
    initial_capital = 1000000  # 初始资金
    cash = initial_capital
    shares = 0
    
    for i in range(len(data)):
        date = data.index[i]
        close = data['Close'].iloc[i]
        
        if data['Position'].iloc[i] == 1:  # 买入信号
            shares_to_buy = cash // close
            cost = shares_to_buy * close
            cash -= cost
            shares += shares_to_buy
            trades.append({
                'date': date,
                'type': '买入',
                'price': close,
                'quantity': shares_to_buy,
                'total': cost,
                'cash': cash,
                'shares': shares,
                'ma50': data['MA50'].iloc[i],
                'ma200': data['MA200'].iloc[i]
            })
        elif data['Position'].iloc[i] == -1:  # 卖出信号
            if shares > 0:
                proceeds = shares * close
                cash += proceeds
                trades.append({
                    'date': date,
                    'type': '卖出',
                    'price': close,
                    'quantity': shares,
                    'total': proceeds,
                    'cash': cash,
                    'shares': 0,
                    'ma50': data['MA50'].iloc[i],
                    'ma200': data['MA200'].iloc[i]
                })
                shares = 0
    
    # 计算策略净值
    portfolio_value = []
    current_shares = 0
    current_cash = initial_capital
    
    for i in range(len(data)):
        close = data['Close'].iloc[i]
        
        if data['Position'].iloc[i] == 1:  # 买入
            shares_to_buy = current_cash // close
            cost = shares_to_buy * close
            current_cash -= cost
            current_shares += shares_to_buy
        elif data['Position'].iloc[i] == -1:  # 卖出
            if current_shares > 0:
                proceeds = current_shares * close
                current_cash += proceeds
                current_shares = 0
        
        total_value = current_cash + (current_shares * close)
        portfolio_value.append(total_value)
    
    data['Portfolio'] = portfolio_value
    data['Return'] = data['Portfolio'].pct_change().fillna(0)
    data['Cumulative_Return'] = (1 + data['Return']).cumprod()
    
    return data, trades

# 计算绩效指标
def calculate_performance(data: pd.DataFrame, trades: List[Dict], initial_capital: float = 1000000) -> Dict:
    """
    计算策略绩效指标
    
    Args:
        data: 包含策略净值的数据
        trades: 交易记录
        initial_capital: 初始资金
        
    Returns:
        performance: 绩效指标字典
    """
    # 总收益率
    total_return = (data['Portfolio'].iloc[-1] - initial_capital) / initial_capital * 100
    
    # 年化收益率
    years = len(data) / 252  # 假设252个交易日
    annual_return = ((data['Portfolio'].iloc[-1] / initial_capital) ** (1/years) - 1) * 100
    
    # 累计收益金额
    cumulative_profit = data['Portfolio'].iloc[-1] - initial_capital
    
    # 最大回撤
    cumulative = data['Cumulative_Return']
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    # 交易胜率
    win_trades = 0
    total_trades = len(trades)
    
    for i in range(1, len(trades)):
        if trades[i]['type'] == '卖出' and trades[i-1]['type'] == '买入':
            profit = trades[i]['total'] - trades[i-1]['total']
            if profit > 0:
                win_trades += 1
    
    win_rate = (win_trades / (total_trades // 2)) * 100 if total_trades >= 2 else 0
    
    # 平均持仓时间
    if len(trades) >= 2:
        total_holding_days = 0
        trade_pairs = len(trades) // 2
        
        for i in range(trade_pairs):
            buy_date = trades[i*2]['date']
            sell_date = trades[i*2+1]['date']
            total_holding_days += (sell_date - buy_date).days
        
        avg_holding_days = total_holding_days / trade_pairs
    else:
        avg_holding_days = 0
    
    return {
        'initial_capital': initial_capital,
        'final_value': data['Portfolio'].iloc[-1],
        'total_return': total_return,
        'annual_return': annual_return,
        'cumulative_profit': cumulative_profit,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'win_trades': win_trades,
        'avg_holding_days': avg_holding_days
    }

# 主应用
def main():
    st.title("📈 金融策略模拟结果可视化")
    st.markdown("### 10年历史数据策略回测模拟")
    
    # 侧边栏配置
    st.sidebar.header("策略配置")
    symbol = st.sidebar.selectbox(
        "选择标的",
        options=["^GSPC", "^IXIC", "^DJI", "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"],
        index=0
    )
    
    years = st.sidebar.slider(
        "历史数据年限",
        min_value=1,
        max_value=15,
        value=10,
        step=1
    )
    
    # 生成数据
    with st.spinner("正在生成策略回测数据..."):
        data, trades = generate_backtest_data(symbol, years)
        performance = calculate_performance(data, trades)
    
    # 主图表区域
    st.subheader("策略净值曲线与交易信号")
    
    # 创建主图表
    fig = go.Figure()
    
    # 添加价格曲线
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        name="价格",
        line=dict(color='#1f77b4', width=1)
    ))
    
    # 添加50日均线
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['MA50'],
        name="MA50",
        line=dict(color='#2ca02c', width=1, dash='dash')
    ))
    
    # 添加200日均线
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['MA200'],
        name="MA200",
        line=dict(color='#d62728', width=1, dash='dash')
    ))
    
    # 添加策略净值
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Portfolio'],
        name="策略净值",
        yaxis="y2",
        line=dict(color='#9467bd', width=2)
    ))
    
    # 添加买入信号
    buy_signals = data[data['Position'] == 1]
    fig.add_trace(go.Scatter(
        x=buy_signals.index,
        y=buy_signals['Close'],
        name="买入",
        mode="markers",
        marker=dict(
            symbol="triangle-up",
            size=10,
            color="green",
            line=dict(width=2, color="darkgreen")
        )
    ))
    
    # 添加卖出信号
    sell_signals = data[data['Position'] == -1]
    fig.add_trace(go.Scatter(
        x=sell_signals.index,
        y=sell_signals['Close'],
        name="卖出",
        mode="markers",
        marker=dict(
            symbol="triangle-down",
            size=10,
            color="red",
            line=dict(width=2, color="darkred")
        )
    ))
    
    # 配置图表布局
    fig.update_layout(
        title=f"{symbol} 10年策略回测结果",
        xaxis=dict(
            title="日期",
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=3, label="3Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="全部")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis=dict(
            title="价格",
            side="left"
        ),
        yaxis2=dict(
            title="策略净值",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        height=600
    )
    
    # 显示主图表
    st.plotly_chart(fig, use_container_width=True)
    
    # 绩效指标区域
    st.subheader("📊 策略绩效指标")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "总收益率",
            f"{performance['total_return']:.2f}%",
            delta=f"{(performance['total_return'] - 50):.2f}% vs 基准"
        )
    
    with col2:
        st.metric(
            "年化收益率",
            f"{performance['annual_return']:.2f}%",
            delta=f"{(performance['annual_return'] - 8):.2f}% vs 基准"
        )
    
    with col3:
        st.metric(
            "累计收益",
            f"¥{performance['cumulative_profit']:,.0f}"
        )
    
    with col4:
        st.metric(
            "最大回撤",
            f"{performance['max_drawdown']:.2f}%"
        )
    
    with col5:
        st.metric(
            "交易胜率",
            f"{performance['win_rate']:.2f}%"
        )
    
    # 扩展绩效指标
    st.markdown("#### 详细绩效指标")
    performance_expanded = {
        "初始资金": f"¥{performance['initial_capital']:,.0f}",
        "最终市值": f"¥{performance['final_value']:,.0f}",
        "总收益率": f"{performance['total_return']:.2f}%",
        "年化收益率": f"{performance['annual_return']:.2f}%",
        "累计收益金额": f"¥{performance['cumulative_profit']:,.0f}",
        "最大回撤": f"{performance['max_drawdown']:.2f}%",
        "交易胜率": f"{performance['win_rate']:.2f}%",
        "总交易次数": f"{performance['total_trades']}",
        "盈利交易次数": f"{performance['win_trades']}",
        "平均持仓天数": f"{performance['avg_holding_days']:.1f}天"
    }
    
    st.table(performance_expanded)
    
    # 交易记录面板
    st.subheader("📋 交易操作记录")
    
    if trades:
        trades_df = pd.DataFrame(trades)
        trades_df['date'] = trades_df['date'].dt.strftime('%Y-%m-%d')
        trades_df['price'] = trades_df['price'].round(2)
        trades_df['total'] = trades_df['total'].round(2)
        trades_df['cash'] = trades_df['cash'].round(2)
        trades_df['ma50'] = trades_df['ma50'].round(2)
        trades_df['ma200'] = trades_df['ma200'].round(2)
        
        # 表格列重命名
        trades_df = trades_df.rename(columns={
            'date': '交易时间',
            'type': '交易类型',
            'price': '交易价格',
            'quantity': '交易数量',
            'total': '交易金额',
            'cash': '剩余现金',
            'shares': '持仓数量',
            'ma50': 'MA50',
            'ma200': 'MA200'
        })
        
        # 条件格式化
        def highlight_trades(row):
            if row['交易类型'] == '买入':
                return ['background-color: #d4edda'] * len(row)
            elif row['交易类型'] == '卖出':
                return ['background-color: #f8d7da'] * len(row)
            else:
                return [''] * len(row)
        
        # 显示交易记录
        st.dataframe(
            trades_df,
            use_container_width=True,
            height=400
        )
        
        # 交易记录统计
        buy_count = len(trades_df[trades_df['交易类型'] == '买入'])
        sell_count = len(trades_df[trades_df['交易类型'] == '卖出'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"总计买入 {buy_count} 次")
        with col2:
            st.info(f"总计卖出 {sell_count} 次")
    else:
        st.info("暂无交易记录")
    
    # 技术分析面板
    st.subheader("📈 技术分析")
    
    # K线图
    st.markdown("##### K线图")
    kline_fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="K线"
    )])
    
    kline_fig.update_layout(
        xaxis_rangeslider_visible=True,
        title=f"{symbol} K线图",
        height=400
    )
    st.plotly_chart(kline_fig, use_container_width=True)
    
    # 收益曲线
    st.markdown("##### 收益曲线")
    return_fig = go.Figure()
    return_fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Cumulative_Return'],
        name="累计收益率",
        line=dict(color='#9467bd', width=2)
    ))
    
    return_fig.update_layout(
        title="策略累计收益率曲线",
        xaxis_title="日期",
        yaxis_title="累计收益率",
        yaxis_tickformat=".1%",
        height=300
    )
    st.plotly_chart(return_fig, use_container_width=True)
    
    # 风险指标
    st.markdown("##### 风险指标")
    
    # 最大回撤曲线
    cumulative = data['Cumulative_Return']
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    
    drawdown_fig = go.Figure()
    drawdown_fig.add_trace(go.Scatter(
        x=data.index,
        y=drawdown,
        fill='tozeroy',
        name="最大回撤",
        line=dict(color='#d62728', width=1)
    ))
    
    drawdown_fig.update_layout(
        title="最大回撤曲线",
        xaxis_title="日期",
        yaxis_title="回撤比例",
        yaxis_tickformat=".1%",
        height=300
    )
    st.plotly_chart(drawdown_fig, use_container_width=True)

if __name__ == "__main__":
    main()
