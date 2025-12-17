# -*- coding: utf-8 -*-
"""
风险监控页面
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.web.components.data_fetcher import get_real_risk_metrics

def show_risk_monitoring():
    """显示风险监控页面"""
    st.title("风险监控")
    
    # 添加配置面板
    with st.expander("风险配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 风险指标配置
            st.markdown("### 风险指标参数")
            volatility_threshold = st.slider("波动率警戒阈值", min_value=0.1, max_value=0.5, value=0.2, step=0.05)
            max_drawdown_threshold = st.slider("最大回撤警戒阈值", min_value=-0.2, max_value=-0.05, value=-0.1, step=0.05)
            var_95_threshold = st.slider("VaR 95%警戒阈值", min_value=-0.05, max_value=-0.01, value=-0.03, step=0.01)
        
        with col2:
            # 模拟数据参数
            st.markdown("### 模拟数据参数")
            seed = st.number_input("随机种子", min_value=0, max_value=1000, value=42)
            risk_level = st.slider("风险水平", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    
    # 设置随机种子
    np.random.seed(seed)
    
    # 第一行：风险指标概览
    st.subheader("风险指标概览")
    st.markdown("#### 核心风险指标")
    st.markdown("展示了投资组合的核心风险指标，包括波动率、夏普比率、最大回撤、VaR和卡玛比率，帮助您全面了解风险水平。")
    
    # 获取风险指标
    risk_metrics = get_real_risk_metrics()
    
    # 应用风险水平调整
    adjusted_metrics = {
        "volatility": risk_metrics["volatility"] * risk_level,
        "sharpe_ratio": risk_metrics["sharpe_ratio"] / risk_level,
        "max_drawdown": risk_metrics["max_drawdown"] * risk_level,
        "var_95": risk_metrics["var_95"] * risk_level,
        "var_99": risk_metrics["var_99"] * risk_level,
        "calmar_ratio": risk_metrics["calmar_ratio"] / risk_level
    }
    
    # 组织风险指标为两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("波动率", f"{adjusted_metrics['volatility']:.2%}")
        st.markdown("**波动率**：衡量投资组合收益的波动程度，反映了投资组合的风险水平。")
        st.metric("夏普比率", f"{adjusted_metrics['sharpe_ratio']:.2f}")
        st.markdown("**夏普比率**：衡量每单位风险所获得的超额收益，越高越好。")
        st.metric("最大回撤", f"{adjusted_metrics['max_drawdown']:.2%}")
        st.markdown("**最大回撤**：衡量投资组合从峰值到谷值的最大损失比例，反映了极端风险。")
    
    with col2:
        st.metric("VaR 95%", f"{adjusted_metrics['var_95']:.2%}")
        st.markdown("**VaR 95%**：在95%置信水平下，投资组合单日可能的最大损失。")
        st.metric("VaR 99%", f"{adjusted_metrics['var_99']:.2%}")
        st.markdown("**VaR 99%**：在99%置信水平下，投资组合单日可能的最大损失。")
        st.metric("卡玛比率", f"{adjusted_metrics['calmar_ratio']:.2f}")
        st.markdown("**卡玛比率**：衡量年化收益率与最大回撤的比值，反映了风险调整后的收益能力。")
    
    # 第二行：风险预警和限制
    st.subheader("风险预警")
    st.markdown("#### 风险指标监控")
    st.markdown("展示了各项风险指标的当前值与阈值对比，当指标接近阈值时会发出预警，帮助您及时控制风险。")
    
    # 计算风险预警状态
    def get_risk_status(value, threshold, is_lower_better=True):
        if is_lower_better:
            if value <= threshold:
                return "警告"
            else:
                return "正常"
        else:
            if value >= threshold:
                return "警告"
            else:
                return "正常"
    
    # 生成风险预警数据
    risk_alerts = [
        {"指标": "最大回撤", "当前值": f"{adjusted_metrics['max_drawdown']:.2%}", "阈值": f"{max_drawdown_threshold:.2%}", "状态": get_risk_status(adjusted_metrics['max_drawdown'], max_drawdown_threshold)},
        {"指标": "波动率", "当前值": f"{adjusted_metrics['volatility']:.2%}", "阈值": f"{volatility_threshold:.2%}", "状态": get_risk_status(adjusted_metrics['volatility'], volatility_threshold)},
        {"指标": "VaR 95%", "当前值": f"{adjusted_metrics['var_95']:.2%}", "阈值": f"{var_95_threshold:.2%}", "状态": get_risk_status(adjusted_metrics['var_95'], var_95_threshold)},
        {"指标": "单日亏损", "当前值": f"{np.random.normal(-0.01, 0.01) * risk_level:.2%}", "阈值": "-3.00%", "状态": get_risk_status(np.random.normal(-0.01, 0.01) * risk_level, -0.03)}
    ]
    
    alerts_df = pd.DataFrame(risk_alerts)
    
    # 为状态添加颜色
    def color_status(val):
        if val == "正常":
            return 'background-color: #d4edda; color: #155724'
        elif val == "警告":
            return 'background-color: #f8d7da; color: #721c24'
        else:
            return ''
    
    styled_alerts = alerts_df.style.map(color_status, subset=['状态'])
    st.dataframe(styled_alerts, width='stretch')
    
    # 第三行：风险暴露分析
    st.subheader("风险暴露分析")
    st.markdown("#### 资产类别风险分布")
    st.markdown("展示了投资组合在不同资产类别上的风险暴露情况，帮助您了解风险的主要来源。")
    
    # 生成模拟的风险暴露数据
    base_exposure = [
        {"资产类别": "股票", "占比": 0.75, "风险贡献": 0.80},
        {"资产类别": "债券", "占比": 0.15, "风险贡献": 0.10},
        {"资产类别": "现金", "占比": 0.10, "风险贡献": 0.05}
    ]
    
    # 应用随机扰动
    exposure_data = []
    for asset in base_exposure:
        exposure_data.append({
            "资产类别": asset["资产类别"],
            "占比": max(0, min(1, asset["占比"] + np.random.normal(0, 0.05))),
            "风险贡献": max(0, min(1, asset["风险贡献"] + np.random.normal(0, 0.05)))
        })
    
    # 归一化占比
    total_ratio = sum(item["占比"] for item in exposure_data)
    for item in exposure_data:
        item["占比"] /= total_ratio
    
    # 归一化风险贡献
    total_risk = sum(item["风险贡献"] for item in exposure_data)
    for item in exposure_data:
        item["风险贡献"] /= total_risk
    
    exposure_df = pd.DataFrame(exposure_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 风险暴露饼图
        fig = px.pie(exposure_df, values='占比', names='资产类别', title='资产配置')
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_traces(textinfo='label+percent')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        # 风险贡献条形图
        fig = px.bar(exposure_df, x='资产类别', y='风险贡献', title='风险贡献')
        fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        fig.update_yaxes(tickformat='.1%')
        fig.update_traces(hovertemplate='资产类别: %{x}<br>风险贡献: %{y:.2%}')
        st.plotly_chart(fig, width='stretch')
    
    # 第四行：风险趋势分析
    st.subheader("风险趋势分析")
    st.markdown("#### 波动率与最大回撤趋势")
    st.markdown("展示了投资组合过去30天的波动率和最大回撤变化趋势，帮助您了解风险的动态变化。")
    
    # 生成模拟的风险趋势数据
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    base_volatility = 0.15
    base_drawdown = -0.08
    
    # 确保数据点数量与日期数量一致
    days_count = len(dates)
    volatility_trend = [base_volatility * risk_level * (1 + np.random.normal(0, 0.1)) for _ in range(days_count)]
    drawdown_trend = [base_drawdown * risk_level * (1 + np.random.normal(0, 0.1)) for _ in range(days_count)]
    
    trend_df = pd.DataFrame({
        '日期': dates,
        '波动率': volatility_trend,
        '最大回撤': drawdown_trend
    })
    
    fig = px.line(trend_df, x='日期', y=['波动率', '最大回撤'], title='风险趋势')
    fig.update_layout(height=350, margin=dict(t=30, b=0, l=0, r=0))
    fig.update_yaxes(tickformat='.1%')
    fig.update_traces(hovertemplate='日期: %{x}<br>值: %{y:.2%}')
    st.plotly_chart(fig, width='stretch')
