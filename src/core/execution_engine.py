# -*- coding: utf-8 -*-
"""
交易执行模块 - 执行引擎核心
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
from loguru import logger

from src.core.event import Event, EventType, SignalEvent, OrderEvent, FillEvent, event_engine
from src.core.order import Order, OrderStatus, OrderType, OrderDirection
from src.data.data_manager import AStockDataManager
from src.core.risk_manager import RiskManager


class Fill:
    """成交数据结构"""
    
    def __init__(self, order: Order, fill_quantity: float, fill_price: float,
                 commission: float = 0.0, fill_id: Optional[str] = None):
        """
        初始化成交记录
        
        Args:
            order: 关联的订单
            fill_quantity: 成交数量
            fill_price: 成交价格
            commission: 手续费
            fill_id: 成交ID，若为None则自动生成
        """
        self.fill_id = fill_id or str(uuid4())
        self.order_id = order.order_id
        self.symbol = order.symbol
        self.direction = order.direction
        self.fill_quantity = fill_quantity
        self.fill_price = fill_price
        self.commission = commission
        self.fill_time = datetime.now()
        self.strategy_name = order.strategy_name
        self.account_id = order.account_id
        
        # 计算成交金额
        self.fill_amount = fill_quantity * fill_price
    
    def __repr__(self):
        return f"Fill({self.fill_id}, Order={self.order_id}, {self.symbol}, {self.direction.value}, {self.fill_quantity} @ {self.fill_price}, Commission={self.commission})"


class SlippageModel:
    """滑点模型"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model_type = config.get("type", "fixed")  # fixed, percentage, volatility_based
        self.fixed_slippage = config.get("fixed_slippage", 0.01)
        self.percentage_slippage = config.get("percentage_slippage", 0.001)
    
    def calculate_slippage(self, order: Order, price: float) -> float:
        """计算滑点"""
        if self.model_type == "fixed":
            return self._fixed_slippage(order, price)
        elif self.model_type == "percentage":
            return self._percentage_slippage(order, price)
        elif self.model_type == "volatility_based":
            return self._volatility_based_slippage(order, price)
        else:
            return price
    
    def _fixed_slippage(self, order: Order, price: float) -> float:
        """固定滑点模型"""
        slippage = self.fixed_slippage
        if order.direction == OrderDirection.BUY:
            return price + slippage
        else:
            return price - slippage
    
    def _percentage_slippage(self, order: Order, price: float) -> float:
        """百分比滑点模型"""
        slippage = price * self.percentage_slippage
        if order.direction == OrderDirection.BUY:
            return price + slippage
        else:
            return price - slippage
    
    def _volatility_based_slippage(self, order: Order, price: float) -> float:
        """基于波动率的滑点模型"""
        # 简化实现，使用固定滑点
        return self._fixed_slippage(order, price)


class CommissionModel:
    """手续费模型"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model_type = config.get("type", "percentage")  # fixed, percentage, tiered
        self.fixed_commission = config.get("fixed_commission", 0.0)
        self.percentage_commission = config.get("percentage_commission", 0.0003)
        self.min_commission = config.get("min_commission", 5.0)
        self.max_commission = config.get("max_commission", float("inf"))
    
    def calculate_commission(self, order: Order, price: float, quantity: float) -> float:
        """计算手续费"""
        if self.model_type == "fixed":
            return self._fixed_commission(order, price, quantity)
        elif self.model_type == "percentage":
            return self._percentage_commission(order, price, quantity)
        elif self.model_type == "tiered":
            return self._tiered_commission(order, price, quantity)
        else:
            return 0.0
    
    def _fixed_commission(self, order: Order, price: float, quantity: float) -> float:
        """固定手续费模型"""
        return self.fixed_commission
    
    def _percentage_commission(self, order: Order, price: float, quantity: float) -> float:
        """百分比手续费模型"""
        commission = price * quantity * self.percentage_commission
        # 应用最小和最大手续费限制
        return max(self.min_commission, min(self.max_commission, commission))
    
    def _tiered_commission(self, order: Order, price: float, quantity: float) -> float:
        """阶梯式手续费模型"""
        # 简化实现，使用百分比手续费
        return self._percentage_commission(order, price, quantity)


class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        self.orders = {}
        self.active_orders = {}
        self.order_history = []
    
    def add_order(self, order: Order):
        """添加订单"""
        self.orders[order.order_id] = order
        self.order_history.append(order)
        
        if order.is_active():
            self._add_to_active_orders(order)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)
    
    def get_all_orders(self, filters: Optional[dict] = None) -> List[Order]:
        """获取所有订单"""
        if not filters:
            return list(self.orders.values())
        
        # 实现订单过滤逻辑
        filtered_orders = []
        for order in self.orders.values():
            match = True
            for key, value in filters.items():
                if getattr(order, key, None) != value:
                    match = False
                    break
            if match:
                filtered_orders.append(order)
        
        return filtered_orders
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取活跃订单"""
        if not symbol:
            return list(self.active_orders.values())
        
        return [order for order in self.active_orders.values() if order.symbol == symbol]
    
    def update_order_status(self, order_id: str, status: OrderStatus):
        """更新订单状态"""
        order = self.orders.get(order_id)
        if not order:
            return
        
        old_status = order.status
        order.status = status
        
        # 更新活跃订单列表
        if old_status.is_active() and not order.is_active():
            self._remove_from_active_orders(order_id)
        elif not old_status.is_active() and order.is_active():
            self._add_to_active_orders(order)
    
    def _add_to_active_orders(self, order: Order):
        """将订单添加到活跃订单列表"""
        self.active_orders[order.order_id] = order
    
    def _remove_from_active_orders(self, order_id: str):
        """将订单从活跃订单列表移除"""
        if order_id in self.active_orders:
            del self.active_orders[order_id]
    
    def get_order_stats(self) -> dict:
        """获取订单统计信息"""
        total = len(self.order_history)
        filled = len([o for o in self.order_history if o.is_filled()])
        cancelled = len([o for o in self.order_history if o.status == OrderStatus.CANCELLED])
        rejected = len([o for o in self.order_history if o.status == OrderStatus.REJECTED])
        
        return {
            "total_orders": total,
            "filled_orders": filled,
            "cancelled_orders": cancelled,
            "rejected_orders": rejected,
            "fill_rate": filled / total if total > 0 else 0
        }


class Simulator:
    """模拟执行器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.slippage_model = SlippageModel(config.get("slippage", {}))
        self.commission_model = CommissionModel(config.get("commission", {}))
        self.data_manager = AStockDataManager()
        self.execution_engine = None
        self._active_orders = {}
    
    def set_execution_engine(self, execution_engine):
        """设置执行引擎引用"""
        self.execution_engine = execution_engine
    
    def submit_order(self, order: Order):
        """提交订单到模拟器"""
        # 将订单添加到活跃订单列表
        self._active_orders[order.order_id] = order
        
        # 根据订单类型执行模拟
        if order.order_type == OrderType.MARKET:
            self._execute_market_order(order)
        elif order.order_type == OrderType.LIMIT:
            self._execute_limit_order(order)
        elif order.order_type == OrderType.STOP:
            self._execute_stop_order(order)
        elif order.order_type == OrderType.STOP_LIMIT:
            self._execute_stop_limit_order(order)
        elif order.order_type == OrderType.TRAILING_STOP:
            self._execute_trailing_stop_order(order)
    
    def _execute_market_order(self, order: Order):
        """执行市价单"""
        # 获取当前价格（使用最新数据的收盘价）
        current_data = self.data_manager.get_daily_data(order.symbol)
        if current_data.empty:
            logger.error(f"无法获取 {order.symbol} 的当前价格")
            return
        
        current_price = current_data['close'].iloc[-1]
        
        # 应用滑点
        fill_price = self.slippage_model.calculate_slippage(order, current_price)
        
        # 计算手续费
        commission = self.commission_model.calculate_commission(order, fill_price, order.quantity)
        
        # 模拟成交
        self._simulate_fill(order, order.quantity, fill_price, commission)
    
    def _execute_limit_order(self, order: Order):
        """执行限价单"""
        # 获取当前价格
        current_data = self.data_manager.get_daily_data(order.symbol)
        if current_data.empty:
            logger.error(f"无法获取 {order.symbol} 的当前价格")
            return
        
        current_price = current_data['close'].iloc[-1]
        
        # 检查是否达到限价
        if order.direction == OrderDirection.BUY:
            if current_price <= order.price:
                # 买入限价单，当前价格低于等于限价，成交
                fill_price = order.price
                commission = self.commission_model.calculate_commission(order, fill_price, order.quantity)
                self._simulate_fill(order, order.quantity, fill_price, commission)
        else:  # SELL
            if current_price >= order.price:
                # 卖出限价单，当前价格高于等于限价，成交
                fill_price = order.price
                commission = self.commission_model.calculate_commission(order, fill_price, order.quantity)
                self._simulate_fill(order, order.quantity, fill_price, commission)
    
    def _execute_stop_order(self, order: Order):
        """执行止损单"""
        # 简化实现，使用市价单执行
        self._execute_market_order(order)
    
    def _execute_stop_limit_order(self, order: Order):
        """执行止损限价单"""
        # 简化实现，使用市价单执行
        self._execute_market_order(order)
    
    def _execute_trailing_stop_order(self, order: Order):
        """执行追踪止损单"""
        # 简化实现，使用市价单执行
        self._execute_market_order(order)
    
    def _simulate_fill(self, order: Order, fill_quantity: float, fill_price: float, commission: float):
        """模拟成交"""
        if self.execution_engine:
            self.execution_engine.handle_fill(order, fill_quantity, fill_price, commission)
    
    def cancel_order(self, order_id: str):
        """取消订单"""
        if order_id in self._active_orders:
            order = self._active_orders[order_id]
            order.status = OrderStatus.CANCELLED
            order.cancel_time = datetime.now()
            del self._active_orders[order_id]
    
    def modify_order(self, order_id: str, order_params: dict):
        """修改订单"""
        if order_id in self._active_orders:
            order = self._active_orders[order_id]
            # 更新订单参数
            for key, value in order_params.items():
                if hasattr(order, key):
                    setattr(order, key, value)


class ExecutionEngine:
    """执行引擎核心"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.order_manager = OrderManager()
        self.mode = self.config.get("mode", "simulation")  # simulation or live
        
        # 初始化风险管理器
        self.risk_manager = RiskManager(self.config.get("risk", {}))
        
        # 投资组合引用
        self.portfolio = None
        
        # 根据模式初始化执行器
        if self.mode == "simulation":
            self.executor = Simulator(self.config.get("simulator", {}))
            self.executor.set_execution_engine(self)
        else:
            # 实盘模式，暂时不实现
            logger.error("实盘模式尚未实现")
            raise NotImplementedError("实盘模式尚未实现")
        
        # 事件引擎
        self.event_engine = event_engine
        
        # 注册事件处理器
        self._register_event_handlers()
        
        logger.info(f"初始化执行引擎，模式: {self.mode}")
        
    def set_portfolio(self, portfolio):
        """设置投资组合引用"""
        self.portfolio = portfolio
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        self.event_engine.register_handler(EventType.SIGNAL, self.on_signal)
        self.event_engine.register_handler(EventType.ORDER, self.on_order)
    
    def on_signal(self, event: SignalEvent):
        """处理交易信号"""
        # 将信号转换为订单
        order = self._create_order_from_signal(event)
        
        # 提交订单
        self.submit_order(order)
    
    def on_order(self, event: OrderEvent):
        """处理订单事件"""
        # 简化实现，直接提交订单
        order = self._create_order_from_event(event)
        self.submit_order(order)
    
    def _create_order_from_signal(self, signal: SignalEvent) -> Order:
        """从交易信号创建订单"""
        # 根据信号类型和强度创建订单
        direction = OrderDirection.BUY if signal.signal_type == "BUY" else OrderDirection.SELL
        
        # 创建订单
        order = Order(
            symbol=signal.symbol,
            order_type=OrderType.MARKET,
            direction=direction,
            quantity=100,  # 固定1手
            price=signal.data.get("price")
        )
        
        return order
    
    def _create_order_from_event(self, event: OrderEvent) -> Order:
        """从订单事件创建订单"""
        # 将事件订单转换为内部订单对象
        direction = OrderDirection.BUY if event.data["direction"] == "LONG" else OrderDirection.SELL
        order_type = OrderType.MARKET if event.data["order_type"] == "MARKET" else OrderType.LIMIT
        
        order = Order(
            symbol=event.symbol,
            order_type=order_type,
            direction=direction,
            quantity=event.data["quantity"],
            price=event.data["price"]
        )
        
        return order
    
    def submit_order(self, order: Order) -> str:
        """提交订单"""
        # 验证订单
        if not self._validate_order(order):
            return None
        
        # 风险检查
        if self.portfolio:
            if not self.risk_manager.check_order_risk(order, self.portfolio):
                order.status = OrderStatus.REJECTED
                order.reject_time = datetime.now()
                logger.warning(f"订单 {order.order_id} 未通过风险检查，被拒绝")
                return None
        
        # 保存订单到订单管理器
        self.order_manager.add_order(order)
        
        # 提交订单到执行器
        try:
            self.executor.submit_order(order)
            order.status = OrderStatus.SUBMITTED
            order.submit_time = datetime.now()
            
            logger.debug(f"订单提交成功: {order}")
            return order.order_id
        except Exception as e:
            logger.error(f"提交订单失败: {e}")
            order.status = OrderStatus.REJECTED
            order.reject_time = datetime.now()
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        order = self.order_manager.get_order(order_id)
        if not order or not order.is_active():
            return False
        
        try:
            self.executor.cancel_order(order_id)
            order.status = OrderStatus.CANCELLED
            order.cancel_time = datetime.now()
            logger.debug(f"订单取消成功: {order_id}")
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False
    
    def modify_order(self, order_id: str, order_params: dict) -> bool:
        """修改订单"""
        order = self.order_manager.get_order(order_id)
        if not order or not order.is_active():
            return False
        
        try:
            self.executor.modify_order(order_id, order_params)
            logger.debug(f"订单修改成功: {order_id}, 参数: {order_params}")
            return True
        except Exception as e:
            logger.error(f"修改订单失败: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.order_manager.get_order(order_id)
    
    def get_all_orders(self, filters: Optional[dict] = None) -> List[Order]:
        """获取所有订单"""
        return self.order_manager.get_all_orders(filters)
    
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """获取活跃订单"""
        return self.order_manager.get_active_orders(symbol)
    
    def _validate_order(self, order: Order) -> bool:
        """验证订单"""
        # 简单验证：检查数量是否为正数
        if order.quantity <= 0:
            logger.error(f"订单数量无效: {order.quantity}")
            return False
        
        # 检查标的代码是否为空
        if not order.symbol:
            logger.error("订单标的代码不能为空")
            return False
        
        return True
    
    def handle_fill(self, order: Order, fill_quantity: float, fill_price: float, commission: float = 0.0):
        """处理成交"""
        # 更新订单成交信息
        order.update_fill(fill_quantity, fill_price)
        
        # 创建成交记录
        fill = Fill(order, fill_quantity, fill_price, commission)
        
        logger.debug(f"订单成交: {fill}")
        
        # 触发成交事件
        fill_event = FillEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            quantity=fill_quantity,
            price=fill_price,
            direction=order.direction.value,
            commission=commission
        )
        
        self.event_engine.put(fill_event)
        
        # 如果订单完全成交，记录日志
        if order.is_filled():
            logger.info(f"订单完全成交: {order}")