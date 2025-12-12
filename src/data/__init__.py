# -*- coding: utf-8 -*-
"""
A股数据模块
"""
from .base import (
    AStockDataFeed,
    BarData,
    AStockDataError
)

from .tushare_data import (
    TushareData,
    tushare_data
)

from .akshare_data import (
    AKShareData,
    akshare_data
)

from .cache import (
    DataCache,
    data_cache
)

from .data_manager import (
    AStockDataManager,
    astock_data_manager
)

from .utils import (
    StockUtils,
    stock_utils
)

__all__ = [
    # 基类
    'AStockDataFeed',
    'BarData',
    'AStockDataError',
    
    # 数据源
    'TushareData',
    'tushare_data',
    'AKShareData',
    'akshare_data',
    
    # 缓存
    'DataCache',
    'data_cache',
    
    # 管理器
    'AStockDataManager',
    'astock_data_manager',
    
    # 工具
    'StockUtils',
    'stock_utils'
]

__version__ = '0.1.0'