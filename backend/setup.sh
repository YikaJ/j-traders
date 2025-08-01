#!/bin/bash

# J-Traders 后端设置脚本

echo "🚀 开始设置 J-Traders 后端环境..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 1 ]]; then
    echo "✅ Python 版本检查通过: $(python3 --version)"
else
    echo "❌ 需要 Python 3.8 或更高版本"
    exit 1
fi

# 检查 pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip 已安装"
else
    echo "❌ pip 未安装，请先安装 pip"
    echo "提示: 大多数 Python 安装都包含 pip，如果没有，请参考: https://pip.pypa.io/en/stable/installation/"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "⬆️ 升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装项目依赖..."
pip install -r requirements.txt

# 创建环境配置文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建环境配置文件..."
    cat > .env << EOF
# 数据库配置
DATABASE_URL=sqlite:///./quantitative_stock.db

# Tushare API 配置
TUSHARE_TOKEN=your_tushare_token_here

# 应用配置
DEBUG=True
LOG_LEVEL=INFO

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 安全配置
SECRET_KEY=your_secret_key_here
EOF
    echo "✅ 环境配置文件已创建 (.env)"
    echo "⚠️  请编辑 .env 文件，配置你的 Tushare Token"
else
    echo "✅ 环境配置文件已存在"
fi

# 初始化数据库
echo "🗄️ 初始化数据库..."
python init_db.py

echo "🎉 设置完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，配置你的 Tushare Token"
echo "2. 运行: python main.py"
echo "3. 访问: http://localhost:8000"
echo ""
echo "开发命令："
echo "- 启动服务: python main.py"
echo "- 代码格式化: black ."
echo "- 代码检查: flake8 ."
echo "- 运行测试: pytest" 