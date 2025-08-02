#!/usr/bin/env python3
"""
后端环境设置脚本
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """运行命令并显示描述"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description}完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description}失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    """主函数"""
    print("🚀 开始设置量化选股系统后端环境")
    
    # 检查Python版本
    if sys.version_info < (3, 9):
        print("❌ 需要Python 3.9或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 创建虚拟环境
    if not Path("venv").exists():
        if not run_command("python3 -m venv venv", "创建虚拟环境"):
            sys.exit(1)
    else:
        print("✅ 虚拟环境已存在")
    
    # 根据操作系统确定激活脚本
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        pip_command = "venv\\Scripts\\pip"
    else:  # macOS/Linux
        activate_script = "source venv/bin/activate"
        pip_command = "venv/bin/pip"
    
    # 升级pip
    if not run_command(f"{pip_command} install --upgrade pip", "升级pip"):
        sys.exit(1)
    
    # 安装依赖
    if not run_command(f"{pip_command} install -r requirements.txt", "安装Python依赖"):
        sys.exit(1)
    
    # 创建.env文件（如果不存在）
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "创建.env配置文件")
            print("⚠️  请编辑.env文件，设置您的Tushare Token")
        else:
            print("⚠️  .env.example文件不存在")
    
    # 创建必要的目录
    Path("logs").mkdir(exist_ok=True)
    print("✅ 创建logs目录")
    
    print("\n🎉 后端环境设置完成！")
    print("\n📝 下一步操作：")
    print("1. 编辑.env文件，设置您的Tushare Token")
    print("2. 激活虚拟环境：")
    if os.name == 'nt':
        print("   Windows: venv\\Scripts\\activate")
    else:
        print("   macOS/Linux: source venv/bin/activate")
    print("3. 启动开发服务器: python main.py")
    print("4. 访问API文档: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    main() 