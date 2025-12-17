# -*- coding: utf-8 -*-
"""
订单数据结构模块
"""
from typing import Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"          # 待提交
    SUBMITTED = "submitted"      # 已提交
    FILLED = "filled"            # 完全成交
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    CANCELLED = "cancelled"      # 已取消
    REJECTED = "rejected"        # 已拒绝
    EXPIRED = "expired"          # 已过期


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"            # 市价单
    LIMIT = "limit"              # 限价单
    STOP = "stop"                # 止损单
    STOP_LIMIT = "stop_limit"    # 止损限价单
    TRAILING_STOP = "trailing_stop"  # 追踪止损单


class OrderDirection(Enum):
    """订单方向枚举"""
    BUY = "buy"                  # 买入
    SELL = "sell"                # 卖出


class Order:
    """订单数据结构"""
    
    def __init__(self, symbol: str, order_type: OrderType, direction: OrderDirection,
                 quantity: float, price: Optional[float] = None,
                 stop_price: Optional[float] = None, trail_amount: Optional[float] = None,
                 order_id: Optional[str] = None):
        """
        初始化订单
        
        Args:
            symbol: 标的代码
            order_type: 订单类型
            direction: 订单方向
            quantity: 订单数量
            price: 订单价格（限价单、止损限价单）
            stop_price: 止损价格（止损单、止损限价单）
            trail_amount: 追踪金额（追踪止损单）
            order_id: 订单ID，若为None则自动生成
        """
        self.order_id = order_id or str(uuid4())
        self.symbol = symbol
        self.order_type = order_type
        self.direction = direction
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.trail_amount = trail_amount
        
        # 订单状态
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0.0
        self.avg_fill_price = 0.0
        
        # 时间戳
        self.create_time = datetime.now()
        self.submit_time = None
        self.fill_time = None
        self.cancel_time = None
        self.reject_time = None
        
        # 附加信息
        self.strategy_name = None
        self.account_id = "default"
        self.meta = {}
    
    def is_filled(self) -> bool:
        """判断订单是否完全成交"""
        return self.status == OrderStatus.FILLED
    
    def is_partially_filled(self) -> bool:
        """判断订单是否部分成交"""
        return self.status == OrderStatus.PARTIALLY_FILLED
    
    def is_active(self) -> bool:
        """判断订单是否处于活跃状态"""
        return self.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    def get_remaining_quantity(self) -> float:
        """获取剩余未成交数量"""
        return self.quantity - self.filled_quantity
    
    def update_fill(self, fill_quantity: float, fill_price: float):
        """更新成交信息"""
        self.filled_quantity += fill_quantity
        
        # 计算平均成交价格
        if self.avg_fill_price == 0:
            self.avg_fill_price = fill_price
        else:
            total_cost = self.avg_fill_price * (self.filled_quantity - fill_quantity) + fill_price * fill_quantity
            self.avg_fill_price = total_cost / self.filled_quantity
        
        # 更新订单状态
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.fill_time = datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def __repr__(self):
        return f"Order({self.order_id}, {self.symbol}, {self.direction.value}, {self.order_type.value}, {self.quantity} @ {self.price}, status={self.status.value})"
