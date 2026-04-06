# PowerShell脚本配置Docker镜像加速器
# 针对中国网络环境优化

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker 镜像加速器配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查当前Docker配置
Write-Host "1. 检查当前Docker配置..." -ForegroundColor Yellow
$dockerConfigPath = "$env:USERPROFILE\.docker\daemon.json"

if (Test-Path $dockerConfigPath) {
    Write-Host "   ✓ 找到Docker配置文件: $dockerConfigPath" -ForegroundColor Green
    $currentConfig = Get-Content $dockerConfigPath -Raw | ConvertFrom-Json
    Write-Host "   当前配置:" -ForegroundColor Gray
    ConvertTo-Json $currentConfig -Depth 5 | Out-Host
} else {
    Write-Host "   ℹ️  Docker配置文件不存在，将创建新配置" -ForegroundColor Yellow
}

# 2. 选择镜像加速器
Write-Host "`n2. 选择镜像加速器 (推荐阿里云)..." -ForegroundColor Yellow

$mirrorOptions = @(
    @{Name="阿里云镜像加速器"; URL="https://cr.console.aliyun.com/cn-hangzhou/instances/mirrors"},
    @{Name="腾讯云镜像加速器"; URL="https://mirror.ccs.tencentyun.com"},
    @{Name="Docker中国官方镜像"; URL="https://registry.docker-cn.com"},
    @{Name="中科大镜像加速器"; URL="https://docker.mirrors.ustc.edu.cn"},
    @{Name="网易镜像加速器"; URL="https://hub-mirror.c.163.com"}
)

for ($i = 0; $i -lt $mirrorOptions.Count; $i++) {
    Write-Host "   $($i+1). $($mirrorOptions[$i].Name)" -ForegroundColor Gray
}

$selection = Read-Host "`n请输入选择 (1-5，推荐1)"
$selectedIndex = [int]$selection - 1

if ($selectedIndex -lt 0 -or $selectedIndex -ge $mirrorOptions.Count) {
    $selectedIndex = 0  # 默认阿里云
}

$selectedMirror = $mirrorOptions[$selectedIndex]
Write-Host "`n   选择: $($selectedMirror.Name)" -ForegroundColor Green
Write-Host "   镜像加速器地址: $($selectedMirror.URL)" -ForegroundColor Gray

# 3. 配置镜像加速器
Write-Host "`n3. 配置镜像加速器..." -ForegroundColor Yellow

# 获取阿里云镜像加速器地址（需要用户注册）
if ($selectedMirror.Name -eq "阿里云镜像加速器") {
    Write-Host "   请访问阿里云容器镜像服务获取个人镜像加速器地址:" -ForegroundColor Cyan
    Write-Host "   1. 打开 https://cr.console.aliyun.com/cn-hangzhou/instances/mirrors" -ForegroundColor Gray
    Write-Host "   2. 登录阿里云账号" -ForegroundColor Gray
    Write-Host "   3. 复制您的专属加速器地址（类似 https://xxxxxx.mirror.aliyuncs.com）" -ForegroundColor Gray
    Write-Host ""

    $aliyunMirror = Read-Host "请输入您的阿里云镜像加速器地址 (按Enter使用公共镜像)"
    if ($aliyunMirror -ne "") {
        $selectedMirror.URL = $aliyunMirror
    } else {
        # 使用公共阿里云镜像（可能不稳定）
        $selectedMirror.URL = "https://registry.cn-hangzhou.aliyuncs.com"
    }
}

# 4. 创建或更新配置文件
Write-Host "`n4. 更新Docker配置文件..." -ForegroundColor Yellow

$daemonConfig = @{
    "registry-mirrors" = @($selectedMirror.URL)
    "insecure-registries" = @()
    "debug" = $true
    "experimental" = $false
}

# 保持现有配置（如果存在）
if (Test-Path $dockerConfigPath) {
    $existingConfig = Get-Content $dockerConfigPath -Raw | ConvertFrom-Json
    foreach ($key in $existingConfig.PSObject.Properties.Name) {
        if ($key -ne "registry-mirrors") {
            $daemonConfig[$key] = $existingConfig.$key
        }
    }
}

# 写入配置文件
$daemonConfigJson = ConvertTo-Json $daemonConfig -Depth 10
Set-Content -Path $dockerConfigPath -Value $daemonConfigJson -Encoding UTF8

Write-Host "   ✓ 配置文件已更新: $dockerConfigPath" -ForegroundColor Green
Write-Host "   配置内容:" -ForegroundColor Gray
$daemonConfigJson | Out-Host

# 5. 重启Docker Desktop
Write-Host "`n5. 重启Docker Desktop..." -ForegroundColor Yellow
Write-Host "   请手动执行以下步骤:" -ForegroundColor Cyan
Write-Host "   1. 右键点击系统托盘中的Docker图标" -ForegroundColor Gray
Write-Host "   2. 选择 'Restart'" -ForegroundColor Gray
Write-Host "   3. 等待Docker完全启动 (约30秒)" -ForegroundColor Gray
Write-Host "   4. 验证配置是否生效: docker info | grep -A 5 'Registry Mirrors'" -ForegroundColor Gray

# 6. 测试镜像拉取
Write-Host "`n6. 测试配置 (重启Docker后执行)..." -ForegroundColor Yellow
Write-Host "   重启Docker后，运行以下命令测试:" -ForegroundColor Gray
Write-Host "   docker pull redis:7-alpine" -ForegroundColor Green
Write-Host "   docker pull pgvector/pgvector:pg16" -ForegroundColor Green
Write-Host "   docker pull kalilinux/kali-rolling:latest" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "配置完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "重要: 请先重启Docker Desktop使配置生效" -ForegroundColor Red
Write-Host ""
Write-Host "如果仍然无法拉取镜像，可能需要检查:" -ForegroundColor Yellow
Write-Host "• 网络连接 (防火墙、代理)" -ForegroundColor Gray
Write-Host "• DNS设置 (可以尝试使用 8.8.8.8 或 114.114.114.114)" -ForegroundColor Gray
Write-Host "• 使用VPN连接国际网络" -ForegroundColor Gray