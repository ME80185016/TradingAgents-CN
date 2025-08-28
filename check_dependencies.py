#!/usr/bin/env python3
"""
TradingAgents-CN 依赖检查脚本
检查所有LLM提供商的依赖是否正确安装
"""

import sys
import importlib

def check_module(module_name, description):
    """检查模块是否可以导入"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {description} | 错误: {str(e)}")
        return False

def main():
    print("🔍 TradingAgents-CN 依赖检查")
    print("=" * 60)
    
    # 核心依赖
    print("\n📦 核心依赖:")
    core_modules = [
        ("streamlit", "Web界面框架"),
        ("pandas", "数据处理"),
        ("numpy", "数值计算"),
        ("plotly", "图表显示")
    ]
    
    core_ok = True
    for module, desc in core_modules:
        if not check_module(module, desc):
            core_ok = False
    
    # LangChain核心
    print("\n🔗 LangChain 核心:")
    langchain_modules = [
        ("langchain", "LangChain主包"),
        ("langchain_core", "LangChain核心"),
        ("langchain_community", "LangChain社区包")
    ]
    
    langchain_ok = True
    for module, desc in langchain_modules:
        if not check_module(module, desc):
            langchain_ok = False
    
    # LLM提供商
    print("\n🤖 LLM 提供商支持:")
    llm_providers = [
        ("langchain_openai", "OpenAI (GPT系列)"),
        ("langchain_anthropic", "Anthropic (Claude系列)"),
        ("langchain_google_genai", "Google AI (Gemini系列)"),
        ("dashscope", "阿里百炼 (通义千问系列)")
    ]
    
    provider_results = {}
    for module, desc in llm_providers:
        provider_results[module] = check_module(module, desc)
    
    # 数据库支持
    print("\n🗄️ 数据库支持:")
    db_modules = [
        ("redis", "Redis缓存"),
        ("pymongo", "MongoDB存储")
    ]
    
    db_ok = True
    for module, desc in db_modules:
        if not check_module(module, desc):
            db_ok = False
    
    # 数据源
    print("\n📊 数据源支持:")
    data_modules = [
        ("akshare", "AKShare数据源"),
        ("yfinance", "Yahoo Finance"),
        ("tushare", "Tushare数据源")
    ]
    
    for module, desc in data_modules:
        check_module(module, desc)
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 依赖检查总结:")
    
    if core_ok:
        print("✅ 核心依赖: 完整")
    else:
        print("❌ 核心依赖: 不完整")
    
    if langchain_ok:
        print("✅ LangChain: 完整")
    else:
        print("❌ LangChain: 不完整")
    
    # LLM提供商统计
    available_providers = sum(provider_results.values())
    total_providers = len(provider_results)
    print(f"🤖 LLM提供商: {available_providers}/{total_providers} 可用")
    
    if provider_results.get("langchain_anthropic", False):
        print("✅ Anthropic (Claude) 支持已启用")
    else:
        print("❌ Anthropic (Claude) 支持未启用")
    
    # 安装建议
    if not core_ok or not langchain_ok:
        print("\n💡 修复建议:")
        print("1. 激活虚拟环境: source env/bin/activate")
        print("2. 安装依赖: pip install -r requirements.txt")
        print("3. 重新检查: python check_dependencies.py")
    
    missing_providers = [name for name, available in provider_results.items() if not available]
    if missing_providers:
        print(f"\n🔧 安装缺失的LLM提供商:")
        for provider in missing_providers:
            print(f"   pip install {provider}")
    
    print("\n🎯 当前状态:", end=" ")
    if core_ok and langchain_ok and provider_results.get("langchain_anthropic", False):
        print("可以正常使用所有功能 🎉")
    elif core_ok and langchain_ok:
        print("可以使用基本功能，部分LLM提供商不可用 ⚠️")
    else:
        print("需要安装核心依赖才能使用 ❌")

if __name__ == "__main__":
    main()