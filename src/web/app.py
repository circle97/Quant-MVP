# -*- coding: utf-8 -*-
"""
Quant-MVP 监控面板主应用
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# 设置页面配置
st.set_page_config(
    page_title="Quant-MVP 监控面板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入自定义模块
from src.core.portfolio import Portfolio
from src.core.event import event_engine
from src.core.risk_manager import RiskManager

# 初始化全局变量
portfolio = Portfolio(initial_capital=100000.0)
risk_manager = RiskManager()

# 辅助函数
def get_real_portfolio_data():
    """从投资组合对象获取真实数据"""
    summary = portfolio.get_portfolio_summary()
    
    data = {
        "total_value": summary['当前总资产'],
        "cash": summary['可用现金'],
        "position_value": summary['持仓市值'],
        "daily_return": 0.0,  # 暂未实现每日收益计算
        "total_return": summary['总收益率'] / 100  # 转换为小数
    }
    return data

def get_real_positions():
    """从投资组合对象获取真实持仓数据"""
    positions = []
    for position in portfolio.get_all_positions():
        # 计算盈亏比例
        pnl_ratio = (position.current_price - position.avg_price) / position.avg_price if position.avg_price != 0 else 0
        
        pos_dict = {
            "symbol": position.symbol,
            "name": position.symbol,  # 简化处理，实际应从行情获取
            "quantity": position.quantity,
            "avg_price": position.avg_price,
            "current_price": position.current_price,
            "market_value": position.market_value,
            "pnl": position.unrealized_pnl,
            "pnl_ratio": pnl_ratio
        }
        positions.append(pos_dict)
    
    # 如果没有持仓，返回模拟数据
    if not positions:
        positions = [
            {
                "symbol": "AAPL",
                "name": "苹果",
                "quantity": 100,
                "avg_price": 175.50,
                "current_price": 176.25,
                "market_value": 17625.0,
                "pnl": 75.0,
                "pnl_ratio": 0.0043
            },
            {
                "symbol": "MSFT",
                "name": "微软",
                "quantity": 50,
                "avg_price": 378.00,
                "current_price": 376.50,
                "market_value": 18825.0,
                "pnl": -75.0,
                "pnl_ratio": -0.0040
            },
            {
                "symbol": "GOOGL",
                "name": "谷歌",
                "quantity": 30,
                "avg_price": 142.50,
                "current_price": 143.75,
                "market_value": 4312.5,
                "pnl": 37.5,
                "pnl_ratio": 0.0088
            },
            {
                "symbol": "TSLA",
                "name": "特斯拉",
                "quantity": 20,
                "avg_price": 248.00,
                "current_price": 252.75,
                "market_value": 5055.0,
                "pnl": 95.0,
                "pnl_ratio": 0.0191
            }
        ]
    
    return positions

def get_real_order_history():
    """获取订单历史（目前返回模拟数据）"""
    # TODO: 从订单管理器获取真实订单历史
    orders = [
        {
            "order_id": "ORDER_20251216103000",
            "symbol": "AAPL",
            "order_type": "MARKET",
            "direction": "BUY",
            "quantity": 100,
            "price": 175.50,
            "status": "FILLED",
            "create_time": "2025-12-16 10:30:00",
            "fill_time": "2025-12-16 10:30:01"
        },
        {
            "order_id": "ORDER_20251216111500",
            "symbol": "MSFT",
            "order_type": "LIMIT",
            "direction": "BUY",
            "quantity": 50,
            "price": 378.00,
            "status": "FILLED",
            "create_time": "2025-12-16 11:15:00",
            "fill_time": "2025-12-16 11:15:05"
        }
    ]
    return orders

def get_real_risk_metrics():
    """从风险管理器获取真实风险指标"""
    # 计算投资组合的风险指标
    performance_metrics = portfolio.get_performance_metrics()
    
    metrics = {
        "volatility": performance_metrics.get("年化波动率", 0.15) / 100,  # 转换为小数
        "sharpe_ratio": performance_metrics.get("夏普比率", 1.8),
        "max_drawdown": performance_metrics.get("最大回撤", -8.0) / 100,  # 转换为小数
        "var_95": -0.025,  # 暂未实现VaR计算
        "var_99": -0.045,  # 暂未实现VaR计算
        "calmar_ratio": performance_metrics.get("年化收益率", 12.5) / abs(performance_metrics.get("最大回撤", 8.0)) if performance_metrics.get("最大回撤", 0) != 0 else 2.2
    }
    return metrics

def get_real_trades():
    """从投资组合获取真实交易记录"""
    # 获取交易记录
    trades = []
    for trade in portfolio.trades:
        trade_dict = {
            "time": trade['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": trade['symbol'],
            "action": trade['action'],
            "quantity": trade['quantity'],
            "price": trade['price'],
            "amount": trade['trade_value']
        }
        trades.append(trade_dict)
    
    # 如果没有交易记录，返回模拟数据
    if not trades:
        trades = [
            {
                "time": "2025-12-16 10:30:01",
                "symbol": "AAPL",
                "action": "买入",
                "quantity": 100,
                "price": 175.50,
                "amount": 17550.0
            },
            {
                "time": "2025-12-16 11:15:05",
                "symbol": "MSFT",
                "action": "买入",
                "quantity": 50,
                "price": 378.00,
                "amount": 18900.0
            },
            {
                "time": "2025-12-13 14:22:18",
                "symbol": "GOOGL",
                "action": "卖出",
                "quantity": 20,
                "price": 141.80,
                "amount": 2836.0
            },
            {
                "time": "2025-12-12 09:45:33",
                "symbol": "TSLA",
                "action": "买入",
                "quantity": 20,
                "price": 248.00,
                "amount": 4960.0
            }
        ]
    
    return trades

# 模拟数据生成函数（作为后备）
def generate_dummy_portfolio_data():
    """生成模拟投资组合数据"""
    data = {
        "total_value": 100000.0 + np.random.normal(0, 500, 1)[0],
        "cash": 30000.0 + np.random.normal(0, 1000, 1)[0],
        "position_value": 70000.0 + np.random.normal(0, 2000, 1)[0],
        "daily_return": np.random.normal(0, 0.01, 1)[0],
        "total_return": (100000.0 + np.random.normal(0, 500, 1)[0]) / 100000.0 - 1
    }
    return data

def generate_dummy_positions():
    """生成模拟持仓数据"""
    positions = [
        {
            "symbol": "AAPL",
            "name": "苹果",
            "quantity": 100,
            "avg_price": 175.50,
            "current_price": 176.25,
            "market_value": 17625.0,
            "pnl": 75.0,
            "pnl_ratio": 0.0043
        },
        {
            "symbol": "MSFT",
            "name": "微软",
            "quantity": 50,
            "avg_price": 378.00,
            "current_price": 376.50,
            "market_value": 18825.0,
            "pnl": -75.0,
            "pnl_ratio": -0.0040
        },
        {
            "symbol": "GOOGL",
            "name": "谷歌",
            "quantity": 30,
            "avg_price": 142.50,
            "current_price": 143.75,
            "market_value": 4312.5,
            "pnl": 37.5,
            "pnl_ratio": 0.0088
        },
        {
            "symbol": "TSLA",
            "name": "特斯拉",
            "quantity": 20,
            "avg_price": 248.00,
            "current_price": 252.75,
            "market_value": 5055.0,
            "pnl": 95.0,
            "pnl_ratio": 0.0191
        }
    ]
    return positions

def generate_dummy_order_history():
    """生成模拟订单历史"""
    orders = [
        {
            "order_id": "ORDER_20251216103000",
            "symbol": "AAPL",
            "order_type": "MARKET",
            "direction": "BUY",
            "quantity": 100,
            "price": 175.50,
            "status": "FILLED",
            "create_time": "2025-12-16 10:30:00",
            "fill_time": "2025-12-16 10:30:01"
        },
        {
            "order_id": "ORDER_20251216111500",
            "symbol": "MSFT",
            "order_type": "LIMIT",
            "direction": "BUY",
            "quantity": 50,
            "price": 378.00,
            "status": "FILLED",
            "create_time": "2025-12-16 11:15:00",
            "fill_time": "2025-12-16 11:15:05"
        }
    ]
    return orders

def generate_dummy_risk_metrics():
    """生成模拟风险指标"""
    metrics = {
        "volatility": 0.15 + np.random.normal(0, 0.02, 1)[0],
        "sharpe_ratio": 1.8 + np.random.normal(0, 0.2, 1)[0],
        "max_drawdown": -0.08 + np.random.normal(0, 0.01, 1)[0],
        "var_95": -0.025 + np.random.normal(0, 0.005, 1)[0],
        "var_99": -0.045 + np.random.normal(0, 0.008, 1)[0],
        "calmar_ratio": 2.2 + np.random.normal(0, 0.3, 1)[0]
    }
    return metrics

# 侧边栏设置
st.sidebar.header("Quant-MVP 监控面板")

# 选择页面
page = st.sidebar.radio(
    "选择监控页面",
    [
        "总览",
        "投资组合",
        "策略表现",
        "风险监控",
        "交易记录",
        "系统状态"
    ]
)

# 系统状态栏
st.sidebar.markdown("---")
st.sidebar.subheader("系统状态")
st.sidebar.info("运行中")

# 主页面内容
if page == "总览":
    st.title("Quant-MVP 系统总览")
    
    # 系统状态栏
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.info("系统状态: 运行中")
    with col2:
        portfolio_data = get_real_portfolio_data()
        st.markdown(f"### 资金: ¥{portfolio_data['total_value']:,.2f} | 总收益率: {portfolio_data['total_return']:.2%} | 当日收益: {portfolio_data['daily_return']:.2%}")
    with col3:
        st.markdown(f"**更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")
    
    # 初始化会话状态用于存储图表数据
    if 'chart_data' not in st.session_state:
        # 初始资金曲线数据
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        values = 100000.0 + np.cumsum(np.random.normal(0, 200, len(dates)))
        st.session_state.chart_data = pd.DataFrame({'date': dates, 'value': values})
    
    # 自动刷新设置（仅图表）
    auto_refresh = st.sidebar.checkbox("图表自动刷新", value=False)
    refresh_interval = st.sidebar.slider("刷新间隔（秒）", min_value=1, max_value=30, value=5) if auto_refresh else 0
    
    # 初始化刷新时间
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = 0
    
    # 检查是否需要更新图表数据
    if auto_refresh and time.time() - st.session_state.last_refresh > refresh_interval:
        # 生成新的数据点并添加到现有数据中
        last_date = st.session_state.chart_data['date'].iloc[-1]
        new_date = last_date + timedelta(days=1)
        last_value = st.session_state.chart_data['value'].iloc[-1]
        new_value = last_value + np.random.normal(0, 200)
        
        new_row = pd.DataFrame({'date': [new_date], 'value': [new_value]})
        st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_row], ignore_index=True)
        
        # 保留最近30天的数据
        st.session_state.chart_data = st.session_state.chart_data.tail(30)
        
        # 更新刷新时间
        st.session_state.last_refresh = time.time()
    
    # 第一行：策略表现图表 + 实时行情
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("策略表现图表")
        # 为资金曲线创建占位符
        fund_chart_placeholder = st.empty()
        
        # 创建图表
        fig = px.line(st.session_state.chart_data, x='date', y='value', title='投资组合资金曲线')
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fund_chart_placeholder.plotly_chart(fig, width='stretch', key='fund_chart')
    
    with col2:
        st.subheader("实时行情")
        tickers_table_placeholder = st.empty()
        
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
        tickers_table_placeholder.dataframe(styled_df, width='stretch', height=300)
    
    # 第二行：当前持仓 + 最近交易
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("当前持仓")
        positions_table_placeholder = st.empty()
        
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
        
        styled_positions = positions_df.style.map(color_negative_red, subset=['pnl', 'pnl_ratio'])
        positions_table_placeholder.dataframe(styled_positions, width='stretch', height=250)
    
    with col2:
        st.subheader("最近交易")
        trades_table_placeholder = st.empty()
        
        recent_trades = get_real_trades()
        trades_df = pd.DataFrame(recent_trades)
        
        # 格式化数据
        trades_df['price'] = trades_df['price'].map('¥{:.2f}'.format)
        trades_df['amount'] = trades_df['amount'].map('¥{:.2f}'.format)
        
        styled_trades = trades_df.style.map(color_negative_red, subset=['amount'])
        trades_table_placeholder.dataframe(styled_trades, width='stretch', height=250)

# 其他页面的基本框架
elif page == "投资组合":
    st.title("投资组合管理")
    # 投资组合详细信息
    st.subheader("投资组合概况")
    portfolio_data = generate_dummy_portfolio_data()
    st.json(portfolio_data)
    
    st.subheader("持仓详情")
    positions = generate_dummy_positions()
    positions_df = pd.DataFrame(positions)
    st.dataframe(positions_df, width='stretch')

elif page == "策略表现":
    st.title("策略表现监控")
    
    # 策略选择（如果有多个策略）
    strategy_list = ["双均线策略", "RSI策略", "MACD策略"]
    selected_strategy = st.selectbox("选择策略", strategy_list)
    
    # 时间范围选择
    time_range = st.radio(
        "时间范围",
        ["最近7天", "最近30天", "最近90天", "最近1年"],
        horizontal=True
    )
    
    # 第一行：策略收益率图表
    st.subheader("策略收益率对比")
    
    # 根据时间范围生成数据
    if time_range == "最近7天":
        days = 7
    elif time_range == "最近30天":
        days = 30
    elif time_range == "最近90天":
        days = 90
    else:
        days = 365
    
    # 生成模拟数据
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
    strategy_returns = np.random.normal(0, 0.01, len(dates))
    benchmark_returns = np.random.normal(0, 0.008, len(dates))
    
    df = pd.DataFrame({
        'date': dates,
        '策略收益率': (1 + strategy_returns).cumprod() - 1,
        '基准收益率': (1 + benchmark_returns).cumprod() - 1
    })
    
    fig = px.line(df, x='date', y=['策略收益率', '基准收益率'], title=f'{selected_strategy} vs 基准收益率')
    fig.update_layout(height=400, margin=dict(t=30, b=0, l=0, r=0))
    fig.update_yaxes(tickformat='.1%')
    st.plotly_chart(fig, width='stretch')
    
    # 第二行：策略绩效指标
    st.subheader("策略绩效指标")
    
    # 从投资组合获取真实绩效指标
    performance_metrics = portfolio.get_performance_metrics()
    
    # 如果没有真实数据，使用模拟数据
    if not performance_metrics:
        performance_metrics = {
            "年化收益率": 12.5,
            "夏普比率": 1.85,
            "最大回撤": -8.2,
            "胜率": 58.3,
            "盈亏比": 1.42,
            "交易次数": 24
        }
    
    # 组织绩效指标为三列布局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("年化收益率", f"{performance_metrics.get('年化收益率', 12.5):.2f}%")
        st.metric("夏普比率", f"{performance_metrics.get('夏普比率', 1.85):.2f}")
    
    with col2:
        st.metric("最大回撤", f"{performance_metrics.get('最大回撤', -8.2):.2f}%")
        st.metric("胜率", f"{performance_metrics.get('胜率', 58.3):.1f}%")
    
    with col3:
        st.metric("盈亏比", f"{performance_metrics.get('盈亏比', 1.42):.2f}")
        st.metric("交易次数", f"{performance_metrics.get('交易次数', 24)}")
    
    # 第三行：策略表现细节
    st.subheader("策略表现细节")
    
    # 策略收益分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**收益分布**")
        # 生成模拟的日收益率分布
        daily_returns = np.random.normal(0, 0.01, 1000)
        fig = px.histogram(daily_returns, title="日收益率分布")
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.write("**月度收益**")
        # 生成模拟的月度收益数据
        months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
        monthly_returns = np.random.normal(0.01, 0.02, 12)
        
        fig = px.bar(x=months, y=monthly_returns, title="月度收益率")
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_yaxes(tickformat='.1%')
        st.plotly_chart(fig, width='stretch')
    
    # 第四行：策略持仓分布
    st.subheader("策略持仓分布")
    
    # 获取持仓数据
    positions = get_real_positions()
    if positions:
        # 计算持仓占比
        total_value = sum(pos['market_value'] for pos in positions)
        pie_data = [pos['market_value'] for pos in positions]
        pie_labels = [pos['symbol'] for pos in positions]
        
        fig = px.pie(values=pie_data, names=pie_labels, title="持仓分布")
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')
    else:
        # 模拟持仓数据
        pie_data = [35, 25, 20, 15, 5]
        pie_labels = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        
        fig = px.pie(values=pie_data, names=pie_labels, title="模拟持仓分布")
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')

elif page == "风险监控":
    st.title("风险监控")
    
    # 第一行：风险指标概览
    st.subheader("风险指标概览")
    
    # 获取风险指标
    risk_metrics = get_real_risk_metrics()
    
    # 组织风险指标为两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("波动率", f"{risk_metrics['volatility']:.2%}")
        st.metric("夏普比率", f"{risk_metrics['sharpe_ratio']:.2f}")
        st.metric("最大回撤", f"{risk_metrics['max_drawdown']:.2%}")
    
    with col2:
        st.metric("VaR 95%", f"{risk_metrics['var_95']:.2%}")
        st.metric("VaR 99%", f"{risk_metrics['var_99']:.2%}")
        st.metric("卡玛比率", f"{risk_metrics['calmar_ratio']:.2f}")
    
    # 第二行：风险预警和限制
    st.subheader("风险预警")
    
    # 模拟风险预警数据
    risk_alerts = [
        {"指标": "最大回撤", "当前值": "-8.20%", "阈值": "-10.00%", "状态": "正常"},
        {"指标": "波动率", "当前值": "15.20%", "阈值": "20.00%", "状态": "正常"},
        {"指标": "VaR 95%", "当前值": "-2.50%", "阈值": "-5.00%", "状态": "正常"},
        {"指标": "单日亏损", "当前值": "-1.20%", "阈值": "-3.00%", "状态": "正常"}
    ]
    
    alerts_df = pd.DataFrame(risk_alerts)
    st.dataframe(alerts_df, width='stretch')
    
    # 第三行：风险暴露分析
    st.subheader("风险暴露分析")
    
    # 生成模拟的风险暴露数据
    exposure_data = [
        {"资产类别": "股票", "占比": 0.75, "风险贡献": 0.80},
        {"资产类别": "债券", "占比": 0.15, "风险贡献": 0.10},
        {"资产类别": "现金", "占比": 0.10, "风险贡献": 0.05}
    ]
    
    exposure_df = pd.DataFrame(exposure_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 风险暴露饼图
        fig = px.pie(exposure_df, values='占比', names='资产类别', title='资产配置')
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # 风险贡献条形图
        fig = px.bar(exposure_df, x='资产类别', y='风险贡献', title='风险贡献')
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_yaxes(tickformat='.1%')
        st.plotly_chart(fig, width='stretch')

elif page == "交易记录":
    st.title("交易记录")
    
    # 订单历史
    st.subheader("订单历史")
    orders = get_real_order_history()
    orders_df = pd.DataFrame(orders)
    st.dataframe(orders_df, width='stretch')
    
    # 成交记录
    st.subheader("成交记录")
    trades = get_real_trades()
    trades_df = pd.DataFrame(trades)
    st.dataframe(trades_df, width='stretch')

elif page == "系统状态":
    st.title("系统状态监控")
    
    # 系统信息
    st.subheader("系统信息")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Python版本", sys.version.split()[0])
        st.metric("Streamlit版本", st.__version__)
    
    with col2:
        st.metric("CPU使用率", f"{np.random.randint(10, 50)}%")
        st.metric("内存使用率", f"{np.random.randint(30, 70)}%")
    
    with col3:
        st.metric("运行时长", "24h 30m")
        st.metric("事件数量", "1,245")
    
    # 组件状态
    st.subheader("组件状态")
    
    components = [
        {"组件": "策略引擎", "状态": "运行中", "最后活跃": "刚刚"},
        {"组件": "订单管理器", "状态": "运行中", "最后活跃": "1分钟前"},
        {"组件": "风险管理器", "状态": "运行中", "最后活跃": "30秒前"},
        {"组件": "数据服务", "状态": "运行中", "最后活跃": "5秒前"}
    ]
    
    components_df = pd.DataFrame(components)
    st.dataframe(components_df, width='stretch')
    
    # 日志信息
    st.subheader("系统日志")
    
    # 生成模拟日志
    logs = [
        {"时间": "2025-12-16 19:43:50", "级别": "INFO", "内容": "初始化投资组合，初始资金: 100000.00"},
        {"时间": "2025-12-16 19:43:50", "级别": "INFO", "内容": "初始化风险管理器"},
        {"时间": "2025-12-16 19:43:59", "级别": "DEBUG", "内容": "注册事件处理器: fill -> handle_fill"},
        {"时间": "2025-12-16 19:44:00", "级别": "INFO", "内容": "系统运行正常"}
    ]
    
    logs_df = pd.DataFrame(logs)
    st.dataframe(logs_df, width='stretch')

# 手动刷新按钮
if st.sidebar.button("刷新数据"):
    st.rerun()
