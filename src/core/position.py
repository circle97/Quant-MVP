# -*- coding: utf-8 -*-
"""
持仓数据结构
"""
from dataclasses import dataclass


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: float  # 持仓数量（正数表示多头，负数表示空头）
    avg_price: float  # 平均成本价
    current_price: float  # 当前价格
    market_value: float  # 市值
    unrealized_pnl: float  # 未实现盈亏
    realized_pnl: float = 0.0  # 已实现盈亏
    
    def update_price(self, price: float):
        """更新价格并重新计算盈亏"""
        self.current_price = price
        self.market_value = self.quantity * price
        self.unrealized_pnl = self.quantity * (price - self.avg_price)
    
    def add_quantity(self, quantity: float, price: float):
        """增加持仓（买入）"""
        if self.quantity + quantity == 0:
            # 平仓
            realized = self.quantity * (price - self.avg_price)
            self.realized_pnl += realized
            self.quantity = 0
            self.avg_price = 0
            self.market_value = 0
            self.unrealized_pnl = 0
        else:
            # 计算新的平均成本
            total_cost = self.quantity * self.avg_price + quantity * price
            self.quantity += quantity
            self.avg_price = total_cost / self.quantity if self.quantity != 0 else 0
            self.update_price(price)
    
    def reduce_quantity(self, quantity: float, price: float):
        """减少持仓（卖出）"""
        # 卖出数量不能超过持仓
        quantity_to_sell = min(abs(quantity), abs(self.quantity))
        if self.quantity > 0:  # 多单
            quantity_to_sell = min(quantity_to_sell, self.quantity)
            realized = quantity_to_sell * (price - self.avg_price)
        else:  # 空单
            quantity_to_sell = min(quantity_to_sell, abs(self.quantity))
            realized = quantity_to_sell * (self.avg_price - price)
        
        self.realized_pnl += realized
        self.quantity -= quantity_to_sell if self.quantity > 0 else -quantity_to_sell
        
        if self.quantity == 0:
            self.avg_price = 0
            self.market_value = 0
            self.unrealized_pnl = 0
        else:
            self.update_price(price)
    
    def __repr__(self):
        side = "多" if self.quantity > 0 else "空" if self.quantity < 0 else "零"
        return (f"Position({self.symbol} {side}x{abs(self.quantity):.0f} "
                f"@{self.avg_price:.2f}, 市值:{self.market_value:.2f}, "
                f"盈亏:{self.unrealized_pnl:.2f})")