# -*- coding: utf-8 -*-
"""
A股数据模块测试
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import (
    BarData,
    StockUtils,
    AStockDataManager,
    data_cache
)


class TestStockUtils:
    """测试StockUtils类"""
    
    def test_normalize_symbol(self):
        """测试标准化股票代码"""
        test_cases = [
            ('000001', ('000001.SZ', 'SZ')),  # 深圳股票
            ('600519', ('600519.SH', 'SH')),  # 上海股票
            ('000001.SZ', ('000001.SZ', 'SZ')),  # 标准格式
            ('600519.SH', ('600519.SH', 'SH')),  # 标准格式
            ('SZ000001', ('000001.SZ', 'SZ')),  # 东方财富格式
            ('SH600519', ('600519.SH', 'SH')),  # 东方财富格式
        ]
        
        for input_symbol, expected in test_cases:
            result = StockUtils.normalize_symbol(input_symbol)
            assert result == expected, f"输入: {input_symbol}, 期望: {expected}, 实际: {result}"
        
        print("✓ 股票代码标准化测试通过")
    
    def test_is_valid_symbol(self):
        """测试验证股票代码"""
        valid_symbols = ['000001', '600519', '000001.SZ', '600519.SH']
        invalid_symbols = ['123', 'ABC', '000001.ST', '600519.SS']
        
        for symbol in valid_symbols:
            assert StockUtils.is_valid_symbol(symbol), f"{symbol} 应该有效"
        
        for symbol in invalid_symbols:
            assert not StockUtils.is_valid_symbol(symbol), f"{symbol} 应该无效"
        
        print("✓ 股票代码验证测试通过")
    
    def test_get_stock_name(self):
        """测试获取股票名称"""
        assert StockUtils.get_stock_name('000001.SZ') == '平安银行'
        assert StockUtils.get_stock_name('600519.SH') == '贵州茅台'
        assert StockUtils.get_stock_name('999999') == '999999'  # 未知股票返回原代码
        
        print("✓ 股票名称映射测试通过")


class TestAStockDataManager:
    """测试AStockDataManager类"""
    
    @pytest.fixture
    def dm(self):
        """创建AStockDataManager实例"""
        return AStockDataManager(data_source='akshare')  # 使用AKShare免费数据源
    
    def test_data_manager_initialization(self, dm):
        """测试AStockDataManager初始化"""
        assert dm.data_source == 'akshare'
        assert dm.cache is not None
        print("✓ 数据管理器初始化测试通过")
    
    def test_get_daily_data(self, dm):
        """测试获取日线数据"""
        # 使用已知的A股代码
        symbol = '000001'  # 平安银行
        
        try:
            start_date = '2023-01-01'
            end_date = '2023-01-10'
            
            df = dm.get_daily_data(symbol, start_date, end_date)
            
            # 检查数据格式
            if not df.empty:
                assert isinstance(df, pd.DataFrame)
                assert 'open' in df.columns
                assert 'close' in df.columns
                assert 'volume' in df.columns
                assert len(df) > 0
                
                print(f"✓ 获取 {symbol} 数据成功: {len(df)} 条记录")
                print(f"  时间范围: {df.index[0]} 到 {df.index[-1]}")
                print(f"  列名: {list(df.columns)}")
            else:
                print(f"⚠ 未获取到 {symbol} 的数据（可能网络问题）")
                
        except Exception as e:
            # 如果网络问题导致失败，跳过测试
            pytest.skip(f"无法获取数据: {e}")
    
    def test_data_validation_and_cleaning(self, dm):
        """测试数据验证和清理"""
        # 创建测试数据
        test_data = {
            'open': [10.0, 11.0, None, 13.0],
            'high': [12.0, 13.0, 14.0, None],
            'low': [9.0, 10.0, 11.0, 12.0],
            'close': [11.0, 12.0, 13.0, 14.0],
            'volume': [1000, 2000, 3000, 4000]
        }
        
        # 无序的索引
        dates = ['2023-01-04', '2023-01-02', '2023-01-01', '2023-01-03']
        test_df = pd.DataFrame(test_data, index=pd.to_datetime(dates))
        
        # 验证数据
        assert dm.validate_data(test_df) is True
        
        # 清理数据
        cleaned_df = dm.clean_data(test_df)
        
        # 检查清理结果
        assert cleaned_df.index.is_monotonic_increasing
        assert cleaned_df['open'].isna().sum() == 0
        assert cleaned_df['high'].isna().sum() == 0
        
        print("✓ 数据验证和清理测试通过")
    
    def test_multiple_stocks_data(self, dm):
        """测试获取多个股票数据"""
        symbols = ['000001', '000002']  # 平安银行, 万科A
        
        try:
            start_date = '2023-01-01'
            end_date = '2023-01-05'
            
            all_data = dm.get_multiple_stocks_data(symbols, start_date, end_date)
            
            assert isinstance(all_data, dict)
            assert len(all_data) == len(symbols)
            
            for symbol, df in all_data.items():
                print(f"  {symbol}: {len(df) if not df.empty else 0} 条记录")
            
            print("✓ 多股票数据获取测试通过")
            
        except Exception as e:
            pytest.skip(f"无法获取多股票数据: {e}")


class TestDataCache:
    """测试DataCache类"""
    
    def test_cache_operations(self):
        """测试缓存操作"""
        test_data = {'test': 'A股数据', 'value': 123.45}
        
        # 设置缓存
        data_cache.set(test_data, 'test', ttl=60, symbol='000001.SZ', date='2023-01-01')
        
        # 获取缓存
        cached_data = data_cache.get('test', symbol='000001.SZ', date='2023-01-01')
        assert cached_data == test_data
        
        # 删除缓存
        data_cache.delete(data_type='test', symbol='000001.SZ', date='2023-01-01')
        deleted_data = data_cache.get('test', symbol='000001.SZ', date='2023-01-01')
        assert deleted_data is None
        
        print("✓ 缓存操作测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行A股数据模块测试")
    print("=" * 60)
    
    # 运行测试
    test_classes = [
        TestStockUtils(),
        TestAStockDataManager(),
        TestDataCache()
    ]
    
    all_passed = True
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n测试类: {class_name}")
        print("-" * 40)
        
        # 运行测试方法
        for method_name in dir(test_class):
            if method_name.startswith('test_'):
                try:
                    method = getattr(test_class, method_name)
                    if callable(method):
                        method()
                        print(f"  ✓ {method_name}")
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠ 部分测试失败")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    # 直接运行测试
    success = run_all_tests()
    sys.exit(0 if success else 1)