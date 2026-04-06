@echo off
echo ========================================
echo   ClawAI 比赛交付物打包脚本
echo ========================================
echo.

REM 设置变量
set PACKAGE_NAME=ClawAI_Competition_Deliverables_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%
set SOURCE_DIR=%~dp0
set PACKAGE_DIR=%SOURCE_DIR%%PACKAGE_NAME%

echo 创建打包目录: %PACKAGE_DIR%
if exist "%PACKAGE_DIR%" (
    echo 目录已存在，删除旧版本...
    rmdir /s /q "%PACKAGE_DIR%"
)
mkdir "%PACKAGE_DIR%"

echo.
echo 复制必须交付物...
mkdir "%PACKAGE_DIR%\mandatory"

REM 复制必须文件
copy "non_interactive_demo.py" "%PACKAGE_DIR%\mandatory\"
copy "competition_demo.py" "%PACKAGE_DIR%\mandatory\"
copy "start.bat" "%PACKAGE_DIR%\mandatory\"
copy "config.py" "%PACKAGE_DIR%\mandatory\"
copy "docker-compose.yml" "%PACKAGE_DIR%\mandatory\"
copy "Dockerfile" "%PACKAGE_DIR%\mandatory\"
copy "presentation_outline.md" "%PACKAGE_DIR%\mandatory\"
copy "emergency_plan.md" "%PACKAGE_DIR%\mandatory\"
xcopy "tests" "%PACKAGE_DIR%\mandatory\tests\" /E /I

echo.
echo 复制建议交付物...
mkdir "%PACKAGE_DIR%\recommended"

copy "record_demo_video.py" "%PACKAGE_DIR%\recommended\"
copy "performance_test.py" "%PACKAGE_DIR%\recommended\"
copy "final_task_verification.py" "%PACKAGE_DIR%\recommended\"
copy "cleanup_duplicate_files.py" "%PACKAGE_DIR%\recommended\"
copy "enhanced_project_cleanup.py" "%PACKAGE_DIR%\recommended\"
copy "tool_check_results_final.json" "%PACKAGE_DIR%\recommended\"
copy "tool_status_summary_final.txt" "%PACKAGE_DIR%\recommended\"

echo.
echo 复制文档文件...
mkdir "%PACKAGE_DIR%\documentation"

copy "README.md" "%PACKAGE_DIR%\documentation\"
copy "README_QUICKSTART.md" "%PACKAGE_DIR%\documentation\"
copy "comprehensive_project_analysis.md" "%PACKAGE_DIR%\documentation\"
copy "PPT_README.md" "%PACKAGE_DIR%\documentation\"

echo.
echo 创建项目结构备份...
xcopy "backend" "%PACKAGE_DIR%\project_structure\backend\" /E /I
xcopy "configs" "%PACKAGE_DIR%\project_structure\configs\" /E /I
xcopy "data" "%PACKAGE_DIR%\project_structure\data\" /E /I
xcopy "docs" "%PACKAGE_DIR%\project_structure\docs\" /E /I
xcopy "frontend" "%PACKAGE_DIR%\project_structure\frontend\" /E /I
xcopy "scripts" "%PACKAGE_DIR%\project_structure\scripts\" /E /I
xcopy "tools" "%PACKAGE_DIR%\project_structure\tools\" /E /I
xcopy "utils" "%PACKAGE_DIR%\project_structure\utils\" /E /I

echo.
echo 创建交付物清单...
echo ClawAI 比赛交付物清单 > "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo ============================== >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 打包时间: %DATE% %TIME% >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 必须交付物: >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 1. non_interactive_demo.py - 非交互式演示脚本 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 2. competition_demo.py - 比赛演示脚本 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 3. tests/test_ai_core_functionality.py - AI核心测试 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 4. start.bat - 启动脚本 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 5. config.py - 配置文件 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 6. docker-compose.yml - Docker编排文件 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 7. Dockerfile - Docker镜像构建文件 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 8. presentation_outline.md - PPT演示大纲 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 9. emergency_plan.md - 比赛应急预案 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 建议交付物: >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 1. record_demo_video.py - 视频录制脚本 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 2. performance_test.py - 性能测试脚本 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 3. cleanup_duplicate_files.py - 文件清理工具 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo. >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 使用说明: >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 1. 启动演示: 运行 start.bat >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 2. 运行演示: python non_interactive_demo.py --scenes 1,2,3 >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 3. 性能测试: python performance_test.py >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"
echo 4. Docker部署: docker-compose up >> "%PACKAGE_DIR%\DELIVERABLES_README.txt"

echo.
echo 创建压缩包...
cd "%PACKAGE_DIR%\.."
tar -czf "%PACKAGE_NAME%.tar.gz" "%PACKAGE_NAME%"

echo.
echo ========================================
echo 打包完成！
echo 压缩包: %PACKAGE_NAME%.tar.gz
echo 原始目录: %PACKAGE_DIR%
echo ========================================
echo.
echo 按任意键退出...
pause > nul
