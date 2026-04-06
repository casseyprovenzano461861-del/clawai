@echo off
echo ========================================
echo ClawAI 自动化部署脚本 (Windows)
echo ========================================
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] 建议以管理员身份运行此脚本
    echo.
)

REM 检查Docker是否安装
echo 1. 检查Docker安装...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker未安装或未正确配置
    echo 请从 https://www.docker.com/products/docker-desktop 安装Docker Desktop
    pause
    exit /b 1
)
docker --version
echo.

REM 检查Docker Compose是否安装
echo 2. 检查Docker Compose安装...
docker compose version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Docker Compose未安装或版本过低
    echo 请更新Docker Desktop或安装最新版Docker Compose
    pause
    exit /b 1
)
docker compose version
echo.

REM 检查环境配置文件
echo 3. 检查环境配置...
if not exist ".env" (
    echo [INFO] .env文件不存在，使用默认配置
    copy .env.example .env >nul 2>&1
    if %errorLevel% neq 0 (
        echo [WARN] 无法创建.env文件，请手动创建
    )
)

if not exist "production.env" (
    echo [INFO] production.env文件不存在，使用默认配置
    copy production.env.example production.env >nul 2>&1
    if %errorLevel% neq 0 (
        echo [WARN] 无法创建production.env文件，请手动创建
    )
)

REM 创建必要的目录
echo 4. 创建必要的目录...
mkdir logs 2>nul
mkdir results 2>nul
mkdir data 2>nul
echo.

REM 构建Docker镜像
echo 5. 构建Docker镜像...
echo 这可能需要几分钟时间，请耐心等待...
docker build -t clawai:latest .
if %errorLevel% neq 0 (
    echo [ERROR] Docker构建失败
    echo 请检查Dockerfile和网络连接
    pause
    exit /b 1
)
echo [OK] Docker镜像构建成功
echo.

REM 启动服务
echo 6. 启动ClawAI服务...
echo 使用docker-compose启动所有服务...
docker-compose up -d
if %errorLevel% neq 0 (
    echo [ERROR] 服务启动失败
    echo 尝试使用: docker-compose up -d --build
    pause
    exit /b 1
)
echo [OK] 服务启动成功
echo.

REM 等待服务启动
echo 7. 等待服务启动...
echo 等待30秒让服务完全启动...
timeout /t 30 /nobreak >nul
echo.

REM 检查服务状态
echo 8. 检查服务运行状态...
echo 检查后端API服务...
curl -f http://localhost:5000/health >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] 后端API服务可能未完全启动，正在重试...
    timeout /t 10 /nobreak >nul
    curl -f http://localhost:5000/health >nul 2>&1
    if %errorLevel% neq 0 (
        echo [ERROR] 后端API服务启动失败
        echo 请查看日志: docker-compose logs clawai-backend
        pause
        exit /b 1
    )
)
echo [OK] 后端API服务运行正常
echo.

echo 9. 显示部署信息...
echo ========================================
echo ClawAI 部署完成！
echo ========================================
echo.
echo 服务访问地址:
echo 后端API: http://localhost:5000
echo API文档: http://localhost:5000/docs
echo 健康检查: http://localhost:5000/health
echo.
echo Docker容器状态:
docker-compose ps
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo   更新服务: docker-compose up -d --build
echo.
echo 注意:
echo 1. 首次使用需要配置API密钥
echo    编辑 .env 或 production.env 文件
echo    设置 DEEPSEEK_API_KEY 等配置
echo 2. 重启服务使配置生效: docker-compose restart
echo 3. 默认管理员账户: admin / admin@clawai123
echo.
echo ========================================
pause