@echo off
echo ========================================
echo ClawAI - Metasploit 安装脚本
echo ========================================
echo.

REM 检查Docker是否安装
echo 检查Docker安装...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker未安装！
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [成功] Docker已安装

REM 创建必要的目录
echo 创建数据目录...
if not exist "data\metasploit" mkdir "data\metasploit"
if not exist "data\postgres" mkdir "data\postgres"
if not exist "logs\metasploit" mkdir "logs\metasploit"

REM 拉取Metasploit镜像
echo 拉取Metasploit Docker镜像...
docker pull metasploitframework/metasploit-framework:latest

if %errorlevel% neq 0 (
    echo [错误] 拉取Metasploit镜像失败！
    pause
    exit /b 1
)

echo [成功] Metasploit镜像已拉取

REM 拉取PostgreSQL镜像
echo 拉取PostgreSQL Docker镜像...
docker pull postgres:14-alpine

if %errorlevel% neq 0 (
    echo [错误] 拉取PostgreSQL镜像失败！
    pause
    exit /b 1
)

echo [成功] PostgreSQL镜像已拉取

REM 启动Metasploit服务
echo 启动Metasploit服务...
docker-compose -f docker-compose.metasploit.yml up -d

if %errorlevel% neq 0 (
    echo [错误] 启动Metasploit服务失败！
    echo 尝试使用docker命令直接启动...
    
    echo 启动PostgreSQL容器...
    docker run -d --name clawai-metasploit-postgres ^
        -e POSTGRES_USER=msf ^
        -e POSTGRES_PASSWORD=msf ^
        -e POSTGRES_DB=msf ^
        -v "%cd%\data\postgres:/var/lib/postgresql/data" ^
        postgres:14-alpine
    
    timeout /t 10 /nobreak >nul
    
    echo 启动Metasploit容器...
    docker run -d --name clawai-metasploit ^
        -p 4444:4444 ^
        -p 8080:8080 ^
        -p 55553:55553 ^
        -e DATABASE_URL=postgres://msf:msf@clawai-metasploit-postgres:5432/msf ^
        -v "%cd%\data\metasploit:/root/.msf4" ^
        -v "%cd%\logs\metasploit:/var/log/metasploit" ^
        --link clawai-metasploit-postgres:postgres ^
        metasploitframework/metasploit-framework:latest ^
        bash -c "sleep 10 && msfdb init && msfconsole -q -x 'db_status; version; exit'"
)

echo.
echo ========================================
echo Metasploit安装完成！
echo ========================================
echo.
echo 服务状态:
docker ps --filter "name=clawai" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 使用说明:
echo 1. 访问Metasploit控制台: docker exec -it clawai-metasploit msfconsole
echo 2. 查看日志: docker logs clawai-metasploit
echo 3. 停止服务: docker-compose -f docker-compose.metasploit.yml down
echo 4. 重启服务: docker-compose -f docker-compose.metasploit.yml restart
echo.
echo 在ClawAI中使用:
echo 1. 确保backend/tools/metasploit_integration.py已正确配置
echo 2. 在complete_tool_list.json中更新Metasploit安装状态
echo 3. 在unified_executor_final.py中集成Metasploit执行器
echo.
pause