#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试回测模块功能
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始测试回测模块...")

try:
    # 导入回测模块的核心组件
    from src.backtest.backtest_engine import BacktestEngine
    from src.strategy.base import Strategy
    from src.data.data_manager import AStockDataManager
    from src.core.event import BarEvent
    
    print("✓ 回测模块组件导入成功！")
    
    # 创建一个简单的测试策略用于回测
    class TestBacktestStrategy(Strategy):
        """回测测试策略"""
        
        def on_init(self):
            """策略初始化回调"""
            self.params = {
                'fast_period': 10,
                'slow_period': 30
            }
            self.symbol = self.symbols[0]  # 使用第一个标的
            self.fast_ma = []
            self.slow_ma = []
            print(f"  策略 {self.name} 初始化完成")
        
        def on_bar(self, event):
            """K线数据回调"""
            if self.running and not self.paused:
                # 简单的移动平均线策略
                close_price = event.bar_data['close']
                
                # 更新移动平均线
                self.fast_ma.append(close_price)
                self.slow_ma.append(close_price)
                
                # 保持移动平均线长度
                if len(self.fast_ma) > self.params['fast_period']:
                    self.fast_ma.pop(0)
                if len(self.slow_ma) > self.params['slow_period']:
                    self.slow_ma.pop(0)
                
                # 生成交易信号
                if len(self.fast_ma) >= self.params['fast_period'] and len(self.slow_ma) >= self.params['slow_period']:
                    fast_ma_value = sum(self.fast_ma) / len(self.fast_ma)
                    slow_ma_value = sum(self.slow_ma) / len(self.slow_ma)
                    
                    # 金叉：快速均线上穿慢速均线，买入信号
                    if fast_ma_value > slow_ma_value:
                        self.generate_signal(event.symbol, "BUY", 0.5, close_price)
                    # 死叉：快速均线下穿慢速均线，卖出信号
                    elif fast_ma_value < slow_ma_value:
                        self.generate_signal(event.symbol, "SELL", 0.5, close_price)
    
    # 1. 测试回测引擎的初始化
    print("\n1. 测试回测引擎的初始化...")
    
    # 回测配置
    config = {
        'initial_capital': 100000.0,
        'start_date': datetime(2025, 9, 3),
        'end_date': datetime(2025, 12, 12),
        'data_frequency': 'daily'
    }
    
    # 初始化回测引擎
    backtest_engine = BacktestEngine(config)
    print("✓ 回测引擎初始化成功！")
    
    # 2. 测试设置策略
    print("\n2. 测试设置策略...")
    test_strategy = TestBacktestStrategy("test_backtest_strategy", ["600000.SH"])
    backtest_engine.set_strategy(test_strategy)
    print("✓ 策略设置成功！")
    
    # 3. 测试设置数据管理器
    print("\n3. 测试设置数据管理器...")
    data_manager = AStockDataManager()
    backtest_engine.set_data_manager(data_manager)
    print("✓ 数据管理器设置成功！")
    
    # 4. 测试运行回测
    print("\n4. 测试运行回测...")
    backtest_engine.run()
    print("✓ 回测运行成功！")
    
    # 5. 测试获取回测结果
    print("\n5. 测试获取回测结果...")
    results = backtest_engine.get_results()
    print(f"  回测结果: {list(results.keys())}")
    print(f"  策略名称: {results['strategy_name']}")
    print(f"  初始资金: {results['initial_capital']:.2f}")
    print(f"  最终资金: {results['final_capital']:.2f}")
    print(f"  总收益率: {results['total_return']:.2%}")
    print(f"  年化收益率: {results['annual_return']:.2%}")
    print(f"  最大回撤: {results['max_drawdown']:.2%}")
    print(f"  夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"  回测时长: {results['duration']}")
    print("✓ 回测结果获取成功！")
    
    # 6. 测试绘制回测结果
    print("\n6. 测试绘制回测结果...")
    backtest_engine.plot_results()
    print("✓ 回测结果绘制调用成功！")
    
    print("\n回测模块测试通过！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n回测模块测试失败！")

print("\n测试完成！")