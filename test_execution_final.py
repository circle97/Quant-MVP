#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
最终测试交易执行模块功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始测试交易执行模块...")

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
    
    # 5. 测试订单统计
    print("\n5. 测试订单统计...")
    
    stats = execution_engine.order_manager.get_order_stats()
    print(f"✓ 获取订单统计成功！")
    print(f"  订单统计: {stats}")
    
    # 6. 测试执行引擎提交订单
    print("\n6. 测试执行引擎提交订单...")
    
    # 创建一个新的买入订单
    new_buy_order = Order(
        symbol="600001.SH",
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=200,
        price=20.0
    )
    
    # 提交订单
    order_id = execution_engine.submit_order(new_buy_order)
    print(f"✓ 提交订单成功！订单ID: {order_id}")
    
    # 7. 测试订单历史查询
    print("\n7. 测试订单历史查询...")
    
    all_orders = execution_engine.get_all_orders()
    print(f"✓ 查询所有订单成功！订单数量: {len(all_orders)}")
    
    for order in all_orders:
        print(f"  订单: {order}")
    
    print("\n交易执行模块测试通过！")
    print("\n测试完成！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n交易执行模块测试失败！")
    print("\n测试完成！")
