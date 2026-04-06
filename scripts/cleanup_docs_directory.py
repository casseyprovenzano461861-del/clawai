#!/usr/bin/env python3
"""
清理docs目录中的冗余文件
主要删除archive_开头的冗余报告和锐评文件
"""

import os
import sys
import shutil
from pathlib import Path
import re

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def cleanup_docs_directory():
    """清理docs目录"""
    docs_dir = Path(__file__).parent.parent / 'docs'
    
    if not docs_dir.exists():
        print(f"docs目录不存在: {docs_dir}")
        return
    
    print(f"清理docs目录: {docs_dir}")
    
    # 定义要保留的重要文件
    important_files = {
        'API使用指南.md',
        'TECHNICAL_DOCUMENTATION.md'
    }
    
    # 定义要保留的目录
    important_dirs = {
        'guides',
        'plans',
        'presentations',
        'reports'
    }
    
    # 删除archive_开头的冗余文件
    files_to_delete = []
    files_to_keep = []
    
    for item in docs_dir.iterdir():
        if item.is_file():
            filename = item.name
            # 保留重要文件
            if filename in important_files:
                files_to_keep.append(filename)
                continue
            
            # 删除archive_开头的文件（锐评文件）
            if filename.startswith('archive_'):
                files_to_delete.append(filename)
            # 删除以_开头的临时文件
            elif filename.startswith('_'):
                files_to_delete.append(filename)
            # 删除.swp等临时文件
            elif filename.endswith('.swp') or filename.endswith('.tmp'):
                files_to_delete.append(filename)
            else:
                files_to_keep.append(filename)
    
    # 执行删除
    print(f"\n删除以下文件:")
    deleted_count = 0
    for filename in files_to_delete:
        file_path = docs_dir / filename
        try:
            file_path.unlink()
            print(f"  [OK] 删除: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"  [FAIL] 删除失败 {filename}: {e}")
    
    # 清理子目录中的冗余文件
    subdir_deleted = 0
    for subdir_name in important_dirs:
        subdir_path = docs_dir / subdir_name
        if subdir_path.exists() and subdir_path.is_dir():
            # 删除子目录中的临时文件
            for root, dirs, files in os.walk(subdir_path):
                for file in files:
                    if file.startswith('_') or file.endswith('.swp') or file.endswith('.tmp'):
                        file_path = Path(root) / file
                        try:
                            file_path.unlink()
                            subdir_deleted += 1
                        except:
                            pass
    
    print(f"\n清理完成:")
    print(f"  - 删除主目录文件: {deleted_count} 个")
    print(f"  - 删除子目录临时文件: {subdir_deleted} 个")
    print(f"  - 保留文件: {len(files_to_keep)} 个")
    
    # 显示保留的文件
    if files_to_keep:
        print(f"\n保留的文件:")
        for filename in sorted(files_to_keep):
            print(f"  - {filename}")
    
    # 创建清理报告
    report_content = f"""# Docs目录清理报告

## 清理时间
{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 清理摘要
- 删除文件总数: {deleted_count + subdir_deleted}
- 保留文件总数: {len(files_to_keep)}
- 清理目录: {docs_dir}

## 删除的文件
{chr(10).join(f'- {f}' for f in files_to_delete)}

## 保留的文件
{chr(10).join(f'- {f}' for f in sorted(files_to_keep))}

## 建议
1. docs目录现在更加整洁，只保留必要的文档
2. archive_开头的冗余报告文件已删除
3. 临时文件已清理
"""
    
    report_path = docs_dir / 'docs_cleanup_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n清理报告已保存: {report_path}")
    
    return deleted_count

def main():
    """主函数"""
    print("=" * 60)
    print("清理Docs目录冗余文件")
    print("=" * 60)
    
    try:
        deleted_count = cleanup_docs_directory()
        
        print("\n" + "=" * 60)
        if deleted_count > 0:
            print(f"[SUCCESS] 清理完成，删除了 {deleted_count} 个冗余文件")
            print("docs目录现在更加整洁！")
        else:
            print("[INFO] 没有需要清理的文件，docs目录已经整洁")
        
        print("\n后续操作:")
        print("1. 检查清理报告了解详细情况")
        print("2. 如有重要文件被误删，可从git历史恢复")
        
    except Exception as e:
        print(f"[ERROR] 清理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
