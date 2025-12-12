#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股数据模块简化测试
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """测试基础包导入"""
    print('=' * 50)
    print('测试Python包导入...')
    print('=' * 50)
    
    packages = [
        ('pandas', '数据处理'),
        ('tushare', 'Tushare数据'),
        ('akshare', 'AKShare数据'),
        ('yaml', '配置文件'),
        ('loguru', '日志'),
    ]
    
    all_success = True
    for package, description in packages:
        try:
            __import__(package)
            print(f'✓ {package:15s} - {description}')
        except ImportError as e:
            print(f'✗ {package:15s} - 导入失败: {e}')
            all_success = False
    
    return all_success

def test_config():
    """测试配置加载"""
    print('\n' + '=' * 50)
    print('测试配置加载...')
    print('=' * 50)
    
    try:
        from src.utils.config import config_manager
        print(f'配置加载成功')
        print(f'数据源: {config_manager.get("data.source")}')
        print(f'初始资金: {config_manager.get("trading.initial_capital")}')
        return True
    except Exception as e:
        print(f'配置加载失败: {e}')
        return False

def test_data_module():
    """测试数据模块"""
    print('\n' + '=' * 50)
    print('测试数据模块导入...')
    print('=' * 50)
    
    try:
        from src.data import stock_utils
        print(f'✓ 股票工具模块导入成功')
        
        # 测试股票代码标准化
        test_symbols = ['000001', '600519', '000001.SZ']
        for symbol in test_symbols:
            normalized, exchange = stock_utils.normalize_symbol(symbol)
            name = stock_utils.get_stock_name(normalized)
            print(f'  {symbol} -> {normalized} ({exchange}) - {name}')
        
        return True
    except Exception as e:
        print(f'数据模块导入失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print('A股数据模块基础测试')
    print('=' * 50)
    
    # 运行测试
    test1 = test_imports()
    test2 = test_config()
    test3 = test_data_module()
    
    print('\n' + '=' * 50)
    print('测试结果汇总:')
    print('=' * 50)
    print('包导入测试: {\"通过\" if test1 else \"失败\"}')
    print('配置加载测试: {\"通过\" if test2 else \"失败\"}')
    print('数据模块测试: {\"通过\" if test3 else \"失败\"}')
    
    if all([test1, test2, test3]):
        print('\n🎉 基础测试通过！可以尝试获取数据了。')
    else:
        print('\n⚠ 部分测试失败，请检查问题。')
    
    return all([test1, test2, test3])

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)