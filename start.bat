@echo off
echo Starting ClawAI...

REM Change to script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+
    pause
    exit /b 1
)

REM Check and activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Install dependencies if needed
if exist "requirements.txt" (
    python -c "import fastapi" >nul 2>&1
    if errorlevel 1 (
        echo Installing dependencies...
        pip install -r requirements.txt
    )
)

REM Check environment file
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Created .env file from template
    )
)

REM Find available port
set PORT=8000
:port_loop
python -c "import socket; s=socket.socket(); s.settimeout(1); r=s.connect_ex(('localhost',%PORT%)); s.close(); exit(r==0)" >nul 2>&1
if errorlevel 1 (
    goto port_found
) else (
    echo Port %PORT% is in use, trying next...
    set /a PORT+=1
    if %PORT% gtr 8010 (
        echo ERROR: No ports available (8000-8010)
        pause
        exit /b 1
    )
    goto port_loop
)

:port_found
echo Using port: %PORT%
echo API: http://localhost:%PORT%/docs
echo.

REM Start the application
python run.py --port %PORT%

pause