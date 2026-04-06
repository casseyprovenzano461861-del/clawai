@echo off
REM Simple startup script for ClawAI
chcp 65001 >nul 2>nul

echo ============================================
echo   ClawAI Security Testing Platform - Startup
echo ============================================

REM Get the script directory and go to project root
cd /d "%~dp0"
echo Script directory: %cd%
cd ..\
echo Project root: %cd%

echo.
echo Starting API Server...
echo Press Ctrl+C to stop
echo.

python backend/api_server.py

pause