## 安全（Security）

- AST 校验：阻止危险导入/调用，强制存在 `compute_factor`
- 沙箱：仅允许名单内导入（numpy、pandas），受限内建与超时控制
- 令牌屏蔽：错误处理时隐藏 `TUSHARE_TOKEN`、`AI_API_KEY`
- 限流与缓存：按端点开关，使用全局令牌桶
