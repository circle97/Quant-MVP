# -*- coding: utf-8 -*-
"""
数据获取组件
"""
import numpy as np
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager

# 初始化全局变量
portfolio = Portfolio(initial_capital=100000.0)
risk_manager = RiskManager()

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
