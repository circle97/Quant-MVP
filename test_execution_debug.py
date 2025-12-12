#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试测试交易执行模块功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始调试测试交易执行模块...")

try:
    # 导入核心组件
    from src.core.execution_engine import ExecutionEngine, Order, OrderType, OrderDirection
    from src.core.portfolio import Portfolio
    
    print("✓ 核心组件导入成功！")
    
    # 1. 测试执行引擎初始化
    print("\n1. 测试执行引擎初始化...")
    
    # 执行引擎配置，使用固定滑点和佣金
    config = {
        "mode": "simulation",
        "simulator": {
            "slippage": {
                "type": "fixed",
                "fixed_slippage": 0.01
            },
            "commission": {
                "type": "fixed",
                "fixed_commission": 5.0
            }
        }
    }
    
    # 初始化执行引擎
    execution_engine = ExecutionEngine(config)
    print("✓ 执行引擎初始化成功！")
    
    # 2. 测试投资组合初始化
    print("\n2. 测试投资组合初始化...")
    portfolio = Portfolio(initial_capital=100000.0)
    print(f"✓ 投资组合初始化成功！初始资金: {portfolio.initial_capital:.2f}")
    
    # 3. 测试订单创建
    print("\n3. 测试订单创建...")
    
    # 创建市价买入订单
    buy_order = Order(
        symbol="600000.SH",
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=100,
        price=10.0
    )
    
    print(f"✓ 创建买入订单成功！订单ID: {buy_order.order_id}")
    print(f"  订单详情: {buy_order}")
    
    # 4. 测试订单管理器
    print("\n4. 测试订单管理器...")
    
    # 将订单添加到订单管理器
    execution_engine.order_manager.add_order(buy_order)
    print(f"✓ 订单添加到订单管理器成功！")
    
    # 获取订单
    retrieved_order = execution_engine.order_manager.get_order(buy_order.order_id)
    print(f"✓ 从订单管理器获取订单成功！")
    print(f"  检索到的订单: {retrieved_order}")
    
    # 5. 测试订单状态更新
    print("\n5. 测试订单状态更新...")
    
    from src.core.execution_engine import OrderStatus
    
    # 更新订单状态
    execution_engine.order_manager.update_order_status(buy_order.order_id, OrderStatus.SUBMITTED)
    print(f"✓ 更新订单状态成功！新状态: {retrieved_order.status}")
    
    # 6. 测试订单统计
    print("\n6. 测试订单统计...")
    
    stats = execution_engine.order_manager.get_order_stats()
    print(f"✓ 获取订单统计成功！")
    print(f"  订单统计: {stats}")
    
    # 7. 测试投资组合直接执行订单
    print("\n7. 测试投资组合直接执行订单...")
    
    # 创建一个简单的订单事件用于测试
    from src.core.event import OrderEvent
    
    order_event = OrderEvent(
        symbol="600000.SH",
        order_type="MARKET",
        quantity=100,
        direction="LONG",
        price=10.0
    )
    
    # 直接调用portfolio的execute_order方法
    result = portfolio.execute_order(order_event)
    print(f"✓ 投资组合执行订单成功！结果: {result}")
    
    # 检查投资组合状态
    portfolio_summary = portfolio.get_portfolio_summary()
    print(f"  执行订单后总资产: {portfolio_summary['当前总资产']:.2f}")
    print(f"  可用现金: {portfolio_summary['可用现金']:.2f}")
    print(f"  持仓数量: {portfolio_summary['持仓数量']}")
    
    # 8. 测试投资组合卖出
    print("\n8. 测试投资组合卖出...")
    
    # 创建卖出订单事件
    sell_order_event = OrderEvent(
        symbol="600000.SH",
        order_type="MARKET",
        quantity=100,
        direction="SHORT",
        price=10.5
    )
    
    # 执行卖出订单
    sell_result = portfolio.execute_order(sell_order_event)
    print(f"✓ 投资组合执行卖出订单成功！结果: {sell_result}")
    
    # 检查最终投资组合状态
    final_summary = portfolio.get_portfolio_summary()
    print(f"  卖出后总资产: {final_summary['当前总资产']:.2f}")
    print(f"  可用现金: {final_summary['可用现金']:.2f}")
    print(f"  持仓数量: {final_summary['持仓数量']}")
    
    # 计算收益
    profit = final_summary['当前总资产'] - portfolio.initial_capital
    print(f"  总收益: {profit:.2f}")
    print(f"  收益率: {(profit / portfolio.initial_capital * 100):.2f}%")
    
    print("\n交易执行模块调试测试通过！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n交易执行模块调试测试失败！")

print("\n")
