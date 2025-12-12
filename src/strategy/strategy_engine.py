# -*- coding: utf-8 -*-
"""
策略引擎 - 负责策略的执行和事件分发
"""
from typing import Dict, Any
from datetime import datetime
from loguru import logger

from src.core.event import event_engine
from .base import Strategy
from .strategy_manager import StrategyManager
from .strategy_loader import StrategyLoader
from .strategy_scheduler import StrategyScheduler
from .parameter_manager import ParameterManager


class StrategyEngine:
    """策略引擎核心，负责策略的执行和事件分发"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.strategies = {}
        self.strategy_manager = StrategyManager()
        self.strategy_loader = StrategyLoader(self)
        self.strategy_scheduler = StrategyScheduler(self)
        self.parameter_manager = ParameterManager(self)
        self.running = False
        
        logger.info("初始化策略引擎")
    
    def start(self):
        """启动策略引擎"""
        if self.running:
            logger.warning("策略引擎已经在运行")
            return
        
        logger.info("启动策略引擎...")
        
        self.running = True
        
        # 启动策略调度器
        self.strategy_scheduler.start()
        
        # 启动策略文件监控（如果配置启用）
        if self.config.get('hot_reload', {}).get('enabled', False):
            self.strategy_loader.start_monitoring()
        
        # 启动所有已注册的策略
        for strategy_name in self.strategies:
            self.strategy_manager.start_strategy(strategy_name)
        
        logger.info("策略引擎启动完成")
    
    def stop(self):
        """停止策略引擎"""
        if not self.running:
            logger.warning("策略引擎已经停止")
            return
        
        logger.info("停止策略引擎...")
        
        self.running = False
        
        # 停止所有策略
        for strategy_name in self.strategies:
            self.strategy_manager.stop_strategy(strategy_name)
        
        # 停止策略调度器
        self.strategy_scheduler.stop()
        
        # 停止策略文件监控
        self.strategy_loader.stop_monitoring()
        
        logger.info("策略引擎停止完成")
    
    def register_strategy(self, strategy: Strategy):
        """注册策略"""
        if strategy.name in self.strategies:
            raise ValueError(f"策略 {strategy.name} 已存在")
        
        self.strategies[strategy.name] = strategy
        self.strategy_manager.add_strategy(strategy)
        logger.info(f"注册策略: {strategy.name}")
    
    def unregister_strategy(self, strategy_name: str):
        """注销策略"""
        if strategy_name not in self.strategies:
            raise ValueError(f"策略 {strategy_name} 不存在")
        
        self.strategy_manager.remove_strategy(strategy_name)
        del self.strategies[strategy_name]
        logger.info(f"注销策略: {strategy_name}")
    
    def get_strategy(self, strategy_name: str) -> Strategy:
        """获取策略实例"""
        return self.strategies.get(strategy_name)
    
    def get_all_strategies(self) -> Dict[str, Strategy]:
        """获取所有策略实例"""
        return self.strategies.copy()
    
    def update_strategy_params(self, strategy_name: str, params: Dict[str, Any]):
        """更新策略参数"""
        strategy = self.get_strategy(strategy_name)
        if strategy:
            strategy.update_params(params)
            logger.info(f"更新策略参数: {strategy_name} -> {params}")
    
    def reload_strategy(self, strategy_name: str):
        """重新加载策略"""
        return self.strategy_loader.reload_strategy(strategy_name)
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            'running': self.running,
            'strategy_count': len(self.strategies),
            'running_strategies': [name for name, strategy in self.strategies.items() if strategy.running],
            'paused_strategies': [name for name, strategy in self.strategies.items() if strategy.paused]
        }


# 全局策略引擎实例
strategy_engine = StrategyEngine()
