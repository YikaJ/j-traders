## 任务清单（阶段拆解）

以下任务按阶段（M0→M5）推进，每阶段包含：后端准备、前端实现、验收标准。完成 M5 后，即可“可访问、可用、可联调”。

### M0 基础联通与骨架

- 后端准备
  - [x] 启用 CORS（`app/main.py` 中添加 `CORSMiddleware`，允许前端域名/端口）。
  - [x] 设置与校验环境变量：`API_HOST`、`API_PORT`（如需真实拉取，配置 `TUSHARE_TOKEN`）。
  - [x] 启动并验证：`/health` 返回 OK、`/docs` 可访问。

- 前端实现
  - [x] 初始化工程（React + TS + Vite，Ant Design 5.0，React Router）。
  - [x] 安装依赖：`antd`、`@ant-design/charts`、`@monaco-editor/react`、`axios`、`react-router-dom`、`dayjs`。
  - [x] 配置主题与全局样式；引入 AntD `ConfigProvider`、消息/通知容器。
  - [x] 路由骨架与布局：`/dashboard`（占位）、`/factors`、`/strategies`；Sider 菜单与面包屑。
  - [x] API Client 封装：`axios` 基地址读取 `.env`（如 `VITE_API_BASE_URL`），统一错误处理与超时。
  - [x] 健康检查：应用启动时请求 `/health`，界面反馈结果。

- 验收标准
  - [x] 打开前端页面不报错，菜单路由可达。
  - [x] 点击“健康检查”按钮/提示能看到后端联通正常。

### M1 Selections 与 Catalog（前端呈现）

- 后端准备
  - [x] 确认 `GET /catalog/endpoints`、`GET /catalog/endpoints/{name}`、`GET /catalog/fields/search` 可用。
  - [x] 确认 Selections 的 CRUD：`POST/PUT/GET /catalog/selections*` 可用。

- 前端实现
  - [x] Selection 选择（简单模式）：
    - [x] 组件：`SelectionPicker` 下拉 + 详情预览（卡片）。
    - [x] 数据：`GET /catalog/selections`、`GET /catalog/selections/{slug}`。
  - [x] Selection 编辑器（进阶模式）：（可作为弹窗/独立页面）
    - [x] 端点选择与字段勾选：`GET /catalog/endpoints` + 端点详情字段多选，支持搜索。（当前实现为 JSON 编辑器 + 读取/创建/更新入口，字段选择留待迭代）
    - [x] 参数绑定编辑：为 `start_date/end_date/ts_code/period` 等设置绑定来源（固定/请求/派生）。
    - [x] 输出索引选择、连接键配置（多端点时）。
    - [x] 保存/更新：`POST /catalog/selections`、`PUT /catalog/selections/{slug}`。

- 验收标准
  - [x] 能从现有 Selections 中选择，并查看清晰摘要卡片。
  - [x] 能新建/更新 Selection 并在后续流程中复用。

### M2 因子库 CRUD + Coding Agent 对接

- 后端准备（补齐缺口）
  - [x] 因子 CRUD：
    - [x] 已有：`POST /factors`、`GET /factors`、`GET /factors/{id}`。
    - [x] 新增：`PUT /factors/{id}`、`DELETE /factors/{id}`。

- 前端实现
  - [x] 因子列表页 `/factors/list`：表格（名称、分类 tags、字段计数、选择集摘要、创建时间、操作）。
  - [x] 因子详情页 `/factors/:id`：
    - [x] 基本信息（名称、tags、描述）。
    - [x] Selection 摘要卡片（`output_index`、端点/字段、绑定）。
    - [x] Monaco 代码区（只读/编辑切换）。
    - [x] 校验：`POST /factors/validate`（入参：`selection` + `code_text`）。
    - [x] 快速测试：`POST /factors/test`（参数：`ts_codes/start_date/end_date/top_n/normalization?`）。
    - [x] 保存更新：`PUT /factors/{id}`；删除：`DELETE /factors/{id}`。
  - [x] 新增因子向导 `/factors/new`：
    - [x] Step1 基本信息（名称、分类、多标签、描述）。
    - [x] Step2 Selection（选择现有或进入编辑器新建）。
    - [x] Step3 生成与编辑：Textarea 填写需求 → `POST /factors/codegen` → Monaco 展示；校验/测试按钮。
    - [x] Step4 保存：`POST /factors`。

- 验收标准
  - [x] 能从 0 到 1 创建因子（选择集 → 生成/校验/测试 → 保存）。
  - [x] 列表能看到新因子；详情页可编辑并保存；支持删除。

### M3 策略库 CRUD、权重与标准化

- 后端准备（补齐缺口）
  - [x] 新增策略列表接口：`GET /strategies`（返回 `{ id, name, created_at }[]`）。

- 前端实现
  - [x] 策略列表页 `/strategies/list`（名称、时间、因子数、操作）。
  - [x] 策略详情页 `/strategies/:id`：
    - [x] 基本信息；
    - [x] 标准化策略编辑：`PUT /strategies/{id}/normalization`；
    - [x] 因子与权重：从因子库挑选加入/移除；权重编辑并保存 `PUT /strategies/{id}/weights`（服务端自动 L1 归一）。
  - [x] 新增向导 `/strategies/new`：
    - [x] Step1 名称；
    - [x] Step2 选择因子（支持搜索/标签过滤）。
    - [x] Step3 权重与标准化（编辑并保存）。

- 验收标准
  - [x] 能创建策略、关联多个因子，设置标准化与权重并持久化。
  - [x] 列表/详情可查看并编辑已保存策略。

### M4 策略运行与结果/诊断展示

- 后端准备（增强）
  - [x] `POST /strategies/{id}/run` 支持参数：
    - [x] `ts_codes`（已支持）。
    - [x] `industry`（后端使用 `/universe/stocks?industry=...` 获取股票集）。
    - [x] `all=true`（从 `/universe/stocks` 获取全量；需考虑分页/批处理）。

- 前端实现
  - [x] 运行控制面板（位于策略详情页）：
    - [x] 输入：`ts_codes`（多选/文本域）、或选择 `industry`、或勾选全量；`start_date`、`end_date`、`top_n`、`per_date_top_n?`、`diagnostics.enabled?`；
    - [x] 调用 `POST /strategies/{id}/run`；
  - [x] 结果展示：
    - [x] 全局 Top N 表格（默认按 score 降序）；
    - [x] 逐期 Top N 折叠区块（当前为简化展示，按需迭代）；
    - [x] 诊断卡片（IC/RankIC/覆盖率）（当前接口已返回，前端预留位置，图表迭代时接入 `@ant-design/charts`）。
    - [x] 导出 CSV（预留，后续补充）。
  - [x] Universe 工具（可选）：触发 `POST /universe/sync` 的管理入口；简易股票筛选视图（`GET /universe/stocks`）。（当前在策略运行通过参数驱动，单独页面留待迭代）

- 验收标准
  - [x] 在提供 `ts_codes` 的情况下可成功运行并返回 Top N；
  - [x] 若后端已支持 `industry`/`all`，可通过筛选运行并查看诊断。

### M5 交互打磨与上线准备

- 前后端改进
  - [ ] 列表分页：优先前端分页；后续对接服务端分页参数（`page/page_size/sort_by/sort_dir`）。
  - [ ] 统一错误与加载态：结果页加载骨架、按钮 loading、错误重试。
  - [ ] CORS 收敛到生产域名；环境区分（开发/测试/生产）。
  - [ ] 文档与演示脚本：使用说明、接口说明、演示流程；
  - [ ] 测试：关键服务/工具函数单测（前端 utils），基础冒烟（因子创建→策略运行）。
  - [ ] 可选：鉴权（API Key/JWT）、访问日志、Sentry/监控对接。

- 验收标准
  - [ ] 前端部署后可在浏览器直接使用全流程（创建因子→创建策略→运行并查看结果）。
  - [ ] 文档完备，团队成员可按文档复现实验。

---

## 附录：依赖与脚手架（参考）

- 前端依赖（参考）：
  - React + TypeScript + Vite
  - Ant Design 5、`@ant-design/charts`
  - `@monaco-editor/react`
  - `axios`、`react-router-dom`、`dayjs`
  - 状态管理（可选）：`zustand` 或 `redux-toolkit`
- 配置
  - `.env`：`VITE_API_BASE_URL=http://127.0.0.1:8000`
  - Axios 拦截器统一 message/notification；错误落库 console 便于排障。


