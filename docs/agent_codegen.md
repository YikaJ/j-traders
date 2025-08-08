## Coding Agent

Context builder
- Aggregates endpoints/fields, output_index, constraints, allowed/denied capabilities.

LLM client (OpenAI-compatible)
- `LLMClient.complete(messages, model, temperature, max_tokens, timeout)`
- Config via env: `AI_ENDPOINT`, `AI_API_KEY`, `AI_MODEL`

Generation flow
1. Build messages (system + user with context & spec)
2. Call LLM; fallback to scaffold if disabled
3. Validate generated code via `/factors/validate`

Security
- Sandbox execution only allows numpy/pandas; imports outside are blocked
- AST checks and field boundary checks
