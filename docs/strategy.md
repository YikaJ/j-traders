## 策略（Strategy）

API
- POST `/strategies` → 创建
- PUT `/strategies/{id}/weights` → 设置/归一化权重（L1）
- PUT `/strategies/{id}/normalization` → 更新策略级标准化方式
- POST `/strategies/{id}/run` → 运行并返回 Top N（支持 `industry`/`ts_codes`/`all`）
- GET `/strategies/{id}`

运行行为（更新）
- 按选择集从 TuShare 拉取真实样本（带缓存/限流/重试）；失败时回退到带扰动的合成样本
- 在沙箱中执行因子 → 按 group（通常为 `trade_date`）做 zscore → 按权重线性合成 `score`
- 返回 Top N 行（全局排序）；并提供研究诊断（IC、RankIC、覆盖率）
