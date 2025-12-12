# -*- coding: utf-8 -*-
"""
双均线交叉策略
当短期均线上穿长期均线时买入，下穿时卖出
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from loguru import logger

from .base import AStockTradingStrategy


class MACrossStrategy(AStockTradingStrategy):
    """双均线交叉策略"""
    
    def __init__(self, symbols: List[str], initial_capital: float = 10000.0,
                 fast_period: int = 10, slow_period: int = 30):
        """
        初始化双均线策略
        
        Args:
            symbols: 交易股票列表
            initial_capital: 初始资金
            fast_period: 快线周期
            slow_period: 慢线周期
        """
        name = f"MA交叉策略({fast_period}/{slow_period})"
        super().__init__(name, symbols, initial_capital)
        
        # 策略参数
        self.params.update({
            'fast_period': fast_period,
            'slow_period': slow_period,
            'position_ratio': 0.8,  # 每次开仓比例
            'stop_loss': 0.08,  # 止损比例
            'take_profit': 0.15  # 止盈比例
        })
        
        # 策略状态
        self.ma_fast = {}  # 快线值
        self.ma_slow = {}  # 慢线值
        self.position_signal = {}  # 持仓信号（1: 持多, 0: 空仓, -1: 持空）
        
        logger.info(f"创建双均线策略: 快线={fast_period}, 慢线={slow_period}")
    
    def on_init(self):
        """策略初始化"""
        logger.info(f"双均线策略初始化: {self.name}")
        
        # 为每个股票初始化状态
        for symbol in self.symbols:
            if symbol in self.data and not self.data[symbol].empty:
                df = self.data[symbol]
                
                # 计算移动平均线
                df['ma_fast'] = df['close'].rolling(window=self.params['fast_period']).mean()
                df['ma_slow'] = df['close'].rolling(window=self.params['slow_period']).mean()
                
                # 初始化信号
                self.position_signal[symbol] = 0
                
                # 如果有足够数据，计算初始均线值
                if len(df) >= self.params['slow_period']:
                    self.ma_fast[symbol] = df['ma_fast'].iloc[-1]
                    self.ma_slow[symbol] = df['ma_slow'].iloc[-1]
                    
                    # 根据历史数据确定初始信号
                    if self.ma_fast[symbol] > self.ma_slow[symbol]:
                        self.position_signal[symbol] = 1
                    else:
                        self.position_signal[symbol] = 0
                
                logger.info(f"初始化 {symbol}: 快线={self.ma_fast.get(symbol, 0):.2f}, "
                           f"慢线={self.ma_slow.get(symbol, 0):.2f}, "
                           f"信号={self.position_signal[symbol]}")
    
    def on_bar(self, event):
        """处理K线数据"""
        if not self.running:
            return
        
        symbol = event.symbol
        bar_data = event.bar_data
        
        # 更新数据
        if symbol not in self.data:
            self.data[symbol] = pd.DataFrame()
        
        # 添加新数据（这里简化处理，实际应该追加）
        new_row = pd.DataFrame([bar_data], index=[event.timestamp])
        if self.data[symbol].empty:
            self.data[symbol] = new_row
        else:
            self.data[symbol] = pd.concat([self.data[symbol], new_row])
        
        # 确保数据足够计算
        if len(self.data[symbol]) < max(self.params['slow_period'], self.params['fast_period']):
            return
        
        # 更新当前价格
        current_price = bar_data.get('close', 0)
        self.current_prices[symbol] = current_price
        
        # 计算移动平均线
        df = self.data[symbol]
        ma_fast = df['close'].rolling(window=self.params['fast_period']).mean().iloc[-1]
        ma_slow = df['close'].rolling(window=self.params['slow_period']).mean().iloc[-1]
        
        # 保存均线值
        prev_ma_fast = self.ma_fast.get(symbol, 0)
        prev_ma_slow = self.ma_slow.get(symbol, 0)
        self.ma_fast[symbol] = ma_fast
        self.ma_slow[symbol] = ma_slow
        
        # 获取之前的信号
        prev_signal = self.position_signal.get(symbol, 0)
        
        # 检查均线交叉
        if prev_ma_fast <= prev_ma_slow and ma_fast > ma_slow:
            # 金叉：快线上穿慢线
            logger.info(f"{symbol} 金叉信号: 快线{ma_fast:.2f} > 慢线{ma_slow:.2f}")
            self._handle_golden_cross(symbol, current_price)
            self.position_signal[symbol] = 1
            
        elif prev_ma_fast >= prev_ma_slow and ma_fast < ma_slow:
            # 死叉：快线下穿慢线
            logger.info(f"{symbol} 死叉信号: 快线{ma_fast:.2f} < 慢线{ma_slow:.2f}")
            self._handle_dead_cross(symbol, current_price)
            self.position_signal[symbol] = 0
        
        # 检查止损止盈
        self._check_stop_loss_take_profit(symbol, current_price)
    
    def _handle_golden_cross(self, symbol: str, price: float):
        """处理金叉信号"""
        # 检查是否已有持仓
        position = self.get_position(symbol)
        
        if position and position.quantity > 0:
            logger.debug(f"{symbol} 已有持仓，不重复买入")
            return
        
        # 检查交易规则
        quantity = self.calculate_position_size(symbol, price)
        can_trade, reason = self.check_trading_rules(symbol, 'BUY', quantity, price)
        
        if not can_trade:
            logger.warning(f"{symbol} 无法买入: {reason}")
            return
        
        # 生成买入信号
        self.generate_signal(symbol, 'BUY', strength=1.0, price=price)
        logger.info(f"{symbol} 生成买入信号: {quantity}股 @{price:.2f}")
    
    def _handle_dead_cross(self, symbol: str, price: float):
        """处理死叉信号"""
        # 检查是否有持仓
        position = self.get_position(symbol)
        
        if not position or position.quantity <= 0:
            logger.debug(f"{symbol} 没有持仓，无需卖出")
            return
        
        # 计算卖出数量（平仓）
        quantity = position.quantity
        
        # 检查交易规则
        can_trade, reason = self.check_trading_rules(symbol, 'SELL', quantity, price)
        
        if not can_trade:
            logger.warning(f"{symbol} 无法卖出: {reason}")
            return
        
        # 生成卖出信号
        self.generate_signal(symbol, 'SELL', strength=1.0, price=price)
        logger.info(f"{symbol} 生成卖出信号: {quantity}股 @{price:.2f}")
    
    def _check_stop_loss_take_profit(self, symbol: str, price: float):
        """检查止损止盈"""
        position = self.get_position(symbol)
        
        if not position or position.quantity <= 0:
            return
        
        # 计算盈亏比例
        profit_ratio = (price - position.avg_price) / position.avg_price
        
        # 止损检查
        if profit_ratio < -self.params['stop_loss']:
            logger.warning(f"{symbol} 触发止损: 成本{position.avg_price:.2f}, "
                          f"当前{price:.2f}, 亏损{profit_ratio:.2%}")
            self.generate_signal(symbol, 'SELL', strength=1.0, price=price)
        
        # 止盈检查
        elif profit_ratio > self.params['take_profit']:
            logger.info(f"{symbol} 触发止盈: 成本{position.avg_price:.2f}, "
                       f"当前{price:.2f}, 盈利{profit_ratio:.2%}")
            self.generate_signal(symbol, 'SELL', strength=0.8, price=price)
    
    def get_strategy_state(self) -> Dict:
        """获取策略状态（扩展版）"""
        base_state = super().get_strategy_state()
        
        # 添加均线策略特有信息
        ma_info = {}
        for symbol in self.symbols:
            if symbol in self.ma_fast and symbol in self.ma_slow:
                ma_info[symbol] = {
                    'ma_fast': self.ma_fast[symbol],
                    'ma_slow': self.ma_slow[symbol],
                    'signal': self.position_signal.get(symbol, 0),
                    'current_price': self.current_prices.get(symbol, 0)
                }
        
        base_state.update({
            'params': self.params,
            'ma_info': ma_info
        })
        
        return base_state


class EnhancedMACrossStrategy(MACrossStrategy):
    """增强版双均线策略（带过滤器和仓位管理）"""
    
    def __init__(self, symbols: List[str], initial_capital: float = 10000.0,
                 fast_period: int = 10, slow_period: int = 30,
                 filter_period: int = 50):
        """
        初始化增强版双均线策略
        
        Args:
            filter_period: 趋势过滤器周期（长期均线）
        """
        super().__init__(symbols, initial_capital, fast_period, slow_period)
        
        self.name = f"增强MA策略({fast_period}/{slow_period}+{filter_period})"
        self.params['filter_period'] = filter_period
        
        # 趋势过滤器
        self.trend_filter = {}
        
        logger.info(f"创建增强版双均线策略: 过滤器={filter_period}")
    
    def on_init(self):
        """策略初始化"""
        super().on_init()
        
        # 初始化趋势过滤器
        for symbol in self.symbols:
            if symbol in self.data and not self.data[symbol].empty:
                df = self.data[symbol]
                
                # 计算长期趋势线
                df['ma_trend'] = df['close'].rolling(window=self.params['filter_period']).mean()
                
                if len(df) >= self.params['filter_period']:
                    self.trend_filter[symbol] = df['ma_trend'].iloc[-1]
    
    def _handle_golden_cross(self, symbol: str, price: float):
        """处理金叉信号（带趋势过滤）"""
        # 检查趋势：价格要在长期均线之上才做多
        if symbol in self.trend_filter and price < self.trend_filter[symbol]:
            logger.debug(f"{symbol} 价格{price:.2f}在长期均线{self.trend_filter[symbol]:.2f}之下，放弃买入")
            return
        
        # 调用父类方法
        super()._handle_golden_cross(symbol, price)
    
    def calculate_position_size(self, symbol: str, price: float, risk_ratio: float = 0.02) -> int:
        """计算头寸大小（考虑趋势强度）"""
        base_size = super().calculate_position_size(symbol, price, risk_ratio)
        
        # 根据趋势强度调整仓位
        if symbol in self.trend_filter:
            trend_strength = abs(price - self.trend_filter[symbol]) / self.trend_filter[symbol]
            
            # 趋势越强，仓位越大（但不超过2倍）
            trend_multiplier = min(1.0 + trend_strength * 5, 2.0)
            adjusted_size = int(base_size * trend_multiplier)
            
            # 确保是100的倍数
            adjusted_size = adjusted_size // 100 * 100
            
            return adjusted_size
        
        return base_size