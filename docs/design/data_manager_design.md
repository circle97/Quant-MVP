# 数据管理模块设计文档

## 1. 模块概述

数据管理模块是Quant-MVP系统的基础组件，负责处理所有与市场数据相关的操作，包括数据获取、存储、清洗、更新和质量检查。该模块设计为可扩展架构，支持多种数据源接入，并提供高效的数据缓存机制，以满足策略回测和实盘交易的需求。

## 2. 设计目标

1. **多数据源支持**：实现对Alpha Vantage、Tushare、本地CSV等多种数据源的统一接入
2. **高效数据缓存**：使用SQLite数据库存储历史数据，减少API调用次数，提高数据访问速度
3. **实时数据更新**：通过定时任务实现行情数据的实时更新
4. **数据质量保障**：提供数据清洗和质量检查机制，确保数据准确性和完整性
5. **统一数据接口**：为上层模块提供统一的数据访问接口，屏蔽不同数据源的差异
6. **可扩展性**：设计模块化架构，支持轻松添加新的数据源和数据类型

## 3. 架构设计

### 3.1 架构层次图

```
+-----------------------------------+
|           数据访问层               |
|  (Strategy, Backtest, Execution)  |
+-----------------------------------+
|           数据管理层               |
|      DataManager, DataCache       |
+-----------------------------------+
|           数据源层                 |
| AlphaVantage, Tushare, LocalCSV   |
+-----------------------------------+
|           存储层                   |
|            SQLite                 |
+-----------------------------------+
```

### 3.2 核心组件

1. **DataFeed**：抽象数据源接口，定义了获取历史数据和实时数据的统一方法
2. **具体数据源实现**：AlphaVantageDataFeed、TushareDataFeed、LocalCSVDataFeed
3. **DataManager**：数据管理中心，负责数据源的选择、数据的获取和分发
4. **DataCache**：数据缓存机制，使用SQLite数据库存储历史数据
5. **DataCleaner**：数据清洗模块，负责处理缺失值、异常值等数据质量问题
6. **DataUpdater**：数据更新模块，使用APScheduler实现定时数据更新

## 4. 核心类和接口

### 4.1 DataFeed (抽象基类)

```python
class DataFeed(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史数据"""
        pass
    
    @abstractmethod
    def get_realtime_data(self, symbol: str) -> dict:
        """获取实时数据"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> list:
        """获取支持的标的列表"""
        pass
```

### 4.2 AlphaVantageDataFeed (具体实现)

```python
class AlphaVantageDataFeed(DataFeed):
    """Alpha Vantage数据源实现"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 实现Alpha Vantage API调用，获取历史数据
        pass
    
    def get_realtime_data(self, symbol: str) -> dict:
        # 实现Alpha Vantage API调用，获取实时数据
        pass
    
    def get_supported_symbols(self) -> list:
        # 返回支持的标的列表
        pass
```

### 4.3 TushareDataFeed (具体实现)

```python
class TushareDataFeed(DataFeed):
    """Tushare数据源实现"""
    
    def __init__(self, token: str):
        self.token = token
        # 初始化Tushare API
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 实现Tushare API调用，获取历史数据
        pass
    
    def get_realtime_data(self, symbol: str) -> dict:
        # 实现Tushare API调用，获取实时数据
        pass
    
    def get_supported_symbols(self) -> list:
        # 返回支持的标的列表
        pass
```

### 4.4 LocalCSVDataFeed (具体实现)

```python
class LocalCSVDataFeed(DataFeed):
    """本地CSV数据源实现"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 从本地CSV文件读取历史数据
        pass
    
    def get_realtime_data(self, symbol: str) -> dict:
        # 本地CSV不支持实时数据，返回最近的历史数据
        pass
    
    def get_supported_symbols(self) -> list:
        # 扫描目录，返回所有可用的CSV文件对应的标的
        pass
```

### 4.5 DataCache

```python
class DataCache:
    """数据缓存类，使用SQLite存储历史数据"""
    
    def __init__(self, db_path: str = "data/quant_mvp.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        # 初始化数据库表结构
        pass
    
    def save_data(self, symbol: str, data: pd.DataFrame, data_type: str = "daily"):
        # 将数据保存到数据库
        pass
    
    def get_data(self, symbol: str, start_date: str, end_date: str, data_type: str = "daily") -> pd.DataFrame:
        # 从数据库获取数据
        pass
    
    def is_data_available(self, symbol: str, start_date: str, end_date: str, data_type: str = "daily") -> bool:
        # 检查数据库中是否存在指定时间段的数据
        pass
    
    def clear_cache(self, symbol: str = None, data_type: str = None):
        # 清除缓存数据
        pass
```

### 4.6 DataCleaner

```python
class DataCleaner:
    """数据清洗类，负责处理数据质量问题"""
    
    def __init__(self):
        pass
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # 执行完整的数据清洗流程
        data = self._handle_missing_values(data)
        data = self._handle_outliers(data)
        data = self._validate_data(data)
        return data
    
    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        # 处理缺失值
        pass
    
    def _handle_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        # 处理异常值
        pass
    
    def _validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        # 验证数据完整性和正确性
        pass
    
    def check_data_quality(self, data: pd.DataFrame) -> dict:
        # 检查数据质量，返回质量报告
        pass
```

### 4.7 DataUpdater

```python
class DataUpdater:
    """数据更新类，使用APScheduler实现定时数据更新"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        # 启动定时任务
        self._add_jobs()
        self.scheduler.start()
    
    def stop(self):
        # 停止定时任务
        self.scheduler.shutdown()
    
    def _add_jobs(self):
        # 添加定时任务
        # 例如：每天收盘后更新日线数据
        self.scheduler.add_job(
            self.data_manager.update_daily_data,
            'cron',
            hour=16,
            minute=30,
            timezone='Asia/Shanghai'
        )
        # 例如：每分钟更新一次实时数据
        self.scheduler.add_job(
            self.data_manager.update_realtime_data,
            'interval',
            minutes=1
        )
```

### 4.8 DataManager

```python
class DataManager:
    """数据管理中心，协调各个数据组件"""
    
    def __init__(self, config: dict):
        self.config = config
        self.data_feeds = {}
        self.data_cache = DataCache(config.get("db_path", "data/quant_mvp.db"))
        self.data_cleaner = DataCleaner()
        self.data_updater = DataUpdater(self)
        
        # 初始化数据源
        self._init_data_feeds()
    
    def _init_data_feeds(self):
        # 根据配置初始化数据源
        for source_name, source_config in self.config.get("data_sources", {}).items():
            if source_name == "alpha_vantage":
                self.data_feeds["alpha_vantage"] = AlphaVantageDataFeed(
                    api_key=source_config["api_key"]
                )
            elif source_name == "tushare":
                self.data_feeds["tushare"] = TushareDataFeed(
                    token=source_config["token"]
                )
            elif source_name == "local_csv":
                self.data_feeds["local_csv"] = LocalCSVDataFeed(
                    data_dir=source_config["data_dir"]
                )
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                          data_type: str = "daily", source: str = None) -> pd.DataFrame:
        """
        获取历史数据，优先从缓存获取，缓存不存在则从数据源获取
        
        Args:
            symbol: 标的代码
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型（daily, minute, tick）
            source: 数据源名称，None表示自动选择
        
        Returns:
            pd.DataFrame: 历史数据
        """
        # 1. 尝试从缓存获取数据
        if self.data_cache.is_data_available(symbol, start_date, end_date, data_type):
            data = self.data_cache.get_data(symbol, start_date, end_date, data_type)
            if not data.empty:
                return data
        
        # 2. 从数据源获取数据
        if source is None:
            # 自动选择数据源
            data_feed = self._select_data_feed(symbol, data_type)
        else:
            data_feed = self.data_feeds.get(source)
            if data_feed is None:
                raise ValueError(f"数据源 {source} 未配置")
        
        # 3. 从数据源获取数据
        data = data_feed.get_historical_data(symbol, start_date, end_date)
        
        # 4. 数据清洗
        data = self.data_cleaner.clean_data(data)
        
        # 5. 保存到缓存
        self.data_cache.save_data(symbol, data, data_type)
        
        return data
    
    def get_realtime_data(self, symbol: str, source: str = None) -> dict:
        """
        获取实时数据
        
        Args:
            symbol: 标的代码
            source: 数据源名称，None表示自动选择
        
        Returns:
            dict: 实时行情数据
        """
        if source is None:
            data_feed = self._select_data_feed(symbol, "realtime")
        else:
            data_feed = self.data_feeds.get(source)
            if data_feed is None:
                raise ValueError(f"数据源 {source} 未配置")
        
        return data_feed.get_realtime_data(symbol)
    
    def _select_data_feed(self, symbol: str, data_type: str) -> DataFeed:
        """自动选择合适的数据源"""
        # 根据标的类型和数据类型选择合适的数据源
        # 实现数据源选择逻辑
        pass
    
    def update_daily_data(self):
        """更新日线数据"""
        # 实现日线数据更新逻辑
        pass
    
    def update_realtime_data(self):
        """更新实时数据"""
        # 实现实时数据更新逻辑
        pass
    
    def start_auto_update(self):
        """启动自动更新"""
        self.data_updater.start()
    
    def stop_auto_update(self):
        """停止自动更新"""
        self.data_updater.stop()
    
    def get_data_quality_report(self, symbol: str, data_type: str = "daily") -> dict:
        """获取数据质量报告"""
        # 实现数据质量报告生成逻辑
        pass
```

## 5. 数据结构

### 5.1 历史数据结构

| 字段名 | 类型 | 描述 |
|-------|------|------|
| datetime | datetime64 | 时间戳 |
| symbol | str | 标的代码 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| volume | int | 成交量 |
| adj_close | float | 复权收盘价 |
| source | str | 数据源 |
| update_time | datetime64 | 更新时间 |

### 5.2 实时数据结构

```python
{
    "symbol": "AAPL",
    "price": 150.25,
    "open": 149.50,
    "high": 151.00,
    "low": 149.00,
    "volume": 12345678,
    "timestamp": "2023-10-01 14:30:00",
    "source": "alpha_vantage"
}
```

### 5.3 数据质量报告结构

```python
{
    "symbol": "AAPL",
    "data_type": "daily",
    "date_range": {
        "start": "2020-01-01",
        "end": "2023-09-30"
    },
    "total_records": 959,
    "missing_values": {
        "open": 0,
        "high": 0,
        "low": 0,
        "close": 0,
        "volume": 0
    },
    "outliers": {
        "price": 5,
        "volume": 3
    },
    "data_coverage": 0.99,
    "last_update": "2023-10-01 16:30:00"
}
```

## 6. 实现细节

### 6.1 数据源优先级策略

1. 对于历史数据，优先从缓存获取，缓存不存在时从配置的主要数据源获取
2. 对于实时数据，直接从实时数据源获取，不进行缓存
3. 当主要数据源不可用时，自动切换到备用数据源

### 6.2 数据更新策略

1. **日线数据**：每天收盘后自动更新（16:30，A股）
2. **分钟数据**：每5分钟更新一次
3. **实时数据**：根据策略需求，可配置为1秒、5秒或1分钟更新一次
4. **数据完整性检查**：每次更新后进行数据完整性检查，确保数据连续

### 6.3 数据清洗规则

1. **缺失值处理**：
   - 对于连续缺失值，使用线性插值或前向填充
   - 对于超过5个连续缺失值的数据点，标记为异常

2. **异常值处理**：
   - 使用3σ原则检测异常值
   - 对于异常价格，使用前后均值替换
   - 对于异常成交量，标记为异常，但保留原始数据

3. **数据验证**：
   - 检查价格逻辑：high >= open, high >= close, low <= open, low <= close
   - 检查成交量非负
   - 检查时间序列连续

### 6.4 性能优化

1. **批量操作**：数据保存和读取采用批量操作，减少数据库IO次数
2. **索引优化**：数据库表建立合适的索引，提高查询速度
3. **数据压缩**：对于历史数据，采用适当的压缩算法存储
4. **异步更新**：数据更新采用异步方式，不阻塞主程序运行

## 7. 依赖关系

| 依赖库 | 版本 | 用途 |
|-------|------|------|
| pandas | 1.3+ | 数据处理和分析 |
| numpy | 1.20+ | 数值计算 |
| sqlite3 | 内置 | 数据存储 |
| APScheduler | 3.9+ | 定时任务调度 |
| requests | 2.26+ | API请求 |
| tushare | 1.2+ | A股数据获取 |

## 8. 测试计划

### 8.1 单元测试

1. **DataFeed接口测试**：测试各数据源实现是否正确实现了DataFeed接口
2. **DataCache测试**：测试数据缓存的保存、读取、检查功能
3. **DataCleaner测试**：测试数据清洗逻辑，包括缺失值处理、异常值处理
4. **DataManager测试**：测试数据获取、更新、质量检查功能

### 8.2 集成测试

1. **多数据源集成测试**：测试系统能否正确切换不同数据源
2. **缓存机制测试**：测试缓存命中率和更新逻辑
3. **实时数据更新测试**：测试定时任务能否正确更新数据

### 8.3 性能测试

1. **数据获取性能**：测试从缓存和从API获取数据的速度
2. **数据存储性能**：测试批量数据存储的速度
3. **并发访问测试**：测试多线程并发访问数据的性能

## 9. 扩展考虑

1. **支持更多数据源**：设计模块化架构，支持轻松添加新的数据源
2. **支持更多数据类型**：如tick数据、level2数据等
3. **分布式数据存储**：支持扩展到PostgreSQL等分布式数据库
4. **数据可视化**：集成数据可视化功能，方便用户查看数据质量
5. **机器学习集成**：支持对数据进行特征工程，为机器学习模型提供数据

## 10. 配置示例

```yaml
data_manager:
  db_path: "data/quant_mvp.db"
  data_sources:
    alpha_vantage:
      api_key: "YOUR_API_KEY"
      priority: 1
    tushare:
      token: "YOUR_TUSHARE_TOKEN"
      priority: 2
    local_csv:
      data_dir: "data/csv"
      priority: 3
  update_schedule:
    daily:
      time: "16:30"
      timezone: "Asia/Shanghai"
    minute:
      interval: 5
      unit: "minutes"
    realtime:
      interval: 1
      unit: "seconds"
  data_quality:
    missing_threshold: 0.05
    outlier_threshold: 3.0
```

## 11. 总结

数据管理模块设计为一个高度可扩展、高性能的数据处理系统，能够满足量化交易系统对数据的各种需求。该模块通过统一的接口设计，屏蔽了不同数据源的差异，为上层模块提供了可靠的数据支持。同时，该模块还提供了数据缓存、清洗和质量检查机制，确保了数据的准确性和完整性。

通过本设计，我们将构建一个功能完善、性能优良的数据管理系统，为Quant-MVP系统的其他模块提供坚实的数据基础。