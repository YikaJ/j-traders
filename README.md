# 量化主观选股系统

一个基于React + FastAPI的量化选股系统，支持自定义Python因子、策略回测和实时监控。

## 项目结构

```
j-traders/
├── backend/                 # Python FastAPI后端
│   ├── app/                # 应用主目录
│   ├── requirements.txt    # Python依赖
│   ├── setup.sh           # 自动化设置脚本
│   ├── README.md          # 后端专用文档
│   └── main.py            # FastAPI入口文件
├── frontend/               # React TypeScript前端
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   ├── vite.config.ts     # Vite配置
│   └── tsconfig.json      # TypeScript配置
├── docs/                  # 项目文档
├── .kiro/                 # Kiro工作流程文档
└── README.md              # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 18+
- pnpm (推荐) 或 npm

### 2. 后端设置

#### 方法一：使用自动化脚本（推荐）

```bash
# 进入后端目录
cd backend

# 运行设置脚本
chmod +x setup.sh
./setup.sh
```

#### 方法二：手动设置

```bash
# 进入后端目录
cd backend

# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建环境配置文件
cp .env.example .env
# 编辑 .env 文件，配置你的 Tushare Token

# 初始化数据库
python init_db.py

# 运行开发服务器
python main.py
```

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖（推荐使用 pnpm）
pnpm install
# 或使用 npm
npm install

# 启动开发服务器
pnpm dev
# 或使用 npm
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看前端应用。

## 功能特性

- 🏛️ **大盘监控**: 实时监控主要指数和自选股价格
- 🧮 **量化选股**: 自定义Python因子，多因子策略组合
- 📊 **专业图表**: 基于Plotly的K线图和技术指标
- 💾 **数据管理**: Tushare数据集成，SQLite本地存储
- 🔒 **安全执行**: RestrictedPython安全执行用户代码
- ⚡ **现代化开发**: Vite + React 19 提供更快的开发体验

## 技术栈

### 后端
- **FastAPI**: 现代高性能Web框架
- **SQLAlchemy**: ORM数据库操作
- **Tushare**: 金融数据源
- **SQLite**: 轻量级数据库

### 前端
- **React 19**: 最新版本UI框架
- **TypeScript**: 类型安全
- **Vite**: 现代化构建工具
- **Ant Design**: 企业级UI组件
- **Plotly.js**: 专业图表库
- **pnpm**: 快速包管理器

## 开发指南

### 后端开发

```bash
cd backend

# 启动开发服务器
python main.py

# 代码格式化
black .

# 代码检查
flake8 .

# 运行测试
pytest
```

### 前端开发

```bash
cd frontend

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 运行测试
pnpm test

# 预览构建结果
pnpm preview
```

### 开发环境特性

- **热重载**: 前后端都支持代码变更自动重载
- **API代理**: 前端开发服务器自动代理API请求到后端
- **TypeScript**: 完整的类型检查和智能提示
- **ESLint**: 代码质量检查

详细的开发文档请参考：
- [需求文档](.kiro/specs/quantitative-stock-selection/requirements.md)
- [架构设计](.kiro/specs/quantitative-stock-selection/design.md)
- [任务规划](.kiro/specs/quantitative-stock-selection/tasks.md)

## 许可证

MIT License
