# ClawAI - 全栈启动脚本（后端 + 前端 Web UI）
# 用法: .\webui.ps1

$ErrorActionPreference = "SilentlyContinue"
Set-Location $PSScriptRoot

# 查找 Python
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    $p = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($p) { $python = $p.Source; break }
}
if (-not $python) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "D:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $python = $c; break }
    }
}
if (-not $python) {
    Write-Host ""
    Write-Host "  [ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 查找 Node.js
$node = Get-Command node -ErrorAction SilentlyContinue
$hasNode = $node -ne $null

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "    ClawAI  Web UI  (Backend + Frontend)" -ForegroundColor Magenta
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend : http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor DarkGray
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""

if (-not $hasNode) {
    Write-Host "  [WARN] Node.js not found - starting backend only" -ForegroundColor Yellow
    Write-Host ""
    & $python start.py --backend --auto-port
    Read-Host "Press Enter to exit"
    exit 0
}

# 检查前端依赖
$nodeModules = Join-Path $PSScriptRoot "frontend\node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "  [SETUP] Installing frontend dependencies (first time)..." -ForegroundColor Yellow
    Push-Location (Join-Path $PSScriptRoot "frontend")
    & npm install
    Pop-Location
    Write-Host ""
}

# 启动
& $python start.py --auto-port
