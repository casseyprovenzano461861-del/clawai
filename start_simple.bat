@echo off
echo ========================================
echo ClawAI Simple Launcher - Easy Interface
echo ========================================
echo.

echo [1/3] Checking backend service...
netstat -ano | findstr :8000 >nul
if errorlevel 1 (
    echo Backend service not running
    echo Starting backend...
    start /B cmd /c "cd /d %~dp0 && python start.py"
    timeout /t 5 >nul
) else (
    echo Backend running (port 8000)
)

echo [2/3] Opening simple web interface...
echo This is a user-friendly interface with buttons and menus
echo It will open in your default browser
start "" "%~dp0\simple_interface.html"

echo.
echo ========================================
echo IMPORTANT:
echo 1. A browser window will open with the simple interface
echo 2. Use the buttons to check health, view tools, run tests
echo 3. If the interface cannot connect, wait a few seconds and refresh
echo 4. Close this window after the interface opens
echo ========================================
echo.
echo ========================================
echo SECURITY WARNING:
echo 1. Only scan websites or systems you have permission to test
echo 2. Unauthorized scanning may be illegal
echo 3. Use demo.target.com for testing, or your own test environment
echo 4. By default, scanning uses MOCK data (not real attacks)
echo 5. For real scanning, ensure you have proper authorization
echo ========================================
echo.
pause