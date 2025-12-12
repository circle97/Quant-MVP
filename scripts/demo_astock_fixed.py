#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股数据模块演示脚本（支持测试数据模式）
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入绘图工具
from src.utils.plotting import setup_chinese_font, setup_plotting_style, get_safe_title

# 设置绘图
setup_chinese_font()
setup_plotting_style()

from src.data import astock_data_manager, stock_utils


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
    
    print(f"\\n主要指数:")
    for index in stock_utils.get_index_symbols():
        print(f"  {index}")


def demo_daily_data():
    """演示获取日线数据"""
    print("\\n" + "=" * 60)
    print("演示：获取A股日线数据")
    print("=" * 60)
    
    # A股代表性股票
    stocks = [
        {'symbol': '000001.SZ', 'name': '平安银行'},
        {'symbol': '600519.SH', 'name': '贵州茅台'},
        {'symbol': '000858.SZ', 'name': '五粮液'},
    ]
    
    start_date = '2023-01-01'
    end_date = '2023-01-31'  # 缩短日期范围
    
    for stock in stocks:
        try:
            print(f"\\n获取 {stock['name']} ({stock['symbol']}) 的历史数据...")
            
            # 获取前复权数据
            df = astock_data_manager.get_daily_data(
                symbol=stock['symbol'],
                start_date=start_date,
                end_date=end_date,
                adjust='qfq',
                use_cache=True,
                fallback_to_test=True  # 允许回退到测试数据
            )
            
            if not df.empty:
                print(f"  ✓ 数据获取成功")
                print(f"     数据形状: {df.shape}")
                print(f"     时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
                print(f"     价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
                
                if len(df) > 1:
                    # 基本统计
                    returns = df['close'].pct_change().dropna()
                    print(f"     平均日收益率: {returns.mean():.4%}")
                    print(f"     收益率波动率: {returns.std():.4%}")
                    print(f"     夏普比率(年化): {(returns.mean() / returns.std() * np.sqrt(252)):.2f}")
                
                # 显示前3行
                print(f"\\n     前3行数据:")
                print(df[['open', 'high', 'low', 'close', 'volume']].head(3).to_string())
            else:
                print(f"  ⚠ 未获取到数据")
                
        except Exception as e:
            print(f"  ❌ 获取数据失败: {e}")


def demo_technical_analysis():
    """演示技术分析"""
    print("\\n" + "=" * 60)
    print("演示：技术分析")
    print("=" * 60)
    
    symbol = '000001.SZ'  # 平安银行
    name = stock_utils.get_stock_name(symbol)
    
    try:
        print(f"\\n对 {name} ({symbol}) 进行技术分析...")
        
        # 获取数据
        df = astock_data_manager.get_daily_data(
            symbol=symbol,
            start_date='2023-01-01',
            end_date='2023-06-30',
            adjust='qfq',
            fallback_to_test=True
        )
        
        if not df.empty and len(df) > 20:  # 确保有足够的数据
            import matplotlib.pyplot as plt
            
            # 计算移动平均线
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            # 创建图表
            fig, axes = plt.subplots(2, 1, figsize=(12, 8))
            
            # 价格和移动平均线
            axes[0].plot(df.index, df['close'], label='收盘价', linewidth=2, color='blue')
            axes[0].plot(df.index, df['MA5'], label='MA5', alpha=0.7, linestyle='--')
            axes[0].plot(df.index, df['MA10'], label='MA10', alpha=0.7, linestyle='-.')
            axes[0].plot(df.index, df['MA20'], label='MA20', alpha=0.7, linestyle=':')
            axes[0].set_title(get_safe_title(f'{name} ({symbol}) - 价格和移动平均线'))
            axes[0].set_xlabel(get_safe_title('日期'))
            axes[0].set_ylabel(get_safe_title('价格 (元)'))
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # 成交量
            axes[1].bar(df.index, df['volume'], alpha=0.6, color='orange')
            axes[1].set_title(get_safe_title(f'{name} ({symbol}) - 成交量'))
            axes[1].set_xlabel(get_safe_title('日期'))
            axes[1].set_ylabel(get_safe_title('成交量'))
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 确保目录存在
            os.makedirs('data', exist_ok=True)
            plt.savefig('data/technical_analysis_demo.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  ✓ 技术分析图表已生成")
            print(f"     文件保存至: data/technical_analysis_demo.png")
            
            # 显示技术指标
            print(f"\\n     技术指标示例（最近5天）:")
            tech_df = df[['close', 'MA5', 'MA10', 'MA20']].tail()
            print(tech_df.to_string())
        else:
            print(f"  ⚠ 数据不足，无法进行技术分析")
            
    except Exception as e:
        print(f"  ❌ 技术分析失败: {e}")
        import traceback
        traceback.print_exc()


def demo_index_data():
    """演示指数数据"""
    print("\\n" + "=" * 60)
    print("演示：获取指数数据")
    print("=" * 60)
    
    indices = [
        ('000001.SH', get_safe_title('上证指数')),
        ('399001.SZ', get_safe_title('深证成指')),
        ('399006.SZ', get_safe_title('创业板指')),
    ]
    
    start_date = '2023-01-01'
    end_date = '2023-06-30'
    
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        
        for index_code, index_name in indices:
            try:
                print(f"获取 {index_name} ({index_code}) 数据...")
                
                df = astock_data_manager.get_index_data(
                    index_code=index_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty and 'close' in df.columns:
                    # 计算累计收益率
                    returns = df['close'].pct_change().dropna()
                    if len(returns) > 0:
                        cumulative_return = (1 + returns).cumprod() - 1
                        
                        # 绘制累计收益率
                        plt.plot(cumulative_return.index, 
                                cumulative_return.values * 100, 
                                label=f'{index_name}', 
                                linewidth=2)
                        
                        print(f"  ✓ 数据获取成功: {len(df)} 条记录")
                        print(f"     累计收益率: {cumulative_return.iloc[-1]:.2%}")
                else:
                    print(f"  ⚠ 未获取到指数数据")
                    
            except Exception as e:
                print(f"  ❌ 获取指数数据失败: {e}")
        
        plt.title(get_safe_title('主要指数累计收益率对比 (2023上半年)'), fontsize=14)
        plt.xlabel(get_safe_title('日期'))
        plt.ylabel(get_safe_title('累计收益率 (%)'))
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 确保目录存在
        os.makedirs('data', exist_ok=True)
        plt.savefig('data/index_performance_demo.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"\\n  ✓ 指数对比图表已生成")
        print(f"     文件保存至: data/index_performance_demo.png")
        
    except Exception as e:
        print(f"❌ 指数数据演示失败: {e}")


def demo_cache_statistics():
    """演示缓存统计"""
    print("\\n" + "=" * 60)
    print("演示：缓存统计")
    print("=" * 60)
    
    stats = astock_data_manager.get_cache_stats()
    
    print("缓存统计信息:")
    print(f"  总缓存条目: {stats.get('total_count', 0)}")
    print(f"  内存缓存大小: {stats.get('memory_cache_size', 0)}")
    print(f"  数据库大小: {stats.get('db_size_mb', 0):.2f} MB")
    print(f"  过期缓存数量: {stats.get('expired_count', 0)}")
    
    if 'type_stats' in stats and stats['type_stats']:
        print(f"  按类型统计:")
        for data_type, count in stats['type_stats'].items():
            print(f"    {data_type}: {count}")
    
    # 清理过期缓存
    print(f"\\n清理过期缓存...")
    astock_data_manager.clear_cache()


def main():
    """主函数"""
    print("Quant-MVP A股数据模块演示")
    print("=" * 60)
    
    # 显示当前模式
    mode = "测试数据模式" if astock_data_manager.use_test_data else "网络数据模式"
    print(f"当前运行模式: {mode}\\n")
    
    try:
        # 运行各个演示
        demo_stock_normalization()
        demo_daily_data()
        demo_technical_analysis()
        demo_index_data()
        demo_cache_statistics()
        
        print("\\n" + "=" * 60)
        print("🎉 A股数据模块演示完成！")
        print("=" * 60)
        
        # 显示重要文件位置
        import os
        cache_dir = os.path.join(project_root, 'data', 'cache')
        print(f"\\n数据缓存位置: {cache_dir}")
        print(f"生成图表位置: {os.path.join(project_root, 'data')}")
        
    except Exception as e:
        print(f"\\n❌ 演示过程中出错: {e}")
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