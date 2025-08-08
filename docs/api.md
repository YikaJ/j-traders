## API Summary

Health
- GET `/health`

Catalog
- GET `/catalog/endpoints`
- GET `/catalog/endpoints/{name}`
- GET `/catalog/fields/search?q=keyword`

Selections
- POST `/catalog/selections`
- PUT `/catalog/selections/{slug}`
- GET `/catalog/selections`
- GET `/catalog/selections/{slug}`

Factors
- POST `/factors/codegen`
- POST `/factors/validate`
- POST `/factors/test`
- POST `/factors`
- GET `/factors`
- GET `/factors/{id}`

Standardize
- POST `/standardize/zscore`

Strategies
- POST `/strategies`
- PUT `/strategies/{id}/weights`
- PUT `/strategies/{id}/normalization`
- POST `/strategies/{id}/run`
- GET `/strategies/{id}`

Universe
- POST `/universe/sync`
- GET `/universe/stocks`
- GET `/universe/stocks/{ts_code}`
