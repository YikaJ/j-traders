# Tushare 集成指南

本文档说明如何配置和使用 Tushare 数据服务，将所有 Mock 数据接口替换为真实的 Tushare 数据。

## 配置要求

### 1. 获取 Tushare Token

1. 访问 [Tushare 官网](https://tushare.pro/)
2. 注册账号并登录
3. 在个人中心获取 API Token

### 2. 环境配置

在项目根目录创建 `.env` 文件：

```bash
# Tushare 配置
TUSHARE_TOKEN=your_tushare_token_here

# 数据库配置
DATABASE_URL=sqlite:///./quantitative_stock.db

# 其他配置
DEBUG=true
API_HOST=127.0.0.1
API_PORT=8000
```

### 3. 安装依赖

确保已安装所需的 Python 包：

```bash
pip install tushare pandas numpy fastapi sqlalchemy
```

## 已集成的接口

### 1. 市场数据接口

#### `/market/indices` - 获取市场指数
- **功能**: 获取主要市场指数数据（上证指数、深证成指、创业板指等）
- **数据源**: Tushare 指数日线数据
- **缓存**: 数据会保存到本地数据库，优先使用缓存数据

#### `/market/quotes` - 获取股票行情
- **功能**: 获取股票实时行情数据
- **数据源**: Tushare 实时行情或最新日线数据
- **支持**: 支持批量查询多只股票

#### `/market/history/{symbol}` - 获取历史数据
- **功能**: 获取股票历史交易数据
- **数据源**: Tushare 日线数据
- **参数**: 
  - `symbol`: 股票代码
  - `days`: 获取天数（默认30天）

### 2. 自选股接口

#### `/watchlist/search` - 搜索股票
- **功能**: 根据关键词搜索股票
- **数据源**: Tushare 股票基础信息
- **搜索**: 支持按股票代码或名称搜索

### 3. 服务层

#### 股票同步服务
- **功能**: 同步股票基础信息到本地数据库
- **数据源**: Tushare 股票列表

#### 策略服务
- **功能**: 执行量化策略选股
- **数据源**: Tushare 历史数据用于因子计算

#### 因子服务
- **功能**: 测试和验证因子代码
- **数据源**: Tushare 历史数据用于因子回测

## 数据流程

### 1. 数据获取流程

```
用户请求 → API 接口 → 检查本地缓存 → 从 Tushare 获取 → 保存到数据库 → 返回结果
```

### 2. 错误处理

- **Tushare 服务不可用**: 返回错误信息，不再使用 Mock 数据
- **数据获取失败**: 记录日志，返回空结果或错误
- **网络超时**: 设置合理的超时时间，避免长时间等待

### 3. 数据缓存策略

- **指数数据**: 缓存最新数据，定期更新
- **股票行情**: 实时数据优先，失败时使用最新日线数据
- **历史数据**: 按股票代码和日期范围缓存

## 测试验证

### 运行集成测试

```bash
cd backend
python test_tushare_integration.py
```

测试内容包括：
- Tushare 服务连接测试
- 市场数据接口测试
- 自选股接口测试
- 服务层功能测试

### 手动测试接口

1. **测试市场指数接口**:
```bash
curl "http://localhost:8000/api/v1/market/indices"
```

2. **测试股票行情接口**:
```bash
curl "http://localhost:8000/api/v1/market/quotes?symbols=000001.SZ,600036.SH"
```

3. **测试股票搜索接口**:
```bash
curl "http://localhost:8000/api/v1/watchlist/search?keyword=茅台&limit=5"
```

## 性能优化

### 1. 并发控制

- 使用 ThreadPoolExecutor 控制并发请求数
- 设置合理的 API 调用间隔，避免触发频率限制

### 2. 数据缓存

- 指数数据缓存到本地数据库
- 股票基础信息定期同步更新
- 历史数据按需加载和缓存

### 3. 错误重试

- 网络错误自动重试
- API 限制时等待后重试
- 记录详细的错误日志

## 监控和日志

### 1. 日志记录

所有 Tushare 相关的操作都会记录详细日志：
- 数据获取成功/失败
- API 调用频率
- 错误信息和堆栈跟踪

### 2. 性能监控

- API 响应时间
- 数据获取成功率
- 缓存命中率

## 故障排除

### 常见问题

1. **Token 无效**
   - 检查 `.env` 文件中的 TUSHARE_TOKEN 配置
   - 确认 Token 是否有效且未过期

2. **网络连接失败**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试使用代理

3. **API 频率限制**
   - 减少并发请求数
   - 增加请求间隔
   - 使用数据缓存

4. **数据格式错误**
   - 检查 Tushare 返回的数据格式
   - 确认字段映射是否正确
   - 查看错误日志

### 调试方法

1. **启用详细日志**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **测试 Tushare 连接**:
```python
import tushare as ts
ts.set_token('your_token')
pro = ts.pro_api()
# 测试简单查询
df = pro.stock_basic(limit=1)
print(df)
```

## 更新日志

### v1.0.0 (当前版本)
- ✅ 移除所有 Mock 数据
- ✅ 集成 Tushare 实时数据
- ✅ 实现数据缓存机制
- ✅ 添加错误处理和重试
- ✅ 创建集成测试脚本
- ✅ 完善文档和配置说明

## 注意事项

1. **API 限制**: Tushare 免费版有调用频率限制，请合理使用
2. **数据延迟**: 实时数据可能有延迟，历史数据相对准确
3. **网络依赖**: 需要稳定的网络连接
4. **Token 安全**: 请妥善保管 Tushare Token，不要提交到代码仓库

## 技术支持

如果遇到问题，请：
1. 查看日志文件 `./logs/app.log`
2. 运行测试脚本验证配置
3. 检查网络连接和 Token 配置
4. 参考 Tushare 官方文档 