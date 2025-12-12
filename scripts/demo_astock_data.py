#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股数据模块演示脚本
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data import astock_data_manager, stock_utils


def setup_plotting():
    """设置绘图样式"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    plt.style.use('seaborn-v0_8-darkgrid')


def demo_stock_normalization():
    """演示股票代码标准化"""
    print("=" * 60)
    print("演示：股票代码标准化")
    print("=" * 60)
    
    test_symbols = ['000001', '600519', '000001.SZ', 'SZ000001', 'SH600519', '300750', '000002']
    
    for symbol in test_symbols:
        normalized, exchange = stock_utils.normalize_symbol(symbol)
        name = stock_utils.get_stock_name(normalized)
        print(f"  {symbol:15s} → {normalized:15s} ({exchange}) - {name}")
    
    print(f"\n主要指数:")
    for index in stock_utils.get_index_symbols():
        print(f"  {index}")
    
    print(f"\n主要ETF:")
    for etf in stock_utils.get_etf_symbols():
        print(f"  {etf}")


def demo_daily_data():
    """演示获取日线数据"""
    print("\n" + "=" * 60)
    print("演示：获取A股日线数据")
    print("=" * 60)
    
    # A股代表性股票
    stocks = [
        {'symbol': '000001.SZ', 'name': '平安银行'},
        {'symbol': '600519.SH', 'name': '贵州茅台'},
        {'symbol': '000858.SZ', 'name': '五粮液'},
        {'symbol': '300750.SZ', 'name': '宁德时代'},
    ]
    
    start_date = '2023-01-01'
    end_date = '2023-06-30'
    
    for stock in stocks:
        try:
            print(f"\n获取 {stock['name']} ({stock['symbol']}) 的历史数据...")
            
            # 获取前复权数据
            df = astock_data_manager.get_daily_data(
                symbol=stock['symbol'],
                start_date=start_date,
                end_date=end_date,
                adjust='qfq',
                use_cache=True
            )
            
            if not df.empty:
                print(f"  数据形状: {df.shape}")
                print(f"  时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
                print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
                
                # 基本统计
                returns = df['close'].pct_change().dropna()
                print(f"  平均日收益率: {returns.mean():.4%}")
                print(f"  收益率波动率: {returns.std():.4%}")
                print(f"  夏普比率(年化): {(returns.mean() / returns.std() * np.sqrt(252)):.2f}")
                
                # 显示前几行
                print(f"\n  前5行数据:")
                print(df[['open', 'high', 'low', 'close', 'volume']].head())
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ❌ 获取数据失败: {e}")


def demo_realtime_data():
    """演示获取实时数据"""
    print("\n" + "=" * 60)
    print("演示：获取A股实时行情")
    print("=" * 60)
    
    symbols = ['000001.SZ', '600519.SH', '300750.SZ']
    
    for symbol in symbols:
        try:
            name = stock_utils.get_stock_name(symbol)
            print(f"\n获取 {name} ({symbol}) 的实时行情...")
            
            quote = astock_data_manager.get_realtime_quote(symbol, use_cache=True)
            
            if quote:
                print(f"  最新价: {quote.get('price', 'N/A')}")
                print(f"  涨跌幅: {quote.get('pct_change', 'N/A'):.2%}")
                print(f"  成交量: {quote.get('volume', 'N/A'):,}")
                print(f"  成交额: {quote.get('amount', 'N/A'):,.0f}")
                if 'bid' in quote and 'ask' in quote:
                    print(f"  买卖价: {quote.get('bid', 'N/A')} / {quote.get('ask', 'N/A')}")
            else:
                print(f"  ⚠ 未获取到实时行情（可能非交易时间）")
                
        except Exception as e:
            print(f"  ❌ 获取实时行情失败: {e}")


def demo_technical_analysis():
    """演示技术分析"""
    print("\n" + "=" * 60)
    print("演示：技术分析")
    print("=" * 60)
    
    symbol = '000001.SZ'  # 平安银行
    name = stock_utils.get_stock_name(symbol)
    
    try:
        print(f"\n对 {name} ({symbol}) 进行技术分析...")
        
        # 获取数据
        df = astock_data_manager.get_daily_data(
            symbol=symbol,
            start_date='2023-01-01',
            end_date='2023-12-31',
            adjust='qfq'
        )
        
        if not df.empty:
            # 计算技术指标
            df_tech = stock_utils.calculate_technical_indicators(df)
            
            # 显示技术指标
            print(f"\n技术指标示例（最近5天）:")
            tech_cols = ['close', 'MA5', 'MA10', 'MA20', 'MACD', 'RSI', 'BB_Upper', 'BB_Lower']
            available_cols = [col for col in tech_cols if col in df_tech.columns]
            print(df_tech[available_cols].tail())
            
            # 创建图表
            setup_plotting()
            fig, axes = plt.subplots(3, 1, figsize=(12, 10))
            
            # 价格和移动平均线
            axes[0].plot(df_tech.index, df_tech['close'], label='收盘价', linewidth=2)
            axes[0].plot(df_tech.index, df_tech['MA5'], label='MA5', alpha=0.7)
            axes[0].plot(df_tech.index, df_tech['MA10'], label='MA10', alpha=0.7)
            axes[0].plot(df_tech.index, df_tech['MA20'], label='MA20', alpha=0.7)
            axes[0].set_title(f'{name} ({symbol}) - 价格和移动平均线')
            axes[0].set_xlabel('日期')
            axes[0].set_ylabel('价格 (元)')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # MACD
            axes[1].plot(df_tech.index, df_tech['MACD'], label='MACD', linewidth=2)
            axes[1].plot(df_tech.index, df_tech['MACD_Signal'], label='信号线', linewidth=2)
            axes[1].bar(df_tech.index, df_tech['MACD_Hist'], label='MACD柱', alpha=0.5, width=1)
            axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
            axes[1].set_title('MACD指标')
            axes[1].set_xlabel('日期')
            axes[1].set_ylabel('MACD')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
            
            # RSI
            axes[2].plot(df_tech.index, df_tech['RSI'], label='RSI', linewidth=2, color='purple')
            axes[2].axhline(y=70, color='red', linestyle='--', alpha=0.5, label='超买线(70)')
            axes[2].axhline(y=30, color='green', linestyle='--', alpha=0.5, label='超卖线(30)')
            axes[2].axhline(y=50, color='gray', linestyle='--', alpha=0.3, label='中线(50)')
            axes[2].set_title('RSI指标')
            axes[2].set_xlabel('日期')
            axes[2].set_ylabel('RSI')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('data/technical_analysis.png', dpi=150, bbox_inches='tight')
            print(f"\n图表已保存至: data/technical_analysis.png")
            
        else:
            print(f"  ⚠ 未获取到数据")
            
    except Exception as e:
        print(f"  ❌ 技术分析失败: {e}")
        import traceback
        traceback.print_exc()


def demo_index_data():
    """演示指数数据"""
    print("\n" + "=" * 60)
    print("演示：获取指数数据")
    print("=" * 60)
    
    indices = [
        ('000001.SH', '上证指数'),
        ('399001.SZ', '深证成指'),
        ('399006.SZ', '创业板指'),
        ('000300.SH', '沪深300'),
    ]
    
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    
    setup_plotting()
    plt.figure(figsize=(12, 6))
    
    for index_code, index_name in indices:
        try:
            print(f"\n获取 {index_name} ({index_code}) 数据...")
            
            df = astock_data_manager.get_index_data(
                index_code=index_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                # 计算累计收益率
                if 'close' in df.columns:
                    returns = df['close'].pct_change().dropna()
                    cumulative_return = (1 + returns).cumprod() - 1
                    
                    # 绘制累计收益率
                    plt.plot(cumulative_return.index, 
                            cumulative_return.values * 100, 
                            label=f'{index_name}', 
                            linewidth=2)
                    
                    print(f"  数据点数: {len(df)}")
                    print(f"  累计收益率: {cumulative_return.iloc[-1]:.2%}")
                    print(f"  年化波动率: {returns.std() * np.sqrt(252):.2%}")
            else:
                print(f"  ⚠ 未获取到指数数据")
                
        except Exception as e:
            print(f"  ❌ 获取指数数据失败: {e}")
    
    plt.title('主要指数累计收益率对比 (2023年)', fontsize=14)
    plt.xlabel('日期')
    plt.ylabel('累计收益率 (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('data/index_performance.png', dpi=150, bbox_inches='tight')
    print(f"\n指数对比图表已保存至: data/index_performance.png")


def demo_cache_statistics():
    """演示缓存统计"""
    print("\n" + "=" * 60)
    print("演示：缓存统计")
    print("=" * 60)
    
    stats = astock_data_manager.get_cache_stats()
    
    print("缓存统计信息:")
    print(f"  总缓存条目: {stats.get('total_count', 0)}")
    print(f"  内存缓存大小: {stats.get('memory_cache_size', 0)}")
    print(f"  数据库大小: {stats.get('db_size_mb', 0):.2f} MB")
    print(f"  过期缓存数量: {stats.get('expired_count', 0)}")
    
    if 'type_stats' in stats:
        print(f"  按类型统计:")
        for data_type, count in stats['type_stats'].items():
            print(f"    {data_type}: {count}")
    
    # 清理过期缓存
    print(f"\n清理过期缓存...")
    astock_data_manager.clear_cache()
    
    # 重新获取统计
    stats = astock_data_manager.get_cache_stats()
    print(f"清理后总缓存条目: {stats.get('total_count', 0)}")


def main():
    """主函数"""
    print("Quant-MVP A股数据模块演示")
    print("=" * 60)
    
    try:
        # 运行各个演示
        demo_stock_normalization()
        demo_daily_data()
        demo_realtime_data()
        demo_technical_analysis()
        demo_index_data()
        demo_cache_statistics()
        
        print("\n" + "=" * 60)
        print("🎉 A股数据模块演示完成！")
        print("=" * 60)
        
        # 显示缓存位置
        import os
        cache_dir = os.path.join(project_root, 'data', 'cache')
        print(f"\n数据缓存位置: {cache_dir}")
        print(f"配置文件位置: {os.path.join(project_root, 'config', 'config.yaml')}")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 关闭数据管理器
        astock_data_manager.close()
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)