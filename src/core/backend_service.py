# -*- coding: utf-8 -*-
"""
后台服务 - 负责交易引擎的后台运行和管理
"""
import os
import sys
import time
import signal
import logging
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

# 添加项目根目录到Python路径，确保能正确导入src模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 尝试导入daemon模块，仅在Unix系统上可用
is_windows = sys.platform.startswith('win')
try:
    if not is_windows:
        import daemon
        from daemon import pidfile
        has_daemon = True
    else:
        has_daemon = False
        logger.warning("Windows系统不支持daemon模式，将使用前台模式")
except ImportError:
    has_daemon = False
    logger.warning("未找到daemon模块，将使用前台模式")

from src.core.event import event_engine
from src.core.execution_engine import ExecutionEngine
from src.core.portfolio import Portfolio
from src.strategy.strategy_engine import StrategyEngine
from src.core.risk_manager import RiskManager
from src.core.state_manager import StateManager
from src.core.transaction_manager import TransactionManager
from src.api.api_server import APIServer
from src.utils.config import config_manager


class BackendService:
    """
    后台服务类 - 管理交易引擎的启动、停止和状态监控
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化后台服务
        
        Args:
            config: 服务配置
        """
        # 基础配置
        self.config = config or {
            'mode': 'simulation',
            'log_file': 'logs/backend_service.log'
        }
        
        self.running = False
        self.start_time = None
        
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
            },
            'sqlite': {
                'path': './trading.db'
            }
        })
        
        # 根据数据库类型构建连接URL
        if db_config['type'] == 'mysql':
            # MySQL连接URL，需要对密码进行URL编码
            mysql = db_config['mysql']
            from urllib.parse import quote_plus
            encoded_password = quote_plus(mysql['password'])
            db_url = f"mysql+pymysql://{mysql['username']}:{encoded_password}@{mysql['host']}:{mysql['port']}/{mysql['database']}?charset={mysql['charset']}"
        else:
            # SQLite连接URL
            sqlite_path = db_config['sqlite']['path']
            db_url = f"sqlite:///{sqlite_path}"
        
        # 从配置文件获取Redis配置
        redis_config = config_manager.get('redis', {
            'enable': True,
            'host': 'localhost',
            'port': 6379,
            'password': '',
            'db': 0
        })
        
        # 初始化组件
        self.transaction_manager = TransactionManager(
            db_url=db_url,
            redis_config={
                'host': redis_config['host'],
                'port': redis_config['port'],
                'password': redis_config['password'],
                'db': redis_config['db']
            }
        )
        self.state_manager = StateManager(transaction_manager=self.transaction_manager)
        
        # 获取初始资金配置
        initial_capital = config_manager.get('trading.initial_capital', 100000.0)
        self.portfolio = Portfolio(initial_capital=initial_capital)
        
        self.execution_engine = ExecutionEngine(config={
            'mode': self.config['mode'],
            'risk': {}
        })
        self.strategy_engine = StrategyEngine()
        self.risk_manager = RiskManager()
        
        # 初始化API服务器
        self.api_server = APIServer(
            execution_engine=self.execution_engine,
            portfolio=self.portfolio,
            strategy_engine=self.strategy_engine,
            state_manager=self.state_manager
        )
        
        # 配置日志
        self._setup_logging()
        
        logger.info("初始化后台服务完成")
    
    def _setup_logging(self):
        """配置日志"""
        # 确保日志目录存在
        log_dir = os.path.dirname(self.config['log_file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置loguru日志
        logger.add(
            self.config['log_file'],
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            level="INFO"
        )
        logger.info(f"日志配置完成，日志文件: {self.config['log_file']}")
    
    def start(self):
        """
        启动后台服务
        """
        if self.running:
            logger.warning("后台服务已在运行中")
            return False
        
        logger.info("开始启动后台服务")
        
        try:
            # 注册信号处理
            self._register_signal_handlers()
            
            # 恢复系统状态
            self.state_manager.restore_state(
                execution_engine=self.execution_engine,
                portfolio=self.portfolio
            )
            
            # 设置组件间的引用
            self.execution_engine.set_portfolio(self.portfolio)
            
            # 启动事件引擎
            event_engine.start()
            logger.info("事件引擎启动成功")
            
            # 启动策略引擎
            self.strategy_engine.start()
            logger.info("策略引擎启动成功")
            
            # 启动执行引擎（已在初始化时启动）
            logger.info("执行引擎启动成功")
            
            # 启动API服务器
            self.api_server.start()
            logger.info("API服务器启动成功")
            
            # 标记服务为运行状态
            self.running = True
            self.start_time = datetime.now()
            
            logger.info("后台服务启动完成")
            return True
        except Exception as e:
            logger.error(f"启动后台服务失败: {e}")
            self.stop()
            return False
    
    def stop(self):
        """
        停止后台服务
        """
        if not self.running:
            logger.warning("后台服务未在运行中")
            return False
        
        logger.info("开始停止后台服务")
        
        try:
            # 保存系统状态
            self.state_manager.save_state(
                execution_engine=self.execution_engine,
                portfolio=self.portfolio
            )
            
            # 停止策略引擎
            self.strategy_engine.stop()
            logger.info("策略引擎停止成功")
            
            # 停止事件引擎
            event_engine.stop()
            logger.info("事件引擎停止成功")
            
            # 停止API服务器
            self.api_server.stop()
            logger.info("API服务器停止成功")
            
            # 标记服务为停止状态
            self.running = False
            self.start_time = None
            
            logger.info("后台服务停止完成")
            return True
        except Exception as e:
            logger.error(f"停止后台服务失败: {e}")
            return False
    
    def restart(self):
        """
        重启后台服务
        """
        logger.info("开始重启后台服务")
        
        # 停止服务
        self.stop()
        
        # 短暂延迟后启动服务
        time.sleep(1)
        
        # 启动服务
        return self.start()
    
    def get_status(self) -> Dict:
        """
        获取服务状态
        
        Returns:
            服务状态信息
        """
        status = {
            'running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': int((datetime.now() - self.start_time).total_seconds()) if self.start_time else 0,
            'components': {
                'event_engine': event_engine.running,
                'strategy_engine': self.strategy_engine.running,
                'execution_engine': True  # 执行引擎没有运行状态标志
            },
            'portfolio': self.portfolio.get_portfolio_summary()
        }
        return status
    
    def _register_signal_handlers(self):
        """
        注册信号处理器
        """
        def signal_handler(signum, frame):
            """信号处理函数"""
            logger.info(f"收到信号 {signum}，准备停止服务")
            self.stop()
            sys.exit(0)
        
        # 注册SIGINT和SIGTERM信号
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("信号处理器注册完成")
    
    def run_forever(self):
        """
        永久运行服务，直到收到停止信号（前台模式）
        """
        if not self.start():
            logger.error("启动服务失败，无法进入永久运行模式")
            return
        
        logger.info("服务进入永久运行模式，按 Ctrl+C 停止")
        
        try:
            while self.running:
                # 定期检查状态
                time.sleep(1)
                
                # 每60秒保存一次系统状态
                if self.start_time and (datetime.now() - self.start_time).total_seconds() % 60 == 0:
                    self.state_manager.save_state(
                        execution_engine=self.execution_engine,
                        portfolio=self.portfolio
                    )
        except KeyboardInterrupt:
            logger.info("收到键盘中断信号，停止服务")
            self.stop()
        except Exception as e:
            logger.error(f"服务运行出错: {e}")
            self.stop()
    
    def run_daemon(self):
        """
        以守护进程方式运行服务
        注意：daemon模式仅在Unix/Linux系统上支持，Windows系统将自动切换到前台模式
        """
        if not has_daemon:
            logger.warning("守护进程模式不可用，将使用前台模式运行")
            self.run_forever()
            return
        
        try:
            # 确保PID目录存在
            pid_dir = os.path.dirname(self.config.get('pid_file', 'logs/backend_service.pid'))
            if pid_dir and not os.path.exists(pid_dir):
                os.makedirs(pid_dir)
            
            pid_file_path = self.config.get('pid_file', 'logs/backend_service.pid')
            
            logger.info(f"准备以守护进程方式启动服务，PID文件: {pid_file_path}")
            
            # 配置daemon上下文
            context = daemon.DaemonContext(
                working_directory=os.getcwd(),
                umask=0o002,
                pidfile=pidfile.TimeoutPIDLockFile(pid_file_path),
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            
            with context:
                # 重新配置日志，确保日志输出到文件
                self._setup_logging()
                
                # 启动服务
                self.run_forever()
        except Exception as e:
            logger.error(f"启动守护进程失败: {e}")
            logger.warning("将切换到前台模式运行")
            self.run_forever()


if __name__ == "__main__":
    # 简单的命令行接口
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="交易引擎后台服务")
    parser.add_argument("action", choices=["start", "stop", "restart", "status"], help="服务操作")
    parser.add_argument("--mode", choices=["simulation", "live"], default="simulation", help="运行模式")
    parser.add_argument("--daemon", action="store_true", help="以守护进程方式运行")
    parser.add_argument("--pid-file", default="logs/backend_service.pid", help="PID文件路径")
    parser.add_argument("--log-file", default="logs/backend_service.log", help="日志文件路径")
    
    args = parser.parse_args()
    
    # 创建服务实例
    config = {
        'mode': args.mode,
        'pid_file': args.pid_file,
        'log_file': args.log_file
    }
    service = BackendService(config=config)
    
    # 执行操作
    if args.action == "start":
        if args.daemon:
            service.run_daemon()
        else:
            service.run_forever()
    elif args.action == "stop":
        service.stop()
    elif args.action == "restart":
        service.restart()
    elif args.action == "status":
        status = service.get_status()
        print(f"服务状态: {status}")