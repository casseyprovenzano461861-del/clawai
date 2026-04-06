@echo off
echo ====================================================
echo ClawAI Tool Installation Script
echo ====================================================
echo.

echo Checking current installation status...
echo.

REM Check for nmap
where nmap >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] nmap is already installed
) else (
    echo [MISSING] nmap - Please install from: https://nmap.org/download.html
)

REM Check for python
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] python is already installed
) else (
    echo [MISSING] python - Please install from: https://www.python.org/downloads/
)

REM Check for other tools
set "tools=masscan nikto nuclei httpx whatweb sqlmap dirsearch"

for %%t in (%tools%) do (
    where %%t >nul 2>nul
    if !errorlevel! equ 0 (
        echo [OK] %%t is already installed
    ) else (
        echo [MISSING] %%t
    )
)

echo.
echo ====================================================
echo Installation Summary
echo ====================================================
echo.

REM Count installed tools
set /a total=9
set /a installed=0

where nmap >nul 2>nul && set /a installed+=1
where python >nul 2>nul && set /a installed+=1
where masscan >nul 2>nul && set /a installed+=1
where nikto >nul 2>nul && set /a installed+=1
where nuclei >nul 2>nul && set /a installed+=1
where httpx >nul 2>nul && set /a installed+=1
where whatweb >nul 2>nul && set /a installed+=1
where sqlmap >nul 2>nul && set /a installed+=1
where dirsearch >nul 2>nul && set /a installed+=1

echo Total tools to install: %total%
echo Currently installed: %installed%

set /a percent=installed*100/total
echo Installation rate: %percent%%%

echo.
echo ====================================================
echo Manual Installation Guide
echo ====================================================
echo.
echo To install missing tools, follow these steps:
echo.
echo 1. Chocolatey (Windows package manager):
echo    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
echo.
echo 2. Install tools with Chocolatey:
echo    choco install nmap -y
echo    choco install masscan -y
echo    choco install nikto -y
echo    choco install nuclei -y
echo    choco install httpx -y
echo.
echo 3. Install Python tools:
echo    pip install dirsearch
echo    pip install sublist3r
echo.
echo ====================================================
echo Testing Instructions
echo ====================================================
echo.
echo After installing tools, test with:
echo.
echo 1. nmap: nmap -sP example.com
echo 2. ClawAI tool checker: python tools/tool_checker.py
echo 3. New nmap tool: python backend/tools/new_nmap.py example.com
echo.
echo ====================================================
pause