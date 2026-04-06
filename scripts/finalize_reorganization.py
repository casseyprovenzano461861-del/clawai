# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
最终整理脚本 - 完成项目重组
"""

import os
import shutil
import sys

def move_file(src, dst_dir, description=""):
    """移动文件到目标目录"""
    if os.path.exists(src) and os.path.isfile(src):
        try:
            os.makedirs(dst_dir, exist_ok=True)
            dst_path = os.path.join(dst_dir, os.path.basename(src))
            shutil.move(src, dst_path)
            desc = f" ({description})" if description else ""
            print(f"  移动: {os.path.basename(src)} -> {dst_dir}/{desc}")
            return True
        except Exception as e:
            print(f"  错误移动 {src}: {e}")
            return False
    else:
        print(f"  文件不存在: {src}")
        return False

def safe_remove_directory(dir_path, description=""):
    """安全删除目录"""
    if os.path.exists(dir_path):
        try:
            # 检查是否为空
            if not os.listdir(dir_path):
                os.rmdir(dir_path)
                print(f"  删除空目录: {dir_path} ({description})")
                return True
            else:
                print(f"  目录非空，保留: {dir_path} ({description})")
                return False
        except Exception as e:
            print(f"  删除目录 {dir_path} 错误: {e}")
            return False
    else:
        print(f"  目录不存在: {dir_path}")
        return False

def main():
    print("=" * 80)
    print("ClawAI 最终整理脚本")
    print("=" * 80)
    
    # 移动final_cleanup.py到scripts/
    print("\n[1] 移动final_cleanup.py到scripts/...")
    move_file("final_cleanup.py", "./scripts", "清理脚本")
    
    # 处理乱码目录 - 先尝试删除
    print("\n[2] 处理乱码目录...")
    
    # 获取所有目录
    all_items = os.listdir(".")
    directories = [d for d in all_items if os.path.isdir(d)]
    
    for dir_name in directories:
        # 跳过正常目录
        normal_dirs = ['.idea', '.venv', '.vscode', 'backend', 'backups', 'configs', 
                      'data', 'demo_data', 'docs', 'external_tools', 'frontend', 
                      'frontend_backup', 'logs', 'project_backup_20260327', 
                      'reports', 'scripts', 'tests', 'tools', 'utils']
        
        if dir_name in normal_dirs:
            continue
        
        # 跳过点开头的隐藏目录
        if dir_name.startswith('.'):
            continue
        
        # 尝试删除空目录
        safe_remove_directory(dir_name, "可疑目录")
    
    # 移动data.json到data/目录（如果还存在）
    print("\n[3] 移动data.json到data/目录...")
    if os.path.exists("data.json") and os.path.isfile("data.json"):
        move_file("data.json", "./data", "数据文件")
    
    # 验证功能
    print("\n[4] 验证基本功能...")
    
    # 检查backend目录存在
    if os.path.exists("backend"):
        print("  [OK] backend目录存在")
        backend_files = [f for f in os.listdir("backend") if f.endswith('.py')]
        print(f"    包含 {len(backend_files)} 个Python文件")
    else:
        print("  [ERROR] backend目录不存在")
    
    # 检查frontend目录存在
    if os.path.exists("frontend"):
        print("  [OK] frontend目录存在")
        frontend_files = os.listdir("frontend")
        print(f"    包含 {len(frontend_files)} 个文件/目录")
    else:
        print("  [ERROR] frontend目录不存在")
    
    # 检查启动脚本
    if os.path.exists("start_claw_ai.bat"):
        print("  [OK] 启动脚本存在: start_claw_ai.bat")
    else:
        print("  [ERROR] 启动脚本不存在: start_claw_ai.bat")
    
    if os.path.exists("start_test.bat"):
        print("  [OK] 测试脚本存在: start_test.bat")
    else:
        print("  [ERROR] 测试脚本不存在: start_test.bat")
    
    # 检查配置文件
    config_files = ['.env', 'config.py', 'requirements.txt', 'docker-compose.yml']
    for config in config_files:
        if os.path.exists(config):
            print(f"  [OK] 配置文件存在: {config}")
        else:
            print(f"  [ERROR] 配置文件不存在: {config}")
    
    # 检查根目录
    print("\n" + "=" * 80)
    print("最终检查根目录...")
    print("=" * 80)
    
    root_files = [f for f in os.listdir(".") if os.path.isfile(f)]
    root_dirs = [d for d in os.listdir(".") if os.path.isdir(d)]
    
    print(f"\n根目录文件数量: {len(root_files)}")
    print(f"根目录目录数量: {len(root_dirs)}")
    
    print("\n根目录文件列表:")
    for file in sorted(root_files):
        if not file.startswith('.'):
            print(f"  {file}")
    
    print("\n根目录目录列表 (跳过隐藏目录):")
    for dir_name in sorted(root_dirs):
        if not dir_name.startswith('.'):
            print(f"  {dir_name}/")
    
    print("\n" + "=" * 80)
    print("重组完成总结:")
    print("-" * 80)
    
    # 统计
    total_moved = 0
    for dir_name in ['utils', 'tests', 'reports', 'scripts', 'docs', 'data', 'configs', 'demo_data']:
        if os.path.exists(dir_name):
            if os.path.isdir(dir_name):
                file_count = 0
                for root, dirs, files in os.walk(dir_name):
                    file_count += len(files)
                print(f"  {dir_name}/: {file_count} 个文件")
                total_moved += file_count
    
    print(f"\n[SUCCESS] 总计移动了大约 {total_moved} 个文件到子目录")
    print("[DONE] 项目重组完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()