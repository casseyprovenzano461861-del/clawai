# ClawAI 自动化渗透测试系统启动脚本 (PowerShell版本)
# 使用方法：右键点击此文件，选择"使用PowerShell运行"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ClawAI 自动化渗透测试系统启动脚本" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "[1/3] 检查Python环境..." -ForegroundColor Gray
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python环境正常: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
} catch {
    Write-Host "❌ 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

# 检查Node.js环境
Write-Host "[2/3] 检查Node.js环境..." -ForegroundColor Gray
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Node.js环境正常: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ 未找到Node.js，请先安装Node.js 16+" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
} catch {
    Write-Host "❌ 未找到Node.js，请先安装Node.js 16+" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

# 检查项目依赖
Write-Host "[3/3] 检查项目依赖..." -ForegroundColor Gray
if (Test-Path "backend\requirements.txt") {
    Write-Host "📦 后端依赖文件存在" -ForegroundColor Blue
} else {
    Write-Host "⚠️  未找到后端依赖文件" -ForegroundColor Yellow
}

if (Test-Path "frontend\package.json") {
    Write-Host "📦 前端依赖文件存在" -ForegroundColor Blue
} else {
    Write-Host "⚠️  未找到前端依赖文件" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           启动服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取当前脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 启动后端API服务器（端口5000）
Write-Host "🚀 启动后端API服务器（端口5000）..." -ForegroundColor Magenta
$backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$scriptDir\backend`" && python api_server.py" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3

# 启动前端开发服务器（端口3000）
Write-Host "🚀 启动前端开发服务器（端口3000）..." -ForegroundColor Magenta
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$scriptDir\frontend`" && npm run dev -- --host 0.0.0.0" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           服务状态" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ 后端API服务器：http://localhost:5000" -ForegroundColor Green
Write-Host "✅ 前端开发服务器：http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "📋 可用接口：" -ForegroundColor Blue
Write-Host "   - POST /attack         生成攻击链" -ForegroundColor Gray
Write-Host "   - GET  /health         健康检查" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 使用步骤：" -ForegroundColor Blue
Write-Host "   1. 打开浏览器访问 http://localhost:3000" -ForegroundColor Gray
Write-Host "   2. 输入目标IP或域名" -ForegroundColor Gray
Write-Host "   3. 点击'开始攻击'按钮" -ForegroundColor Gray
Write-Host "   4. 查看攻击链可视化结果" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  注意：请确保两个终端窗口都保持打开状态" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 显示进程信息
Write-Host "📊 进程信息：" -ForegroundColor Blue
Write-Host "   后端进程ID: $($backendProcess.Id)" -ForegroundColor Gray
Write-Host "   前端进程ID: $($frontendProcess.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "要停止服务，请关闭两个终端窗口" -ForegroundColor Yellow

# 保持脚本运行，但允许用户按Enter继续
Read-Host "按Enter键继续（脚本将继续运行，服务在后台）"

# 可选：打开浏览器
$openBrowser = Read-Host "是否要打开浏览器访问前端界面？(y/n)"
if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
    Start-Process "http://localhost:3000"
    Write-Host "🌐 浏览器已打开" -ForegroundColor Green
}

Write-Host ""
Write-Host "脚本运行完成，服务已在后台启动。" -ForegroundColor Green
Write-Host "要停止服务，请手动关闭两个终端窗口。" -ForegroundColor Yellow