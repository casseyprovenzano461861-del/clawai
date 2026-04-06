@echo off
echo ========================================
echo ClawAI Simple Starter
echo ========================================
echo.

echo [1/3] Setting environment...
set DISABLE_AUTH=1

echo [2/3] Starting backend service...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python start.py

REM Note: The backend will run in this window
REM Press Ctrl+C to stop the backend when done