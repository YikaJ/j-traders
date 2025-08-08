## Strategy

APIs
- POST `/strategies` → create
- PUT `/strategies/{id}/weights` → set/normalize weights (L1)
- PUT `/strategies/{id}/normalization` → update strategy-level standardization
- POST `/strategies/{id}/run` → run and return Top N (supports `industry`/`ts_codes`/`all`)
- GET `/strategies/{id}`

Run behavior (MVP)
- Synthetic data generation per factor selection (MVP)
- Sandbox execute factor → zscore by group → weight sum score
- Return Top N rows with score
