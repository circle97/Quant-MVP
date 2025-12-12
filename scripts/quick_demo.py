#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股数据快速演示 - 确保能看到结果
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("=" * 60)
print("Quant-MVP A股数据快速演示")
print("=" * 60)

# 1. 测试导入模块
print("\n1. 测试模块导入...")
try:
    from src.data import stock_utils
    print("✓ 股票工具模块导入成功")
    
    # 测试股票代码标准化
    test_symbol = '000001'
    normalized, exchange = stock_utils.normalize_symbol(test_symbol)
    name = stock_utils.get_stock_name(normalized)
    print(f"   示例: {test_symbol} -> {normalized} ({exchange}) - {name}")
    
except Exception as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)

# 2. 测试数据管理器
print("\n2. 测试数据管理器...")
try:
    from src.data import astock_data_manager
    print("✓ 数据管理器导入成功")
    
    # 获取平安银行数据
    symbol = '000001.SZ'
    start_date = '2023-01-01'
    end_date = '2023-01-10'
    
    print(f"\n获取 {name} ({symbol}) 数据...")
    print(f"日期范围: {start_date} 到 {end_date}")
    
    df = astock_data_manager.get_daily_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust='qfq',
        use_cache=True
    )
    
    if not df.empty:
        print(f"✓ 数据获取成功!")
        print(f"   数据形状: {df.shape}")
        print(f"   时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
        print(f"   数据列: {', '.join(df.columns)}")
        
        # 显示数据
        print(f"\n   前5行数据:")
        print(df[['open', 'high', 'low', 'close', 'volume']].head().to_string())
        
        # 基本统计
        print(f"\n   基本统计:")
        print(f"     平均收盘价: {df['close'].mean():.2f}")
        print(f"     最高价: {df['close'].max():.2f}")
        print(f"     最低价: {df['close'].min():.2f}")
        print(f"     总成交量: {df['volume'].sum():,.0f}")
        
        if len(df) > 1:
            returns = df['close'].pct_change().dropna()
            print(f"     平均日收益率: {returns.mean():.4%}")
            print(f"     收益率波动率: {returns.std():.4%}")
    else:
        print("✗ 未获取到数据")
        
except Exception as e:
    print(f"✗ 数据管理器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试技术指标计算
print("\n3. 测试技术指标计算...")
try:
    if not df.empty and len(df) > 10:
        # 计算移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        
        print("✓ 技术指标计算成功")
        print(f"   最近一天的MA5: {df['MA5'].iloc[-1]:.2f}")
        print(f"   最近一天的MA10: {df['MA10'].iloc[-1]:.2f}")
        
        # 显示技术指标
        print(f"\n   技术指标示例（最近3天）:")
        tech_df = df[['close', 'MA5', 'MA10']].tail(3)
        print(tech_df.to_string())
    else:
        print("⚠ 数据不足，跳过技术指标计算")
        
except Exception as e:
    print(f"✗ 技术指标计算失败: {e}")

# 4. 测试多个股票获取
print("\n4. 测试多个股票获取...")
try:
    symbols = ['000001.SZ', '600519.SH', '000858.SZ']
    
    print(f"获取 {len(symbols)} 个股票的数据...")
    
    all_data = astock_data_manager.get_multiple_stocks_data(
        symbols=symbols,
        start_date='2023-01-01',
        end_date='2023-01-05'
    )
    
    print(f"✓ 多股票数据获取成功")
    
    for symbol, data_df in all_data.items():
        if not data_df.empty:
            stock_name = stock_utils.get_stock_name(symbol)
            print(f"   {stock_name:10s} ({symbol}): {len(data_df)} 条记录")
        else:
            print(f"   {symbol}: 无数据")
            
except Exception as e:
    print(f"✗ 多股票获取失败: {e}")

# 5. 清理和关闭
print("\n5. 清理资源...")
try:
    # 获取缓存统计
    stats = astock_data_manager.get_cache_stats()
    print(f"   缓存统计: {stats.get('total_count', 0)} 条记录")
    
    # 关闭数据管理器
    astock_data_manager.close()
    print("✓ 资源清理完成")
    
except Exception as e:
    print(f"✗ 资源清理失败: {e}")

print("\n" + "=" * 60)
print("🎉 快速演示完成！")
print("=" * 60)

# 显示重要信息
print(f"\n项目根目录: {project_root}")
print(f"数据缓存位置: {os.path.join(project_root, 'data', 'cache')}")

# 检查生成的文件
data_dir = os.path.join(project_root, 'data')
if os.path.exists(data_dir):
    print(f"\n数据目录内容:")
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            print(f"  {item} ({size:,} bytes)")
        else:
            print(f"  {item}/ (目录)")

print("\n下一步: 可以开始开发策略模块了！")