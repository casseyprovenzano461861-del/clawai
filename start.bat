@echo off
setlocal enabledelayedexpansion

echo ==========================
echo ClawAI 一键启动脚本
echo ==========================

:: 检查Python是否安装
echo 检查Python安装情况...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python 3.8或更高版本。
    pause
    exit /b 1
)
echo Python已安装

:: 检查后端依赖
echo 检查后端依赖...
if not exist "backend\requirements.txt" (
    echo 错误: 未找到backend\requirements.txt文件。
    pause
    exit /b 1
)

:: 安装后端依赖
if not exist "backend\venv" (
    echo 创建虚拟环境...
    python -m venv backend\venv
)

echo 激活虚拟环境...
call backend\venv\Scripts\activate.bat

echo 安装后端依赖...
pip install -r backend\requirements.txt

:: 检查前端依赖
echo 检查前端依赖...
if not exist "frontend\package.json" (
    echo 错误: 未找到frontend\package.json文件。
    pause
    exit /b 1
)

:: 安装前端依赖
if not exist "frontend\node_modules" (
    echo 安装前端依赖...
    cd frontend
    npm install
    cd ..
)

:: 启动后端服务
echo 启动后端服务...
start "ClawAI Backend" cmd /c "call backend\venv\Scripts\activate.bat && python backend\main.py"

:: 等待后端服务启动
echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

:: 启动前端开发服务器
echo 启动前端开发服务器...
start "ClawAI Frontend" cmd /c "cd frontend && npm run dev"

:: 等待前端服务启动
echo 等待前端服务启动...
timeout /t 5 /nobreak >nul

:: 打开浏览器
echo 打开浏览器...
start http://localhost:5173

echo ==========================
echo ClawAI 启动完成！
echo 后端服务运行在: http://localhost:5000
echo 前端服务运行在: http://localhost:5173
echo ==========================
echo 按任意键退出...
pause >nul
exit /b 0
