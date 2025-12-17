# -*- coding: utf-8 -*-
"""
策略验证模块 - 用于验证策略的有效性、稳健性和防止过拟合
"""

from .validation_pipeline import StrategyValidationPipeline
from .overfitting_detector import OverfittingDetector
from .robustness_scorer import RobustnessScorer
from .market_regime import MarketRegimeClassifier, RuleBasedClassifier
from .adaptive_executor import AdaptiveStrategyExecutor
from .factor_analyzer import FactorEffectivenessScorer
from .portfolio_optimizer import StrategyPortfolioOptimizer
from .strategy_generator import StrategyIdeaGenerator, LLMGenerator
from .live_preparer import LiveTradingPreparer

__all__ = [
    # 阶段1: 策略有效性验证框架
    'StrategyValidationPipeline',
    'OverfittingDetector',
    'RobustnessScorer',
    
    # 阶段2: 市场状态识别与自适应机制
    'MarketRegimeClassifier',
    'RuleBasedClassifier',
    'AdaptiveStrategyExecutor',
    
    # 阶段3: 因子有效性分析与组合构建
    'FactorEffectivenessScorer',
    'StrategyPortfolioOptimizer',
    
    # 阶段4: 轻量级AI集成与实盘准备
    'StrategyIdeaGenerator',
    'LLMGenerator',
    'LiveTradingPreparer'
]
