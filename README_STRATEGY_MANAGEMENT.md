# 策略管理系统

全新的量化策略管理功能已经实现！支持创建、配置、执行多因子选股策略。

## 🎯 核心功能

### ✅ 策略创建
- **分步式创建流程**：引导用户逐步完成策略配置
- **因子选择**：从因子库中选择多个因子
- **权重配置**：为每个因子设置权重，自动验证权重总和
- **筛选条件**：配置市值、价格、行业等筛选条件
- **策略参数**：设置最大选股数量、调仓频率等

### ✅ 策略管理
- **策略列表**：展示所有创建的策略及其状态
- **策略详情**：查看策略的完整配置信息
- **策略执行**：一键执行策略选股
- **策略编辑**：支持修改策略配置（后续扩展）
- **策略删除**：安全删除不需要的策略

### ✅ 执行管理
- **实时执行**：立即执行策略选股
- **执行历史**：记录每次执行的结果
- **执行统计**：统计执行次数、平均耗时等
- **结果展示**：显示选中的股票及其得分

## 🏗️ 技术架构

### 后端实现

```
backend/app/
├── schemas/strategy.py              # 策略相关数据模型
├── db/models/strategy.py           # 策略数据库模型
├── services/strategy_management_service.py  # 策略管理服务
└── api/v1/endpoints/strategy_management.py  # 策略管理API
```

#### 核心数据模型

**StrategyFactor** - 策略中的因子配置
```python
{
    "factor_id": "alpha001",      # 因子ID
    "factor_name": "动量因子",     # 因子名称
    "weight": 0.3,               # 权重
    "is_enabled": true           # 是否启用
}
```

**StrategyFilter** - 策略筛选条件
```python
{
    "min_market_cap": 1000000,   # 最小市值
    "max_market_cap": 50000000,  # 最大市值
    "exclude_st": true,          # 排除ST股票
    "exclude_new_stock": true,   # 排除新股
    "exclude_suspend": true      # 排除停牌股票
}
```

**StrategyConfig** - 策略配置
```python
{
    "max_results": 50,           # 最大选股数量
    "rebalance_frequency": "weekly",  # 调仓频率
    "ranking_method": "composite"     # 排序方法
}
```

### 前端实现

```
frontend/src/
├── components/StrategyCreateModal.tsx   # 策略创建组件
├── pages/StrategyManagement.tsx         # 策略管理页面
└── services/api.ts                      # API接口定义
```

#### 核心组件

**StrategyCreateModal** - 分步式策略创建
- 第一步：基本信息（名称、描述）
- 第二步：因子选择（选择因子、设置权重）
- 第三步：配置参数（筛选条件、策略参数）

**StrategyManagement** - 策略管理主界面
- 策略列表展示
- 搜索和筛选
- 策略操作（查看、执行、删除）
- 统计信息展示

## 🎛️ API接口

### 策略管理接口

```http
# 创建策略
POST /api/v1/strategy-management/
Content-Type: application/json

{
  "name": "多因子选股策略",
  "description": "基于动量和价值因子的选股策略",
  "factors": [
    {
      "factor_id": "alpha001",
      "factor_name": "动量因子",
      "weight": 0.6,
      "is_enabled": true
    },
    {
      "factor_id": "alpha002",
      "factor_name": "价值因子",
      "weight": 0.4,
      "is_enabled": true
    }
  ],
  "filters": {
    "min_market_cap": 1000000,
    "exclude_st": true,
    "exclude_new_stock": true
  },
  "config": {
    "max_results": 30,
    "rebalance_frequency": "weekly"
  }
}
```

```http
# 获取策略列表
GET /api/v1/strategy-management/?skip=0&limit=20&keyword=多因子

# 获取单个策略
GET /api/v1/strategy-management/{strategy_id}

# 执行策略
POST /api/v1/strategy-management/{strategy_id}/execute
{
  "dry_run": false,
  "save_result": true
}

# 获取执行历史
GET /api/v1/strategy-management/{strategy_id}/executions

# 获取可用因子
GET /api/v1/strategy-management/{strategy_id}/available-factors
```

## 🌟 用户体验

### 策略创建流程

1. **点击"创建策略"** - 打开创建向导
2. **填写基本信息** - 输入策略名称和描述
3. **选择因子** - 从因子库中选择所需因子
4. **设置权重** - 为每个因子分配权重（自动验证总和为1）
5. **配置参数** - 设置筛选条件和策略参数
6. **确认创建** - 验证配置并创建策略

### 策略管理界面

- **卡片式展示**：每个策略以卡片形式展示，包含关键信息
- **状态标识**：清晰显示策略的启用/禁用状态
- **快速操作**：提供查看、执行、编辑、删除等操作按钮
- **统计信息**：展示总策略数、启用策略数、执行次数等
- **搜索筛选**：支持按关键词搜索策略

### 因子权重管理

- **可视化权重**：以百分比形式显示因子权重
- **实时验证**：权重修改时实时验证总和
- **自动分配**：添加/删除因子时自动重新分配等权重
- **启用切换**：支持临时禁用某个因子

## 🚀 使用示例

### 创建多因子策略

```javascript
// 前端API调用示例
const strategyData = {
  name: "价值动量组合策略",
  description: "结合价值和动量因子的长期策略",
  factors: [
    {
      factor_id: "value_factor_001",
      factor_name: "PB估值因子", 
      weight: 0.4,
      is_enabled: true
    },
    {
      factor_id: "momentum_factor_001", 
      factor_name: "20日动量因子",
      weight: 0.6,
      is_enabled: true
    }
  ],
  filters: {
    min_market_cap: 5000000,     // 最小市值50亿
    exclude_st: true,            // 排除ST股票
    exclude_new_stock: true,     // 排除新股
    exclude_suspend: true        // 排除停牌股票
  },
  config: {
    max_results: 30,             // 最多选30只股票
    rebalance_frequency: "weekly", // 每周调仓
    ranking_method: "composite"   // 综合排序
  }
};

const strategy = await strategyManagementApi.createStrategy(strategyData);
```

### 执行策略选股

```javascript
// 执行策略
const result = await strategyManagementApi.executeStrategy(strategy.strategy_id, {
  dry_run: false,      // 实际执行
  save_result: true    // 保存结果
});

console.log(`选中${result.stock_count}只股票，耗时${result.execution_time}秒`);
```

## 📊 执行结果

策略执行后会返回选中的股票列表，包含：

```javascript
{
  "execution_id": "uuid",
  "strategy_id": "strategy_uuid", 
  "execution_date": "2024-01-15",
  "execution_time": 2.35,
  "stock_count": 25,
  "selected_stocks": [
    {
      "stock_code": "000001.SZ",
      "stock_name": "平安银行",
      "composite_score": 0.85,
      "factor_scores": {
        "value_factor_001": 0.8,
        "momentum_factor_001": 0.9
      },
      "rank": 1,
      "market_cap": 3500000,
      "price": 15.68
    }
    // ... 更多股票
  ]
}
```

## 🔧 配置选项

### 筛选条件选项

- **市值筛选**：最小/最大市值限制
- **价格筛选**：最小/最大股价限制  
- **换手率筛选**：最小/最大换手率限制
- **特殊股票**：排除ST、新股、停牌股票
- **行业筛选**：包含/排除特定行业

### 策略参数选项

- **选股数量**：1-1000只股票
- **调仓频率**：每日/每周/每月
- **排序方法**：综合得分/加权求和

## 💡 最佳实践

### 因子选择建议

1. **因子数量**：建议选择2-5个因子，避免过度复杂
2. **因子类型**：选择不同类型的因子以分散风险
3. **权重分配**：根据因子的历史表现调整权重
4. **定期检查**：定期检查因子的有效性

### 策略配置建议

1. **选股数量**：建议20-50只股票，平衡风险和收益
2. **调仓频率**：根据市场环境选择合适频率
3. **筛选条件**：设置合理的市值和流动性要求
4. **回测验证**：创建后进行历史回测验证

## 📈 后续扩展

### 计划功能

1. **策略编辑**：支持修改现有策略配置
2. **策略复制**：基于现有策略创建新策略
3. **策略模板**：预定义的策略模板
4. **策略回测**：历史数据回测功能
5. **策略组合**：多策略组合管理
6. **风险控制**：风险指标和控制措施

### 优化方向

1. **执行性能**：优化选股算法执行速度
2. **因子计算**：集成更多因子计算服务
3. **数据源**：支持更多数据源接入
4. **可视化**：增强策略和结果的可视化
5. **监控告警**：策略执行监控和异常告警

这套策略管理系统为量化投资提供了完整的策略生命周期管理，从创建到执行，让量化选股变得更加系统化和专业化！