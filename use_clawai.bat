@echo off
echo ========================================
echo ClawAI Simple Launcher
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
echo This is a pure HTML interface, no build needed
start "" "%~dp0\simple_interface.html"

echo [3/3] Opening API documentation...
echo Full interactive API documentation
start "" "http://localhost:8000/docs"

echo.
echo ========================================
echo TWO WINDOWS WILL OPEN:
echo 1. SIMPLE WEB INTERFACE (user-friendly) - quick actions with buttons
echo 2. API DOCS (Swagger UI) - for developers only
echo.
echo IMPORTANT: Use the SIMPLE WEB INTERFACE for normal usage.
echo The API docs are technical and complex - ignore them if you're not a developer.
echo.
echo If the simple interface cannot connect, wait a few seconds and refresh the page.
echo ========================================
echo.
pause