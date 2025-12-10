# Quant-MVP 量化交易系统

## 项目概述
个人量化交易最小可行产品（MVP）系统

## 功能特性
- 多数据源行情获取
- 策略开发与回测
- 模拟交易执行
- 实时监控面板

## 快速开始
1. 安装依赖：\`pip install -r requirements.txt\`
2. 配置环境：复制 \`config/config.example.yaml\` 到 \`config/config.yaml\`
3. 运行示例：\`python scripts/run_strategy.py\`

## 项目结构
\`\`\`
quant-mvp/
├── config/          # 配置文件
├── data/           # 数据文件
├── docs/           # 文档
├── logs/           # 日志文件
├── notebooks/      # Jupyter笔记本
├── scripts/        # 运行脚本
├── src/            # 源代码
│   ├── broker/     # 经纪商接口
│   ├── core/       # 核心模块
│   ├── data/       # 数据模块
│   ├── execution/  # 执行模块
│   ├── strategy/   # 策略模块
│   └── utils/      # 工具函数
├── tests/          # 测试代码
├── requirements.txt
└── README.md
\`\`\`