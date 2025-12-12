# -*- coding: utf-8 -*-
"""
事件系统 - 量化框架的核心驱动机制
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from loguru import logger


class EventType(Enum):
    """事件类型枚举"""
    MARKET_DATA = "market_data"        # 市场数据事件
    BAR_DATA = "bar_data"              # K线数据事件
    SIGNAL = "signal"                  # 交易信号事件
    ORDER = "order"                    # 订单事件
    FILL = "fill"                      # 成交事件
    TIMER = "timer"                    # 定时器事件
    STRATEGY_START = "strategy_start"  # 策略启动事件
    STRATEGY_STOP = "strategy_stop"    # 策略停止事件


@dataclass
class Event:
    """事件基类"""
    event_type: EventType
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    
    def __repr__(self):
        return f"Event(type={self.event_type.value}, time={self.timestamp})"


class BarEvent(Event):
    """K线数据事件"""
    
    def __init__(self, symbol: str, bar_data: Dict[str, Any], timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
            
        data = {
            'symbol': symbol,
            'bar_data': bar_data
        }
        
        super().__init__(EventType.BAR_DATA, timestamp, data)
    
    @property
    def symbol(self) -> str:
        return self.data['symbol']
    
    @property
    def bar_data(self) -> Dict[str, Any]:
        return self.data['bar_data']
    
    def __repr__(self):
        return f"BarEvent(symbol={self.symbol}, time={self.timestamp})"


class SignalEvent(Event):
    """交易信号事件"""
    
    def __init__(self, symbol: str, signal_type: str, strength: float = 1.0,
                 price: Optional[float] = None, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
            
        data = {
            'symbol': symbol,
            'signal_type': signal_type,  # 'BUY', 'SELL', 'HOLD'
            'strength': strength,
            'price': price
        }
        
        super().__init__(EventType.SIGNAL, timestamp, data)
    
    @property
    def symbol(self) -> str:
        return self.data['symbol']
    
    @property
    def signal_type(self) -> str:
        return self.data['signal_type']
    
    @property
    def strength(self) -> float:
        return self.data['strength']
    
    def __repr__(self):
        price_str = f"@{self.data['price']}" if self.data['price'] else ""
        return f"SignalEvent({self.symbol} {self.signal_type}{price_str}, strength={self.strength})"


class OrderEvent(Event):
    """订单事件"""
    
    def __init__(self, symbol: str, order_type: str, quantity: float,
                 direction: str, price: Optional[float] = None,
                 timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
            
        data = {
            'symbol': symbol,
            'order_type': order_type,    # 'MARKET', 'LIMIT'
            'quantity': quantity,
            'direction': direction,      # 'LONG', 'SHORT'
            'price': price
        }
        
        super().__init__(EventType.ORDER, timestamp, data)
    
    def __repr__(self):
        price_str = f"@{self.data['price']}" if self.data['price'] else "MARKET"
        return f"OrderEvent({self.symbol} {self.data['direction']} {self.data['quantity']} {price_str})"


class TimerEvent(Event):
    """定时器事件"""
    
    def __init__(self, interval: int, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
            
        data = {
            'interval': interval  # 时间间隔（秒）
        }
        
        super().__init__(EventType.TIMER, timestamp, data)
    
    @property
    def interval(self) -> int:
        return self.data['interval']


class EventEngine:
    """事件引擎 - 负责事件的注册和分发"""
    
    def __init__(self):
        self._handlers = {}
        self._running = False
    
    def register_handler(self, event_type: EventType, handler):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"注册事件处理器: {event_type.value} -> {handler.__name__}")
    
    def unregister_handler(self, event_type: EventType, handler):
        """取消注册事件处理器"""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                logger.debug(f"移除事件处理器: {event_type.value} -> {handler.__name__}")
    
    def put(self, event: Event):
        """放入事件"""
        self._process_event(event)
    
    def _process_event(self, event: Event):
        """处理事件"""
        event_type = event.event_type
        
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"事件处理器 {handler.__name__} 处理事件 {event} 时出错: {e}")
        else:
            logger.debug(f"事件 {event} 没有注册的处理器")
    
    def start(self):
        """启动事件引擎"""
        self._running = True
        logger.info("事件引擎已启动")
    
    def stop(self):
        """停止事件引擎"""
        self._running = False
        logger.info("事件引擎已停止")


# 全局事件引擎实例
event_engine = EventEngine()