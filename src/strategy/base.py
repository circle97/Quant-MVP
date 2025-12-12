# -*- coding: utf-8 -*-
"""
策略基类 - 所有交易策略的模板
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from loguru import logger

from src.core.event import Event, BarEvent, SignalEvent, TimerEvent, event_engine
from src.core.portfolio import Portfolio
from src.data import astock_data_manager, stock_utils


class Strategy(ABC):
    """策略抽象基类"""
    
    def __init__(self, name: str, symbols: List[str], initial_capital: float = 10000.0):
        """
        初始化策略
        
        Args:
            name: 策略名称
            symbols: 交易的股票代码列表
            initial_capital: 初始资金
        """
        self.name = name
        self.symbols = [stock_utils.normalize_symbol(s)[0] for s in symbols]
        self.initial_capital = initial_capital
        
        # 数据相关
        self.data = {}  # 存储各股票的历史数据
        self.current_prices = {}  # 当前价格
        
        # 状态管理
        self.initialized = False
        self.running = False
        
        # 投资组合
        self.portfolio = Portfolio(initial_capital)
        
        # 策略参数
        self.params = {}
        
        # 注册事件处理器
        self._register_event_handlers()
        
        logger.info(f"初始化策略: {name}, 交易标的: {self.symbols}")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        event_engine.register_handler(BarEvent, self.on_bar)
        event_engine.register_handler(TimerEvent, self.on_timer)
    
    def initialize(self):
        """策略初始化"""
        if self.initialized:
            return
        
        logger.info(f"策略 {self.name} 初始化开始...")
        
        # 加载历史数据
        self.load_historical_data()
        
        # 调用子类的初始化方法
        self.on_init()
        
        self.initialized = True
        logger.info(f"策略 {self.name} 初始化完成")
    
    def load_historical_data(self, lookback_days: int = 100):
        """加载历史数据"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - pd.Timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        logger.info(f"加载历史数据: {start_date} 到 {end_date}")
        
        for symbol in self.symbols:
            try:
                df = astock_data_manager.get_daily_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust='qfq'
                )
                
                if not df.empty:
                    self.data[symbol] = df
                    # 设置当前价格（最新收盘价）
                    if not df.empty:
                        self.current_prices[symbol] = df['close'].iloc[-1]
                    logger.info(f"加载 {symbol} 数据成功: {len(df)} 条记录")
                else:
                    logger.warning(f"未获取到 {symbol} 的历史数据")
                    
            except Exception as e:
                logger.error(f"加载 {symbol} 数据失败: {e}")
    
    def start(self):
        """启动策略"""
        if not self.initialized:
            self.initialize()
        
        self.running = True
        logger.info(f"策略 {self.name} 已启动")
    
    def stop(self):
        """停止策略"""
        self.running = False
        logger.info(f"策略 {self.name} 已停止")
    
    @abstractmethod
    def on_init(self):
        """策略初始化回调（子类实现）"""
        pass
    
    @abstractmethod
    def on_bar(self, event: BarEvent):
        """
        K线数据回调（子类实现）
        
        Args:
            event: K线事件
        """
        pass
    
    def on_timer(self, event: TimerEvent):
        """定时器回调（可选实现）"""
        pass
    
    def generate_signal(self, symbol: str, signal_type: str, 
                       strength: float = 1.0, price: Optional[float] = None):
        """
        生成交易信号
        
        Args:
            symbol: 股票代码
            signal_type: 信号类型 ('BUY', 'SELL', 'HOLD')
            strength: 信号强度 (0.0-1.0)
            price: 建议价格
        """
        if not self.running:
            return
        
        # 创建信号事件
        signal_event = SignalEvent(
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            price=price,
            timestamp=datetime.now()
        )
        
        # 放入事件引擎
        event_engine.put(signal_event)
        
        logger.debug(f"策略 {self.name} 生成信号: {signal_event}")
    
    def update_portfolio_price(self, symbol: str, price: float):
        """更新投资组合中的价格"""
        if symbol in self.current_prices:
            self.current_prices[symbol] = price
        
        # 更新投资组合
        self.portfolio.update_total_value(price)
    
    def get_strategy_state(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            'name': self.name,
            'symbols': self.symbols,
            'initialized': self.initialized,
            'running': self.running,
            'initial_capital': self.initial_capital,
            'current_capital': self.portfolio.current_capital,
            'total_return': self.portfolio.get_portfolio_summary()['总收益率'],
            'positions': len(self.portfolio.positions)
        }
    
    def get_position(self, symbol: str):
        """获取持仓"""
        return self.portfolio.get_position(symbol)
    
    def get_all_positions(self):
        """获取所有持仓"""
        return self.portfolio.get_all_positions()
    
    def get_portfolio_summary(self):
        """获取投资组合摘要"""
        return self.portfolio.get_portfolio_summary()
    
    def get_performance_metrics(self):
        """获取绩效指标"""
        return self.portfolio.get_performance_metrics()


class AStockTradingStrategy(Strategy):
    """A股交易策略基类（包含A股特有规则）"""
    
    def __init__(self, name: str, symbols: List[str], initial_capital: float = 10000.0):
        super().__init__(name, symbols, initial_capital)
        
        # A股特有参数
        self.trading_hours = {
            'morning_open': '09:30:00',
            'morning_close': '11:30:00',
            'afternoon_open': '13:00:00',
            'afternoon_close': '15:00:00'
        }
        
        # A股交易规则
        self.min_trade_units = 100  # 最小交易单位（手）
        self.price_limit = 0.1  # 涨跌幅限制（10%）
        
        # 风险管理
        self.max_position_ratio = 0.8  # 最大持仓比例
        self.stop_loss_ratio = 0.08  # 止损比例
        self.take_profit_ratio = 0.15  # 止盈比例
    
    def is_trading_hours(self, dt: datetime = None) -> bool:
        """判断是否为交易时间"""
        if dt is None:
            dt = datetime.now()
        
        time_str = dt.strftime('%H:%M:%S')
        weekday = dt.weekday()
        
        # 周末不交易
        if weekday >= 5:
            return False
        
        # 检查交易时间
        morning_open = self.trading_hours['morning_open']
        morning_close = self.trading_hours['morning_close']
        afternoon_open = self.trading_hours['afternoon_open']
        afternoon_close = self.trading_hours['afternoon_close']
        
        return (morning_open <= time_str <= morning_close) or \
               (afternoon_open <= time_str <= afternoon_close)
    
    def calculate_position_size(self, symbol: str, price: float, risk_ratio: float = 0.02) -> int:
        """
        计算头寸大小（基于风险管理的凯利公式简化版）
        
        Args:
            symbol: 股票代码
            price: 价格
            risk_ratio: 风险比例（每次交易最大亏损比例）
            
        Returns:
            建议交易数量（股的整数倍）
        """
        # 可用资金
        available_cash = self.portfolio.cash * self.max_position_ratio
        
        # 单笔交易风险金额
        risk_amount = self.portfolio.total_value * risk_ratio
        
        # 止损距离（基于ATR或固定比例）
        stop_distance = price * self.stop_loss_ratio
        
        # 计算头寸
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            position_size = available_cash / price
        
        # 转换为A股手数（100股的整数倍）
        position_size = max(position_size // 100 * 100, 100)
        
        # 确保不超过可用资金
        max_by_cash = available_cash // price // 100 * 100
        position_size = min(position_size, max_by_cash)
        
        return int(position_size)
    
    def check_trading_rules(self, symbol: str, action: str, quantity: int, price: float) -> Tuple[bool, str]:
        """
        检查A股交易规则
        
        Returns:
            (是否允许交易, 原因)
        """
        # 检查交易时间
        if not self.is_trading_hours():
            return False, "非交易时间"
        
        # 检查最小交易单位
        if quantity < self.min_trade_units or quantity % self.min_trade_units != 0:
            return False, f"交易数量必须是{self.min_trade_units}的整数倍"
        
        # 检查涨跌停
        if symbol in self.current_prices:
            prev_close = self.current_prices[symbol]
            price_limit_up = prev_close * (1 + self.price_limit)
            price_limit_down = prev_close * (1 - self.price_limit)
            
            if price > price_limit_up or price < price_limit_down:
                return False, f"价格超出涨跌停限制: {price_limit_down:.2f}-{price_limit_up:.2f}"
        
        # 检查持仓限制
        if action == 'BUY':
            position_value = quantity * price
            total_position_value = sum(p.market_value for p in self.portfolio.positions.values())
            
            if total_position_value + position_value > self.portfolio.total_value * self.max_position_ratio:
                return False, f"超过最大持仓比例 {self.max_position_ratio*100}%"
        
        return True, "允许交易"