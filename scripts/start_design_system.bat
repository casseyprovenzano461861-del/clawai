@echo off
echo ========================================
echo ClawAI 设计系统启动脚本
echo ========================================
echo.

REM 检查是否在frontend目录
if not exist "package.json" (
    echo 错误：请在frontend目录中运行此脚本
    echo 当前目录：%cd%
    pause
    exit /b 1
)

echo 1. 检查依赖...
call npm list react-router-dom
if errorlevel 1 (
    echo 安装react-router-dom...
    call npm install react-router-dom
)

echo.
echo 2. 启动开发服务器...
echo 请访问：http://localhost:5173
echo.
echo 可用页面：
echo - 主仪表板：http://localhost:5173/
echo - 设计系统：http://localhost:5173/design-system
echo - 实施进度：http://localhost:5173/implementation
echo.
echo 按 Ctrl+C 停止服务器
echo.

REM 启动开发服务器
call npx vite --host