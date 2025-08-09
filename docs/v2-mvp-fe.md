## V2 前端 MVP 需求拆解（v2-mvp-fe）

本稿面向 V2 版本的最小可用前端，围绕三个路由（大盘监控/因子库/策略库），给出信息架构、页面/交互设计、与现有 backend-v2 的 API 映射，以及必要的后端小改项。前端实现遵循组件解耦与可复用优先（列表、表单、编辑器、对话框等），代码编辑统一采用 Monaco 编辑器以获得良好开发体验与语法高亮。

范围边界：本期暂不实现“大盘监控”的具体功能，仅保留路由与骨架，主力建设“因子库”“策略库”。

---

### 全局对接前提

- 后端服务：FastAPI（`backend-v2/app/main.py`），提供 `/health`、`/catalog`、`/factors`、`/standardize`、`/strategies`、`/universe` 等。
- CORS：需在后端启用 `CORSMiddleware`（按环境变量配置允许来源），否则浏览器前端会被同源策略拦截。
- 环境变量：参考 `docs/configuration.md`。开发期至少设置 `API_HOST`/`API_PORT`；如需真实拉取样本/Universe，配置 `TUSHARE_TOKEN`。
- 编辑器：前端代码编辑统一使用 Monaco Editor（便于语法高亮、折叠与快捷键）。

---

## 路由与信息架构

顶层导航与路由：
- `/dashboard`（大盘监控）— 本期仅占位骨架（导航 + 空态/说明）。
- `/factors`（因子库）
  - `/factors/list` 因子列表
  - `/factors/new` 新增因子（向导）
  - `/factors/:id` 因子详情（查看/编辑/删除）
- `/strategies`（策略库）
  - `/strategies/list` 策略列表
  - `/strategies/new` 新增策略（向导）
  - `/strategies/:id` 策略详情（查看/编辑/运行）

全局能力：
- 分页与排序（后端暂不分页，先前端分页；后续对接服务端分页）。
- 统一通知（成功/错误提示）、空态与加载骨架。
- 统一确认对话框（删除/覆盖等危险操作）。
- 统一异常兜底：展示后端错误 `error/message`，并在控制台输出完整响应便于排查。

---

## 因子库（Factors）

### 列表页 `/factors/list`
- 目标：快速浏览自己创建过的因子，查看分类（Category）、关联选择集（Selection）、使用字段与创建时间。
- 数据来源：`GET /factors`（后端：`persist.router.get_factors`）。
- 表格字段（建议）：
  - 名称（`name`）
  - 分类（Category → 对应后端 `tags`；多选，以标签样式显示）
  - 使用字段计数（`fields_used.length`，点击可展开查看）
  - 选择集（从 `selection.factor_slug` 或简要概览生成，点击查看详情）
  - 创建时间（`created_at`）
  - 操作（查看/编辑、删除）
- 交互：
  - 顶部“新增因子”跳转 `/factors/new`。
  - 行点击进入 `/factors/:id`。
  - 搜索（名称/标签/字段名模糊）；标签侧边筛选。

### 详情页 `/factors/:id`
- 数据来源：`GET /factors/{id}`。
- 结构：
  - 基本信息：名称、分类（tags）、描述。
  - 选择集（Selection）预览：以可读卡片展示 `output_index`、所含 endpoint/fields、`param_binding` 概要。
  - 代码编辑：Monaco Editor 展示 `code_text`，只读/编辑切换。
  - 快速校验：按钮触发 `POST /factors/validate`（入参：`selection` + `code_text`）。
  - 快速测试：
    - 参数：`ts_codes`、`start_date`、`end_date`、`top_n`、可选 `normalization`（用于预览，不落库）。
    - 调用：`POST /factors/test`，返回样例行与诊断（均值/标准差/偏度/峰度/缺失率）。
  - 标准化预览：如仅对已有数据做 zscore 预览，可调用 `POST /standardize/zscore`。
  - 操作区：保存（PUT）、删除（DELETE）。
- 后端小改项（CRUD 补全）：
  - 现状：有 `POST /factors`、`GET /factors`、`GET /factors/{id}`；无更新/删除。
  - 建议新增：`PUT /factors/{id}`、`DELETE /factors/{id}`；前端编辑/删除据此实现完整 CRUD。

### 新增向导 `/factors/new`
- Step 1 基本信息
  - 名称（必填）
  - 分类（Category）：多选标签（对应后端 `tags`）
  - 描述（可选）
- Step 2 选择集（Selections）
  - 选择已有 Selection：
    - 下拉选择 `selection_slug`（来源 `GET /catalog/selections`）；
    - 详情预览（`GET /catalog/selections/{slug}`）。
  - 或创建新的 Selection：可视化“选择集编辑器”（见下文“Selections 在前端的呈现”）。
- Step 3 因子代码生成（Coding Agent 协作）
  - “需求说明”文本区域（Textarea），用于书写 `user_factor_spec`；
  - 点击“生成代码”→ 调用 `POST /factors/codegen`：
    - 入参：`selection_slug` 或完整 `selection`、`user_factor_spec`、`coding_prefs?`；
    - 返回：`{ code_text, fields_used, notes }`；
  - 生成后在 Monaco Editor 中展示/可编辑；
  - “校验”→ `POST /factors/validate`；
  - “快速测试”→ `POST /factors/test`（小样本/短时间窗）。
- Step 4 保存
  - `POST /factors`：提交 `name/desc/code_text/fields_used/tags/selection/normalization?`；
  - 成功后跳转 `/factors/:id`。

#### Selections 在前端的呈现（建议实现）

Selections 是“因子数据输入契约”的前置勾选，包含：数据源端点、字段、`param_binding`、输出索引等。前端提供两种视图：

1) 选择现有规范（简单模式）
- 直接选择 `selection_slug`；展示卡片化摘要：
  - `output_index`（如 `["ts_code","trade_date"]`）
  - 端点与字段（如 `daily_basic`: `pe_ttm`, `pb`）
  - 参数绑定摘要（从请求/固定/派生而来）

2) 可视化编辑器（进阶模式）
- 多段式表单：
  - 选择端点：数据来源 `GET /catalog/endpoints`（名称/描述/频率/轴/示例）。
  - 勾选字段：从端点字段清单中多选；可关键词搜索（如 `pe_ttm`）。
  - 参数绑定：为 `start_date/end_date/ts_code/period` 等设置“绑定来源”（固定值/来自请求参数/派生）。
  - 输出索引：选择 `[ts_code, trade_date]` 或 `[ts_code, end_date]`。
  - 连接键（join_keys）：多端点时声明对齐字段。
- 保存为 selection JSON（允许“另存为”），并持久化 `POST /catalog/selections`（后端已支持）。

注意：后端因子执行与校验都依赖 selection。以此方式，用户无需直接编辑 JSON，也能完成选择集构建；同时保留“高级/JSON”切换，供资深用户直接编辑原始 JSON。

---

## 策略库（Strategies）

### 列表页 `/strategies/list`
- 目标：总览策略与创建时间，快速进入详情/运行。
- 数据来源（建议）：`GET /strategies`（后端当前缺失，建议新增简单列表接口）。
- 列：名称、创建时间、已配置因子数、操作（查看/运行）。

### 详情页 `/strategies/:id`
- 数据来源：`GET /strategies/{id}`。
- 结构：
  - 基本信息：名称、创建时间。
  - 标准化策略（NormalizationPolicy）：展示/编辑（方法、winsor、fill、by 等）；保存：`PUT /strategies/{id}/normalization`。
  - 因子与权重：
    - 列表展示关联因子（从 `/factors` 选择加入，或在“新建策略”阶段配置）；
    - 权重编辑：支持正负；保存调用 `PUT /strategies/{id}/weights`（后端会自动 L1 归一）。
  - 运行与诊断：
    - 参数：`ts_codes?`、`industry?`、`all?`、`start_date`、`end_date`、`top_n`、`per_date_top_n?`、`diagnostics.enabled?`；
    - 调用：`POST /strategies/{id}/run` → 返回 `results`、`group_by`、`per_date_results?`、`diagnostics?`（IC/RankIC/覆盖率等）。
    - 结果展示：
      - 全局 Top N 表格（默认按 score 降序）；
      - 逐期 Top N（可折叠）；
      - 诊断卡片：IC/RankIC/覆盖率；
      - 导出（CSV）。
- 后端小改项（补齐 Universe 过滤）：
  - 现状：`/strategies/{id}/run` 支持 `ts_codes`；未显式处理 `industry`/`all`。
  - 建议：
    - 支持 body 中 `industry`（用 `/universe/stocks?industry=...` 取代码集）与 `all=true`（取全量 Universe）；
    - 支持 `per_date_top_n`（已存在，保留）。

### 新增向导 `/strategies/new`
- Step 1 基本信息：名称。
- Step 2 选择因子：从因子库多选（支持搜索/标签过滤）。
- Step 3 权重与标准化：
  - 权重编辑：允许任意实数；保存时调用 `PUT /strategies/{id}/weights`（后端归一处理）。
  - 标准化：选择方法（zscore/robust_zscore/rank/minmax 预留）、winsor、fill、by（默认按主时间轴）。
- Step 4 保存：`POST /strategies` → 返回 `id`，随后跳至 `/strategies/:id` 补全权重/标准化并保存。

---

## 后端 API 映射（关键交互）

因子库：
- 列表：`GET /factors`
- 详情：`GET /factors/{id}`
- 新增：`POST /factors`
- 更新：建议新增 `PUT /factors/{id}`（缺口）
- 删除：建议新增 `DELETE /factors/{id}`（缺口）
- 代码生成：`POST /factors/codegen`
- 校验：`POST /factors/validate`
- 快速测试：`POST /factors/test`

选择集：
- 列表：`GET /catalog/selections`
- 详情：`GET /catalog/selections/{slug}`
- 新建：`POST /catalog/selections`
- 更新：`PUT /catalog/selections/{slug}`
- 端点与字段检索：`GET /catalog/endpoints`、`GET /catalog/endpoints/{name}`、`GET /catalog/fields/search?q=`

策略库：
- 新建：`POST /strategies`
- 更新权重：`PUT /strategies/{id}/weights`（服务端自动 L1 归一）
- 更新标准化：`PUT /strategies/{id}/normalization`
- 详情：`GET /strategies/{id}`
- 列表：建议新增 `GET /strategies`（缺口）
- 运行：`POST /strategies/{id}/run`（建议增强：支持 `industry`/`all` 的 Universe 过滤）

Universe：
- 同步：`POST /universe/sync`
- 查询：`GET /universe/stocks`（支持过滤）、`GET /universe/stocks/{ts_code}`

标准化：
- `POST /standardize/zscore`（用于测试/可视化预览）

---

## UI 组件与技术要点

- 使用 React + AntDesign5.0 实现
- Monaco Editor（代码编辑）：
  - 用于因子代码的生成、编辑与校验；支持只读/编辑模式切换；
  - 代码片段高亮、折叠、搜索、格式化、行号定位。
- 表格：
  - Ant Design Table
  - 大列表前端分页；列宽拖拽；固定列；
  - 行展开支持展示 `fields_used`/`selection` 摘要；
  - 批量选择（删除/导出）。
- 表单：
  - Ant Design Form
  - 分步向导（新增因子/策略）；
  - 动态校验与禁用状态（调用中）；
  - 失败后定位到出错字段并提示。
- 图表（可选）：
  - Ant Design Chart
  - 策略诊断：IC/RankIC/覆盖率的小型趋势图；
  - 结果分布（直方/箱线，后续版本再引入）。

---

## 权限与安全（MVP）

- 本期可不做鉴权（内网/本机开发）；如需公网演示，建议补充 API Key/JWT。
- 统一错误：展示后端 `message`，并隐藏敏感信息（后端已屏蔽 token）。
- 速率与缓存：尽量通过后端；前端避免高频轮询（运行策略按钮使用一次性触发）。

---

## 验收标准（FE 版）

- 路由可达：`/dashboard`（骨架），`/factors/*`、`/strategies/*` 可用。
- 因子库：
  - 能列表、搜索与查看详情；
  - 新增因子：通过选择集 + Coding Agent 生成代码，能校验与快速测试，最终保存成功；
  - 能编辑与删除（依赖后端 `PUT/DELETE /factors/{id}`）。
- 选择集：
  - 能从已存选择集选择；
  - 能通过可视化编辑器构建新的选择集并保存；
  - 能在因子详情中以卡片形式查看其选择集。
- 策略库：
  - 能创建策略、配置因子权重与标准化，并保存；
  - 能运行策略，展示 Top N 与（可选）逐期 Top N，能显示诊断（IC/RankIC/覆盖率）。
- 运行过滤：
  - 能选择全量/行业/指定股票集三种方式之一（取决于后端增强落地进度，至少支持 `ts_codes`）。
- CORS：浏览器端可直接对后端 API 进行跨域请求。

---

## 后端小改项清单（优先级从高到低）

1) 启用 CORS 中间件（高）
- 允许来源由环境变量配置，开发期可 `*`，生产期收敛为前端域名列表。

2) 因子 CRUD 完整化（高）
- 新增：`PUT /factors/{id}`、`DELETE /factors/{id}`。

3) 策略列表接口（中）
- 新增：`GET /strategies` 返回 `[{ id, name, created_at }]`。

4) 策略运行的 Universe 过滤（中）
- `POST /strategies/{id}/run` 支持 body：`industry`、`all=true`；
- 若传 `industry`：调用 `/universe/stocks?industry=...` 得到 `ts_codes`；
- 若 `all=true`：从 `/universe/stocks` 拉取全量（考虑分页/批量）。

5) 服务端分页（低）
- 对 `/factors`、`/universe/stocks`、`/strategies`（新）等提供 `page/page_size/sort_by/sort_dir`，以便前端长远扩展。

---

## 里程碑拆分（建议）

- M0：前端脚手架与路由、CORS、健康页联通；因子列表只读。
- M1：Selections 列表 + 详情预览；因子新增向导（能选择 selection 与生成/校验代码）。
- M2：因子快速测试与保存；因子详情编辑。
- M3：策略新建与权重/标准化配置；策略详情查看。
- M4：策略运行（至少支持 `ts_codes`）；展示 Top N；基础诊断展示。
- M5：补齐因子/策略的删除；策略运行支持 `industry`/`all`；列表分页。

---

## 术语对齐

- Category ↔ 后端 `tags`（因子可多分类标签）。
- Selection（选择集）↔ 因子数据输入契约（端点/字段/参数绑定/输出索引）。
- Normalization ↔ 标准化策略（winsor/fill/by/method 等），策略级统一配置，可被运行时临时覆盖。

---

## 备注

- 代码编辑统一采用 Monaco Editor，以满足专业代码编辑需求（高亮/折叠/快捷键/查找替换）。
- 因子库遵循“可配置因子公式”体系，前端仅管理与展示用户公式（而非内置硬编码），后端以沙箱与校验保证安全执行。


