## API 概览

健康检查
- GET `/health`

目录（Catalog）
- GET `/catalog/endpoints`
- GET `/catalog/endpoints/{name}`
- GET `/catalog/fields/search?q=keyword`

选择集（Selections）
- POST `/catalog/selections`
- PUT `/catalog/selections/{slug}`
- GET `/catalog/selections`
- GET `/catalog/selections/{slug}`

因子（Factors）
- POST `/factors/codegen`
- POST `/factors/validate`
- POST `/factors/test`
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
- POST `/universe/sync`
- GET `/universe/stocks`
- GET `/universe/stocks/{ts_code}`
