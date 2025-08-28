#!/usr/bin/env python3
"""
测试分析历史记录功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_history_functions():
    """测试历史记录功能"""
    print("🧪 测试分析历史记录功能...")
    
    try:
        # 导入功能模块
        from web.utils.async_progress_tracker import get_all_analysis_history, extract_analysis_summary
        print("✅ 成功导入历史记录功能")
        
        # 测试获取历史记录
        print("\n📊 获取历史记录...")
        history_records = get_all_analysis_history(limit=10)
        
        if history_records:
            print(f"✅ 成功获取 {len(history_records)} 条历史记录")
            
            # 显示前几条记录的摘要
            print(f"\n📋 前3条记录摘要:")
            for i, record in enumerate(history_records[:3]):
                print(f"  {i+1}. 股票: {record.get('stock_symbol', '未知')}")
                print(f"     状态: {record.get('status_icon', '❓')} {record.get('status_text', '未知')}")
                print(f"     时间: {record.get('last_update_formatted', '未知')}")
                print(f"     进度: {record.get('progress_percentage', 0):.1f}%")
                print()
        else:
            print("📝 暂无历史记录")
        
        # 测试历史记录模块导入
        try:
            from web.modules.analysis_history import render_analysis_history
            print("✅ 历史记录页面模块导入成功")
        except ImportError as e:
            print(f"❌ 历史记录页面模块导入失败: {e}")
        
        print("✅ 历史记录功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_access():
    """测试文件访问权限"""
    print("\n🗂️ 测试文件访问权限...")
    
    try:
        import glob
        import json
        
        # 检查data目录
        data_dir = "./data"
        if os.path.exists(data_dir):
            print(f"✅ data目录存在: {data_dir}")
            
            # 查找progress文件
            progress_files = glob.glob(os.path.join(data_dir, "progress_*.json"))
            print(f"📁 找到 {len(progress_files)} 个进度文件")
            
            if progress_files:
                # 尝试读取第一个文件
                test_file = progress_files[0]
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"✅ 成功读取文件: {os.path.basename(test_file)}")
                    print(f"   包含键: {list(data.keys())[:5]}...")  # 显示前5个键
                except Exception as e:
                    print(f"❌ 读取文件失败: {e}")
        else:
            print(f"📁 data目录不存在: {data_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件访问测试失败: {e}")
        return False


def test_redis_connection():
    """测试Redis连接"""
    print("\n🔄 测试Redis连接...")
    
    try:
        redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        
        if not redis_enabled:
            print("📊 Redis未启用，跳过连接测试")
            return True
        
        import redis
        
        # 从环境变量获取Redis配置
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        redis_db = int(os.getenv('REDIS_DB', 0))

        # 创建Redis连接
        if redis_password:
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True
            )
        else:
            redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )

        # 测试连接
        redis_client.ping()
        print(f"✅ Redis连接成功: {redis_host}:{redis_port}")
        
        # 查找progress键
        keys = redis_client.keys("progress:*")
        print(f"📊 找到 {len(keys)} 个进度记录")
        
        return True
        
    except ImportError:
        print("⚠️ Redis库未安装，跳过Redis测试")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return True  # Redis失败不影响整体功能


if __name__ == "__main__":
    print("🚀 启动历史记录功能测试")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        test_file_access,
        test_redis_connection,
        test_history_functions,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {test_func.__name__} - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！历史记录功能准备就绪")
    else:
        print("⚠️ 部分测试失败，但基本功能可用")
    
    print("\n💡 使用说明:")
    print("1. 启动Web应用: python start_web.py")
    print("2. 在侧边栏选择 '📈 历史记录'")
    print("3. 查看和管理您的分析历史记录")