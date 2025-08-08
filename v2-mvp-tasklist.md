## backend-v2 MVP 研发任务清单（v2-mvp-tasklist）

本清单基于 `v2-MVP.md` 的最终版本，拆解为可执行任务与验收标准，按阶段推进。MVP 聚焦 `cashflow`、`daily_basic` 两个接口与最小多因子策略闭环。

### 里程碑与阶段
- M0 基础与骨架
- M1 Catalog 与 Selections
- M2 TuShare 客户端与缓存
- M3 因子代码生成与校验/沙箱
- M4 标准化能力与测试预览
- M5 持久化与策略 CRUD/配权
- M6 策略执行流水线（统一标准化+权重归一）
- M7 质量保障与上线

---

### M0 基础与骨架
- [x] FastAPI/uvicorn 项目骨架，模块化目录 `backend-v2/`
- [x] 环境变量接入：`TUSHARE_TOKEN`, `CACHE_TTL_HOURS(24)`, `MAX_QPS`, `LOG_LEVEL`, `API_HOST`, `API_PORT`
- [x] 健康检查接口：GET `/health` → { status, version }
- [x] 统一错误返回模型与异常处理中间件
- [x] 结构化日志（请求/响应、耗时、错误栈）
- [x] 基础依赖与锁定（requirements/poetry）

验收
- 启动成功 `uvicorn`，`/health` 返回 200，日志与环境变量读取正常

---

### M1 Catalog 与 Selections
- [x] 目录与样例文件落地
  - [x] `backend-v2/catalog/endpoints/{cashflow,daily_basic}.json`
  - [x] `backend-v2/catalog/registry.json`
  - [x] `backend-v2/catalog/selections/`（空目录，可放示例）
- [x] JSON Schema 校验器（endpoints/selection 文件）
- [x] Catalog API
  - [x] GET `/catalog/endpoints`（读取 `registry.json`）
  - [x] GET `/catalog/endpoints/{name}`（读取对应 endpoints json）
  - [x] GET `/catalog/fields/search?q=keyword`（聚合检索字段，返回字段名/接口/描述）
- [x] Selections CRUD（MVP 文件存储 + JSON 校验）
  - [x] POST `/catalog/selections`
  - [x] PUT `/catalog/selections/{slug}`
  - [x] GET `/catalog/selections`
  - [x] GET `/catalog/selections/{slug}`
  - [x] 备注：本期不引入版本号与变更注释（已在文档标注）

验收
- 能列举接口与字段并检索，能创建/更新/获取 `selection` 文件并通过 Schema 校验

---

### M2 TuShare 客户端与缓存
- [x] `tushare_client.fetch(endpoint, params)`
  - [x] 多 `ts_code` 分批/迭代合并
  - [x] 速率限制（默认跟随 `rate_limit`，可覆盖 `MAX_QPS`）
  - [x] 本地缓存（json 基础封装；键 = endpoint + 参数哈希，TTL = 24h 默认）
  - [x] 错误重试与兜底（指数退避 3 次）
- [x] 参数绑定器：按 `selection.param_binding` 拼装 fixed/request_arg/derived（MVP 暂不实现 derived 复杂规则，仅保留接口）

验收
- 能对 `cashflow`/`daily_basic` 按参数拉取数据；缓存命中率可观；QPS 受控

---

### M3 因子代码生成与校验/沙箱
- [ ] Agent 上下文构建器（由 `selection` 生成）
  - [ ] 汇总 endpoints/fields 元数据、输出索引、约束、可用库、禁用能力
  - [ ] 生成给 Coding Agent 的结构化 payload（不对外暴露）
- [ ] API：POST `/factors/codegen`
  - [ ] 输入：`selection_slug`/`selection` + `user_factor_spec` + 可选 `coding_prefs`
  - [ ] 输出：`code_text`, `fields_used`, `notes?`
- [ ] 校验：POST `/factors/validate`
  - [ ] AST 安全检查：黑/白名单、禁用 I/O/网络/子进程/反射/动态导入
  - [ ] 签名一致性：`def compute_factor(data: dict[str, pd.DataFrame], params: dict)`
  - [ ] 依赖/导入白名单检查
  - [ ] 字段越界检查：代码中引用字段必须属于 `selection` 的字段集合
  - [ ] 产出 `fields_used`（静态提取）
- [ ] 受限沙箱执行器
  - [ ] 超时/内存限制
  - [ ] 仅暴露 `numpy`, `pandas` 受限对象
  - [ ] 掩码敏感信息（token）

验收
- 提交 `user_factor_spec` 能获得可运行 `code_text`
- `validate` 能阻止危险代码/越权字段/签名不符

---

### M4 标准化能力与测试预览
- [ ] 标准化服务
  - [ ] POST `/standardize/zscore`：横截面逐期 Z-Score（支持 winsor、缺失填充）
  - [ ] 内部支持：`zscore`、`robust_zscore`、`rank`、`minmax`（MVP 默认 `zscore`）
- [ ] 预览标准化（测试阶段）
  - [ ] POST `/factors/test`：拉数 → 执行因子 → 按“临时配置”预览标准化
  - [ ] 输出诊断：均值/标准差/偏度/峰度、去极值比例、缺失率与填充值、分布图指标、逐期均值/方差时间序列、Top/Bottom N 样本
  - [ ] 限制：股票 3–10 支、期次建议 ≤ 8；不持久化标准化后的因子值

验收
- 能对小样本运行单因子，获取“标准化预览 + 诊断”

---

### M5 持久化与策略 CRUD/配权
- [ ] SQLite 初始化与迁移
  - [ ] `factors`：id, name, desc?, code_text, fields_used(json), normalization(json), tags(json), created_at
  - [ ] `strategies`：id, name, normalization(json), created_at
  - [ ] `strategy_factors`：strategy_id, factor_id, weight（已归一化后存储；默认 L1）
  - [ ] （可选）`test_runs`：id, factor_id?, request(json), stats(json), sample_rows(json), created_at
- [ ] 因子 CRUD
  - [ ] POST `/factors`（保存）
  - [ ] GET `/factors`, GET `/factors/{id}`
- [ ] 策略 CRUD/配权
  - [ ] POST `/strategies`（可含 `normalization`、`universe`）
  - [ ] PUT `/strategies/{id}/weights`（接收原始权重，服务端按归一规则规范化并持久化；可同时设置 `normalization`）
  - [ ] PUT `/strategies/{id}/normalization`（可选；通常随权重一起设置）

验收
- 能创建/查看/更新策略与其因子配权，权重在持久化前被规范化（默认 L1）

---

### M6 策略执行流水线（统一标准化+权重归一）
- [ ] Universe 默认过滤（实现 + 默认集）
  - 建议默认：
  - [ ] 排除 ST（名称含 ST/*ST）
  - [ ] 排除停牌（当期停牌标记）
  - [ ] 排除涨跌停（当期触及涨跌停）
  - [ ] 最小成交额或换手阈值（例如当日成交额 ≥ 1e7 或换手 ≥ 0.5%）
  - [ ] 可配置白名单/黑名单扩展点
- [ ] 权重归一策略（默认 L1：∑|w|=1；可扩展 L2/非负/softmax）
- [ ] 策略运行：POST `/strategies/{id}/run`
  - [ ] 拉取各因子数据（按各自 `selection`）
  - [ ] 逐期横截面：方向一致化 → winsor → 缺失填充 → 标准化（默认 zscore）
  - [ ] 归一化权重加权合成，得到当期综合得分
  - [ ] 输出：每期 Top N 股票列表及分数；运行统计
  - [ ] 支持 `normalization_override`（临时覆盖）

验收
- 对已配置策略执行成功，输出 Top N 结果，符合默认过滤与标准化/归一规则

---

### M7 质量保障与上线
- [ ] 单元测试（数据绑定、缓存、标准化、归一化、越界校验、沙箱限制）
- [ ] API 测试（happy path + 限制/错误场景）
- [ ] E2E 验收用例（从 selection → codegen → validate → test 预览 → 保存 → 策略/配权 → run）
- [ ] 性能与稳定性：缓存命中率、QPS 限制、内存/时间阈值验证
- [ ] 安全检查：token 掩码、AST 黑/白、禁止导入、资源限制
- [ ] 文档：OpenAPI、示例请求体/响应体、错误码定义
- [ ] 可选：Dockerfile 与启动指南

验收
- 测试覆盖核心路径，E2E 通过；具备上线文档与回滚方案

---

### 默认与边界（与 v2-MVP 一致）
- 标准化默认：`zscore` + winsor [1%, 99%] + 缺失按期中位数 + `std` 缩放，策略级可配置
- 测试规模：股票 3–10 支，期次建议 ≤ 8
- 缓存：TTL 24h（默认）
- Selections：本期不引入版本号/变更注释
- 跨接口时间轴对齐：本期不实现，已记录在文档（后续支持近邻/传播窗口）
- `daily`（行情 K 线）动量/波动：下一期再引入，MVP 先跑通基本面多因子

---

### 风险与待决
- TuShare 接口速率与配额波动 → 加强缓存与退避
- 沙箱执行安全边界 → 持续加固黑/白名单与资源限制
- Universe 默认过滤的口径一致性 → 与前端/研究侧确认并锁定默认阈值

