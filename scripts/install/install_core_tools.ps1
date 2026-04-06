# ClawAI 核心工具安装脚本 (PowerShell)
# 自动安装关键渗透测试工具，提升真实执行比例

Write-Host "🔧 ClawAI 核心工具安装脚本" -ForegroundColor Cyan
Write-Host "正在安装核心渗透测试工具以提升真实执行比例..." -ForegroundColor Yellow
Write-Host ""

# 检查是否为管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  建议以管理员权限运行此脚本以获得最佳安装体验" -ForegroundColor Red
    Write-Host ""
}

# 1. 检查并安装 Chocolatey（Windows 包管理器）
function Install-Chocolatey {
    Write-Host "1. 检查 Chocolatey 包管理器..." -ForegroundColor Green
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "   ✅ Chocolatey 已安装" -ForegroundColor Green
        return $true
    } else {
        Write-Host "   🔧 正在安装 Chocolatey..." -ForegroundColor Yellow
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
            Write-Host "   ✅ Chocolatey 安装完成" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "   ❌ Chocolatey 安装失败: $_" -ForegroundColor Red
            Write-Host "   您可以手动安装 Chocolatey: https://chocolatey.org/install" -ForegroundColor Yellow
            return $false
        }
    }
}

# 2. 安装核心工具
function Install-CoreTools {
    Write-Host ""
    Write-Host "2. 安装核心渗透测试工具..." -ForegroundColor Green
    
    $toolsToInstall = @(
        @{Name = "nmap"; Description = "端口扫描器"},
        @{Name = "masscan"; Description = "高速端口扫描器"},
        @{Name = "nikto"; Description = "Web服务器扫描器"},
        @{Name = "nuclei"; Description = "漏洞扫描器"},
        @{Name = "httpx"; Description = "HTTP探测工具"},
        @{Name = "whatweb"; Description = "Web指纹识别"},
        @{Name = "sqlmap"; Description = "SQL注入工具"}
    )
    
    $chocoAvailable = Get-Command choco -ErrorAction SilentlyContinue
    
    foreach ($tool in $toolsToInstall) {
        $toolName = $tool.Name
        $description = $tool.Description
        
        Write-Host "   📦 $toolName - $description" -ForegroundColor Cyan
        
        # 检查是否已安装
        $installed = $false
        if (Get-Command $toolName -ErrorAction SilentlyContinue) {
            Write-Host "      ✅ 已安装" -ForegroundColor Green
            $installed = $true
        } else {
            Write-Host "      🔧 需要安装" -ForegroundColor Yellow
            
            # 尝试使用 Chocolatey 安装
            if ($chocoAvailable) {
                try {
                    Write-Host "      正在使用 Chocolatey 安装..." -ForegroundColor Gray
                    choco install $toolName -y --no-progress
                    Write-Host "      ✅ 安装完成" -ForegroundColor Green
                    $installed = $true
                } catch {
                    Write-Host "      ❌ Chocolatey 安装失败" -ForegroundColor Red
                }
            } else {
                Write-Host "      ℹ️  Chocolatey 不可用，请手动安装" -ForegroundColor Yellow
                Write-ManualInstallGuide $toolName
            }
        }
        
        # 验证安装
        if ($installed) {
            try {
                $version = & $toolName --version 2>&1 | Select-Object -First 1
                if ($version -and $version -notmatch "错误|错误|Error|error") {
                    Write-Host "      版本: $version" -ForegroundColor Gray
                }
            } catch {
                # 忽略版本检查错误
            }
        }
        
        Write-Host ""
    }
}

# 3. 安装 Python 工具
function Install-PythonTools {
    Write-Host ""
    Write-Host "3. 安装 Python 工具..." -ForegroundColor Green
    
    $pythonTools = @(
        @{Name = "dirsearch"; Description = "目录爆破工具"; InstallCmd = "pip install dirsearch"},
        @{Name = "sublist3r"; Description = "子域名枚举"; InstallCmd = "pip install sublist3r"}
    )
    
    # 检查 Python
    $pythonAvailable = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonAvailable) {
        Write-Host "   ❌ Python 未安装，无法安装 Python 工具" -ForegroundColor Red
        Write-Host "   请先安装 Python: https://www.python.org/downloads/" -ForegroundColor Yellow
        return
    }
    
    foreach ($tool in $pythonTools) {
        $toolName = $tool.Name
        $description = $tool.Description
        $installCmd = $tool.InstallCmd
        
        Write-Host "   📦 $toolName - $description" -ForegroundColor Cyan
        
        # 尝试导入模块来检查是否安装
        $installed = $false
        try {
            $null = python -c "import $toolName" 2>&1
            Write-Host "      ✅ 已安装" -ForegroundColor Green
            $installed = $true
        } catch {
            Write-Host "      🔧 需要安装" -ForegroundColor Yellow
            
            try {
                Write-Host "      正在安装: $installCmd" -ForegroundColor Gray
                Invoke-Expression $installCmd
                Write-Host "      ✅ 安装完成" -ForegroundColor Green
                $installed = $true
            } catch {
                Write-Host "      ❌ 安装失败: $_" -ForegroundColor Red
            }
        }
        
        Write-Host ""
    }
}

# 4. 提供手动安装指南
function Write-ManualInstallGuide($toolName) {
    $guides = @{
        "masscan" = @"
  手动安装指南:
    1. 访问 https://github.com/robertdavidgraham/masscan/releases
    2. 下载最新版本的 masscan-windows.exe
    3. 重命名为 masscan.exe 并放置到系统 PATH 路径中
    4. 或直接放在当前目录下
"@
        "nikto" = @"
  手动安装指南:
    1. 下载 Nikto: https://github.com/sullo/nikto
    2. 解压到任意目录
    3. 将 nikto.pl 所在目录添加到系统 PATH
    4. 需要 Perl 环境 (Windows: https://strawberryperl.com/)
"@
        "nuclei" = @"
  手动安装指南:
    1. 下载 Nuclei: https://github.com/projectdiscovery/nuclei/releases
    2. 解压并将 nuclei.exe 放到系统 PATH 路径中
"@
        "httpx" = @"
  手动安装指南:
    1. 下载 HTTPX: https://github.com/projectdiscovery/httpx/releases
    2. 解压并将 httpx.exe 放到系统 PATH 路径中
"@
        "whatweb" = @"
  手动安装指南:
    1. 下载 WhatWeb: https://github.com/urbanadventurer/WhatWeb
    2. 需要 Ruby 环境，然后运行: ruby whatweb.rb
"@
    }
    
    if ($guides.ContainsKey($toolName)) {
        Write-Host $guides[$toolName] -ForegroundColor Gray
    }
}

# 5. 验证安装结果
function Test-Installations {
    Write-Host ""
    Write-Host "4. 验证工具安装..." -ForegroundColor Green
    
    $toolsToTest = @("nmap", "masscan", "nikto", "nuclei", "httpx", "whatweb", "sqlmap", "dirsearch")
    
    $installedCount = 0
    $totalCount = $toolsToTest.Count
    
    foreach ($tool in $toolsToTest) {
        if (Get-Command $tool -ErrorAction SilentlyContinue) {
            Write-Host "   ✅ $tool" -ForegroundColor Green
            $installedCount++
        } else {
            Write-Host "   ❌ $tool" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "安装完成统计:" -ForegroundColor Cyan
    Write-Host "  总工具数: $totalCount" -ForegroundColor White
    Write-Host "  已安装: $installedCount" -ForegroundColor Green
    Write-Host "  安装率: $([math]::Round($installedCount/$totalCount*100, 1))%" -ForegroundColor Yellow
    
    if ($installedCount -gt 0) {
        Write-Host ""
        Write-Host "🎉 安装完成！现在可以测试 ClawAI 的真实执行功能。" -ForegroundColor Green
        Write-Host "运行以下命令测试工具:" -ForegroundColor Cyan
        Write-Host "  python tools/tool_checker.py" -ForegroundColor White
        Write-Host "  python monitor_real_execution.py" -ForegroundColor White
        Write-Host "  python backend/tools/new_masscan.py example.com" -ForegroundColor White
    }
}

# 主执行流程
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "ClawAI 工具安装助手" -ForegroundColor Cyan
Write-Host "目标: 安装核心工具，提升真实执行比例" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# 询问用户确认
$confirmation = Read-Host "是否继续安装？(Y/N)"
if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-Host "安装已取消" -ForegroundColor Red
    exit 0
}

Write-Host ""

# 执行安装步骤
try {
    # 安装 Chocolatey
    $chocoInstalled = Install-Chocolatey
    
    # 安装核心工具
    Install-CoreTools
    
    # 安装 Python 工具
    Install-PythonTools
    
    # 验证安装结果
    Test-Installations
    
} catch {
    Write-Host "安装过程中出现错误: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "安装脚本执行完成" -ForegroundColor Cyan
Write-Host "请检查以上输出，确认工具安装状态" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Magenta