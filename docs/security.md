## Security

- AST validation: block dangerous imports/calls, enforce compute_factor presence
- Sandbox: allowlist imports (numpy, pandas), restricted builtins, timeout
- Token masking: error handler masks `TUSHARE_TOKEN`, `AI_API_KEY`
- Rate limiting & caching: per-endpoint flags, global token bucket
