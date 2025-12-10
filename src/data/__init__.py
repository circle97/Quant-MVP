# -*- coding: utf-8 -*-
"""
数据模块
"""
from .base import (
    DataFeed,
    BarData,
    DataError,
    DataValidationError
)

from .yfinance_data import (
    YahooFinanceData,
    yfinance_data
)

from .cache import (
    DataCache,
    data_cache
)

from .data_manager import (
    DataManager,
    data_manager
)

__all__ = [
    # 基类
    'DataFeed',
    'BarData',
    'DataError',
    'DataValidationError',
    
    # 数据源
    'YahooFinanceData',
    'yfinance_data',
    
    # 缓存
    'DataCache',
    'data_cache',
    
    # 管理器
    'DataManager',
    'data_manager'
]

__version__ = '0.1.0'