#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试交易执行模块功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始简单测试交易执行模块...")

try:
    # 导入核心组件
    from src.core.execution_engine import ExecutionEngine, Order, OrderType, OrderDirection
    from src.core.portfolio import Portfolio
    from src.core.event import event_engine
    
    print("✓ 核心组件导入成功！")
    
    # 1. 初始化执行引擎
    print("\n1. 初始化执行引擎...")
    execution_engine = ExecutionEngine()
    print("✓ 执行引擎初始化成功！")
    
    # 2. 初始化投资组合
    print("\n2. 初始化投资组合...")
    portfolio = Portfolio(initial_capital=100000.0)
    print(f"✓ 投资组合初始化成功！初始资金: {portfolio.initial_capital:.2f}")
    
    # 3. 启动事件引擎
    print("\n3. 启动事件引擎...")
    event_engine.start()
    print("✓ 事件引擎启动成功！")
    
    # 4. 测试直接创建和提交订单
    print("\n4. 测试直接创建和提交订单...")
    
    # 创建市价买入订单
    buy_order = Order(
        symbol="600000.SH",
        order_type=OrderType.MARKET,
        direction=OrderDirection.BUY,
        quantity=100,
        price=10.0
    )
    
    # 提交订单
    order_id = execution_engine.submit_order(buy_order)
    print(f"✓ 提交买入订单成功！订单ID: {order_id}")
    
    # 等待订单执行
    import time
    time.sleep(1)
    
    # 5. 检查订单状态
    print("\n5. 检查订单状态...")
    order = execution_engine.get_order(order_id)
    print(f"✓ 获取订单成功！订单状态: {order.status}")
    print(f"  订单详情: {order}")
    
    # 6. 检查投资组合状态
    print("\n6. 检查投资组合状态...")
    portfolio_summary = portfolio.get_portfolio_summary()
    print(f"  总资产: {portfolio_summary['当前总资产']:.2f}")
    print(f"  可用现金: {portfolio_summary['可用现金']:.2f}")
    print(f"  持仓数量: {portfolio_summary['持仓数量']}")
    
    # 7. 测试卖出订单
    print("\n7. 测试卖出订单...")
    
    # 创建市价卖出订单
    sell_order = Order(
        symbol="600000.SH",
        order_type=OrderType.MARKET,
        direction=OrderDirection.SELL,
        quantity=100,
        price=10.5
    )
    
    # 提交订单
    sell_order_id = execution_engine.submit_order(sell_order)
    print(f"✓ 提交卖出订单成功！订单ID: {sell_order_id}")
    
    # 等待订单执行
    time.sleep(1)
    
    # 8. 检查最终投资组合状态
    print("\n8. 检查最终投资组合状态...")
    final_summary = portfolio.get_portfolio_summary()
    print(f"  最终总资产: {final_summary['当前总资产']:.2f}")
    print(f"  可用现金: {final_summary['可用现金']:.2f}")
    print(f"  持仓数量: {final_summary['持仓数量']}")
    
    # 计算收益
    profit = final_summary['当前总资产'] - portfolio.initial_capital
    print(f"  总收益: {profit:.2f}")
    print(f"  收益率: {(profit / portfolio.initial_capital * 100):.2f}%")
    
    # 9. 检查订单历史
    print("\n9. 检查订单历史...")
    all_orders = execution_engine.get_all_orders()
    print(f"  总订单数量: {len(all_orders)}")
    for ord in all_orders:
        print(f"  订单: {ord}")
    
    # 停止事件引擎
    event_engine.stop()
    print("\n✓ 事件引擎已停止")
    
    print("\n交易执行模块简单测试通过！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n交易执行模块简单测试失败！")

print("\n测试完成")
