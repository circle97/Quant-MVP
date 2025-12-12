# -*- coding: utf-8 -*-
"""
回测数据管理器 - 负责回测数据的获取和管理
"""
from typing import Dict, List, Any
import pandas as pd
from loguru import logger

from src.data.data_manager import AStockDataManager as DataManager


class BacktestDataManager(DataManager):
    """回测数据管理器，负责回测数据的获取和管理"""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        logger.info("初始化回测数据管理器")
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                          frequency: str = 'daily') -> pd.DataFrame:
        """获取历史数据（回测专用）
        
        Args:
            symbol: 标的代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            frequency: 数据频率，默认为 daily
            
        Returns:
            历史数据 DataFrame
        """
        logger.info(f"获取 {symbol} 的历史数据，时间范围: {start_date} 到 {end_date}")
        
        # 从父类获取数据
        data = super().get_daily_data(symbol, start_date, end_date)
        
        # 转换数据频率（如果需要）
        if frequency != 'daily':
            data = self._resample_data(data, frequency)
        
        return data
    
    def _resample_data(self, data: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """转换数据频率
        
        Args:
            data: 原始数据
            frequency: 目标频率
            
        Returns:
            转换后的数据
        """
        logger.info(f"转换数据频率: {frequency}")
        
        # 定义重采样规则
        resample_rules = {
            'weekly': 'W',
            'monthly': 'M',
            'quarterly': 'Q',
            'yearly': 'Y'
        }
        
        if frequency not in resample_rules:
            logger.warning(f"不支持的数据频率: {frequency}，使用 daily")
            return data
        
        # 重采样数据
        rule = resample_rules[frequency]
        resampled = {
            'open': data['open'].resample(rule).first(),
            'high': data['high'].resample(rule).max(),
            'low': data['low'].resample(rule).min(),
            'close': data['close'].resample(rule).last(),
            'volume': data['volume'].resample(rule).sum()
        }
        
        return pd.DataFrame(resampled)
    
    def get_data_feed(self, symbols: List[str], start_date: str, end_date: str, 
                     frequency: str = 'daily') -> Dict[str, pd.DataFrame]:
        """获取多个标的的数据馈送
        
        Args:
            symbols: 标的代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            
        Returns:
            标的数据字典，key 为标的代码，value 为数据 DataFrame
        """
        data_feed = {}
        
        for symbol in symbols:
            data = self.get_historical_data(symbol, start_date, end_date, frequency)
            data_feed[symbol] = data
        
        return data_feed
    
    def get_latest_data(self, symbol: str, n: int = 1) -> pd.DataFrame:
        """获取最新的 n 条数据
        
        Args:
            symbol: 标的代码
            n: 获取的条数
            
        Returns:
            最新数据 DataFrame
        """
        if symbol not in self.data_cache:
            return pd.DataFrame()
        
        return self.data_cache[symbol].tail(n)
    
    def clear_cache(self):
        """清空数据缓存"""
        self.data_cache.clear()
        logger.info("清空数据缓存")
