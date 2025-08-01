# 量化主观选股系统

一个基于React + FastAPI的量化选股系统，支持自定义Python因子、策略回测和实时监控。

## 项目结构

```
quantitative-stock-selection/
├── backend/                 # Python FastAPI后端
│   ├── app/                # 应用主目录
│   ├── requirements.txt    # Python依赖
│   ├── .env.example       # 环境变量示例
│   └── main.py            # FastAPI入口文件
├── frontend/               # React TypeScript前端
│   ├── src/               # 源代码
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   └── tsconfig.json      # TypeScript配置
├── docs/                  # 项目文档
├── .kiro/                 # Kiro工作流程文档
└── README.md              # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

### 2. 后端设置

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

# 运行开发服务器
python main.py
```

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

## 功能特性

- 🏛️ **大盘监控**: 实时监控主要指数和自选股价格
- 🧮 **量化选股**: 自定义Python因子，多因子策略组合
- 📊 **专业图表**: 基于Plotly的K线图和技术指标
- 💾 **数据管理**: Tushare数据集成，SQLite本地存储
- 🔒 **安全执行**: RestrictedPython安全执行用户代码

## 技术栈

### 后端
- **FastAPI**: 现代高性能Web框架
- **SQLAlchemy**: ORM数据库操作
- **Tushare**: 金融数据源
- **SQLite**: 轻量级数据库

### 前端
- **React 18**: 现代UI框架
- **TypeScript**: 类型安全
- **Ant Design**: 企业级UI组件
- **Plotly.js**: 专业图表库

## 开发指南

详细的开发文档请参考：
- [需求文档](.kiro/specs/quantitative-stock-selection/requirements.md)
- [架构设计](.kiro/specs/quantitative-stock-selection/design.md)
- [任务规划](.kiro/specs/quantitative-stock-selection/tasks.md)

## 许可证

MIT License
