# 策略执行引擎架构设计

## 🎯 核心目标

实现一个强大、灵活、可扩展的策略执行引擎，支持：

1. **灵活的股票范围选择** - 全量股票、行业筛选、概念选择、指数成分股、自定义股票池
2. **智能数据获取与组装** - 按因子需求实时从Tushare拉取数据，支持缓存和并发优化
3. **完整的执行日志** - 提供详细的执行过程监控，让用户了解每个步骤的进展

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        策略执行引擎架构                           │
├─────────────────────────────────────────────────────────────────┤
│  🌐 Frontend Layer                                             │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐      │
│  │ 股票范围选择UI │ │ 实时执行监控UI │ │ 日志查看组件   │      │
│  └────────────────┘ └────────────────┘ └────────────────┘      │
├─────────────────────────────────────────────────────────────────┤
│  🔌 API Gateway Layer                                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ /strategy-execution/* - 策略执行API接口                      │ │
│  │ • POST /{id}/execute - 异步执行策略                         │ │
│  │ • GET /executions/{id}/progress - 获取执行进度              │ │
│  │ • GET /executions/{id}/logs - 获取执行日志                  │ │
│  │ • POST /validate-filter - 验证筛选条件                      │ │
│  │ • GET /scopes - 获取可用股票范围选项                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Business Logic Layer                                       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │ 执行控制器    │ │ 股票筛选器    │ │ 数据获取器    │        │
│  │ ExecutionEngine│ │ StockFilter   │ │ DataFetcher   │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │ 因子计算器    │ │ 股票选择器    │ │ 日志记录器    │        │
│  │ FactorCalc    │ │ StockSelector │ │ Logger        │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │ 进度跟踪器    │ │ 缓存管理器    │ │ 错误处理器    │        │
│  │ ProgressTracker│ │ CacheService  │ │ ErrorHandler  │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
├─────────────────────────────────────────────────────────────────┤
│  💾 Data Access Layer                                          │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│  │ Tushare API   │ │ 本地数据库    │ │ 因子库        │        │
│  │ 实时数据拉取  │ │ 策略执行记录  │ │ 因子定义管理  │        │
│  └───────────────┘ └───────────────┘ └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件详解

### 1. 策略执行引擎 (StrategyExecutionEngine)

**职责**: 策略执行的总控制器

**核心功能**:
- 执行流程编排：6个关键阶段的顺序执行
- 并发控制：管理同时执行的策略数量
- 状态管理：跟踪执行状态和进度
- 错误处理：异常捕获和恢复机制

**执行阶段**:
```python
1. initialization (5%)      - 初始化验证
2. stock_filtering (10%)    - 股票池筛选
3. data_fetching (40%)      - 数据获取
4. factor_calculation (35%) - 因子计算
5. ranking_selection (8%)   - 排序选股
6. finalization (2%)        - 结果整理
```

### 2. 股票筛选器 (StockFilter)

**支持的筛选范围**:
```python
class StockScope:
    ALL = "all"                # 全部A股（约5000只）
    INDUSTRY = "industry"      # 按申万行业分类
    CONCEPT = "concept"        # 按概念主题分类
    INDEX = "index"            # 指数成分股
    CUSTOM = "custom"          # 用户自定义股票列表
```

**筛选条件**:
- **市场类型**: 主板、中小板、创业板、科创板、北交所
- **基础指标**: 市值范围、股价范围、换手率范围
- **特殊条件**: 排除ST、排除新股、排除停牌
- **行业概念**: 指定包含/排除的行业和概念

### 3. 数据获取器 (DataFetcher)

**智能数据获取策略**:
```python
async def fetch_stock_data(self, stock_codes, required_fields, trade_date):
    """
    智能数据获取流程:
    1. 分析因子需求，确定所需数据字段
    2. 检查缓存，减少API调用
    3. 分批获取，避免API限制
    4. 并发处理，提升获取速度
    5. 数据验证，确保质量
    """
```

**缓存策略**:
- **L1缓存**: 内存缓存，1小时有效期
- **键值设计**: `stock_data_{date}_{fields_hash}`
- **淘汰策略**: LRU算法，最大1000项
- **命中率监控**: 实时统计缓存效率

**Tushare集成**:
```python
# 根据因子需求动态获取字段
required_fields = await self._analyze_factor_requirements(strategy)

# 分批API调用，避免限制
batch_size = 100  # 每批100只股票
for batch in batches:
    data = await tushare_service.get_daily_data(
        ts_codes=batch,
        fields=required_fields,
        trade_date=execution_date
    )
```

### 4. 因子计算器 (FactorCalculator)

**计算引擎**:
```python
async def calculate_factors(self, strategy, stock_data):
    """
    因子计算流程:
    1. 遍历策略中的启用因子
    2. 获取因子定义和公式
    3. 准备计算所需数据
    4. 执行因子计算公式
    5. 统计计算结果和性能
    """
```

**支持的因子类型**:
- **技术指标**: MA、RSI、MACD、布林带等
- **基本面因子**: PE、PB、ROE、ROA等  
- **量价因子**: 成交量、换手率、价格动量等
- **自定义因子**: 用户编写的Python公式

### 5. 执行日志系统 (ExecutionLogger)

**日志级别**:
```python
class LogLevel:
    INFO = "info"         # 一般信息
    WARNING = "warning"   # 警告信息
    ERROR = "error"       # 错误信息
    DEBUG = "debug"       # 调试信息
```

**日志内容**:
```python
class ExecutionLog:
    timestamp: datetime   # 时间戳
    level: LogLevel      # 日志级别
    stage: str           # 执行阶段
    message: str         # 日志消息
    details: dict        # 详细信息
    progress: float      # 进度百分比
```

### 6. 进度跟踪器 (ProgressTracker)

**阶段权重分配**:
```python
stage_weights = {
    "initialization": 5,        # 初始化
    "stock_filtering": 10,      # 股票筛选
    "data_fetching": 40,        # 数据获取（最耗时）
    "factor_calculation": 35,   # 因子计算
    "ranking_selection": 8,     # 排序选股
    "finalization": 2          # 结果整理
}
```

**实时进度计算**:
```python
def get_overall_progress(self) -> float:
    """加权计算总体进度"""
    weighted_progress = sum(
        stage.progress * weight 
        for stage, weight in stage_weights.items()
    )
    return weighted_progress / sum(stage_weights.values())
```

## 📊 数据流设计

### 输入数据流
```
用户选择策略 → 配置股票范围 → 设置筛选条件 → 提交执行请求
      ↓
股票池筛选 → 获取股票列表 → 分析因子需求 → 确定数据字段
      ↓
Tushare API调用 → 数据获取 → 缓存存储 → 数据验证
      ↓
因子计算 → 得分计算 → 权重合成 → 排序筛选
      ↓
结果输出 → 数据库存储 → 前端展示
```

### 执行状态流
```
PENDING → RUNNING → DATA_FETCHING → FACTOR_CALCULATING 
   ↓         ↓            ↓              ↓
RANKING → FILTERING → COMPLETED/FAILED/CANCELLED
```

## 🎨 前端界面设计

### 1. 股票范围选择界面

**卡片式选择**:
```typescript
const STOCK_SCOPES = [
  { 
    value: 'all', 
    label: '全部股票', 
    description: '所有A股市场股票',
    icon: '🌍'
  },
  { 
    value: 'industry', 
    label: '按行业筛选', 
    description: '选择特定行业的股票',
    icon: '🏭'
  },
  // ... 更多选项
];
```

**动态选项加载**:
```typescript
// 根据选择的范围动态加载相应选项
useEffect(() => {
  if (scope === 'industry') {
    loadIndustries();
  } else if (scope === 'concept') {
    loadConcepts();
  }
}, [scope]);
```

### 2. 实时执行监控

**进度条展示**:
```tsx
<div className="w-full bg-base-300 rounded-full h-2">
  <div 
    className="bg-primary h-2 rounded-full transition-all duration-300"
    style={{ width: `${progress}%` }}
  />
</div>
```

**状态指示器**:
```tsx
const STATUS_MAP = {
  'data_fetching': { label: '数据获取中', color: 'text-info' },
  'factor_calculating': { label: '因子计算中', color: 'text-info' },
  'completed': { label: '执行完成', color: 'text-success' },
  'failed': { label: '执行失败', color: 'text-error' }
};
```

### 3. 日志监控界面

**实时日志流**:
```tsx
// 1秒轮询获取最新日志
useEffect(() => {
  const interval = setInterval(() => {
    if (executionId && isExecuting) {
      fetchExecutionLogs();
    }
  }, 1000);
  return () => clearInterval(interval);
}, [executionId, isExecuting]);
```

**日志级别过滤**:
```tsx
<select onChange={(e) => setLogLevel(e.target.value)}>
  <option value="">全部级别</option>
  <option value="info">信息</option>
  <option value="warning">警告</option>
  <option value="error">错误</option>
</select>
```

## 🚀 性能优化策略

### 1. 数据获取优化

**分批处理**:
```python
batch_size = 100  # 每批100只股票
batches = [stocks[i:i + batch_size] for i in range(0, len(stocks), batch_size)]

# 并发处理多个批次
async with aiohttp.ClientSession() as session:
    tasks = [fetch_batch(session, batch) for batch in batches]
    results = await asyncio.gather(*tasks)
```

**智能缓存**:
```python
# 缓存键设计
cache_key = f"daily_data_{trade_date}_{hash(tuple(sorted(fields)))}"

# 分层缓存策略
if cache_key in memory_cache:
    return memory_cache[cache_key]
elif cache_key in redis_cache:
    data = redis_cache.get(cache_key)
    memory_cache[cache_key] = data
    return data
else:
    data = await fetch_from_tushare()
    memory_cache[cache_key] = data
    redis_cache.set(cache_key, data, expire=3600)
    return data
```

### 2. 因子计算优化

**向量化计算**:
```python
# 使用pandas向量化操作替代循环
def calculate_momentum_factor(data):
    # 避免: for循环计算每只股票
    # 使用: 向量化计算
    return (data['close'] / data['close'].shift(20) - 1).fillna(0)
```

**并行计算**:
```python
# 多进程并行计算不同因子
from concurrent.futures import ProcessPoolExecutor

async def calculate_factors_parallel(strategy, stock_data):
    with ProcessPoolExecutor(max_workers=4) as executor:
        tasks = []
        for factor in strategy.factors:
            if factor.is_enabled:
                task = executor.submit(calculate_single_factor, factor, stock_data)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return dict(zip([f.factor_id for f in strategy.factors], results))
```

### 3. 内存管理

**数据分块处理**:
```python
def process_large_dataset(data, chunk_size=10000):
    """分块处理大数据集，避免内存溢出"""
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield process_chunk(chunk)
```

**及时清理**:
```python
# 计算完成后立即清理大对象
del large_dataframe
gc.collect()
```

## 🔒 错误处理与容错

### 1. 分层错误处理

**网络层错误**:
```python
async def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        except aiohttp.ClientError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

**数据验证错误**:
```python
def validate_stock_data(data):
    """验证股票数据完整性"""
    if data.empty:
        raise DataValidationError("股票数据为空")
    
    required_fields = ['ts_code', 'trade_date', 'close']
    missing_fields = [f for f in required_fields if f not in data.columns]
    if missing_fields:
        raise DataValidationError(f"缺少必要字段: {missing_fields}")
    
    if data['close'].isna().all():
        raise DataValidationError("收盘价数据全部为空")
```

**因子计算错误**:
```python
async def calculate_factor_safe(factor_def, stock_data):
    """安全的因子计算，捕获并记录错误"""
    try:
        return await calculate_factor(factor_def, stock_data)
    except ZeroDivisionError:
        logger.warning(f"因子 {factor_def.id} 计算出现除零错误")
        return pd.Series(index=stock_data.index, data=np.nan)
    except Exception as e:
        logger.error(f"因子 {factor_def.id} 计算失败: {e}")
        return pd.Series(index=stock_data.index, data=np.nan)
```

### 2. 优雅降级

**部分失败处理**:
```python
# 即使部分股票数据获取失败，也继续处理成功的部分
if len(failed_stocks) > 0:
    logger.warning(f"部分股票数据获取失败: {len(failed_stocks)}只")
    
if len(successful_data) > 0:
    logger.info(f"继续处理成功获取的数据: {len(successful_data)}只")
    continue_execution(successful_data)
else:
    raise ExecutionError("所有股票数据获取失败")
```

## 📈 监控与指标

### 1. 执行性能指标

```python
class ExecutionMetrics:
    total_time: float           # 总执行时间
    data_fetch_time: float      # 数据获取时间
    factor_calc_time: float     # 因子计算时间
    stock_count: int            # 处理股票数量
    cache_hit_rate: float       # 缓存命中率
    api_call_count: int         # API调用次数
    success_rate: float         # 成功率
```

### 2. 实时监控

**执行状态监控**:
```python
# WebSocket实时推送执行进度
@websocket_route("/ws/execution/{execution_id}")
async def execution_websocket(websocket, execution_id):
    while execution_id in running_executions:
        progress = get_execution_progress(execution_id)
        await websocket.send_json({
            "type": "progress_update",
            "data": progress.dict()
        })
        await asyncio.sleep(1)
```

**系统资源监控**:
```python
import psutil

def get_system_metrics():
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_executions": len(running_executions)
    }
```

## 🔮 扩展性设计

### 1. 插件化因子计算

```python
class FactorPlugin:
    """因子计算插件基类"""
    
    @abstractmethod
    async def calculate(self, stock_data: pd.DataFrame) -> pd.Series:
        pass
    
    @property
    @abstractmethod
    def required_fields(self) -> List[str]:
        pass

# 注册自定义因子
@register_factor_plugin("custom_momentum")
class CustomMomentumFactor(FactorPlugin):
    async def calculate(self, stock_data):
        return calculate_custom_momentum(stock_data)
```

### 2. 多数据源支持

```python
class DataSource:
    """数据源抽象基类"""
    
    @abstractmethod
    async def fetch_data(self, symbols, fields, date) -> pd.DataFrame:
        pass

class TushareDataSource(DataSource):
    async def fetch_data(self, symbols, fields, date):
        return await tushare_client.get_data(symbols, fields, date)

class WindDataSource(DataSource):
    async def fetch_data(self, symbols, fields, date):
        return await wind_client.get_data(symbols, fields, date)
```

### 3. 分布式执行

```python
# 使用Celery实现分布式执行
from celery import Celery

app = Celery('strategy_execution')

@app.task
def execute_strategy_task(strategy_id, execution_config):
    """异步执行策略任务"""
    return strategy_execution_engine.execute_strategy(
        strategy_id, execution_config
    )

# 任务状态跟踪
def get_task_progress(task_id):
    result = execute_strategy_task.AsyncResult(task_id)
    return {
        "state": result.state,
        "progress": result.info.get('progress', 0),
        "logs": result.info.get('logs', [])
    }
```

## 🎯 总结

这套策略执行引擎架构具备以下核心优势：

### ✅ 功能完整性
- **全面的股票筛选**: 支持多种筛选方式，满足不同投资需求
- **智能数据获取**: 按需获取，缓存优化，提升执行效率
- **详细执行日志**: 完整记录执行过程，便于问题诊断

### ✅ 性能优化
- **分批并发处理**: 避免API限制，提升数据获取速度
- **多层缓存策略**: 减少重复数据获取，降低成本
- **向量化计算**: 利用pandas优化，提升因子计算效率

### ✅ 用户体验
- **直观的界面设计**: 分步引导，降低使用门槛
- **实时进度监控**: 清晰显示执行状态和进度
- **详细的日志查看**: 帮助用户了解执行细节

### ✅ 系统可靠性
- **分层错误处理**: 优雅处理各种异常情况
- **优雅降级机制**: 部分失败不影响整体执行
- **完整的监控体系**: 实时掌握系统运行状态

### ✅ 扩展性
- **插件化架构**: 支持自定义因子和数据源
- **分布式支持**: 可扩展到多机执行
- **模块化设计**: 便于功能迭代和维护

这套架构为量化策略执行提供了工业级的解决方案，既满足了当前需求，又为未来扩展奠定了坚实基础！