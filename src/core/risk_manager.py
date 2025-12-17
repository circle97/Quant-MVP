# -*- coding: utf-8 -*-
"""
风险控制模块 - 负责监控和管理交易过程中的各种风险
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import time
from threading import Thread
from loguru import logger

from .event import Event, EventType, SignalEvent, OrderEvent, FillEvent, RiskEvent, ExceptionEvent, StrategyEvent, event_engine
from .order import Order, OrderStatus, OrderDirection


class RiskRule(ABC):
    """风险规则抽象基类"""
    
    def __init__(self, name: str, params: dict, enabled: bool = True):
        """
        初始化风险规则
        
        Args:
            name: 规则名称
            params: 规则参数
            enabled: 是否启用
        """
        self.name = name
        self.params = params
        self.enabled = enabled
        self.violations = []
    
    @abstractmethod
    def check(self, context: dict) -> bool:
        """
        检查是否违反规则
        
        Args:
            context: 检查上下文，包含订单、账户、策略等信息
            
        Returns:
            bool: 是否违反规则，True表示违反，False表示通过
        """
        pass
    
    def get_violation_message(self) -> str:
        """
        获取违规信息
        
        Returns:
            str: 违规信息
        """
        if not self.violations:
            return ""
        return "; ".join(self.violations)
    
    def enable(self):
        """启用规则"""
        self.enabled = True
    
    def disable(self):
        """禁用规则"""
        self.enabled = False


class PositionLimitRule(RiskRule):
    """仓位限制规则"""
    
    def __init__(self, name: str, params: dict, enabled: bool = True):
        """
        初始化仓位限制规则
        
        Args:
            name: 规则名称
            params: 规则参数，包含:
                max_position_percent: 单只股票最大持仓比例
                max_total_position: 总持仓比例上限
                max_industry_exposure: 单一行业最大暴露度
            enabled: 是否启用
        """
        super().__init__(name, params, enabled)
    
    def check(self, context: dict) -> bool:
        """检查仓位限制"""
        portfolio = context.get("portfolio")
        order = context.get("order")
        
        if not portfolio or not order:
            return False
        
        self.violations = []
        
        # 计算交易后的仓位
        expected_position = self._estimate_position_after_trade(portfolio, order)
        
        # 检查单只股票最大持仓比例
        max_position_percent = self.params.get("max_position_percent", 0.2)
        symbol_position_value = expected_position.get(order.symbol, 0)
        total_value = portfolio.total_value
        
        if total_value > 0 and symbol_position_value / total_value > max_position_percent:
            self.violations.append(f"单只股票持仓比例超过限制: {symbol_position_value/total_value:.2%} > {max_position_percent:.2%}")
        
        # 检查总持仓比例
        max_total_position = self.params.get("max_total_position", 1.0)
        total_position_value = sum(expected_position.values())
        
        if total_value > 0 and total_position_value / total_value > max_total_position:
            self.violations.append(f"总持仓比例超过限制: {total_position_value/total_value:.2%} > {max_total_position:.2%}")
        
        return len(self.violations) > 0
    
    def _estimate_position_after_trade(self, portfolio, order) -> Dict[str, float]:
        """估计交易后的仓位"""
        # 初始化估计仓位为当前仓位
        estimated = {}
        for symbol, position in portfolio.positions.items():
            estimated[symbol] = position.market_value
        
        # 计算交易金额
        order_amount = order.quantity * (order.price or 0)
        
        # 根据订单方向调整估计仓位
        if order.direction == OrderDirection.BUY:
            estimated[order.symbol] = estimated.get(order.symbol, 0) + order_amount
        elif order.direction == OrderDirection.SELL:
            estimated[order.symbol] = estimated.get(order.symbol, 0) - order_amount
        
        return estimated


class StopLossTakeProfitRule(RiskRule):
    """止损止盈规则"""
    
    def __init__(self, name: str, params: dict, enabled: bool = True):
        """
        初始化止损止盈规则
        
        Args:
            name: 规则名称
            params: 规则参数，包含:
                stop_loss_ratio: 止损比例
                take_profit_ratio: 止盈比例
            enabled: 是否启用
        """
        super().__init__(name, params, enabled)
    
    def check(self, context: dict) -> bool:
        """检查止损止盈"""
        portfolio = context.get("portfolio")
        order = context.get("order")
        
        if not portfolio or not order:
            return False
        
        self.violations = []
        
        # 获取当前持仓
        position = portfolio.get_position(order.symbol)
        if not position:
            return False
        
        # 计算当前盈亏比例
        current_price = context.get("current_price", position.current_price)
        pnl_ratio = (current_price - position.avg_price) / position.avg_price
        
        # 检查止损
        stop_loss_ratio = self.params.get("stop_loss_ratio", -0.08)
        if pnl_ratio < stop_loss_ratio:
            self.violations.append(f"触发止损: 盈亏比例 {pnl_ratio:.2%} < {stop_loss_ratio:.2%}")
        
        # 检查止盈
        take_profit_ratio = self.params.get("take_profit_ratio", 0.15)
        if pnl_ratio > take_profit_ratio:
            self.violations.append(f"触发止盈: 盈亏比例 {pnl_ratio:.2%} > {take_profit_ratio:.2%}")
        
        return len(self.violations) > 0


class OrderAmountLimitRule(RiskRule):
    """订单金额限制规则"""
    
    def __init__(self, name: str, params: dict, enabled: bool = True):
        """
        初始化订单金额限制规则
        
        Args:
            name: 规则名称
            params: 规则参数，包含:
                max_single_order_amount: 单笔订单最大金额
                max_daily_order_amount: 单日累计最大金额
            enabled: 是否启用
        """
        super().__init__(name, params, enabled)
        self.daily_order_amount = 0
        self.last_reset_date = datetime.now().date()
    
    def check(self, context: dict) -> bool:
        """检查订单金额限制"""
        order = context.get("order")
        
        if not order:
            return False
        
        self.violations = []
        
        # 重置每日累计金额
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_order_amount = 0
            self.last_reset_date = today
        
        # 计算订单金额
        order_amount = order.quantity * (order.price or context.get("current_price", 0))
        
        # 检查单笔订单最大金额
        max_single_order_amount = self.params.get("max_single_order_amount", 10000)
        if order_amount > max_single_order_amount:
            self.violations.append(f"单笔订单金额超过限制: {order_amount:.2f} > {max_single_order_amount:.2f}")
        
        # 检查单日累计最大金额
        max_daily_order_amount = self.params.get("max_daily_order_amount", 50000)
        if self.daily_order_amount + order_amount > max_daily_order_amount:
            self.violations.append(f"单日累计订单金额超过限制: {self.daily_order_amount + order_amount:.2f} > {max_daily_order_amount:.2f}")
        
        return len(self.violations) > 0
    
    def update_daily_amount(self, order_amount: float):
        """更新每日累计金额"""
        self.daily_order_amount += order_amount


class RiskMetricsCalculator:
    """风险指标计算器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.rolling_window = config.get("rolling_window", 252)  # 默认使用252个交易日
    
    def calculate_volatility(self, returns: pd.Series, annualize: bool = True) -> float:
        """
        计算波动率
        
        Args:
            returns: 收益率序列
            annualize: 是否年化
            
        Returns:
            float: 波动率
        """
        if returns.empty:
            return 0.0
        
        volatility = returns.std()
        if annualize:
            volatility *= np.sqrt(self.rolling_window)
        return volatility
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95, method: str = "historical") -> float:
        """
        计算VaR (Value at Risk)
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            method: 计算方法 (historical, parametric, monte_carlo)
            
        Returns:
            float: VaR值
        """
        if returns.empty:
            return 0.0
        
        if method == "historical":
            # 历史模拟法
            var = np.percentile(returns, (1 - confidence_level) * 100)
        elif method == "parametric":
            # 参数法（假设收益率服从正态分布）
            mean = returns.mean()
            std = returns.std()
            from scipy.stats import norm
            z_score = norm.ppf(1 - confidence_level)
            var = mean + z_score * std
        elif method == "monte_carlo":
            # 蒙特卡洛模拟法
            # 简化实现，使用历史模拟法结果
            var = np.percentile(returns, (1 - confidence_level) * 100)
        else:
            raise ValueError(f"不支持的VaR计算方法: {method}")
        
        return var
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率
            
        Returns:
            float: 夏普比率
        """
        if returns.empty:
            return 0.0
        
        excess_returns = returns - risk_free_rate / self.rolling_window
        if excess_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(self.rolling_window)
    
    def calculate_max_drawdown(self, portfolio_values: pd.Series) -> float:
        """
        计算最大回撤
        
        Args:
            portfolio_values:  portfolio价值序列
            
        Returns:
            float: 最大回撤
        """
        if portfolio_values.empty:
            return 0.0
        
        cumulative_max = portfolio_values.cummax()
        drawdown = (portfolio_values - cumulative_max) / cumulative_max
        return drawdown.min() if not drawdown.empty else 0.0
    
    def calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """
        计算卡玛比率
        
        Args:
            returns: 收益率序列
            
        Returns:
            float: 卡玛比率
        """
        if returns.empty:
            return 0.0
        
        annual_return = returns.mean() * self.rolling_window
        max_drawdown = self.calculate_max_drawdown(pd.Series(returns.cumsum()))
        return annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    def calculate_all_metrics(self, portfolio) -> dict:
        """
        计算所有风险指标
        
        Args:
            portfolio: 投资组合对象
            
        Returns:
            dict: 包含所有风险指标的字典
        """
        # 获取收益率序列和组合价值序列
        returns = self._get_returns(portfolio)
        portfolio_values = self._get_portfolio_values(portfolio)
        
        metrics = {
            "volatility": self.calculate_volatility(returns),
            "var_95": self.calculate_var(returns, confidence_level=0.95),
            "var_99": self.calculate_var(returns, confidence_level=0.99),
            "sharpe_ratio": self.calculate_sharpe_ratio(returns),
            "max_drawdown": self.calculate_max_drawdown(portfolio_values),
            "calmar_ratio": self.calculate_calmar_ratio(returns),
            "total_return": (portfolio.total_value / portfolio.initial_capital - 1) * 100,
            "annual_return": returns.mean() * self.rolling_window * 100 if not returns.empty else 0
        }
        
        return metrics
    
    def _get_returns(self, portfolio) -> pd.Series:
        """获取收益率序列"""
        if not portfolio.daily_values:
            return pd.Series()
        
        values = [record["total_value"] for record in portfolio.daily_values]
        returns = pd.Series(values).pct_change().dropna()
        return returns
    
    def _get_portfolio_values(self, portfolio) -> pd.Series:
        """获取投资组合价值序列"""
        if not portfolio.daily_values:
            return pd.Series()
        
        return pd.Series([record["total_value"] for record in portfolio.daily_values])


class RuleEngine:
    """规则引擎，执行风险规则"""
    
    def __init__(self):
        self.rules = []
    
    def add_rule(self, rule: RiskRule):
        """添加风险规则"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """移除风险规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def get_rule(self, rule_name: str) -> Optional[RiskRule]:
        """获取风险规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def check_rules(self, context: dict) -> List[RiskRule]:
        """
        检查所有风险规则
        
        Args:
            context: 检查上下文
            
        Returns:
            List[RiskRule]: 违反的规则列表
        """
        violated_rules = []
        
        for rule in self.rules:
            if rule.enabled and rule.check(context):
                violated_rules.append(rule)
        
        return violated_rules
    
    def enable_rule(self, rule_name: str):
        """启用风险规则"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.enable()
    
    def disable_rule(self, rule_name: str):
        """禁用风险规则"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.disable()


class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self, config: dict, risk_manager):
        self.config = config
        self.risk_manager = risk_manager
        self.retry_count = config.get("retry_count", 3)
        self.retry_delay = config.get("retry_delay", 5)  # 重试延迟（秒）
    
    def handle_exception(self, exception: Exception, context: dict) -> bool:
        """
        处理异常
        
        Args:
            exception: 异常对象
            context: 异常上下文
            
        Returns:
            bool: 是否成功处理异常
        """
        exception_type = type(exception).__name__
        
        logger.error(f"处理异常: {exception_type}, 上下文: {context}, 异常信息: {str(exception)}")
        
        # 根据异常类型执行不同的处理逻辑
        if exception_type == "NetworkError":
            return self._handle_network_error(exception, context)
        elif exception_type == "APIError":
            return self._handle_api_error(exception, context)
        elif exception_type == "DataError":
            return self._handle_data_error(exception, context)
        elif exception_type == "OrderRejectedError":
            return self._handle_order_rejected_error(exception, context)
        else:
            return self._handle_generic_error(exception, context)
    
    def _handle_network_error(self, exception: Exception, context: dict) -> bool:
        """处理网络异常"""
        # 实现网络异常处理逻辑
        # 例如：重试请求、切换备用API等
        retry_count = context.get("retry_count", 0)
        
        if retry_count < self.retry_count:
            logger.info(f"网络异常，将在 {self.retry_delay} 秒后重试，重试次数: {retry_count + 1}/{self.retry_count}")
            time.sleep(self.retry_delay)
            context["retry_count"] = retry_count + 1
            return False  # 表示需要重试
        else:
            logger.error("网络异常重试次数超过限制，暂停相关策略")
            self.risk_manager.pause_strategy(context.get("strategy_name"))
            return True  # 表示已处理
    
    def _handle_api_error(self, exception: Exception, context: dict) -> bool:
        """处理API异常"""
        # 实现API异常处理逻辑
        # 例如：检查API错误码、调整请求频率等
        return True
    
    def _handle_data_error(self, exception: Exception, context: dict) -> bool:
        """处理数据异常"""
        # 实现数据异常处理逻辑
        # 例如：使用备用数据源、跳过异常数据等
        return True
    
    def _handle_order_rejected_error(self, exception: Exception, context: dict) -> bool:
        """处理订单拒绝异常"""
        # 实现订单拒绝异常处理逻辑
        # 例如：记录日志、调整订单参数等
        return True
    
    def _handle_generic_error(self, exception: Exception, context: dict) -> bool:
        """处理通用异常"""
        # 实现通用异常处理逻辑
        # 例如：记录日志、通知管理员等
        return True


class RiskMonitor:
    """风险监控器"""
    
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
        self.config = risk_manager.config.get("monitor", {})
        self.metrics_thresholds = self.config.get("metrics_thresholds", {})
        
        # 启动监控线程
        self.monitor_thread = Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.running = False
    
    def start(self):
        """启动监控"""
        if not self.running:
            self.running = True
            self.monitor_thread.start()
    
    def stop(self):
        """停止监控"""
        self.running = False
    
    def _monitor_loop(self):
        """监控循环"""
        monitor_interval = self.config.get("interval", 60)  # 默认60秒监控一次
        
        while self.running:
            try:
                self._check_risk_metrics()
                self._check_system_status()
            except Exception as e:
                logger.error(f"风险监控异常: {str(e)}")
            
            time.sleep(monitor_interval)
    
    def _check_risk_metrics(self):
        """检查风险指标"""
        # 获取所有策略的投资组合
        portfolios = self._get_all_portfolios()
        
        for strategy_name, portfolio in portfolios.items():
            # 计算风险指标
            metrics = self.risk_manager.calculate_risk_metrics(portfolio)
            
            # 检查风险指标是否超过阈值
            for metric_name, value in metrics.items():
                threshold = self.metrics_thresholds.get(metric_name)
                if threshold:
                    if isinstance(threshold, dict):
                        # 阈值是一个范围
                        min_val = threshold.get("min")
                        max_val = threshold.get("max")
                        
                        if min_val is not None and value < min_val:
                            self._handle_metric_breach(strategy_name, metric_name, value, min_val, max_val)
                        if max_val is not None and value > max_val:
                            self._handle_metric_breach(strategy_name, metric_name, value, min_val, max_val)
                    else:
                        # 阈值是一个单一值
                        if value > threshold:
                            self._handle_metric_breach(strategy_name, metric_name, value, None, threshold)
    
    def _check_system_status(self):
        """检查系统状态"""
        # 实现系统状态检查逻辑
        # 例如：检查CPU使用率、内存使用率、磁盘空间等
        pass
    
    def _handle_metric_breach(self, strategy_name: str, metric_name: str, value: float, min_val: float, max_val: float):
        """
        处理风险指标突破阈值
        
        Args:
            strategy_name: 策略名称
            metric_name: 指标名称
            value: 指标值
            min_val: 最小阈值
            max_val: 最大阈值
        """
        logger.warning(f"策略 {strategy_name} 的风险指标 {metric_name} 突破阈值: {value}, 阈值范围: [{min_val}, {max_val}]")
        
        # 触发风险事件
        self.risk_manager.event_engine.put(RiskEvent(
            event_type="METRIC_BREACH",
            strategy_name=strategy_name,
            metric_name=metric_name,
            metric_value=value,
            min_threshold=min_val,
            max_threshold=max_val
        ))
        
        # 根据指标重要性决定是否暂停策略
        if metric_name in ["var_99", "max_drawdown"]:
            self.risk_manager.pause_strategy(strategy_name)
    
    def _get_all_portfolios(self) -> Dict[str, object]:
        """获取所有策略的投资组合"""
        # 实现获取所有投资组合的逻辑
        # 这里简化实现，返回空字典
        return {}


class RiskManager:
    """风险管理器核心"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.rule_engine = RuleEngine()
        self.metrics_calculator = RiskMetricsCalculator(self.config.get("metrics", {}))
        self.exception_handler = ExceptionHandler(self.config.get("exception", {}), self)
        self.risk_monitor = RiskMonitor(self)
        
        # 初始化风险规则
        self._init_rules()
        
        # 事件引擎
        self.event_engine = event_engine
        
        # 注册事件处理器
        self._register_event_handlers()
        
        # 风险状态
        self.paused_strategies = set()
        self.global_pause = False
        
        logger.info("初始化风险管理器")
    
    def _init_rules(self):
        """初始化风险规则"""
        rules_config = self.config.get("rules", {})
        
        # 添加仓位限制规则
        if "position_limit" in rules_config:
            self.rule_engine.add_rule(
                PositionLimitRule("position_limit", rules_config["position_limit"])
            )
        
        # 添加止损止盈规则
        if "stop_loss_take_profit" in rules_config:
            self.rule_engine.add_rule(
                StopLossTakeProfitRule("stop_loss_take_profit", rules_config["stop_loss_take_profit"])
            )
        
        # 添加订单金额限制规则
        if "order_amount_limit" in rules_config:
            self.rule_engine.add_rule(
                OrderAmountLimitRule("order_amount_limit", rules_config["order_amount_limit"])
            )
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        self.event_engine.register_handler(EventType.SIGNAL, self.on_signal)
        self.event_engine.register_handler(EventType.ORDER, self.on_order)
        self.event_engine.register_handler(EventType.FILL, self.on_fill)
        self.event_engine.register_handler(EventType.EXCEPTION, self.on_exception)
    
    def on_signal(self, event: SignalEvent):
        """处理交易信号，事前风控"""
        # 检查策略是否被暂停
        if hasattr(event, 'strategy_name') and event.strategy_name in self.paused_strategies or self.global_pause:
            logger.warning(f"策略 {event.strategy_name} 已被暂停，忽略交易信号")
            return
        
        # 实现信号级别的风控检查
        # 这里简化实现，只记录日志
        logger.debug(f"处理交易信号: {event}")
    
    def on_order(self, event: OrderEvent):
        """处理订单事件，事中风控"""
        # 订单生成前的风控检查
        logger.debug(f"处理订单事件: {event}")
        # 这里简化实现，实际应该检查订单风险
    
    def on_fill(self, event: FillEvent):
        """处理成交事件，事后风控"""
        # 实现成交后的风控检查
        # 例如：更新风险指标、检查是否触发止损止盈等
        logger.debug(f"处理成交事件: {event}")
    
    def on_exception(self, event: ExceptionEvent):
        """处理异常事件"""
        # 调用异常处理器处理异常
        self.exception_handler.handle_exception(event.exception, event.context)
    
    def check_order_risk(self, order: Order, portfolio) -> bool:
        """
        检查订单风险
        
        Args:
            order: 订单对象
            portfolio: 投资组合对象
            
        Returns:
            bool: 是否通过风控检查
        """
        # 构建检查上下文
        context = {
            "order": order,
            "portfolio": portfolio,
            "current_price": self._get_current_price(order.symbol),
            "strategy_name": getattr(order, "strategy_name", "default")
        }
        
        # 执行所有风险规则
        violated_rules = self.rule_engine.check_rules(context)
        
        if violated_rules:
            # 生成风控报告
            risk_report = self._generate_risk_report(violated_rules, context)
            logger.warning(f"订单 {order.order_id} 触发风控规则，被拒绝: {risk_report}")
            
            # 触发风控事件
            self.event_engine.put(RiskEvent(
                event_type="ORDER_REJECTED",
                order_id=order.order_id,
                violated_rules=[rule.name for rule in violated_rules],
                risk_report=risk_report,
                strategy_name=context["strategy_name"]
            ))
            
            return False
        
        return True
    
    def calculate_risk_metrics(self, portfolio) -> dict:
        """
        计算投资组合的风险指标
        
        Args:
            portfolio: 投资组合对象
            
        Returns:
            dict: 风险指标字典
        """
        return self.metrics_calculator.calculate_all_metrics(portfolio)
    
    def pause_strategy(self, strategy_name: str):
        """暂停策略"""
        if strategy_name:
            self.paused_strategies.add(strategy_name)
            logger.info(f"策略 {strategy_name} 已暂停")
            
            # 触发策略暂停事件
            self.event_engine.put(StrategyEvent(
                strategy_name=strategy_name,
                event_type="PAUSED"
            ))
    
    def resume_strategy(self, strategy_name: str):
        """恢复策略"""
        if strategy_name and strategy_name in self.paused_strategies:
            self.paused_strategies.remove(strategy_name)
            logger.info(f"策略 {strategy_name} 已恢复")
            
            # 触发策略恢复事件
            self.event_engine.put(StrategyEvent(
                strategy_name=strategy_name,
                event_type="RESUMED"
            ))
    
    def pause_all_strategies(self):
        """暂停所有策略"""
        self.global_pause = True
        logger.info("所有策略已暂停")
    
    def resume_all_strategies(self):
        """恢复所有策略"""
        self.global_pause = False
        self.paused_strategies.clear()
        logger.info("所有策略已恢复")
    
    def _get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        # 实现获取当前价格的逻辑
        # 这里简化实现，返回默认值
        return 10.0
    
    def _generate_risk_report(self, violated_rules: List[RiskRule], context: dict) -> str:
        """生成风险报告"""
        report = []
        for rule in violated_rules:
            report.append(f"{rule.name}: {rule.get_violation_message()}")
        return "; ".join(report)
    
    def start_monitoring(self):
        """启动风险监控"""
        self.risk_monitor.start()
        logger.info("风险监控已启动")
    
    def stop_monitoring(self):
        """停止风险监控"""
        self.risk_monitor.stop()
        logger.info("风险监控已停止")
