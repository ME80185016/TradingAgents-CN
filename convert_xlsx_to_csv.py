#!/usr/bin/env python3
"""
Excel to CSV Converter
将xlsx文件转换为CSV格式，支持多sheet页
每个sheet将保存为单独的CSV文件
"""

import pandas as pd
import os
import sys
from pathlib import Path


def convert_xlsx_to_csv(xlsx_file, output_dir=None, encoding='utf-8-sig'):
    """
    将xlsx文件转换为CSV格式
    
    Args:
        xlsx_file: xlsx文件路径
        output_dir: 输出目录，如果为None则使用xlsx文件所在目录
        encoding: CSV文件编码，默认为utf-8-sig（带BOM，Excel友好）
    """
    xlsx_path = Path(xlsx_file)
    
    if not xlsx_path.exists():
        print(f"错误: 文件 {xlsx_file} 不存在")
        return False
    
    # 确定输出目录
    if output_dir is None:
        output_dir = xlsx_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"正在读取Excel文件: {xlsx_path}")
    print("-" * 50)
    
    try:
        # 读取所有sheet页
        excel_file = pd.ExcelFile(xlsx_path)
        sheet_names = excel_file.sheet_names
        
        print(f"发现 {len(sheet_names)} 个sheet页:")
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"  {i}. {sheet_name}")
        
        print("-" * 50)
        
        # 转换每个sheet
        base_name = xlsx_path.stem
        converted_files = []
        
        for sheet_name in sheet_names:
            print(f"\n正在处理sheet: {sheet_name}")
            
            # 读取sheet数据
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            
            print(f"  - 行数: {len(df)}")
            print(f"  - 列数: {len(df.columns)}")
            print(f"  - 列名: {', '.join(df.columns.astype(str).tolist()[:10])}" + 
                  ("..." if len(df.columns) > 10 else ""))
            
            # 生成CSV文件名
            # 如果只有一个sheet，不加后缀；多个sheet则添加sheet名称
            if len(sheet_names) == 1:
                csv_filename = f"{base_name}.csv"
            else:
                # 清理sheet名称，去除特殊字符
                safe_sheet_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                         for c in sheet_name)
                csv_filename = f"{base_name}_{safe_sheet_name}.csv"
            
            csv_path = output_dir / csv_filename
            
            # 保存为CSV
            df.to_csv(csv_path, index=False, encoding=encoding)
            converted_files.append(csv_path)
            
            print(f"  ✓ 已保存到: {csv_path}")
        
        print("\n" + "=" * 50)
        print(f"✓ 转换完成! 共生成 {len(converted_files)} 个CSV文件:")
        for csv_file in converted_files:
            file_size = csv_file.stat().st_size
            size_kb = file_size / 1024
            print(f"  - {csv_file.name} ({size_kb:.2f} KB)")
        
        return True
        
    except Exception as e:
        print(f"\n错误: 转换失败")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='将Excel (xlsx) 文件转换为CSV格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 转换当前目录下的xlsx文件
  python convert_xlsx_to_csv.py qyxxcjb.xlsx
  
  # 转换并指定输出目录
  python convert_xlsx_to_csv.py qyxxcjb.xlsx -o output/
  
  # 使用UTF-8编码（不带BOM）
  python convert_xlsx_to_csv.py qyxxcjb.xlsx -e utf-8
        """
    )
    
    parser.add_argument('xlsx_file', help='要转换的xlsx文件路径')
    parser.add_argument('-o', '--output-dir', help='输出目录（默认为xlsx文件所在目录）')
    parser.add_argument('-e', '--encoding', default='utf-8-sig',
                       help='CSV文件编码 (默认: utf-8-sig，Excel友好)')
    
    args = parser.parse_args()
    
    success = convert_xlsx_to_csv(args.xlsx_file, args.output_dir, args.encoding)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

