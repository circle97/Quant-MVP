# -*- coding: utf-8 -*-
"""
本地测试数据生成器
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import random


class LocalTestData:
    """本地测试数据生成器"""
    
    @staticmethod
    def generate_stock_data(symbol: str, start_date: str, end_date: str, 
                           start_price: float = 10.0) -> pd.DataFrame:
        """生成股票测试数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            start_price: 起始价格
            
        Returns:
            生成的股票数据
        """
        # 生成日期范围（工作日）
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # B表示工作日
        
        if len(dates) == 0:
            # 如果没有工作日，使用普通日期
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        days = len(dates)
        
        if days == 0:
            # 如果还是没有日期，生成30天的数据
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            days = 30
        
        # 生成随机价格序列（模拟股票价格）
        prices = [start_price]
        for i in range(1, days):
            # 模拟随机波动（正态分布）
            daily_return = np.random.normal(0.0005, 0.02)  # 平均日收益0.05%，波动2%
            new_price = prices[-1] * (1 + daily_return)
            # 确保价格在合理范围内
            new_price = max(new_price, 0.01)
            prices.append(new_price)
        
        # 创建DataFrame
        df = pd.DataFrame(index=dates)
        
        # 生成OHLC数据
        df['open'] = [p * random.uniform(0.98, 1.02) for p in prices]
        df['high'] = [max(o, p) * random.uniform(1.0, 1.05) for o, p in zip(df['open'], prices)]
        df['low'] = [min(o, p) * random.uniform(0.95, 1.0) for o, p in zip(df['open'], prices)]
        df['close'] = prices
        df['volume'] = [random.randint(100000, 10000000) for _ in range(days)]
        df['amount'] = df['close'] * df['volume']
        
        # 计算涨跌幅
        if days > 1:
            df['pct_chg'] = df['close'].pct_change() * 100
            df.loc[df.index[0], 'pct_chg'] = 0
        else:
            df['pct_chg'] = 0
        
        # 计算振幅
        df['amplitude'] = (df['high'] - df['low']) / df['close'] * 100
        
        # 计算换手率（模拟）
        df['turnover'] = [random.uniform(0.5, 5.0) for _ in range(days)]
        
        df.index.name = 'date'
        return df
    
    @staticmethod
    def generate_multiple_stocks(symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """生成多个股票的测试数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            字典，键为股票代码，值为DataFrame
        """
        result = {}
        start_prices = {
            '000001.SZ': 10.0,    # 平安银行
            '600519.SH': 1500.0,  # 贵州茅台
            '000858.SZ': 100.0,   # 五粮液
            '300750.SZ': 200.0,   # 宁德时代
            '000002.SZ': 20.0,    # 万科A
            '000333.SZ': 50.0,    # 美的集团
            '000651.SZ': 40.0,    # 格力电器
            '002415.SZ': 30.0,    # 海康威视
            '300059.SZ': 15.0,    # 东方财富
            '002594.SZ': 250.0,   # 比亚迪
        }
        
        for symbol in symbols:
            start_price = start_prices.get(symbol, 10.0)
            df = LocalTestData.generate_stock_data(symbol, start_date, end_date, start_price)
            result[symbol] = df
        
        return result
    
    @staticmethod
    def generate_index_data(index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成指数测试数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            生成的指数数据
        """
        start_prices = {
            '000001.SH': 3000.0,  # 上证指数
            '399001.SZ': 10000.0, # 深证成指
            '399006.SZ': 2000.0,  # 创业板指
            '000300.SH': 3800.0,  # 沪深300
            '000905.SH': 6000.0,  # 中证500
            '000852.SH': 7000.0,  # 中证1000
        }
        
        start_price = start_prices.get(index_code, 3000.0)
        return LocalTestData.generate_stock_data(index_code, start_date, end_date, start_price)


# 全局实例
local_test_data = LocalTestData()


if __name__ == '__main__':
    # 测试生成数据
    df = local_test_data.generate_stock_data('000001.SZ', '2023-01-01', '2023-01-10')
    print("生成的测试数据：")
    print(df.head())
    print(f"\n数据形状: {df.shape}")
    print(f"日期范围: {df.index[0]} 到 {df.index[-1]}")
    print(f"列名: {list(df.columns)}")