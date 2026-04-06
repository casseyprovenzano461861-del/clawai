# ClawAI 中国镜像服务启动脚本 - PowerShell版本
# 使用国内镜像源，解决网络连接问题

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ClawAI 中国镜像服务启动脚本 (PowerShell版本)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "使用国内镜像源，解决Docker Hub连接问题"
Write-Host ""

# 检查是否在正确目录
if (-not (Test-Path "docker-compose.microservices.china.yml")) {
    Write-Host "错误: 缺少中国镜像配置文件" -ForegroundColor Red
    Write-Host "请确保 docker-compose.microservices.china.yml 存在" -ForegroundColor Yellow
    pause
    exit 1
}

# 检查Docker是否运行
try {
    docker info 2>$null | Out-Null
    Write-Host "✓ Docker守护进程正常运行" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker守护进程未运行" -ForegroundColor Red
    Write-Host "请启动Docker Desktop应用程序" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""

# 停止现有服务
Write-Host "停止现有服务..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.microservices.yml down 2>$null
} catch {
    try {
        docker-compose -f docker-compose.microservices.china.yml down 2>$null
    } catch {
        Write-Host "没有运行中的服务" -ForegroundColor Gray
    }
}

Write-Host ""

# 步骤1: 拉取Redis镜像
Write-Host "步骤1: 拉取Redis镜像 (阿里云镜像)..." -ForegroundColor Yellow
$redisSuccess = $false
try {
    docker pull registry.cn-hangzhou.aliyuncs.com/aliyun-ocs/redis:7-alpine 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Redis镜像拉取成功 (aliyun-ocs)" -ForegroundColor Green
        $redisSuccess = $true
    }
} catch {
    Write-Host "⚠️  Redis镜像拉取失败" -ForegroundColor Yellow
    Write-Host "可能的原因:" -ForegroundColor Gray
    Write-Host "1. 需要登录阿里云容器镜像服务" -ForegroundColor Gray
    Write-Host "2. 镜像地址不正确" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Gray
    Write-Host "备选方案: 使用Docker Hub官方镜像 (可能需要VPN)" -ForegroundColor Gray
    Write-Host "  docker pull redis:7-alpine" -ForegroundColor Gray
    Write-Host ""

    $continue = Read-Host "是否尝试拉取Docker Hub官方镜像? (y/N)"
    if ($continue -eq "y" -or $continue -eq "Y") {
        try {
            docker pull redis:7-alpine 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Docker Hub Redis镜像拉取成功" -ForegroundColor Green
                $redisSuccess = $true
            } else {
                Write-Host "❌ Redis镜像拉取失败" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Redis镜像拉取失败" -ForegroundColor Red
        }
    }
}

Write-Host ""

# 步骤2: 拉取PostgreSQL镜像
Write-Host "步骤2: 拉取PostgreSQL镜像 (阿里云镜像)..." -ForegroundColor Yellow
$postgresSuccess = $false
try {
    docker pull registry.aliyuncs.com/pgvector/pgvector:pg16 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL镜像拉取成功" -ForegroundColor Green
        $postgresSuccess = $true
    }
} catch {
    Write-Host "⚠️  PostgreSQL镜像拉取失败" -ForegroundColor Yellow
    Write-Host "可能的原因:" -ForegroundColor Gray
    Write-Host "1. 阿里云镜像仓库中不存在此镜像" -ForegroundColor Gray
    Write-Host "2. 需要从Docker Hub拉取原始镜像" -ForegroundColor Gray
    Write-Host "" -ForegroundColor Gray
    Write-Host "备选方案: 使用Docker Hub官方镜像 (可能需要VPN)" -ForegroundColor Gray
    Write-Host "  docker pull pgvector/pgvector:pg16" -ForegroundColor Gray
    Write-Host ""

    $continue = Read-Host "是否尝试拉取Docker Hub官方镜像? (y/N)"
    if ($continue -eq "y" -or $continue -eq "Y") {
        try {
            docker pull pgvector/pgvector:pg16 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Docker Hub PostgreSQL镜像拉取成功" -ForegroundColor Green
                $postgresSuccess = $true
            } else {
                Write-Host "❌ PostgreSQL镜像拉取失败" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ PostgreSQL镜像拉取失败" -ForegroundColor Red
        }
    }
}

Write-Host ""

# 步骤3: 启动基础服务
Write-Host "步骤3: 启动基础服务..." -ForegroundColor Yellow
Write-Host "使用中国镜像配置启动Redis和PostgreSQL..." -ForegroundColor Gray
Write-Host ""

if ($redisSuccess -or $postgresSuccess) {
    try {
        docker-compose -f docker-compose.microservices.china.yml up -d redis postgres
        Write-Host "✓ 服务启动命令已执行" -ForegroundColor Green
    } catch {
        Write-Host "❌ 服务启动失败" -ForegroundColor Red
        Write-Host "错误信息: $_" -ForegroundColor DarkRed
    }
} else {
    Write-Host "⚠️  没有成功拉取任何镜像，跳过服务启动" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "等待15秒让服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""

# 步骤4: 验证服务状态
Write-Host "步骤4: 验证服务状态..." -ForegroundColor Yellow
Write-Host ""

# 检查Redis
Write-Host "检查Redis服务..." -ForegroundColor Cyan
try {
    $redisOutput = docker-compose -f docker-compose.microservices.china.yml exec -T redis redis-cli ping 2>$null
    if ($redisOutput -match "PONG") {
        Write-Host "✓ Redis服务正常运行" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis服务未就绪" -ForegroundColor Red
        Write-Host "查看日志: docker-compose -f docker-compose.microservices.china.yml logs redis" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Redis服务未就绪" -ForegroundColor Red
    Write-Host "查看日志: docker-compose -f docker-compose.microservices.china.yml logs redis" -ForegroundColor Gray
}

Write-Host ""

# 检查PostgreSQL
Write-Host "检查PostgreSQL服务..." -ForegroundColor Cyan
try {
    docker-compose -f docker-compose.microservices.china.yml exec -T postgres pg_isready -U clawai 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL服务正常运行" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL服务未就绪" -ForegroundColor Red
        Write-Host "查看日志: docker-compose -f docker-compose.microservices.china.yml logs postgres" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ PostgreSQL服务未就绪" -ForegroundColor Red
    Write-Host "查看日志: docker-compose -f docker-compose.microservices.china.yml logs postgres" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "中国镜像服务启动完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 服务状态:" -ForegroundColor White
Write-Host "  配置文件: docker-compose.microservices.china.yml" -ForegroundColor Gray
Write-Host "  Redis:     localhost:6379" -ForegroundColor Gray
Write-Host "  PostgreSQL: localhost:5432" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 管理命令:" -ForegroundColor White
Write-Host "  查看状态: docker-compose -f docker-compose.microservices.china.yml ps" -ForegroundColor Gray
Write-Host "  查看日志: docker-compose -f docker-compose.microservices.china.yml logs -f" -ForegroundColor Gray
Write-Host "  停止服务: docker-compose -f docker-compose.microservices.china.yml down" -ForegroundColor Gray
Write-Host ""
Write-Host "📌 注意事项:" -ForegroundColor White
Write-Host "  1. 如果镜像拉取失败，可能需要配置VPN或代理" -ForegroundColor Gray
Write-Host "  2. 阿里云镜像可能需要登录账户" -ForegroundColor Gray
Write-Host "  3. 可尝试手动拉取镜像: docker pull redis:7-alpine" -ForegroundColor Gray
Write-Host ""

pause