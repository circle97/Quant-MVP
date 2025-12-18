# -*- coding: utf-8 -*-
"""
交易管理器单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.core.order import Order, OrderType, OrderDirection, OrderStatus
from src.core.position import Position
from src.core.transaction_manager import TransactionManager, OrderDB, FillDB, PositionDB, PortfolioDB, TradeDB, SystemStatusDB


class TestTransactionManager:
    """交易管理器单元测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        # 使用内存数据库进行测试
        self.transaction_manager = TransactionManager(db_url='sqlite:///:memory:')
    
    def test_save_order(self):
        """测试保存订单"""
        # 创建测试订单
        order = Order(
            symbol='600000.SH',
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            price=10.0
        )
        
        # 保存订单
        self.transaction_manager.save_order(order)
        
        # 从数据库中获取订单
        saved_order = self.transaction_manager.get_order(order.order_id)
        
        # 验证订单是否保存成功
        assert saved_order is not None
        assert saved_order.order_id == order.order_id
        assert saved_order.symbol == order.symbol
        assert saved_order.order_type == order.order_type
        assert saved_order.direction == order.direction
        assert saved_order.quantity == order.quantity
        assert saved_order.price == order.price
    
    def test_update_order(self):
        """测试更新订单"""
        # 创建测试订单
        order = Order(
            symbol='600000.SH',
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            price=10.0
        )
        
        # 保存订单
        self.transaction_manager.save_order(order)
        
        # 更新订单状态
        order.status = OrderStatus.FILLED
        order.filled_quantity = 100
        order.avg_fill_price = 10.0
        order.fill_time = datetime.now()
        
        # 保存更新后的订单
        self.transaction_manager.save_order(order)
        
        # 从数据库中获取订单
        saved_order = self.transaction_manager.get_order(order.order_id)
        
        # 验证订单是否更新成功
        assert saved_order.status == OrderStatus.FILLED
        assert saved_order.filled_quantity == 100
        assert saved_order.avg_fill_price == 10.0
        assert saved_order.fill_time is not None
    
    def test_save_position(self):
        """测试保存持仓"""
        # 创建测试持仓
        position = Position(
            symbol='600000.SH',
            quantity=100,
            avg_price=10.0,
            current_price=11.0,
            market_value=1100.0,
            unrealized_pnl=100.0
        )
        
        # 保存持仓
        self.transaction_manager.save_position(position)
        
        # 从数据库中获取持仓
        positions = self.transaction_manager.get_positions()
        
        # 验证持仓是否保存成功
        assert len(positions) == 1
        saved_position = positions[0]
        assert saved_position.symbol == position.symbol
        assert saved_position.quantity == position.quantity
        assert saved_position.avg_price == position.avg_price
        assert saved_position.current_price == position.current_price
        assert saved_position.market_value == position.market_value
        assert saved_position.unrealized_pnl == position.unrealized_pnl
    
    def test_save_portfolio(self):
        """测试保存投资组合"""
        # 创建测试投资组合
        from src.core.portfolio import Portfolio
        portfolio = Portfolio(initial_capital=100000.0)
        portfolio.cash = 90000.0
        portfolio.total_value = 110000.0
        
        # 保存投资组合
        self.transaction_manager.save_portfolio(portfolio)
        
        # 从数据库中获取投资组合
        saved_portfolio = self.transaction_manager.get_portfolio()
        
        # 验证投资组合是否保存成功
        assert saved_portfolio is not None
        assert saved_portfolio.initial_capital == portfolio.initial_capital
        assert saved_portfolio.cash == portfolio.cash
        assert saved_portfolio.total_value == portfolio.total_value
    
    def test_save_system_status(self):
        """测试保存系统状态"""
        # 保存系统状态
        self.transaction_manager.save_system_status('test_key', 'test_value')
        
        # 从数据库中获取系统状态
        status_value = self.transaction_manager.get_system_status('test_key')
        
        # 验证系统状态是否保存成功
        assert status_value == 'test_value'
    
    def test_get_all_orders(self):
        """测试获取所有订单"""
        # 创建测试订单
        order1 = Order(
            symbol='600000.SH',
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            price=10.0
        )
        
        order2 = Order(
            symbol='000001.SZ',
            order_type=OrderType.LIMIT,
            direction=OrderDirection.SELL,
            quantity=200,
            price=20.0
        )
        
        # 保存订单
        self.transaction_manager.save_order(order1)
        self.transaction_manager.save_order(order2)
        
        # 获取所有订单
        orders = self.transaction_manager.get_all_orders()
        
        # 验证订单是否获取成功
        assert len(orders) == 2
        symbols = [order.symbol for order in orders]
        assert '600000.SH' in symbols
        assert '000001.SZ' in symbols
    
    def test_get_positions(self):
        """测试获取所有持仓"""
        # 创建测试持仓
        position1 = Position(
            symbol='600000.SH',
            quantity=100,
            avg_price=10.0,
            current_price=11.0,
            market_value=1100.0,
            unrealized_pnl=100.0
        )
        
        position2 = Position(
            symbol='000001.SZ',
            quantity=200,
            avg_price=20.0,
            current_price=22.0,
            market_value=4400.0,
            unrealized_pnl=400.0
        )
        
        # 保存持仓
        self.transaction_manager.save_position(position1)
        self.transaction_manager.save_position(position2)
        
        # 获取所有持仓
        positions = self.transaction_manager.get_positions()
        
        # 验证持仓是否获取成功
        assert len(positions) == 2
        symbols = [position.symbol for position in positions]
        assert '600000.SH' in symbols
        assert '000001.SZ' in symbols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])