@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title ClawAI - AI 渗透测试助手

:: ======== 颜色定义 ========
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "BOLD=%ESC%[1m"
set "END=%ESC%[0m"

:: ======== 横幅 ========
echo.
echo     %CYAN%██████╗██╗     ███████╗ █████╗  ██████╗ ██╗  ██╗%END%
echo    %CYAN%██╔════╝██║     ██╔════╝██╔══██╗██╔═══██╗╚██╗██╔╝%END%
echo    %CYAN%██║     ██║     █████╗  ███████║██║   ██║ ╚███╔╝ %END%
echo    %CYAN%██║     ██║     ██╔══╝  ██╔══██║██║   ██║ ██╔██╗ %END%
echo    %CYAN%╚██████╗███████╗███████╗██║  ██║╚██████╔╝██╔╝ ██╗%END%
echo    %CYAN%╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝%END%
echo                %BOLD%[ AI 渗透测试助手 ]%END%
echo.
echo %CYAN%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%END%
echo.

:: ======== 检查 Python ========
echo %BOLD%[1/5] 检查 Python...%END%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   %RED%✗ 未找到 Python，请安装 Python 3.10+%END%
    echo   %YELLOW%  下载地址: https://www.python.org/downloads/%END%
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   %GREEN%✓ Python %PYVER%%END%

:: ======== 检查 Node.js ========
echo %BOLD%[2/5] 检查 Node.js...%END%
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   %RED%✗ 未找到 Node.js，请安装 LTS 版本%END%
    echo   %YELLOW%  下载地址: https://nodejs.org/%END%
    pause
    exit /b 1
)
for /f %%v in ('node --version') do set NODEVER=%%v
echo   %GREEN%✓ Node.js %NODEVER%%END%

:: ======== 检查 .env ========
echo %BOLD%[3/5] 检查配置...%END%
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo   %YELLOW%⚠ 已从 .env.example 创建 .env，请编辑配置 API Key%END%
    ) else (
        echo   %YELLOW%⚠ 未找到 .env 文件，AI 功能可能无法使用%END%
    )
) else (
    echo   %GREEN%✓ .env 配置文件存在%END%
)

:: ======== 创建必要目录 ========
if not exist "data\databases" mkdir data\databases
if not exist "logs" mkdir logs

:: ======== 安装依赖 ========
echo %BOLD%[4/5] 检查依赖...%END%

:: 检查后端依赖
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo   %YELLOW%⬇ 安装 Python 依赖（首次运行可能需要几分钟）...%END%
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo   %RED%✗ Python 依赖安装失败%END%
        pause
        exit /b 1
    )
)
echo   %GREEN%✓ Python 依赖就绪%END%

:: 检查前端依赖
if not exist "frontend\node_modules" (
    echo   %YELLOW%⬇ 安装前端依赖（首次运行可能需要几分钟）...%END%
    cd frontend
    call npm install
    cd ..
    if %errorlevel% neq 0 (
        echo   %RED%✗ 前端依赖安装失败%END%
        pause
        exit /b 1
    )
)
echo   %GREEN%✓ 前端依赖就绪%END%

:: ======== 启动服务 ========
echo %BOLD%[5/5] 启动服务...%END%
echo.

:: 启动后端
echo   %CYAN%▸ 启动后端服务 (端口 8000)...%END%
start "ClawAI Backend" cmd /c "python -m uvicorn src.shared.backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端就绪
echo   %YELLOW%  等待后端启动...%END%
timeout /t 5 /nobreak >nul

:: 启动前端
echo   %CYAN%▸ 启动前端服务 (端口 3000)...%END%
start "ClawAI Frontend" cmd /c "cd frontend && npm run dev"

:: 等待前端就绪
timeout /t 3 /nobreak >nul

:: 尝试打开浏览器
echo   %CYAN%▸ 打开浏览器...%END%
start http://localhost:3000

:: ======== 完成 ========
echo.
echo %CYAN%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%END%
echo   %BOLD%%GREEN%  ClawAI 启动完成！%END%
echo %CYAN%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%END%
echo.
echo   %BOLD%访问地址:%END%
echo     前端界面:  %GREEN%http://localhost:3000%END%
echo     后端 API:  %GREEN%http://localhost:8000%END%
echo     API 文档:  %GREEN%http://localhost:8000/docs%END%
echo.
echo   %BOLD%停止服务:%END%
echo     关闭后端/前端命令行窗口即可
echo.
echo   %BOLD%CLI 模式:%END%
echo     python clawai.py
echo.
echo %CYAN%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%END%
echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
