# -*- coding: utf-8 -*-
"""
过拟合检测器 - 检测策略是否过拟合的多种方法
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from loguru import logger


class OverfittingDetector:
    """
    检测策略是否过拟合的多种方法
    """
    def __init__(self):
        self.detectors = {
            'train_test_gap': self.detect_train_test_gap,
            'parameter_sensitivity': self.detect_parameter_sensitivity,
            'feature_importance_stability': self.detect_feature_instability
        }
    
    def detect_train_test_gap(self, train_performance: Dict[str, float], 
                             test_performance: Dict[str, float]) -> Dict[str, Any]:
        """
        检测训练集与测试集表现差距
        
        Args:
            train_performance: 训练集表现指标字典
            test_performance: 测试集表现指标字典
            
        Returns:
            检测结果字典，包含是否可疑、差距百分比和评分
        """
        metrics_to_compare = ['sharpe', 'max_drawdown', 'win_rate']
        
        gaps = {}
        for metric in metrics_to_compare:
            train_val = train_performance.get(metric, 0)
            test_val = test_performance.get(metric, 0)
            
            if train_val != 0:
                gap_pct = abs(train_val - test_val) / abs(train_val)
                gaps[metric] = gap_pct
        
        # 如果有任一指标差距超过50%，标记为可疑
        is_suspicious = any(gap > 0.5 for gap in gaps.values())
        
        return {
            'is_suspicious': is_suspicious,
            'gaps': gaps,
            'score': 100 * (1 - max(gaps.values()) if gaps else 1)
        }
    
    def detect_parameter_sensitivity(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检测参数敏感性
        
        Args:
            strategy: 策略实例
            data: 测试数据
            
        Returns:
            检测结果字典，包含敏感性指标和评分
        """
        # 获取策略的关键参数
        key_params = self._get_key_params(strategy)
        if not key_params:
            return {
                'is_suspicious': False,
                'sensitivity': 0.0,
                'score': 100.0
            }
        
        sensitivity_results = {}
        base_performance = self._evaluate_strategy(strategy, data)
        
        for param_name, param_value in key_params.items():
            # 尝试调整参数（上下波动10%）
            original_value = param_value
            adjustments = [0.9 * original_value, 1.1 * original_value]
            
            param_performances = []
            for adjusted_value in adjustments:
                # 创建策略副本并调整参数
                adjusted_strategy = self._copy_and_adjust_strategy(
                    strategy, {param_name: adjusted_value}
                )
                
                # 评估调整后的策略
                performance = self._evaluate_strategy(adjusted_strategy, data)
                param_performances.append(performance)
            
            # 计算参数敏感性（表现变化幅度）
            if 'sharpe' in base_performance:
                base_sharpe = base_performance['sharpe']
                sharpe_changes = []
                for perf in param_performances:
                    if 'sharpe' in perf and base_sharpe != 0:
                        change = abs(perf['sharpe'] - base_sharpe) / abs(base_sharpe)
                        sharpe_changes.append(change)
                
                if sharpe_changes:
                    sensitivity_results[param_name] = {
                        'base_sharpe': base_sharpe,
                        'adjusted_sharpes': [p.get('sharpe', 0) for p in param_performances],
                        'sensitivity': np.mean(sharpe_changes)
                    }
        
        # 计算综合敏感性
        if sensitivity_results:
            avg_sensitivity = np.mean([r['sensitivity'] for r in sensitivity_results.values()])
            is_suspicious = avg_sensitivity > 0.3  # 如果平均敏感性超过30%，标记为可疑
        else:
            avg_sensitivity = 0.0
            is_suspicious = False
        
        return {
            'is_suspicious': is_suspicious,
            'sensitivity_results': sensitivity_results,
            'average_sensitivity': avg_sensitivity,
            'score': 100 * (1 - avg_sensitivity)
        }
    
    def detect_feature_instability(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检测特征重要性稳定性
        
        Args:
            strategy: 策略实例
            data: 测试数据
            
        Returns:
            检测结果字典，包含特征稳定性指标和评分
        """
        # 这里假设策略使用了机器学习模型，具有feature_importances_属性
        # 对于非机器学习策略，可以跳过此检测
        if not hasattr(strategy, 'model') or not hasattr(strategy.model, 'feature_importances_'):
            return {
                'is_suspicious': False,
                'stability_score': 1.0,
                'score': 100.0
            }
        
        # 使用不同数据子集计算特征重要性
        n_splits = 5
        feature_importances = []
        
        for i in range(n_splits):
            # 随机选择80%的数据
            sample_data = data.sample(frac=0.8, replace=True)
            
            # 重新训练模型
            sampled_strategy = self._copy_and_retrain(strategy, sample_data)
            if hasattr(sampled_strategy.model, 'feature_importances_'):
                feature_importances.append(sampled_strategy.model.feature_importances_)
        
        if len(feature_importances) < 2:
            return {
                'is_suspicious': False,
                'stability_score': 1.0,
                'score': 100.0
            }
        
        # 计算特征重要性的标准差
        feature_importances = np.array(feature_importances)
        std_per_feature = np.std(feature_importances, axis=0)
        mean_per_feature = np.mean(feature_importances, axis=0)
        
        # 计算变异系数
        cv_per_feature = np.where(mean_per_feature != 0, std_per_feature / mean_per_feature, 0)
        avg_cv = np.mean(cv_per_feature)
        
        is_suspicious = avg_cv > 0.5  # 如果平均变异系数超过50%，标记为可疑
        
        return {
            'is_suspicious': is_suspicious,
            'feature_cv': cv_per_feature.tolist(),
            'average_cv': float(avg_cv),
            'score': 100 * (1 - avg_cv if avg_cv <= 1.0 else 0)
        }
    
    def generate_overfitting_report(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成完整的过拟合检测报告
        
        Args:
            strategy: 策略实例
            data: 用于检测的数据
            
        Returns:
            完整的过拟合检测报告
        """
        report = {}
        
        # 分割数据为训练集和测试集
        train_data, test_data = self._split_data(data)
        
        # 训练和测试策略
        train_strategy = self._copy_and_retrain(strategy, train_data)
        train_performance = self._evaluate_strategy(train_strategy, train_data)
        test_performance = self._evaluate_strategy(train_strategy, test_data)
        
        # 执行所有检测方法
        report['train_test_gap'] = self.detect_train_test_gap(
            train_performance, test_performance
        )
        
        report['parameter_sensitivity'] = self.detect_parameter_sensitivity(
            train_strategy, test_data
        )
        
        report['feature_stability'] = self.detect_feature_instability(
            train_strategy, test_data
        )
        
        # 计算综合过拟合风险评分
        overall_risk = self._calculate_overall_risk(report)
        
        report['overall'] = {
            'risk_score': overall_risk,
            'risk_level': self._risk_level(overall_risk),
            'recommendations': self._generate_recommendations(report)
        }
        
        return report
    
    def _calculate_overall_risk(self, report: Dict[str, Any]) -> float:
        """
        计算综合过拟合风险
        
        Args:
            report: 各检测方法的结果报告
            
        Returns:
            综合风险评分（0-100，越高风险越大）
        """
        weights = {
            'train_test_gap': 0.5,
            'parameter_sensitivity': 0.3,
            'feature_stability': 0.2
        }
        
        weighted_risk = 0.0
        for section_name, section_result in report.items():
            if section_name in weights:
                # 转换为风险评分（100 - 原评分）
                risk_score = 100 - section_result['score']
                weighted_risk += risk_score * weights[section_name]
        
        return weighted_risk
    
    def _risk_level(self, risk_score: float) -> str:
        """
        根据风险评分确定风险等级
        
        Args:
            risk_score: 风险评分
            
        Returns:
            风险等级字符串
        """
        if risk_score < 20:
            return '低风险'
        elif risk_score < 50:
            return '中等风险'
        elif risk_score < 80:
            return '高风险'
        else:
            return '极高风险'
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """
        根据检测报告生成改进建议
        
        Args:
            report: 过拟合检测报告
            
        Returns:
            建议列表
        """
        recommendations = []
        
        if report['train_test_gap']['is_suspicious']:
            recommendations.append('训练集与测试集表现差距较大，建议增加测试集数据量或使用更严格的验证方法')
        
        if report['parameter_sensitivity']['is_suspicious']:
            recommendations.append('策略对参数敏感，建议降低参数复杂度或使用正则化方法')
        
        if report['feature_stability']['is_suspicious']:
            recommendations.append('特征重要性不稳定，建议减少特征数量或使用更稳定的特征选择方法')
        
        if not recommendations:
            recommendations.append('未发现明显过拟合风险，建议继续监控策略在新数据上的表现')
        
        return recommendations
    
    def _split_data(self, data: pd.DataFrame) -> tuple:
        """分割数据为训练集和测试集"""
        split_idx = int(len(data) * 0.7)
        return data.iloc[:split_idx], data.iloc[split_idx:]
    
    def _get_key_params(self, strategy) -> Dict[str, Any]:
        """获取策略的关键参数"""
        # 这里需要根据实际策略的实现来获取参数
        # 暂时返回一个模拟的参数列表
        return getattr(strategy, 'params', {})
    
    def _copy_and_adjust_strategy(self, strategy, params: Dict[str, Any]):
        """复制策略并调整参数"""
        # 这里需要根据实际策略的实现来复制和调整参数
        # 暂时返回原策略
        return strategy
    
    def _copy_and_retrain(self, strategy, data: pd.DataFrame):
        """复制策略并重新训练"""
        # 这里需要根据实际策略的实现来复制和重新训练
        # 暂时返回原策略
        return strategy
    
    def _evaluate_strategy(self, strategy, data: pd.DataFrame) -> Dict[str, float]:
        """评估策略表现"""
        # 这里需要根据实际策略的实现来评估表现
        # 暂时返回模拟结果
        return {
            'sharpe': np.random.normal(1.0, 0.5),
            'max_drawdown': np.random.uniform(0.05, 0.2),
            'annual_return': np.random.uniform(0.05, 0.3),
            'win_rate': np.random.uniform(0.4, 0.6)
        }
