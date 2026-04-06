@echo off
chcp 65001 >nul
echo ========================================
echo ClawAI 真实启动器 - 完整功能版
echo ========================================
echo.

echo [1/3] 设置环境变量...
set DISABLE_AUTH=1

echo [2/3] 检查后端服务...
netstat -ano | findstr :8000 >nul
if errorlevel 1 (
    echo 后端服务未运行
    echo 正在启动后端服务...
    start /B cmd /c "cd /d %~dp0 && set DISABLE_AUTH=1 && python start.py"
    echo 等待后端启动...
    timeout /t 10 >nul
) else (
    echo 后端运行正常 (端口 8000)
)

echo [3/3] 打开真实功能界面...
echo 正在打开浏览器...
echo.
echo ========================================
echo 重要说明:
echo 1. 浏览器将打开真实功能界面
echo 2. 点击"执行安全扫描"按钮进行测试
echo 3. 所有数据来自真实API，非模拟数据
echo 4. 如需API文档，访问: http://localhost:8000/docs
echo 5. 如需停止服务，关闭此窗口和所有Python窗口
echo ========================================
echo.

start "" "http://localhost:8000/static/simple_interface.html"

echo 按任意键查看服务状态...
pause >nul

echo.
echo 当前服务状态:
curl -s http://localhost:8000/health | python -c "import sys,json; data=json.load(sys.stdin); print('状态:', data.get('status')); print('版本:', data.get('version'))" 2>nul || echo 无法获取状态，请检查服务

echo.
echo 按任意键退出...
pause >nul