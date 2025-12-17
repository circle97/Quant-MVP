# -*- coding: utf-8 -*-
"""
策略组合优化器 - 基于风险和相关性构建策略组合
"""
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from loguru import logger


class StrategyPortfolioOptimizer:
    """
    基于风险和相关性构建策略组合
    """
    
    def __init__(self, optimization_method: str = 'risk_parity'):
        self.method = optimization_method
        self.min_correlation_threshold = 0.3
    
    def optimize_portfolio(self, strategies_returns: pd.DataFrame, constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        优化策略组合权重
        
        Args:
            strategies_returns: 各策略的收益率DataFrame，行索引为时间，列名为策略名称
            constraints: 约束条件字典（可选）
            
        Returns:
            包含优化后权重、选中策略和预期夏普比率的结果字典
        """
        # 1. 计算策略间相关性
        correlation_matrix = strategies_returns.corr()
        
        # 2. 筛选低相关性策略组合
        selected_strategies = self._select_diverse_strategies(
            correlation_matrix, 
            strategies_returns.columns.tolist()
        )
        
        # 3. 根据优化方法计算权重
        if self.method == 'risk_parity':
            weights = self._risk_parity_optimization(
                strategies_returns[selected_strategies]
            )
        elif self.method == 'equal_risk_contribution':
            weights = self._equal_risk_contribution(
                strategies_returns[selected_strategies]
            )
        else:  # 等权重
            n = len(selected_strategies)
            weights = {s: 1.0/n for s in selected_strategies}
        
        # 4. 应用约束
        if constraints:
            weights = self._apply_constraints(weights, constraints)
        
        return {
            'weights': weights,
            'selected_strategies': selected_strategies,
            'correlation_matrix': correlation_matrix,
            'expected_sharpe': self._estimate_sharpe(strategies_returns, weights)
        }
    
    def _select_diverse_strategies(self, corr_matrix: pd.DataFrame, all_strategies: List[str], 
                                  max_strategies: int = 8) -> List[str]:
        """
        选择低相关性的策略组合
        
        Args:
            corr_matrix: 策略间相关系数矩阵
            all_strategies: 所有可用策略列表
            max_strategies: 最大策略数量
            
        Returns:
            选中的策略列表
        """
        selected = []
        remaining = all_strategies.copy()
        
        if not all_strategies:
            return selected
        
        # 先选择夏普比率最高的策略（这里简化处理，假设第一个策略夏普最高）
        selected.append(all_strategies[0])
        remaining.remove(all_strategies[0])
        
        # 贪心选择：每次选择与已选策略平均相关性最低的
        while len(selected) < min(max_strategies, len(all_strategies)) and remaining:
            best_candidate = None
            best_avg_correlation = float('inf')
            
            for candidate in remaining:
                # 计算候选策略与已选策略的平均相关性
                avg_corr = np.mean([
                    abs(corr_matrix.loc[candidate, s]) 
                    for s in selected
                ])
                
                if avg_corr < best_avg_correlation:
                    best_avg_correlation = avg_corr
                    best_candidate = candidate
            
            # 如果平均相关性过高，停止添加
            if best_avg_correlation > 0.6:
                break
            
            selected.append(best_candidate)
            remaining.remove(best_candidate)
        
        return selected
    
    def _risk_parity_optimization(self, returns: pd.DataFrame) -> Dict[str, float]:
        """
        风险平价优化
        使每个策略贡献相等的风险
        
        Args:
            returns: 选中策略的收益率DataFrame
            
        Returns:
            优化后的权重字典
        """
        # 简化实现：基于波动率的风险平价
        # 实际实现中可以使用更复杂的优化算法
        volatilities = returns.std()
        inverse_vol = 1.0 / volatilities
        weights = inverse_vol / inverse_vol.sum()
        
        return weights.to_dict()
    
    def _equal_risk_contribution(self, returns: pd.DataFrame) -> Dict[str, float]:
        """
        等风险贡献优化
        
        Args:
            returns: 选中策略的收益率DataFrame
            
        Returns:
            优化后的权重字典
        """
        # 这里实现简化版的等风险贡献
        # 实际实现需要使用优化算法求解
        cov_matrix = returns.cov()
        n = len(returns.columns)
        
        # 初始权重设为等权重
        weights = np.ones(n) / n
        
        # 迭代调整权重
        for _ in range(100):
            # 计算每个策略的边际风险贡献
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
            marginal_contributions = (cov_matrix @ weights) / portfolio_vol
            total_contributions = weights * marginal_contributions
            
            # 计算风险贡献差异
            target_contribution = portfolio_vol / n
            diff = total_contributions - target_contribution
            
            # 调整权重
            weights -= 0.01 * diff
            weights = np.maximum(0.01, weights)  # 确保权重不为负且至少为0.01
            weights /= weights.sum()  # 归一化
        
        return {returns.columns[i]: weights[i] for i in range(n)}
    
    def _apply_constraints(self, weights: Dict[str, float], constraints: Dict[str, Any]) -> Dict[str, float]:
        """
        应用约束条件
        
        Args:
            weights: 初始权重字典
            constraints: 约束条件字典，支持以下约束：
                - min_weight: 单个策略最小权重
                - max_weight: 单个策略最大权重
                - min_total_weight: 总权重下限（通常为1.0）
                - max_total_weight: 总权重上限（通常为1.0）
            
        Returns:
            应用约束后的权重字典
        """
        adjusted_weights = weights.copy()
        
        # 应用单个策略权重约束
        min_weight = constraints.get('min_weight', 0.0)
        max_weight = constraints.get('max_weight', 1.0)
        
        for strategy in adjusted_weights:
            adjusted_weights[strategy] = max(min_weight, min(max_weight, adjusted_weights[strategy]))
        
        # 归一化权重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            for strategy in adjusted_weights:
                adjusted_weights[strategy] /= total_weight
        
        return adjusted_weights
    
    def _estimate_sharpe(self, returns: pd.DataFrame, weights: Dict[str, float]) -> float:
        """
        估计组合的夏普比率
        
        Args:
            returns: 策略收益率DataFrame
            weights: 策略权重字典
            
        Returns:
            估计的夏普比率
        """
        # 将权重转换为向量
        weight_vector = np.array([weights.get(col, 0) for col in returns.columns])
        
        # 计算组合收益率
        portfolio_returns = returns @ weight_vector
        
        # 计算夏普比率
        sharpe = (portfolio_returns.mean() / portfolio_returns.std()) * np.sqrt(252) if portfolio_returns.std() != 0 else 0
        
        return sharpe
    
    def backtest_portfolio(self, strategies_returns: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
        """
        回测策略组合
        
        Args:
            strategies_returns: 策略收益率DataFrame
            weights: 策略权重字典
            
        Returns:
            组合收益率序列
        """
        # 将权重应用到收益率
        weight_vector = np.array([weights.get(col, 0) for col in strategies_returns.columns])
        portfolio_returns = strategies_returns @ weight_vector
        
        return portfolio_returns
    
    def calculate_portfolio_performance(self, portfolio_returns: pd.Series) -> Dict[str, float]:
        """
        计算组合表现指标
        
        Args:
            portfolio_returns: 组合收益率序列
            
        Returns:
            包含各项表现指标的字典
        """
        annual_return = portfolio_returns.mean() * 252
        annual_vol = portfolio_returns.std() * np.sqrt(252)
        sharpe = (annual_return / annual_vol) if annual_vol != 0 else 0
        
        # 计算最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()
        
        # 计算胜率
        win_rate = (portfolio_returns > 0).mean()
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_return': cumulative.iloc[-1] - 1
        }
    
    def generate_portfolio_report(self, strategies_returns: pd.DataFrame, 
                                optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成组合优化报告
        
        Args:
            strategies_returns: 策略收益率DataFrame
            optimization_result: 优化结果字典
            
        Returns:
            组合优化报告
        """
        # 回测组合
        portfolio_returns = self.backtest_portfolio(
            strategies_returns, optimization_result['weights']
        )
        
        # 计算组合表现
        performance = self.calculate_portfolio_performance(portfolio_returns)
        
        # 计算各策略的表现
        strategies_performance = {}
        for strategy in optimization_result['selected_strategies']:
            strat_returns = strategies_returns[strategy]
            strategies_performance[strategy] = self.calculate_portfolio_performance(strat_returns)
        
        return {
            'optimization_method': self.method,
            'weights': optimization_result['weights'],
            'selected_strategies': optimization_result['selected_strategies'],
            'correlation_matrix': optimization_result['correlation_matrix'],
            'portfolio_performance': performance,
            'strategies_performance': strategies_performance,
            'expected_sharpe': optimization_result['expected_sharpe'],
            'actual_sharpe': performance['sharpe_ratio'],
            'portfolio_returns': portfolio_returns
        }
    
    def rebalance_portfolio(self, strategies_returns: pd.DataFrame, 
                          current_weights: Dict[str, float], 
                          rebalance_threshold: float = 0.1) -> Dict[str, Any]:
        """
        重新平衡组合
        
        Args:
            strategies_returns: 策略收益率DataFrame
            current_weights: 当前权重字典
            rebalance_threshold: 再平衡阈值（当权重偏差超过此值时触发再平衡）
            
        Returns:
            包含是否需要再平衡和新权重的结果字典
        """
        # 计算新的优化权重
        new_optimization = self.optimize_portfolio(strategies_returns)
        new_weights = new_optimization['weights']
        
        # 检查是否需要再平衡
        needs_rebalance = any(
            abs(new_weights.get(s, 0) - current_weights.get(s, 0)) > rebalance_threshold
            for s in set(current_weights.keys()) | set(new_weights.keys())
        )
        
        return {
            'needs_rebalance': needs_rebalance,
            'new_weights': new_weights,
            'current_weights': current_weights,
            'optimization_result': new_optimization
        }
