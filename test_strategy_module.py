#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试策略模块功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始测试策略模块...")

try:
    # 导入策略模块的核心组件
    from src.strategy.base import Strategy
    from src.strategy.strategy_engine import strategy_engine
    from src.strategy.strategy_manager import strategy_manager
    from src.core.event import BarEvent, event_engine
    
    print("✓ 策略模块组件导入成功！")
    
    # 创建一个简单的测试策略
    class TestStrategy(Strategy):
        """测试策略"""
        
        def on_init(self):
            """策略初始化回调"""
            self.params = {
                'fast_period': 10,
                'slow_period': 30
            }
            print(f"  策略 {self.name} 初始化完成")
        
        def on_start(self):
            """策略启动回调"""
            print(f"  策略 {self.name} 启动完成")
        
        def on_stop(self):
            """策略停止回调"""
            print(f"  策略 {self.name} 停止完成")
        
        def on_pause(self):
            """策略暂停回调"""
            print(f"  策略 {self.name} 暂停完成")
        
        def on_resume(self):
            """策略恢复回调"""
            print(f"  策略 {self.name} 恢复完成")
        
        def on_params_update(self, params):
            """参数更新回调"""
            print(f"  策略 {self.name} 参数更新: {params}")
        
        def on_bar(self, event):
            """K线数据回调"""
            if self.running and not self.paused:
                print(f"  策略 {self.name} 处理K线事件: {event}")
                # 生成测试信号
                self.generate_signal(event.symbol, "BUY", 0.8, event.bar_data['close'])
        
    # 测试策略的创建和注册
    print("\n1. 测试策略的创建和注册...")
    test_strategy = TestStrategy("test_strategy", ["600000.SH", "000001.SZ"])
    strategy_engine.register_strategy(test_strategy)
    print(f"✓ 策略 {test_strategy.name} 创建和注册成功！")
    
    # 测试策略的初始化
    print("\n2. 测试策略的初始化...")
    test_strategy.initialize()
    print("✓ 策略初始化成功！")
    
    # 测试策略的启动
    print("\n3. 测试策略的启动...")
    strategy_manager.start_strategy("test_strategy")
    print("✓ 策略启动成功！")
    
    # 测试策略的参数更新
    print("\n4. 测试策略的参数更新...")
    strategy_manager.update_strategy_params("test_strategy", {"fast_period": 5, "slow_period": 20})
    print("✓ 策略参数更新成功！")
    
    # 测试策略的暂停
    print("\n5. 测试策略的暂停...")
    strategy_manager.pause_strategy("test_strategy")
    print("✓ 策略暂停成功！")
    
    # 测试策略的恢复
    print("\n6. 测试策略的恢复...")
    strategy_manager.resume_strategy("test_strategy")
    print("✓ 策略恢复成功！")
    
    # 测试策略的信号生成
    print("\n7. 测试策略的信号生成...")
    # 创建一个测试K线事件
    test_bar_data = {
        'open': 10.0,
        'high': 10.5,
        'low': 9.8,
        'close': 10.2,
        'volume': 1000000
    }
    test_bar_event = BarEvent(
        symbol="600000.SH",
        bar_data=test_bar_data,
        timestamp=datetime.now()
    )
    # 放入事件引擎
    event_engine.put(test_bar_event)
    # 等待事件处理
    time.sleep(0.5)
    print("✓ 策略信号生成测试完成！")
    
    # 测试策略的停止
    print("\n8. 测试策略的停止...")
    strategy_manager.stop_strategy("test_strategy")
    print("✓ 策略停止成功！")
    
    # 测试策略的注销
    print("\n9. 测试策略的注销...")
    strategy_engine.unregister_strategy("test_strategy")
    print("✓ 策略注销成功！")
    
    print("\n策略模块测试通过！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n策略模块测试失败！")

print("\n测试完成！")
