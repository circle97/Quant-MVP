# -*- coding: utf-8 -*-
"""
策略调度器 - 负责策略的定时执行
"""
from typing import Dict, Any
from datetime import datetime
from loguru import logger

from apscheduler.schedulers.background import BackgroundScheduler
from src.core.event import TimerEvent, event_engine


class StrategyScheduler:
    """策略调度器，负责策略的定时执行"""
    
    def __init__(self, strategy_engine):
        self.strategy_engine = strategy_engine
        self.scheduler = BackgroundScheduler()
        self.running = False
        
        logger.info("初始化策略调度器")
    
    def start(self):
        """启动调度器"""
        if not self.running:
            self.running = True
            self.scheduler.start()
            logger.info("启动策略调度器")
    
    def stop(self):
        """停止调度器"""
        if self.running:
            self.running = False
            self.scheduler.shutdown()
            logger.info("停止策略调度器")
    
    def add_strategy_schedule(self, strategy_name: str, schedule_type: str, **kwargs):
        """添加策略调度
        
        Args:
            strategy_name: 策略名称
            schedule_type: 调度类型 ('cron', 'interval', 'date')
            **kwargs: 调度参数
        """
        def _run_strategy():
            strategy = self.strategy_engine.get_strategy(strategy_name)
            if strategy and strategy.running and not strategy.paused:
                # 触发策略的定时器事件
                timer_event = TimerEvent(interval=0, timestamp=datetime.now())
                event_engine.put(timer_event)
        
        # 添加调度任务
        if schedule_type == 'cron':
            self.scheduler.add_job(_run_strategy, 'cron', **kwargs)
        elif schedule_type == 'interval':
            self.scheduler.add_job(_run_strategy, 'interval', **kwargs)
        elif schedule_type == 'date':
            self.scheduler.add_job(_run_strategy, 'date', **kwargs)
        
        logger.info(f"添加策略调度: {strategy_name} ({schedule_type})")
    
    def remove_strategy_schedule(self, job_id: str):
        """移除策略调度"""
        self.scheduler.remove_job(job_id)
        logger.info(f"移除策略调度: {job_id}")
    
    def get_all_schedules(self):
        """获取所有调度任务"""
        return self.scheduler.get_jobs()
