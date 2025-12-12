# -*- coding: utf-8 -*-
"""
策略管理器 - 管理多个策略的协调运行
"""
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.core.event import Event, BarEvent, SignalEvent, OrderEvent, TimerEvent, event_engine
from src.core.portfolio import Portfolio
from .base import Strategy


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.running = False
        
        # 注册事件处理器
        self._register_event_handlers()
        
        # 信号到订单的转换器
        self.signal_to_order_enabled = True
        
        logger.info("策略管理器初始化完成")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        event_engine.register_handler(SignalEvent, self.on_signal)
        event_engine.register_handler(TimerEvent, self.on_timer)
    
    def add_strategy(self, strategy: Strategy):
        """添加策略"""
        if strategy.name in self.strategies:
            logger.warning(f"策略 {strategy.name} 已存在，将被替换")
        
        self.strategies[strategy.name] = strategy
        logger.info(f"添加策略: {strategy.name}")
    
    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            strategy.stop()
            del self.strategies[strategy_name]
            logger.info(f"移除策略: {strategy_name}")
    
    def start_all(self):
        """启动所有策略"""
        if self.running:
            logger.warning("策略管理器已经在运行")
            return
        
        logger.info("启动所有策略...")
        
        for name, strategy in self.strategies.items():
            try:
                strategy.start()
                logger.info(f"策略 {name} 启动成功")
            except Exception as e:
                logger.error(f"策略 {name} 启动失败: {e}")
        
        # 启动事件引擎
        event_engine.start()
        self.running = True
        
        logger.info("所有策略启动完成")
    
    def stop_all(self):
        """停止所有策略"""
        if not self.running:
            return
        
        logger.info("停止所有策略...")
        
        for name, strategy in self.strategies.items():
            try:
                strategy.stop()
                logger.info(f"策略 {name} 停止成功")
            except Exception as e:
                logger.error(f"策略 {name} 停止失败: {e}")
        
        # 停止事件引擎
        event_engine.stop()
        self.running = False
        
        logger.info("所有策略停止完成")
    
    def on_signal(self, event: SignalEvent):
        """处理信号事件"""
        if not self.signal_to_order_enabled:
            return
        
        symbol = event.symbol
        signal_type = event.signal_type
        price = event.price
        
        # 这里应该根据信号生成订单
        # 实际实现中，这里会有更复杂的订单管理和风险控制
        logger.info(f"接收到信号: {event}")
        
        # 简单的信号到订单转换（示例）
        if signal_type == 'BUY':
            # 这里应该查询所有策略的持仓，决定是否下单
            order_event = OrderEvent(
                symbol=symbol,
                order_type='MARKET',
                quantity=100,  # 示例：固定100股
                direction='LONG',
                price=price,
                timestamp=event.timestamp
            )
            
            # 将订单放入事件引擎
            event_engine.put(order_event)
            
        elif signal_type == 'SELL':
            order_event = OrderEvent(
                symbol=symbol,
                order_type='MARKET',
                quantity=100,  # 示例：固定100股
                direction='SHORT',
                price=price,
                timestamp=event.timestamp
            )
            
            event_engine.put(order_event)
    
    def on_timer(self, event: TimerEvent):
        """处理定时器事件"""
        # 定期更新策略状态
        for strategy in self.strategies.values():
            if strategy.running:
                # 记录每日资产
                strategy.portfolio.record_daily_value(event.timestamp)
    
    def get_strategy(self, name: str) -> Optional[Strategy]:
        """获取策略"""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> List[Strategy]:
        """获取所有策略"""
        return list(self.strategies.values())
    
    def get_strategies_status(self) -> Dict:
        """获取所有策略状态"""
        status = {}
        
        for name, strategy in self.strategies.items():
            status[name] = {
                'running': strategy.running,
                **strategy.get_strategy_state()
            }
        
        return status
    
    def get_combined_portfolio(self) -> Portfolio:
        """获取合并的投资组合（所有策略的汇总）"""
        # 创建一个新的投资组合来汇总
        total_initial = sum(s.initial_capital for s in self.strategies.values())
        combined = Portfolio(total_initial)
        
        # 这里应该汇总所有策略的持仓和交易记录
        # 简化实现：只返回第一个策略的组合（如果有）
        if self.strategies:
            first_strategy = next(iter(self.strategies.values()))
            return first_strategy.portfolio
        
        return combined
    
    def __repr__(self):
        return f"StrategyManager(策略数量:{len(self.strategies)}, 运行中:{self.running})"


# 全局策略管理器实例
strategy_manager = StrategyManager()