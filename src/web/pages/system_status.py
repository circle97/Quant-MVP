# -*- coding: utf-8 -*-
"""
系统状态页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys

from src.web.components.sidebar import sidebar

def show_system_status():
    """
    显示系统状态页面
    """
    st.title("系统状态监控")
    
    # 添加配置面板
    with st.expander("系统状态配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 显示配置
            show_resource_chart = st.checkbox("显示资源使用图表", value=True)
            show_component_status = st.checkbox("显示组件状态", value=True)
            show_system_logs = st.checkbox("显示系统日志", value=True)
        
        with col2:
            # 模拟数据参数
            st.markdown("### 模拟数据参数")
            seed = st.number_input("随机种子", min_value=0, max_value=1000, value=42)
            load_level = st.slider("系统负载水平", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
            log_count = st.slider("显示日志数量", min_value=5, max_value=20, value=10)
    
    # 设置随机种子
    np.random.seed(seed)
    
    # 系统信息
    st.subheader("系统信息")
    st.markdown("#### 基本信息")
    st.markdown("展示了系统的基本信息，包括Python版本、Streamlit版本等。")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Python版本", sys.version.split()[0])
        st.metric("Streamlit版本", st.__version__)
    
    # 动态资源使用情况
    with col2:
        cpu_usage = f"{np.random.randint(10, 50) * load_level:.0f}%"
        memory_usage = f"{np.random.randint(30, 70) * load_level:.0f}%"
        st.metric("CPU使用率", cpu_usage)
        st.metric("内存使用率", memory_usage)
    
    with col3:
        st.metric("运行时长", "24h 30m")
        event_count = int(np.random.uniform(500, 2000) * load_level)
        st.metric("事件数量", f"{event_count:,}")
    
    # 组件状态
    if show_component_status:
        st.subheader("组件状态")
        st.markdown("#### 系统组件运行状态")
        st.markdown("展示了系统各个核心组件的运行状态，包括策略引擎、订单管理器、风险管理器和数据服务。")
        
        # 生成动态组件状态
        component_statuses = ["运行中", "异常", "暂停"]
        components = [
            {"组件": "策略引擎", "状态": np.random.choice(component_statuses, p=[0.8, 0.1, 0.1]), "最后活跃": f"{np.random.randint(0, 60)}秒前"},
            {"组件": "订单管理器", "状态": np.random.choice(component_statuses, p=[0.8, 0.1, 0.1]), "最后活跃": f"{np.random.randint(0, 60)}秒前"},
            {"组件": "风险管理器", "状态": np.random.choice(component_statuses, p=[0.8, 0.1, 0.1]), "最后活跃": f"{np.random.randint(0, 60)}秒前"},
            {"组件": "数据服务", "状态": np.random.choice(component_statuses, p=[0.9, 0.05, 0.05]), "最后活跃": f"{np.random.randint(0, 60)}秒前"}
        ]
        
        components_df = pd.DataFrame(components)
        
        # 为组件状态添加颜色
        def color_component_status(val):
            if val == "运行中":
                return 'background-color: #d4edda; color: #155724'  # 运行中绿色
            elif val == "异常":
                return 'background-color: #f8d7da; color: #721c24'  # 异常红色
            elif val == "暂停":
                return 'background-color: #fff3cd; color: #856404'  # 暂停黄色
            else:
                return ''
        
        # 使用map替代applymap以避免警告
        styled_components = components_df.style.map(color_component_status, subset=['状态'])
        st.dataframe(styled_components, width='stretch')
    
    # 资源使用情况
    if show_resource_chart:
        st.subheader("资源使用情况")
        st.markdown("#### 系统资源监控")
        st.markdown("展示了系统资源的使用情况，包括CPU使用率和内存使用率的历史趋势。")
        
        # 生成模拟的资源使用数据
        time_points = pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(hours=24), periods=24, freq='H')
        cpu_usage = [np.random.randint(10, 50) * load_level for _ in range(24)]
        memory_usage = [np.random.randint(30, 70) * load_level for _ in range(24)]
        
        resource_df = pd.DataFrame({
            '时间': time_points,
            'CPU使用率': cpu_usage,
            '内存使用率': memory_usage
        })
        
        # 创建资源使用图表
        fig = px.line(resource_df, x='时间', y=['CPU使用率', '内存使用率'], title='系统资源使用趋势')
        fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_yaxes(tickformat='.0f%%')
        fig.update_traces(hovertemplate='时间: %{x}<br>使用率: %{y}%')
        st.plotly_chart(fig, width='stretch')
    
    # 日志信息
    if show_system_logs:
        st.subheader("系统日志")
        st.markdown("#### 最近系统日志")
        st.markdown("展示了系统的最近日志信息，包括时间、级别和内容，帮助您了解系统的运行情况。")
        
        # 生成模拟日志
        log_levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
        log_messages = [
            "初始化投资组合，初始资金: 100000.00",
            "初始化风险管理器",
            "注册事件处理器: fill -> handle_fill",
            "系统运行正常",
            "执行双均线策略，生成买入信号: AAPL",
            "订单已提交: ORDER_20251216194531",
            "订单已成交: ORDER_20251216194531",
            "执行RSI策略，生成卖出信号: MSFT",
            "更新市场数据",
            "计算投资组合绩效指标",
            "检查风险指标，未发现异常",
            "处理市场事件: MARKET_OPEN",
            "处理市场事件: MARKET_CLOSE",
            "生成每日报告",
            "执行定时任务",
            "清理过期数据",
            "备份数据库",
            "更新策略参数",
            "重启数据服务",
            "检查网络连接"
        ]
        
        logs = []
        for i in range(log_count):
            log_time = pd.Timestamp.now() - pd.Timedelta(minutes=np.random.randint(0, 1440))
            logs.append({
                "时间": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                "级别": np.random.choice(log_levels, p=[0.6, 0.2, 0.15, 0.05]),
                "内容": np.random.choice(log_messages)
            })
        
        logs_df = pd.DataFrame(logs)
        logs_df = logs_df.sort_values(by="时间", ascending=False).reset_index(drop=True)
        
        # 为日志级别添加颜色
        def color_log_level(val):
            if val == "INFO":
                return 'background-color: #d4edda; color: #155724'  # 信息绿色
            elif val == "DEBUG":
                return 'background-color: #cce7ff; color: #004085'  # 调试蓝色
            elif val == "WARNING":
                return 'background-color: #fff3cd; color: #856404'  # 警告黄色
            elif val == "ERROR":
                return 'background-color: #f8d7da; color: #721c24'  # 错误红色
            else:
                return ''
        
        # 使用map替代applymap以避免警告
        styled_logs = logs_df.style.map(color_log_level, subset=['级别'])
        st.dataframe(styled_logs, width='stretch', height=300)
