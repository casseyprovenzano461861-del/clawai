@echo off
echo ========================================
echo ClawAI 增强部署脚本 (Windows)
echo 一键部署 + 环境检查 + 性能优化
echo ========================================
echo.

REM 设置颜色
set "RESET=[0m"
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "BLUE=[34m"

REM 检查是否以管理员身份运行
echo %YELLOW%1. 检查管理员权限...%RESET%
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[WARN] 建议以管理员身份运行此脚本%RESET%
    echo.
)

REM 检查Python环境
echo %YELLOW%2. 检查Python环境...%RESET%
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[ERROR] Python未安装%RESET%
    echo 请从 https://www.python.org/downloads/ 安装Python 3.8+
    pause
    exit /b 1
)
python --version
echo.

REM 检查Node.js环境
echo %YELLOW%3. 检查Node.js环境...%RESET%
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[WARN] Node.js未安装，前端构建将跳过%RESET%
    set "NODE_MISSING=1"
) else (
    node --version
)
echo.

REM 检查Docker环境（可选）
echo %YELLOW%4. 检查Docker环境（可选）...%RESET%
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %YELLOW%[INFO] Docker未安装，将使用本地模式%RESET%
    set "DOCKER_MISSING=1"
) else (
    docker --version
)
echo.

REM 安装Python依赖
echo %YELLOW%5. 安装Python依赖...%RESET%
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo %RED%[ERROR] Python依赖安装失败%RESET%
    pause
    exit /b 1
)
echo %GREEN%[OK] Python依赖安装成功%RESET%
echo.

REM 安装前端依赖（如果有Node.js）
if not defined NODE_MISSING (
    echo %YELLOW%6. 安装前端依赖...%RESET%
    cd frontend
    if exist "package-lock.json" (
        npm ci --silent
    ) else (
        npm install --silent
    )
    if %errorLevel% neq 0 (
        echo %RED%[ERROR] 前端依赖安装失败%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%[OK] 前端依赖安装成功%RESET%
    cd ..
    echo.
)

REM 创建环境配置文件
echo %YELLOW%7. 创建环境配置文件...%RESET%
if not exist ".env" (
    echo [INFO] 创建 .env 配置文件...
    copy .env.example .env >nul 2>&1
    if %errorLevel% neq 0 (
        echo %YELLOW%[WARN] 无法创建.env文件，请手动创建%RESET%
    ) else (
        echo %GREEN%[OK] .env文件创建成功%RESET%
    )
)

if not exist "production.env" (
    echo [INFO] 创建 production.env 配置文件...
    copy production.env.example production.env >nul 2>&1
    if %errorLevel% neq 0 (
        echo %YELLOW%[WARN] 无法创建production.env文件，请手动创建%RESET%
    ) else (
        echo %GREEN%[OK] production.env文件创建成功%RESET%
    )
)
echo.

REM 创建必要的目录
echo %YELLOW%8. 创建必要的目录...%RESET%
mkdir logs 2>nul && echo [INFO] logs目录创建成功
mkdir results 2>nul && echo [INFO] results目录创建成功
mkdir data 2>nul && echo [INFO] data目录创建成功
echo %GREEN%[OK] 目录结构创建完成%RESET%
echo.

REM 构建前端（如果有Node.js）
if not defined NODE_MISSING (
    echo %YELLOW%9. 构建前端应用...%RESET%
    cd frontend
    npm run build --silent
    if %errorLevel% neq 0 (
        echo %RED%[ERROR] 前端构建失败%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%[OK] 前端构建成功%RESET%
    cd ..
    echo.
)

REM 检查安全工具
echo %YELLOW%10. 检查安全工具...%RESET%
python check_downloaded_tools.py
if %errorLevel% neq 0 (
    echo %YELLOW%[WARN] 安全工具检查失败，部分功能可能受限%RESET%
)
echo.

REM 启动模式选择
echo %BLUE%请选择启动模式:%RESET%
echo 1) 本地模式（推荐快速启动）
echo 2) Docker模式（需要Docker）
echo 3) 开发模式（前后端分别启动）
echo.
set /p MODE="请输入选择（默认1）: "
if "%MODE%"=="" set MODE=1

if "%MODE%"=="1" (
    call :local_mode
) else if "%MODE%"=="2" (
    call :docker_mode
) else if "%MODE%"=="3" (
    call :dev_mode
) else (
    call :local_mode
)

echo %GREEN%========================================%RESET%
echo %GREEN%ClawAI 部署完成！%RESET%
echo %GREEN%========================================%RESET%
echo.
pause
exit /b 0

:local_mode
echo.
echo %YELLOW%启动本地模式...%RESET%
echo 启动后端API服务器...
start cmd /k "python backend/api_server.py"
echo 等待后端启动...
timeout /t 10 /nobreak >nul
echo.
if not defined NODE_MISSING (
    echo 启动前端开发服务器...
    start cmd /k "cd frontend && npm run dev"
    echo 等待前端启动...
    timeout /t 5 /nobreak >nul
)
echo %GREEN%[OK] 本地模式启动完成%RESET%
echo.
goto :eof

:docker_mode
if defined DOCKER_MISSING (
    echo %RED%[ERROR] Docker未安装，无法使用Docker模式%RESET%
    pause
    exit /b 1
)
echo.
echo %YELLOW%启动Docker模式...%RESET%
echo 构建Docker镜像...
docker build -t clawai:latest .
if %errorLevel% neq 0 (
    echo %RED%[ERROR] Docker构建失败%RESET%
    pause
    exit /b 1
)
echo 启动Docker Compose服务...
docker-compose up -d
if %errorLevel% neq 0 (
    echo %RED%[ERROR] Docker Compose启动失败%RESET%
    pause
    exit /b 1
)
echo 等待服务启动...
timeout /t 30 /nobreak >nul
echo %GREEN%[OK] Docker模式启动完成%RESET%
echo.
goto :eof

:dev_mode
echo.
echo %YELLOW%启动开发模式...%RESET%
echo 此模式下，前后端将分别启动在独立终端中
echo 后端将在 http://localhost:5000 启动
echo 前端将在 http://localhost:3000 启动
echo.
echo 启动后端服务器...
start cmd /k "python backend/api_server.py"
echo.
if not defined NODE_MISSING (
    echo 启动前端服务器...
    start cmd /k "cd frontend && npm run dev"
    echo.
)
echo %GREEN%[OK] 开发模式启动完成%RESET%
echo 请手动在两个终端中查看日志
goto :eof

:error_handler
echo %RED%[ERROR] 部署过程中发生错误%RESET%
echo 错误代码: %errorlevel%
pause
exit /b %errorlevel%