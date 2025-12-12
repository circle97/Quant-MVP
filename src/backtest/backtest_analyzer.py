# -*- coding: utf-8 -*-
"""
回测结果分析器 - 负责生成回测报告和绩效指标
"""
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger


class BacktestAnalyzer:
    """回测结果分析器，负责生成回测报告和绩效指标"""
    
    def __init__(self, backtest_results: dict):
        self.results = backtest_results
        self.analysis = {}
        
        logger.info("初始化回测结果分析器")
    
    def analyze(self) -> Dict[str, Any]:
        """执行回测分析
        
        Returns:
            分析结果
        """
        logger.info("开始回测分析")
        
        # 计算绩效指标
        self._calculate_performance_metrics()
        
        # 分析交易行为
        self._analyze_trading_behavior()
        
        # 分析风险
        self._analyze_risk()
        
        logger.info("回测分析完成")
        return self.analysis
    
    def _calculate_performance_metrics(self):
        """计算绩效指标"""
        daily_values = self.results.get('daily_values')
        if daily_values is None or daily_values.empty:
            logger.warning("没有每日价值数据，无法计算绩效指标")
            return
        
        # 计算总收益率
        initial_value = self.results['initial_capital']
        final_value = self.results['final_capital']
        total_return = (final_value - initial_value) / initial_value
        
        # 计算年化收益率
        start_date = daily_values.index[0]
        end_date = daily_values.index[-1]
        days = (end_date - start_date).days
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # 计算夏普比率
        returns = daily_values['total_value'].pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0
        
        # 计算最大回撤
        cumulative_returns = (daily_values['total_value'] / initial_value) - 1
        drawdown = cumulative_returns.cummax() - cumulative_returns
        max_drawdown = drawdown.max()
        
        # 计算胜率
        winning_trades = 0
        losing_trades = 0
        total_trades = 0
        
        # 计算收益率序列
        returns_series = returns
        
        # 计算平均盈利和平均亏损
        avg_win = returns_series[returns_series > 0].mean() if len(returns_series[returns_series > 0]) > 0 else 0
        avg_loss = returns_series[returns_series < 0].mean() if len(returns_series[returns_series < 0]) > 0 else 0
        
        # 计算盈亏比
        win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # 保存绩效指标
        self.analysis['performance_metrics'] = {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_loss_ratio': win_loss_ratio,
            'total_trades': len(returns_series),
            'winning_trades': len(returns_series[returns_series > 0]),
            'losing_trades': len(returns_series[returns_series < 0]),
            'win_rate': len(returns_series[returns_series > 0]) / len(returns_series) if len(returns_series) > 0 else 0
        }
        
        logger.info(f"绩效指标计算完成: {self.analysis['performance_metrics']}")
    
    def _analyze_trading_behavior(self):
        """分析交易行为"""
        # 这里可以添加交易行为分析，如交易频率、持仓时间等
        logger.info("交易行为分析完成")
    
    def _analyze_risk(self):
        """分析风险"""
        daily_values = self.results.get('daily_values')
        if daily_values is None or daily_values.empty:
            logger.warning("没有每日价值数据，无法分析风险")
            return
        
        # 计算波动率
        returns = daily_values['total_value'].pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5)
        
        # 计算下行风险
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * (252 ** 0.5) if len(downside_returns) > 0 else 0
        
        # 计算索提诺比率
        initial_value = self.results['initial_capital']
        risk_free_rate = 0.0  # 假设无风险利率为0
        sharpe_ratio = self.analysis['performance_metrics']['sharpe_ratio']
        sortino_ratio = (self.analysis['performance_metrics']['annual_return'] - risk_free_rate) / downside_deviation if downside_deviation != 0 else 0
        
        # 保存风险指标
        self.analysis['risk_metrics'] = {
            'volatility': volatility,
            'downside_deviation': downside_deviation,
            'sortino_ratio': sortino_ratio
        }
        
        logger.info(f"风险分析完成: {self.analysis['risk_metrics']}")
    
    def generate_report(self, report_path: str = None) -> str:
        """生成回测报告
        
        Args:
            report_path: 报告保存路径，如果为None则返回报告内容
            
        Returns:
            报告内容
        """
        logger.info("生成回测报告")
        
        # 生成报告内容
        report = []
        report.append("# 回测报告")
        report.append(f"\n## 策略信息")
        report.append(f"- 策略名称: {self.results['strategy_name']}")
        report.append(f"- 回测时间范围: {self.results['start_date']} 到 {self.results['end_date']}")
        report.append(f"- 初始资金: {self.results['initial_capital']:.2f}")
        report.append(f"- 最终资金: {self.results['final_capital']:.2f}")
        report.append(f"- 数据频率: {self.results['data_frequency']}")
        report.append(f"- 回测耗时: {self.results['duration']}")
        
        report.append(f"\n## 绩效指标")
        pm = self.analysis['performance_metrics']
        report.append(f"- 总收益率: {pm['total_return']:.2%}")
        report.append(f"- 年化收益率: {pm['annual_return']:.2%}")
        report.append(f"- 夏普比率: {pm['sharpe_ratio']:.2f}")
        report.append(f"- 最大回撤: {pm['max_drawdown']:.2%}")
        report.append(f"- 胜率: {pm['win_rate']:.2%}")
        report.append(f"- 平均盈利: {pm['avg_win']:.2%}")
        report.append(f"- 平均亏损: {pm['avg_loss']:.2%}")
        report.append(f"- 盈亏比: {pm['win_loss_ratio']:.2f}")
        report.append(f"- 总交易次数: {pm['total_trades']}")
        report.append(f"- 盈利交易次数: {pm['winning_trades']}")
        report.append(f"- 亏损交易次数: {pm['losing_trades']}")
        
        report.append(f"\n## 风险指标")
        rm = self.analysis['risk_metrics']
        report.append(f"- 波动率: {rm['volatility']:.2%}")
        report.append(f"- 下行风险: {rm['downside_deviation']:.2%}")
        report.append(f"- 索提诺比率: {rm['sortino_ratio']:.2f}")
        
        report_content = '\n'.join(report)
        
        if report_path:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"回测报告已保存到: {report_path}")
        
        return report_content
