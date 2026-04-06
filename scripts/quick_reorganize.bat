@echo off
echo ==========================================
echo ClawAI 快速重组脚本
echo ==========================================
echo.

echo [1/10] 创建目录结构...
mkdir utils\analysis 2>nul
mkdir utils\migration 2>nul
mkdir utils\verification 2>nul
mkdir utils\cleanup 2>nul
mkdir utils\performance 2>nul
mkdir utils\fix 2>nul
mkdir reports 2>nul
mkdir configs 2>nul

echo [2/10] 移动分析工具...
if exist check_tool_match.py move check_tool_match.py utils\analysis\
if exist project_analysis.json move project_analysis.json utils\analysis\

echo [3/10] 移动迁移工具...
if exist merge_executors.py move merge_executors.py utils\migration\
if exist update_imports.py move update_imports.py utils\migration\
if exist consolidate_new_files.py move consolidate_new_files.py utils\migration\
if exist copy_tools_to_project.py move copy_tools_to_project.py utils\migration\

echo [4/10] 移动验证工具...
if exist verify_architecture_improvements.py move verify_architecture_improvements.py utils\verification\
if exist verify_day6_completion.py move verify_day6_completion.py utils\verification\
if exist verify_improvements.py move verify_improvements.py utils\verification\
if exist verify_integration.py move verify_integration.py utils\verification\
if exist verify_optimization.py move verify_optimization.py utils\verification\
if exist quick_validation.py move quick_validation.py utils\verification\
if exist "验证改进效果.py" move "验证改进效果.py" utils\verification\
if exist "验证用户体验优化.py" move "验证用户体验优化.py" utils\verification\

echo [5/10] 移动清理工具...
if exist cleanup_db.py move cleanup_db.py utils\cleanup\
if exist cleanup_project.py move cleanup_project.py utils\cleanup\
if exist delete_backup_files.py move delete_backup_files.py utils\cleanup\
if exist safe_cleanup.py move safe_cleanup.py utils\cleanup\

echo [6/10] 移动性能工具...
if exist performance_test_suite.py move performance_test_suite.py utils\performance\
if exist monitor_real_execution.py move monitor_real_execution.py utils\performance\

echo [7/10] 移动修复工具...
if exist fix_unicode.py move fix_unicode.py utils\fix\
if exist fix_unicode_final.py move fix_unicode_final.py utils\fix\
if exist fix_unicode_simple.py move fix_unicode_simple.py utils\fix\

echo [8/10] 移动其他工具...
if exist config_manager.py move config_manager.py utils\
if exist create_missing_tools.py move create_missing_tools.py utils\
if exist create_ppt.py move create_ppt.py utils\
if exist create_ppt_with_fallback.py move create_ppt_with_fallback.py utils\
if exist final_verification.py move final_verification.py utils\
if exist quick_check.py move quick_check.py utils\
if exist run_new_api.py move run_new_api.py utils\
if exist run_tests.py move run_tests.py utils\
if exist debug_workflow_db.py move debug_workflow_db.py utils\

echo [9/10] 移动测试文件...
if exist test_ai_core_functionality.py move test_ai_core_functionality.py tests\
if exist test_ai_fix.py move test_ai_fix.py tests\
if exist test_ai_workflow_functionality.py move test_ai_workflow_functionality.py tests\
if exist test_all_changes.py move test_all_changes.py tests\
if exist test_architecture_improvement.py move test_architecture_improvement.py tests\
if exist test_command_injection.py move test_command_injection.py tests\
if exist test_comprehensive_improvements.py move test_comprehensive_improvements.py tests\
if exist test_dynamic_attack_chain.py move test_dynamic_attack_chain.py tests\
if exist test_enhanced_executor.py move test_enhanced_executor.py tests\
if exist test_evolution.py move test_evolution.py tests\
if exist test_evolution_detailed.py move test_evolution_detailed.py tests\
if exist test_final_integration.py move test_final_integration.py tests\
if exist test_full_integration.py move test_full_integration.py tests\
if exist test_improvements.py move test_improvements.py tests\
if exist test_new_api_final.py move test_new_api_final.py tests\
if exist test_new_ui.py move test_new_ui.py tests\
if exist test_real_execution_ratio.py move test_real_execution_ratio.py tests\
if exist test_refactored_modules.py move test_refactored_modules.py tests\
if exist test_security_improvements.py move test_security_improvements.py tests\
if exist test_smart_orchestrator_integration.py move test_smart_orchestrator_integration.py tests\
if exist test_workflow_manager.py move test_workflow_manager.py tests\
if exist user_acceptance_test.py move user_acceptance_test.py tests\

echo [10/10] 移动演示和数据库文件...
if exist competition_demo.py move competition_demo.py demo_data\
if exist clawai_workflows.db move clawai_workflows.db data\
if exist env_example.txt move env_example.txt configs\

echo.
echo ==========================================
echo 完成！检查根目录...
echo ==========================================
dir /b

echo.
echo 根目录现在应该只有：
echo   - README.md
echo   - config.py
echo   - requirements.txt
echo   - docker-compose.yml
echo   - Dockerfile, Dockerfile.frontend
echo   - .env 文件
echo   - start_claw_ai.bat, start_test.bat
echo   - 其他核心配置文件
echo.
pause