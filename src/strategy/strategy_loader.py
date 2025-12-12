# -*- coding: utf-8 -*-
"""
策略加载器 - 支持策略热更新
"""
import os
import importlib.util
import threading
from typing import Dict, Any
from datetime import datetime
from loguru import logger

from .base import Strategy


class StrategyLoader:
    """策略加载器，支持策略热更新"""
    
    def __init__(self, strategy_engine):
        self.strategy_engine = strategy_engine
        self.strategy_modules = {}
        self.strategy_files = {}
        self.last_modified_times = {}
        
        # 启动文件监控线程，检测策略文件变化
        self.monitor_thread = threading.Thread(target=self._monitor_strategy_files)
        self.monitor_thread.daemon = True
        self.monitor_running = False
        
        logger.info("初始化策略加载器")
    
    def start_monitoring(self):
        """启动策略文件监控"""
        if not self.monitor_running:
            self.monitor_running = True
            self.monitor_thread.start()
            logger.info("启动策略文件监控")
    
    def stop_monitoring(self):
        """停止策略文件监控"""
        self.monitor_running = False
        logger.info("停止策略文件监控")
    
    def load_strategy(self, strategy_file: str, strategy_class_name: str) -> Strategy:
        """加载策略"""
        # 动态导入模块
        module_name = os.path.basename(strategy_file).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, strategy_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 获取策略类
        strategy_class = getattr(module, strategy_class_name)
        
        # 实例化策略
        strategy = strategy_class()
        
        # 保存模块和文件信息
        self.strategy_modules[strategy.name] = module
        self.strategy_files[strategy.name] = strategy_file
        self.last_modified_times[strategy.name] = os.path.getmtime(strategy_file)
        
        # 注册策略
        self.strategy_engine.register_strategy(strategy)
        
        logger.info(f"加载策略: {strategy.name} 从文件 {strategy_file}")
        return strategy
    
    def reload_strategy(self, strategy_name: str) -> Strategy:
        """重新加载策略"""
        if strategy_name not in self.strategy_files:
            raise ValueError(f"策略 {strategy_name} 未通过文件加载")
        
        strategy_file = self.strategy_files[strategy_name]
        
        # 获取策略类名
        module = self.strategy_modules[strategy_name]
        strategy_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Strategy) and attr != Strategy:
                strategy_class = attr
                break
        
        if not strategy_class:
            raise ValueError(f"在文件 {strategy_file} 中未找到策略类")
        
        # 停止旧策略
        self.strategy_engine.strategy_manager.stop_strategy(strategy_name)
        
        # 注销旧策略
        self.strategy_engine.unregister_strategy(strategy_name)
        
        # 重新加载模块
        module_name = os.path.basename(strategy_file).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, strategy_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 实例化新策略
        strategy_class = getattr(module, strategy_class.__name__)
        strategy = strategy_class()
        
        # 保存模块信息
        self.strategy_modules[strategy_name] = module
        self.last_modified_times[strategy_name] = os.path.getmtime(strategy_file)
        
        # 注册新策略
        self.strategy_engine.register_strategy(strategy)
        
        # 启动新策略
        self.strategy_engine.strategy_manager.start_strategy(strategy_name)
        
        logger.info(f"重新加载策略: {strategy_name} 从文件 {strategy_file}")
        return strategy
    
    def _monitor_strategy_files(self):
        """监控策略文件变化"""
        while self.monitor_running:
            for strategy_name, strategy_file in self.strategy_files.items():
                try:
                    current_mtime = os.path.getmtime(strategy_file)
                    if current_mtime > self.last_modified_times[strategy_name]:
                        # 文件已修改，重新加载策略
                        logger.info(f"策略文件 {strategy_file} 已修改，正在重新加载...")
                        self.reload_strategy(strategy_name)
                        logger.info(f"策略 {strategy_name} 重新加载完成")
                except Exception as e:
                    logger.error(f"监控策略文件 {strategy_file} 失败: {e}")
            
            # 每秒检查一次
            import time
            time.sleep(1)
