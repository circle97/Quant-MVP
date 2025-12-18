# -*- coding: utf-8 -*-
"""
交易管理器 - 负责交易数据的持久化存储
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger
import redis
import json

from src.core.order import Order, OrderStatus, OrderType, OrderDirection, Fill
from src.core.position import Position

# 创建基类
Base = declarative_base()


class OrderDB(Base):
    """订单表模型"""
    __tablename__ = 'orders'
    
    id = Column(String(36), primary_key=True, name='order_id')  # UUID长度
    symbol = Column(String(20), nullable=False)  # 股票代码长度
    order_type = Column(String(10), nullable=False)  # 订单类型长度
    direction = Column(String(10), nullable=False)  # 方向长度
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    status = Column(String(20), nullable=False)  # 状态长度
    create_time = Column(DateTime, nullable=False)
    submit_time = Column(DateTime)
    fill_time = Column(DateTime)
    cancel_time = Column(DateTime)
    reject_time = Column(DateTime)
    strategy_name = Column(String(50))  # 策略名称长度
    account_id = Column(String(36), nullable=False)  # UUID长度
    filled_quantity = Column(Float, default=0.0)
    avg_fill_price = Column(Float, default=0.0)


class FillDB(Base):
    """成交记录表模型"""
    __tablename__ = 'fills'
    
    id = Column(String(36), primary_key=True, name='fill_id')  # UUID长度
    order_id = Column(String(36), ForeignKey('orders.order_id'), nullable=False)  # UUID长度
    symbol = Column(String(20), nullable=False)  # 股票代码长度
    direction = Column(String(10), nullable=False)  # 方向长度
    fill_quantity = Column(Float, nullable=False)
    fill_price = Column(Float, nullable=False)
    commission = Column(Float, nullable=False, default=0.0)
    fill_time = Column(DateTime, nullable=False)
    strategy_name = Column(String(50))  # 策略名称长度
    account_id = Column(String(36), nullable=False)  # UUID长度


class PositionDB(Base):
    """持仓表模型"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)  # 股票代码长度
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)
    realized_pnl = Column(Float, default=0.0)
    update_time = Column(DateTime, nullable=False)
    account_id = Column(String(36), nullable=False)  # UUID长度
    
    __table_args__ = (
        {'extend_existing': True},
        )


class PortfolioDB(Base):
    """投资组合表模型"""
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(36), nullable=False, unique=True)  # UUID长度
    initial_capital = Column(Float, nullable=False)
    current_capital = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    update_time = Column(DateTime, nullable=False)


class TradeDB(Base):
    """交易记录表模型"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String(20), nullable=False)  # 股票代码长度
    action = Column(String(10), nullable=False)  # 操作类型长度
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    trade_value = Column(Float, nullable=False)
    fees = Column(Float, nullable=False)
    cash_after = Column(Float, nullable=False)
    account_id = Column(String(36), nullable=False)  # UUID长度


class SystemStatusDB(Base):
    """系统状态表模型"""
    __tablename__ = 'system_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)  # 状态键长度
    value = Column(String(500), nullable=False)  # 状态值长度
    update_time = Column(DateTime, nullable=False)


class TransactionManager:
    """
    交易管理器 - 负责交易数据的持久化存储
    支持MySQL数据库和Redis缓存
    """
    
    def __init__(self, db_url: str = 'sqlite:///trading.db', redis_config: Dict = None):
        """
        初始化交易管理器
        
        Args:
            db_url: 数据库连接URL
            redis_config: Redis连接配置，格式: {"host": "localhost", "port": 6379, "password": "", "db": 0}
        """
        # 初始化MySQL数据库
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False, pool_size=10, max_overflow=20)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建所有表
        self._create_tables()
        
        # 初始化Redis客户端
        self.redis_config = redis_config or {"host": "localhost", "port": 6379, "password": "", "db": 0}
        self.redis_client = redis.Redis(**self.redis_config)
        
        # 测试Redis连接
        try:
            self.redis_client.ping()
            logger.info(f"初始化Redis客户端成功，连接到: {self.redis_config['host']}:{self.redis_config['port']}")
        except Exception as e:
            logger.warning(f"初始化Redis客户端失败: {e}")
            self.redis_client = None
        
        logger.info(f"初始化TransactionManager，数据库: {db_url}")
    
    def _create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("创建数据库表成功")
    
    def get_db(self) -> Session:
        """获取数据库会话"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def save_order(self, order: Order):
        """
        保存订单到数据库和Redis缓存
        """
        db = next(self.get_db())
        try:
            # 检查订单是否已存在
            existing_order = db.query(OrderDB).filter(OrderDB.id == order.order_id).first()
            
            if existing_order:
                # 更新现有订单
                existing_order.status = order.status.value
                existing_order.submit_time = order.submit_time
                existing_order.fill_time = order.fill_time
                existing_order.cancel_time = order.cancel_time
                existing_order.reject_time = order.reject_time
                existing_order.filled_quantity = order.filled_quantity
                existing_order.avg_fill_price = order.avg_fill_price
            else:
                # 创建新订单
                order_db = OrderDB(
                    id=order.order_id,
                    symbol=order.symbol,
                    order_type=order.order_type.value,
                    direction=order.direction.value,
                    quantity=order.quantity,
                    price=order.price,
                    status=order.status.value,
                    create_time=order.create_time,
                    submit_time=order.submit_time,
                    fill_time=order.fill_time,
                    cancel_time=order.cancel_time,
                    reject_time=order.reject_time,
                    strategy_name=order.strategy_name,
                    account_id=order.account_id,
                    filled_quantity=order.filled_quantity,
                    avg_fill_price=order.avg_fill_price
                )
                db.add(order_db)
            
            db.commit()
            logger.debug(f"保存订单成功: {order.order_id}")
            
            # 保存到Redis缓存
            if self.redis_client:
                order_data = {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "order_type": order.order_type.value,
                    "direction": order.direction.value,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status.value,
                    "create_time": order.create_time.isoformat() if order.create_time else None,
                    "submit_time": order.submit_time.isoformat() if order.submit_time else None,
                    "fill_time": order.fill_time.isoformat() if order.fill_time else None,
                    "cancel_time": order.cancel_time.isoformat() if order.cancel_time else None,
                    "reject_time": order.reject_time.isoformat() if order.reject_time else None,
                    "strategy_name": order.strategy_name,
                    "account_id": order.account_id,
                    "filled_quantity": order.filled_quantity,
                    "avg_fill_price": order.avg_fill_price
                }
                self.redis_client.set(f"order:{order.order_id}", json.dumps(order_data), ex=3600)  # 1小时过期
        except Exception as e:
            db.rollback()
            logger.error(f"保存订单失败: {e}")
        finally:
            db.close()
    
    def save_fill(self, fill: Fill):
        """保存成交记录到数据库"""
        db = next(self.get_db())
        try:
            fill_db = FillDB(
                id=fill.fill_id,
                order_id=fill.order_id,
                symbol=fill.symbol,
                direction=fill.direction.value,
                fill_quantity=fill.fill_quantity,
                fill_price=fill.fill_price,
                commission=fill.commission,
                fill_time=fill.fill_time,
                strategy_name=fill.strategy_name,
                account_id=fill.account_id
            )
            db.add(fill_db)
            db.commit()
            logger.debug(f"保存成交记录成功: {fill.fill_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"保存成交记录失败: {e}")
        finally:
            db.close()
    
    def save_position(self, position: Position, account_id: str = 'default'):
        """保存持仓到数据库"""
        db = next(self.get_db())
        try:
            # 检查持仓是否已存在
            existing_position = db.query(PositionDB).filter(
                PositionDB.symbol == position.symbol,
                PositionDB.account_id == account_id
            ).first()
            
            if existing_position:
                # 更新现有持仓
                existing_position.quantity = position.quantity
                existing_position.avg_price = position.avg_price
                existing_position.current_price = position.current_price
                existing_position.market_value = position.market_value
                existing_position.unrealized_pnl = position.unrealized_pnl
                existing_position.realized_pnl = position.realized_pnl
                existing_position.update_time = datetime.now()
            else:
                # 创建新持仓
                position_db = PositionDB(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    avg_price=position.avg_price,
                    current_price=position.current_price,
                    market_value=position.market_value,
                    unrealized_pnl=position.unrealized_pnl,
                    realized_pnl=position.realized_pnl,
                    update_time=datetime.now(),
                    account_id=account_id
                )
                db.add(position_db)
            
            db.commit()
            logger.debug(f"保存持仓成功: {position.symbol}")
        except Exception as e:
            db.rollback()
            logger.error(f"保存持仓失败: {e}")
        finally:
            db.close()
    
    def save_portfolio(self, portfolio):
        """保存投资组合到数据库"""
        db = next(self.get_db())
        try:
            # 检查投资组合是否已存在
            existing_portfolio = db.query(PortfolioDB).filter(
                PortfolioDB.account_id == 'default'
            ).first()
            
            if existing_portfolio:
                # 更新现有投资组合
                existing_portfolio.current_capital = portfolio.current_capital
                existing_portfolio.cash = portfolio.cash
                existing_portfolio.total_value = portfolio.total_value
                existing_portfolio.update_time = datetime.now()
            else:
                # 创建新投资组合
                portfolio_db = PortfolioDB(
                    account_id='default',
                    initial_capital=portfolio.initial_capital,
                    current_capital=portfolio.current_capital,
                    cash=portfolio.cash,
                    total_value=portfolio.total_value,
                    update_time=datetime.now()
                )
                db.add(portfolio_db)
            
            db.commit()
            logger.debug(f"保存投资组合成功")
        except Exception as e:
            db.rollback()
            logger.error(f"保存投资组合失败: {e}")
        finally:
            db.close()
    
    def save_trade(self, trade: Dict, account_id: str = 'default'):
        """保存交易记录到数据库"""
        db = next(self.get_db())
        try:
            trade_db = TradeDB(
                timestamp=trade['timestamp'],
                symbol=trade['symbol'],
                action=trade['action'],
                quantity=trade['quantity'],
                price=trade['price'],
                trade_value=trade['trade_value'],
                fees=trade['fees'],
                cash_after=trade['cash_after'],
                account_id=account_id
            )
            db.add(trade_db)
            db.commit()
            logger.debug(f"保存交易记录成功")
        except Exception as e:
            db.rollback()
            logger.error(f"保存交易记录失败: {e}")
        finally:
            db.close()
    
    def save_system_status(self, key: str, value: str):
        """保存系统状态到数据库"""
        db = next(self.get_db())
        try:
            # 检查状态是否已存在
            existing_status = db.query(SystemStatusDB).filter(
                SystemStatusDB.key == key
            ).first()
            
            if existing_status:
                # 更新现有状态
                existing_status.value = value
                existing_status.update_time = datetime.now()
            else:
                # 创建新状态
                status_db = SystemStatusDB(
                    key=key,
                    value=value,
                    update_time=datetime.now()
                )
                db.add(status_db)
            
            db.commit()
            logger.debug(f"保存系统状态成功: {key} = {value}")
        except Exception as e:
            db.rollback()
            logger.error(f"保存系统状态失败: {e}")
        finally:
            db.close()
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        从Redis缓存或数据库获取订单
        """
        # 先从Redis缓存获取
        if self.redis_client:
            try:
                order_data = self.redis_client.get(f"order:{order_id}")
                if order_data:
                    order_data = json.loads(order_data)
                    # 转换为Order对象
                    order = Order(
                        symbol=order_data["symbol"],
                        order_type=OrderType(order_data["order_type"]),
                        direction=OrderDirection(order_data["direction"]),
                        quantity=order_data["quantity"],
                        price=order_data["price"],
                        order_id=order_data["order_id"]
                    )
                    order.status = OrderStatus(order_data["status"])
                    order.create_time = datetime.fromisoformat(order_data["create_time"]) if order_data["create_time"] else None
                    order.submit_time = datetime.fromisoformat(order_data["submit_time"]) if order_data["submit_time"] else None
                    order.fill_time = datetime.fromisoformat(order_data["fill_time"]) if order_data["fill_time"] else None
                    order.cancel_time = datetime.fromisoformat(order_data["cancel_time"]) if order_data["cancel_time"] else None
                    order.reject_time = datetime.fromisoformat(order_data["reject_time"]) if order_data["reject_time"] else None
                    order.strategy_name = order_data["strategy_name"]
                    order.account_id = order_data["account_id"]
                    order.filled_quantity = order_data["filled_quantity"]
                    order.avg_fill_price = order_data["avg_fill_price"]
                    
                    logger.debug(f"从Redis缓存获取订单成功: {order_id}")
                    return order
            except Exception as e:
                logger.warning(f"从Redis缓存获取订单失败: {e}")
        
        # 从数据库获取
        db = next(self.get_db())
        try:
            order_db = db.query(OrderDB).filter(OrderDB.id == order_id).first()
            if not order_db:
                return None
            
            # 转换为Order对象
            order = Order(
                symbol=order_db.symbol,
                order_type=OrderType(order_db.order_type),
                direction=OrderDirection(order_db.direction),
                quantity=order_db.quantity,
                price=order_db.price,
                order_id=order_db.id
            )
            order.status = OrderStatus(order_db.status)
            order.create_time = order_db.create_time
            order.submit_time = order_db.submit_time
            order.fill_time = order_db.fill_time
            order.cancel_time = order_db.cancel_time
            order.reject_time = order_db.reject_time
            order.strategy_name = order_db.strategy_name
            order.account_id = order_db.account_id
            order.filled_quantity = order_db.filled_quantity
            order.avg_fill_price = order_db.avg_fill_price
            
            logger.debug(f"从数据库获取订单成功: {order_id}")
            
            # 保存到Redis缓存
            if self.redis_client:
                order_data = {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "order_type": order.order_type.value,
                    "direction": order.direction.value,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status.value,
                    "create_time": order.create_time.isoformat() if order.create_time else None,
                    "submit_time": order.submit_time.isoformat() if order.submit_time else None,
                    "fill_time": order.fill_time.isoformat() if order.fill_time else None,
                    "cancel_time": order.cancel_time.isoformat() if order.cancel_time else None,
                    "reject_time": order.reject_time.isoformat() if order.reject_time else None,
                    "strategy_name": order.strategy_name,
                    "account_id": order.account_id,
                    "filled_quantity": order.filled_quantity,
                    "avg_fill_price": order.avg_fill_price
                }
                self.redis_client.set(f"order:{order_id}", json.dumps(order_data), ex=3600)  # 1小时过期
            
            return order
        except Exception as e:
            logger.error(f"从数据库获取订单失败: {e}")
            return None
        finally:
            db.close()
    
    def get_all_orders(self) -> List[Order]:
        """从数据库获取所有订单"""
        db = next(self.get_db())
        try:
            orders_db = db.query(OrderDB).all()
            orders = []
            for order_db in orders_db:
                order = Order(
                    symbol=order_db.symbol,
                    order_type=OrderType(order_db.order_type),
                    direction=OrderDirection(order_db.direction),
                    quantity=order_db.quantity,
                    price=order_db.price,
                    order_id=order_db.id
                )
                order.status = OrderStatus(order_db.status)
                order.create_time = order_db.create_time
                order.submit_time = order_db.submit_time
                order.fill_time = order_db.fill_time
                order.cancel_time = order_db.cancel_time
                order.reject_time = order_db.reject_time
                order.strategy_name = order_db.strategy_name
                order.account_id = order_db.account_id
                order.filled_quantity = order_db.filled_quantity
                order.avg_fill_price = order_db.avg_fill_price
                orders.append(order)
            
            return orders
        except Exception as e:
            logger.error(f"获取所有订单失败: {e}")
            return []
        finally:
            db.close()
    
    def get_positions(self, account_id: str = 'default') -> List[Position]:
        """从数据库获取所有持仓"""
        db = next(self.get_db())
        try:
            positions_db = db.query(PositionDB).filter(
                PositionDB.account_id == account_id
            ).all()
            
            positions = []
            for position_db in positions_db:
                position = Position(
                    symbol=position_db.symbol,
                    quantity=position_db.quantity,
                    avg_price=position_db.avg_price,
                    current_price=position_db.current_price,
                    market_value=position_db.market_value,
                    unrealized_pnl=position_db.unrealized_pnl,
                    realized_pnl=position_db.realized_pnl
                )
                positions.append(position)
            
            return positions
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
        finally:
            db.close()
    
    def get_portfolio(self, account_id: str = 'default'):
        """从数据库获取投资组合"""
        from src.core.portfolio import Portfolio
        
        db = next(self.get_db())
        try:
            portfolio_db = db.query(PortfolioDB).filter(
                PortfolioDB.account_id == account_id
            ).first()
            
            if not portfolio_db:
                return None
            
            # 创建Portfolio对象
            portfolio = Portfolio(initial_capital=portfolio_db.initial_capital)
            portfolio.current_capital = portfolio_db.current_capital
            portfolio.cash = portfolio_db.cash
            portfolio.total_value = portfolio_db.total_value
            
            return portfolio
        except Exception as e:
            logger.error(f"获取投资组合失败: {e}")
            return None
        finally:
            db.close()
    
    def get_system_status(self, key: str) -> Optional[str]:
        """从数据库获取系统状态"""
        db = next(self.get_db())
        try:
            status_db = db.query(SystemStatusDB).filter(
                SystemStatusDB.key == key
            ).first()
            
            if status_db:
                return status_db.value
            return None
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return None
        finally:
            db.close()