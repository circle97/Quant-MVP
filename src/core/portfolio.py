# -*- coding: utf-8 -*-
"""
投资组合管理 - 跟踪持仓、资金和风险
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger

from .event import SignalEvent, OrderEvent, FillEvent, EventType, event_engine


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
        
        self.update_price(price)
    
    def __repr__(self):
        side = "多" if self.quantity > 0 else "空" if self.quantity < 0 else "零"
        return (f"Position({self.symbol} {side}x{abs(self.quantity):.0f} "
                f"@{self.avg_price:.2f}, 市值:{self.market_value:.2f}, "
                f"盈亏:{self.unrealized_pnl:.2f})")


class Portfolio:
    """投资组合"""
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        初始化投资组合
        
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Position] = {}  # 持仓字典
        self.cash = initial_capital  # 可用现金
        self.total_value = initial_capital  # 总资产（现金+持仓市值）
        
        # 交易记录
        self.trades: List[Dict] = []
        self.daily_values: List[Dict] = []
        
        # A股交易成本
        self.commission_rate = 0.00025  # 佣金率 0.025%
        self.stamp_duty_rate = 0.001  # 印花税率 0.1%（仅卖出时收取）
        self.min_commission = 5.0  # 最低佣金 5元
        self.transfer_fee_rate = 0.00002  # 过户费 0.002%
        
        # 注册事件处理器
        self._register_event_handlers()
        
        logger.info(f"初始化投资组合，初始资金: {initial_capital:.2f}")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        event_engine.register_handler(EventType.FILL, self.handle_fill)
    
    def calculate_commission(self, value: float, is_buy: bool = True) -> float:
        """
        计算交易费用
        
        Args:
            value: 交易金额
            is_buy: 是否为买入交易
            
        Returns:
            交易费用
        """
        # 佣金
        commission = value * self.commission_rate
        commission = max(commission, self.min_commission)
        
        # 印花税（仅卖出时收取）
        stamp_duty = 0
        if not is_buy:
            stamp_duty = value * self.stamp_duty_rate
        
        # 过户费（沪市收取，这里简化为都收）
        transfer_fee = value * self.transfer_fee_rate
        
        total_fee = commission + stamp_duty + transfer_fee
        return total_fee
    
    def can_buy(self, symbol: str, price: float, quantity: float) -> Tuple[bool, str]:
        """
        检查是否可以买入
        
        Returns:
            (是否可以买入, 原因)
        """
        # 计算交易金额
        trade_value = price * quantity
        
        # 计算费用
        fees = self.calculate_commission(trade_value, is_buy=True)
        total_cost = trade_value + fees
        
        # 检查资金是否足够
        if total_cost > self.cash:
            return False, f"资金不足: 需要{total_cost:.2f}, 可用{self.cash:.2f}"
        
        # 检查是否为有效数量（A股最小100股）
        if quantity < 100 or quantity % 100 != 0:
            return False, f"无效数量: A股最小100股且为100的整数倍"
        
        return True, "可以买入"
    
    def can_sell(self, symbol: str, price: float, quantity: float) -> Tuple[bool, str]:
        """
        检查是否可以卖出
        
        Returns:
            (是否可以卖出, 原因)
        """
        # 检查是否有持仓
        if symbol not in self.positions:
            return False, f"没有 {symbol} 的持仓"
        
        position = self.positions[symbol]
        
        # 检查卖出数量是否超过持仓
        if quantity > position.quantity:
            return False, f"卖出数量{quantity}超过持仓{position.quantity}"
        
        # 检查是否为有效数量
        if quantity < 100 or quantity % 100 != 0:
            return False, f"无效数量: A股最小100股且为100的整数倍"
        
        return True, "可以卖出"
    
    def execute_order(self, order_event: OrderEvent) -> bool:
        """
        执行订单
        
        Args:
            order_event: 订单事件
            
        Returns:
            是否执行成功
        """
        data = order_event.data
        symbol = data['symbol']
        direction = data['direction']
        quantity = data['quantity']
        price = data['price']
        order_type = data['order_type']
        
        # 如果是市价单，使用当前价格（这里简化处理）
        if order_type == 'MARKET' and price is None:
            # 实际应该从行情获取，这里用模拟价格
            price = 10.0  # 默认价格
        
        if direction == 'LONG':  # 买入
            can_buy, reason = self.can_buy(symbol, price, quantity)
            if not can_buy:
                logger.warning(f"无法买入 {symbol}: {reason}")
                return False
            
            # 计算交易金额和费用
            trade_value = price * quantity
            fees = self.calculate_commission(trade_value, is_buy=True)
            
            # 更新持仓
            if symbol not in self.positions:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=price,
                    current_price=price,
                    market_value=trade_value,
                    unrealized_pnl=0
                )
            else:
                self.positions[symbol].add_quantity(quantity, price)
            
            # 更新资金
            self.cash -= (trade_value + fees)
            
            # 记录交易
            trade_record = {
                'timestamp': order_event.timestamp,
                'symbol': symbol,
                'action': 'BUY',
                'quantity': quantity,
                'price': price,
                'trade_value': trade_value,
                'fees': fees,
                'cash_after': self.cash
            }
            self.trades.append(trade_record)
            
            logger.info(f"执行买入: {symbol} {quantity}股 @{price:.2f}, "
                       f"费用:{fees:.2f}, 剩余现金:{self.cash:.2f}")
            
        elif direction == 'SHORT':  # 卖出（这里简化为卖出多单）
            can_sell, reason = self.can_sell(symbol, price, quantity)
            if not can_sell:
                logger.warning(f"无法卖出 {symbol}: {reason}")
                return False
            
            # 计算交易金额和费用
            trade_value = price * quantity
            fees = self.calculate_commission(trade_value, is_buy=False)
            
            # 更新持仓
            self.positions[symbol].reduce_quantity(quantity, price)
            
            # 如果持仓为0，移除该持仓
            if self.positions[symbol].quantity == 0:
                del self.positions[symbol]
            
            # 更新资金
            self.cash += (trade_value - fees)
            
            # 记录交易
            trade_record = {
                'timestamp': order_event.timestamp,
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'price': price,
                'trade_value': trade_value,
                'fees': fees,
                'cash_after': self.cash
            }
            self.trades.append(trade_record)
            
            logger.info(f"执行卖出: {symbol} {quantity}股 @{price:.2f}, "
                       f"费用:{fees:.2f}, 剩余现金:{self.cash:.2f}")
        
        # 更新总资产
        self.update_total_value(price if price else 10.0)
        
        return True
    
    def update_total_value(self, price: float = None):
        """更新总资产"""
        # 计算持仓总市值
        position_value = 0
        for symbol, position in self.positions.items():
            if price and symbol in self.positions:
                position.update_price(price)
            position_value += position.market_value
        
        # 总资产 = 现金 + 持仓市值
        self.total_value = self.cash + position_value
        self.current_capital = self.total_value
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        self.update_total_value()
        
        # 计算收益
        total_pnl = self.total_value - self.initial_capital
        total_return = (self.total_value / self.initial_capital - 1) * 100
        
        # 计算持仓比例
        position_ratio = {}
        for symbol, position in self.positions.items():
            ratio = position.market_value / self.total_value * 100
            position_ratio[symbol] = ratio
        
        summary = {
            '初始资金': self.initial_capital,
            '当前总资产': self.total_value,
            '可用现金': self.cash,
            '持仓市值': self.total_value - self.cash,
            '总盈亏': total_pnl,
            '总收益率': total_return,
            '持仓数量': len(self.positions),
            '交易次数': len(self.trades),
            '持仓比例': position_ratio
        }
        
        return summary
    
    def record_daily_value(self, timestamp: datetime = None):
        """记录每日资产"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.update_total_value()
        
        daily_record = {
            'timestamp': timestamp,
            'total_value': self.total_value,
            'cash': self.cash,
            'position_value': self.total_value - self.cash,
            'positions': len(self.positions)
        }
        
        self.daily_values.append(daily_record)
    
    def get_performance_metrics(self) -> Dict:
        """获取绩效指标"""
        if not self.daily_values:
            return {}
        
        # 转换为DataFrame
        df = pd.DataFrame(self.daily_values)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 计算日收益率
        df['daily_return'] = df['total_value'].pct_change()
        
        # 基本指标
        total_return = (df['total_value'].iloc[-1] / df['total_value'].iloc[0] - 1) * 100
        
        # 年化收益率（假设252个交易日）
        if len(df) > 1:
            days = (df.index[-1] - df.index[0]).days
            if days > 0:
                annual_return = (df['total_value'].iloc[-1] / df['total_value'].iloc[0]) ** (365 / days) - 1
                annual_return *= 100
            else:
                annual_return = 0
        else:
            annual_return = 0
        
        # 波动率
        if len(df) > 1:
            volatility = df['daily_return'].std() * np.sqrt(252) * 100
        else:
            volatility = 0
        
        # 夏普比率（无风险利率假设为3%）
        if volatility > 0:
            sharpe_ratio = (annual_return - 3) / volatility
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        df['cummax'] = df['total_value'].cummax()
        df['drawdown'] = (df['total_value'] - df['cummax']) / df['cummax'] * 100
        max_drawdown = df['drawdown'].min()
        
        metrics = {
            '总收益率': total_return,
            '年化收益率': annual_return,
            '年化波动率': volatility,
            '夏普比率': sharpe_ratio,
            '最大回撤': max_drawdown,
            '交易天数': len(df),
            '交易次数': len(self.trades)
        }
        
        return metrics
    
    def handle_fill(self, fill_event: FillEvent):
        """
        处理成交事件
        
        Args:
            fill_event: 成交事件
        """
        data = fill_event.data
        symbol = data['symbol']
        direction = data['direction']
        quantity = data['quantity']
        price = data['price']
        commission = data['commission']
        timestamp = fill_event.timestamp
        
        logger.info(f"处理成交事件: {fill_event}")
        
        if direction == 'BUY':
            # 买入成交
            self._handle_buy_fill(symbol, quantity, price, commission, timestamp)
        elif direction == 'SELL':
            # 卖出成交
            self._handle_sell_fill(symbol, quantity, price, commission, timestamp)
        
        # 更新总资产
        self.update_total_value(price)
    
    def _handle_buy_fill(self, symbol: str, quantity: float, price: float, 
                        commission: float, timestamp: datetime):
        """处理买入成交"""
        # 计算交易金额
        trade_value = price * quantity
        total_cost = trade_value + commission
        
        # 更新持仓
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                current_price=price,
                market_value=trade_value,
                unrealized_pnl=0
            )
        else:
            self.positions[symbol].add_quantity(quantity, price)
        
        # 更新资金
        self.cash -= total_cost
        
        # 记录交易
        trade_record = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'trade_value': trade_value,
            'fees': commission,
            'cash_after': self.cash
        }
        self.trades.append(trade_record)
        
        logger.info(f"买入成交: {symbol} {quantity}股 @{price:.2f}, "
                   f"费用:{commission:.2f}, 剩余现金:{self.cash:.2f}")
    
    def _handle_sell_fill(self, symbol: str, quantity: float, price: float, 
                         commission: float, timestamp: datetime):
        """处理卖出成交"""
        # 检查是否有持仓
        if symbol not in self.positions:
            logger.warning(f"卖出成交但没有 {symbol} 的持仓")
            return
        
        # 计算交易金额
        trade_value = price * quantity
        total_revenue = trade_value - commission
        
        # 更新持仓
        self.positions[symbol].reduce_quantity(quantity, price)
        
        # 如果持仓为0，移除该持仓
        if self.positions[symbol].quantity == 0:
            del self.positions[symbol]
        
        # 更新资金
        self.cash += total_revenue
        
        # 记录交易
        trade_record = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'trade_value': trade_value,
            'fees': commission,
            'cash_after': self.cash
        }
        self.trades.append(trade_record)
        
        logger.info(f"卖出成交: {symbol} {quantity}股 @{price:.2f}, "
                   f"费用:{commission:.2f}, 剩余现金:{self.cash:.2f}")
    
    def __repr__(self):
        summary = self.get_portfolio_summary()
        return (f"Portfolio(总资产:{summary['当前总资产']:.2f}, "
                f"现金:{summary['可用现金']:.2f}, "
                f"收益率:{summary['总收益率']:.2f}%)")