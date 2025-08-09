## API 概览

健康检查
- GET `/health`

目录（Catalog）
- GET `/catalog/endpoints`
- GET `/catalog/endpoints/{name}`
- GET `/catalog/fields/search?q=keyword`

（已移除）选择集相关接口在本阶段不再提供

因子（Factors）
- POST `/factors/codegen`（请求体须携带数据选择 spec，即临时 selection）
- POST `/factors/validate`（请求体须携带数据选择 spec）
- POST `/factors/sample`（请求体须携带数据选择 spec）
- POST `/factors/test`（请求体须携带数据选择 spec）
- POST `/factors`
- GET `/factors`
- GET `/factors/{id}`

标准化（Standardize）
- POST `/standardize/zscore`

策略（Strategies）
- POST `/strategies`
- PUT `/strategies/{id}/weights`
- PUT `/strategies/{id}/normalization`
- POST `/strategies/{id}/run`
- GET `/strategies/{id}`

股票池（Universe）
- POST `/universe/sync`（支持查询参数：`since`、`list_status`、`exchange`、`market`、`industry`、`is_hs`、`limit`；可选 `mock=true`）
- GET `/universe/stocks`
- GET `/universe/stocks/{ts_code}`
