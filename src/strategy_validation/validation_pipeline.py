# -*- coding: utf-8 -*-
"""
策略验证流水线 - 防止过拟合的核心工具
"""
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from loguru import logger


class BaseValidationMethod(ABC):
    """验证方法基类"""
    
    @abstractmethod
    def validate(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        """
        执行验证
        
        Args:
            strategy: 待验证的策略实例
            data: 用于验证的数据
            
        Returns:
            验证结果字典
        """
        pass
    
    def _train_and_test(self, strategy, train_data: pd.DataFrame, test_data: pd.DataFrame):
        """
        训练和测试策略
        
        Args:
            strategy: 策略实例
            train_data: 训练数据
            test_data: 测试数据
            
        Returns:
            包含sharpe、max_drawdown等指标的结果对象
        """
        # 这里需要根据实际策略的接口进行实现
        # 暂时返回一个模拟结果
        class MockResult:
            def __init__(self):
                self.sharpe = np.random.normal(1.0, 0.5)
                self.max_drawdown = np.random.uniform(0.05, 0.2)
                self.annual_return = np.random.uniform(0.05, 0.3)
                self.win_rate = np.random.uniform(0.4, 0.6)
        
        return MockResult()


class TimeSplitValidation(BaseValidationMethod):
    """时间分割验证"""
    
    def __init__(self, train_ratio: float = 0.6):
        self.train_ratio = train_ratio
    
    def validate(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        train_data, test_data = self._split_data(data)
        base_result = self._train_and_test(strategy, train_data, test_data)
        
        return {
            'type': 'time_split',
            'train_ratio': self.train_ratio,
            'result': base_result
        }
    
    def _split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """分割数据为训练集和测试集"""
        split_idx = int(len(data) * self.train_ratio)
        return data.iloc[:split_idx], data.iloc[split_idx:]


class WalkForwardValidation(BaseValidationMethod):
    """前向遍历验证"""
    
    def __init__(self, window_size: int = 252, step_size: int = 63):
        self.window_size = window_size
        self.step_size = step_size
    
    def validate(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        results = []
        for train_window, test_window in self._get_windows(data):
            result = self._train_and_test(strategy, train_window, test_window)
            results.append(result)
        
        return {
            'type': 'walk_forward',
            'window_size': self.window_size,
            'step_size': self.step_size,
            'results': results
        }
    
    def _get_windows(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """生成前向遍历的滑动窗口"""
        windows = []
        total_len = len(data)
        
        for i in range(0, total_len - self.window_size, self.step_size):
            train_window = data.iloc[i:i+self.window_size]
            test_window = data.iloc[i+self.window_size:i+self.window_size+self.step_size]
            if len(test_window) > 0:
                windows.append((train_window, test_window))
        
        return windows


class MonteCarloValidation(BaseValidationMethod):
    """蒙特卡洛验证"""
    
    def __init__(self, num_simulations: int = 100, train_ratio: float = 0.6):
        self.num_simulations = num_simulations
        self.train_ratio = train_ratio
    
    def validate(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        results = []
        for i in range(self.num_simulations):
            train_data, test_data = self._random_split(data)
            result = self._train_and_test(strategy, train_data, test_data)
            results.append(result)
        
        return {
            'type': 'monte_carlo',
            'num_simulations': self.num_simulations,
            'results': results
        }
    
    def _random_split(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """随机分割数据"""
        # 使用时间序列保持的随机分割（按时间块随机选择）
        n = len(data)
        train_size = int(n * self.train_ratio)
        
        # 随机选择起始位置
        start_idx = np.random.randint(0, n - train_size)
        train_data = data.iloc[start_idx:start_idx+train_size]
        test_data = pd.concat([data.iloc[:start_idx], data.iloc[start_idx+train_size:]])
        
        return train_data, test_data


class RegimeAwareValidation(BaseValidationMethod):
    """市场状态感知验证"""
    
    def __init__(self, regime_classifier):
        self.regime_classifier = regime_classifier
    
    def validate(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        # 分类市场状态
        regimes = self.regime_classifier.classify_market_regimes(data)
        
        # 按市场状态分组验证
        regime_results = {}
        for regime, regime_data in self._group_by_regime(data, regimes).items():
            if len(regime_data) > 50:  # 确保有足够数据
                train_data, test_data = self._split_data(regime_data)
                result = self._train_and_test(strategy, train_data, test_data)
                regime_results[regime] = result
        
        return {
            'type': 'regime_aware',
            'regime_classifier': self.regime_classifier.__class__.__name__,
            'results': regime_results
        }
    
    def _split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """分割数据"""
        split_idx = int(len(data) * 0.6)
        return data.iloc[:split_idx], data.iloc[split_idx:]
    
    def _group_by_regime(self, data: pd.DataFrame, regimes: pd.Series) -> Dict[str, pd.DataFrame]:
        """按市场状态分组数据"""
        grouped = {}
        for regime in regimes.unique():
            grouped[regime] = data[regimes == regime]
        return grouped


class StrategyValidationPipeline:
    """
    策略验证流水线 - 防止过拟合的核心工具
    """
    def __init__(self, regime_classifier=None):
        self.validation_methods = [
            ('time_split', TimeSplitValidation()),
            ('walk_forward', WalkForwardValidation()),
            ('monte_carlo', MonteCarloValidation())
        ]
        # 只有当提供了regime_classifier时，才添加regime_aware验证
        if regime_classifier is not None:
            self.validation_methods.append(
                ('regime_aware', RegimeAwareValidation(regime_classifier))
            )
    
    def validate_strategy(self, strategy, full_data: pd.DataFrame):
        """
        执行多层验证，返回稳健性评分
        
        Args:
            strategy: 待验证的策略实例
            full_data: 完整的历史数据
            
        Returns:
            验证结果字典，包含稳健性评分和详细结果
        """
        validation_results = {}
        
        # 1. 基础时间分割验证
        logger.info("执行基础时间分割验证...")
        time_split_method = TimeSplitValidation()
        time_split_result = time_split_method.validate(strategy, full_data)
        validation_results['base'] = time_split_result['result']
        
        # 2. 执行所有验证方法
        for method_name, method in self.validation_methods:
            logger.info(f"执行{method_name}验证...")
            try:
                result = method.validate(strategy, full_data)
                validation_results[method_name] = result
            except Exception as e:
                logger.error(f"{method_name}验证失败: {e}")
                validation_results[method_name] = {'error': str(e)}
        
        # 3. 计算稳健性评分（0-100）
        logger.info("计算稳健性评分...")
        robustness_score = self._calculate_robustness_score(validation_results)
        
        return {
            'score': robustness_score,
            'details': validation_results,
            'recommendation': '通过' if robustness_score > 70 else '拒绝'
        }
    
    def _calculate_robustness_score(self, results: Dict[str, Any]) -> float:
        """
        加权计算策略稳健性评分
        权重分配：
        - 样本外表现一致性: 40%
        - 参数敏感性: 30%
        - 市场状态适应性: 30%
        """
        score = 0
        
        # 检查样本外表现一致性
        out_of_sample_performance = []
        for method_name, result in results.items():
            if method_name == 'base':
                # 基础结果直接取sharpe
                if hasattr(result, 'sharpe'):
                    out_of_sample_performance.append(result.sharpe)
            elif method_name == 'walk_forward':
                # 前向遍历结果取所有窗口sharpe的平均值
                walk_forward_results = result.get('results', [])
                for wf_result in walk_forward_results:
                    if hasattr(wf_result, 'sharpe'):
                        out_of_sample_performance.append(wf_result.sharpe)
            elif method_name == 'monte_carlo':
                # 蒙特卡洛结果取所有模拟sharpe的平均值
                mc_results = result.get('results', [])
                for mc_result in mc_results:
                    if hasattr(mc_result, 'sharpe'):
                        out_of_sample_performance.append(mc_result.sharpe)
            elif method_name == 'regime_aware':
                # 市场状态感知结果取各状态sharpe的平均值
                regime_results = result.get('results', {})
                for regime_result in regime_results.values():
                    if hasattr(regime_result, 'sharpe'):
                        out_of_sample_performance.append(regime_result.sharpe)
        
        # 计算变异系数（越低越好）
        if len(out_of_sample_performance) > 1:
            mean_perf = np.mean(out_of_sample_performance)
            std_perf = np.std(out_of_sample_performance)
            
            if mean_perf != 0:
                cv = std_perf / abs(mean_perf)
                consistency_score = max(0, 100 * (1 - cv))
                score += consistency_score * 0.4
            else:
                score += 0 * 0.4
        else:
            score += 50 * 0.4
        
        # 参数敏感性评分（简化实现）
        param_sensitivity_score = 70  # 假设中等敏感性
        score += param_sensitivity_score * 0.3
        
        # 市场适应性评分（简化实现）
        regime_aware_result = results.get('regime_aware', {})
        regime_results = regime_aware_result.get('results', {})
        
        if len(regime_results) >= 3:
            # 检查各状态下表现是否都为正
            positive_regimes = sum(1 for r in regime_results.values() if hasattr(r, 'sharpe') and r.sharpe > 0)
            market_adaptability = (positive_regimes / len(regime_results)) * 100
        else:
            market_adaptability = 50
        
        score += market_adaptability * 0.3
        
        return min(100, max(0, score))
    
    def _train_and_test(self, strategy, train_data: pd.DataFrame, test_data: pd.DataFrame):
        """
        训练和测试策略
        
        Args:
            strategy: 策略实例
            train_data: 训练数据
            test_data: 测试数据
            
        Returns:
            包含sharpe、max_drawdown等指标的结果对象
        """
        # 这里需要根据实际策略的接口进行实现
        # 暂时返回一个模拟结果
        class MockResult:
            def __init__(self):
                self.sharpe = np.random.normal(1.0, 0.5)
                self.max_drawdown = np.random.uniform(0.05, 0.2)
                self.annual_return = np.random.uniform(0.05, 0.3)
                self.win_rate = np.random.uniform(0.4, 0.6)
        
        return MockResult()
