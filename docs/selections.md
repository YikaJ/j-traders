## 选择集（Selections）

规范字段
- `factor_slug`、`title`
- `output_index`：例如 ["ts_code","trade_date"]
- `selection`：数组，元素为 `{ endpoint, fields, param_binding, join_keys }`
- `constraints`：如 winsor、zscore_axis
- `code_contract`：函数签名、数据键

API
- POST `/catalog/selections`
- PUT `/catalog/selections/{slug}`
- GET `/catalog/selections`
- GET `/catalog/selections/{slug}`
