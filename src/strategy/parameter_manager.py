# -*- coding: utf-8 -*-
"""
参数管理器 - 负责策略参数的动态调整
"""
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger


class ParameterManager:
    """参数管理器，负责策略参数的动态调整"""
    
    def __init__(self, strategy_engine):
        self.strategy_engine = strategy_engine
        self.param_history = {}
        
        logger.info("初始化参数管理器")
    
    def update_strategy_params(self, strategy_name: str, params: Dict[str, Any]):
        """更新策略参数"""
        # 保存参数历史
        if strategy_name not in self.param_history:
            self.param_history[strategy_name] = []
        
        self.param_history[strategy_name].append({
            'timestamp': datetime.now(),
            'params': params.copy()
        })
        
        # 更新策略参数
        self.strategy_engine.update_strategy_params(strategy_name, params)
        
        logger.info(f"更新策略参数: {strategy_name} -> {params}")
    
    def get_param_history(self, strategy_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取参数历史"""
        if strategy_name not in self.param_history:
            return []
        
        return self.param_history[strategy_name][-limit:]
    
    def reset_strategy_params(self, strategy_name: str):
        """重置策略参数"""
        strategy = self.strategy_engine.get_strategy(strategy_name)
        if strategy:
            # 获取策略的默认参数
            default_params = self._get_default_params(strategy)
            self.update_strategy_params(strategy_name, default_params)
            logger.info(f"重置策略参数: {strategy_name} -> {default_params}")
    
    def _get_default_params(self, strategy) -> Dict[str, Any]:
        """获取策略的默认参数"""
        # 实现获取默认参数的逻辑
        # 例如：从策略类的默认属性或配置文件中获取
        return {}
