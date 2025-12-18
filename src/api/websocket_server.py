# -*- coding: utf-8 -*-
"""
WebSocket服务 - 提供实时数据推送
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.core.event import event_engine, EventType, FillEvent, OrderEvent, SignalEvent


class WebSocketManager:
    """
    WebSocket连接管理器，负责管理WebSocket连接和消息推送
    """
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            'default': [],
            'orders': [],
            'fills': [],
            'positions': [],
            'signals': []
        }
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """
        注册事件处理器，监听交易引擎事件
        """
        event_engine.register_handler(EventType.ORDER, self._on_order_event)
        event_engine.register_handler(EventType.FILL, self._on_fill_event)
        event_engine.register_handler(EventType.SIGNAL, self._on_signal_event)
        logger.info("WebSocket事件处理器注册完成")
    
    async def connect(self, websocket: WebSocket, channel: str = "default"):
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            channel: 连接通道，默认为default
        """
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"客户端连接到通道 {channel}, 当前连接数: {len(self.active_connections[channel])}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "default"):
        """
        断开WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            channel: 连接通道，默认为default
        """
        if channel in self.active_connections and websocket in self.active_connections[channel]:
            self.active_connections[channel].remove(websocket)
            logger.info(f"客户端从通道 {channel} 断开连接, 当前连接数: {len(self.active_connections[channel])}")
    
    async def broadcast(self, message: dict, channel: str = "default"):
        """
        向指定通道的所有客户端广播消息
        
        Args:
            message: 要广播的消息
            channel: 广播通道，默认为default
        """
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"向客户端发送消息失败: {e}")
                    self.disconnect(connection, channel)
    
    async def broadcast_all(self, message: dict):
        """
        向所有通道的所有客户端广播消息
        
        Args:
            message: 要广播的消息
        """
        for channel in self.active_connections:
            await self.broadcast(message, channel)
    
    async def _on_order_event(self, event: OrderEvent):
        """
        处理订单事件，实时推送订单状态变化
        
        Args:
            event: 订单事件
        """
        message = {
            "type": "order",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "order_id": event.data["order_id"],
                "symbol": event.data["symbol"],
                "order_type": event.data["order_type"],
                "direction": event.data["direction"],
                "quantity": event.data["quantity"],
                "price": event.data["price"],
                "status": "submitted"  # 订单事件默认为提交状态
            }
        }
        await self.broadcast(message, "orders")
        await self.broadcast(message, "default")
    
    async def _on_fill_event(self, event: FillEvent):
        """
        处理成交事件，实时推送成交记录
        
        Args:
            event: 成交事件
        """
        message = {
            "type": "fill",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "order_id": event.data["order_id"],
                "symbol": event.data["symbol"],
                "direction": event.data["direction"],
                "quantity": event.data["quantity"],
                "price": event.data["price"],
                "commission": event.data["commission"]
            }
        }
        await self.broadcast(message, "fills")
        await self.broadcast(message, "default")
    
    async def _on_signal_event(self, event: SignalEvent):
        """
        处理信号事件，实时推送交易信号
        
        Args:
            event: 信号事件
        """
        message = {
            "type": "signal",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "symbol": event.symbol,
                "signal_type": event.signal_type,
                "strength": event.strength,
                "price": event.data.get("price"),
                "strategy_name": event.data.get("strategy_name")
            }
        }
        await self.broadcast(message, "signals")
        await self.broadcast(message, "default")
    
    async def send_ping(self):
        """
        发送心跳包，保持连接活跃
        """
        message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_all(message)
    
    async def send_position_update(self, position_data: dict):
        """
        发送持仓更新消息
        
        Args:
            position_data: 持仓更新数据
        """
        message = {
            "type": "position_update",
            "timestamp": datetime.now().isoformat(),
            "data": position_data
        }
        await self.broadcast(message, "positions")
        await self.broadcast(message, "default")
    
    async def send_portfolio_update(self, portfolio_data: dict):
        """
        发送投资组合更新消息
        
        Args:
            portfolio_data: 投资组合更新数据
        """
        message = {
            "type": "portfolio_update",
            "timestamp": datetime.now().isoformat(),
            "data": portfolio_data
        }
        await self.broadcast(message, "default")


class WebSocketServer:
    """
    WebSocket服务器，提供实时数据推送服务
    """
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
    
    def get_websocket_manager(self):
        """
        获取WebSocket连接管理器
        
        Returns:
            WebSocketManager实例
        """
        return self.websocket_manager
    
    async def handle_websocket(self, websocket: WebSocket, channel: str = "default"):
        """
        处理WebSocket连接请求
        
        Args:
            websocket: WebSocket连接对象
            channel: 连接通道，默认为default
        """
        await self.websocket_manager.connect(websocket, channel)
        try:
            while True:
                # 接收客户端消息（如果需要）
                await websocket.receive_text()
                # 发送心跳响应
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
        except WebSocketDisconnect:
            self.websocket_manager.disconnect(websocket, channel)
        except Exception as e:
            logger.error(f"WebSocket连接异常: {e}")
            self.websocket_manager.disconnect(websocket, channel)
    
    def register_routes(self, app):
        """
        注册WebSocket路由
        
        Args:
            app: FastAPI应用实例
        """
        @app.websocket("/ws/{channel}")
        async def websocket_endpoint(websocket: WebSocket, channel: str = "default"):
            """
            WebSocket端点
            
            Args:
                websocket: WebSocket连接对象
                channel: 连接通道，默认为default
            """
            await self.handle_websocket(websocket, channel)
        
        logger.info("WebSocket路由注册完成")