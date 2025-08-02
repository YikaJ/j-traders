# 策略服务整合说明

## 整合概述

本次整合将原来的三个策略相关服务整合为两个核心服务，简化了架构并提高了代码的可维护性。

## 整合前的架构

- `strategy_service.py` - 策略服务（旧版本）
- `strategy_management_service.py` - 策略管理服务
- `strategy_execution_engine.py` - 策略执行引擎

## 整合后的架构

### 1. `strategy_management_service.py` - 策略管理服务
**主要职责：**
- 策略的CRUD操作（创建、读取、更新、删除）
- 策略列表管理和查询
- 策略执行历史记录
- 策略验证和配置管理
- 调用执行引擎进行策略执行

**核心方法：**
- `create_strategy()` - 创建策略
- `get_strategies()` - 获取策略列表
- `update_strategy()` - 更新策略
- `delete_strategy()` - 删除策略
- `execute_strategy()` - 执行策略（调用执行引擎）
- `get_execution_history()` - 获取执行历史
- `get_execution_detail()` - 获取执行详情

### 2. `strategy_execution_engine.py` - 策略执行引擎
**主要职责：**
- 策略的完整执行流程
- 实时进度跟踪和日志记录
- 异步执行管理
- 股票筛选、数据获取、因子计算、排序选股
- 整合了原 `strategy_service.py` 的核心功能

**核心组件：**
- `ExecutionLogger` - 执行日志记录器
- `ProgressTracker` - 进度跟踪器
- `DataFetcher` - 数据获取器（整合了历史数据获取功能）
- `FactorCalculator` - 因子计算器（整合了因子计算逻辑）
- `StockSelector` - 股票选择器（整合了股票池获取和选股逻辑）

**核心方法：**
- `execute_strategy()` - 执行策略（支持异步和进度跟踪）
- `get_execution_progress()` - 获取执行进度
- `cancel_execution()` - 取消执行
- `get_available_scopes()` - 获取可用的股票范围选项

## 整合的功能

### 从 `strategy_service.py` 整合到 `strategy_execution_engine.py` 的功能：

1. **股票池获取** (`_get_stock_pool`)
   - 从数据库获取股票数据
   - 应用基础过滤条件（ST股票、新股、市值、换手率等）
   - 模拟数据生成

2. **历史数据获取** (`_get_stock_historical_data`)
   - 从数据库获取股票历史数据
   - 支持从Tushare获取数据
   - 数据格式标准化

3. **因子计算** (`_execute_single_factor`)
   - 安全的因子代码执行环境
   - 支持pandas和numpy操作
   - 错误处理和NaN值处理

4. **因子值标准化** (`_normalize_factor_values`)
   - Z-Score标准化
   - 处理零值和异常值

5. **综合得分计算** (`_calculate_composite_scores`)
   - 多因子权重计算
   - 股票排名和筛选

6. **结果保存** (`_save_results`)
   - 选股结果数据库保存
   - 执行统计信息计算

## 删除的文件

- `strategy_service.py` - 已删除，功能整合到执行引擎中
- `backend/app/api/v1/endpoints/strategies.py` - 已删除，被新的策略管理API替代

## 更新的引用

### API端点更新
- `backend/app/api/v1/endpoints/strategies.py` - 已删除，功能由 `strategy_management.py` 提供
- `backend/app/api/v1/api.py` - 更新路由配置，移除对已删除模块的引用

### 服务引用更新
- 所有引用 `strategy_service` 的地方都更新为使用 `strategy_management_service`
- 因子服务引用更新为 `unified_factor_service`

## 架构优势

1. **职责分离清晰**
   - 管理服务专注于策略生命周期管理
   - 执行引擎专注于策略执行和计算

2. **功能整合**
   - 避免了重复代码
   - 统一了执行逻辑
   - 提高了代码复用性

3. **扩展性更好**
   - 执行引擎支持异步和进度跟踪
   - 模块化设计便于功能扩展
   - 支持实时监控和日志记录

4. **维护性提升**
   - 减少了代码重复
   - 统一了错误处理
   - 简化了依赖关系

## 使用建议

### 新功能开发
- 策略管理相关功能 → 使用 `strategy_management_service`
- 策略执行相关功能 → 使用 `strategy_execution_engine`

### API调用
```python
# 策略管理
from app.services.strategy_management_service import strategy_management_service

# 策略执行
from app.services.strategy_execution_engine import strategy_execution_engine
```

### 执行流程
1. 通过管理服务创建/获取策略
2. 调用执行引擎执行策略
3. 通过管理服务获取执行结果和历史

## 注意事项

1. **数据库模型兼容性**
   - 确保数据库模型与新的服务架构兼容
   - 可能需要更新数据库迁移脚本

2. **API兼容性**
   - 检查前端API调用是否需要更新
   - 确保返回格式的一致性

3. **测试覆盖**
   - 更新单元测试以覆盖新的服务架构
   - 确保集成测试正常工作

4. **性能优化**
   - 监控执行引擎的性能表现
   - 根据需要调整线程池和缓存配置

## 兼容性检查结果

### 1. 数据库模型兼容性 ✅

**检查结果：**
- ✅ 数据库模型 `Strategy` 使用 JSON 字段存储配置，与新的服务架构兼容
- ✅ 数据库模型 `StrategyExecution` 支持新的执行结果格式
- ✅ 数据库模型 `SelectionResult` 支持选股结果存储

**修复的问题：**
- ❌ 旧API端点 `strategies.py` 使用了不存在的数据库字段（如 `factor_ids`, `factor_weights` 等）
- ✅ 已删除旧的API端点，使用新的 `strategy_management.py` API
- ✅ 新的API端点正确使用 JSON 字段（`factors`, `filters`, `config`）

**数据库字段映射：**
```python
# 旧字段（已废弃）
factor_ids: List[int]
factor_weights: Dict[str, float]
max_results: int
min_market_cap: float
exclude_st: bool

# 新字段（当前使用）
factors: JSON  # 存储因子配置列表
filters: JSON  # 存储筛选条件
config: JSON   # 存储策略配置
```

### 2. API兼容性 ✅

**检查结果：**
- ✅ 前端API已正确使用新的 `strategy-management` 端点
- ✅ 数据结构定义与后端模型兼容
- ✅ 旧的 `strategyApi` 已更新为使用新的端点

**修复的问题：**
- ❌ 前端API中有旧的 `/strategies/` 端点引用
- ✅ 已更新为使用 `/strategy-execution/` 端点
- ✅ 删除了重复的旧API端点文件

**API端点映射：**
```typescript
// 旧端点（已废弃）
POST /strategies/execute
GET /strategies/history
POST /strategies/backtest

// 新端点（当前使用）
POST /strategy-management/{strategy_id}/execute
GET /strategy-management/{strategy_id}/executions
POST /strategy-execution/execute
```

**前端数据结构兼容性：**
```typescript
// 新的策略数据结构
interface Strategy {
  strategy_id: string;
  name: string;
  description?: string;
  factors: StrategyFactor[];  // JSON格式
  filters?: StrategyFilter;   // JSON格式
  config?: StrategyConfig;    // JSON格式
  is_active: boolean;
  // ... 其他字段
}
```

### 3. 服务架构兼容性 ✅

**检查结果：**
- ✅ 新的服务架构清晰分离了管理功能和执行功能
- ✅ 所有旧功能已正确整合到新的服务中
- ✅ 依赖关系已正确更新

**服务调用示例：**
```python
# 策略管理
strategy = await strategy_management_service.create_strategy(db, strategy_data)
strategies = await strategy_management_service.get_strategies(db, request)

# 策略执行
result = await strategy_execution_engine.execute_strategy(db, strategy, request)
progress = strategy_execution_engine.get_execution_progress(execution_id)
```

### 4. 路由配置更新 ✅

**修复的问题：**
- ❌ API路由配置中引用了已删除的 `strategies` 模块
- ✅ 已更新路由配置，移除对已删除模块的引用

**当前路由配置：**
```python
# backend/app/api/v1/api.py
api_router.include_router(strategy_management.router, prefix="/strategy-management", tags=["strategy-management"])
api_router.include_router(strategy_execution.router, prefix="/strategy-execution", tags=["strategy-execution"])
```

## 总结

✅ **数据库模型兼容性**：已修复，新的JSON字段结构完全兼容
✅ **API兼容性**：已修复，前端API已更新为使用新的端点
✅ **服务架构兼容性**：已修复，功能正确整合到新的服务中
✅ **路由配置兼容性**：已修复，移除了对已删除模块的引用

所有兼容性问题已解决，新的架构可以正常使用。 