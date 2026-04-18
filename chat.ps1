# ClawAI - AI 命令行模式启动脚本
# 用法: .\chat.ps1 [目标地址]

$ErrorActionPreference = "SilentlyContinue"
Set-Location $PSScriptRoot

# 查找 Python
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    $p = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($p) { $python = $p.Source; break }
}
# 备用路径
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
    Write-Host "  Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "    ClawAI  AI Penetration Testing Assistant" -ForegroundColor Magenta
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host "  Python: $python" -ForegroundColor DarkGray
Write-Host ""

# API Key 检查
$envFile = Join-Path $PSScriptRoot ".env"
$hasKey = $false
if (Test-Path $envFile) {
    $content = Get-Content $envFile -Raw
    if ($content -match "DEEPSEEK_API_KEY\s*=\s*\S+" -or $content -match "OPENAI_API_KEY\s*=\s*\S+") {
        $hasKey = $true
    }
}
if (-not $hasKey) {
    Write-Host "  [INFO] No API Key detected - will use mock mode" -ForegroundColor Yellow
    Write-Host "  Edit .env and set DEEPSEEK_API_KEY to use real AI" -ForegroundColor DarkGray
    Write-Host ""
}

# 启动
if ($args.Count -gt 0) {
    & $python clawai.py chat -t $args[0]
} else {
    & $python clawai.py chat
}
