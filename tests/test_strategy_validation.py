# -*- coding: utf-8 -*-
"""
测试策略验证模块
"""
import sys
import os
import numpy as np
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.strategy_validation import (
    StrategyValidationPipeline,
    OverfittingDetector,
    RobustnessScorer,
    MarketRegimeClassifier,
    AdaptiveStrategyExecutor,
    FactorEffectivenessScorer,
    StrategyPortfolioOptimizer,
    StrategyIdeaGenerator,
    LiveTradingPreparer
)


class MockStrategy:
    """模拟策略类用于测试"""
    
    def __init__(self, name="MockStrategy"):
        self.name = name
        self.params = {
            'param1': 10,
            'param2': 0.5
        }
    
    def generate_signal(self, symbol, signal_type, strength=1.0, price=None):
        """生成交易信号"""
        return {
            'symbol': symbol,
            'signal_type': signal_type,
            'strength': strength,
            'price': price
        }
    
    def get_strategy_state(self):
        """获取策略状态"""
        return {
            'name': self.name,
            'params': self.params,
            'running': True
        }


# 创建模拟数据
def create_mock_data(length=1000):
    """创建模拟的价格数据"""
    dates = pd.date_range('2020-01-01', periods=length)
    
    # 生成带有趋势和噪声的价格数据
    trend = np.linspace(0, 100, length)
    noise = np.random.normal(0, 10, length)
    price = 100 + trend + noise
    
    volume = np.random.randint(1000, 10000, length)
    high = price + np.random.uniform(0, 5, length)
    low = price - np.random.uniform(0, 5, length)
    open_ = low + np.random.uniform(0, 5, length)
    close = price
    
    return pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)


# 测试策略验证流水线
def test_strategy_validation_pipeline():
    """测试策略验证流水线"""
    # 创建模拟数据和策略
    mock_data = create_mock_data()
    mock_strategy = MockStrategy()
    
    # 初始化验证流水线
    validation_pipeline = StrategyValidationPipeline()
    
    # 执行验证
    validation_result = validation_pipeline.validate_strategy(mock_strategy, mock_data)
    
    # 验证结果
    assert 'score' in validation_result
    assert 'details' in validation_result
    assert 'recommendation' in validation_result
    assert 0 <= validation_result['score'] <= 100
    print(f"策略验证流水线测试通过，得分: {validation_result['score']}")


# 测试过拟合检测器
def test_overfitting_detector():
    """测试过拟合检测器"""
    # 创建模拟数据和策略
    mock_data = create_mock_data()
    mock_strategy = MockStrategy()
    
    # 初始化过拟合检测器
    detector = OverfittingDetector()
    
    # 生成过拟合检测报告
    report = detector.generate_overfitting_report(mock_strategy, mock_data)
    
    # 验证结果
    assert 'train_test_gap' in report
    assert 'parameter_sensitivity' in report
    assert 'feature_stability' in report
    assert 'overall' in report
    print("过拟合检测器测试通过")


# 测试稳健性评分器
def test_robustness_scorer():
    """测试稳健性评分器"""
    # 创建模拟数据和策略
    mock_data = create_mock_data()
    mock_strategy = MockStrategy()
    
    # 先运行验证流水线获取结果
    validation_pipeline = StrategyValidationPipeline()
    validation_result = validation_pipeline.validate_strategy(mock_strategy, mock_data)
    
    # 初始化稳健性评分器
    scorer = RobustnessScorer()
    
    # 评分策略
    score_result = scorer.score_strategy(mock_strategy, validation_result)
    
    # 验证结果
    assert 'overall_score' in score_result
    assert 'grade' in score_result
    assert 'dimension_scores' in score_result
    assert 0 <= score_result['overall_score'] <= 100
    print(f"稳健性评分器测试通过，得分: {score_result['overall_score']}, 等级: {score_result['grade']}")


# 测试市场状态分类器
def test_market_regime_classifier():
    """测试市场状态分类器"""
    # 创建模拟数据
    mock_data = create_mock_data()
    
    # 初始化分类器
    classifier = MarketRegimeClassifier()
    
    # 分类当前市场状态
    current_regime = classifier.classify_current_market(mock_data)
    
    # 验证结果
    assert 'regime' in current_regime
    assert 'confidence' in current_regime
    assert 'features' in current_regime
    assert 0 <= current_regime['confidence'] <= 1.0
    
    # 测试历史市场状态分类
    regime_history = classifier.classify_market_regimes(mock_data)
    assert isinstance(regime_history, pd.Series)
    print(f"市场状态分类器测试通过，当前状态: {current_regime['regime']}, 置信度: {current_regime['confidence']}")


# 测试自适应策略执行器
def test_adaptive_strategy_executor():
    """测试自适应策略执行器"""
    # 创建模拟数据和策略
    mock_data = create_mock_data()
    mock_strategy = MockStrategy()
    
    # 定义不同市场状态的配置
    regime_configs = {
        'trend_up': {
            'params': {'param1': 15, 'param2': 0.7},
            'position_size': 1.2
        },
        'trend_down': {
            'params': {'param1': 5, 'param2': 0.3},
            'position_size': 0.8
        },
        'range_high_vol': {
            'params': {'param1': 10, 'param2': 0.5},
            'position_size': 0.5
        },
        'range_low_vol': {
            'params': {'param1': 20, 'param2': 0.6},
            'position_size': 1.0
        },
        'default': {
            'params': {'param1': 10, 'param2': 0.5},
            'position_size': 1.0
        }
    }
    
    # 初始化执行器
    executor = AdaptiveStrategyExecutor(mock_strategy, regime_configs)
    
    # 执行信号生成
    execution_result = executor.execute_signal(mock_data)
    
    # 验证结果
    assert 'signal' in execution_result
    assert 'regime' in execution_result
    assert 'adjusted_params' in execution_result
    assert 'confidence' in execution_result
    print(f"自适应策略执行器测试通过，执行结果: {execution_result['regime']}")


# 测试因子有效性评分器
def test_factor_effectiveness_scorer():
    """测试因子有效性评分器"""
    # 创建模拟数据
    mock_data = create_mock_data()
    
    # 生成模拟因子
    factor_series = mock_data['close'].rolling(20).mean()
    returns_series = mock_data['close'].pct_change().dropna()
    
    # 初始化评分器
    scorer = FactorEffectivenessScorer()
    
    # 评分因子
    score_result = scorer.score_factor(factor_series, returns_series)
    
    # 验证结果
    assert 'score' in score_result
    assert 'details' in score_result
    assert 'grade' in score_result
    assert 0 <= score_result['score'] <= 100
    print(f"因子有效性评分器测试通过，得分: {score_result['score']}, 等级: {score_result['grade']}")


# 测试策略组合优化器
def test_strategy_portfolio_optimizer():
    """测试策略组合优化器"""
    # 创建模拟的策略收益率数据
    dates = pd.date_range('2020-01-01', periods=1000)
    strategy_returns = pd.DataFrame({
        'strategy1': np.random.normal(0.001, 0.01, 1000),
        'strategy2': np.random.normal(0.0012, 0.012, 1000),
        'strategy3': np.random.normal(0.0008, 0.008, 1000),
        'strategy4': np.random.normal(0.0015, 0.015, 1000)
    }, index=dates)
    
    # 初始化优化器
    optimizer = StrategyPortfolioOptimizer(optimization_method='risk_parity')
    
    # 执行优化
    optimization_result = optimizer.optimize_portfolio(strategy_returns)
    
    # 验证结果
    assert 'weights' in optimization_result
    assert 'selected_strategies' in optimization_result
    assert 'correlation_matrix' in optimization_result
    assert 'expected_sharpe' in optimization_result
    
    # 验证权重之和为1
    total_weight = sum(optimization_result['weights'].values())
    assert abs(total_weight - 1.0) < 0.01
    print(f"策略组合优化器测试通过，预期夏普比率: {optimization_result['expected_sharpe']}")


# 测试策略想法生成器
def test_strategy_idea_generator():
    """测试策略想法生成器"""
    # 初始化生成器（不使用LLM）
    generator = StrategyIdeaGenerator(use_api_llm=False)
    
    # 生成策略想法
    market_context = {
        'market_regime': 'trend_up',
        'volatility': 0.15,
        'trend_strength': 0.6
    }
    
    constraints = {
        'max_holding_period': 30,
        'min_sharpe_ratio': 1.0
    }
    
    ideas = generator.generate_ideas(market_context, constraints)
    
    # 验证结果
    assert len(ideas) <= 10
    for idea in ideas:
        assert 'name' in idea
        assert 'type' in idea
        assert 'description' in idea
        assert 'params' in idea
    print(f"策略想法生成器测试通过，生成了 {len(ideas)} 个策略想法")


# 测试实盘准备器
def test_live_trading_preparer():
    """测试实盘准备器"""
    # 创建模拟数据和策略
    mock_data = create_mock_data()
    mock_strategy = MockStrategy()
    
    # 初始化准备器
    preparer = LiveTradingPreparer()
    
    # 生成实盘交易检查清单
    checklist = preparer.generate_live_trading_checklist()
    
    # 验证结果
    assert len(checklist) > 0
    for category in checklist:
        assert 'category' in category
        assert 'items' in category
        assert len(category['items']) > 0
    
    print(f"实盘准备器测试通过，生成了 {len(checklist)} 个检查类别")


# 运行所有测试
if __name__ == "__main__":
    print("开始测试高级策略模式组件...")
    
    # 运行所有测试函数
    test_strategy_validation_pipeline()
    test_overfitting_detector()
    test_robustness_scorer()
    test_market_regime_classifier()
    test_adaptive_strategy_executor()
    test_factor_effectiveness_scorer()
    test_strategy_portfolio_optimizer()
    test_strategy_idea_generator()
    test_live_trading_preparer()
    
    print("所有测试通过！")
