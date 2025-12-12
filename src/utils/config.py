# -*- coding: utf-8 -*-
"""
配置文件管理模块
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/config.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            # 如果配置文件不存在，使用默认配置
            logger.warning(f"配置文件不存在: {self.config_path}")
            return self._get_default_config()
        
        try:
            # 尝试不同的编码方式
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
            config = None
            
            for encoding in encodings:
                try:
                    with open(self.config_path, 'r', encoding=encoding) as f:
                        config = yaml.safe_load(f)
                    logger.info(f"配置文件加载成功，使用编码: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"使用编码 {encoding} 加载失败: {e}")
                    continue
            
            if config is None:
                raise ValueError("无法使用任何编码加载配置文件")
                
            # 合并默认配置
            default_config = self._get_default_config()
            config = self._merge_config(default_config, config)
            
            return config
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'system': {
                'mode': 'backtest',
                'log_level': 'INFO',
                'timezone': 'Asia/Shanghai'
            },
            'data': {
                'source': 'akshare',
                'cache_dir': './data/cache',
                'update_interval': 300,
                'tushare': {
                    'token': '',
                    'pro_api': False
                },
                'akshare': {
                    'timeout': 10
                },
                'symbols': ['000001.SZ', '000002.SZ', '600519.SH'],
                'start_date': '2020-01-01',
                'end_date': '2023-12-31'
            },
            'strategies': {
                'ma_cross': {
                    'enabled': True,
                    'symbols': ['000001.SZ', '600519.SH'],
                    'params': {
                        'fast_period': 10,
                        'slow_period': 30,
                        'cash_percent': 0.95
                    }
                }
            },
            'trading': {
                'initial_capital': 10000.0,
                'commission': 0.00025,
                'stamp_duty': 0.001,
                'transfer_fee': 0.00002,
                'min_commission': 5.0
            },
            'risk': {
                'max_position_size': 0.2,
                'max_portfolio_size': 0.8,
                'stop_loss': 0.08,
                'take_profit': 0.15,
                'max_drawdown': 0.15
            }
        }
    
    def _merge_config(self, default: Dict, custom: Dict) -> Dict:
        """递归合并配置字典"""
        if custom is None:
            return default
        
        for key, value in custom.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_config(default[key], value)
            else:
                default[key] = value
        return default
    
    def get(self, key: str, default=None):
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔符，如 'data.source'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def save(self, config: Dict = None):
        """保存配置到文件"""
        if config:
            self.config = config
            
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置保存成功: {self.config_path}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            raise


# 全局配置实例
config_manager = ConfigManager()
config = config_manager.config


if __name__ == '__main__':
    # 测试配置管理器
    print("当前配置:")
    print(f"数据源: {config_manager.get('data.source')}")
    print(f"初始资金: {config_manager.get('trading.initial_capital')}")