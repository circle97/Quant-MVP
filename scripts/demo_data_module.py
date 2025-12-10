#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据模块演示脚本
"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data import data_manager, data_cache


def demo_historical_data():
    """演示获取历史数据"""
    print("=" * 60)
    print("演示：获取历史数据")
    print("=" * 60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    start_date = '2023-01-01'
    end_date = '2023-01-31'
    
    for symbol in symbols:
        try:
            print(f"\n获取 {symbol} 的历史数据...")
            df = data_manager.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval='1d',
                use_cache=True
            )
            
            if not df.empty:
                print(f"数据形状: {df.shape}")
                print("前5行数据:")
                print(df[['open', 'high', 'low', 'close', 'volume']].head())
                print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
                
                # 基本统计
                print(f"\n收盘价统计:")
                print(f"  平均值: ${df['close'].mean():.2f}")
                print(f"  最高值: ${df['close'].max():.2f}")
                print(f"  最低值: ${df['close'].min():.2f}")
                print(f"  标准差: ${df['close'].std():.2f}")
            else:
                print(f"⚠ 未获取到 {symbol} 的数据")
                
        except Exception as e:
            print(f"❌ 获取 {symbol} 数据失败: {e}")


def demo_realtime_data():
    """演示获取实时数据"""
    print("\n" + "=" * 60)
    print("演示：获取实时数据")
    print("=" * 60)
    
    symbols = ['AAPL', 'MSFT', 'TSLA']
    
    for symbol in symbols:
        try:
            print(f"\n获取 {symbol} 的实时数据...")
            data = data_manager.get_realtime_data(symbol, use_cache=True)
            
            if data:
                print(f"  当前价格: ${data.get('price', 'N/A')}")
                print(f"  涨跌幅: {data.get('change_percent', 'N/A')}%")
                print(f"  成交量: {data.get('volume', 'N/A'):,}")
                print(f"  市值: ${data.get('market_cap', 'N/A'):,}")
            else:
                print(f"⚠ 未获取到 {symbol} 的实时数据（可能非交易时间）")
                
        except Exception as e:
            print(f"❌ 获取 {symbol} 实时数据失败: {e}")


def demo_cache_functionality():
    """演示缓存功能"""
    print("\n" + "=" * 60)
    print("演示：缓存功能")
    print("=" * 60)
    
    # 获取缓存统计
    stats = data_cache.get_stats()
    
    print("缓存统计信息:")
    print(f"  总缓存条目: {stats.get('total_count', 0)}")
    print(f"  内存缓存大小: {stats.get('memory_cache_size', 0)}")
    print(f"  数据库大小: {stats.get('db_size_mb', 0):.2f} MB")
    
    if 'type_stats' in stats:
        print("  按类型统计:")
        for data_type, count in stats['type_stats'].items():
            print(f"    {data_type}: {count}")
    
    # 清理过期缓存
    print("\n清理过期缓存...")
    data_cache.clear_expired()
    
    # 重新获取统计
    stats = data_cache.get_stats()
    print(f"清理后总缓存条目: {stats.get('total_count', 0)}")


def demo_multiple_symbols():
    """演示获取多个股票数据"""
    print("\n" + "=" * 60)
    print("演示：批量获取多个股票数据")
    print("=" * 60)
    
    symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META']
    start_date = '2023-01-01'
    end_date = '2023-01-15'
    
    print(f"批量获取 {len(symbols)} 个股票的数据...")
    
    try:
        all_data = data_manager.get_multiple_symbols_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval='1d',
            use_cache=True
        )
        
        print(f"\n获取结果汇总:")
        for symbol, df in all_data.items():
            if not df.empty:
                close_prices = df['close']
                first_close = close_prices.iloc[0]
                last_close = close_prices.iloc[-1]
                change_pct = (last_close - first_close) / first_close * 100
                
                print(f"  {symbol}: {len(df)} 条记录，"
                      f"价格变化: {change_pct:+.2f}% "
                      f"({first_close:.2f} → {last_close:.2f})")
            else:
                print(f"  {symbol}: 无数据")
                
    except Exception as e:
        print(f"❌ 批量获取数据失败: {e}")


def demo_data_validation_and_cleaning():
    """演示数据验证和清理"""
    print("\n" + "=" * 60)
    print("演示：数据验证和清理")
    print("=" * 60)
    
    # 创建一个有问题的测试数据
    test_data = {
        'open': [100, 101, None, 103],
        'high': [105, 106, 107, None],
        'low': [98, 99, 100, 101],
        'close': [103, 104, 105, 106],
        'volume': [1000, 2000, 3000, 4000]
    }
    
    # 无序的索引
    dates = ['2023-01-04', '2023-01-02', '2023-01-01', '2023-01-03']
    test_df = pd.DataFrame(test_data, index=pd.to_datetime(dates))
    
    print("原始数据（有问题）:")
    print(test_df)
    
    # 验证数据
    print(f"\n数据验证结果: {data_manager.validate_data(test_df)}")
    
    # 清理数据
    print("\n清理后的数据:")
    cleaned_df = data_manager.clean_data(test_df)
    print(cleaned_df)
    
    print(f"\n清理后验证结果: {data_manager.validate_data(cleaned_df)}")


def main():
    """主函数"""
    print("Quant-MVP 数据模块演示")
    print("=" * 60)
    
    try:
        # 运行各个演示
        demo_historical_data()
        demo_realtime_data()
        demo_multiple_symbols()
        demo_cache_functionality()
        demo_data_validation_and_cleaning()
        
        print("\n" + "=" * 60)
        print("🎉 数据模块演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 关闭数据管理器
        data_manager.close()
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)