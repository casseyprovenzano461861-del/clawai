@echo off
REM ClawAI 基础服务启动脚本 - Windows批处理版本
REM 如果已安装Git Bash，会自动调用bash执行

echo ========================================
echo ClawAI 基础服务启动脚本 (Windows版本)
echo ========================================
echo.

REM 检查是否在正确目录
if not exist "docker-compose.microservices.yml" (
    echo 错误: 请在ClawAI项目根目录运行此脚本
    echo 当前目录: %cd%
    pause
    exit /b 1
)

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker守护进程未运行
    echo 请启动Docker Desktop应用程序
    pause
    exit /b 1
)
echo ✓ Docker守护进程正常运行
echo.

REM 尝试使用bash执行脚本（如果可用）
where bash >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未找到bash命令
    echo.
    echo 解决方案:
    echo 1. 安装Git Bash (推荐): https://git-scm.com/download/win
    echo 2. 或者直接运行PowerShell脚本
    echo.
    echo 使用PowerShell执行:
    echo   .\check-docker.ps1
    echo   .\configure-docker-mirror.ps1
    echo.
    echo 安装Git Bash后，可运行:
    echo   .\start-basic-services.sh
    echo.
    pause
    exit /b 1
)

echo 检测到bash环境，执行shell脚本...
echo.

REM 切换到bash执行
bash -c "./start-basic-services.sh"

echo.
echo ========================================
echo 脚本执行完成
echo ========================================
echo.
echo 如果遇到问题，请尝试:
echo 1. 在Git Bash中直接运行: ./start-basic-services.sh
echo 2. 配置镜像加速器: .\configure-docker-mirror.ps1
echo 3. 检查网络连接
echo.
pause