## 编码代理（Coding Agent）

### 上下文构建器（Context Builder）
- 汇总端点/字段、`output_index`、约束与允许/禁止的能力集。
- 由 `build_agent_context(selection)` 生成，作为 LLM 的 `user` 消息部分内容。

### 对接与配置（OpenAI 兼容 + Qwen/DashScope）
- 客户端实现走 OpenAI 兼容协议，调用 `POST <base_url>/chat/completions`。
- 环境变量（二选一）：
  - 通用 OpenAI 兼容：`AI_ENDPOINT`、`AI_API_KEY`、`AI_MODEL`
  - DashScope（推荐快捷）：设置 `DASHSCOPE_API_KEY=sk-xxx`
    - 自动采用 `AI_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1`
    - 默认 `AI_MODEL=qwen3-coder-plus`
- 运行时可通过 `coding_prefs` 覆盖模型，并用 `coding_prefs.extra` 透传附加参数（如 `{"enable_thinking": false}`）。

### 生成流程
1) 构建消息（system + user）
- system：约束 `compute_factor` 的函数签名与安全边界（仅用 numpy/pandas，不得 IO/网络/子进程/反射/动态导入等），并要求返回包含 `factor` 列、保留 `output_index` 的 DataFrame。
- user：注入结构化上下文（selection 与 endpoints 元数据）与 `USER_FACTOR_SPEC`，并强调“仅返回 Python 代码、无解释/注释/Markdown”。

2) 调用 LLM（可透传 `coding_prefs`）
- `model`、`temperature`、`max_tokens` 可配置；`extra` 用于模型特性（如 DashScope 的 `enable_thinking`）。

3) 结果后处理（剥壳）
- 自动剥离 ```python 围栏，只保留 `def compute_factor...` 起始的纯代码。
- 若无法解析出有效函数，则回退到脚手架代码（安全兜底）。

4) 校验
- `/factors/validate`：AST 安全检查（导入/调用黑白名单、函数签名校验、语法错误提示）。
- 字段边界检查：仅允许引用 selection 中声明的字段；忽略赋值新建的派生列（如 `df['pe_ttm_z'] = ...`）。

### API
- `POST /factors/codegen`
  - 入参：
    - `selection` 或 `selection_slug`
    - `user_factor_spec`（文本）
    - `coding_prefs?`：`{ model?, temperature?, max_tokens?, extra? }`
  - 返回：`{ code_text, fields_used, notes }`

示例（Qwen/DashScope）：
```bash
curl -X POST http://127.0.0.1:8000/factors/codegen \
  -H 'Content-Type: application/json' \
  -d '{
    "selection_slug": "val_low_combo",
    "user_factor_spec": "neutral",
    "coding_prefs": {
      "model": "qwen3-coder-plus",
      "extra": { "enable_thinking": false }
    }
  }'
```

### 安全性
- 沙箱执行仅允许 numpy/pandas；禁止其他导入。
- AST 校验 + 字段边界检查；屏蔽敏感信息（token）。
