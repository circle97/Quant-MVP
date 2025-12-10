# -*- coding: utf-8 -*-
"""
数据管理器
"""
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from .base import DataFeed, BarData
from .yfinance_data import YahooFinanceData, yfinance_data
from .cache import DataCache, data_cache
from ..utils.config import config_manager


class DataManager:
    """数据管理器：统一管理数据源和数据缓存"""
    
    def __init__(self, data_source: str = None):
        """初始化数据管理器
        
        Args:
            data_source: 数据源名称，默认为配置中的data.source
        """
        if data_source is None:
            data_source = config_manager.get('data.source', 'yfinance')
        
        self.data_source = data_source
        self.data_feeds: Dict[str, DataFeed] = {}
        self.cache = data_cache
        
        self._init_data_feeds()
        
    def _init_data_feeds(self):
        """初始化数据源"""
        # 注册可用的数据源
        if self.data_source == 'yfinance':
            self.data_feeds['yfinance'] = YahooFinanceData()
        # 后续可以添加其他数据源
        
        # 连接数据源
        for name, feed in self.data_feeds.items():
            try:
                feed.connect()
                logger.info(f"数据源 '{name}' 连接成功")
            except Exception as e:
                logger.error(f"数据源 '{name}' 连接失败: {e}")
    
    def get_data_feed(self, name: str = None) -> Optional[DataFeed]:
        """获取数据源实例
        
        Args:
            name: 数据源名称，默认为主数据源
            
        Returns:
            数据源实例
        """
        if name is None:
            name = self.data_source
        
        return self.data_feeds.get(name)
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
        use_cache: bool = True,
        cache_ttl: int = 3600
    ) -> pd.DataFrame:
        """获取历史数据（带缓存）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            use_cache: 是否使用缓存
            cache_ttl: 缓存存活时间（秒）
            
        Returns:
            历史数据DataFrame
        """
        # 生成缓存参数
        cache_params = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'interval': interval
        }
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = self.cache.get('historical', **cache_params)
            if cached_data is not None:
                logger.info(f"从缓存获取 {symbol} 历史数据")
                return cached_data
        
        # 从数据源获取
        data_feed = self.get_data_feed()
        if data_feed is None:
            raise ValueError(f"未找到数据源: {self.data_source}")
        
        try:
            data = data_feed.get_historical_data(symbol, start_date, end_date, interval)
            
            # 缓存数据
            if use_cache:
                self.cache.set(data, 'historical', cache_ttl, **cache_params)
            
            return data
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            raise
    
    def get_realtime_data(
        self,
        symbol: str,
        use_cache: bool = True,
        cache_ttl: int = 30
    ) -> Dict[str, Any]:
        """获取实时数据（带缓存）
        
        Args:
            symbol: 股票代码
            use_cache: 是否使用缓存
            cache_ttl: 缓存存活时间（秒），实时数据缓存时间较短
            
        Returns:
            实时数据字典
        """
        cache_params = {'symbol': symbol}
        
        if use_cache:
            cached_data = self.cache.get('realtime', **cache_params)
            if cached_data is not None:
                return cached_data
        
        data_feed = self.get_data_feed()
        if data_feed is None:
            raise ValueError(f"未找到数据源: {self.data_source}")
        
        try:
            data = data_feed.get_realtime_data(symbol)
            
            if use_cache and data:
                self.cache.set(data, 'realtime', cache_ttl, **cache_params)
            
            return data
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}
    
    def get_multiple_symbols_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """获取多个股票的数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            use_cache: 是否使用缓存
            
        Returns:
            字典，键为股票代码，值为DataFrame
        """
        result = {}
        data_feed = self.get_data_feed()
        
        if data_feed is None:
            raise ValueError(f"未找到数据源: {self.data_source}")
        
        for symbol in symbols:
            try:
                data = self.get_historical_data(
                    symbol, start_date, end_date, interval, use_cache
                )
                result[symbol] = data
            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                result[symbol] = pd.DataFrame()
        
        return result
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """验证数据质量
        
        Args:
            df: 要验证的DataFrame
            
        Returns:
            验证结果
        """
        if df.empty:
            logger.warning("数据为空")
            return False
        
        # 检查必需的列
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"数据缺少必需的列: {missing_columns}")
            return False
        
        # 检查NaN值
        nan_count = df[required_columns].isna().sum().sum()
        if nan_count > 0:
            logger.warning(f"数据包含 {nan_count} 个NaN值")
            # 可以选择填充或删除NaN值
            # df = df.fillna(method='ffill')
        
        # 检查数据顺序（应该按时间升序）
        if not df.index.is_monotonic_increasing:
            logger.warning("数据索引不是单调递增的")
            df = df.sort_index()
        
        return True
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理数据
        
        Args:
            df: 原始数据
            
        Returns:
            清理后的数据
        """
        # 确保索引是datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # 按日期排序
        df = df.sort_index()
        
        # 前向填充NaN值
        df = df.fillna(method='ffill')
        
        # 后向填充剩余的NaN值
        df = df.fillna(method='bfill')
        
        # 确保数值列是float类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """清理过期缓存"""
        self.cache.clear_expired()
    
    def close(self):
        """关闭数据管理器和所有数据源"""
        for name, feed in self.data_feeds.items():
            try:
                feed.disconnect()
                logger.info(f"数据源 '{name}' 已断开")
            except Exception as e:
                logger.error(f"断开数据源 '{name}' 失败: {e}")
        
        self.cache.close()
        logger.info("数据管理器已关闭")


# 创建全局数据管理器实例
data_manager = DataManager()