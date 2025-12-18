# -*- coding: utf-8 -*-
"""
状态管理器单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.core.order import Order, OrderType, OrderDirection, OrderStatus
from src.core.position import Position
from src.core.transaction_manager import TransactionManager
from src.core.state_manager import StateManager
from src.core.execution_engine import ExecutionEngine
from src.core.portfolio import Portfolio


class TestStateManager:
    """状态管理器单元测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        # 使用内存数据库进行测试
        self.transaction_manager = TransactionManager(db_url='sqlite:///:memory:')
        self.state_manager = StateManager(transaction_manager=self.transaction_manager)
        
        # 创建测试执行引擎和投资组合
        self.execution_engine = ExecutionEngine(config={'mode': 'simulation'})
        self.portfolio = Portfolio(initial_capital=100000.0)
        self.execution_engine.set_portfolio(self.portfolio)
    
    def test_save_state(self):
        """测试保存系统状态"""
        # 创建测试订单
        order = Order(
            symbol='600000.SH',
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            price=10.0
        )
        
        # 提交订单
        order_id = self.execution_engine.submit_order(order)
        assert order_id is not None
        
        # 保存系统状态
        saved_count = self.state_manager.save_state(
            execution_engine=self.execution_engine,
            portfolio=self.portfolio
        )
        
        # 验证状态保存成功
        assert saved_count['orders'] >= 1
        assert saved_count['portfolio'] == 1
        assert saved_count['positions'] >= 0
    
    def test_restore_state(self):
        """测试恢复系统状态"""
        # 创建测试订单
        order = Order(
            symbol='600000.SH',
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            price=10.0
        )
        
        # 提交订单
        order_id = self.execution_engine.submit_order(order)
        assert order_id is not None
        
        # 保存系统状态
        self.state_manager.save_state(
            execution_engine=self.execution_engine,
            portfolio=self.portfolio
        )
        
        # 创建新的执行引擎和投资组合
        new_execution_engine = ExecutionEngine(config={'mode': 'simulation'})
        new_portfolio = Portfolio(initial_capital=50000.0)
        new_execution_engine.set_portfolio(new_portfolio)
        
        # 恢复系统状态
        restored_count = self.state_manager.restore_state(
            execution_engine=new_execution_engine,
            portfolio=new_portfolio
        )
        
        # 验证状态恢复成功
        assert restored_count['orders'] >= 1
        assert restored_count['portfolio'] == 1
        assert restored_count['positions'] >= 0
        
        # 验证订单是否恢复成功
        orders = new_execution_engine.get_all_orders()
        assert len(orders) >= 1
        
        # 验证投资组合是否恢复成功
        assert new_portfolio.initial_capital == self.portfolio.initial_capital
    
    def test_check_state_consistency(self):
        """测试状态一致性检查"""
        # 创建测试订单
        order = Order(
            symbol='600000.SH',
            order_type=OrderType.MARKET,
            direction=OrderDirection.BUY,
            quantity=100,
            price=10.0
        )
        
        # 提交订单
        order_id = self.execution_engine.submit_order(order)
        assert order_id is not None
        
        # 保存系统状态
        self.state_manager.save_state(
            execution_engine=self.execution_engine,
            portfolio=self.portfolio
        )
        
        # 检查状态一致性
        is_consistent = self.state_manager.check_state_consistency(
            execution_engine=self.execution_engine,
            portfolio=self.portfolio
        )
        
        # 验证状态一致性检查通过
        assert is_consistent is True
    
    def test_get_system_status(self):
        """测试获取系统状态"""
        # 保存系统状态信息
        self.transaction_manager.save_system_status('test_key', 'test_value')
        
        # 获取系统状态
        status_value = self.state_manager.get_system_status('test_key')
        
        # 验证系统状态获取成功
        assert status_value == 'test_value'
    
    def test_set_system_status(self):
        """测试设置系统状态"""
        # 设置系统状态
        self.state_manager.set_system_status('test_key', 'test_value')
        
        # 获取系统状态
        status_value = self.state_manager.get_system_status('test_key')
        
        # 验证系统状态设置成功
        assert status_value == 'test_value'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])