# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
删除乱码目录
"""

import os
import shutil
import sys

def remove_bad_directories():
    print("=" * 80)
    print("删除乱码目录")
    print("=" * 80)
    
    # 获取当前目录所有项目
    items = os.listdir('.')
    
    for item in items:
        # 只处理目录
        if os.path.isdir(item):
            # 跳过正常的目录
            normal_dirs = ['.idea', '.venv', '.vscode', 'backend', 'backups', 'configs',
                          'data', 'demo_data', 'docs', 'external_tools', 'frontend',
                          'frontend_backup', 'logs', 'project_backup_20260327',
                          'reports', 'scripts', 'tests', 'tools', 'utils']
            
            if item in normal_dirs:
                continue
            
            # 跳过点开头的隐藏目录
            if item.startswith('.'):
                continue
            
            # 尝试检查是否是乱码（包含非ASCII字符）
            try:
                # 尝试编码为GBK，如果不能编码可能是乱码
                item.encode('gbk')
                # 如果能编码，检查是否包含常见的中文字符
                # 暂时保留看起来像中文的目录
                continue
            except UnicodeEncodeError:
                # 不能编码为GBK，可能是乱码目录
                print(f"发现可能的乱码目录: {item}")
                
                # 检查目录是否为空
                try:
                    dir_contents = os.listdir(item)
                    if len(dir_contents) == 0:
                        print(f"  删除空目录: {item}")
                        os.rmdir(item)
                    else:
                        print(f"  目录非空 ({len(dir_contents)}个文件)，跳过: {item}")
                except Exception as e:
                    print(f"  检查目录内容失败: {e}")
                    try:
                        # 强制删除
                        shutil.rmtree(item, ignore_errors=True)
                        print(f"  强制删除目录: {item}")
                    except Exception as e2:
                        print(f"  强制删除也失败: {e2}")

def main():
    remove_bad_directories()
    
    # 检查最终状态
    print("\n" + "=" * 80)
    print("检查最终根目录")
    print("=" * 80)
    
    items = os.listdir('.')
    files = [f for f in items if os.path.isfile(f)]
    dirs = [d for d in items if os.path.isdir(d)]
    
    print(f"文件数量: {len(files)}")
    print(f"目录数量: {len(dirs)}")
    
    print("\n根目录文件:")
    for f in sorted(files):
        if not f.startswith('.'):
            print(f"  {f}")
    
    print("\n根目录目录:")
    for d in sorted(dirs):
        if not d.startswith('.'):
            print(f"  {d}/")
    
    print("\n" + "=" * 80)
    print("重组完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()