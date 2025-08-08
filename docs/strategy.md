## 策略（Strategy）

API
- POST `/strategies` → 创建
- PUT `/strategies/{id}/weights` → 设置/归一化权重（L1）
- PUT `/strategies/{id}/normalization` → 更新策略级标准化方式
- POST `/strategies/{id}/run` → 运行并返回 Top N（支持 `industry`/`ts_codes`/`all`）
- GET `/strategies/{id}`

运行行为（MVP）
- 基于每个因子的选择集生成合成数据（MVP）
- 沙箱执行因子 → 分组 zscore → 按权重求和为分数
- 返回带分数的 Top N 行
