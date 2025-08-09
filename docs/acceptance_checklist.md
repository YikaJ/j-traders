## 验收清单（Acceptance Checklist）

- M0：健康检查正常，日志/配置已加载
- M1：端点可列出，端点详情可返回，字段搜索可用；选择集支持增改查
- M2：TuShare 拉取具备缓存、限流与重试；参数绑定可用
- M3：代码生成返回代码；校验能拦截危险代码/字段；沙箱限制生效
- M4：标准化 zscore API 可用；`/factors/sample` 可返回真实小样本（失败回退合成扰动）；`/factors/test` 返回 zscore 预览与诊断
- M5：因子/策略可持久化；权重已归一化；读取可见数据
- M6：股票池通过真实源同步（可按 `since`/`list_status`/`exchange`/`market`/`industry`/`is_hs`/`limit` 过滤）；策略运行在指定股票池下返回 Top N
- M7：端到端冒烟通过；标准化具单元测试；关键安全措施到位；策略运行提供研究诊断（IC/RankIC/覆盖率）
