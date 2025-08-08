## Catalog & Endpoints

Structure
- `catalog/endpoints/*.json`: endpoint metadata
- `catalog/registry.json`: enabled endpoints
- `catalog/selections/*.json`: per-factor selection specs

EndpointMeta
- sdk.method
- axis, frequency, ids, params, fields
- rate_limit (qps/burst)
- cache_enabled, rate_limit_enabled

APIs
- GET `/catalog/endpoints`
- GET `/catalog/endpoints/{name}`
- GET `/catalog/fields/search?q=keyword`
