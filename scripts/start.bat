@echo off
REM Set UTF-8 encoding
chcp 65001 >nul 2>nul
setlocal enabledelayedexpansion

REM Switch to project root directory
cd /d "%~dp0"
cd ..\

REM Set project root variable
set PROJECT_ROOT=%cd%

echo ============================================
echo   ClawAI Security Testing Platform - Menu
echo ============================================
echo.
echo Please select an option:
echo.
echo  [1] Start API Server (default port 5000)
echo  [2] Auto-install security tools (P0/P1/P2 priority)
echo  [3] Run real execution monitoring system
echo  [4] Analyze API performance (cache and slow endpoints)
echo  [5] Clean up redundant files and outdated docs
echo  [6] Run comprehensive tests (verify all improvements)
echo  [7] Show system information and tool status
echo  [8] Exit
echo.
set /p choice=Enter choice (1-8): 

REM Clean up the choice variable (remove spaces and CR/LF)
set choice=%choice: =%
set choice=%choice:	=%
for /f "delims=" %%a in ("%choice%") do set choice=%%a

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
echo Starting ClawAI API Server...
echo Press Ctrl+C to stop
echo.
python backend/api_server.py
goto exit

:install_tools
echo.
echo Running tool auto-installation script...
python scripts/auto_install_tools.py
echo.
pause
goto exit

:run_monitor
echo.
echo Running real execution monitoring system...
python scripts/enhanced_real_execution_monitor.py
echo.
pause
goto exit

:analyze_performance
echo.
echo Analyzing API performance...
python scripts/analyze_api_performance.py --test
echo.
pause
goto exit

:cleanup_files
echo.
echo Cleaning up redundant files and outdated docs...
echo 1. Cleaning archive directory...
python scripts/cleanup_archive_files.py --execute
echo.
echo 2. Cleaning docs directory...
python scripts/cleanup_docs_and_archive.py --docs-only --execute
echo.
echo 3. Cleaning redundant files...
python scripts/cleanup_redundant_files.py --execute
echo.
pause
goto exit

:run_tests
echo.
echo Running comprehensive tests...
python scripts/simple_test_all.py
echo.
pause
goto exit

:system_info
echo.
echo System Information:
echo Operating System: Windows
echo Project Directory: %cd%
echo Python Version:
python --version
echo.
echo Tool Status:
python scripts/enhanced_real_execution_monitor.py --quick
echo.
pause
goto exit

:default
echo.
echo Using default option: Starting API Server...
goto start_api

:exit
echo.
echo Thank you for using ClawAI!
pause
