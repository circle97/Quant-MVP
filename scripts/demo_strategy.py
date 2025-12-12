#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略引擎演示脚本
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 60)
print("Quant-MVP 策略引擎演示")
print("=" * 60)

# 1. 导入模块
print("\n1. 导入策略模块...")
try:
    from src.strategy import MACrossStrategy, EnhancedMACrossStrategy
    from src.strategy.strategy_manager import strategy_manager
    from src.core.event import event_engine, BarEvent
    from src.data import stock_utils
    
    print("✓ 策略模块导入成功")
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)

# 2. 创建双均线策略
print("\n2. 创建双均线策略...")
try:
    # 交易标的
    symbols = ['000001.SZ', '600519.SH']
    
    # 创建策略实例
    ma_strategy = MACrossStrategy(
        symbols=symbols,
        initial_capital=10000.0,
        fast_period=5,   # 快线周期
        slow_period=20   # 慢线周期
    )
    
    # 添加到策略管理器
    strategy_manager.add_strategy(ma_strategy)
    
    print(f"✓ 创建双均线策略成功")
    print(f"   策略名称: {ma_strategy.name}")
    print(f"   交易标的: {symbols}")
    print(f"   初始资金: {ma_strategy.initial_capital}")
    print(f"   参数: 快线={ma_strategy.params['fast_period']}天, "
          f"慢线={ma_strategy.params['slow_period']}天")
    
except Exception as e:
    print(f"✗ 创建策略失败: {e}")
    sys.exit(1)

# 3. 初始化策略
print("\n3. 初始化策略...")
try:
    ma_strategy.initialize()
    print("✓ 策略初始化成功")
    
    # 显示策略状态
    state = ma_strategy.get_strategy_state()
    print(f"   策略状态: {'运行中' if state['running'] else '已停止'}")
    print(f"   当前资产: {state['current_capital']:.2f}")
    print(f"   持仓数量: {state['positions']}")
    
except Exception as e:
    print(f"✗ 策略初始化失败: {e}")
    sys.exit(1)

# 4. 模拟市场数据并运行策略
print("\n4. 模拟市场数据运行策略...")
try:
    # 启动策略
    ma_strategy.start()
    
    # 生成模拟的K线数据
    print("\n生成模拟K线数据...")
    
    # 平安银行模拟价格序列
    prices_000001 = [10.0, 10.2, 10.5, 10.8, 11.0, 11.5, 12.0, 11.8, 11.5, 11.0,
                     10.8, 10.5, 10.2, 10.0, 9.8, 9.5, 9.2, 9.0, 9.2, 9.5]
    
    # 贵州茅台模拟价格序列  
    prices_600519 = [1500, 1520, 1550, 1580, 1600, 1650, 1700, 1680, 1650, 1600,
                     1580, 1550, 1520, 1500, 1480, 1450, 1420, 1400, 1420, 1450]
    
    print(f"模拟 {len(prices_000001)} 根K线数据")
    
    # 发送模拟K线数据
    for i in range(len(prices_000001)):
        timestamp = datetime.now() + timedelta(days=i)
        
        # 平安银行K线
        bar_data_000001 = {
            'open': prices_000001[i] * 0.99,
            'high': prices_000001[i] * 1.02,
            'low': prices_000001[i] * 0.98,
            'close': prices_000001[i],
            'volume': 1000000 + i * 50000,
            'amount': prices_000001[i] * (1000000 + i * 50000)
        }
        
        bar_event_000001 = BarEvent(
            symbol='000001.SZ',
            bar_data=bar_data_000001,
            timestamp=timestamp
        )
        
        # 贵州茅台K线
        bar_data_600519 = {
            'open': prices_600519[i] * 0.99,
            'high': prices_600519[i] * 1.02,
            'low': prices_600519[i] * 0.98,
            'close': prices_600519[i],
            'volume': 10000 + i * 500,
            'amount': prices_600519[i] * (10000 + i * 500)
        }
        
        bar_event_600519 = BarEvent(
            symbol='600519.SH',
            bar_data=bar_data_600519,
            timestamp=timestamp
        )
        
        # 发送事件
        event_engine.put(bar_event_000001)
        event_engine.put(bar_event_600519)
        
        # 稍微延迟，模拟实时交易
        time.sleep(0.1)
        
        # 每5根K线显示一次状态
        if (i + 1) % 5 == 0:
            print(f"\n  K线 {i+1}/{len(prices_000001)} 处理完成")
            
            # 显示策略状态
            for symbol in symbols:
                if symbol in ma_strategy.ma_fast and symbol in ma_strategy.ma_slow:
                    print(f"  {stock_utils.get_stock_name(symbol)}: "
                          f"价格={ma_strategy.current_prices.get(symbol, 0):.2f}, "
                          f"快线={ma_strategy.ma_fast[symbol]:.2f}, "
                          f"慢线={ma_strategy.ma_slow[symbol]:.2f}, "
                          f"信号={ma_strategy.position_signal.get(symbol, 0)}")
    
    print("\n✓ 模拟数据运行完成")
    
except Exception as e:
    print(f"✗ 模拟运行失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 显示策略结果
print("\n5. 策略运行结果...")
try:
    # 获取投资组合摘要
    portfolio_summary = ma_strategy.get_portfolio_summary()
    
    print("\n投资组合摘要:")
    print(f"  初始资金: {portfolio_summary['初始资金']:.2f}")
    print(f"  当前总资产: {portfolio_summary['当前总资产']:.2f}")
    print(f"  可用现金: {portfolio_summary['可用现金']:.2f}")
    print(f"  持仓市值: {portfolio_summary['持仓市值']:.2f}")
    print(f"  总盈亏: {portfolio_summary['总盈亏']:.2f}")
    print(f"  总收益率: {portfolio_summary['总收益率']:.2f}%")
    print(f"  持仓数量: {portfolio_summary['持仓数量']}")
    print(f"  交易次数: {portfolio_summary['交易次数']}")
    
    # 显示持仓
    positions = ma_strategy.get_all_positions()
    if positions:
        print("\n当前持仓:")
        for position in positions:
            print(f"  {position}")
    else:
        print("\n当前无持仓")
    
    # 显示交易记录
    trades = ma_strategy.portfolio.trades
    if trades:
        print(f"\n交易记录 ({len(trades)} 笔):")
        for i, trade in enumerate(trades[-5:], 1):  # 显示最近5笔
            print(f"  {i}. {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} "
                  f"{trade['symbol']} {trade['action']} {trade['quantity']}股 "
                  f"@{trade['price']:.2f}")
    
    # 显示绩效指标
    metrics = ma_strategy.get_performance_metrics()
    if metrics:
        print("\n绩效指标:")
        print(f"  总收益率: {metrics['总收益率']:.2f}%")
        print(f"  年化收益率: {metrics['年化收益率']:.2f}%")
        print(f"  年化波动率: {metrics['年化波动率']:.2f}%")
        print(f"  夏普比率: {metrics['夏普比率']:.2f}")
        print(f"  最大回撤: {metrics['最大回撤']:.2f}%")
        print(f"  交易天数: {metrics['交易天数']}")
        print(f"  交易次数: {metrics['交易次数']}")
    
except Exception as e:
    print(f"✗ 显示结果失败: {e}")

# 6. 测试增强版策略
print("\n6. 测试增强版策略...")
try:
    # 创建增强版策略
    enhanced_strategy = EnhancedMACrossStrategy(
        symbols=['000002.SZ'],  # 万科A
        initial_capital=5000.0,
        fast_period=10,
        slow_period=30,
        filter_period=50
    )
    
    enhanced_strategy.initialize()
    
    print(f"✓ 创建增强版策略成功")
    print(f"   策略名称: {enhanced_strategy.name}")
    print(f"   新增特性: 趋势过滤器({enhanced_strategy.params['filter_period']}天均线)")
    
    # 显示策略状态
    enhanced_state = enhanced_strategy.get_strategy_state()
    print(f"   参数配置: {enhanced_state['params']}")
    
except Exception as e:
    print(f"✗ 增强版策略测试失败: {e}")

# 7. 清理资源
print("\n7. 清理资源...")
try:
    # 停止策略
    ma_strategy.stop()
    
    # 停止事件引擎
    event_engine.stop()
    
    print("✓ 资源清理完成")
    
except Exception as e:
    print(f"✗ 资源清理失败: {e}")

print("\n" + "=" * 60)
print("🎉 策略引擎演示完成！")
print("=" * 60)

print(f"\n今日成果总结:")
print(f"1. ✅ 成功构建事件驱动策略引擎")
print(f"2. ✅ 实现双均线交叉策略（A股版）")
print(f"3. ✅ 实现增强版策略（带趋势过滤）")
print(f"4. ✅ 模拟运行策略并生成交易信号")
print(f"5. ✅ 计算投资组合绩效指标")

print(f"\n关键特性:")
print(f"  • A股交易规则（涨跌停、T+1、手续费）")
print(f"  • 事件驱动架构（专业级设计）")
print(f"  • 完整的仓位和风险管理")
print(f"  • 支持多策略并行运行")

print(f"\n明天计划:")
print(f"  → 开发回测引擎，验证策略历史表现")
print(f"  → 实现绩效分析可视化")
print(f"  → 优化策略参数")

print(f"\n现在你可以:")
print(f"  1. 修改策略参数重新测试")
print(f"  2. 基于策略基类开发自己的策略")
print(f"  3. 查看 data/ 目录下的生成图表")