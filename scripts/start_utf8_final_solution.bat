@echo off
chcp 65001 >nul 2>nul
cd /d "%~dp0"

echo ============================================
echo   ClawAI 网络安全渗透测试平台 - 启动菜单
echo ============================================
echo.
echo 请选择要执行的操作：
echo.
echo  [1] 启动 API 服务器 (默认端口 5000)
echo  [2] 自动安装安全工具 (P0/P1/P2 优先级)
echo  [3] 运行真实执行监控系统
echo  [4] 分析 API 性能 (缓存和慢速接口)
echo  [5] 清理冗余文件和过期文档
echo  [6] 运行综合测试 (验证所有改进)
echo  [7] 显示系统信息和工具状态
echo  [8] 退出
echo.
set /p choice=请输入选择 (1-8): 

if "%choice%"=="" goto default
if "%choice%"=="1" goto start_api
if "%choice%"=="2" goto install_tools
if "%choice%"=="3" goto run_monitor
if "%choice%"=="4" goto analyze_performance
if "%choice%"=="5" goto cleanup_files
if "%choice%"=="6" goto run_tests
if "%choice%"=="7" goto system_info
if "%choice%"=="8" goto exit

:start_api
echo.
echo 启动 ClawAI API 服务器...
echo 按 Ctrl+C 停止服务
echo.
python backend/api_server.py
goto exit

:install_tools
echo.
echo 运行工具自动安装脚本...
python scripts/auto_install_tools.py
echo.
pause
goto exit

:run_monitor
echo.
echo 运行真实执行监控系统...
python scripts/enhanced_real_execution_monitor.py
echo.
pause
goto exit

:analyze_performance
echo.
echo 分析 API 性能...
python scripts/analyze_api_performance.py --test
echo.
pause
goto exit

:cleanup_files
echo.
echo 清理冗余文件和过期文档...
echo 1. 清理 archive 目录...
python scripts/cleanup_archive_files.py --execute
echo.
echo 2. 清理 docs 目录...
python scripts/cleanup_docs_and_archive.py --docs-only --execute
echo.
echo 3. 清理冗余文件...
python scripts/cleanup_redundant_files.py --execute
echo.
pause
goto exit

:run_tests
echo.
echo 运行综合测试...
python scripts/simple_test_all.py
echo.
pause
goto exit

:system_info
echo.
echo 系统信息:
echo 操作系统: Windows
echo 项目目录: %cd%
echo Python 版本:
python --version
echo.
echo 工具状态:
python scripts/enhanced_real_execution_monitor.py --quick
echo.
pause
goto exit

:default
echo.
echo 使用默认选项：启动 API 服务器...
goto start_api

:exit
echo.
echo 感谢使用 ClawAI！
pause