# -*- coding: utf-8 -*-
"""
核心工具保证 - 第二阶段：真实工具集成
技术诚信重建：只列出真正能安装的工具
"""

from enum import Enum
from typing import Dict, List, Any


class ToolPriority(Enum):
    """工具优先级"""
    CRITICAL = "critical"    # 必须安装的核心工具
    ESSENTIAL = "essential"  # 重要工具，推荐安装
    ADVANCED = "advanced"    # 高级工具，可选安装
    OPTIONAL = "optional"    # 可选工具


class OSPlatform(Enum):
    """操作系统平台"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "mac"


class InstallMethod(Enum):
    """安装方法"""
    CHOCO = "choco"      # Chocolatey (Windows)
    BREW = "brew"        # Homebrew (macOS)
    APT = "apt"          # APT (Debian/Ubuntu)
    YUM = "yum"          # YUM (RHEL/CentOS)
    PIP = "pip"          # Python PIP
    GIT = "git"          # Git 源码编译
    MANUAL = "manual"    # 手动下载
    SCRIPT = "script"    # 安装脚本


# 核心工具配置
ESSENTIAL_TOOLS = {
    # ========== 必须安装的核心工具 ==========
    "nmap": {
        "priority": ToolPriority.CRITICAL.value,
        "min_version": "7.80",
        "description": "网络发现和安全审计工具",
        "installation": {
            OSPlatform.WINDOWS.value: {
                "method": InstallMethod.CHOCO.value,
                "command": "choco install nmap -y",
                "manual_url": "https://nmap.org/download.html",
                "download_url": "https://nmap.org/dist/nmap-7.95-setup.exe",
                "instructions": "1. 下载安装包\n2. 运行安装程序\n3. 确保nmap.exe在PATH中"
            },
            OSPlatform.LINUX.value: {
                "method": InstallMethod.APT.value,
                "command": "sudo apt-get install nmap -y",
                "manual_guide": "sudo apt-get install nmap"
            },
            OSPlatform.MACOS.value: {
                "method": InstallMethod.BREW.value,
                "command": "brew install nmap",
                "manual_guide": "brew install nmap"
            }
        },
        "test_command": ["nmap", "--version"],
        "test_args": ["--version"],
        "version_pattern": r"Nmap version (\d+\.\d+(?:\.\d+)?)",
        "required": True,
        "health_check_interval": 86400,  # 24小时检查一次
        "fallback_tools": ["masscan", "rustscan"]
    },
    
    "whatweb": {
        "priority": ToolPriority.CRITICAL.value,
        "description": "Web指纹识别工具",
        "installation": {
            OSPlatform.WINDOWS.value: {
                "method": InstallMethod.MANUAL.value,
                "download_url": "https://github.com/urbanadventurer/WhatWeb/archive/refs/heads/master.zip",
                "instructions": "1. 下载源码\n2. 安装Ruby环境\n3. 运行bundle install\n4. 添加whatweb到PATH",
                "dependencies": ["ruby", "bundler"],
                "manual_guide": "需要Ruby环境，详细步骤参考GitHub README"
            },
            OSPlatform.LINUX.value: {
                "method": InstallMethod.APT.value,
                "command": "sudo apt-get install whatweb -y",
                "manual_guide": "sudo apt-get install whatweb"
            },
            OSPlatform.MACOS.value: {
                "method": InstallMethod.BREW.value,
                "command": "brew install whatweb",
                "manual_guide": "brew install whatweb"
            }
        },
        "test_command": ["whatweb", "--version"],
        "test_args": ["--version"],
        "version_pattern": r"WhatWeb version (\d+\.\d+(?:\.\d+)?)",
        "required": True,
        "health_check_interval": 86400,
        "fallback_tools": ["wappalyzer-cli", "builtwith"]
    },
    
    # ========== 推荐安装的重要工具 ==========
    "nuclei": {
        "priority": ToolPriority.ESSENTIAL.value,
        "min_version": "2.9.0",
        "description": "基于模板的漏洞扫描器",
        "installation": {
            OSPlatform.WINDOWS.value: {
                "method": InstallMethod.MANUAL.value,
                "download_url": "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_2.10.2_windows_amd64.zip",
                "instructions": "1. 下载nuclei-windows.zip\n2. 解压到tools/nuclei目录\n3. 将nuclei.exe加入PATH",
                "manual_guide": "下载预编译二进制文件并添加到PATH"
            },
            OSPlatform.LINUX.value: {
                "method": InstallMethod.SCRIPT.value,
                "command": "go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
                "dependencies": ["go"],
                "manual_guide": "需要Go语言环境: go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
            },
            OSPlatform.MACOS.value: {
                "method": InstallMethod.BREW.value,
                "command": "brew install nuclei",
                "manual_guide": "brew install nuclei"
            }
        },
        "test_command": ["nuclei", "-version"],
        "test_args": ["-version"],
        "version_pattern": r"Current Version: (\d+\.\d+\.\d+)",
        "required": False,
        "health_check_interval": 172800,  # 48小时
        "fallback_tools": ["nikto", "nikto2"]
    },
    
    "sqlmap": {
        "priority": ToolPriority.ESSENTIAL.value,
        "description": "SQL注入自动化利用工具",
        "installation": {
            OSPlatform.WINDOWS.value: {
                "method": InstallMethod.PIP.value,
                "command": "pip install sqlmap",
                "dependencies": ["python", "pip"],
                "manual_guide": "pip install sqlmap 或从 https://github.com/sqlmapproject/sqlmap 下载源码"
            },
            OSPlatform.LINUX.value: {
                "method": InstallMethod.PIP.value,
                "command": "pip install sqlmap",
                "dependencies": ["python3", "pip3"],
                "manual_guide": "pip install sqlmap"
            },
            OSPlatform.MACOS.value: {
                "method": InstallMethod.PIP.value,
                "command": "pip install sqlmap",
                "dependencies": ["python3", "pip3"],
                "manual_guide": "pip install sqlmap"
            }
        },
        "test_command": ["sqlmap", "--version"],
        "test_args": ["--version"],
        "version_pattern": r"(\d+\.\d+(?:\.\d+)?)",
        "required": False,
        "health_check_interval": 172800,
        "fallback_tools": ["nosqlmap", "jsql"]
    },
    
    # ========== 可选的高级工具 ==========
    "httpx": {
        "priority": ToolPriority.ADVANCED.value,
        "description": "HTTP探测与存活检测",
        "installation": {
            OSPlatform.WINDOWS.value: {
                "method": InstallMethod.MANUAL.value,
                "download_url": "https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_1.3.8_windows_amd64.zip",
                "instructions": "1. 下载httpx-windows.zip\n2. 解压\n3. 将httpx.exe加入PATH"
            },
            OSPlatform.LINUX.value: {
                "method": InstallMethod.SCRIPT.value,
                "command": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
                "dependencies": ["go"],
                "manual_guide": "需要Go语言环境"
            },
            OSPlatform.MACOS.value: {
                "method": InstallMethod.BREW.value,
                "command": "brew install httpx",
                "manual_guide": "brew install httpx"
            }
        },
        "test_command": ["httpx", "-version"],
        "test_args": ["-version"],
        "version_pattern": r"Current Version: (\d+\.\d+\.\d+)",
        "required": False,
        "health_check_interval": 259200  # 72小时
    },
    
    "dirsearch": {
        "priority": ToolPriority.ADVANCED.value,
        "description": "目录和文件爆破工具",
        "installation": {
            OSPlatform.WINDOWS.value: {
                "method": InstallMethod.PIP.value,
                "command": "pip install dirsearch",
                "dependencies": ["python", "pip"],
                "manual_guide": "pip install dirsearch"
            },
            OSPlatform.LINUX.value: {
                "method": InstallMethod.PIP.value,
                "command": "pip install dirsearch",
                "dependencies": ["python3", "pip3"],
                "manual_guide": "pip install dirsearch"
            },
            OSPlatform.MACOS.value: {
                "method": InstallMethod.PIP.value,
                "command": "pip install dirsearch",
                "dependencies": ["python3", "pip3"],
                "manual_guide": "pip install dirsearch"
            }
        },
        "test_command": ["dirsearch", "--version"],
        "test_args": ["--version"],
        "version_pattern": r"dirsearch v(\d+\.\d+(?:\.\d+)?)",
        "required": False,
        "health_check_interval": 259200
    }
}


def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """获取工具配置"""
    if tool_name not in ESSENTIAL_TOOLS:
        raise ValueError(f"工具未配置: {tool_name}")
    
    return ESSENTIAL_TOOLS[tool_name]


def get_critical_tools() -> List[str]:
    """获取必须安装的核心工具列表"""
    return [tool for tool, config in ESSENTIAL_TOOLS.items() 
            if config.get("required", False)]


def get_tools_by_priority(priority: str) -> List[str]:
    """按优先级获取工具列表"""
    return [tool for tool, config in ESSENTIAL_TOOLS.items() 
            if config.get("priority") == priority]


def get_all_tools() -> List[str]:
    """获取所有配置的工具"""
    return list(ESSENTIAL_TOOLS.keys())


def get_installation_info(tool_name: str, platform: str) -> Dict[str, Any]:
    """获取工具的安装信息"""
    if tool_name not in ESSENTIAL_TOOLS:
        return {}
    
    tool_config = ESSENTIAL_TOOLS[tool_name]
    installation = tool_config.get("installation", {})
    
    if platform in installation:
        return installation[platform]
    else:
        # 返回第一个可用的安装方法
        for os_key, info in installation.items():
            return info
    
    return {}


def print_tool_status():
    """打印工具状态概览"""
    print("=" * 80)
    print("ClawAI 核心工具配置")
    print("=" * 80)
    
    critical_count = len(get_critical_tools())
    essential_count = len(get_tools_by_priority(ToolPriority.ESSENTIAL.value))
    advanced_count = len(get_tools_by_priority(ToolPriority.ADVANCED.value))
    
    print(f"总工具数: {len(ESSENTIAL_TOOLS)}")
    print(f"必须安装: {critical_count}")
    print(f"推荐安装: {essential_count}")
    print(f"高级工具: {advanced_count}")
    
    print("\n工具列表:")
    for tool_name, config in ESSENTIAL_TOOLS.items():
        priority = config.get("priority", "unknown")
        required = "✓" if config.get("required", False) else " "
        description = config.get("description", "")
        
        print(f"  [{priority}] {required} {tool_name}: {description}")
    
    print("\n技术诚信声明:")
    print("  1. 只列出真正能安装的工具")
    print("  2. 明确标注必须安装和可选工具")
    print("  3. 提供真实的安装指南和下载链接")
    print("  4. 诚实地告知工具依赖和要求")
    
    print("=" * 80)


if __name__ == "__main__":
    print_tool_status()
    
    # 测试功能
    print("\n功能测试:")
    print(f"核心工具: {get_critical_tools()}")
    print(f"所有工具: {get_all_tools()}")
    
    # 测试获取安装信息
    test_tool = "nmap"
    if test_tool in ESSENTIAL_TOOLS:
        install_info = get_installation_info(test_tool, "windows")
        print(f"\n{test_tool} Windows安装方法: {install_info.get('method', 'unknown')}")