#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试交易执行模块功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始测试交易执行模块...")

try:
    # 导入交易执行模块组件
    from src.core.execution_engine import ExecutionEngine
    from src.core.portfolio import Portfolio
    from src.core.event import SignalEvent, event_engine
    from src.data.data_manager import AStockDataManager
    
    print("✓ 交易执行模块组件导入成功！")
    
    # 1. 测试执行引擎初始化
    print("\n1. 测试执行引擎初始化...")
    
    # 执行引擎配置
    config = {
        "mode": "simulation",
        "simulator": {
            "slippage": {
                "type": "percentage",
                "percentage_slippage": 0.001
            },
            "commission": {
                "type": "percentage",
                "percentage_commission": 0.0003,
                "min_commission": 5.0
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
    
    # 3. 测试数据管理器初始化
    print("\n3. 测试数据管理器初始化...")
    data_manager = AStockDataManager()
    print("✓ 数据管理器初始化成功！")
    
    # 4. 测试事件引擎启动
    print("\n4. 测试事件引擎启动...")
    event_engine.start()
    print("✓ 事件引擎启动成功！")
    
    # 5. 测试信号生成与订单执行
    print("\n5. 测试信号生成与订单执行...")
    
    # 生成一个买入信号
    signal_event = SignalEvent(
        symbol="600000.SH",
        signal_type="BUY",
        strength=0.8,
        price=10.0
    )
    
    # 将信号放入事件引擎
    event_engine.put(signal_event)
    print(f"✓ 生成并发送买入信号: {signal_event}")
    
    # 等待事件处理
    import time
    time.sleep(0.5)
    
    # 6. 测试投资组合更新
    print("\n6. 测试投资组合更新...")
    portfolio_summary = portfolio.get_portfolio_summary()
    print(f"  投资组合摘要: {portfolio_summary}")
    
    # 检查是否有持仓
    positions = portfolio.get_all_positions()
    print(f"  持仓数量: {len(positions)}")
    for pos in positions:
        print(f"  持仓: {pos}")
    
    # 7. 测试卖出信号
    print("\n7. 测试卖出信号...")
    
    # 生成一个卖出信号
    sell_signal = SignalEvent(
        symbol="600000.SH",
        signal_type="SELL",
        strength=0.8,
        price=10.5
    )
    
    # 将信号放入事件引擎
    event_engine.put(sell_signal)
    print(f"✓ 生成并发送卖出信号: {sell_signal}")
    
    # 等待事件处理
    time.sleep(0.5)
    
    # 8. 测试最终投资组合状态
    print("\n8. 测试最终投资组合状态...")
    final_summary = portfolio.get_portfolio_summary()
    print(f"  最终投资组合摘要: {final_summary}")
    
    final_positions = portfolio.get_all_positions()
    print(f"  最终持仓数量: {len(final_positions)}")
    for pos in final_positions:
        print(f"  最终持仓: {pos}")
    
    # 9. 测试订单历史
    print("\n9. 测试订单历史...")
    orders = execution_engine.get_all_orders()
    print(f"  订单数量: {len(orders)}")
    for order in orders:
        print(f"  订单: {order}")
    
    # 10. 测试执行引擎统计信息
    print("\n10. 测试执行引擎统计信息...")
    order_stats = execution_engine.order_manager.get_order_stats()
    print(f"  订单统计: {order_stats}")
    
    # 停止事件引擎
    event_engine.stop()
    print("\n✓ 事件引擎已停止")
    
    print("\n交易执行模块测试通过！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n交易执行模块测试失败！")

print("\n测试完成！")
