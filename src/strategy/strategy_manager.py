# -*- coding: utf-8 -*-
"""
策略管理器 - 管理多个策略的协调运行
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from src.core.event import Event, BarEvent, SignalEvent, OrderEvent, TimerEvent, EventType, event_engine
from src.core.portfolio import Portfolio
from .base import Strategy


class StrategyManager:
    """策略管理器，负责策略的注册、启动、停止和监控"""
    
    def __init__(self, strategy_engine=None):
        self.strategy_engine = strategy_engine
        self.registered_strategies: Dict[str, Strategy] = {}
        self.strategy_stats: Dict[str, Dict] = {}
        self.running = False
        
        # 注册事件处理器
        self._register_event_handlers()
        
        # 信号到订单的转换器
        self.signal_to_order_enabled = True
        
        logger.info("策略管理器初始化完成")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        event_engine.register_handler(EventType.SIGNAL, self.on_signal)
        event_engine.register_handler(EventType.TIMER, self.on_timer)
    
    def register_strategy(self, strategy: Strategy):
        """注册策略"""
        self.registered_strategies[strategy.name] = strategy
        self.strategy_stats[strategy.name] = {
            'start_time': None,
            'stop_time': None,
            'run_count': 0,
            'error_count': 0
        }
        logger.info(f"注册策略: {strategy.name}")
    
    def unregister_strategy(self, strategy_name: str):
        """注销策略"""
        if strategy_name in self.registered_strategies:
            del self.registered_strategies[strategy_name]
            del self.strategy_stats[strategy_name]
            logger.info(f"注销策略: {strategy_name}")
    
    def add_strategy(self, strategy: Strategy):
        """添加策略（兼容旧接口）"""
        self.register_strategy(strategy)
    
    def remove_strategy(self, strategy_name: str):
        """移除策略（兼容旧接口）"""
        if strategy_name in self.registered_strategies:
            strategy = self.registered_strategies[strategy_name]
            strategy.stop()
            self.unregister_strategy(strategy_name)
            logger.info(f"移除策略: {strategy_name}")
    
    def start_strategy(self, strategy_name: str):
        """启动单个策略"""
        strategy = self.registered_strategies.get(strategy_name)
        if strategy and not strategy.running:
            try:
                strategy.start()
                self.strategy_stats[strategy_name]['start_time'] = datetime.now()
                self.strategy_stats[strategy_name]['run_count'] += 1
                logger.info(f"策略 {strategy_name} 启动成功")
                return True
            except Exception as e:
                logger.error(f"启动策略 {strategy_name} 失败: {e}")
                self.strategy_stats[strategy_name]['error_count'] += 1
        return False
    
    def stop_strategy(self, strategy_name: str):
        """停止单个策略"""
        strategy = self.registered_strategies.get(strategy_name)
        if strategy and strategy.running:
            try:
                strategy.stop()
                self.strategy_stats[strategy_name]['stop_time'] = datetime.now()
                logger.info(f"策略 {strategy_name} 停止成功")
                return True
            except Exception as e:
                logger.error(f"停止策略 {strategy_name} 失败: {e}")
                self.strategy_stats[strategy_name]['error_count'] += 1
        return False
    
    def pause_strategy(self, strategy_name: str):
        """暂停单个策略"""
        strategy = self.registered_strategies.get(strategy_name)
        if strategy and strategy.running and not strategy.paused:
            try:
                strategy.pause()
                logger.info(f"策略 {strategy_name} 暂停成功")
                return True
            except Exception as e:
                logger.error(f"暂停策略 {strategy_name} 失败: {e}")
                self.strategy_stats[strategy_name]['error_count'] += 1
        return False
    
    def resume_strategy(self, strategy_name: str):
        """恢复单个策略"""
        strategy = self.registered_strategies.get(strategy_name)
        if strategy and strategy.running and strategy.paused:
            try:
                strategy.resume()
                logger.info(f"策略 {strategy_name} 恢复成功")
                return True
            except Exception as e:
                logger.error(f"恢复策略 {strategy_name} 失败: {e}")
                self.strategy_stats[strategy_name]['error_count'] += 1
        return False
    
    def update_strategy_params(self, strategy_name: str, params: dict):
        """更新策略参数"""
        strategy = self.registered_strategies.get(strategy_name)
        if strategy:
            try:
                strategy.update_params(params)
                logger.info(f"策略 {strategy_name} 参数更新成功: {params}")
                return True
            except Exception as e:
                logger.error(f"策略 {strategy_name} 参数更新失败: {e}")
                self.strategy_stats[strategy_name]['error_count'] += 1
        return False
    
    def start_all(self):
        """启动所有策略"""
        if self.running:
            logger.warning("策略管理器已经在运行")
            return
        
        logger.info("启动所有策略...")
        
        for name, strategy in self.registered_strategies.items():
            try:
                self.start_strategy(name)
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
        
        for name, strategy in self.registered_strategies.items():
            try:
                self.stop_strategy(name)
            except Exception as e:
                logger.error(f"策略 {name} 停止失败: {e}")
        
        # 停止事件引擎
        event_engine.stop()
        self.running = False
        
        logger.info("所有策略停止完成")
    
    def get_strategy_status(self, strategy_name: str) -> Dict[str, Any]:
        """获取策略状态"""
        strategy = self.registered_strategies.get(strategy_name)
        if not strategy:
            return None
        
        return {
            'state': self._get_strategy_state(strategy),
            'portfolio': strategy.portfolio.get_portfolio_summary(),
            'params': strategy.params,
            'stats': strategy.stats,
            'manager_stats': self.strategy_stats[strategy_name]
        }
    
    def get_all_strategy_status(self) -> Dict[str, Any]:
        """获取所有策略状态"""
        status = {}
        for strategy_name in self.registered_strategies:
            status[strategy_name] = self.get_strategy_status(strategy_name)
        return status
    
    def _get_strategy_state(self, strategy: Strategy) -> str:
        """获取策略状态字符串"""
        if not strategy.initialized:
            return "未初始化"
        if not strategy.running:
            return "已停止"
        if strategy.paused:
            return "已暂停"
        return "运行中"
    
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
        for strategy in self.registered_strategies.values():
            if strategy.running:
                # 记录每日资产
                strategy.portfolio.record_daily_value(event.timestamp)
    
    def get_strategy(self, name: str) -> Optional[Strategy]:
        """获取策略"""
        return self.registered_strategies.get(name)
    
    def get_all_strategies(self) -> List[Strategy]:
        """获取所有策略"""
        return list(self.registered_strategies.values())
    
    def get_strategies_status(self) -> Dict:
        """获取所有策略状态（兼容旧接口）"""
        return self.get_all_strategy_status()
    
    def get_combined_portfolio(self) -> Portfolio:
        """获取合并的投资组合（所有策略的汇总）"""
        # 创建一个新的投资组合来汇总
        total_initial = sum(s.initial_capital for s in self.registered_strategies.values())
        combined = Portfolio(total_initial)
        
        # 这里应该汇总所有策略的持仓和交易记录
        # 简化实现：只返回第一个策略的组合（如果有）
        if self.registered_strategies:
            first_strategy = next(iter(self.registered_strategies.values()))
            return first_strategy.portfolio
        
        return combined
    
    def __repr__(self):
        return f"StrategyManager(策略数量:{len(self.registered_strategies)}, 运行中:{self.running})"


# 全局策略管理器实例
strategy_manager = StrategyManager()