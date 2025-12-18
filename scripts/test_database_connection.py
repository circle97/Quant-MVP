#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
用于测试MySQL和Redis连接是否正常
"""

import sys
import os
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import config_manager
from src.core.transaction_manager import TransactionManager


def test_mysql_connection():
    """
    测试MySQL连接
    """
    logger.info("开始测试MySQL连接...")
    
    # 从配置文件获取数据库配置
    db_config = config_manager.get('database', {
        'type': 'sqlite',
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'username': 'root',
            'password': '',
            'database': 'quant_mvp',
            'charset': 'utf8mb4'
        }
    })
    
    if db_config['type'] == 'mysql':
        mysql = db_config['mysql']
        from urllib.parse import quote_plus
        encoded_password = quote_plus(mysql['password'])
        db_url = f"mysql+pymysql://{mysql['username']}:{encoded_password}@{mysql['host']}:{mysql['port']}/{mysql['database']}?charset={mysql['charset']}"
        
        try:
            from sqlalchemy import create_engine
            engine = create_engine(db_url, echo=False)
            conn = engine.connect()
            conn.close()
            logger.success(f"MySQL连接成功！连接到: {mysql['host']}:{mysql['port']}/{mysql['database']}")
            return True
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            return False
    else:
        logger.warning("当前配置为SQLite，跳过MySQL连接测试")
        return True


def test_redis_connection():
    """
    测试Redis连接
    """
    logger.info("开始测试Redis连接...")
    
    # 从配置文件获取Redis配置
    redis_config = config_manager.get('redis', {
        'enable': True,
        'host': 'localhost',
        'port': 6379,
        'password': '',
        'db': 0
    })
    
    if redis_config['enable']:
        try:
            import redis
            redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                password=redis_config['password'],
                db=redis_config['db']
            )
            redis_client.ping()
            logger.success(f"Redis连接成功！连接到: {redis_config['host']}:{redis_config['port']} (DB: {redis_config['db']})")
            return True
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False
    else:
        logger.warning("Redis未启用，跳过Redis连接测试")
        return True


def test_transaction_manager():
    """
    测试TransactionManager初始化
    """
    logger.info("开始测试TransactionManager初始化...")
    
    try:
        transaction_manager = TransactionManager()
        logger.success("TransactionManager初始化成功！")
        return True
    except Exception as e:
        logger.error(f"TransactionManager初始化失败: {e}")
        return False


def main():
    """
    主函数
    """
    logger.info("===== 数据库连接测试开始 =====")
    
    # 测试MySQL连接
    mysql_ok = test_mysql_connection()
    
    # 测试Redis连接
    redis_ok = test_redis_connection()
    
    # 测试TransactionManager初始化
    tm_ok = test_transaction_manager()
    
    logger.info("===== 数据库连接测试结束 =====")
    
    if mysql_ok and redis_ok and tm_ok:
        logger.success("所有测试通过！数据库连接正常")
        return 0
    else:
        logger.error("部分测试失败，请检查配置和服务状态")
        return 1


if __name__ == "__main__":
    # 设置日志格式
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
    
    sys.exit(main())
