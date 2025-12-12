#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试config_manager导入
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("开始测试config_manager导入...")

try:
    from src.utils.config import config_manager
    print("✓ config_manager导入成功！")
    print(f"  配置文件路径: {config_manager.config_path}")
    print(f"  数据源配置: {config_manager.get('data.source')}")
    print("导入测试通过！")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    print("导入测试失败！")

print("测试完成！")