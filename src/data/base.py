# -*- coding: utf-8 -*-
"""
A股数据源基类定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger


@dataclass
class BarData:
    """A股K线数据类"""
    
    symbol: str           # 股票代码，如 '000001.SZ'
    datetime: datetime    # 日期时间
    open: float           # 开盘价
    high: float           # 最高价
    low: float            # 最低价
    close: float          # 收盘价
    volume: float         # 成交量（手）
    amount: float         # 成交额（元）
    turnover: Optional[float] = None  # 换手率
    pre_close: Optional[float] = None  # 前收盘价
    change: Optional[float] = None     # 涨跌额
    pct_change: Optional[float] = None  # 涨跌幅
    
    def __repr__(self):
        return (f"BarData(symbol={self.symbol}, datetime={self.datetime}, "
                f"close={self.close}, volume={self.volume:,}, "
                f"pct_change={self.pct_change:.2%})")
    
    def to_dict(self):
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'datetime': self.datetime,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'turnover': self.turnover,
            'pre_close': self.pre_close,
            'change': self.change,
            'pct_change': self.pct_change
        }


class AStockDataFeed(ABC):
    """A股数据源基类（抽象类）"""
    
    def __init__(self, name: str):
        self.name = name
        self.connected = False
        
    @abstractmethod
    def connect(self):
        """连接数据源"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开数据源连接"""
        pass
    
    @abstractmethod
    def get_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取日线数据
        
        Args:
            symbol: 股票代码，如 '000001.SZ'
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 qfq(前复权), hfq(后复权), None(不复权)
            
        Returns:
            pandas DataFrame，包含OHLCV等数据
        """
        pass
    
    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> Dict:
        """获取实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时行情字典
        """
        pass
    
    @abstractmethod
    def get_basic_info(self, symbol: str) -> Dict:
        """获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
        """
        pass
    
    def get_daily_bars(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> List[BarData]:
        """获取日K线数据列表
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            BarData列表
        """
        df = self.get_daily_data(symbol, start_date, end_date, adjust)
        
        bars = []
        for idx, row in df.iterrows():
            bar = BarData(
                symbol=symbol,
                datetime=idx if isinstance(idx, datetime) else pd.to_datetime(idx),
                open=row.get('open', 0),
                high=row.get('high', 0),
                low=row.get('low', 0),
                close=row.get('close', 0),
                volume=row.get('volume', 0),
                amount=row.get('amount', 0),
                turnover=row.get('turnover_rate', row.get('turnover', 0)),
                pre_close=row.get('pre_close', row.get('close', 0)),
                change=row.get('change', 0),
                pct_change=row.get('pct_chg', 0)
            )
            bars.append(bar)
        
        return bars
    
    def get_multiple_stocks_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> Dict[str, pd.DataFrame]:
        """获取多个股票的历史数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            字典，键为股票代码，值为DataFrame
        """
        result = {}
        for symbol in symbols:
            try:
                df = self.get_daily_data(symbol, start_date, end_date, adjust)
                result[symbol] = df
                logger.info(f"获取 {symbol} 数据成功: {len(df)} 条记录")
            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                result[symbol] = pd.DataFrame()
        
        return result


class AStockDataError(Exception):
    """A股数据错误异常"""
    pass