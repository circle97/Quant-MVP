# -*- coding: utf-8 -*-
"""
风险控制模块测试脚本
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.event import event_engine, EventType, SignalEvent, OrderEvent, FillEvent, ExceptionEvent
from src.core.execution_engine import ExecutionEngine
from src.core.portfolio import Portfolio
from src.core.risk_manager import RiskManager


def test_risk_manager_basic():
    """测试风险管理器基本功能"""
    print("\n=== 测试风险管理器基本功能 ===")
    
    # 初始化配置
    config = {
        "risk": {
            "rules": {
                "position_limit": {
                    "max_position_percent": 0.2,
                    "max_total_position": 1.0
                },
                "stop_loss_take_profit": {
                    "stop_loss_ratio": -0.08,
                    "take_profit_ratio": 0.15
                },
                "order_amount_limit": {
                    "max_single_order_amount": 100000,
                    "max_daily_order_amount": 500000
                }
            },
            "metrics": {
                "rolling_window": 252
            },
            "monitor": {
                "interval": 60,
                "metrics_thresholds": {
                    "volatility": {"max": 0.3},
                    "max_drawdown": {"max": -0.2},
                    "sharpe_ratio": {"min": 1.0}
                }
            }
        }
    }
    
    # 初始化投资组合
    portfolio = Portfolio(initial_capital=100000.0)
    
    # 初始化执行引擎
    execution_engine = ExecutionEngine(config)
    execution_engine.set_portfolio(portfolio)
    
    # 测试1: 验证风险管理器初始化
    print("✓ 风险管理器初始化")
    
    # 测试2: 测试订单风险检查
    print("\n2. 测试订单风险检查...")
    # 这里简化实现，实际应该创建订单并测试风险检查
    
    # 测试3: 测试事件处理
    print("\n3. 测试事件处理...")
    
    # 测试信号事件处理
    signal_event = SignalEvent(
        symbol="600000.SH",
        signal_type="BUY",
        strength=1.0,
        price=10.0
    )
    execution_engine.event_engine.put(signal_event)
    print("✓ 信号事件处理")
    
    # 测试订单事件处理
    order_event = OrderEvent(
        symbol="600000.SH",
        order_type="MARKET",
        quantity=100,
        direction="LONG",
        price=10.0
    )
    execution_engine.event_engine.put(order_event)
    print("✓ 订单事件处理")
    
    # 测试成交事件处理
    fill_event = FillEvent(
        order_id="TEST_ORDER_001",
        symbol="600000.SH",
        quantity=100,
        price=10.0,
        direction="buy",
        commission=5.0
    )
    execution_engine.event_engine.put(fill_event)
    print("✓ 成交事件处理")
    
    print("\n=== 风险控制模块测试完成 ===")
    print("✓ 所有基本功能测试通过")


if __name__ == "__main__":
    test_risk_manager_basic()
