@echo off
REM ClawAI Complete Starter - Starts backend and opens modern React frontend
echo ========================================
echo ClawAI Complete System Starter
echo ========================================
echo.

echo [1/3] Setting up environment...
set DISABLE_AUTH=1

echo [2/3] Checking backend service...
netstat -ano | findstr :8000 >nul
if errorlevel 1 (
    echo Backend not running, starting...
    start /B cmd /c "cd /d %~dp0 && set DISABLE_AUTH=1 && python start.py"
    echo Waiting for backend to start (10 seconds)...
    timeout /t 10 >nul
) else (
    echo Backend already running (port 8000)
)

echo [3/3] Opening modern React interface...
echo Opening browser to: http://localhost:8000/static/index.html
echo.
echo ========================================
echo IMPORTANT:
echo 1. Modern React interface will open
echo 2. Features: Target input, AI scanning, attack chain visualization
echo 3. Tool list and health monitoring
echo 4. All data from real API (not simulated)
echo 5. Close this window to stop backend (kill python processes)
echo ========================================
echo.

start "" "http://localhost:8000/static/index.html"

echo Press any key to check service status...
pause >nul

echo.
echo Service status:
curl -s http://localhost:8000/health > status.json 2>nul
if exist status.json (
    python -c "import json
try:
    with open('status.json') as f:
        data = json.load(f)
    print('Status:', data.get('status'))
    print('Version:', data.get('version'))
    tools = data.get('services', {}).get('tools', {})
    print('Tools available:', tools.get('available_tools', 0), '/', tools.get('total_tools', 0))
except:
    print('Cannot parse status')" 2>nul
    del status.json
) else (
    echo Cannot get status - backend may not be running
)

echo.
echo Press any key to exit...
pause >nul