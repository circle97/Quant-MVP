# -*- coding: utf-8 -*-
"""
数据源基类定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger


class BarData:
    """K线数据类"""
    
    def __init__(
        self,
        symbol: str,
        datetime: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        turnover: Optional[float] = None
    ):
        self.symbol = symbol
        self.datetime = datetime
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume
        self.turnover = turnover
        
    def __repr__(self):
        return (f"BarData(symbol={self.symbol}, datetime={self.datetime}, "
                f"open={self.open}, high={self.high}, low={self.low}, "
                f"close={self.close}, volume={self.volume})")
    
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
            'turnover': self.turnover
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建BarData"""
        return cls(
            symbol=data['symbol'],
            datetime=data['datetime'],
            open_price=data['open'],
            high_price=data['high'],
            low_price=data['low'],
            close_price=data['close'],
            volume=data['volume'],
            turnover=data.get('turnover')
        )


class DataFeed(ABC):
    """数据源基类（抽象类）"""
    
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
            interval: 时间间隔 (1d, 1h, 1m等)
            
        Returns:
            pandas DataFrame，包含OHLCV数据
        """
        pass
    
    @abstractmethod
    def get_realtime_data(self, symbol: str) -> Dict:
        """获取实时数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时数据字典
        """
        pass
    
    def get_historical_bars(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> List[BarData]:
        """获取历史K线数据列表
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 时间间隔
            
        Returns:
            BarData列表
        """
        df = self.get_historical_data(symbol, start_date, end_date, interval)
        
        bars = []
        for idx, row in df.iterrows():
            bar = BarData(
                symbol=symbol,
                datetime=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                open_price=row['Open'],
                high_price=row['High'],
                low_price=row['Low'],
                close_price=row['Close'],
                volume=row.get('Volume', 0),
                turnover=row.get('Turnover', 0)
            )
            bars.append(bar)
        
        return bars
    
    def get_multiple_symbols_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """获取多个股票的历史数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间间隔
            
        Returns:
            字典，键为股票代码，值为DataFrame
        """
        result = {}
        for symbol in symbols:
            try:
                df = self.get_historical_data(symbol, start_date, end_date, interval)
                result[symbol] = df
                logger.info(f"获取 {symbol} 数据成功: {len(df)} 条记录")
            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                result[symbol] = pd.DataFrame()
        
        return result


class DataError(Exception):
    """数据错误异常"""
    pass


class DataValidationError(DataError):
    """数据验证错误"""
    pass