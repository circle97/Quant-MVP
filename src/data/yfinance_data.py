# -*- coding: utf-8 -*-
"""
yfinance数据源实现
"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from .base import DataFeed, BarData, DataError


class YahooFinanceData(DataFeed):
    """Yahoo Finance数据源"""
    
    def __init__(self):
        super().__init__("Yahoo Finance")
        self.connected = False
        
    def connect(self):
        """连接数据源（yfinance无需显式连接）"""
        self.connected = True
        logger.info(f"已连接 {self.name} 数据源")
        
    def disconnect(self):
        """断开连接"""
        self.connected = False
        logger.info(f"已断开 {self.name} 数据源")
        
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """获取历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 时间间隔 (1d, 1wk, 1mo, 1h, 30m, 15m, 5m, 1m)
            
        Returns:
            pandas DataFrame，包含OHLCV数据
        """
        if not self.connected:
            self.connect()
            
        try:
            # 下载数据
            ticker = yf.Ticker(symbol)
            
            # yfinance的interval参数
            valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', 
                              '1h', '1d', '5d', '1wk', '1mo', '3mo']
            
            if interval not in valid_intervals:
                logger.warning(f"不支持的时间间隔 {interval}，使用默认的1d")
                interval = "1d"
            
            # 下载数据
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if df.empty:
                raise DataError(f"未获取到 {symbol} 的数据")
            
            # 重命名列以保持一致性
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 确保索引是datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # 按日期排序
            df = df.sort_index()
            
            logger.info(f"获取 {symbol} 数据成功: {start_date} 到 {end_date}, "
                       f"共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            raise DataError(f"获取 {symbol} 历史数据失败: {e}")
    
    def get_realtime_data(self, symbol: str) -> Dict:
        """获取实时数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时数据字典
        """
        if not self.connected:
            self.connect()
            
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取重要信息
            realtime_data = {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', 0),
                'previous_close': info.get('regularMarketPreviousClose', 0),
                'open': info.get('regularMarketOpen', 0),
                'high': info.get('dayHigh', 0),
                'low': info.get('dayLow', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'currency': info.get('currency', 'USD'),
                'timestamp': datetime.now().isoformat()
            }
            
            # 计算涨跌幅
            if realtime_data['previous_close'] and realtime_data['price']:
                change_percent = ((realtime_data['price'] - realtime_data['previous_close']) 
                                 / realtime_data['previous_close'] * 100)
                realtime_data['change_percent'] = round(change_percent, 2)
            
            logger.debug(f"获取 {symbol} 实时数据成功")
            return realtime_data
            
        except Exception as e:
            logger.error(f"获取 {symbol} 实时数据失败: {e}")
            return {}
    
    def get_company_info(self, symbol: str) -> Dict:
        """获取公司信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            公司信息字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            company_info = {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'country': info.get('country', ''),
                'website': info.get('website', ''),
                'description': info.get('longBusinessSummary', ''),
                'employees': info.get('fullTimeEmployees', 0)
            }
            
            return company_info
            
        except Exception as e:
            logger.error(f"获取 {symbol} 公司信息失败: {e}")
            return {}
    
    def get_dividend_history(self, symbol: str) -> pd.DataFrame:
        """获取股息历史
        
        Args:
            symbol: 股票代码
            
        Returns:
            股息历史DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if not dividends.empty:
                dividends_df = dividends.reset_index()
                dividends_df.columns = ['date', 'dividend']
                return dividends_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取 {symbol} 股息历史失败: {e}")
            return pd.DataFrame()


# 创建全局实例
yfinance_data = YahooFinanceData()