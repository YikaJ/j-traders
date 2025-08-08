## 股票池（Universe，基于 stock_basic）

- 数据源：TuShare `stock_basic`
- 持久化：SQLite 表 `securities`（sec_type, ts_code, symbol, name, area, industry, market, exchange, list_status, list_date, delist_date, is_hs, updated_at）
- 同步 API：POST `/universe/sync`（支持 `?mock=true`）
- 查询 API：
  - GET `/universe/stocks`（过滤项：industry、market、list_status、exchange、is_hs、q）
  - GET `/universe/stocks/{ts_code}`
- 策略运行：支持通过 `industry` / `ts_codes` / `all` 指定股票池
- 可扩展性：`sec_type` 预留用于未来的 ETF/指数等
