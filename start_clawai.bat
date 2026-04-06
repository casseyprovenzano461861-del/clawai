@echo off
REM ClawAI Real Starter - English version (no encoding issues)
echo ========================================
echo ClawAI Real Starter - Full Functional Version
echo ========================================
echo.

echo [1/3] Setting environment variables...
set DISABLE_AUTH=1

echo [2/3] Checking backend service...
netstat -ano | findstr :8000 >nul
if errorlevel 1 (
    echo Backend service not running
    echo Starting backend service...
    start /B cmd /c "cd /d %~dp0 && set DISABLE_AUTH=1 && python start.py"
    echo Waiting for backend to start...
    timeout /t 10 >nul
) else (
    echo Backend running (port 8000)
)

echo [3/3] Opening real interface...
echo Opening browser...
echo.
echo ========================================
echo IMPORTANT NOTES:
echo 1. Browser will open real function interface
echo 2. Click "Execute Security Scan" button to test
echo 3. All data from real API, not simulated
echo 4. For API docs: http://localhost:8000/docs
echo 5. To stop service, close this window and all Python windows
echo ========================================
echo.

start "" "http://localhost:8000/static/simple_interface.html"

echo Press any key to check service status...
pause >nul

echo.
echo Current service status:
curl -s http://localhost:8000/health 2>nul | python -c "import sys,json;
try:
    data=json.load(sys.stdin)
    print('Status:', data.get('status'))
    print('Version:', data.get('version'))
except:
    print('Cannot get status, please check service')" 2>nul || echo Cannot get status, please check service

echo.
echo Press any key to exit...
pause >nul