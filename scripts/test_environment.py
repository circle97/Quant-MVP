#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
quant-mvp 系统测试脚本
验证环境是否正常
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
        ('numpy', '科学计算'),
        ('pandas', '数据处理'),
        ('matplotlib', '数据可视化'),
        ('yfinance', '金融数据'),
        ('streamlit', 'Web界面'),
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

def test_environment():
    """测试环境配置"""
    print('\n' + '=' * 50)
    print('测试环境配置...')
    print('=' * 50)
    
    print(f'Python版本: {sys.version}')
    print(f'项目根目录: {project_root}')
    print(f'当前工作目录: {os.getcwd()}')
    
    # 检查配置文件
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    if os.path.exists(config_path):
        print(f'✓ 配置文件存在: {config_path}')
    else:
        print(f'⚠ 配置文件不存在，请复制config.example.yaml')
    
    # 检查数据目录
    data_dir = os.path.join(project_root, 'data')
    if os.path.exists(data_dir):
        print(f'✓ 数据目录存在: {data_dir}')
    else:
        print(f'⚠ 数据目录不存在，正在创建...')
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f'✓ 数据目录已创建: {data_dir}')
        except Exception as e:
            print(f'✗ 创建数据目录失败: {e}')
    
    return True

def get_stock_price(symbol='AAPL'):
    """测试获取股票数据"""
    print('\n' + '=' * 50)
    print(f'测试获取 {symbol} 股票数据...')
    print('=' * 50)
    
    try:
        import yfinance as yf
        
        # 获取股票信息
        stock = yf.Ticker(symbol)
        info = stock.info
        
        print(f'股票代码: {symbol}')
        print(f'公司名称: {info.get("longName", "N/A")}')
        print(f'当前价格: {info.get("regularMarketPrice", "N/A")}')
        print(f'市值: {info.get("marketCap", "N/A")}')
        
        # 获取历史数据
        hist = stock.history(period='5d')
        if not hist.empty:
            print(f'\n最近5天数据:')
            print(hist[['Open', 'High', 'Low', 'Close', 'Volume']].tail())
            return True
        else:
            print('⚠ 无法获取历史数据')
            return False
            
    except Exception as e:
        print(f'✗ 获取数据失败: {e}')
        return False

def main():
    """主函数"""
    print('Quant-MVP 环境测试')
    print('=' * 50)
    
    # 运行测试
    test1 = test_imports()
    test2 = test_environment()
    test3 = get_stock_price('AAPL')
    
    print('\n' + '=' * 50)
    print('测试结果汇总:')
    print('=' * 50)
    print(f'包导入测试: {"通过" if test1 else "失败"}')
    print(f'环境配置测试: {"通过" if test2 else "失败"}')
    print(f'数据获取测试: {"通过" if test3 else "失败"}')
    
    if all([test1, test2, test3]):
        print('\n🎉 所有测试通过！环境配置成功！')
        print('接下来可以开始开发量化策略了。')
    else:
        print('\n⚠ 部分测试失败，请检查环境配置。')
        print('常见问题：')
        print('1. 确保虚拟环境已激活')
        print('2. 确保已安装所有依赖：pip install -r requirements.txt')
        print('3. 检查网络连接')
    
    return all([test1, test2, test3])

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)