# -*- coding: utf-8 -*-
"""
稳健性评分系统 - 对策略进行评分，评估其稳健性
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from loguru import logger


class RobustnessScorer:
    """
    策略稳健性评分系统
    对策略进行多维度评分，评估其稳健性
    """
    
    def __init__(self):
        # 评分指标权重配置
        self.metrics_weights = {
            'return': 0.2,
            'risk': 0.25,
            'consistency': 0.3,
            'adaptability': 0.15,
            'simplicity': 0.1
        }
        
        # 评分等级配置
        self.grade_thresholds = {
            'S': 90,
            'A': 80,
            'B': 70,
            'C': 60,
            'D': 50,
            'F': 0
        }
    
    def score_strategy(self, strategy, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        对策略进行综合评分
        
        Args:
            strategy: 策略实例
            validation_results: 验证流水线的结果
            
        Returns:
            包含综合评分和各维度评分的结果字典
        """
        # 计算各维度评分
        return_score = self._calculate_return_score(validation_results)
        risk_score = self._calculate_risk_score(validation_results)
        consistency_score = self._calculate_consistency_score(validation_results)
        adaptability_score = self._calculate_adaptability_score(validation_results)
        simplicity_score = self._calculate_simplicity_score(strategy)
        
        # 计算综合评分
        scores = {
            'return': return_score,
            'risk': risk_score,
            'consistency': consistency_score,
            'adaptability': adaptability_score,
            'simplicity': simplicity_score
        }
        
        weighted_score = 0.0
        for metric, weight in self.metrics_weights.items():
            weighted_score += scores[metric] * weight
        
        # 确定评分等级
        grade = self._get_grade(weighted_score)
        
        return {
            'overall_score': weighted_score,
            'grade': grade,
            'dimension_scores': scores,
            'metrics_weights': self.metrics_weights,
            'validation_results': validation_results
        }
    
    def _calculate_return_score(self, validation_results: Dict[str, Any]) -> float:
        """
        计算收益评分
        
        Args:
            validation_results: 验证流水线的结果
            
        Returns:
            收益评分（0-100）
        """
        # 从验证结果中提取收益相关指标
        sharpe_values = []
        
        # 基础结果
        if 'base' in validation_results and hasattr(validation_results['base'], 'sharpe'):
            sharpe_values.append(validation_results['base'].sharpe)
        
        # 前向遍历结果
        if 'walk_forward' in validation_results:
            walk_forward_results = validation_results['walk_forward'].get('results', [])
            for result in walk_forward_results:
                if hasattr(result, 'sharpe'):
                    sharpe_values.append(result.sharpe)
        
        if not sharpe_values:
            return 50.0
        
        # 计算平均夏普比率
        avg_sharpe = np.mean(sharpe_values)
        
        # 将夏普比率映射到0-100分
        # 假设夏普比率的合理范围是-1到3
        min_sharpe = -1.0
        max_sharpe = 3.0
        
        normalized_score = (avg_sharpe - min_sharpe) / (max_sharpe - min_sharpe) * 100
        
        return max(0.0, min(100.0, normalized_score))
    
    def _calculate_risk_score(self, validation_results: Dict[str, Any]) -> float:
        """
        计算风险评分
        
        Args:
            validation_results: 验证流水线的结果
            
        Returns:
            风险评分（0-100）
        """
        # 从验证结果中提取风险相关指标
        drawdown_values = []
        
        # 基础结果
        if 'base' in validation_results and hasattr(validation_results['base'], 'max_drawdown'):
            drawdown_values.append(validation_results['base'].max_drawdown)
        
        # 前向遍历结果
        if 'walk_forward' in validation_results:
            walk_forward_results = validation_results['walk_forward'].get('results', [])
            for result in walk_forward_results:
                if hasattr(result, 'max_drawdown'):
                    drawdown_values.append(result.max_drawdown)
        
        if not drawdown_values:
            return 50.0
        
        # 计算平均最大回撤
        avg_drawdown = np.mean(drawdown_values)
        
        # 将最大回撤映射到0-100分（越小越好）
        # 假设最大回撤的合理范围是0到0.5
        min_drawdown = 0.0
        max_drawdown = 0.5
        
        normalized_score = (max_drawdown - avg_drawdown) / (max_drawdown - min_drawdown) * 100
        
        return max(0.0, min(100.0, normalized_score))
    
    def _calculate_consistency_score(self, validation_results: Dict[str, Any]) -> float:
        """
        计算一致性评分
        
        Args:
            validation_results: 验证流水线的结果
            
        Returns:
            一致性评分（0-100）
        """
        # 从验证结果中提取表现一致性指标
        sharpe_values = []
        
        # 前向遍历结果
        if 'walk_forward' in validation_results:
            walk_forward_results = validation_results['walk_forward'].get('results', [])
            for result in walk_forward_results:
                if hasattr(result, 'sharpe'):
                    sharpe_values.append(result.sharpe)
        
        # 蒙特卡洛结果
        if 'monte_carlo' in validation_results:
            mc_results = validation_results['monte_carlo'].get('results', [])
            for result in mc_results:
                if hasattr(result, 'sharpe'):
                    sharpe_values.append(result.sharpe)
        
        if len(sharpe_values) < 2:
            return 50.0
        
        # 计算夏普比率的变异系数（越低越好）
        mean_sharpe = np.mean(sharpe_values)
        std_sharpe = np.std(sharpe_values)
        
        if mean_sharpe == 0:
            return 50.0
        
        cv = std_sharpe / abs(mean_sharpe)
        
        # 将变异系数映射到0-100分
        # 假设变异系数的合理范围是0到2
        min_cv = 0.0
        max_cv = 2.0
        
        normalized_score = (max_cv - cv) / (max_cv - min_cv) * 100
        
        return max(0.0, min(100.0, normalized_score))
    
    def _calculate_adaptability_score(self, validation_results: Dict[str, Any]) -> float:
        """
        计算适应性评分
        
        Args:
            validation_results: 验证流水线的结果
            
        Returns:
            适应性评分（0-100）
        """
        # 从市场状态感知验证结果中提取适应性指标
        if 'regime_aware' not in validation_results:
            return 50.0
        
        regime_results = validation_results['regime_aware'].get('results', {})
        if not regime_results:
            return 50.0
        
        # 计算在不同市场状态下的表现
        positive_regimes = 0
        total_regimes = len(regime_results)
        
        for regime_result in regime_results.values():
            if hasattr(regime_result, 'sharpe') and regime_result.sharpe > 0:
                positive_regimes += 1
        
        # 计算适应性评分
        adaptability_score = (positive_regimes / total_regimes) * 100
        
        return adaptability_score
    
    def _calculate_simplicity_score(self, strategy) -> float:
        """
        计算简单性评分
        
        Args:
            strategy: 策略实例
            
        Returns:
            简单性评分（0-100）
        """
        # 基于策略的参数数量和复杂度来评估简单性
        # 参数越少，策略越简单，评分越高
        params = getattr(strategy, 'params', {})
        param_count = len(params)
        
        # 假设参数数量的合理范围是0到10
        min_params = 0
        max_params = 10
        
        normalized_score = (max_params - param_count) / (max_params - min_params) * 100
        
        return max(0.0, min(100.0, normalized_score))
    
    def _get_grade(self, score: float) -> str:
        """
        根据分数确定等级
        
        Args:
            score: 分数（0-100）
            
        Returns:
            等级字符串（S, A, B, C, D, F）
        """
        for grade, threshold in sorted(self.grade_thresholds.items(), key=lambda x: -x[1]):
            if score >= threshold:
                return grade
        return 'F'
    
    def generate_score_report(self, score_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成评分报告
        
        Args:
            score_results: 评分结果
            
        Returns:
            格式化的评分报告
        """
        # 生成策略基本信息
        strategy_info = {
            'name': getattr(score_results.get('strategy', {}), 'name', 'Unknown'),
            'type': strategy.__class__.__name__,
            'params': getattr(strategy, 'params', {})
        }
        
        # 生成评分详情
        report = {
            'strategy_info': strategy_info,
            'overall_score': score_results['overall_score'],
            'grade': score_results['grade'],
            'dimension_scores': score_results['dimension_scores'],
            'metrics_weights': score_results['metrics_weights'],
            'grade_explanation': self._get_grade_explanation(score_results['grade']),
            'recommendations': self._generate_score_recommendations(score_results)
        }
        
        return report
    
    def _get_grade_explanation(self, grade: str) -> str:
        """
        获取评分等级的解释
        
        Args:
            grade: 评分等级
            
        Returns:
            等级解释字符串
        """
        explanations = {
            'S': '优秀：策略表现出色，各维度均表现良好，具有很高的稳健性',
            'A': '良好：策略表现较好，核心维度表现优秀，具有较强的稳健性',
            'B': '合格：策略表现基本符合要求，具有一定的稳健性',
            'C': '一般：策略表现一般，存在一些问题，需要改进',
            'D': '较差：策略表现较差，存在明显问题，需要大幅改进',
            'F': '不合格：策略表现极差，不建议使用'
        }
        
        return explanations.get(grade, '未知等级')
    
    def _generate_score_recommendations(self, score_results: Dict[str, Any]) -> List[str]:
        """
        基于评分结果生成改进建议
        
        Args:
            score_results: 评分结果
            
        Returns:
            改进建议列表
        """
        recommendations = []
        dimension_scores = score_results['dimension_scores']
        
        # 针对各维度评分较低的情况生成建议
        if dimension_scores['return'] < 70:
            recommendations.append('收益表现一般，建议优化策略的收益生成逻辑，或调整风险敞口')
        
        if dimension_scores['risk'] < 70:
            recommendations.append('风险控制不足，建议加强止损机制，或调整仓位管理策略')
        
        if dimension_scores['consistency'] < 70:
            recommendations.append('表现一致性较差，建议优化策略参数，或增加验证样本')
        
        if dimension_scores['adaptability'] < 70:
            recommendations.append('市场适应性不足，建议增加市场状态识别，或设计自适应机制')
        
        if dimension_scores['simplicity'] < 70:
            recommendations.append('策略过于复杂，建议简化策略逻辑，减少参数数量')
        
        # 综合建议
        if score_results['overall_score'] >= 80:
            recommendations.append('策略表现优秀，建议进行实盘模拟测试')
        elif score_results['overall_score'] >= 60:
            recommendations.append('策略表现合格，建议进一步优化后进行实盘模拟测试')
        else:
            recommendations.append('策略表现较差，建议重新设计或大幅改进')
        
        return recommendations
