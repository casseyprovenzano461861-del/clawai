@echo off
echo ============================================
echo ClawAI 项目整理与清理脚本
echo ============================================

echo.
echo [1/6] 检查当前目录结构...
dir /b

echo.
echo [2/6] 清理明显的冗余文件...
if exist desktop.ini (
    echo 删除 desktop.ini...
    del desktop.ini
)

if exist test_file.txt (
    echo 删除 test_file.txt...
    del test_file.txt
)

if exist "A类赛事" (
    echo 删除空目录标记 "A类赛事"...
    rmdir "A类赛事"
)

echo.
echo [3/6] 清理 frontend_backup 目录...
if exist frontend_backup (
    echo 删除 frontend_backup 目录...
    rmdir /s /q frontend_backup
)

echo.
echo [4/6] 移动 project_backup_20260327 到 data\backups...
if exist project_backup_20260327 (
    if not exist data\backups mkdir data\backups
    echo 移动 project_backup_20260327 到 data\backups...
    move project_backup_20260327 data\backups\
)

echo.
echo [5/6] 重命名Python文件...
if exist "简单验证.py" (
    echo 重命名 "简单验证.py" 为 "quick_validation.py"...
    ren "简单验证.py" quick_validation.py
)

if exist "验证改进效果.py" (
    echo 重命名 "验证改进效果.py" 为 "validate_improvements.py"...
    ren "验证改进效果.py" validate_improvements.py
)

if exist "验证用户体验优化.py" (
    echo 重命名 "验证用户体验优化.py" 为 "validate_user_experience.py"...
    ren "验证用户体验优化.py" validate_user_experience.py
)

echo.
echo [6/6] 移动数据库文件到data目录...
if exist clawai_workflows.db (
    if not exist data mkdir data
    echo 移动 clawai_workflows.db 到 data\...
    move clawai_workflows.db data\
)

echo.
echo ============================================
echo 清理完成！
echo ============================================
echo.
echo 执行结果：
echo 1. 删除了明显的冗余文件
echo 2. 清理了备份目录
echo 3. 重命名了中文Python文件
echo 4. 整理了数据库文件
echo.
echo 请手动移动剩余的文档文件到docs目录。
echo 使用：move *.md docs\ (保留README.md和README_dynamic_rendering.md)
echo ============================================

pause