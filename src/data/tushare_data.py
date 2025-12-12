# -*- coding: utf-8 -*-
"""
Tushare数据源实现
"""
import tushare as ts
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from .base import AStockDataFeed, BarData, AStockDataError
from ..utils.config import config_manager


class TushareData(AStockDataFeed):
    """Tushare数据源"""
    
    def __init__(self):
        super().__init__("Tushare")
        self.token = config_manager.get('data.tushare.token', '')
        self.pro_api = config_manager.get('data.tushare.pro_api', False)
        self.pro = None
        
    def connect(self):
        """连接Tushare数据源"""
        try:
            if not self.token:
                raise AStockDataError("未配置Tushare token，请在config.yaml中配置")
            
            # 设置token
            ts.set_token(self.token)
            
            # 如果需要使用pro接口
            if self.pro_api:
                self.pro = ts.pro_api()
                logger.info("已连接 Tushare Pro 接口")
            else:
                logger.info("已连接 Tushare 免费接口")
            
            self.connected = True
            logger.info(f"已连接 {self.name} 数据源")
            
        except Exception as e:
            logger.error(f"连接 Tushare 失败: {e}")
            raise AStockDataError(f"连接 Tushare 失败: {e}")
        
    def disconnect(self):
        """断开连接"""
        self.connected = False
        self.pro = None
        logger.info(f"已断开 {self.name} 数据源")
        
    def get_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取日线数据
        
        Args:
            symbol: 股票代码，如 '000001.SZ'
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            adjust: 复权类型 qfq(前复权), hfq(后复权), None(不复权)
            
        Returns:
            pandas DataFrame
        """
        if not self.connected:
            self.connect()
        
        try:
            # 提取股票代码和交易所
            if '.' in symbol:
                ts_code = symbol  # 已经是标准格式
            else:
                # 根据代码判断交易所
                if symbol.startswith(('6', '9')):
                    ts_code = f"{symbol}.SH"  # 上海
                elif symbol.startswith(('0', '3')):
                    ts_code = f"{symbol}.SZ"  # 深圳
                elif symbol.startswith('4'):
                    ts_code = f"{symbol}.BJ"  # 北京
                else:
                    ts_code = f"{symbol}.SH"  # 默认上海
            
            # 使用pro接口或普通接口
            if self.pro_api and self.pro:
                # 使用pro接口获取日线数据
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )
                
                if not df.empty:
                    # 重命名列
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'ts_code': 'symbol',
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'vol': 'volume',
                        'amount': 'amount',
                        'pct_chg': 'pct_chg'
                    })
                    
                    # 转换为datetime
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    df = df.sort_index()
                    
            else:
                # 使用免费接口
                stock_code = ts_code.split('.')[0]  # 去掉交易所后缀
                
                # 获取不复权数据
                df = ts.get_k_data(
                    code=stock_code,
                    start=start_date,
                    end=end_date,
                    ktype='D'
                )
                
                if not df.empty:
                    # 重命名列
                    df = df.rename(columns={
                        'date': 'date',
                        'code': 'symbol',
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume'
                    })
                    
                    # 转换为datetime
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')
                    df = df.sort_index()
                    
                    # 计算成交额（免费接口没有，这里用近似值）
                    df['amount'] = df['close'] * df['volume'] * 100  # volume是手数
                    
                    # 计算涨跌幅
                    df['pct_chg'] = df['close'].pct_change() * 100
            
            if df.empty:
                logger.warning(f"未获取到 {symbol} 的数据")
                return pd.DataFrame()
            
            # 处理复权
            if adjust and adjust in ['qfq', 'hfq']:
                df = self._adjust_data(df, ts_code, adjust)
            
            logger.info(f"获取 {symbol} 数据成功: {start_date} 到 {end_date}, "
                       f"共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def _adjust_data(self, df: pd.DataFrame, ts_code: str, adjust: str) -> pd.DataFrame:
        """处理复权数据
        
        Args:
            df: 原始数据
            ts_code: 股票代码
            adjust: 复权类型
            
        Returns:
            复权后的数据
        """
        try:
            # 获取复权因子
            if self.pro_api and self.pro:
                adj_factor = self.pro.adj_factor(
                    ts_code=ts_code,
                    trade_date=''
                )
                
                if not adj_factor.empty:
                    # 合并复权因子
                    adj_factor['trade_date'] = pd.to_datetime(adj_factor['trade_date'])
                    adj_factor = adj_factor.set_index('trade_date')
                    df = df.join(adj_factor['adj_factor'], how='left')
                    
                    # 前向填充复权因子
                    df['adj_factor'] = df['adj_factor'].ffill().bfill()
                    
                    if adjust == 'qfq':  # 前复权
                        df['open'] = df['open'] * df['adj_factor']
                        df['high'] = df['high'] * df['adj_factor']
                        df['low'] = df['low'] * df['adj_factor']
                        df['close'] = df['close'] * df['adj_factor']
                    elif adjust == 'hfq':  # 后复权
                        latest_adj = df['adj_factor'].iloc[-1] if not df['adj_factor'].empty else 1
                        df['open'] = df['open'] * df['adj_factor'] / latest_adj
                        df['high'] = df['high'] * df['adj_factor'] / latest_adj
                        df['low'] = df['low'] * df['adj_factor'] / latest_adj
                        df['close'] = df['close'] * df['adj_factor'] / latest_adj
            
            return df
            
        except Exception as e:
            logger.warning(f"复权处理失败: {e}")
            return df
    
    def get_realtime_quote(self, symbol: str) -> Dict:
        """获取实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时行情字典
        """
        if not self.connected:
            self.connect()
        
        try:
            # 获取实时行情数据
            if self.pro_api and self.pro:
                # pro接口获取实时行情
                ts_code = f"{symbol}.SH" if not '.' in symbol else symbol
                df = self.pro.daily_basic(
                    ts_code=ts_code,
                    trade_date=datetime.now().strftime('%Y%m%d')
                )
                
                if not df.empty:
                    quote = {
                        'symbol': symbol,
                        'close': float(df.iloc[0]['close']),
                        'turnover_rate': float(df.iloc[0]['turnover_rate']),
                        'volume_ratio': float(df.iloc[0]['volume_ratio']),
                        'pe': float(df.iloc[0]['pe']),
                        'pb': float(df.iloc[0]['pb']),
                        'total_share': float(df.iloc[0]['total_share']),
                        'float_share': float(df.iloc[0]['float_share']),
                        'timestamp': datetime.now().isoformat()
                    }
                    return quote
            else:
                # 免费接口获取实时行情
                stock_code = symbol.split('.')[0] if '.' in symbol else symbol
                df = ts.get_realtime_quotes(stock_code)
                
                if not df.empty:
                    quote = {
                        'symbol': symbol,
                        'name': df.iloc[0]['name'],
                        'price': float(df.iloc[0]['price']),
                        'open': float(df.iloc[0]['open']),
                        'high': float(df.iloc[0]['high']),
                        'low': float(df.iloc[0]['low']),
                        'pre_close': float(df.iloc[0]['pre_close']),
                        'volume': int(df.iloc[0]['volume']),
                        'amount': float(df.iloc[0]['amount']),
                        'bid': float(df.iloc[0]['b1_p']),
                        'ask': float(df.iloc[0]['a1_p']),
                        'timestamp': datetime.now().isoformat()
                    }
                    return quote
                    
        except Exception as e:
            logger.error(f"获取 {symbol} 实时行情失败: {e}")
        
        return {}
    
    def get_basic_info(self, symbol: str) -> Dict:
        """获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
        """
        try:
            ts_code = f"{symbol}.SH" if not '.' in symbol else symbol
            
            if self.pro_api and self.pro:
                # pro接口获取股票基本信息
                df = self.pro.stock_basic(
                    ts_code=ts_code,
                    fields='ts_code,name,area,industry,market,list_date'
                )
                
                if not df.empty:
                    info = {
                        'symbol': symbol,
                        'name': df.iloc[0]['name'],
                        'area': df.iloc[0]['area'],
                        'industry': df.iloc[0]['industry'],
                        'market': df.iloc[0]['market'],
                        'list_date': df.iloc[0]['list_date']
                    }
                    return info
            else:
                # 免费接口获取基本信息
                stock_code = ts_code.split('.')[0]
                df = ts.get_stock_basics()
                
                if stock_code in df.index:
                    info = {
                        'symbol': symbol,
                        'name': df.loc[stock_code, 'name'],
                        'industry': df.loc[stock_code, 'industry'],
                        'area': df.loc[stock_code, 'area'],
                        'pe': float(df.loc[stock_code, 'pe']),
                        'outstanding': float(df.loc[stock_code, 'outstanding']),
                        'totals': float(df.loc[stock_code, 'totals']),
                        'totalAssets': float(df.loc[stock_code, 'totalAssets']),
                        'liquidAssets': float(df.loc[stock_code, 'liquidAssets'])
                    }
                    return info
                    
        except Exception as e:
            logger.error(f"获取 {symbol} 基本信息失败: {e}")
        
        return {}
    
    def get_index_data(self, index_code: str = '000001.SH', 
                      start_date: str = None, 
                      end_date: str = None) -> pd.DataFrame:
        """获取指数数据
        
        Args:
            index_code: 指数代码，默认上证指数
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据DataFrame
        """
        try:
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            df = self.get_daily_data(index_code, start_date, end_date, adjust=None)
            return df
            
        except Exception as e:
            logger.error(f"获取指数 {index_code} 数据失败: {e}")
            return pd.DataFrame()


# 创建全局实例
tushare_data = TushareData()