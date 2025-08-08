## Persistence

SQLite schema
- factors(id, name, desc, code_text, fields_used, normalization, tags, selection, created_at)
- strategies(id, name, normalization, created_at)
- strategy_factors(strategy_id, factor_id, weight)
- securities(ts_code PK, sec_type, symbol, name, area, industry, market, exchange, list_status, list_date, delist_date, is_hs, updated_at)

APIs
- Factors: POST `/factors`, GET `/factors`, GET `/factors/{id}`
- Strategies: POST `/strategies`, PUT `/strategies/{id}/weights`, PUT `/strategies/{id}/normalization`, GET `/strategies/{id}`
- Universe: POST `/universe/sync`, GET `/universe/stocks`, GET `/universe/stocks/{ts_code}`
