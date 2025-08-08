## 标准化（Standardization）

方法（MVP）
- zscore（已实现）
- robust_zscore（规划中）
- rank（规划中）
- minmax（规划中）

截尾与填充（Winsor & Fill）
- winsor：分位数区间 [low, high]
- fill：`median` | `zero` | `drop`

API
- POST `/standardize/zscore`，参数包含 `{ by, winsor, fill, value_col, data }`

诊断指标
- `mean`、`std`、`skew`、`kurt`、`missing_rate`
