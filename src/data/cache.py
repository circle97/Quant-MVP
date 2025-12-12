# -*- coding: utf-8 -*-
"""
数据缓存模块
"""
import sqlite3
import pandas as pd
import pickle
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
from loguru import logger

from ..utils.config import config_manager


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = None):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录，默认为配置中的cache_dir
        """
        if cache_dir is None:
            cache_dir = config_manager.get('data.cache_dir', './data/cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite数据库路径
        self.db_path = self.cache_dir / 'data_cache.db'
        self.conn = None
        self._init_database()
        
        # 内存缓存
        self.memory_cache = {}
        self.memory_cache_ttl = 300  # 5分钟
        
    def _init_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # 创建数据缓存表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_cache (
                cache_key TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                interval TEXT,
                data BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
            ''')
            
            # 创建索引
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol ON data_cache (symbol)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires ON data_cache (expires_at)
            ''')
            
            self.conn.commit()
            logger.info(f'数据缓存数据库初始化完成: {self.db_path}')
            
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')
            raise
    
    def _generate_cache_key(self, data_type: str, **kwargs) -> str:
        """生成缓存键
        
        Args:
            data_type: 数据类型，如 'historical', 'realtime'
            **kwargs: 其他参数
            
        Returns:
            缓存键字符串
        """
        # 将参数排序后转换为字符串
        params_str = json.dumps(kwargs, sort_keys=True)
        
        # 生成MD5哈希
        key_str = f'{data_type}:{params_str}'
        cache_key = hashlib.md5(key_str.encode()).hexdigest()
        
        return cache_key
    
    def get(self, data_type: str, **kwargs) -> Optional[Any]:
        """从缓存获取数据
        
        Args:
            data_type: 数据类型
            **kwargs: 查询参数
            
        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        # 1. 检查内存缓存
        memory_key = self._generate_cache_key(data_type, **kwargs)
        if memory_key in self.memory_cache:
            data, timestamp = self.memory_cache[memory_key]
            if datetime.now().timestamp() - timestamp < self.memory_cache_ttl:
                logger.debug(f'从内存缓存获取数据: {memory_key}')
                return data
        
        # 2. 检查数据库缓存
        cache_key = memory_key  # 使用相同的键
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''SELECT data, expires_at FROM data_cache 
                   WHERE cache_key = ?''',
                (cache_key,)
            )
            
            row = cursor.fetchone()
            if row:
                data_blob, expires_at = row
                
                # 检查是否过期
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        # 数据已过期，删除
                        self.delete(cache_key)
                        return None
                
                # 反序列化数据
                data = pickle.loads(data_blob)
                
                # 存入内存缓存
                self.memory_cache[memory_key] = (data, datetime.now().timestamp())
                
                logger.debug(f'从数据库缓存获取数据: {cache_key}')
                return data
                
        except Exception as e:
            logger.error(f'从缓存获取数据失败: {e}')
        
        return None
    
    def set(self, data: Any, data_type: str, ttl: int = 3600, **kwargs):
        """设置缓存数据
        
        Args:
            data: 要缓存的数据
            data_type: 数据类型
            ttl: 存活时间（秒）
            **kwargs: 查询参数
        """
        try:
            cache_key = self._generate_cache_key(data_type, **kwargs)
            
            # 1. 存入内存缓存
            self.memory_cache[cache_key] = (data, datetime.now().timestamp())
            
            # 2. 存入数据库缓存
            # 序列化数据
            data_blob = pickle.dumps(data)
            
            # 计算过期时间
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO data_cache 
            (cache_key, data_type, symbol, start_date, end_date, interval, data, updated_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cache_key,
                data_type,
                kwargs.get('symbol', ''),
                kwargs.get('start_date', ''),
                kwargs.get('end_date', ''),
                kwargs.get('interval', ''),
                data_blob,
                datetime.now().isoformat(),
                expires_at.isoformat()
            ))
            
            self.conn.commit()
            logger.debug(f'数据已缓存: {cache_key}, TTL: {ttl}秒')
            
        except Exception as e:
            logger.error(f'设置缓存失败: {e}')
    
    def delete(self, cache_key: str = None, **kwargs):
        """删除缓存数据
        
        Args:
            cache_key: 直接指定缓存键
            **kwargs: 或通过参数生成缓存键
        """
        try:
            if cache_key is None:
                cache_key = self._generate_cache_key(**kwargs)
            
            # 从内存缓存删除
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            # 从数据库删除
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM data_cache WHERE cache_key = ?', (cache_key,))
            self.conn.commit()
            
            logger.debug(f'缓存已删除: {cache_key}')
            
        except Exception as e:
            logger.error(f'删除缓存失败: {e}')
    
    def clear_expired(self):
        """清理过期缓存"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                '''DELETE FROM data_cache 
                   WHERE expires_at IS NOT NULL AND expires_at < ?''',
                (datetime.now().isoformat(),)
            )
            deleted_count = cursor.rowcount
            self.conn.commit()
            
            logger.info(f'已清理 {deleted_count} 条过期缓存')
            
        except Exception as e:
            logger.error(f'清理过期缓存失败: {e}')
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            cursor = self.conn.cursor()
            
            # 总缓存数量
            cursor.execute('SELECT COUNT(*) FROM data_cache')
            total_count = cursor.fetchone()[0]
            
            # 按数据类型统计
            cursor.execute('''
            SELECT data_type, COUNT(*) as count 
            FROM data_cache 
            GROUP BY data_type
            ''')
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 过期缓存数量
            cursor.execute('''
            SELECT COUNT(*) FROM data_cache 
            WHERE expires_at IS NOT NULL AND expires_at < ?
            ''', (datetime.now().isoformat(),))
            expired_count = cursor.fetchone()[0]
            
            stats = {
                'total_count': total_count,
                'memory_cache_size': len(self.memory_cache),
                'type_stats': type_stats,
                'expired_count': expired_count,
                'cache_dir': str(self.cache_dir),
                'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f'获取缓存统计失败: {e}')
            return {}
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info('缓存数据库连接已关闭')


# 创建全局缓存实例
data_cache = DataCache()