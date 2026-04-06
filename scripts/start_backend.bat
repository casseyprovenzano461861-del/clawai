@echo off
echo ========================================
echo ClawAI 后端启动脚本
echo ========================================
echo.

REM 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python
    echo 请安装Python 3.8或更高版本
    echo 下载地址: https://python.org/
    pause
    exit /b 1
)

REM 显示版本信息
echo ✅ Python版本:
python --version
echo.

REM 检查后端目录
if not exist "backend\" (
    echo ❌ 错误: 未找到backend目录
    echo 请确保在当前目录运行脚本
    pause
    exit /b 1
)

REM 进入后端目录
cd backend

REM 检查app.py
if not exist "app.py" (
    echo ❌ 错误: 未找到app.py
    echo 后端项目结构不完整
    pause
    exit /b 1
)

REM 检查requirements.txt
if not exist "requirements.txt" (
    echo ⚠️ 警告: 未找到requirements.txt
    echo 将尝试直接启动应用...
) else (
    echo 📦 检查Python依赖...
    echo.
    
    REM 检查pip
    where pip >nul 2>nul
    if %errorlevel% neq 0 (
        echo ⚠️ 警告: 未找到pip，跳过依赖检查
    ) else (
        echo ✅ pip版本:
        pip --version
        echo.
        
        REM 检查Flask
        python -c "import flask" 2>nul
        if %errorlevel% neq 0 (
            echo ⚠️ 检测到缺少依赖，开始安装...
            echo 这可能需要几分钟时间，请耐心等待...
            echo.
            pip install -r requirements.txt
            if %errorlevel% neq 0 (
                echo ❌ 错误: 依赖安装失败
                echo 请手动运行: pip install -r requirements.txt
                pause
                exit /b 1
            )
            echo ✅ 依赖安装完成
            echo.
        ) else (
            echo ✅ 依赖已安装
            echo.
        )
    )
)

echo 🚀 启动ClawAI后端...
echo API地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

REM 启动Flask应用
python app.py