@echo off
echo ========================================
echo ClawAI Docker 启动脚本
echo ========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装或未启动
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM 检查docker-compose是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  docker-compose未找到，尝试使用docker compose
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

echo ✅ Docker已安装
echo.

REM 显示环境变量配置提示
echo 环境变量配置提示:
echo 1. 创建.env文件（可选）:
echo    DEEPSEEK_API_KEY=your_api_key_here
echo    JWT_SECRET=your_jwt_secret_here
echo    API_SECRET_KEY=your_api_secret_here
echo.
echo 2. 或者通过命令行设置:
echo    set DEEPSEEK_API_KEY=your_api_key_here
echo    set JWT_SECRET=your_jwt_secret_here
echo    set API_SECRET_KEY=your_api_secret_here
echo.

REM 检查.env文件是否存在
if exist .env (
    echo ✅ 找到.env文件
) else (
    echo ⚠️  未找到.env文件，将使用默认值
    echo    建议创建.env文件以配置敏感信息
)

echo.
echo 启动选项:
echo 1. 构建并启动容器
echo 2. 仅启动容器（如果已构建）
echo 3. 停止容器
echo 4. 查看容器状态
echo 5. 查看容器日志
echo 6. 重建容器
echo 7. 清理所有容器和卷
echo.

set /p choice="请选择操作 (1-7): "

if "%choice%"=="1" (
    echo.
    echo 🚀 构建并启动ClawAI容器...
    %COMPOSE_CMD% up -d --build
    echo.
    echo ✅ 容器已启动
    echo 📍 访问地址: http://localhost:5000
    echo 📍 API文档: http://localhost:5000/api-docs
    echo 📍 健康检查: http://localhost:5000/health
    echo.
    echo 查看日志: %COMPOSE_CMD% logs -f
    echo 停止容器: %COMPOSE_CMD% down
)

if "%choice%"=="2" (
    echo.
    echo 🚀 启动ClawAI容器...
    %COMPOSE_CMD% up -d
    echo.
    echo ✅ 容器已启动
    echo 📍 访问地址: http://localhost:5000
)

if "%choice%"=="3" (
    echo.
    echo 🛑 停止ClawAI容器...
    %COMPOSE_CMD% down
    echo.
    echo ✅ 容器已停止
)

if "%choice%"=="4" (
    echo.
    echo 📊 容器状态:
    %COMPOSE_CMD% ps
)

if "%choice%"=="5" (
    echo.
    echo 📝 容器日志:
    %COMPOSE_CMD% logs -f
)

if "%choice%"=="6" (
    echo.
    echo 🔄 重建ClawAI容器...
    %COMPOSE_CMD% down
    %COMPOSE_CMD% up -d --build
    echo.
    echo ✅ 容器已重建并启动
)

if "%choice%"=="7" (
    echo.
    echo 🧹 清理所有容器和卷...
    %COMPOSE_CMD% down -v
    echo.
    echo ✅ 所有容器和卷已清理
)

if not "%choice%"=="1" if not "%choice%"=="2" if not "%choice%"=="3" if not "%choice%"=="4" if not "%choice%"=="5" if not "%choice%"=="6" if not "%choice%"=="7" (
    echo.
    echo ❌ 无效选择
)

echo.
pause