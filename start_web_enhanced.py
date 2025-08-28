#!/usr/bin/env python3
"""
TradingAgents-CN 增强启动脚本
自动检查并安装缺失的依赖包
"""

import os
import sys
import subprocess
from pathlib import Path

def check_virtual_env():
    """检查是否在虚拟环境中运行"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def install_package(package_name):
    """安装Python包"""
    try:
        print(f"🔄 正在安装 {package_name}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                      check=True, capture_output=True, text=True)
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e.stderr}")
        return False

def check_and_install_dependencies():
    """检查并安装依赖包"""
    print("🔍 检查依赖包...")
    
    # 核心依赖
    core_dependencies = [
        "streamlit",
        "plotly", 
        "pandas",
        "numpy",
        "requests"
    ]
    
    # LLM相关依赖
    llm_dependencies = [
        "langchain",
        "langchain-core",
        "langchain-openai",
        "langchain-anthropic",
        "langchain-google-genai"
    ]
    
    # 数据库依赖
    db_dependencies = [
        "redis",
        "pymongo"
    ]
    
    missing_packages = []
    
    # 检查核心依赖
    for package in core_dependencies:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} 缺失")
            missing_packages.append(package)
    
    # 检查LLM依赖
    for package in llm_dependencies:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"⚠️ {package} 缺失 (LLM支持)")
            missing_packages.append(package)
    
    # 检查数据库依赖（可选）
    for package in db_dependencies:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"📝 {package} 缺失 (可选功能)")
    
    # 安装缺失的包
    if missing_packages:
        print(f"\n🛠️ 发现 {len(missing_packages)} 个缺失的依赖包")
        
        if not check_virtual_env():
            print("⚠️ 强烈建议在虚拟环境中安装依赖:")
            print("   source env/bin/activate")
            print("   然后重新运行此脚本")
            response = input("是否继续在系统环境中安装? (y/N): ")
            if response.lower() != 'y':
                return False
        
        failed_packages = []
        for package in missing_packages:
            if not install_package(package):
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n❌ 以下包安装失败: {', '.join(failed_packages)}")
            print("💡 请手动安装:")
            print(f"   pip install {' '.join(failed_packages)}")
            return False
        else:
            print("\n🎉 所有依赖包安装成功!")
    
    return True

def main():
    """主函数"""
    print("🚀 TradingAgents-CN 增强启动器")
    print("=" * 50)
    
    # 检查虚拟环境
    if check_virtual_env():
        print("✅ 虚拟环境已激活")
    else:
        print("⚠️ 未检测到虚拟环境")
        print("💡 建议使用虚拟环境:")
        print("   source env/bin/activate")
        print()
    
    # 检查并安装依赖
    if not check_and_install_dependencies():
        print("❌ 依赖检查失败，无法启动应用")
        return
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    web_dir = project_root / "web"
    app_file = web_dir / "app.py"
    
    # 检查应用文件
    if not app_file.exists():
        print(f"❌ 找不到应用文件: {app_file}")
        return
    
    # 设置环境变量
    env = os.environ.copy()
    current_path = env.get('PYTHONPATH', '')
    if current_path:
        env['PYTHONPATH'] = f"{project_root}{os.pathsep}{current_path}"
    else:
        env['PYTHONPATH'] = str(project_root)
    
    # 构建启动命令
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_file),
        "--server.port", "8501",
        "--server.address", "localhost", 
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none"
    ]
    
    print("\n🌐 启动Web应用...")
    print("📱 浏览器将自动打开 http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, cwd=project_root, env=env)
    except KeyboardInterrupt:
        print("\n⏹️ Web应用已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        print("\n💡 故障排除:")
        print("   1. 确保虚拟环境已激活")
        print("   2. 运行: pip install -r requirements.txt")
        print("   3. 检查.env配置文件")

if __name__ == "__main__":
    main()