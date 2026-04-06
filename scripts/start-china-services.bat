@echo off
REM ClawAI 中国镜像服务启动脚本 - Windows批处理版本
REM 使用国内镜像源，解决网络连接问题

echo ========================================
echo ClawAI 中国镜像服务启动脚本 (Windows版本)
echo ========================================
echo 使用国内镜像源，解决Docker Hub连接问题
echo.

REM 检查是否在正确目录
if not exist "docker-compose.microservices.china.yml" (
    echo 错误: 缺少中国镜像配置文件
    echo 请确保 docker-compose.microservices.china.yml 存在
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

REM 停止现有服务
echo 停止现有服务...
docker-compose -f docker-compose.microservices.yml down 2>nul || (
    docker-compose -f docker-compose.microservices.china.yml down 2>nul || echo "没有运行中的服务"
)
echo.

REM 尝试拉取国内镜像
echo 步骤1: 拉取Redis镜像 (阿里云镜像)...
docker pull registry.cn-hangzhou.aliyuncs.com/aliyun-ocs/redis:7-alpine
if errorlevel 1 (
    echo ⚠️  Redis镜像拉取失败
    echo 可能的原因:
    echo 1. 需要登录阿里云容器镜像服务
    echo 2. 镜像地址不正确
    echo.
    echo 备选方案: 使用Docker Hub官方镜像 (可能需要VPN)
    echo docker pull redis:7-alpine
    echo.
    set /p continue="是否继续尝试启动? (y/N): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    echo ✓ Redis镜像拉取成功
)

echo.
echo 步骤2: 拉取PostgreSQL镜像 (阿里云镜像)...
docker pull registry.aliyuncs.com/pgvector/pgvector:pg16
if errorlevel 1 (
    echo ⚠️  PostgreSQL镜像拉取失败
    echo 可能的原因:
    echo 1. 阿里云镜像仓库中不存在此镜像
    echo 2. 需要从Docker Hub拉取原始镜像
    echo.
    echo 备选方案: 使用Docker Hub官方镜像 (可能需要VPN)
    echo docker pull pgvector/pgvector:pg16
    echo.
    set /p continue="是否继续尝试启动? (y/N): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    echo ✓ PostgreSQL镜像拉取成功
)

echo.
echo 步骤3: 启动基础服务...
echo 使用中国镜像配置启动Redis和PostgreSQL...
echo.

docker-compose -f docker-compose.microservices.china.yml up -d redis postgres

echo.
echo 等待服务启动...
timeout /t 15 /nobreak >nul

echo.
echo 步骤4: 验证服务状态...
echo.

REM 检查Redis
echo 检查Redis服务...
docker-compose -f docker-compose.microservices.china.yml exec -T redis redis-cli ping 2>nul | find "PONG" >nul
if errorlevel 1 (
    echo ❌ Redis服务未就绪
    echo 查看日志: docker-compose -f docker-compose.microservices.china.yml logs redis
) else (
    echo ✓ Redis服务正常运行
)

REM 检查PostgreSQL
echo 检查PostgreSQL服务...
docker-compose -f docker-compose.microservices.china.yml exec -T postgres pg_isready -U clawai 2>nul
if errorlevel 1 (
    echo ❌ PostgreSQL服务未就绪
    echo 查看日志: docker-compose -f docker-compose.microservices.china.yml logs postgres
) else (
    echo ✓ PostgreSQL服务正常运行
)

echo.
echo ========================================
echo 中国镜像服务启动完成
echo ========================================
echo.
echo 📊 服务状态:
echo   配置文件: docker-compose.microservices.china.yml
echo   Redis:     localhost:6379
echo   PostgreSQL: localhost:5432
echo.
echo 🔧 管理命令:
echo   查看状态: docker-compose -f docker-compose.microservices.china.yml ps
echo   查看日志: docker-compose -f docker-compose.microservices.china.yml logs -f
echo   停止服务: docker-compose -f docker-compose.microservices.china.yml down
echo.
echo 📌 注意事项:
echo   1. 如果镜像拉取失败，可能需要配置VPN或代理
echo   2. 阿里云镜像可能需要登录账户
echo   3. 可尝试手动拉取镜像: docker pull redis:7-alpine
echo.
pause