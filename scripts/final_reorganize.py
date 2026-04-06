# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 最终重组脚本
目标：根目录只保留启动文件和必要的文字文件，其他全部归纳到子目录
"""

import os
import shutil
from pathlib import Path
import datetime

def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)
    return path

def backup_file(file_path, backup_dir):
    """备份文件"""
    if os.path.exists(file_path):
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        if os.path.isfile(file_path):
            shutil.copy2(file_path, backup_path)
            print(f"  备份: {file_path} -> {backup_path}")
        return True
    return False

def move_file(src, dst_dir, description=""):
    """移动文件到目标目录"""
    if os.path.exists(src):
        dst_path = os.path.join(dst_dir, os.path.basename(src))
        shutil.move(src, dst_path)
        desc = f" ({description})" if description else ""
        print(f"  移动: {os.path.basename(src)} -> {dst_dir}/{desc}")
        return True
    return False

def create_init_files():
    """创建__init__.py文件"""
    utils_dirs = [
        "utils",
        "utils/analysis",
        "utils/migration", 
        "utils/verification",
        "utils/cleanup",
        "utils/performance",
        "utils/reports",
        "utils/fix"
    ]
    
    for dir_path in utils_dirs:
        if os.path.exists(dir_path):
            init_file = os.path.join(dir_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("# Package initialization\n")
                print(f"  创建: {init_file}")

def main():
    print("=" * 80)
    print("ClawAI 项目最终重组脚本")
    print("=" * 80)
    
    # 创建备份目录
    backup_dir = ensure_dir(f"./backups/reorg_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print(f"备份目录: {backup_dir}")
    
    # 步骤1：移动分析工具
    print("\n[1/6] 移动分析工具到 utils/analysis...")
    analysis_files = [
        "project_analysis.json",
    ]
    
    for file in analysis_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils/analysis", "分析工具")
    
    # 步骤2：移动迁移工具
    print("\n[2/6] 移动迁移工具到 utils/migration...")
    migration_files = [
        "merge_executors.py",
        "update_imports.py", 
        "consolidate_new_files.py",
        "copy_tools_to_project.py"
    ]
    
    for file in migration_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils/migration", "迁移工具")
    
    # 步骤3：移动验证工具
    print("\n[3/6] 移动验证工具到 utils/verification...")
    verification_files = [
        "verify_architecture_improvements.py",
        "verify_day6_completion.py",
        "verify_improvements.py",
        "verify_integration.py",
        "verify_optimization.py",
        "quick_validation.py"
    ]
    
    for file in verification_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils/verification", "验证工具")
    
    # 步骤4：移动清理工具
    print("\n[4/6] 移动清理工具到 utils/cleanup...")
    cleanup_files = [
        "cleanup_db.py",
        "cleanup_project.py",
        "delete_backup_files.py",
        "safe_cleanup.py"
    ]
    
    for file in cleanup_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils/cleanup", "清理工具")
    
    # 步骤5：移动性能工具
    print("\n[5/6] 移动性能工具到 utils/performance...")
    performance_files = [
        "performance_test_suite.py",
        "monitor_real_execution.py"
    ]
    
    for file in performance_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils/performance", "性能工具")
    
    # 步骤6：移动修复工具
    print("\n[6/6] 移动修复工具到 utils/fix...")
    fix_files = [
        "fix_unicode.py",
        "fix_unicode_final.py",
        "fix_unicode_simple.py"
    ]
    
    for file in fix_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils/fix", "修复工具")
    
    # 步骤7：移动其他工具到 utils/
    print("\n[7/6] 移动其他工具到 utils/...")
    utils_files = [
        "config_manager.py",
        "create_missing_tools.py",
        "create_ppt.py",
        "create_ppt_with_fallback.py",
        "final_verification.py",
        "quick_check.py",
        "run_new_api.py",
        "run_tests.py",
        "debug_workflow_db.py"
    ]
    
    for file in utils_files:
        backup_file(file, backup_dir)
        move_file(file, "./utils", "工具")
    
    # 步骤8：移动测试文件
    print("\n[8/6] 移动测试文件到 tests/...")
    test_files = [
        "test_ai_core_functionality.py",
        "test_ai_fix.py",
        "test_ai_workflow_functionality.py",
        "test_all_changes.py",
        "test_architecture_improvement.py",
        "test_command_injection.py",
        "test_comprehensive_improvements.py",
        "test_dynamic_attack_chain.py",
        "test_enhanced_executor.py",
        "test_evolution.py",
        "test_evolution_detailed.py",
        "test_final_integration.py",
        "test_full_integration.py",
        "test_improvements.py",
        "test_new_api_final.py",
        "test_new_ui.py",
        "test_real_execution_ratio.py",
        "test_refactored_modules.py",
        "test_security_improvements.py",
        "test_smart_orchestrator_integration.py",
        "test_workflow_manager.py",
        "user_acceptance_test.py"
    ]
    
    for file in test_files:
        backup_file(file, backup_dir)
        move_file(file, "./tests", "测试文件")
    
    # 步骤9：移动报告文件
    print("\n[9/6] 移动报告文件到 reports/...")
    report_files = [
        "agent_system_integration_report.json",
        "concurrent_performance_results.json",
        "day6_verification_20260328_103617.json",
        "day6_verification_20260328_103701.json",
        "enhanced_executor_validation.json",
        "executor_migration_report.json",
        "improvement_verification.json",
        "performance_test_results_20260328_103321.json",
        "real_execution_history.json",
        "tool_check_results.json",
        "tool_check_results_enhanced.json",
        "tool_improvement_plan.json",
        "user_acceptance_test_report.json",
        "用户体验优化简单验证报告.json",
        "用户体验优化验证报告.json",
        "real_execution_progress_report.txt"
    ]
    
    for file in report_files:
        backup_file(file, backup_dir)
        move_file(file, "./reports", "报告文件")
    
    # 步骤10：移动数据库和配置文件
    print("\n[10/6] 移动数据库和配置文件...")
    data_files = [
        ("clawai_workflows.db", "./data", "数据库"),
        ("env_example.txt", "./configs", "配置模板"),
        ("competition_demo.py", "./demo_data", "演示脚本")
    ]
    
    for src, dst, desc in data_files:
        backup_file(src, backup_dir)
        move_file(src, dst, desc)
    
    # 步骤11：创建__init__.py文件
    print("\n[11/6] 初始化Python包...")
    create_init_files()
    
    # 步骤12：清理冗余
    print("\n[12/6] 清理冗余...")
    
    # 删除空目录标记
    empty_dirs = ["A类赛事"]
    for dir_path in empty_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"  删除: {dir_path}")
            except:
                pass
    
    # 检查根目录文件
    print("\n" + "=" * 80)
    print("重组完成！检查根目录文件...")
    print("=" * 80)
    
    root_files = [f for f in os.listdir(".") if os.path.isfile(f)]
    root_dirs = [d for d in os.listdir(".") if os.path.isdir(d)]
    
    print(f"\n根目录文件数量: {len(root_files)}")
    print(f"根目录目录数量: {len(root_dirs)}")
    
    print("\n根目录文件列表:")
    for file in sorted(root_files):
        print(f"  {file}")
    
    print("\n根目录目录列表:")
    for dir_name in sorted(root_dirs):
        print(f"  {dir_name}/")
    
    print("\n" + "=" * 80)
    print("重要提示:")
    print("1. 所有文件已备份到:", backup_dir)
    print("2. 需要更新路径引用:")
    print("   - start_claw_ai.bat")
    print("   - start_test.bat") 
    print("   - config.py")
    print("   - Python导入语句")
    print("3. 下一步: 运行验证脚本检查功能")
    print("=" * 80)

if __name__ == "__main__":
    main()