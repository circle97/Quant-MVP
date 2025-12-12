# -*- coding: utf-8 -*-
"""
AKShare数据源实现（免费，无需token）
"""
import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import time
import random

from .base import AStockDataFeed, BarData, AStockDataError


class AKShareData(AStockDataFeed):
    """AKShare数据源（免费，无需token）"""
    
    def __init__(self, timeout: int = 30):
        super().__init__("AKShare")
        self.timeout = timeout
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
    def connect(self):
        """连接数据源（AKShare无需显式连接）"""
        self.connected = True
        logger.info(f"已连接 {self.name} 数据源")
        
    def disconnect(self):
        """断开连接"""
        self.connected = False
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
            symbol: 股票代码，如 '000001' 或 'sz000001'
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            pandas DataFrame
        """
        if not self.connected:
            self.connect()
        
        max_retries = 3  # 最大重试次数
        retry_delay = 2   # 重试延迟（秒）
        
        for attempt in range(max_retries):
            try:
                # 清理股票代码格式
                if '.' in symbol:
                    # 将 '000001.SZ' 转换为 'sz000001'
                    code, exchange = symbol.split('.')
                    if exchange.upper() == 'SH':
                        ak_symbol = f"sh{code}"
                    elif exchange.upper() == 'SZ':
                        ak_symbol = f"sz{code}"
                    elif exchange.upper() == 'BJ':
                        ak_symbol = f"bj{code}"
                    else:
                        ak_symbol = code
                else:
                    # 根据代码判断市场
                    if symbol.startswith(('6', '9', '5')):
                        ak_symbol = f"sh{symbol}"
                    elif symbol.startswith(('0', '3')):
                        ak_symbol = f"sz{symbol}"
                    elif symbol.startswith('4'):
                        ak_symbol = f"bj{symbol}"
                    else:
                        ak_symbol = symbol
                
                logger.info(f"尝试获取 {symbol} ({ak_symbol}) 数据，第 {attempt+1} 次尝试...")
                
                # 根据复权类型选择接口
                if adjust == 'qfq':
                    df = ak.stock_zh_a_hist(
                        symbol=ak_symbol,
                        period="daily",
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust="qfq"
                    )
                elif adjust == 'hfq':
                    df = ak.stock_zh_a_hist(
                        symbol=ak_symbol,
                        period="daily",
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust="hfq"
                    )
                else:
                    df = ak.stock_zh_a_hist(
                        symbol=ak_symbol,
                        period="daily",
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust=""
                    )
                
                if df.empty:
                    logger.warning(f"未获取到 {symbol} 的数据")
                    # 尝试另一种格式的股票代码
                    if attempt == 0:
                        continue
                    else:
                        return pd.DataFrame()
                
                # 重命名列
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_chg',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
                
                # 转换为datetime
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df.sort_index()
                
                # 确保数据类型正确
                numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount', 'pct_chg', 'turnover']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.info(f"获取 {symbol} 数据成功: {start_date} 到 {end_date}, "
                           f"共 {len(df)} 条记录")
                
                # 添加随机延迟，避免请求过快
                time.sleep(random.uniform(0.5, 1.5))
                
                return df
                
            except Exception as e:
                logger.warning(f"获取 {symbol} 历史数据失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    retry_delay *= 1.5  # 指数退避
                else:
                    logger.error(f"获取 {symbol} 历史数据失败，已达最大重试次数")
                    return pd.DataFrame()
    
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
            # 清理股票代码格式
            if '.' in symbol:
                code, exchange = symbol.split('.')
                if exchange.upper() == 'SH':
                    ak_symbol = f"sh{code}"
                elif exchange.upper() == 'SZ':
                    ak_symbol = f"sz{code}"
                else:
                    ak_symbol = code
            else:
                ak_symbol = symbol
            
            # 获取实时行情 - 使用更稳定的接口
            df = ak.stock_zh_a_spot_em()
            
            if not df.empty:
                # 找到对应的股票
                # 可能需要尝试不同的代码格式
                possible_codes = [
                    ak_symbol,
                    ak_symbol.upper(),
                    ak_symbol.lower(),
                    symbol.replace('.', '')
                ]
                
                for code in possible_codes:
                    stock_row = df[df['代码'] == code]
                    if not stock_row.empty:
                        quote = {
                            'symbol': symbol,
                            'name': str(stock_row.iloc[0]['名称']),
                            'price': float(stock_row.iloc[0]['最新价']),
                            'change': float(stock_row.iloc[0]['涨跌额']),
                            'pct_change': float(str(stock_row.iloc[0]['涨跌幅']).replace('%', '')) / 100,
                            'volume': float(str(stock_row.iloc[0]['成交量']).replace('手', '')) * 100,
                            'amount': float(str(stock_row.iloc[0]['成交额']).replace('万', '')) * 10000,
                            'high': float(stock_row.iloc[0]['最高']),
                            'low': float(stock_row.iloc[0]['最低']),
                            'open': float(stock_row.iloc[0]['今开']),
                            'pre_close': float(stock_row.iloc[0]['昨收']),
                            'timestamp': datetime.now().isoformat()
                        }
                        return quote
                
                logger.warning(f"未找到股票 {symbol} 的实时数据")
                    
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
            # 清理股票代码格式
            if '.' in symbol:
                code, exchange = symbol.split('.')
                if exchange.upper() == 'SH':
                    ak_symbol = f"sh{code}"
                elif exchange.upper() == 'SZ':
                    ak_symbol = f"sz{code}"
                else:
                    ak_symbol = code
            else:
                ak_symbol = symbol
            
            # 获取股票基本信息 - 使用更稳定的接口
            df = ak.stock_individual_info_em(symbol=ak_symbol)
            
            if not df.empty:
                info = {
                    'symbol': symbol,
                    'name': df[df['item'] == '股票简称']['value'].iloc[0] if not df[df['item'] == '股票简称'].empty else '',
                    'industry': df[df['item'] == '行业']['value'].iloc[0] if not df[df['item'] == '行业'].empty else '',
                    'area': df[df['item'] == '区域']['value'].iloc[0] if not df[df['item'] == '区域'].empty else '',
                    'market': df[df['item'] == '市场']['value'].iloc[0] if not df[df['item'] == '市场'].empty else '',
                    'list_date': df[df['item'] == '上市时间']['value'].iloc[0] if not df[df['item'] == '上市时间'].empty else ''
                }
                return info
                
        except Exception as e:
            logger.error(f"获取 {symbol} 基本信息失败: {e}")
        
        return {}
    
    def get_index_data(self, index_code: str = 'sh000001', 
                      start_date: str = None, 
                      end_date: str = None) -> pd.DataFrame:
        """获取指数数据
        
        Args:
            index_code: 指数代码
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
            
            # 获取指数数据 - 使用更稳定的接口
            df = ak.index_zh_a_hist(
                symbol=index_code,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if not df.empty:
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df.sort_index()
                
                return df
                
        except Exception as e:
            logger.error(f"获取指数 {index_code} 数据失败: {e}")
        
        return pd.DataFrame()


# 创建全局实例
akshare_data = AKShareData()