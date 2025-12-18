# -*- coding: utf-8 -*-
"""
API客户端 - 用于与交易引擎的REST API通信
"""
import requests
from typing import Dict, List, Optional
from loguru import logger


class APIClient:
    """
    API客户端类，用于与交易引擎的REST API通信
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化API客户端
        
        Args:
            base_url: API服务的基础URL，默认为http://localhost:8000
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 5.0
        logger.info(f"初始化API客户端，基础URL: {base_url}")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """
        发送API请求
        
        Args:
            endpoint: API端点路径
            method: 请求方法，默认为GET
            data: 请求数据，默认为None
        
        Returns:
            API响应数据
        
        Raises:
            requests.exceptions.RequestException: 请求失败时抛出异常
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, json=data)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, json=data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {url} - {e}")
            # 返回空数据，让调用者处理
            return {}
    
    def get_system_status(self) -> Dict:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        return self._make_request("/api/v1/status")
    
    def get_portfolio_summary(self) -> Dict:
        """
        获取投资组合摘要
        
        Returns:
            投资组合摘要信息
        """
        return self._make_request("/api/v1/portfolio")
    
    def get_positions(self) -> List[Dict]:
        """
        获取持仓信息
        
        Returns:
            持仓列表
        """
        return self._make_request("/api/v1/positions")
    
    def get_orders(self, symbol: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """
        获取订单列表
        
        Args:
            symbol: 标的代码，可选
            status: 订单状态，可选
        
        Returns:
            订单列表
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        if status:
            params["status"] = status
        
        return self._make_request(f"/api/v1/orders?symbol={symbol}&status={status}" if params else "/api/v1/orders")
    
    def get_strategies(self) -> List[Dict]:
        """
        获取策略列表
        
        Returns:
            策略列表
        """
        return self._make_request("/api/v1/strategies")
    
    def get_performance_metrics(self) -> Dict:
        """
        获取绩效指标
        
        Returns:
            绩效指标信息
        """
        return self._make_request("/api/v1/performance")
    
    def get_system_info(self) -> Dict:
        """
        获取系统信息
        
        Returns:
            系统信息
        """
        return self._make_request("/api/v1/system/status")
    
    def create_order(self, order_request: Dict) -> Dict:
        """
        创建订单
        
        Args:
            order_request: 订单请求数据
        
        Returns:
            订单创建结果
        """
        return self._make_request("/api/v1/orders", method="POST", data=order_request)
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        取消订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            订单取消结果
        """
        return self._make_request(f"/api/v1/orders/{order_id}", method="DELETE")
    
    def start_strategy(self, strategy_name: str) -> Dict:
        """
        启动策略
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            策略启动结果
        """
        return self._make_request(f"/api/v1/strategies/{strategy_name}/start", method="POST")
    
    def stop_strategy(self, strategy_name: str) -> Dict:
        """
        停止策略
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            策略停止结果
        """
        return self._make_request(f"/api/v1/strategies/{strategy_name}/stop", method="POST")
