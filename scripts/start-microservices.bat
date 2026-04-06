@echo off
REM ClawAI 微服务启动脚本 - Windows批处理版本

echo ========================================
echo ClawAI 微服务启动脚本 (Windows版本)
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

REM 检查bash是否可用
where bash >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未找到bash命令
    echo.
    echo 请安装Git Bash: https://git-scm.com/download/win
    echo 或使用以下替代方案:
    echo.
    echo 1. 使用PowerShell配置镜像加速器:
    echo    .\configure-docker-mirror.ps1
    echo.
    echo 2. 手动启动服务:
    echo    docker-compose -f docker-compose.microservices.yml up -d
    echo.
    echo 3. 检查服务状态:
    echo    docker-compose -f docker-compose.microservices.yml ps
    echo.
    pause
    exit /b 1
)

echo 检测到bash环境，执行微服务启动脚本...
echo 注意: 首次启动可能需要下载镜像，请耐心等待...
echo.

REM 执行bash脚本
bash -c "./start-microservices.sh"

echo.
echo ========================================
echo 脚本执行完成
echo ========================================
echo.
echo 后续操作:
echo 1. 查看服务状态: docker-compose -f docker-compose.microservices.yml ps
echo 2. 查看日志: docker-compose -f docker-compose.microservices.yml logs -f
echo 3. 停止服务: docker-compose -f docker-compose.microservices.yml down
echo.
echo 如果遇到网络问题，请先运行:
echo   .\configure-docker-mirror.ps1
echo   .\start-basic-services.bat
echo.
pause