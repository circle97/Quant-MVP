# -*- coding: utf-8 -*-
"""
自适应策略执行器 - 根据市场状态自适应调整策略参数
"""
from typing import Dict, Any, Optional
import copy
import numpy as np
import pandas as pd
from loguru import logger

from .market_regime import MarketRegimeClassifier


class AdaptiveStrategyExecutor:
    """
    根据市场状态自适应调整策略参数
    """
    
    def __init__(self, base_strategy, regime_configs: Dict[str, Dict[str, Any]]):
        """
        初始化自适应策略执行器
        
        Args:
            base_strategy: 基础策略实例
            regime_configs: 不同市场状态下的配置字典
                格式: {regime: {params: {param_name: param_value}, position_size: float}}
        """
        self.base_strategy = base_strategy
        self.regime_configs = regime_configs  # 不同市场状态的配置
        self.current_regime = None
        
        # 市场状态分类器
        self.regime_classifier = MarketRegimeClassifier()
    
    def execute_signal(self, market_data: pd.DataFrame, current_position: Optional[float] = None) -> Dict[str, Any]:
        """
        根据当前市场状态生成自适应信号
        
        Args:
            market_data: 市场数据
            current_position: 当前持仓数量
            
        Returns:
            包含信号、市场状态和调整后参数的结果字典
        """
        # 1. 识别当前市场状态
        market_features = self._extract_market_features(market_data)
        regime = self._classify_regime(market_features)
        
        # 2. 获取该状态下的策略配置
        regime_config = self.regime_configs.get(regime, self.regime_configs.get('default', {}))
        
        # 3. 调整策略参数
        adjusted_strategy = self._adjust_strategy_params(
            self.base_strategy, 
            regime_config
        )
        
        # 4. 生成信号
        signal = self._generate_signal(adjusted_strategy, market_data, current_position)
        
        # 5. 添加风险调整
        final_signal = self._apply_risk_adjustment(signal, regime, market_features)
        
        # 更新当前状态
        self.current_regime = regime
        
        return {
            'signal': final_signal,
            'regime': regime,
            'adjusted_params': regime_config,
            'confidence': self._calculate_signal_confidence(signal, regime)
        }
    
    def _extract_market_features(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """
        提取市场特征
        """
        return self.regime_classifier.feature_extractor.extract(market_data)
    
    def _classify_regime(self, market_features: Dict[str, float]) -> str:
        """
        分类市场状态
        """
        # 使用规则分类器进行分类
        return self.regime_classifier.rule_based_classifier.classify(market_features)
    
    def _adjust_strategy_params(self, strategy, regime_config: Dict[str, Any]):
        """
        调整策略参数
        
        Args:
            strategy: 策略实例
            regime_config: 市场状态配置
            
        Returns:
            调整后的策略实例
        """
        # 深拷贝策略避免相互影响
        adjusted = copy.deepcopy(strategy)
        
        # 调整参数
        params = regime_config.get('params', {})
        for param_name, param_value in params.items():
            if hasattr(adjusted, param_name):
                setattr(adjusted, param_name, param_value)
            elif hasattr(adjusted, 'params') and isinstance(adjusted.params, dict):
                adjusted.params[param_name] = param_value
        
        # 调整仓位大小
        adjusted.position_size_multiplier = regime_config.get('position_size', 1.0)
        
        logger.debug(f"调整策略参数: {params}, 仓位乘数: {adjusted.position_size_multiplier}")
        
        return adjusted
    
    def _generate_signal(self, strategy, market_data: pd.DataFrame, current_position: Optional[float] = None):
        """
        生成交易信号
        
        Args:
            strategy: 策略实例
            market_data: 市场数据
            current_position: 当前持仓
            
        Returns:
            交易信号
        """
        # 这里需要根据实际策略的接口进行实现
        # 暂时返回一个模拟信号
        signal_types = ['BUY', 'SELL', 'HOLD']
        return {
            'type': np.random.choice(signal_types),
            'strength': np.random.uniform(0.5, 1.0),
            'price': market_data['close'].iloc[-1],
            'quantity': 100 if current_position is None else abs(current_position) * 2
        }
    
    def _apply_risk_adjustment(self, signal: Dict[str, Any], regime: str, market_features: Dict[str, float]) -> Dict[str, Any]:
        """
        应用风险调整
        
        Args:
            signal: 原始信号
            regime: 市场状态
            market_features: 市场特征
            
        Returns:
            调整后的信号
        """
        adjusted_signal = copy.deepcopy(signal)
        
        # 根据波动率调整仓位大小
        volatility = market_features.get('volatility', 0.15)
        
        # 波动率越高，仓位越小
        volatility_adjustment = 0.15 / (volatility + 0.01)
        adjusted_signal['quantity'] = int(adjusted_signal['quantity'] * volatility_adjustment)
        
        # 根据趋势强度调整信号强度
        trend_strength = market_features.get('trend_strength', 0)
        if signal['type'] == 'BUY' and trend_strength < 0:
            # 买入信号但趋势向下，降低信号强度
            adjusted_signal['strength'] *= 0.5
        elif signal['type'] == 'SELL' and trend_strength > 0:
            # 卖出信号但趋势向上，降低信号强度
            adjusted_signal['strength'] *= 0.5
        
        return adjusted_signal
    
    def _calculate_signal_confidence(self, signal: Dict[str, Any], regime: str) -> float:
        """
        计算信号置信度
        
        Args:
            signal: 交易信号
            regime: 市场状态
            
        Returns:
            信号置信度（0-1）
        """
        # 基础置信度
        base_confidence = signal['strength']
        
        # 根据市场状态调整置信度
        regime_confidence_adjustments = {
            'trend_up': 1.1,  # 趋势明确时置信度更高
            'trend_down': 1.1,
            'range_high_vol': 0.8,  # 高波动区间置信度更低
            'range_low_vol': 0.9
        }
        
        adjustment = regime_confidence_adjustments.get(regime, 1.0)
        final_confidence = base_confidence * adjustment
        
        return min(1.0, max(0.0, final_confidence))
    
    def backtest_adaptive_strategy(self, historical_data: pd.DataFrame) -> pd.DataFrame:
        """
        回测自适应策略
        
        Args:
            historical_data: 历史数据
            
        Returns:
            包含回测结果的DataFrame
        """
        # 初始化回测结果
        results = []
        current_position = 0
        
        # 滚动窗口回测
        lookback = self.regime_classifier.config['lookback_window']
        for i in range(lookback, len(historical_data)):
            # 获取窗口数据
            window_data = historical_data.iloc[i-lookback:i]
            
            # 执行信号生成
            execution_result = self.execute_signal(window_data, current_position)
            
            # 更新持仓
            current_position = self._update_position(current_position, execution_result['signal'])
            
            # 记录结果
            result_row = {
                'timestamp': historical_data.index[i],
                'close_price': historical_data['close'].iloc[i],
                'signal': execution_result['signal'],
                'regime': execution_result['regime'],
                'position': current_position,
                'confidence': execution_result['confidence'],
                'adjusted_params': execution_result['adjusted_params']
            }
            results.append(result_row)
        
        return pd.DataFrame(results).set_index('timestamp')
    
    def _update_position(self, current_position: float, signal: Dict[str, Any]) -> float:
        """
        根据信号更新持仓
        """
        if signal['type'] == 'BUY':
            return current_position + signal['quantity']
        elif signal['type'] == 'SELL':
            return current_position - signal['quantity']
        else:
            return current_position
    
    def optimize_regime_configs(self, historical_data: pd.DataFrame, param_grid: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化不同市场状态下的策略配置
        
        Args:
            historical_data: 历史数据
            param_grid: 参数网格，用于搜索最优参数
            
        Returns:
            优化后的市场状态配置
        """
        # 这里需要实现参数优化逻辑
        # 暂时返回原始配置
        logger.info("优化市场状态配置...")
        return self.regime_configs
    
    def generate_adaptive_report(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成自适应策略报告
        
        Args:
            historical_data: 历史数据
            
        Returns:
            自适应策略报告
        """
        # 回测自适应策略
        backtest_results = self.backtest_adaptive_strategy(historical_data)
        
        # 计算各市场状态下的表现
        regime_performance = self._calculate_regime_performance(backtest_results, historical_data)
        
        # 计算整体表现
        overall_performance = self._calculate_overall_performance(backtest_results, historical_data)
        
        return {
            'backtest_results': backtest_results,
            'regime_performance': regime_performance,
            'overall_performance': overall_performance,
            'regime_configs': self.regime_configs,
            'current_regime': self.current_regime
        }
    
    def _calculate_regime_performance(self, backtest_results: pd.DataFrame, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        计算各市场状态下的表现
        """
        performance = {}
        
        # 按市场状态分组
        regime_groups = backtest_results.groupby('regime')
        
        for regime, group in regime_groups:
            if len(group) < 10:  # 跳过数据量太少的状态
                continue
            
            # 计算该状态下的收益率
            returns = self._calculate_returns(group, historical_data)
            
            performance[regime] = {
                'count': len(group),
                'win_rate': self._calculate_win_rate(group),
                'avg_return': returns.mean(),
                'std_return': returns.std(),
                'sharpe': self._calculate_sharpe_ratio(returns),
                'max_drawdown': self._calculate_max_drawdown(returns)
            }
        
        return performance
    
    def _calculate_overall_performance(self, backtest_results: pd.DataFrame, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """
        计算整体表现
        """
        returns = self._calculate_returns(backtest_results, historical_data)
        
        return {
            'total_trades': len(backtest_results),
            'win_rate': self._calculate_win_rate(backtest_results),
            'avg_return': returns.mean(),
            'std_return': returns.std(),
            'sharpe': self._calculate_sharpe_ratio(returns),
            'max_drawdown': self._calculate_max_drawdown(returns)
        }
    
    def _calculate_returns(self, backtest_results: pd.DataFrame, historical_data: pd.DataFrame) -> pd.Series:
        """
        计算收益率
        """
        # 这里需要根据实际情况实现
        # 暂时返回模拟收益率
        return pd.Series(np.random.normal(0.001, 0.01, len(backtest_results)))
    
    def _calculate_win_rate(self, backtest_results: pd.DataFrame) -> float:
        """
        计算胜率
        """
        # 这里需要根据实际情况实现
        # 暂时返回模拟胜率
        return np.random.uniform(0.4, 0.6)
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """
        计算夏普比率
        """
        if returns.std() == 0:
            return 0.0
        
        return (returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        计算最大回撤
        """
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        return drawdown.min()
