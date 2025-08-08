## Universe (stock_basic)

- Source: TuShare `stock_basic`
- Persistence: SQLite table `securities` (sec_type, ts_code, symbol, name, area, industry, market, exchange, list_status, list_date, delist_date, is_hs, updated_at)
- Sync API: POST `/universe/sync` (supports `?mock=true`)
- Query APIs:
  - GET `/universe/stocks` (filters: industry, market, list_status, exchange, is_hs, q)
  - GET `/universe/stocks/{ts_code}`
- Strategy Run: supports universe selection via `industry`/`ts_codes`/`all`
- Extensibility: `sec_type` reserved for ETF/index in future
