# -*- coding: utf-8 -*-
"""
因子有效性分析模块 - 用于评估因子的有效性和稳定性
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from loguru import logger


class FactorEffectivenessScorer:
    """
    从多个维度评估因子有效性
    """
    
    def __init__(self):
        # 评分指标权重配置
        self.metrics_weights = {
            'ic_mean': 0.25,        # 信息系数均值
            'ic_ir': 0.20,         # 信息比率
            'ic_std': -0.15,       # IC标准差（负权重）
            'turnover': -0.15,     # 换手率（负权重）
            'decay_half_life': 0.15, # 半衰期
            'regime_stability': 0.10 # 市场状态稳定性
        }
    
    def score_factor(self, factor_series: pd.Series, returns_series: pd.Series, 
                    regime_series: pd.Series = None) -> Dict[str, Any]:
        """
        计算因子综合评分（0-100）
        
        Args:
            factor_series: 因子值序列
            returns_series: 收益率序列
            regime_series: 市场状态序列（可选）
            
        Returns:
            包含因子评分和各维度详细结果的字典
        """
        scores = {}
        
        # 1. 计算信息系数相关指标
        ic_series = self._calculate_ic_series(factor_series, returns_series)
        scores['ic_mean'] = self._normalize_score(np.mean(ic_series), -0.1, 0.1)
        scores['ic_ir'] = self._normalize_score(
            np.mean(ic_series) / (np.std(ic_series) + 1e-8), 
            0, 2
        )
        scores['ic_std'] = self._normalize_score(np.std(ic_series), 0, 0.05, invert=True)
        
        # 2. 计算换手率
        turnover = self._calculate_factor_turnover(factor_series)
        scores['turnover'] = self._normalize_score(turnover, 0, 0.5, invert=True)
        
        # 3. 计算衰减半衰期
        decay_rate = self._calculate_decay_rate(ic_series)
        half_life = -np.log(2) / (decay_rate + 1e-8)
        scores['decay_half_life'] = self._normalize_score(half_life, 5, 30)
        
        # 4. 市场状态稳定性
        if regime_series is not None:
            stability_score = self._calculate_regime_stability(
                ic_series, regime_series
            )
            scores['regime_stability'] = stability_score
        
        # 5. 加权计算总分
        total_score = 0
        for metric, weight in self.metrics_weights.items():
            if metric in scores:
                total_score += scores[metric] * weight
        
        # 转换为0-100分
        final_score = max(0, min(100, 50 + total_score * 50))
        
        return {
            'score': final_score,
            'details': scores,
            'grade': self._score_to_grade(final_score),
            'ic_series': ic_series,
            'half_life': half_life,
            'turnover': turnover
        }
    
    def select_top_factors(self, factor_dict: Dict[str, pd.Series], 
                          returns_series: pd.Series, 
                          top_n: int = 10) -> Dict[str, Any]:
        """
        选择得分最高的因子
        
        Args:
            factor_dict: 因子字典，键为因子名称，值为因子序列
            returns_series: 收益率序列
            top_n: 要选择的顶级因子数量
            
        Returns:
            包含顶级因子和所有因子评分的结果字典
        """
        factor_scores = {}
        
        for factor_name, factor_data in factor_dict.items():
            score_result = self.score_factor(factor_data, returns_series)
            factor_scores[factor_name] = score_result['score']
        
        # 按得分排序
        sorted_factors = sorted(
            factor_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'top_factors': sorted_factors[:top_n],
            'all_scores': factor_scores
        }
    
    def _calculate_ic_series(self, factor_series: pd.Series, 
                            returns_series: pd.Series) -> pd.Series:
        """
        计算信息系数（IC）序列
        
        Args:
            factor_series: 因子值序列
            returns_series: 收益率序列
            
        Returns:
            IC序列
        """
        # 确保索引对齐
        aligned_data = pd.concat([factor_series, returns_series], axis=1, join='inner')
        aligned_data.columns = ['factor', 'returns']
        
        # 计算Pearson相关系数作为IC（避免依赖scipy）
        # 这里简化处理，直接计算整体相关系数
        # 实际应用中，IC序列应该是按时间滚动计算的相关系数
        ic = aligned_data['factor'].corr(aligned_data['returns'], method='pearson')
        
        # 返回包含单个IC值的序列
        return pd.Series([ic], index=[aligned_data.index[-1]])
    
    def _calculate_factor_turnover(self, factor_series: pd.Series) -> float:
        """
        计算因子换手率
        
        Args:
            factor_series: 因子值序列
            
        Returns:
            换手率值
        """
        # 计算因子值的变化率
        factor_changes = factor_series.diff().dropna().abs()
        avg_turnover = factor_changes.mean() / (factor_series.abs().mean() + 1e-8)
        
        return avg_turnover
    
    def _calculate_decay_rate(self, ic_series: pd.Series) -> float:
        """
        计算IC衰减率
        
        Args:
            ic_series: IC序列
            
        Returns:
            衰减率
        """
        # 使用自相关函数计算衰减率
        max_lag = 10
        autocorrs = []
        
        for lag in range(1, max_lag + 1):
            autocorr = ic_series.autocorr(lag=lag)
            autocorrs.append(autocorr)
        
        if not autocorrs:
            return 0.0
        
        # 拟合指数衰减模型: acf(lag) = exp(-decay_rate * lag)
        lags = np.arange(1, max_lag + 1)
        log_autocorrs = np.log(np.abs(autocorrs) + 1e-8)  # 加小值避免log(0)
        
        # 线性回归
        slope, _ = np.polyfit(lags, log_autocorrs, 1)
        decay_rate = -slope
        
        return max(0.0, decay_rate)  # 确保衰减率非负
    
    def _calculate_regime_stability(self, ic_series: pd.Series, 
                                  regime_series: pd.Series) -> float:
        """
        计算因子在不同市场状态下的稳定性
        
        Args:
            ic_series: IC序列
            regime_series: 市场状态序列
            
        Returns:
            稳定性评分（0-100）
        """
        # 确保索引对齐
        aligned_data = pd.concat([ic_series, regime_series], axis=1, join='inner')
        aligned_data.columns = ['ic', 'regime']
        
        # 计算各市场状态下的IC均值和标准差
        regime_stats = aligned_data.groupby('regime')['ic'].agg(['mean', 'std', 'count'])
        
        if len(regime_stats) < 2:
            return 50.0  # 市场状态不足，返回中等分数
        
        # 计算IC均值的变异系数（越低越稳定）
        ic_means = regime_stats['mean']
        cv = ic_means.std() / (ic_means.abs().mean() + 1e-8)
        
        # 转换为稳定性评分（0-100）
        stability_score = max(0.0, min(100.0, (1 - cv) * 100))
        
        return stability_score
    
    def _normalize_score(self, value: float, min_val: float, max_val: float, 
                        invert: bool = False) -> float:
        """
        将值归一化到0-1范围
        
        Args:
            value: 要归一化的值
            min_val: 最小值
            max_val: 最大值
            invert: 是否反转（值越小得分越高）
            
        Returns:
            归一化后的值（0-1）
        """
        # 限制值在指定范围内
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))
        
        if invert:
            normalized = 1.0 - normalized
        
        return normalized
    
    def _score_to_grade(self, score: float) -> str:
        """
        将分数转换为等级
        
        Args:
            score: 分数（0-100）
            
        Returns:
            等级字符串
        """
        if score >= 90:
            return 'S'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    
    def generate_factor_report(self, factor_name: str, factor_series: pd.Series, 
                              returns_series: pd.Series, 
                              regime_series: pd.Series = None) -> Dict[str, Any]:
        """
        生成因子有效性报告
        
        Args:
            factor_name: 因子名称
            factor_series: 因子值序列
            returns_series: 收益率序列
            regime_series: 市场状态序列（可选）
            
        Returns:
            因子有效性报告
        """
        # 计算因子评分
        score_result = self.score_factor(factor_series, returns_series, regime_series)
        
        # 计算因子收益率分布
        factor_returns = self._calculate_factor_returns(factor_series, returns_series)
        
        # 计算分层回测结果
        quantile_results = self._calculate_quantile_results(factor_series, returns_series)
        
        report = {
            'factor_name': factor_name,
            'score': score_result['score'],
            'grade': score_result['grade'],
            'details': score_result['details'],
            'ic_series': score_result['ic_series'],
            'half_life': score_result['half_life'],
            'turnover': score_result['turnover'],
            'returns_distribution': {
                'mean': factor_returns.mean(),
                'std': factor_returns.std(),
                'skewness': factor_returns.skew(),
                'kurtosis': factor_returns.kurtosis()
            },
            'quantile_results': quantile_results
        }
        
        return report
    
    def _calculate_factor_returns(self, factor_series: pd.Series, 
                                returns_series: pd.Series) -> pd.Series:
        """
        计算因子收益率
        
        Args:
            factor_series: 因子值序列
            returns_series: 收益率序列
            
        Returns:
            因子收益率序列
        """
        # 这里假设因子值越高，预期收益越高
        # 根据因子值排序，买入前10%，卖出后10%
        aligned_data = pd.concat([factor_series, returns_series], axis=1, join='inner')
        aligned_data.columns = ['factor', 'returns']
        
        # 按因子值分组
        aligned_data['factor_rank'] = aligned_data.groupby(level=0)['factor'].rank(pct=True)
        
        # 计算因子组合收益率
        long_group = aligned_data[aligned_data['factor_rank'] > 0.9]
        short_group = aligned_data[aligned_data['factor_rank'] < 0.1]
        
        long_returns = long_group.groupby(level=0)['returns'].mean()
        short_returns = short_group.groupby(level=0)['returns'].mean()
        
        factor_returns = long_returns - short_returns
        
        return factor_returns
    
    def _calculate_quantile_results(self, factor_series: pd.Series, 
                              returns_series: pd.Series, n_groups: int = 5) -> Dict[str, Any]:
        """
        计算分层回测结果
        
        Args:
            factor_series: 因子值序列
            returns_series: 收益率序列
            n_groups: 分组数量
            
        Returns:
            分层回测结果
        """
        aligned_data = pd.concat([factor_series, returns_series], axis=1, join='inner')
        aligned_data.columns = ['factor', 'returns']
        
        # 按因子值分组
        aligned_data['group'] = aligned_data.groupby(level=0)['factor'].transform(
            lambda x: pd.qcut(x, n_groups, labels=False, duplicates='drop')
        )
        
        # 计算每组的平均收益率
        group_returns = aligned_data.groupby(['group', aligned_data.index.get_level_values(0)])['returns'].mean().unstack(level=0)
        
        # 计算累计收益率
        cumulative_returns = (1 + group_returns).cumprod()
        
        # 计算每组的年化收益率和夏普比率
        group_stats = {}
        for group in range(n_groups):
            if group in group_returns.columns:
                group_returns_series = group_returns[group]
                group_stats[group] = {
                    'annual_return': group_returns_series.mean() * 252,
                    'sharpe': (group_returns_series.mean() / group_returns_series.std()) * np.sqrt(252) if group_returns_series.std() != 0 else 0
                }
        
        return {
            'group_returns': group_returns,
            'cumulative_returns': cumulative_returns,
            'group_stats': group_stats
        }
