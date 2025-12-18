# -*- coding: utf-8 -*-
"""
测试数据持久化和状态恢复功能
"""
import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.event import event_engine, SignalEvent
from src.core.execution_engine import ExecutionEngine
from src.core.portfolio import Portfolio
from src.core.order import Order, OrderType, OrderDirection
from src.strategy.strategy_engine import StrategyEngine
from src.core.state_manager import StateManager
from src.core.transaction_manager import TransactionManager


def test_data_persistence():
    """
    测试数据持久化功能
    """
    print("=" * 60)
    print("测试数据持久化功能")
    print("=" * 60)
    
    # 初始化组件
    db_url = 'sqlite:///test_persistence.db'
    transaction_manager = TransactionManager(db_url=db_url)
    state_manager = StateManager(transaction_manager=transaction_manager)
    portfolio = Portfolio(initial_capital=100000.0)
    execution_engine = ExecutionEngine(config={'mode': 'simulation'})
    
    # 设置执行引擎的投资组合和交易管理器
    execution_engine.set_portfolio(portfolio)
    execution_engine.transaction_manager = transaction_manager
    
    # 创建测试订单
    order1 = Order(
        symbol='600000.SH',
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=100,
        price=10.0
    )
    
    # 提交订单
    order_id = execution_engine.submit_order(order1)
    print(f"提交订单: {order_id}")
    
    # 等待订单处理
    time.sleep(1)
    
    # 检查订单状态
    order = execution_engine.get_order(order_id)
    print(f"订单状态: {order.status}")
    
    # 检查数据库中是否有订单
    saved_order = transaction_manager.get_order(order_id)
    print(f"数据库中订单状态: {saved_order.status}")
    
    # 创建另一个测试订单
    order2 = Order(
        symbol='000001.SZ',
        order_type=OrderType.LIMIT,
        direction=OrderDirection.SELL,
        quantity=200,
        price=20.0
    )
    
    # 提交订单
    order_id2 = execution_engine.submit_order(order2)
    print(f"提交订单: {order_id2}")
    
    # 等待订单处理
    time.sleep(1)
    
    # 取消订单
    execution_engine.cancel_order(order_id2)
    print(f"取消订单: {order_id2}")
    
    # 等待订单处理
    time.sleep(1)
    
    # 检查订单状态
    order = execution_engine.get_order(order_id2)
    print(f"订单状态: {order.status}")
    
    # 检查数据库中是否有取消的订单
    saved_order = transaction_manager.get_order(order_id2)
    print(f"数据库中订单状态: {saved_order.status}")
    
    # 测试投资组合持久化
    print(f"初始投资组合: {portfolio}")
    
    # 保存状态
    saved_count = state_manager.save_state(execution_engine=execution_engine, portfolio=portfolio)
    print(f"保存状态: {saved_count}")
    
    # 测试状态恢复
    print("\n" + "=" * 60)
    print("测试状态恢复功能")
    print("=" * 60)
    
    # 创建新的组件实例
    new_portfolio = Portfolio(initial_capital=50000.0)  # 不同的初始资金
    new_execution_engine = ExecutionEngine(config={'mode': 'simulation'})
    new_execution_engine.set_portfolio(new_portfolio)
    
    print(f"恢复前投资组合: {new_portfolio}")
    print(f"恢复前订单数量: {len(new_execution_engine.get_all_orders())}")
    
    # 恢复状态
    restored_count = state_manager.restore_state(execution_engine=new_execution_engine, portfolio=new_portfolio)
    print(f"恢复状态: {restored_count}")
    
    print(f"恢复后投资组合: {new_portfolio}")
    print(f"恢复后订单数量: {len(new_execution_engine.get_all_orders())}")
    
    # 检查恢复的订单
    orders = new_execution_engine.get_all_orders()
    for order in orders:
        print(f"  - 订单: {order.order_id}, 状态: {order.status}, 标的: {order.symbol}")
    
    # 检查恢复的持仓
    positions = new_portfolio.get_all_positions()
    print(f"恢复后持仓数量: {len(positions)}")
    for position in positions:
        print(f"  - 持仓: {position.symbol}, 数量: {position.quantity}, 均价: {position.avg_price:.2f}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_data_persistence()