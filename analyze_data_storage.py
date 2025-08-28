#!/usr/bin/env python3
"""
历史记录数据存储分析脚本
"""

import os
import sys
import json
import glob
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_file_storage():
    """分析文件存储的历史记录"""
    print("📁 文件存储分析")
    print("=" * 50)
    
    # 检查data目录
    data_dir = "./data"
    if os.path.exists(data_dir):
        print(f"✅ data目录存在: {data_dir}")
        
        # 查找所有progress文件
        progress_files = glob.glob(os.path.join(data_dir, "progress_*.json"))
        print(f"📊 找到 {len(progress_files)} 个进度文件")
        
        for i, file_path in enumerate(progress_files, 1):
            try:
                filename = os.path.basename(file_path)
                file_stat = os.stat(file_path)
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analysis_id = data.get('analysis_id', '未知')
                status = data.get('status', '未知')
                stock_symbol = '未知'
                
                # 尝试从raw_results获取股票信息
                raw_results = data.get('raw_results', {})
                if isinstance(raw_results, dict):
                    stock_symbol = raw_results.get('stock_symbol', stock_symbol)
                
                print(f"  {i}. 文件: {filename}")
                print(f"     股票: {stock_symbol}")
                print(f"     状态: {status}")
                print(f"     修改时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     文件大小: {file_stat.st_size} 字节")
                print()
                
            except Exception as e:
                print(f"  ❌ 读取文件失败: {filename} - {e}")
    else:
        print(f"❌ data目录不存在: {data_dir}")
    
    # 检查results目录
    results_dir = "./results"
    if os.path.exists(results_dir):
        print(f"\n📋 results目录存在: {results_dir}")
        
        # 递归查找所有分析结果文件
        result_files = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                if file.endswith(('.json', '.md', '.txt')):
                    result_files.append(os.path.join(root, file))
        
        print(f"📊 找到 {len(result_files)} 个结果文件")
        
        if result_files:
            print("结果文件详情:")
            for i, file_path in enumerate(result_files[:10], 1):  # 只显示前10个
                try:
                    filename = os.path.basename(file_path)
                    dir_name = os.path.basename(os.path.dirname(file_path))
                    file_stat = os.stat(file_path)
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    print(f"  {i}. 目录: {dir_name}")
                    print(f"     文件: {filename}")
                    print(f"     修改时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"     文件大小: {file_stat.st_size} 字节")
                    print()
                    
                except Exception as e:
                    print(f"  ❌ 读取文件信息失败: {file_path} - {e}")
    else:
        print(f"\n❌ results目录不存在: {results_dir}")


def analyze_redis_storage():
    """分析Redis存储的历史记录"""
    print("\n🔄 Redis存储分析")
    print("=" * 50)
    
    try:
        redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        
        if not redis_enabled:
            print("❌ Redis未启用")
            return
        
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
        print(f"✅ Redis连接成功: {redis_host}:{redis_port} (数据库: {redis_db})")
        
        # 查找所有progress键
        keys = redis_client.keys("progress:*")
        print(f"📊 找到 {len(keys)} 个Redis记录")
        
        for i, key in enumerate(keys, 1):
            try:
                data = redis_client.get(key)
                if data:
                    progress_data = json.loads(data)
                    analysis_id = key.replace('progress:', '')
                    status = progress_data.get('status', '未知')
                    last_update = progress_data.get('last_update', 0)
                    
                    stock_symbol = '未知'
                    raw_results = progress_data.get('raw_results', {})
                    if isinstance(raw_results, dict):
                        stock_symbol = raw_results.get('stock_symbol', stock_symbol)
                    
                    if last_update:
                        update_time = datetime.fromtimestamp(last_update)
                        update_str = update_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        update_str = '未知时间'
                    
                    print(f"  {i}. 键: {key}")
                    print(f"     股票: {stock_symbol}")
                    print(f"     状态: {status}")
                    print(f"     更新时间: {update_str}")
                    print()
                    
            except Exception as e:
                print(f"  ❌ 解析Redis记录失败: {key} - {e}")
                
        # 检查TTL
        if keys:
            sample_key = keys[0]
            ttl = redis_client.ttl(sample_key)
            if ttl > 0:
                print(f"⏰ 记录过期时间: {ttl} 秒")
            elif ttl == -1:
                print(f"♾️ 记录永不过期")
            else:
                print(f"⚠️ 记录已过期或不存在")
        
    except ImportError:
        print("❌ Redis库未安装")
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")


def analyze_data_retention():
    """分析数据保留情况"""
    print("\n📅 数据保留分析")
    print("=" * 50)
    
    # 检查昨天的数据
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    
    print(f"📆 今天日期: {today}")
    print(f"📆 昨天日期: {yesterday}")
    
    # 查找可能的昨天数据
    data_patterns = [
        f"./data/*{yesterday.strftime('%Y%m%d')}*",
        f"./data/*{yesterday.strftime('%Y-%m-%d')}*", 
        f"./data/*{yesterday.strftime('%Y%m%d')}*",
        f"./results/*{yesterday.strftime('%Y%m%d')}*",
        f"./results/*{yesterday.strftime('%Y-%m-%d')}*"
    ]
    
    found_yesterday_files = []
    for pattern in data_patterns:
        files = glob.glob(pattern)
        found_yesterday_files.extend(files)
    
    if found_yesterday_files:
        print(f"✅ 找到 {len(found_yesterday_files)} 个昨天的文件:")
        for file in found_yesterday_files:
            print(f"  - {file}")
    else:
        print("❌ 未找到昨天的数据文件")
    
    # 分析可能的数据丢失原因
    print("\n🔍 可能的数据丢失原因:")
    print("1. Redis TTL过期 - Redis记录默认1小时过期")
    print("2. 文件存储位置变更 - 检查是否存储在其他目录")
    print("3. 数据库切换 - Redis数据库编号变更")
    print("4. 缓存清理 - 系统或手动清理了缓存数据")
    print("5. 进程重启 - 服务重启导致内存数据丢失")


def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案建议")
    print("=" * 50)
    
    print("🔧 立即可执行的解决方案:")
    print("1. 增加Redis TTL时间 - 修改过期时间为7天或更长")
    print("2. 启用文件持久化 - 确保所有分析都保存到文件")
    print("3. 备份机制 - 定期备份重要的分析结果")
    print("4. 数据恢复 - 检查其他可能的存储位置")
    
    print("\n📋 具体操作步骤:")
    print("• 修改Redis TTL: 在async_progress_tracker.py中调整setex时间")
    print("• 检查results目录: 查看是否有完整的分析报告")
    print("• 恢复文件存储: 确保所有分析都会保存到本地文件")
    print("• 增强数据持久化: 同时使用Redis和文件双重存储")


if __name__ == "__main__":
    print("🔍 TradingAgents-CN 历史记录数据分析")
    print("=" * 60)
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # 手动设置Redis配置
        os.environ.setdefault('REDIS_ENABLED', 'true')
        os.environ.setdefault('REDIS_HOST', 'localhost')
        os.environ.setdefault('REDIS_PORT', '6379')
        os.environ.setdefault('REDIS_DB', '1')
    
    # 执行分析
    analyze_file_storage()
    analyze_redis_storage()
    analyze_data_retention()
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("📊 数据分析完成")