# -*- coding: utf-8 -*-
"""
回测模块 - 负责策略的回测执行和结果分析
"""

from .backtest_engine import BacktestEngine
from .backtest_data_manager import BacktestDataManager
from .backtest_execution_engine import BacktestExecutionEngine
from .backtest_analyzer import BacktestAnalyzer

__all__ = [
    'BacktestEngine',
    'BacktestDataManager',
    'BacktestExecutionEngine',
    'BacktestAnalyzer'
]

__version__ = '1.0.0'
