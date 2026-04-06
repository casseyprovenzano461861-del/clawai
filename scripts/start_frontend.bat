@echo off
echo ========================================
echo ClawAI 前端启动脚本
echo ========================================
echo.

REM 检查Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Node.js
    echo 请安装Node.js 16.0或更高版本
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 检查npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到npm
    echo 请确保Node.js安装完整
    pause
    exit /b 1
)

REM 显示版本信息
echo ✅ Node.js版本:
node --version
echo ✅ npm版本:
npm --version
echo.

REM 检查前端目录
if not exist "frontend\" (
    echo ❌ 错误: 未找到frontend目录
    echo 请确保在当前目录运行脚本
    pause
    exit /b 1
)

REM 进入前端目录
cd frontend

REM 检查package.json
if not exist "package.json" (
    echo ❌ 错误: 未找到package.json
    echo 前端项目结构不完整
    pause
    exit /b 1
)

REM 检查node_modules
if not exist "node_modules\" (
    echo ⚠️ 检测到未安装依赖，开始安装...
    echo 这可能需要几分钟时间，请耐心等待...
    echo.
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 错误: 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
    echo.
)

echo 🚀 启动ClawAI前端...
echo 访问地址: http://localhost:5173
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

REM 启动开发服务器
npm run dev