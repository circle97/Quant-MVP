# -*- coding: utf-8 -*-
"""
回测引擎 - 负责策略的回测执行和结果分析
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from loguru import logger

from src.core.event import EventEngine, EventType, BarEvent, SignalEvent, OrderEvent, FillEvent, TimerEvent
from src.strategy.base import Strategy
from src.core.portfolio import Portfolio
from src.data.data_manager import AStockDataManager as DataManager


class BacktestEngine:
    """回测引擎，负责策略的回测执行和结果分析"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.event_engine = EventEngine()
        self.strategy = None
        self.portfolio = None
        self.data_manager = None
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # 回测参数
        self.initial_capital = self.config.get('initial_capital', 100000.0)
        self.start_date = self.config.get('start_date')
        self.end_date = self.config.get('end_date')
        self.data_frequency = self.config.get('data_frequency', 'daily')
        
        logger.info("初始化回测引擎")
    
    def set_strategy(self, strategy: Strategy):
        """设置回测策略"""
        # 将回测引擎的事件引擎传递给策略
        strategy.event_engine = self.event_engine
        self.strategy = strategy
        logger.info(f"设置回测策略: {strategy.name}")
    
    def set_data_manager(self, data_manager: DataManager):
        """设置数据管理器"""
        self.data_manager = data_manager
        logger.info(f"设置数据管理器")
    
    def init_portfolio(self):
        """初始化投资组合"""
        self.portfolio = Portfolio(self.initial_capital)
        logger.info(f"初始化投资组合，初始资金: {self.initial_capital:.2f}")
    
    def run(self):
        """运行回测"""
        if not self.strategy:
            raise ValueError("策略未设置")
        
        if not self.data_manager:
            raise ValueError("数据管理器未设置")
        
        logger.info("开始回测...")
        self.start_time = datetime.now()
        
        # 初始化投资组合
        self.init_portfolio()
        
        # 初始化策略
        self.strategy.initialize()
        
        # 启动策略
        self.strategy.start()
        
        # 注册事件处理器
        self.event_engine.register_handler(EventType.BAR_DATA, self.strategy.on_bar)
        self.event_engine.register_handler(EventType.SIGNAL, self._handle_signal)
        self.event_engine.register_handler(EventType.ORDER, self._handle_order)
        
        # 获取回测数据
        symbols = self.strategy.symbols
        bars = self._get_backtest_data(symbols)
        
        # 按时间顺序处理K线数据
        self._process_bars(bars)
        
        # 停止策略
        self.strategy.stop()
        
        self.end_time = datetime.now()
        
        # 生成回测结果
        self._generate_results()
        
        logger.info(f"回测完成，耗时: {self.end_time - self.start_time}")
    
    def _handle_signal(self, signal_event: SignalEvent):
        """处理信号事件，生成订单"""
        data = signal_event.data
        symbol = data['symbol']
        signal_type = data['signal_type']
        strength = data['strength']
        price = data['price']
        
        # 简单的信号转订单逻辑：根据信号强度决定交易数量
        # 这里简化处理，使用固定数量
        quantity = 100  # 1手
        
        if signal_type == 'BUY':
            order_type = 'MARKET'  # 市价单
            direction = 'LONG'  # 买入
            
            # 创建订单事件
            order_event = OrderEvent(
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                direction=direction,
                price=price,
                timestamp=signal_event.timestamp
            )
            
            self.event_engine.put(order_event)
            logger.debug(f"信号转订单: {signal_event} -> {order_event}")
        
        elif signal_type == 'SELL':
            order_type = 'MARKET'  # 市价单
            direction = 'SHORT'  # 卖出
            
            # 创建订单事件
            order_event = OrderEvent(
                symbol=symbol,
                order_type=order_type,
                quantity=quantity,
                direction=direction,
                price=price,
                timestamp=signal_event.timestamp
            )
            
            self.event_engine.put(order_event)
            logger.debug(f"信号转订单: {signal_event} -> {order_event}")
    
    def _handle_order(self, order_event: OrderEvent):
        """处理订单事件，执行订单"""
        # 执行订单
        success = self.portfolio.execute_order(order_event)
        if success:
            # 记录每日资产
            self.portfolio.record_daily_value(order_event.timestamp)
            logger.debug(f"订单执行成功: {order_event}")
    
    def _process_bars(self, bars: Dict[str, List[BarEvent]]):
        """按时间顺序处理K线数据"""
        # 将所有K线按时间排序
        all_bars = []
        for symbol, symbol_bars in bars.items():
            all_bars.extend(symbol_bars)
        
        # 按时间排序
        all_bars.sort(key=lambda x: x.timestamp)
        
        # 处理每根K线数据
        for bar in all_bars:
            self.event_engine.put(bar)
            # 记录每日资产
            self.portfolio.record_daily_value(bar.timestamp)
    
    def _get_backtest_data(self, symbols: List[str]) -> Dict[str, List[BarEvent]]:
        """获取回测数据"""
        bars = {}
        
        for symbol in symbols:
            # 从数据管理器获取历史数据
            data = self.data_manager.get_daily_data(symbol, self.start_date, self.end_date)
            
            # 转换为BarEvent列表
            symbol_bars = []
            for index, row in data.iterrows():
                bar_data = {
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                
                bar_event = BarEvent(
                    symbol=symbol,
                    bar_data=bar_data,
                    timestamp=index
                )
                
                symbol_bars.append(bar_event)
            
            bars[symbol] = symbol_bars
            logger.info(f"加载 {symbol} 回测数据，共 {len(symbol_bars)} 根K线")
        
        return bars
    
    def _process_bars(self, bars: Dict[str, List[BarEvent]]):
        """按时间顺序处理K线数据"""
        # 将所有K线按时间排序
        all_bars = []
        for symbol, symbol_bars in bars.items():
            all_bars.extend(symbol_bars)
        
        # 按时间排序
        all_bars.sort(key=lambda x: x.timestamp)
        
        # 处理每根K线
        for bar in all_bars:
            self.event_engine.put(bar)
    
    def _generate_results(self):
        """生成回测结果"""
        if not self.portfolio:
            return
        
        # 获取投资组合摘要
        portfolio_summary = self.portfolio.get_portfolio_summary()
        
        # 计算回测指标
        total_return = portfolio_summary['总收益率'] / 100  # 转换为小数
        
        # 使用 portfolio 的绩效指标计算方法
        performance_metrics = self.portfolio.get_performance_metrics()
        
        # 构建回测结果
        self.results = {
            'strategy_name': self.strategy.name,
            'initial_capital': self.initial_capital,
            'final_capital': self.portfolio.current_capital,
            'total_return': total_return,
            'annual_return': performance_metrics.get('年化收益率', 0.0) / 100,  # 转换为小数
            'max_drawdown': abs(performance_metrics.get('最大回撤', 0.0) / 100),  # 转换为小数
            'sharpe_ratio': performance_metrics.get('夏普比率', 0.0),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'data_frequency': self.data_frequency,
            'duration': self.end_time - self.start_time,
            'portfolio_summary': portfolio_summary,
            'daily_values': self.portfolio.daily_values
        }
        
        # 从 results 中获取回测指标用于日志输出
        annual_return = self.results['annual_return']
        max_drawdown = self.results['max_drawdown']
        sharpe_ratio = self.results['sharpe_ratio']
        
        logger.info(f"回测结果:")
        logger.info(f"  总收益率: {total_return:.2%}")
        logger.info(f"  年化收益率: {annual_return:.2%}")
        logger.info(f"  最大回撤: {max_drawdown:.2%}")
        logger.info(f"  夏普比率: {sharpe_ratio:.2f}")
        logger.info(f"  最终资金: {self.portfolio.current_capital:.2f}")
    
    def get_results(self) -> Dict[str, Any]:
        """获取回测结果"""
        return self.results
    
    def plot_results(self):
        """绘制回测结果"""
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
            
            # 设置中文支持
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']  # 设置中文字体
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
            
            if not self.results:
                logger.warning("回测结果为空，无法绘制")
                return
            
            daily_values = self.results['daily_values']
            if not daily_values:
                logger.warning("没有每日价值数据，无法绘制")
                return
            
            # 将列表转换为DataFrame
            df = pd.DataFrame(daily_values)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # 创建画布
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            
            # 绘制资产曲线
            ax1.plot(df.index, df['total_value'], label='总资产')
            ax1.set_title('回测资产曲线')
            ax1.set_ylabel('资产价值')
            ax1.legend()
            ax1.grid(True)
            
            # 绘制收益率曲线
            cumulative_returns = (df['total_value'] / df['total_value'].iloc[0]) - 1
            ax2.plot(df.index, cumulative_returns, label='累计收益率')
            ax2.set_title('回测收益率曲线')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('收益率')
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            plt.show()
            
            logger.info("绘制回测结果完成")
        except ImportError:
            logger.warning("matplotlib 未安装，无法绘制回测结果")
        except Exception as e:
            logger.error(f"绘制回测结果失败: {e}")
