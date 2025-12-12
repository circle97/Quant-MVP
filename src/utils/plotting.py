# -*- coding: utf-8 -*-
"""
Matplotlib字体设置工具
"""
import matplotlib
import matplotlib.pyplot as plt
import os
import sys


def setup_chinese_font():
    """设置中文字体"""
    try:
        # 尝试不同的中文字体
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',      # 黑体
            'C:/Windows/Fonts/simsun.ttc',      # 宋体
            'C:/Windows/Fonts/msyh.ttc',        # 微软雅黑
            'C:/Windows/Fonts/msyhbd.ttc',      # 微软雅黑粗体
        ]
        
        # 检查哪些字体可用
        available_fonts = []
        for font_path in font_paths:
            if os.path.exists(font_path):
                available_fonts.append(font_path)
        
        if available_fonts:
            # 使用第一个可用的字体
            font_path = available_fonts[0]
            matplotlib.font_manager.fontManager.addfont(font_path)
            font_name = matplotlib.font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            print(f"✓ 已设置中文字体: {font_name}")
            return True
        else:
            print("⚠ 未找到系统中文字体，使用默认字体")
            # 设置回退方案
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
            return False
            
    except Exception as e:
        print(f"❌ 设置中文字体失败: {e}")
        # 设置回退方案
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
        return False


def setup_plotting_style():
    """设置绘图样式"""
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 150
    plt.rcParams['savefig.bbox'] = 'tight'
    
    # 设置颜色
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=[
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
        '#bcbd22', '#17becf'
    ])


def get_safe_title(title: str) -> str:
    """获取安全的标题（避免中文字体问题）
    
    Args:
        title: 原始标题
        
    Returns:
        安全的标题（可能替换为英文）
    """
    # 如果中文字体设置失败，使用英文标题
    if 'simhei' not in str(plt.rcParams['font.sans-serif']).lower() and \
       'simsun' not in str(plt.rcParams['font.sans-serif']).lower() and \
       'microsoft' not in str(plt.rcParams['font.sans-serif']).lower():
        
        # 替换常见中文标题为英文
        replacements = {
            '上证指数': 'Shanghai Composite',
            '深证成指': 'Shenzhen Component',
            '创业板指': 'ChiNext Index',
            '沪深300': 'CSI 300',
            '收盘价': 'Close Price',
            '成交量': 'Volume',
            '日收益率': 'Daily Return',
            '累计收益率': 'Cumulative Return',
            '技术分析': 'Technical Analysis',
            '移动平均线': 'Moving Average',
            '价格走势': 'Price Trend',
            '实时行情': 'Real-time Quote',
            '股票代码': 'Stock Symbol',
            '涨跌幅': 'Change %',
            '成交额': 'Turnover',
            '主要指数': 'Major Indices',
            '对比': 'Comparison',
            '年': 'Year',
        }
        
        for chinese, english in replacements.items():
            title = title.replace(chinese, english)
    
    return title


if __name__ == '__main__':
    setup_chinese_font()
    setup_plotting_style()
    print("绘图设置完成")