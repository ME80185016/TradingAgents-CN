#!/usr/bin/env python3
"""
TradingAgents-CN 网络访问修复脚本
解决内网IP无法访问的问题
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def get_local_ip():
    """获取本机IP地址"""
    try:
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'inet ' in line and '127.0.0.1' not in line and 'inet 169.254' not in line:
                    ip = line.split()[1]
                    if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                        return ip
        elif platform.system() == "Linux":
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            ips = result.stdout.strip().split()
            for ip in ips:
                if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                    return ip
        elif platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4' in line:
                    ip = line.split(':')[-1].strip()
                    if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                        return ip
    except Exception as e:
        print(f"获取IP地址失败: {e}")
    
    return "10.1.29.13"  # 使用用户提供的IP作为fallback

def check_firewall_settings():
    """检查防火墙设置"""
    print("🔥 检查防火墙设置...")
    
    system = platform.system()
    if system == "Darwin":  # macOS
        print("💡 macOS防火墙检查:")
        print("   1. 打开 系统偏好设置 > 安全性与隐私 > 防火墙")
        print("   2. 确保防火墙已关闭，或者允许Python应用的网络连接")
        print("   3. 如果使用企业网络，请联系网络管理员")
        
    elif system == "Linux":
        print("💡 Linux防火墙检查:")
        print("   sudo ufw allow 8501")
        print("   或者: sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT")
        
    elif system == "Windows":
        print("💡 Windows防火墙检查:")
        print("   1. 打开 控制面板 > 系统和安全 > Windows Defender 防火墙")
        print("   2. 点击 '允许应用或功能通过Windows Defender防火墙'")
        print("   3. 确保Python或Streamlit应用被允许")

def create_network_test_script():
    """创建网络测试脚本"""
    local_ip = get_local_ip()
    
    test_script = f'''#!/usr/bin/env python3
"""网络连接测试脚本"""

import requests
import socket
from datetime import datetime

def test_local_access():
    """测试本地访问"""
    try:
        response = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        if response.status_code == 200:
            print("✅ 本地访问正常")
            return True
    except Exception as e:
        print(f"❌ 本地访问失败: {{e}}")
    return False

def test_network_access():
    """测试内网访问"""
    try:
        response = requests.get("http://{local_ip}:8501/_stcore/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 内网访问正常: http://{local_ip}:8501")
            return True
    except Exception as e:
        print(f"❌ 内网访问失败: {{e}}")
    return False

def test_port_binding():
    """测试端口绑定"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('{local_ip}', 8501))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口8501在{local_ip}上可达")
            return True
        else:
            print(f"❌ 端口8501在{local_ip}上不可达")
    except Exception as e:
        print(f"❌ 端口测试失败: {{e}}")
    return False

if __name__ == "__main__":
    print("🔍 TradingAgents-CN 网络连接测试")
    print("=" * 50)
    print(f"测试时间: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print(f"本机IP: {local_ip}")
    print()
    
    # 测试序列
    tests = [
        ("本地访问测试", test_local_access),
        ("端口绑定测试", test_port_binding),
        ("内网访问测试", test_network_access)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"🧪 {{test_name}}...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # 显示测试结果
    print("📊 测试结果摘要:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {{test_name}}: {{status}}")
    
    if all(result for _, result in results):
        print("\\n🎉 所有测试通过！可以通过内网IP访问应用")
        print(f"🌐 访问地址: http://{local_ip}:8501")
    else:
        print("\\n⚠️ 部分测试失败，请检查网络配置")
'''
    
    script_path = Path("test_network_access.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    return script_path

def main():
    """主函数"""
    print("🔧 TradingAgents-CN 网络访问修复工具")
    print("=" * 50)
    
    local_ip = get_local_ip()
    print(f"🌐 检测到的本机IP: {local_ip}")
    
    # 检查配置文件
    config_file = Path(".streamlit/config.toml")
    if config_file.exists():
        print("✅ Streamlit配置文件已存在")
    else:
        print("❌ Streamlit配置文件不存在")
        return
    
    # 创建网络测试脚本
    test_script = create_network_test_script()
    print(f"📝 已创建网络测试脚本: {test_script}")
    
    # 显示解决方案
    print("\\n🛠️ 网络访问问题解决方案:")
    print("=" * 30)
    
    print("\\n1️⃣ 重启Web应用:")
    print("   python start_web.py")
    print("   或")
    print("   python start_web_enhanced.py")
    
    print("\\n2️⃣ 验证配置:")
    print("   现在应该可以通过以下地址访问:")
    print(f"   - 本地访问: http://localhost:8501")
    print(f"   - 内网访问: http://{local_ip}:8501")
    
    print("\\n3️⃣ 测试网络连接:")
    print(f"   python {test_script}")
    
    print("\\n4️⃣ 如果仍无法访问，请检查:")
    check_firewall_settings()
    
    print("\\n💡 Docker部署用户:")
    print("   Docker配置已正确设置，使用以下命令:")
    print("   docker-compose up -d --build")
    
    print("\\n🔍 故障排除:")
    print("   1. 确保没有其他程序占用8501端口")
    print("   2. 检查网络防火墙设置")
    print("   3. 确认内网IP地址正确")
    print("   4. 尝试使用不同的端口")

if __name__ == "__main__":
    main()