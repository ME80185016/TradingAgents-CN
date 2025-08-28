#!/usr/bin/env python3
"""
历史数据恢复脚本
搜索和恢复可能存在的历史分析数据
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta
import shutil

def search_all_possible_locations():
    """搜索所有可能的数据存储位置"""
    print("🔍 搜索所有可能的历史数据...")
    
    search_locations = [
        "./data",
        "./results",  
        "./reports",
        "./cache",
        "./logs",
        "./web/data",
        "./tradingagents/data",
        "./temp",
        "./tmp",
        "~/.tradingagents",
        "/tmp/tradingagents"
    ]
    
    found_files = []
    
    for location in search_locations:
        expanded_path = os.path.expanduser(location)
        if os.path.exists(expanded_path):
            print(f"📁 搜索目录: {expanded_path}")
            
            # 搜索各种可能的文件格式
            patterns = [
                "progress_*.json",
                "analysis_*.json", 
                "*.json",
                "*.md",
                "*analysis*",
                "*stock*",
                "*trading*"
            ]
            
            for pattern in patterns:
                try:
                    files = glob.glob(os.path.join(expanded_path, "**", pattern), recursive=True)
                    for file in files:
                        if is_analysis_file(file):
                            found_files.append(file)
                except Exception as e:
                    continue
    
    # 去重
    found_files = list(set(found_files))
    
    print(f"✅ 共找到 {len(found_files)} 个潜在的分析文件")
    return found_files


def is_analysis_file(file_path):
    """判断文件是否为分析相关文件"""
    try:
        filename = os.path.basename(file_path).lower()
        
        # 检查文件名特征
        analysis_keywords = [
            'progress', 'analysis', 'stock', 'trading', 
            'report', 'result', 'decision', 'market'
        ]
        
        if any(keyword in filename for keyword in analysis_keywords):
            # 检查文件大小（避免空文件或配置文件）
            if os.path.getsize(file_path) > 100:  # 大于100字节
                return True
    except:
        pass
    return False


def analyze_file_content(file_path):
    """分析文件内容提取关键信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                data = json.load(f)
                
                # 检查是否为分析进度文件
                if isinstance(data, dict):
                    analysis_info = {}
                    
                    # 提取基本信息
                    analysis_info['file_path'] = file_path
                    analysis_info['file_size'] = os.path.getsize(file_path)
                    analysis_info['modification_time'] = datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 提取分析相关信息
                    analysis_info['analysis_id'] = data.get('analysis_id', '未知')
                    analysis_info['status'] = data.get('status', '未知')
                    analysis_info['progress'] = data.get('progress_percentage', 0)
                    
                    # 提取股票信息
                    stock_symbol = '未知'
                    raw_results = data.get('raw_results', {})
                    if isinstance(raw_results, dict):
                        stock_symbol = raw_results.get('stock_symbol', stock_symbol)
                    
                    # 如果没找到，尝试从analysis_id提取
                    if stock_symbol == '未知' and 'analysis_id' in data:
                        import re
                        match = re.search(r'([A-Z]{1,5}|\d{6}|\d{3,4}\.HK)', 
                                        str(data['analysis_id']).upper())
                        if match:
                            stock_symbol = match.group(1)
                    
                    analysis_info['stock_symbol'] = stock_symbol
                    
                    # 提取时间信息
                    if 'start_time' in data:
                        analysis_info['start_time'] = datetime.fromtimestamp(
                            data['start_time']
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        analysis_info['start_time'] = '未知'
                    
                    return analysis_info
            
            else:
                # 对于非JSON文件，尝试提取基本信息
                content = f.read(1000)  # 读取前1000字符
                if any(keyword in content.lower() for keyword in 
                      ['stock', 'analysis', 'trading', 'investment']):
                    return {
                        'file_path': file_path,
                        'file_size': os.path.getsize(file_path),
                        'modification_time': datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        'file_type': 'text',
                        'preview': content[:200] + '...' if len(content) > 200 else content
                    }
    except Exception as e:
        return None
    
    return None


def recover_to_standard_location(analysis_files):
    """将找到的分析文件恢复到标准位置"""
    print("\n🔄 恢复数据到标准位置...")
    
    # 确保标准目录存在
    os.makedirs('./data/recovered', exist_ok=True)
    
    recovered_count = 0
    
    for file_info in analysis_files:
        try:
            source_path = file_info['file_path']
            filename = os.path.basename(source_path)
            
            # 生成恢复后的文件名
            if file_info.get('analysis_id', '未知') != '未知':
                recovered_filename = f"recovered_{file_info['analysis_id']}.json"
            else:
                timestamp = file_info['modification_time'].replace(':', '-').replace(' ', '_')
                recovered_filename = f"recovered_{timestamp}_{filename}"
            
            dest_path = f"./data/recovered/{recovered_filename}"
            
            # 复制文件
            shutil.copy2(source_path, dest_path)
            print(f"✅ 恢复文件: {filename} -> {recovered_filename}")
            recovered_count += 1
            
        except Exception as e:
            print(f"❌ 恢复文件失败: {file_info['file_path']} - {e}")
    
    print(f"🎉 成功恢复 {recovered_count} 个文件到 ./data/recovered/")


def generate_recovery_report(analysis_files):
    """生成数据恢复报告"""
    print("\n📊 生成数据恢复报告...")
    
    if not analysis_files:
        print("❌ 未找到可恢复的数据")
        return
    
    # 按日期分组
    by_date = {}
    for file_info in analysis_files:
        mod_time = file_info['modification_time']
        date_key = mod_time[:10]  # 取日期部分
        if date_key not in by_date:
            by_date[date_key] = []
        by_date[date_key].append(file_info)
    
    print(f"📅 按日期统计:")
    for date, files in sorted(by_date.items()):
        print(f"  {date}: {len(files)} 个文件")
        
        # 显示该日期的股票
        stocks = set()
        for file_info in files:
            stock = file_info.get('stock_symbol', '未知')
            if stock != '未知':
                stocks.add(stock)
        
        if stocks:
            print(f"    股票: {', '.join(sorted(stocks))}")
    
    # 生成详细报告文件
    report_file = f"./data_recovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'recovery_time': datetime.now().isoformat(),
                'total_files_found': len(analysis_files),
                'files_by_date': by_date,
                'detailed_files': analysis_files
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 详细报告已保存: {report_file}")
    except Exception as e:
        print(f"❌ 保存报告失败: {e}")


if __name__ == "__main__":
    print("🛠️ TradingAgents-CN 历史数据恢复工具")
    print("=" * 60)
    
    # 搜索所有可能的文件
    found_files = search_all_possible_locations()
    
    if not found_files:
        print("❌ 未找到任何历史数据文件")
        print("\n💡 可能的原因:")
        print("1. 数据确实已被删除")
        print("2. 数据存储在其他位置")
        print("3. 分析从未成功完成并保存")
        exit(1)
    
    # 分析文件内容
    print(f"\n📊 分析 {len(found_files)} 个文件...")
    analysis_files = []
    
    for file_path in found_files:
        file_info = analyze_file_content(file_path)
        if file_info:
            analysis_files.append(file_info)
    
    if not analysis_files:
        print("❌ 没有找到有效的分析文件")
        exit(1)
    
    print(f"✅ 找到 {len(analysis_files)} 个有效的分析文件")
    
    # 显示找到的文件
    print(f"\n📋 找到的分析文件:")
    for i, file_info in enumerate(analysis_files, 1):
        print(f"  {i}. 股票: {file_info.get('stock_symbol', '未知')}")
        print(f"     状态: {file_info.get('status', '未知')}")
        print(f"     时间: {file_info.get('modification_time', '未知')}")
        print(f"     文件: {os.path.basename(file_info['file_path'])}")
        print()
    
    # 恢复数据
    recover_to_standard_location(analysis_files)
    
    # 生成报告
    generate_recovery_report(analysis_files)
    
    print("\n" + "=" * 60)
    print("🎯 数据恢复完成！")
    print("💡 建议:")
    print("1. 重启Web应用以加载恢复的数据")
    print("2. 检查历史记录页面是否显示更多数据")
    print("3. 今后分析会自动保存更长时间（7天）")