# -*- coding: utf-8 -*-
"""
REST API服务 - 提供交易引擎的HTTP接口
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from src.core.execution_engine import ExecutionEngine
from src.core.portfolio import Portfolio
from src.strategy.strategy_engine import StrategyEngine
from src.core.state_manager import StateManager
from src.core.transaction_manager import TransactionManager


class OrderRequest(BaseModel):
    """订单请求模型"""
    symbol: str
    order_type: str
    direction: str
    quantity: float
    price: Optional[float] = None
    strategy_name: Optional[str] = None
    account_id: Optional[str] = "default"


class OrderResponse(BaseModel):
    """订单响应模型"""
    order_id: str
    status: str
    message: str


class StrategyStatus(BaseModel):
    """策略状态模型"""
    strategy_name: str
    running: bool
    paused: bool
    params: Dict


class PortfolioSummary(BaseModel):
    """投资组合摘要模型"""
    total_value: float
    cash: float
    positions: int
    total_return: float
    daily_return: float


class PositionInfo(BaseModel):
    """持仓信息模型"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float


class RESTAPIServer:
    """REST API服务器"""
    
    def __init__(self, 
                 execution_engine: ExecutionEngine = None,
                 portfolio: Portfolio = None,
                 strategy_engine: StrategyEngine = None,
                 state_manager: StateManager = None):
        """
        初始化REST API服务器
        
        Args:
            execution_engine: 执行引擎实例
            portfolio: 投资组合实例
            strategy_engine: 策略引擎实例
            state_manager: 状态管理器实例
        """
        self.app = FastAPI(title="量化交易引擎API", version="1.0.0")
        self.execution_engine = execution_engine
        self.portfolio = portfolio
        self.strategy_engine = strategy_engine
        self.state_manager = state_manager
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册API路由"""
        @self.app.get("/", tags=["系统状态"])
        def root():
            """API根路径，返回API信息和文档链接"""
            return {
                "message": "Quant-MVP API Service",
                "version": "1.0.0",
                "docs": {
                    "swagger_ui": "/docs",
                    "redoc": "/redoc"
                },
                "endpoints": {
                    "status": "/api/v1/status",
                    "portfolio": "/api/v1/portfolio",
                    "positions": "/api/v1/positions",
                    "orders": "/api/v1/orders",
                    "strategies": "/api/v1/strategies"
                }
            }
        
        @self.app.get("/api/v1/status", tags=["系统状态"])
        def get_system_status():
            """获取系统状态"""
            return {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "execution_engine": True,
                    "portfolio": True,
                    "strategy_engine": self.strategy_engine.running if self.strategy_engine else False
                }
            }
        
        @self.app.get("/api/v1/portfolio", response_model=PortfolioSummary, tags=["投资组合"])
        def get_portfolio_summary():
            """获取投资组合摘要"""
            if not self.portfolio:
                raise HTTPException(status_code=500, detail="投资组合未初始化")
            
            summary = self.portfolio.get_portfolio_summary()
            return PortfolioSummary(
                total_value=summary["当前总资产"],
                cash=summary["可用现金"],
                positions=summary["持仓数量"],
                total_return=summary["总收益率"],
                daily_return=0.0  # 暂时返回0，后续可以实现日收益率计算
            )
        
        @self.app.get("/api/v1/positions", response_model=List[PositionInfo], tags=["投资组合"])
        def get_positions():
            """获取所有持仓"""
            if not self.portfolio:
                raise HTTPException(status_code=500, detail="投资组合未初始化")
            
            positions = self.portfolio.get_all_positions()
            return [
                PositionInfo(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    avg_price=pos.avg_price,
                    current_price=pos.current_price,
                    market_value=pos.market_value,
                    unrealized_pnl=pos.unrealized_pnl,
                    realized_pnl=pos.realized_pnl
                ) for pos in positions
            ]
        
        @self.app.get("/api/v1/orders", tags=["订单管理"])
        def get_orders(symbol: Optional[str] = None, status: Optional[str] = None):
            """获取订单列表"""
            if not self.execution_engine:
                raise HTTPException(status_code=500, detail="执行引擎未初始化")
            
            filters = {}
            if symbol:
                filters["symbol"] = symbol
            if status:
                filters["status"] = status
            
            orders = self.execution_engine.get_all_orders(filters=filters)
            return [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "order_type": order.order_type.value,
                    "direction": order.direction.value,
                    "quantity": order.quantity,
                    "filled_quantity": order.filled_quantity,
                    "avg_fill_price": order.avg_fill_price,
                    "price": order.price,
                    "status": order.status.value,
                    "create_time": order.create_time.isoformat(),
                    "submit_time": order.submit_time.isoformat() if order.submit_time else None,
                    "fill_time": order.fill_time.isoformat() if order.fill_time else None,
                    "cancel_time": order.cancel_time.isoformat() if order.cancel_time else None,
                    "reject_time": order.reject_time.isoformat() if order.reject_time else None,
                    "strategy_name": order.strategy_name,
                    "account_id": order.account_id
                } for order in orders
            ]
        
        @self.app.post("/api/v1/orders", response_model=OrderResponse, tags=["订单管理"])
        def create_order(order_request: OrderRequest):
            """创建订单"""
            if not self.execution_engine:
                raise HTTPException(status_code=500, detail="执行引擎未初始化")
            
            from src.core.order import Order, OrderType, OrderDirection
            
            # 转换订单类型和方向
            try:
                order_type = OrderType(order_request.order_type)
                direction = OrderDirection(order_request.direction)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"无效的订单类型或方向: {e}")
            
            # 创建订单
            order = Order(
                symbol=order_request.symbol,
                order_type=order_type,
                direction=direction,
                quantity=order_request.quantity,
                price=order_request.price
            )
            
            order.strategy_name = order_request.strategy_name
            order.account_id = order_request.account_id
            
            # 提交订单
            order_id = self.execution_engine.submit_order(order)
            
            if not order_id:
                raise HTTPException(status_code=500, detail="订单提交失败")
            
            return OrderResponse(
                order_id=order_id,
                status=order.status.value,
                message="订单提交成功"
            )
        
        @self.app.delete("/api/v1/orders/{order_id}", tags=["订单管理"])
        def cancel_order(order_id: str):
            """取消订单"""
            if not self.execution_engine:
                raise HTTPException(status_code=500, detail="执行引擎未初始化")
            
            success = self.execution_engine.cancel_order(order_id)
            if not success:
                raise HTTPException(status_code=404, detail="订单取消失败")
            
            return {
                "order_id": order_id,
                "status": "cancelled",
                "message": "订单取消成功"
            }
        
        @self.app.get("/api/v1/strategies", tags=["策略管理"])
        def get_strategies():
            """获取策略列表"""
            if not self.strategy_engine:
                raise HTTPException(status_code=500, detail="策略引擎未初始化")
            
            strategies = self.strategy_engine.get_all_strategies()
            return [
                {
                    "strategy_name": name,
                    "running": strategy.running,
                    "paused": strategy.paused,
                    "params": strategy.params
                } for name, strategy in strategies.items()
            ]
        
        @self.app.post("/api/v1/strategies/{strategy_name}/start", tags=["策略管理"])
        def start_strategy(strategy_name: str):
            """启动策略"""
            if not self.strategy_engine:
                raise HTTPException(status_code=500, detail="策略引擎未初始化")
            
            try:
                self.strategy_engine.strategy_manager.start_strategy(strategy_name)
                return {
                    "strategy_name": strategy_name,
                    "status": "started",
                    "message": "策略启动成功"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"策略启动失败: {e}")
        
        @self.app.post("/api/v1/strategies/{strategy_name}/stop", tags=["策略管理"])
        def stop_strategy(strategy_name: str):
            """停止策略"""
            if not self.strategy_engine:
                raise HTTPException(status_code=500, detail="策略引擎未初始化")
            
            try:
                self.strategy_engine.strategy_manager.stop_strategy(strategy_name)
                return {
                    "strategy_name": strategy_name,
                    "status": "stopped",
                    "message": "策略停止成功"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"策略停止失败: {e}")
        
        @self.app.get("/api/v1/performance", tags=["绩效分析"])
        def get_performance_metrics():
            """获取绩效指标"""
            if not self.portfolio:
                raise HTTPException(status_code=500, detail="投资组合未初始化")
            
            metrics = self.portfolio.get_performance_metrics()
            return {
                "total_return": metrics.get("总收益率", 0.0),
                "annual_return": metrics.get("年化收益率", 0.0),
                "annual_volatility": metrics.get("年化波动率", 0.0),
                "sharpe_ratio": metrics.get("夏普比率", 0.0),
                "max_drawdown": metrics.get("最大回撤", 0.0),
                "trading_days": metrics.get("交易天数", 0),
                "trade_count": metrics.get("交易次数", 0)
            }
        
        @self.app.get("/api/v1/system/status", tags=["系统管理"])
        def get_system_info():
            """获取系统信息"""
            if not self.state_manager:
                raise HTTPException(status_code=500, detail="状态管理器未初始化")
            
            last_save_time = self.state_manager.get_system_status("last_save_time")
            system_version = self.state_manager.get_system_status("system_version")
            
            return {
                "last_save_time": last_save_time,
                "system_version": system_version,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/v1/system/save", tags=["系统管理"])
        def save_system_state():
            """保存系统状态"""
            if not self.state_manager:
                raise HTTPException(status_code=500, detail="状态管理器未初始化")
            
            saved_count = self.state_manager.save_state(
                execution_engine=self.execution_engine,
                portfolio=self.portfolio
            )
            
            return {
                "status": "success",
                "saved_count": saved_count,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_app(self):
        """获取FastAPI应用实例"""
        return self.app