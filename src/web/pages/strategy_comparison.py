# -*- coding: utf-8 -*-
"""
策略选择与对比功能页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import copy

from src.web.components.data_fetcher import get_real_positions

# 导入策略相关模块
from src.strategy.base import Strategy, AStockTradingStrategy
from src.strategy.ma_cross_strategy import MACrossStrategy, EnhancedMACrossStrategy
from src.strategy.strategy_loader import StrategyLoader
from src.strategy.strategy_manager import StrategyManager

# 模拟策略列表
AVAILABLE_STRATEGIES = {
    "双均线策略": {
        "class": MACrossStrategy,
        "description": "基于短期和长期均线交叉信号的趋势跟踪策略",
        "parameters": {
            "short_window": 20,
            "long_window": 60,
            "signal_strength": 1.0
        },
        "features": ["趋势跟踪", "简单易用", "适合中长线"]
    },
    "增强版双均线策略": {
        "class": EnhancedMACrossStrategy,
        "description": "在双均线基础上增加了波动率过滤和资金管理的增强策略",
        "parameters": {
            "short_window": 15,
            "long_window": 50,
            "volatility_window": 20,
            "signal_strength": 1.0
        },
        "features": ["趋势跟踪", "波动率过滤", "资金管理", "适合中线"]
    },
    "RSI策略": {
        "class": None,
        "description": "基于相对强弱指标的超买超卖策略",
        "parameters": {
            "rsi_period": 14,
            "overbought": 70,
            "oversold": 30,
            "signal_strength": 1.0
        },
        "features": ["超买超卖", "适合短线", "震荡行情有效"]
    },
    "MACD策略": {
        "class": None,
        "description": "基于移动平均收敛发散指标的趋势和动量策略",
        "parameters": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "signal_strength": 1.0
        },
        "features": ["趋势识别", "动量跟踪", "适合中短线"]
    }
}

# 评估指标权重配置
DEFAULT_WEIGHTS = {
    "年化收益率": 0.3,
    "夏普比率": 0.25,
    "最大回撤": 0.2,
    "胜率": 0.15,
    "盈亏比": 0.1
}

# 模拟测试数据生成
def generate_test_data(days=30, symbols=["AAPL", "MSFT"]):
    """生成模拟测试数据"""
    data = {}
    for symbol in symbols:
        # 生成日期序列
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), end=datetime.now(), freq='D')
        
        # 生成模拟价格数据
        base_price = 100 + np.random.uniform(0, 50)
        trend = np.linspace(0, np.random.uniform(-0.2, 0.5), len(dates))
        volatility = np.random.uniform(0.01, 0.05)
        noise = np.cumsum(np.random.normal(0, volatility, len(dates)))
        prices = base_price * (1 + trend + noise)
        
        # 生成OHLC数据
        ohlc_data = pd.DataFrame({
            'date': dates,
            'open': prices * np.random.uniform(0.99, 1.01, len(prices)),
            'high': prices * np.random.uniform(1.0, 1.02, len(prices)),
            'low': prices * np.random.uniform(0.98, 1.0, len(prices)),
            'close': prices,
            'volume': np.random.uniform(1000000, 10000000, len(prices))
        })
        
        data[symbol] = ohlc_data
    
    return data

# 模拟策略运行
def run_strategy_simulation(strategy_name, params, test_data, initial_capital=100000.0):
    """模拟策略运行"""
    # 模拟运行结果
    days = len(next(iter(test_data.values())))
    
    # 生成模拟收益曲线
    volatility = np.random.uniform(0.01, 0.03)
    trend = np.random.uniform(-0.1, 0.3)  # 年化趋势
    daily_returns = np.random.normal(trend / 252, volatility, days)
    cumulative_returns = (1 + daily_returns).cumprod() - 1
    equity_curve = initial_capital * (1 + cumulative_returns)
    
    # 计算绩效指标
    annual_return = trend
    sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) != 0 else 0
    
    # 计算最大回撤
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    max_drawdown = np.min(drawdown)
    
    # 模拟胜率和盈亏比
    wins = len(daily_returns[daily_returns > 0])
    losses = len(daily_returns[daily_returns < 0])
    win_rate = wins / len(daily_returns) if len(daily_returns) > 0 else 0
    
    avg_win = np.mean(daily_returns[daily_returns > 0]) if wins > 0 else 0
    avg_loss = np.abs(np.mean(daily_returns[daily_returns < 0])) if losses > 0 else 1
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
    
    # 模拟交易次数
    trades = int(np.random.uniform(5, 50))
    
    # 生成模拟持仓
    positions = []
    for symbol in test_data.keys():
        positions.append({
            "symbol": symbol,
            "name": symbol,
            "quantity": int(np.random.uniform(10, 1000)),
            "avg_price": np.random.uniform(80, 120),
            "current_price": np.random.uniform(80, 120),
            "market_value": np.random.uniform(5000, 50000),
            "pnl": np.random.uniform(-1000, 5000),
            "pnl_ratio": np.random.uniform(-0.1, 0.2)
        })
    
    # 模拟信号和订单
    signals = int(np.random.uniform(10, 100))
    orders = int(np.random.uniform(5, 50))
    fills = int(np.random.uniform(5, 50))
    
    return {
        "strategy_name": strategy_name,
        "params": params,
        "equity_curve": equity_curve,
        "daily_returns": daily_returns,
        "dates": [d.strftime("%Y-%m-%d") for d in next(iter(test_data.values()))['date']],
        "performance": {
            "年化收益率": annual_return * 100,
            "夏普比率": sharpe_ratio,
            "最大回撤": max_drawdown * 100,
            "胜率": win_rate * 100,
            "盈亏比": profit_loss_ratio,
            "交易次数": trades,
            "信号数量": signals,
            "订单数量": orders,
            "成交数量": fills
        },
        "final_value": equity_curve[-1],
        "total_return": cumulative_returns[-1] * 100,
        "positions": positions
    }

# 策略评估与评分
def evaluate_strategies(results, weights=DEFAULT_WEIGHTS):
    """评估策略并生成评分"""
    # 计算每个指标的最高分（用于归一化）
    max_scores = {}
    for metric in weights.keys():
        values = [res["performance"][metric] for res in results]
        if metric == "最大回撤":
            # 最大回撤是负数，我们希望它尽可能大（接近0）
            max_scores[metric] = abs(min(values))
        else:
            max_scores[metric] = max(values)
    
    # 计算每个策略的综合评分
    for res in results:
        score = 0
        normalized_scores = {}
        
        for metric, weight in weights.items():
            value = res["performance"][metric]
            
            if metric == "最大回撤":
                # 最大回撤是负数，归一化为0-1，越大越好
                normalized = (abs(value) / max_scores[metric]) if max_scores[metric] != 0 else 0
            else:
                # 其他指标归一化为0-1，越大越好
                normalized = (value / max_scores[metric]) if max_scores[metric] != 0 else 0
            
            normalized_scores[metric] = normalized
            score += normalized * weight
        
        res["normalized_scores"] = normalized_scores
        res["total_score"] = score
    
    # 按总分排序
    sorted_results = sorted(results, key=lambda x: x["total_score"], reverse=True)
    
    return sorted_results

def show_strategy_comparison():
    """显示策略选择与对比页面"""
    st.title("策略选择与对比")
    
    # 页面配置
    with st.expander("配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 选择策略
            selected_strategies = st.multiselect(
                "选择要比较的策略",
                list(AVAILABLE_STRATEGIES.keys()),
                default=["双均线策略", "增强版双均线策略"]
            )
            
            # 测试参数
            initial_capital = st.number_input("初始资金", min_value=10000.0, max_value=1000000.0, value=100000.0, step=10000.0)
            test_days = st.slider("测试天数", min_value=7, max_value=365, value=30, step=7)
            
            # 测试标的
            test_symbols = st.multiselect(
                "测试标的",
                ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA"],
                default=["AAPL", "MSFT"]
            )
        
        with col2:
            # 评估权重配置
            st.markdown("### 评估权重配置")
            weights = {}
            for metric, default_weight in DEFAULT_WEIGHTS.items():
                weights[metric] = st.slider(
                    metric,
                    min_value=0.0, max_value=1.0, value=default_weight, step=0.05
                )
            
            # 归一化权重
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v / total_weight for k, v in weights.items()}
            
            st.markdown(f"**权重总和**: {sum(weights.values()):.2f}")
    
    # 策略配置面板
    if selected_strategies:
        st.subheader("策略配置")
        strategy_params = {}
        
        for strategy_name in selected_strategies:
            with st.expander(f"{strategy_name} 参数", expanded=False):
                strategy_info = AVAILABLE_STRATEGIES[strategy_name]
                params = {}
                
                for param_name, default_value in strategy_info["parameters"].items():
                    # 根据参数类型选择合适的控件
                    if isinstance(default_value, int):
                        params[param_name] = st.slider(
                            param_name,
                            min_value=int(default_value * 0.5),
                            max_value=int(default_value * 2),
                            value=default_value,
                            step=1,
                            key=f"{strategy_name}_{param_name}"
                        )
                    else:
                        params[param_name] = st.slider(
                            param_name,
                            min_value=float(default_value * 0.5),
                            max_value=float(default_value * 2),
                            value=float(default_value),
                            step=0.1,
                            key=f"{strategy_name}_{param_name}"
                        )
                
                strategy_params[strategy_name] = params
        
        # 运行测试按钮
        if st.button("运行策略对比测试"):
            with st.spinner("正在运行策略测试..."):
                # 生成测试数据
                test_data = generate_test_data(days=test_days, symbols=test_symbols)
                
                # 运行每个策略
                results = []
                for strategy_name in selected_strategies:
                    result = run_strategy_simulation(
                        strategy_name=strategy_name,
                        params=strategy_params[strategy_name],
                        test_data=test_data,
                        initial_capital=initial_capital
                    )
                    results.append(result)
                
                # 评估策略
                evaluated_results = evaluate_strategies(results, weights)
                
                # 存储结果到会话状态
                st.session_state["strategy_comparison_results"] = evaluated_results
                st.session_state["test_symbols"] = test_symbols
    
    # 显示结果
    if "strategy_comparison_results" in st.session_state:
        results = st.session_state["strategy_comparison_results"]
        test_symbols = st.session_state["test_symbols"]
        
        # 结果概览
        st.subheader("策略对比结果概览")
        
        # 绩效指标对比表格
        st.markdown("#### 绩效指标对比")
        performance_data = []
        for result in results:
            row = {"策略名称": result["strategy_name"]}
            row.update(result["performance"])
            row["最终市值"] = result["final_value"]
            row["总收益率"] = result["total_return"]
            row["综合评分"] = result["total_score"] * 100
            performance_data.append(row)
        
        performance_df = pd.DataFrame(performance_data)
        
        # 格式化数据
        format_dict = {
            "年化收益率": "{:.2f}%",
            "夏普比率": "{:.2f}",
            "最大回撤": "{:.2f}%",
            "胜率": "{:.1f}%",
            "盈亏比": "{:.2f}",
            "最终市值": "¥{:,.2f}",
            "总收益率": "{:.2f}%",
            "综合评分": "{:.1f}"
        }
        
        styled_df = performance_df.style.format(format_dict)
        st.dataframe(styled_df, width='stretch')
        
        # 收益曲线对比
        st.subheader("收益曲线对比")
        
        # 准备数据
        curve_data = []
        for result in results:
            for i, (date, value) in enumerate(zip(result["dates"], result["equity_curve"])):
                curve_data.append({
                    "日期": date,
                    "策略": result["strategy_name"],
                    "市值": value
                })
        
        curve_df = pd.DataFrame(curve_data)
        
        fig = px.line(curve_df, x="日期", y="市值", color="策略", title="策略收益曲线对比")
        fig.update_layout(height=400, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_yaxes(tickformat='¥,.2f')
        fig.update_traces(hovertemplate='日期: %{x}<br>市值: ¥%{y:,.2f}')
        st.plotly_chart(fig, width='stretch')
        
        # 绩效指标雷达图
        st.subheader("绩效指标雷达图")
        
        radar_data = []
        metrics = list(DEFAULT_WEIGHTS.keys())
        
        for result in results:
            for metric in metrics:
                # 归一化值（用于雷达图）
                normalized_value = result["normalized_scores"][metric]
                radar_data.append({
                    "策略": result["strategy_name"],
                    "指标": metric,
                    "归一化值": normalized_value
                })
        
        radar_df = pd.DataFrame(radar_data)
        
        fig = px.line_polar(
            radar_df, 
            r="归一化值", 
            theta="指标", 
            color="策略",
            line_close=True,
            title="策略绩效指标对比"
        )
        fig.update_layout(height=400, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, width='stretch')
        
        # 策略排名和推荐
        st.subheader("策略排名与推荐")
        
        # 排名表格
        rank_data = []
        for i, result in enumerate(results):
            rank_data.append({
                "排名": i + 1,
                "策略名称": result["strategy_name"],
                "综合评分": result["total_score"] * 100,
                "最终市值": result["final_value"],
                "总收益率": result["total_return"],
                "年化收益率": result["performance"]["年化收益率"],
                "夏普比率": result["performance"]["夏普比率"],
                "最大回撤": result["performance"]["最大回撤"]
            })
        
        rank_df = pd.DataFrame(rank_data)
        styled_rank_df = rank_df.style.format({
            "综合评分": "{:.1f}",
            "最终市值": "¥{:,.2f}",
            "总收益率": "{:.2f}%",
            "年化收益率": "{:.2f}%",
            "夏普比率": "{:.2f}",
            "最大回撤": "{:.2f}%"
        })
        st.dataframe(styled_rank_df, width='stretch')
        
        # 推荐报告
        st.subheader("策略推荐报告")
        
        best_strategy = results[0]
        st.markdown(f"### 推荐策略: {best_strategy['strategy_name']}")
        st.markdown(f"**综合评分**: {best_strategy['total_score'] * 100:.1f}")
        st.markdown(f"**推荐理由**:")
        st.markdown(f"1. 在所有测试策略中综合评分最高，表现最优")
        st.markdown(f"2. 年化收益率达到 {best_strategy['performance']['年化收益率']:.2f}%")
        st.markdown(f"3. 夏普比率为 {best_strategy['performance']['夏普比率']:.2f}，风险调整后收益优秀")
        st.markdown(f"4. 最大回撤控制在 {best_strategy['performance']['最大回撤']:.2f}%，风险可控")
        st.markdown(f"5. 胜率为 {best_strategy['performance']['胜率']:.1f}%，盈亏比为 {best_strategy['performance']['盈亏比']:.2f}，交易质量较高")
        
        # 策略参数建议
        st.markdown("### 建议参数配置:")
        param_df = pd.DataFrame([{
            "参数名称": k,
            "建议值": v
        } for k, v in best_strategy['params'].items()])
        st.dataframe(param_df, width='stretch')
        
        # 适合场景
        strategy_info = AVAILABLE_STRATEGIES[best_strategy['strategy_name']]
        st.markdown("### 适合场景:")
        for feature in strategy_info['features']:
            st.markdown(f"- {feature}")
        
        # 风险提示
        st.markdown("### 风险提示:")
        st.markdown("1. 历史回测结果不代表未来表现")
        st.markdown("2. 不同市场环境下策略表现可能差异较大")
        st.markdown("3. 建议结合其他分析方法使用")
        st.markdown("4. 实盘交易中需注意滑点、手续费等成本影响")
        
        # 详细结果展开
        st.subheader("详细结果")
        for result in results:
            with st.expander(f"{result['strategy_name']} 详细结果", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 绩效指标")
                    perf_df = pd.DataFrame([{
                        "指标": k,
                        "值": v
                    } for k, v in result['performance'].items()])
                    st.dataframe(perf_df, width='stretch')
                
                with col2:
                    st.markdown("#### 最终持仓")
                    pos_df = pd.DataFrame(result['positions'])
                    styled_pos = pos_df.style.format({
                        "avg_price": "¥{:.2f}",
                        "current_price": "¥{:.2f}",
                        "market_value": "¥{:.2f}",
                        "pnl": "¥{:.2f}",
                        "pnl_ratio": "{:.2%}"
                    })
                    st.dataframe(styled_pos, width='stretch')
    
    # 策略信息展示
    st.subheader("可用策略信息")
    for strategy_name, info in AVAILABLE_STRATEGIES.items():
        with st.expander(f"{strategy_name}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**描述**: {info['description']}")
                st.markdown("**特点**:")
                for feature in info['features']:
                    st.markdown(f"- {feature}")
            
            with col2:
                st.markdown("**默认参数**:")
                default_params_df = pd.DataFrame([{
                    "参数": k,
                    "默认值": v
                } for k, v in info['parameters'].items()])
                st.dataframe(default_params_df, width='stretch')
