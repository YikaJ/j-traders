## 持久化（Persistence）

SQLite 表结构
- `factors(id, name, desc, code_text, fields_used, normalization, tags, selection, created_at)`
- `strategies(id, name, normalization, created_at)`
- `strategy_factors(strategy_id, factor_id, weight)`
- `securities(ts_code PK, sec_type, symbol, name, area, industry, market, exchange, list_status, list_date, delist_date, is_hs, updated_at)`

API
- 因子：POST `/factors`，GET `/factors`，GET `/factors/{id}`
- 策略：POST `/strategies`，PUT `/strategies/{id}/weights`，PUT `/strategies/{id}/normalization`，GET `/strategies/{id}`
- 股票池：POST `/universe/sync`，GET `/universe/stocks`，GET `/universe/stocks/{ts_code}`
