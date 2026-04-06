@echo off
echo ========================================
echo ClawAI 前端构建脚本 (Windows)
echo ========================================
echo.

REM 检查Node.js是否安装
echo 1. 检查Node.js安装...
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Node.js未安装或未正确配置
    echo 请从 https://nodejs.org 安装Node.js 18或更高版本
    pause
    exit /b 1
)
node --version
echo.

REM 检查npm是否安装
echo 2. 检查npm安装...
npm --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] npm未安装或未正确配置
    echo 请重新安装Node.js
    pause
    exit /b 1
)
npm --version
echo.

REM 进入前端目录
echo 3. 进入前端目录...
cd /d "%~dp0frontend" || (
    echo [ERROR] 无法进入前端目录
    pause
    exit /b 1
)
echo.

REM 安装依赖
echo 4. 安装依赖...
echo 这可能需要几分钟时间，请耐心等待...
npm ci --only=production
if %errorLevel% neq 0 (
    echo [WARN] 依赖安装失败，尝试npm install...
    npm install
    if %errorLevel% neq 0 (
        echo [ERROR] 依赖安装失败
        pause
        exit /b 1
    )
)
echo [OK] 依赖安装成功
echo.

REM 构建前端
echo 5. 构建前端应用...
npm run build
if %errorLevel% neq 0 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)
echo [OK] 前端构建成功
echo.

echo 6. 构建完成...
echo ========================================
echo 前端构建完成！
echo ========================================
echo.
echo 构建文件位置:
echo 前端静态文件: frontend\dist\
echo 后端API: http://localhost:5000
echo 前端服务: http://localhost:3000
echo.
echo 启动方式:
echo 1. 启动后端服务: python backend/api_server.py
echo 2. 使用Docker部署: 运行 deploy.bat
echo 3. 手动部署: 将 dist/ 目录部署到任何Web服务器
echo.
echo ========================================
pause