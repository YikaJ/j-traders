## 目录与数据端点（Catalog & Endpoints）

结构
- `catalog/endpoints/*.json`：端点元数据
- `catalog/registry.json`：已启用端点列表
- `catalog/selections/*.json`：按因子定义的字段选择规范

端点元数据字段（EndpointMeta）
- `sdk.method`
- `axis`、`frequency`、`ids`、`params`、`fields`
- `rate_limit`（qps/burst）
- `cache_enabled`、`rate_limit_enabled`

相关 API
- GET `/catalog/endpoints`
- GET `/catalog/endpoints/{name}`
- GET `/catalog/fields/search?q=keyword`
