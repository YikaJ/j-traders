## Factors

APIs
- POST `/factors/codegen` → returns code_text, fields_used, notes
- POST `/factors/validate` → returns ok, fields_used, errors
- POST `/factors/test` → execute with synthetic data + zscore preview
- POST `/factors` → save factor
- GET `/factors`, GET `/factors/{id}`

Contract
- `def compute_factor(data: dict[str, pd.DataFrame], params: dict) -> pd.DataFrame`
- Output DataFrame includes `factor` column and preserves `output_index`
