# PowerShell脚本检查Docker Desktop状态
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop 诊断工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker Desktop进程
Write-Host "1. 检查Docker Desktop进程..." -ForegroundColor Yellow
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "   ✓ Docker Desktop进程正在运行 (PID: $($dockerProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "   ❌ Docker Desktop进程未运行" -ForegroundColor Red
}

# 检查Docker服务
Write-Host "`n2. 检查Docker服务状态..." -ForegroundColor Yellow
try {
    $dockerService = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
    if ($dockerService -and $dockerService.Status -eq "Running") {
        Write-Host "   ✓ Docker服务正在运行" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker服务未运行" -ForegroundColor Red
    }
} catch {
    Write-Host "   ⚠  无法检查Docker服务状态: $_" -ForegroundColor Yellow
}

# 检查Docker CLI连接
Write-Host "`n3. 测试Docker CLI连接..." -ForegroundColor Yellow
try {
    docker version --format "{{.Client.Version}}" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker CLI连接正常" -ForegroundColor Green
        $dockerVersion = docker version --format "{{.Client.Version}}"
        Write-Host "   Docker版本: $dockerVersion" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ Docker CLI连接失败" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Docker CLI连接异常: $_" -ForegroundColor Red
}

# 检查Docker守护进程连接
Write-Host "`n4. 测试Docker守护进程连接..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker守护进程连接正常" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker守护进程连接失败" -ForegroundColor Red
        Write-Host "   错误信息: $dockerInfo" -ForegroundColor DarkRed
    }
} catch {
    Write-Host "   ❌ 连接测试异常: $_" -ForegroundColor Red
}

# 检查Docker Compose
Write-Host "`n5. 检查Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker Compose可用: $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker Compose不可用" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Docker Compose检查异常: $_" -ForegroundColor Red
}

# 提供解决方案
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "解决方案" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($dockerProcess -and ($dockerInfo -notmatch "failed to connect")) {
    Write-Host "✅ Docker Desktop运行正常，可以继续执行微服务启动。" -ForegroundColor Green
    Write-Host "   运行: .\start-microservices.sh" -ForegroundColor Gray
} else {
    Write-Host "⚠  Docker Desktop需要启动或重启" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请执行以下步骤:" -ForegroundColor White
    Write-Host "1. 点击开始菜单，搜索 'Docker Desktop' 并启动" -ForegroundColor Gray
    Write-Host "2. 等待系统托盘显示 'Docker Desktop is running' (约30-60秒)" -ForegroundColor Gray
    Write-Host "3. 重新运行此诊断脚本: .\check-docker.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "如果问题持续存在:" -ForegroundColor White
    Write-Host "• 重启Docker Desktop: 右键点击系统托盘图标 → Restart" -ForegroundColor Gray
    Write-Host "• 重启计算机" -ForegroundColor Gray
    Write-Host "• 确保Windows版本支持Docker Desktop (Windows 10/11 Pro/Enterprise)" -ForegroundColor Gray
}

Write-Host "`n提示: 如果使用Git Bash或WSL，请确保在Docker Desktop设置中启用:" -ForegroundColor Cyan
Write-Host "• Settings → General → Expose daemon on tcp://localhost:2375 without TLS" -ForegroundColor Gray
Write-Host "• Settings → Resources → WSL Integration → 启用WSL2集成" -ForegroundColor Gray
