# J-Traders 后端服务

## 环境要求

- Python 3.8+
- pip (Python 包管理器)

## 快速开始

### 1. 创建虚拟环境

```bash
# 使用 venv (推荐)
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 确保 pip 是最新版本
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件并配置必要的环境变量：

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

### 4. 数据库初始化

```bash
# 初始化数据库
python init_db.py
```

### 5. 启动服务

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 开发工具

项目包含以下开发工具：

- **代码格式化**: `black .`
- **代码检查**: `flake8 .`
- **导入排序**: `isort .`
- **类型检查**: `mypy .`
- **测试**: `pytest`

## 项目结构

```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 核心配置
│   ├── db/           # 数据库模型
│   ├── schemas/      # 数据验证模式
│   └── services/     # 业务服务
├── logs/             # 日志文件
├── requirements.txt   # 项目依赖
├── main.py           # 应用入口
└── init_db.py        # 数据库初始化
```

## 注意事项

- 确保使用虚拟环境避免依赖冲突
- 定期更新依赖包以获取安全补丁
- 在生产环境中使用 `requirements.txt` 锁定版本号 