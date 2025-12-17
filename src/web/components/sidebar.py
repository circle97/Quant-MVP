# -*- coding: utf-8 -*-
"""
侧边栏组件
"""
import streamlit as st

def sidebar():
    """生成侧边栏"""
    # 侧边栏设置
    st.sidebar.header("Quant-MVP 监控面板")
    
    # 选择页面
    page = st.sidebar.radio(
        "选择监控页面",
        [
            "总览",
            "投资组合",
            "策略表现",
            "策略对比",
            "风险监控",
            "交易记录",
            "系统状态"
        ]
    )
    
    # 系统状态栏
    st.sidebar.markdown("---")
    st.sidebar.subheader("系统状态")
    st.sidebar.info("运行中")
    
    return page
