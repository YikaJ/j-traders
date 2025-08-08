## Selections

Spec fields
- factor_slug, title
- output_index: e.g., ["ts_code","trade_date"]
- selection: array of { endpoint, fields, param_binding, join_keys }
- constraints: winsor, zscore_axis
- code_contract: signature, data_keys

APIs
- POST `/catalog/selections`
- PUT `/catalog/selections/{slug}`
- GET `/catalog/selections`
- GET `/catalog/selections/{slug}`
