## Standardization

Methods (MVP)
- zscore (implemented)
- robust_zscore (planned)
- rank (planned)
- minmax (planned)

Winsor & Fill
- winsor: [low, high] quantiles
- fill: median|zero|drop

API
- POST `/standardize/zscore` with { by, winsor, fill, value_col, data }

Diagnostics
- mean, std, skew, kurt, missing_rate
