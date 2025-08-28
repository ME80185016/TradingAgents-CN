#!/usr/bin/env python3
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
        print(f"❌ 本地访问失败: {e}")
    return False

def test_network_access():
    """测试内网访问"""
    try:
        response = requests.get("http://10.1.29.13:8501/_stcore/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 内网访问正常: http://10.1.29.13:8501")
            return True
    except Exception as e:
        print(f"❌ 内网访问失败: {e}")
    return False

def test_port_binding():
    """测试端口绑定"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('10.1.29.13', 8501))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口8501在10.1.29.13上可达")
            return True
        else:
            print(f"❌ 端口8501在10.1.29.13上不可达")
    except Exception as e:
        print(f"❌ 端口测试失败: {e}")
    return False

if __name__ == "__main__":
    print("🔍 TradingAgents-CN 网络连接测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"本机IP: 10.1.29.13")
    print()
    
    # 测试序列
    tests = [
        ("本地访问测试", test_local_access),
        ("端口绑定测试", test_port_binding),
        ("内网访问测试", test_network_access)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"🧪 {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # 显示测试结果
    print("📊 测试结果摘要:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    if all(result for _, result in results):
        print("\n🎉 所有测试通过！可以通过内网IP访问应用")
        print(f"🌐 访问地址: http://10.1.29.13:8501")
    else:
        print("\n⚠️ 部分测试失败，请检查网络配置")
