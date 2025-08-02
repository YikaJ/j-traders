# 因子服务整合说明

## 整合概述

将原来的两个因子服务整合为一个统一的因子服务：

- `factor_service.py` (已删除) - 专注于因子代码验证和测试
- `unified_factor_service.py` (保留并增强) - 整合了所有因子相关功能

## 整合后的功能

### 1. 因子管理功能
- `get_all_factors()` - 获取所有因子
- `get_factor_by_id()` - 根据ID获取因子
- `create_factor()` - 创建新因子
- `update_factor()` - 更新因子
- `delete_factor()` - 删除因子

### 2. 因子验证功能
- `validate_factor_code()` - 验证因子代码语法和安全性
- `validate_formula()` - 验证因子公式
- `_check_code_security()` - 检查代码安全性

### 3. 因子测试功能
- `test_factor()` - 测试因子代码
- `_get_test_data()` - 获取测试数据
- `_execute_factor_code()` - 执行因子代码
- `_calculate_statistics()` - 计算统计信息

### 4. 因子执行功能
- `calculate_factor()` - 计算因子值
- `_execute_formula()` - 动态执行因子公式

### 5. 辅助功能
- `get_formula_history()` - 获取因子公式历史
- `_factor_to_dict()` - 转换因子对象为字典
- `_get_cache_key()` - 生成缓存键
- `_update_usage_stats()` - 更新使用统计

## 更新的文件

### 删除的文件
- `backend/app/services/factor_service.py` - 已删除

### 更新的文件
1. `backend/app/services/strategy_management_service.py`
   - 更新导入：`from app.services.unified_factor_service import unified_factor_service`
   - 更新实例引用：`self.factor_service = unified_factor_service`

2. `backend/app/services/strategy_execution_engine.py`
   - 更新导入：`from app.services.unified_factor_service import unified_factor_service`
   - 更新方法调用：`unified_factor_service.get_factor_by_id(factor_id, db)`

3. `backend/app/api/v1/endpoints/strategy_management.py`
   - 更新导入：`from app.services.unified_factor_service import unified_factor_service`
   - 更新方法调用：`unified_factor_service.get_all_factors(db)`

## 优势

1. **统一管理** - 所有因子相关功能集中在一个服务中
2. **减少重复** - 消除了两个服务之间的功能重复
3. **更好的维护性** - 单一服务更容易维护和扩展
4. **完整功能** - 保留了所有原有功能，包括验证、测试、管理和执行
5. **向后兼容** - 保持了原有的API接口

## 测试结果

- ✅ 统一因子服务导入成功
- ✅ 所有核心功能方法存在
- ✅ 因子代码验证功能正常
- ✅ 因子公式验证功能正常
- ✅ 所有引用已正确更新

## 使用示例

```python
from app.services.unified_factor_service import unified_factor_service

# 验证因子代码
validation_result = await unified_factor_service.validate_factor_code(code)

# 测试因子
test_result = await unified_factor_service.test_factor(code, symbols)

# 创建因子
factor_data = {
    'factor_id': 'momentum_factor',
    'name': '动量因子',
    'formula': 'result = data["close"].pct_change()'
}
created_factor = unified_factor_service.create_factor(factor_data, db)

# 计算因子值
factor_values = unified_factor_service.calculate_factor(factor_id, data, parameters, db)
```

## 注意事项

1. 所有原有的功能都已保留
2. 异步方法保持不变（如 `validate_factor_code`, `test_factor`）
3. 同步方法保持不变（如 `create_factor`, `get_factor_by_id`）
4. 缓存机制和安全性检查都已保留
5. 错误处理和日志记录都已保留 