# -*- coding: utf-8 -*-
"""
回测执行引擎 - 负责回测过程中的订单执行和成交模拟
"""
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.core.event import OrderEvent, FillEvent


class BacktestExecutionEngine:
    """回测执行引擎，负责回测过程中的订单执行和成交模拟"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.orders = []  # 待处理订单列表
        self.order_history = []  # 订单历史记录
        self.fill_history = []  # 成交历史记录
        
        # 回测执行参数
        self.slippage = self.config.get('slippage', 0.0)  # 滑点，默认为0
        self.commission_rate = self.config.get('commission_rate', 0.0003)  # 佣金费率，默认为0.03%
        self.min_commission = self.config.get('min_commission', 5.0)  # 最低佣金，默认为5元
        
        logger.info("初始化回测执行引擎")
    
    def execute_order(self, order: OrderEvent) -> Optional[FillEvent]:
        """执行订单
        
        Args:
            order: 订单事件
            
        Returns:
            成交事件，如果订单未成交则返回None
        """
        logger.debug(f"执行订单: {order}")
        
        # 记录订单历史
        self.order_history.append(order)
        
        # 模拟成交
        fill_event = self._simulate_fill(order)
        
        if fill_event:
            # 记录成交历史
            self.fill_history.append(fill_event)
            logger.debug(f"订单成交: {fill_event}")
        else:
            # 将订单加入待处理列表
            self.orders.append(order)
            logger.debug(f"订单未成交，加入待处理列表: {order}")
        
        return fill_event
    
    def _simulate_fill(self, order: OrderEvent) -> Optional[FillEvent]:
        """模拟订单成交
        
        Args:
            order: 订单事件
            
        Returns:
            成交事件，如果订单未成交则返回None
        """
        # 计算成交价格（考虑滑点）
        if order.order_type == 'MARKET':
            # 市价单，使用当前价格加上滑点
            fill_price = order.price * (1 + self.slippage * (1 if order.direction == 'LONG' else -1))
        elif order.order_type == 'LIMIT':
            # 限价单，只有当当前价格达到限价时才成交
            if order.direction == 'LONG' and order.price >= order.price:
                fill_price = order.price
            elif order.direction == 'SHORT' and order.price <= order.price:
                fill_price = order.price
            else:
                return None
        else:
            logger.warning(f"不支持的订单类型: {order.order_type}")
            return None
        
        # 计算佣金
        commission = max(fill_price * order.quantity * self.commission_rate, self.min_commission)
        
        # 生成成交事件
        fill_event = FillEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=fill_price,
            direction=order.direction,
            commission=commission,
            timestamp=order.timestamp
        )
        
        return fill_event
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否取消成功
        """
        for i, order in enumerate(self.orders):
            if order.order_id == order_id:
                del self.orders[i]
                logger.info(f"取消订单: {order_id}")
                return True
        
        logger.warning(f"订单未找到: {order_id}")
        return False
    
    def get_order_history(self) -> List[OrderEvent]:
        """获取订单历史记录"""
        return self.order_history
    
    def get_fill_history(self) -> List[FillEvent]:
        """获取成交历史记录"""
        return self.fill_history
    
    def get_open_orders(self) -> List[OrderEvent]:
        """获取未成交订单"""
        return self.orders
    
    def clear(self):
        """清空所有历史记录"""
        self.orders.clear()
        self.order_history.clear()
        self.fill_history.clear()
        logger.info("清空回测执行引擎历史记录")
