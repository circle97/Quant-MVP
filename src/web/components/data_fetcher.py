# -*- coding: utf-8 -*-
"""
数据获取组件
"""
from src.web.components.api_client import APIClient

# 初始化API客户端
api_client = APIClient()

def get_real_portfolio_data():
    """从API获取投资组合数据"""
    portfolio_data = api_client.get_portfolio_summary()
    
    if not portfolio_data:
        # 返回默认数据，防止页面崩溃
        return {
            "total_value": 100000.0,
            "cash": 100000.0,
            "position_value": 0.0,
            "daily_return": 0.0,
            "total_return": 0.0
        }
    
    data = {
        "total_value": portfolio_data.get("total_value", 100000.0),
        "cash": portfolio_data.get("cash", 100000.0),
        "position_value": portfolio_data.get("total_value", 100000.0) - portfolio_data.get("cash", 100000.0),
        "daily_return": portfolio_data.get("daily_return", 0.0),
        "total_return": portfolio_data.get("total_return", 0.0) / 100  # 转换为小数
    }
    return data

def get_real_positions():
    """从API获取持仓数据"""
    positions = api_client.get_positions()
    
    # 转换持仓数据格式
    formatted_positions = []
    for pos in positions:
        # 计算盈亏比例
        pnl_ratio = (pos.get("current_price", 0) - pos.get("avg_price", 0)) / pos.get("avg_price", 1) if pos.get("avg_price", 0) != 0 else 0
        
        pos_dict = {
            "symbol": pos.get("symbol", ""),
            "name": pos.get("symbol", ""),  # 简化处理，实际应从行情获取
            "quantity": pos.get("quantity", 0),
            "avg_price": pos.get("avg_price", 0),
            "current_price": pos.get("current_price", 0),
            "market_value": pos.get("market_value", 0),
            "pnl": pos.get("unrealized_pnl", 0),
            "pnl_ratio": pnl_ratio
        }
        formatted_positions.append(pos_dict)
    
    # 如果没有持仓，返回模拟数据
    if not formatted_positions:
        formatted_positions = [
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
    
    return formatted_positions

def get_real_order_history():
    """从API获取订单历史"""
    orders = api_client.get_orders()
    
    # 转换订单数据格式
    formatted_orders = []
    for order in orders:
        order_dict = {
            "order_id": order.get("order_id", ""),
            "symbol": order.get("symbol", ""),
            "order_type": order.get("order_type", ""),
            "direction": order.get("direction", ""),
            "quantity": order.get("quantity", 0),
            "price": order.get("price", 0),
            "status": order.get("status", ""),
            "create_time": order.get("create_time", ""),
            "fill_time": order.get("fill_time", "")
        }
        formatted_orders.append(order_dict)
    
    # 如果没有订单，返回模拟数据
    if not formatted_orders:
        formatted_orders = [
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
    
    return formatted_orders

def get_real_risk_metrics():
    """从API获取风险指标"""
    performance_data = api_client.get_performance_metrics()
    
    if not performance_data:
        # 返回默认风险指标
        return {
            "volatility": 0.15,
            "sharpe_ratio": 1.8,
            "max_drawdown": -0.08,
            "var_95": -0.025,
            "var_99": -0.045,
            "calmar_ratio": 2.2
        }
    
    metrics = {
        "volatility": performance_data.get("annual_volatility", 15.0) / 100,  # 转换为小数
        "sharpe_ratio": performance_data.get("sharpe_ratio", 1.8),
        "max_drawdown": performance_data.get("max_drawdown", -8.0) / 100,  # 转换为小数
        "var_95": -0.025,  # 暂未实现VaR计算
        "var_99": -0.045,  # 暂未实现VaR计算
        "calmar_ratio": performance_data.get("annual_return", 12.5) / abs(performance_data.get("max_drawdown", 8.0)) if abs(performance_data.get("max_drawdown", 0)) != 0 else 2.2
    }
    return metrics

def get_real_trades():
    """从API获取交易记录（目前使用订单历史代替，后续需要添加交易记录API）"""
    # 目前使用订单历史作为交易记录，后续需要添加专门的交易记录API
    orders = api_client.get_orders()
    
    # 转换订单为交易记录格式
    trades = []
    for order in orders:
        if order.get("status") == "FILLED":
            trade_dict = {
                "time": order.get("fill_time", order.get("create_time", "")),
                "symbol": order.get("symbol", ""),
                "action": order.get("direction", ""),
                "quantity": order.get("filled_quantity", order.get("quantity", 0)),
                "price": order.get("avg_fill_price", order.get("price", 0)),
                "amount": order.get("avg_fill_price", order.get("price", 0)) * order.get("filled_quantity", order.get("quantity", 0))
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
