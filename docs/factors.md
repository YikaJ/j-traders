## 因子（Factors）

API
- POST `/factors/codegen` → 返回 `code_text`、`fields_used`、`notes`
- POST `/factors/validate` → 返回 `ok`、`fields_used`、`errors`
- POST `/factors/test` → 使用合成数据执行并提供 zscore 预览
- POST `/factors` → 保存因子
- GET `/factors`，GET `/factors/{id}`

契约（Contract）
- `def compute_factor(data: dict[str, pd.DataFrame], params: dict) -> pd.DataFrame`
- 输出的 DataFrame 必须包含 `factor` 列，并保留 `output_index`
