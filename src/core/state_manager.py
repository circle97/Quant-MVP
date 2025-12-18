# -*- coding: utf-8 -*-
"""
状态管理器 - 负责系统状态的恢复和保存
"""
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.core.transaction_manager import TransactionManager
from src.core.portfolio import Portfolio
from src.core.execution_engine import ExecutionEngine
from src.core.order import Order
from src.core.position import Position


class StateManager:
    """状态管理器 - 负责系统状态的恢复和保存"""
    
    def __init__(self, transaction_manager: TransactionManager = None):
        """
        初始化状态管理器
        
        Args:
            transaction_manager: 交易管理器实例，若为None则创建新实例
        """
        self.transaction_manager = transaction_manager or TransactionManager()
        logger.info("初始化状态管理器")
    
    def restore_state(self, execution_engine: ExecutionEngine = None, portfolio: Portfolio = None) -> Dict:
        """
        从数据库恢复系统状态
        
        Args:
            execution_engine: 执行引擎实例，若提供则恢复订单状态
            portfolio: 投资组合实例，若提供则恢复投资组合和持仓状态
        
        Returns:
            恢复状态的统计信息
        """
        logger.info("开始恢复系统状态")
        
        restored_count = {
            'orders': 0,
            'positions': 0,
            'portfolio': 0,
            'trades': 0
        }
        
        try:
            # 恢复投资组合
            if portfolio:
                restored_portfolio = self.transaction_manager.get_portfolio()
                if restored_portfolio:
                    # 恢复投资组合基本信息
                    portfolio.initial_capital = restored_portfolio.initial_capital
                    portfolio.current_capital = restored_portfolio.current_capital
                    portfolio.cash = restored_portfolio.cash
                    portfolio.total_value = restored_portfolio.total_value
                    restored_count['portfolio'] = 1
                    logger.info(f"恢复投资组合成功，初始资金: {restored_portfolio.initial_capital:.2f}")
                
                # 恢复持仓
                positions = self.transaction_manager.get_positions()
                for position in positions:
                    portfolio.positions[position.symbol] = position
                    restored_count['positions'] += 1
                logger.info(f"恢复持仓成功，共 {restored_count['positions']} 个持仓")
            
            # 恢复订单
            if execution_engine:
                orders = self.transaction_manager.get_all_orders()
                for order in orders:
                    execution_engine.order_manager.add_order(order)
                    restored_count['orders'] += 1
                logger.info(f"恢复订单成功，共 {restored_count['orders']} 个订单")
            
            # 恢复系统配置
            self._restore_system_config()
            
            # 检查状态一致性
            self.check_state_consistency(execution_engine, portfolio)
            
            logger.info(f"系统状态恢复完成: {restored_count}")
            return restored_count
        except Exception as e:
            logger.error(f"恢复系统状态失败: {e}", exc_info=True)
            return restored_count
    
    def _restore_system_config(self):
        """
        恢复系统配置
        """
        logger.debug("开始恢复系统配置")
        
        # 从数据库获取系统配置
        # 目前系统配置主要存储在配置文件中，这里可以添加从数据库恢复特定配置的逻辑
        # 例如：恢复最后一次运行的策略列表、恢复风险参数等
        
        # 示例：恢复最后一次保存时间
        last_save_time = self.transaction_manager.get_system_status('last_save_time')
        if last_save_time:
            logger.info(f"最后一次保存时间: {last_save_time}")
        
        logger.debug("系统配置恢复完成")
    
    def save_state(self, execution_engine: ExecutionEngine = None, portfolio: Portfolio = None) -> Dict:
        """
        保存系统状态到数据库
        
        Args:
            execution_engine: 执行引擎实例，若提供则保存订单状态
            portfolio: 投资组合实例，若提供则保存投资组合和持仓状态
        
        Returns:
            保存状态的统计信息
        """
        logger.info("开始保存系统状态")
        
        saved_count = {
            'orders': 0,
            'positions': 0,
            'portfolio': 0
        }
        
        try:
            # 保存投资组合
            if portfolio:
                self.transaction_manager.save_portfolio(portfolio)
                saved_count['portfolio'] = 1
                logger.info(f"保存投资组合成功")
                
                # 保存持仓
                for position in portfolio.get_all_positions():
                    self.transaction_manager.save_position(position)
                    saved_count['positions'] += 1
                logger.info(f"保存持仓成功，共 {saved_count['positions']} 个持仓")
            
            # 保存订单
            if execution_engine:
                orders = execution_engine.order_manager.get_all_orders()
                for order in orders:
                    self.transaction_manager.save_order(order)
                    saved_count['orders'] += 1
                logger.info(f"保存订单成功，共 {saved_count['orders']} 个订单")
            
            # 保存系统状态信息
            self.transaction_manager.save_system_status(
                key='last_save_time',
                value=datetime.now().isoformat()
            )
            
            # 保存当前系统时间
            self.transaction_manager.save_system_status(
                key='current_time',
                value=datetime.now().isoformat()
            )
            
            # 保存系统版本信息
            self.transaction_manager.save_system_status(
                key='system_version',
                value='1.0.0'
            )
            
            logger.info(f"系统状态保存完成: {saved_count}")
            return saved_count
        except Exception as e:
            logger.error(f"保存系统状态失败: {e}", exc_info=True)
            return saved_count
    
    def get_system_status(self, key: str) -> Optional[str]:
        """
        获取系统状态
        
        Args:
            key: 状态键
        
        Returns:
            状态值
        """
        return self.transaction_manager.get_system_status(key)
    
    def set_system_status(self, key: str, value: str):
        """
        设置系统状态
        
        Args:
            key: 状态键
            value: 状态值
        """
        self.transaction_manager.save_system_status(key, value)
    
    def check_state_consistency(self, execution_engine: ExecutionEngine = None, portfolio: Portfolio = None) -> bool:
        """
        检查系统状态一致性
        
        Args:
            execution_engine: 执行引擎实例
            portfolio: 投资组合实例
        
        Returns:
            状态是否一致
        """
        logger.info("开始检查系统状态一致性")
        
        is_consistent = True
        
        # 订单数量一致性检查
        if execution_engine:
            memory_orders = len(execution_engine.order_manager.get_all_orders())
            db_orders = len(self.transaction_manager.get_all_orders())
            if memory_orders != db_orders:
                logger.warning(f"订单数量不一致：内存中 {memory_orders} 个，数据库中 {db_orders} 个")
                is_consistent = False
        
        # 持仓数量一致性检查
        if portfolio:
            memory_positions = len(portfolio.get_all_positions())
            db_positions = len(self.transaction_manager.get_positions())
            if memory_positions != db_positions:
                logger.warning(f"持仓数量不一致：内存中 {memory_positions} 个，数据库中 {db_positions} 个")
                is_consistent = False
        
        # 投资组合总资产一致性检查
        if portfolio:
            # 计算内存中总资产
            memory_total = portfolio.cash
            for position in portfolio.get_all_positions():
                memory_total += position.market_value
            
            # 从数据库获取总资产
            db_portfolio = self.transaction_manager.get_portfolio()
            if db_portfolio and abs(memory_total - db_portfolio.total_value) > 0.01:
                logger.warning(f"投资组合总资产不一致：内存中 {memory_total:.2f}，数据库中 {db_portfolio.total_value:.2f}")
                is_consistent = False
        
        # 活跃订单状态检查
        if execution_engine:
            active_orders = execution_engine.get_active_orders()
            for order in active_orders:
                # 检查订单状态是否为活跃状态
                if not order.status.is_active():
                    logger.warning(f"订单 {order.order_id} 状态不一致：标记为活跃订单，但实际状态为 {order.status}")
                    is_consistent = False
        
        # 持仓数量非零检查
        if portfolio:
            for position in portfolio.get_all_positions():
                if abs(position.quantity) < 0.01:
                    logger.warning(f"持仓 {position.symbol} 数量接近零：{position.quantity}")
                    is_consistent = False
        
        if is_consistent:
            logger.info("系统状态一致性检查通过")
        else:
            logger.warning("系统状态一致性检查未通过")
        
        return is_consistent
    
    def clear_state(self):
        """
        清除系统状态（仅用于测试）
        """
        logger.warning("开始清除系统状态")
        
        # 注意：这里没有实际删除数据，因为TransactionManager没有提供删除方法
        # 实际应用中应该添加删除方法并谨慎使用
        
        logger.warning("系统状态清除完成（仅标记，实际数据未删除）")