# -*- coding: utf-8 -*-
"""
A股数据工具函数
"""
import re
from typing import List, Tuple, Optional
from loguru import logger


class StockUtils:
    """股票工具类"""
    
    @staticmethod
    def normalize_symbol(symbol: str) -> Tuple[str, str]:
        """标准化股票代码
        
        Args:
            symbol: 股票代码，可以是 '000001'、'000001.SZ'、'SZ000001' 等格式
            
        Returns:
            (标准化代码, 交易所)
        """
        symbol = str(symbol).strip().upper()
        
        # 移除可能的空格和其他字符
        symbol = symbol.replace(' ', '')
        
        # 处理不同格式的代码
        if '.' in symbol:
            # 格式: 000001.SZ
            code, exchange = symbol.split('.')
            if exchange in ['SH', 'SZ', 'BJ']:
                return f"{code}.{exchange}", exchange
            else:
                # 无法识别交易所，默认根据代码判断
                if code.startswith(('6', '9')):
                    return f"{code}.SH", 'SH'
                elif code.startswith(('0', '3')):
                    return f"{code}.SZ", 'SZ'
                elif code.startswith('4'):
                    return f"{code}.BJ", 'BJ'
                else:
                    return f"{code}.SH", 'SH'
        elif re.match(r'^[SZBJ][SHZJB]\d{6}$', symbol):
            # 格式: SZ000001
            exchange = symbol[:2] if symbol.startswith(('BJ', 'SH', 'SZ')) else symbol[0]
            code = symbol[2:] if symbol.startswith(('BJ', 'SH', 'SZ')) else symbol[1:]
            return f"{code}.{exchange.upper()}", exchange.upper()
        else:
            # 格式: 000001
            if symbol.startswith(('6', '9', '5')):
                return f"{symbol}.SH", 'SH'
            elif symbol.startswith(('0', '3')):
                return f"{symbol}.SZ", 'SZ'
            elif symbol.startswith('4'):
                return f"{symbol}.BJ", 'BJ'
            else:
                # 默认上海
                return f"{symbol}.SH", 'SH'
    
    @staticmethod
    def get_stock_name(symbol: str) -> str:
        """获取股票名称映射（简版）"""
        stock_names = {
            '000001.SZ': '平安银行',
            '000002.SZ': '万科A',
            '000858.SZ': '五粮液',
            '002415.SZ': '海康威视',
            '300750.SZ': '宁德时代',
            '600519.SH': '贵州茅台',
            '600036.SH': '招商银行',
            '601318.SH': '中国平安',
            '601888.SH': '中国中免',
            '000333.SZ': '美的集团',
            '000651.SZ': '格力电器',
            '300059.SZ': '东方财富',
            '002594.SZ': '比亚迪',
            '300760.SZ': '迈瑞医疗',
        }
        
        normalized, _ = StockUtils.normalize_symbol(symbol)
        return stock_names.get(normalized, symbol)
    
    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """验证股票代码是否有效格式"""
        try:
            normalized, exchange = StockUtils.normalize_symbol(symbol)
            code = normalized.split('.')[0]
            
            # 检查代码长度和格式
            if len(code) != 6 or not code.isdigit():
                return False
            
            # 根据交易所检查代码前缀
            if exchange == 'SH':
                return code.startswith(('6', '9', '5'))
            elif exchange == 'SZ':
                return code.startswith(('0', '3'))
            elif exchange == 'BJ':
                return code.startswith('4')
            else:
                return False
                
        except Exception:
            return False
    
    @staticmethod
    def get_index_symbols() -> List[str]:
        """获取主要指数代码"""
        return [
            '000001.SH',  # 上证指数
            '399001.SZ',  # 深证成指
            '399006.SZ',  # 创业板指
            '000300.SH',  # 沪深300
            '000905.SH',  # 中证500
            '000852.SH',  # 中证1000
        ]
    
    @staticmethod
    def get_etf_symbols() -> List[str]:
        """获取主要ETF代码"""
        return [
            '510300.SH',  # 沪深300ETF
            '510500.SH',  # 中证500ETF
            '510050.SH',  # 上证50ETF
            '159919.SZ',  # 沪深300ETF
            '159915.SZ',  # 创业板ETF
        ]
    
    @staticmethod
    def calculate_technical_indicators(df, price_col='close', volume_col='volume'):
        """计算技术指标"""
        import pandas as pd
        import numpy as np
        
        result = df.copy()
        
        # 移动平均线
        result['MA5'] = result[price_col].rolling(window=5).mean()
        result['MA10'] = result[price_col].rolling(window=10).mean()
        result['MA20'] = result[price_col].rolling(window=20).mean()
        result['MA60'] = result[price_col].rolling(window=60).mean()
        
        # 指数移动平均线
        result['EMA12'] = result[price_col].ewm(span=12).mean()
        result['EMA26'] = result[price_col].ewm(span=26).mean()
        
        # MACD
        result['MACD'] = result['EMA12'] - result['EMA26']
        result['MACD_Signal'] = result['MACD'].ewm(span=9).mean()
        result['MACD_Hist'] = result['MACD'] - result['MACD_Signal']
        
        # RSI
        delta = result[price_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        result['BB_Middle'] = result[price_col].rolling(window=20).mean()
        bb_std = result[price_col].rolling(window=20).std()
        result['BB_Upper'] = result['BB_Middle'] + (bb_std * 2)
        result['BB_Lower'] = result['BB_Middle'] - (bb_std * 2)
        
        # 成交量相关
        if volume_col in result.columns:
            result['Volume_MA5'] = result[volume_col].rolling(window=5).mean()
            result['Volume_MA10'] = result[volume_col].rolling(window=10).mean()
        
        # ATR（平均真实波幅）
        high_low = result['high'] - result['low']
        high_close = abs(result['high'] - result[price_col].shift())
        low_close = abs(result['low'] - result[price_col].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        result['ATR'] = true_range.rolling(window=14).mean()
        
        return result


# 创建全局工具实例
stock_utils = StockUtils()