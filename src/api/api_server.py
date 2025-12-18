# -*- coding: utf-8 -*-
"""
API服务器 - 整合REST API和WebSocket服务
"""
import uvicorn
from fastapi import FastAPI
from threading import Thread
from loguru import logger
from typing import Dict, Optional

from src.api.rest_api import RESTAPIServer
from src.api.websocket_server import WebSocketServer
from src.core.execution_engine import ExecutionEngine
from src.core.portfolio import Portfolio
from src.strategy.strategy_engine import StrategyEngine
from src.core.state_manager import StateManager


class APIServer:
    """
    API服务器，整合REST API和WebSocket服务
    """
    
    def __init__(self, 
                 execution_engine: ExecutionEngine = None,
                 portfolio: Portfolio = None,
                 strategy_engine: StrategyEngine = None,
                 state_manager: StateManager = None):
        """
        初始化API服务器
        
        Args:
            execution_engine: 执行引擎实例
            portfolio: 投资组合实例
            strategy_engine: 策略引擎实例
            state_manager: 状态管理器实例
        """
        # 初始化REST API服务器
        self.rest_api = RESTAPIServer(
            execution_engine=execution_engine,
            portfolio=portfolio,
            strategy_engine=strategy_engine,
            state_manager=state_manager
        )
        
        # 初始化WebSocket服务器
        self.websocket_server = WebSocketServer()
        
        # 获取FastAPI应用实例
        self.app = self.rest_api.get_app()
        
        # 注册WebSocket路由
        self.websocket_server.register_routes(self.app)
        
        # 服务器配置
        self.config = {
            'host': '0.0.0.0',
            'port': 8000,
            'log_level': 'info'
        }
        
        # 服务器线程
        self.server_thread: Optional[Thread] = None
        self.running = False
        
        logger.info("API服务器初始化完成")
    
    def start(self, blocking: bool = False):
        """
        启动API服务器
        
        Args:
            blocking: 是否阻塞运行，默认为False（后台运行）
        """
        if self.running:
            logger.warning("API服务器已经在运行中")
            return
        
        logger.info(f"启动API服务器，监听 {self.config['host']}:{self.config['port']}")
        
        if blocking:
            # 阻塞运行，直接启动服务器
            uvicorn.run(
                self.app,
                host=self.config['host'],
                port=self.config['port'],
                log_level=self.config['log_level'],
                access_log=False
            )
        else:
            # 后台运行，创建线程
            self.server_thread = Thread(
                target=uvicorn.run,
                args=(self.app,),
                kwargs={
                    'host': self.config['host'],
                    'port': self.config['port'],
                    'log_level': self.config['log_level'],
                    'access_log': False
                },
                daemon=True
            )
            self.server_thread.start()
            self.running = True
    
    def stop(self):
        """
        停止API服务器
        """
        if not self.running:
            logger.warning("API服务器未在运行中")
            return
        
        logger.info("停止API服务器")
        
        # Uvicorn没有提供优雅停止的API，只能等待线程自然结束
        # 这里我们只是标记服务器为停止状态
        self.running = False
    
    def get_status(self) -> Dict:
        """
        获取API服务器状态
        
        Returns:
            服务器状态信息
        """
        return {
            'running': self.running,
            'host': self.config['host'],
            'port': self.config['port'],
            'config': self.config
        }
    
    def set_config(self, config: Dict):
        """
        更新服务器配置
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        logger.info(f"API服务器配置更新: {self.config}")


# 单例API服务器实例
_api_server_instance = None


def get_api_server(
    execution_engine: ExecutionEngine = None,
    portfolio: Portfolio = None,
    strategy_engine: StrategyEngine = None,
    state_manager: StateManager = None
) -> APIServer:
    """
    获取API服务器单例实例
    
    Args:
        execution_engine: 执行引擎实例
        portfolio: 投资组合实例
        strategy_engine: 策略引擎实例
        state_manager: 状态管理器实例
    
    Returns:
        APIServer实例
    """
    global _api_server_instance
    if _api_server_instance is None:
        _api_server_instance = APIServer(
            execution_engine=execution_engine,
            portfolio=portfolio,
            strategy_engine=strategy_engine,
            state_manager=state_manager
        )
    return _api_server_instance