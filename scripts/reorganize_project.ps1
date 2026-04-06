# ClawAI 项目彻底重组脚本
# 目标：根目录只保留启动文件和必要的文字文件，其他全部归纳到子目录

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ClawAI 项目彻底重组脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 备份当前目录状态
$backupDir = ".\backups\reorg_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "创建备份目录: $backupDir" -ForegroundColor Yellow
}

# 步骤1：创建必要的目录结构
Write-Host "步骤1：创建目录结构..." -ForegroundColor Green

# utils子目录
$utilsDirs = @("analysis", "migration", "verification", "cleanup", "performance", "reports", "fix")
foreach ($dir in $utilsDirs) {
    $fullPath = ".\utils\$dir"
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  创建目录: $fullPath" -ForegroundColor Gray
    }
}

# docs子目录
$docsDirs = @("api", "technical", "guides")
foreach ($dir in $docsDirs) {
    $fullPath = ".\docs\$dir"
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  创建目录: $fullPath" -ForegroundColor Gray
    }
}

# 其他目录
$otherDirs = @(".\reports", ".\backups", ".\configs", ".\src")
foreach ($dir in $otherDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  创建目录: $dir" -ForegroundColor Gray
    }
}

Write-Host "目录结构创建完成。" -ForegroundColor Green
Write-Host ""

# 步骤2：移动分析工具到 utils\analysis
Write-Host "步骤2：移动分析工具到 utils\analysis..." -ForegroundColor Green
$analysisFiles = @(
    "analyze_tool_dependencies.py",
    "check_downloaded_tools.py", 
    "check_tool_match.py",
    "project_analysis.json"
)

foreach ($file in $analysisFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\analysis\" -Force
        Write-Host "  移动: $file -> utils\analysis\" -ForegroundColor Gray
    }
}

# 步骤3：移动迁移工具到 utils\migration
Write-Host "步骤3：移动迁移工具到 utils\migration..." -ForegroundColor Green
$migrationFiles = @(
    "merge_executors.py",
    "update_imports.py", 
    "consolidate_new_files.py",
    "copy_tools_to_project.py"
)

foreach ($file in $migrationFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\migration\" -Force
        Write-Host "  移动: $file -> utils\migration\" -ForegroundColor Gray
    }
}

# 步骤4：移动验证工具到 utils\verification
Write-Host "步骤4：移动验证工具到 utils\verification..." -ForegroundColor Green
$verificationFiles = @(
    "verify_architecture_improvements.py",
    "verify_day6_completion.py",
    "verify_improvements.py",
    "verify_integration.py",
    "verify_optimization.py",
    "quick_validation.py", # 原简单验证.py
    "validate_improvements.py", # 原验证改进效果.py
    "validate_user_experience.py" # 原验证用户体验优化.py
)

foreach ($file in $verificationFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\verification\" -Force
        Write-Host "  移动: $file -> utils\verification\" -ForegroundColor Gray
    }
}

# 步骤5：移动清理工具到 utils\cleanup
Write-Host "步骤5：移动清理工具到 utils\cleanup..." -ForegroundColor Green
$cleanupFiles = @(
    "cleanup_db.py",
    "cleanup_project.py",
    "delete_backup_files.py",
    "safe_cleanup.py"
)

foreach ($file in $cleanupFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\cleanup\" -Force
        Write-Host "  移动: $file -> utils\cleanup\" -ForegroundColor Gray
    }
}

# 步骤6：移动性能工具到 utils\performance
Write-Host "步骤6：移动性能工具到 utils\performance..." -ForegroundColor Green
$performanceFiles = @(
    "performance_test_suite.py",
    "monitor_real_execution.py"
)

foreach ($file in $performanceFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\performance\" -Force
        Write-Host "  移动: $file -> utils\performance\" -ForegroundColor Gray
    }
}

# 步骤7：移动修复工具到 utils\fix
Write-Host "步骤7：移动修复工具到 utils\fix..." -ForegroundColor Green
$fixFiles = @(
    "fix_unicode.py",
    "fix_unicode_final.py",
    "fix_unicode_simple.py"
)

foreach ($file in $fixFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\fix\" -Force
        Write-Host "  移动: $file -> utils\fix\" -ForegroundColor Gray
    }
}

# 步骤8：移动其他工具到 utils\
Write-Host "步骤8：移动其他工具到 utils\..." -ForegroundColor Green
$utilsFiles = @(
    "config_manager.py",
    "create_missing_tools.py",
    "create_ppt.py",
    "create_ppt_with_fallback.py",
    "final_verification.py",
    "quick_check.py",
    "run_new_api.py",
    "run_tests.py",
    "debug_workflow_db.py"
)

foreach ($file in $utilsFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\utils\" -Force
        Write-Host "  移动: $file -> utils\" -ForegroundColor Gray
    }
}

Write-Host "工具文件移动完成。" -ForegroundColor Green
Write-Host ""

# 步骤9：移动测试文件到 tests\
Write-Host "步骤9：移动测试文件到 tests\..." -ForegroundColor Green
$testFiles = @(
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
)

foreach ($file in $testFiles) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\tests\" -Force
        Write-Host "  移动: $file -> tests\" -ForegroundColor Gray
    }
}

Write-Host "测试文件移动完成。" -ForegroundColor Green
Write-Host ""

# 步骤10：移动文档文件
Write-Host "步骤10：移动文档文件..." -ForegroundColor Green

# 技术文档 -> docs\technical
$techDocs = @(
    "TECHNICAL_DOCUMENTATION.md",
    "workflow_system_architecture.md",
    "optimized_project_structure.md"
)

foreach ($file in $techDocs) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\docs\technical\" -Force
        Write-Host "  移动: $file -> docs\technical\" -ForegroundColor Gray
    }
}

# API文档 -> docs\api
if (Test-Path ".\API使用指南.md") {
    Copy-Item ".\API使用指南.md" "$backupDir\" -Force
    Move-Item ".\API使用指南.md" ".\docs\api\" -Force
    Write-Host "  移动: API使用指南.md -> docs\api\" -ForegroundColor Gray
}

# 其他文档 -> docs\
$otherDocs = @(
    "install_downloaded_tools_guide.md"
)

foreach ($file in $otherDocs) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\docs\" -Force
        Write-Host "  移动: $file -> docs\" -ForegroundColor Gray
    }
}

# 中文文档 -> docs\
$chineseDocs = @(
    "全面用户体验优化方案.md",
    "深度锐评报告_20260328.md",
    "真实执行比例提升方案.md",
    "项目优化改进计划.md",
    "项目整理优化方案.md",
    "项目锐评报告.md",
    "要求"
)

foreach ($file in $chineseDocs) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\docs\" -Force
        Write-Host "  移动: $file -> docs\" -ForegroundColor Gray
    }
}

Write-Host "文档文件移动完成。" -ForegroundColor Green
Write-Host ""

# 步骤11：移动报告文件到 reports\
Write-Host "步骤11：移动报告文件到 reports\..." -ForegroundColor Green

# JSON报告
$jsonReports = @(
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
    "user_acceptance_test_report.json"
)

foreach ($file in $jsonReports) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\reports\" -Force
        Write-Host "  移动: $file -> reports\" -ForegroundColor Gray
    }
}

# 其他报告文件
$otherReports = @(
    "real_execution_progress_report.txt",
    "real_execution_trend.png"
)

foreach ($file in $otherReports) {
    if (Test-Path ".\$file") {
        Copy-Item ".\$file" "$backupDir\" -Force
        Move-Item ".\$file" ".\reports\" -Force
        Write-Host "  移动: $file -> reports\" -ForegroundColor Gray
    }
}

# 步骤12：移动备份文件
Write-Host "步骤12：移动备份文件..." -ForegroundColor Green
if (Test-Path ".\project_backup_20260327") {
    Copy-Item ".\project_backup_20260327" "$backupDir\" -Recurse -Force
    Move-Item ".\project_backup_20260327" ".\backups\" -Force
    Write-Host "  移动: project_backup_20260327 -> backups\" -ForegroundColor Gray
}

# 步骤13：移动数据库文件
Write-Host "步骤13：移动数据库文件..." -ForegroundColor Green
if (Test-Path ".\clawai_workflows.db") {
    Copy-Item ".\clawai_workflows.db" "$backupDir\" -Force
    Move-Item ".\clawai_workflows.db" ".\data\" -Force
    Write-Host "  移动: clawai_workflows.db -> data\" -ForegroundColor Gray
}

# 步骤14：移动环境文件模板
Write-Host "步骤14：移动环境文件模板..." -ForegroundColor Green
if (Test-Path ".\env_example.txt") {
    Copy-Item ".\env_example.txt" "$backupDir\" -Force
    Move-Item ".\env_example.txt" ".\configs\" -Force
    Write-Host "  移动: env_example.txt -> configs\" -ForegroundColor Gray
}

# 步骤15：移动演示文件
Write-Host "步骤15：移动演示文件..." -ForegroundColor Green
if (Test-Path ".\competition_demo.py") {
    Copy-Item ".\competition_demo.py" "$backupDir\" -Force
    Move-Item ".\competition_demo.py" ".\demo_data\" -Force
    Write-Host "  移动: competition_demo.py -> demo_data\" -ForegroundColor Gray
}

# 步骤16：清理冗余
Write-Host "步骤16：清理冗余..." -ForegroundColor Green

# 删除空目录标记
if (Test-Path ".\A类赛事") {
    Remove-Item ".\A类赛事" -Force -Recurse
    Write-Host "  删除: A类赛事" -ForegroundColor Gray
}

# 删除前端备份（先备份）
if (Test-Path ".\frontend_backup") {
    Copy-Item ".\frontend_backup" "$backupDir\" -Recurse -Force
    Remove-Item ".\frontend_backup" -Force -Recurse
    Write-Host "  删除: frontend_backup" -ForegroundColor Gray
}

# 步骤17：在utils目录创建__init__.py文件
Write-Host "步骤17：初始化Python包..." -ForegroundColor Green
$initFiles = @(".\utils", ".\utils\analysis", ".\utils\migration", ".\utils\verification", ".\utils\cleanup", ".\utils\performance", ".\utils\reports", ".\utils\fix")
foreach ($dir in $initFiles) {
    if (Test-Path $dir) {
        $initFile = Join-Path $dir "__init__.py"
        if (-not (Test-Path $initFile)) {
            Set-Content -Path $initFile -Value "# Package initialization"
            Write-Host "  创建: $initFile" -ForegroundColor Gray
        }
    }
}

# 步骤18：在src目录创建__init__.py
if (Test-Path ".\src") {
    $srcInit = ".\src\__init__.py"
    if (-not (Test-Path $srcInit)) {
        Set-Content -Path $srcInit -Value "# Source package initialization"
        Write-Host "  创建: $srcInit" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "重组完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 显示重组后的根目录文件
Write-Host "重组后的根目录文件：" -ForegroundColor Yellow
Get-ChildItem -Path . -File | Select-Object -ExpandProperty Name | Sort-Object
Write-Host ""

Write-Host "重组后的目录结构：" -ForegroundColor Yellow
Get-ChildItem -Path . -Directory | Select-Object -ExpandProperty Name | Sort-Object
Write-Host ""

Write-Host "重要提示：" -ForegroundColor Red
Write-Host "1. 所有原始文件已备份到: $backupDir" -ForegroundColor Yellow
Write-Host "2. 需要更新脚本中的路径引用：" -ForegroundColor Yellow
Write-Host "   - start_claw_ai.bat" -ForegroundColor Gray
Write-Host "   - start_test.bat" -ForegroundColor Gray
Write-Host "   - config.py" -ForegroundColor Gray
Write-Host "   - Python导入语句" -ForegroundColor Gray
Write-Host "3. 运行验证命令: .\scripts\verify_reorganization.bat" -ForegroundColor Yellow
Write-Host ""

Write-Host "下一步：" -ForegroundColor Green
Write-Host "1. 运行验证脚本检查功能" -ForegroundColor Gray
Write-Host "2. 更新路径引用" -ForegroundColor Gray
Write-Host "3. 运行核心测试" -ForegroundColor Gray

# 创建验证脚本
$verifyScript = @"
@echo off
echo ==========================================
echo ClawAI 重组验证脚本
echo ==========================================

echo.
echo [1/5] 检查目录结构...
dir /b /ad

echo.
echo [2/5] 检查Python导入...
python -c "import sys; sys.path.insert(0, 'utils'); import config_manager; print('✅ config_manager导入成功')"

echo.
echo [3/5] 检查核心模块...
if exist backend\api_server.py (
    echo ✅ API服务器文件存在
) else (
    echo ❌ API服务器文件不存在
)

if exist frontend\package.json (
    echo ✅ 前端项目存在
) else (
    echo ❌ 前端项目不存在
)

echo.
echo [4/5] 检查启动脚本...
if exist start_claw_ai.bat (
    echo ✅ 主启动脚本存在
) else (
    echo ❌ 主启动脚本不存在
)

if exist start_test.bat (
    echo ✅ 测试启动脚本存在
) else (
    echo ❌ 测试启动脚本不存在
)

echo.
echo [5/5] 检查配置文件...
if exist config.py (
    echo ✅ 配置文件存在
) else (
    echo ❌ 配置文件不存在
)

echo.
echo ==========================================
echo 验证完成！
echo ==========================================
pause
"@

Set-Content -Path ".\scripts\verify_reorganization.bat" -Value $verifyScript
Write-Host "验证脚本已创建: .\scripts\verify_reorganization.bat" -ForegroundColor Green