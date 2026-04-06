# ClawAI 核心工具安装脚本 - 简化版
# 安装关键渗透测试工具以提升真实执行比例

Write-Host "=== ClawAI 核心工具安装脚本 ==="
Write-Host "正在安装核心渗透测试工具..."
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "警告: 建议以管理员权限运行此脚本"
    Write-Host ""
}

# 安装 Chocolatey
function Install-Chocolatey {
    Write-Host "1. 检查 Chocolatey 包管理器..."
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "   Chocolatey 已安装"
        return $true
    } else {
        Write-Host "   正在安装 Chocolatey..."
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
            Write-Host "   Chocolatey 安装完成"
            return $true
        } catch {
            Write-Host "   Chocolatey 安装失败: $_"
            Write-Host "   您可以手动安装 Chocolatey: https://chocolatey.org/install"
            return $false
        }
    }
}

# 安装核心工具
function Install-CoreTools {
    Write-Host ""
    Write-Host "2. 安装核心渗透测试工具..."
    
    # 定义要安装的工具
    $tools = @("nmap", "masscan", "nikto", "nuclei", "httpx", "whatweb", "sqlmap")
    
    foreach ($tool in $tools) {
        Write-Host "   检查 $tool..."
        
        # 检查是否已安装
        if (Get-Command $tool -ErrorAction SilentlyContinue) {
            Write-Host "   $tool 已安装"
        } else {
            Write-Host "   正在安装 $tool..."
            
            # 尝试使用 Chocolatey 安装
            if (Get-Command choco -ErrorAction SilentlyContinue) {
                try {
                    choco install $tool -y --no-progress
                    Write-Host "   $tool 安装完成"
                } catch {
                    Write-Host "   $tool Chocolatey 安装失败，尝试其他方法"
                }
            } else {
                Write-Host "   Chocolatey 不可用，需要手动安装 $tool"
                Write-Host "   请访问相关网站手动安装"
            }
        }
        Write-Host ""
    }
}

# 安装 Python 工具
function Install-PythonTools {
    Write-Host ""
    Write-Host "3. 安装 Python 工具..."
    
    # 检查 Python
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "   Python 未安装，跳过 Python 工具"
        return
    }
    
    # Python 工具列表
    $pythonTools = @(
        @{Name="dirsearch"; Cmd="pip install dirsearch"},
        @{Name="sublist3r"; Cmd="pip install sublist3r"}
    )
    
    foreach ($tool in $pythonTools) {
        $toolName = $tool.Name
        $installCmd = $tool.Cmd
        
        Write-Host "   检查 $toolName..."
        
        # 检查是否已安装
        $installed = $false
        try {
            $null = python -c "import $toolName" 2>&1
            $installed = $true
        } catch {
            $installed = $false
        }
        
        if ($installed) {
            Write-Host "   $toolName 已安装"
        } else {
            Write-Host "   正在安装 $toolName: $installCmd"
            try {
                Invoke-Expression $installCmd
                Write-Host "   $toolName 安装完成"
            } catch {
                Write-Host "   $toolName 安装失败: $_"
            }
        }
        Write-Host ""
    }
}

# 验证安装结果
function Test-Installations {
    Write-Host ""
    Write-Host "4. 验证工具安装..."
    
    $toolsToTest = @("nmap", "masscan", "nikto", "nuclei", "httpx", "whatweb", "sqlmap", "dirsearch")
    $installedCount = 0
    
    foreach ($tool in $toolsToTest) {
        if (Get-Command $tool -ErrorAction SilentlyContinue) {
            Write-Host "   $tool - 已安装"
            $installedCount++
        } else {
            Write-Host "   $tool - 未安装"
        }
    }
    
    Write-Host ""
    Write-Host "安装统计:"
    Write-Host "   总工具数: $($toolsToTest.Count)"
    Write-Host "   已安装: $installedCount"
    Write-Host "   安装率: $([math]::Round($installedCount/$toolsToTest.Count*100, 1))%"
    
    if ($installedCount -gt 0) {
        Write-Host ""
        Write-Host "安装完成！现在可以测试 ClawAI 的真实执行功能。"
        Write-Host "运行以下命令测试工具:"
        Write-Host "  python tools/tool_checker.py"
    }
}

# 主执行流程
Write-Host "========================================"
Write-Host "开始安装..."
Write-Host ""

# 执行安装步骤
try {
    # 安装 Chocolatey
    $chocoInstalled = Install-Chocolatey
    
    # 等待一下让 Chocolatey 生效
    Start-Sleep -Seconds 2
    
    # 安装核心工具
    Install-CoreTools
    
    # 安装 Python 工具
    Install-PythonTools
    
    # 验证安装结果
    Test-Installations
    
} catch {
    Write-Host "安装过程中出现错误: $_"
}

Write-Host ""
Write-Host "========================================"
Write-Host "安装脚本执行完成"
Write-Host "请检查以上输出，确认工具安装状态"
Write-Host "========================================"