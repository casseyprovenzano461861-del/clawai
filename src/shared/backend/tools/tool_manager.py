# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
工具管理器 - 第二阶段：工具集成优化
支持工具自动化安装、状态监控和优先级管理
"""

import os
import sys
import json
import platform
import subprocess
import shutil
import time
import requests
import zipfile
import tarfile
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具类别"""
    CRITICAL = "critical"    # 核心工具，必须安装
    ESSENTIAL = "essential"  # 重要工具，推荐安装
    ADVANCED = "advanced"    # 高级工具，可选安装
    OPTIONAL = "optional"    # 可选工具


class InstallPriority(Enum):
    """安装优先级"""
    LEVEL1 = 1  # 最高优先级，核心工具
    LEVEL2 = 2  # 高优先级，重要工具
    LEVEL3 = 3  # 中等优先级
    LEVEL4 = 4  # 低优先级


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


@dataclass
class ToolStatus:
    """工具状态"""
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    health: str = "unknown"  # healthy, warning, error
    last_check: float = field(default_factory=time.time)
    installation_method: Optional[str] = None


@dataclass
class ToolInstallation:
    """工具安装信息"""
    success: bool
    tool_name: str
    method: str
    output: str
    duration: float
    error: Optional[str] = None
    installed_version: Optional[str] = None


class ToolManager:
    """
    工具管理器
    支持工具自动化安装、状态监控和优先级管理
    """
    
    def __init__(self, config_file: str = None):
        self.tool_registry: Dict[str, Any] = {}
        self.tool_status: Dict[str, ToolStatus] = {}
        self.os_platform = self._detect_os()
        
        # 加载工具配置
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
        else:
            self._load_default_config()
        
        # 初始化工具状态
        self._init_tool_status()
    
    def _detect_os(self) -> OSPlatform:
        """检测操作系统"""
        system = platform.system().lower()
        if system == "windows":
            return OSPlatform.WINDOWS
        elif system == "linux":
            return OSPlatform.LINUX
        elif system == "darwin":
            return OSPlatform.MACOS
        else:
            logger.warning(f"未知操作系统: {system}")
            return OSPlatform.LINUX  # 默认Linux
    
    def _load_default_config(self):
        """加载默认工具配置"""
        self.tool_registry = {
            # ========== 核心工具 (CRITICAL) ==========
            "nmap": {
                "category": ToolCategory.CRITICAL.value,
                "priority": InstallPriority.LEVEL1.value,
                "description": "网络发现和安全审计工具",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.CHOCO.value,
                        "command": "choco install nmap -y",
                        "url": "https://nmap.org/dist/nmap-7.95-setup.exe",
                        "manual_guide": "从 https://nmap.org/download.html 下载安装"
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
                "version_pattern": r"Nmap version (\d+\.\d+(?:\.\d+)?)"
            },
            
            "whatweb": {
                "category": ToolCategory.CRITICAL.value,
                "priority": InstallPriority.LEVEL1.value,
                "description": "Web指纹识别工具",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.MANUAL.value,
                        "url": "https://github.com/urbanadventurer/WhatWeb/archive/refs/heads/master.zip",
                        "manual_guide": "下载WhatWeb源码并安装Ruby环境"
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
                "version_pattern": r"WhatWeb version (\d+\.\d+(?:\.\d+)?)"
            },
            
            # ========== 重要工具 (ESSENTIAL) ==========
            "nuclei": {
                "category": ToolCategory.ESSENTIAL.value,
                "priority": InstallPriority.LEVEL2.value,
                "description": "基于模板的漏洞扫描器",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.MANUAL.value,
                        "url": "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_2.10.2_windows_amd64.zip",
                        "manual_guide": "下载nuclei-windows.zip，解压并将nuclei.exe加入PATH"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.SCRIPT.value,
                        "command": "go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
                        "manual_guide": "需要Go语言环境: go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.BREW.value,
                        "command": "brew install nuclei",
                        "manual_guide": "brew install nuclei"
                    }
                },
                "test_command": ["nuclei", "-version"],
                "version_pattern": r"Current Version: (\d+\.\d+\.\d+)"
            },
            
            "sqlmap": {
                "category": ToolCategory.ESSENTIAL.value,
                "priority": InstallPriority.LEVEL2.value,
                "description": "SQL注入自动化利用工具",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.PIP.value,
                        "command": "pip install sqlmap",
                        "manual_guide": "pip install sqlmap 或从 https://github.com/sqlmapproject/sqlmap 下载"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.PIP.value,
                        "command": "pip install sqlmap",
                        "manual_guide": "pip install sqlmap"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.PIP.value,
                        "command": "pip install sqlmap",
                        "manual_guide": "pip install sqlmap"
                    }
                },
                "test_command": ["sqlmap", "--version"],
                "version_pattern": r"(\d+\.\d+(?:\.\d+)?)"
            },
            
            # ========== 高级工具 (ADVANCED) ==========
            "masscan": {
                "category": ToolCategory.ADVANCED.value,
                "priority": InstallPriority.LEVEL3.value,
                "description": "高速端口扫描器",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.MANUAL.value,
                        "url": "https://github.com/robertdavidgraham/masscan/releases/latest/download/masscan.exe",
                        "manual_guide": "下载masscan.exe并加入PATH"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.GIT.value,
                        "command": "git clone https://github.com/robertdavidgraham/masscan && cd masscan && make",
                        "manual_guide": "源码编译: git clone https://github.com/robertdavidgraham/masscan && cd masscan && make"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.BREW.value,
                        "command": "brew install masscan",
                        "manual_guide": "brew install masscan"
                    }
                },
                "test_command": ["masscan", "--version"],
                "version_pattern": r"Masscan version (\d+\.\d+(?:\.\d+)?)"
            },
            
            "dirsearch": {
                "category": ToolCategory.ADVANCED.value,
                "priority": InstallPriority.LEVEL3.value,
                "description": "目录和文件爆破工具",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.PIP.value,
                        "command": "pip install dirsearch",
                        "manual_guide": "pip install dirsearch"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.PIP.value,
                        "command": "pip install dirsearch",
                        "manual_guide": "pip install dirsearch"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.PIP.value,
                        "command": "pip install dirsearch",
                        "manual_guide": "pip install dirsearch"
                    }
                },
                "test_command": ["dirsearch", "--version"],
                "version_pattern": r"dirsearch v(\d+\.\d+(?:\.\d+)?)"
            },
            
            "httpx": {
                "category": ToolCategory.ADVANCED.value,
                "priority": InstallPriority.LEVEL3.value,
                "description": "HTTP探测与存活检测",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.MANUAL.value,
                        "url": "https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_1.3.8_windows_amd64.zip",
                        "manual_guide": "下载httpx-windows.zip，解压并将httpx.exe加入PATH"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.SCRIPT.value,
                        "command": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
                        "manual_guide": "需要Go语言环境: go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.BREW.value,
                        "command": "brew install httpx",
                        "manual_guide": "brew install httpx"
                    }
                },
                "test_command": ["httpx", "-version"],
                "version_pattern": r"Current Version: (\d+\.\d+\.\d+)"
            },
            
            # ========== 可选工具 (OPTIONAL) ==========
            "nikto": {
                "category": ToolCategory.OPTIONAL.value,
                "priority": InstallPriority.LEVEL4.value,
                "description": "Web服务器漏洞扫描器",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.MANUAL.value,
                        "url": "https://github.com/sullo/nikto/archive/refs/heads/master.zip",
                        "manual_guide": "需要Perl环境，下载nikto源码"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.APT.value,
                        "command": "sudo apt-get install nikto -y",
                        "manual_guide": "sudo apt-get install nikto"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.BREW.value,
                        "command": "brew install nikto",
                        "manual_guide": "brew install nikto"
                    }
                },
                "test_command": ["nikto", "-Version"],
                "version_pattern": r"Version (\d+\.\d+(?:\.\d+)?)"
            },
            
            "gobuster": {
                "category": ToolCategory.OPTIONAL.value,
                "priority": InstallPriority.LEVEL4.value,
                "description": "Go编写的目录爆破工具",
                "install_methods": {
                    OSPlatform.WINDOWS.value: {
                        "method": InstallMethod.MANUAL.value,
                        "url": "https://github.com/OJ/gobuster/releases/latest/download/gobuster-windows-amd64.exe",
                        "manual_guide": "下载gobuster.exe并加入PATH"
                    },
                    OSPlatform.LINUX.value: {
                        "method": InstallMethod.APT.value,
                        "command": "sudo apt-get install gobuster -y",
                        "manual_guide": "sudo apt-get install gobuster"
                    },
                    OSPlatform.MACOS.value: {
                        "method": InstallMethod.BREW.value,
                        "command": "brew install gobuster",
                        "manual_guide": "brew install gobuster"
                    }
                },
                "test_command": ["gobuster", "--version"],
                "version_pattern": r"gobuster/(\d+\.\d+(?:\.\d+)?)"
            }
        }
    
    def _load_config(self, config_file: str):
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 合并配置
            self.tool_registry.update(config_data.get("tools", {}))
            
            logger.info(f"从 {config_file} 加载了 {len(config_data.get('tools', {}))} 个工具配置")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self._load_default_config()
    
    def _init_tool_status(self):
        """初始化工具状态"""
        for tool_name in self.tool_registry.keys():
            self.tool_status[tool_name] = ToolStatus(installed=False)
    
    def check_tool_availability(self) -> Dict[str, Dict[str, Any]]:
        """检查所有工具的可用性"""
        results = {}
        
        for tool_name, tool_config in self.tool_registry.items():
            logger.info(f"检查工具: {tool_name}")
            status = self._check_tool(tool_name, tool_config)
            
            results[tool_name] = {
                "installed": status.installed,
                "version": status.version,
                "path": status.path,
                "health": status.health,
                "category": tool_config.get("category", "unknown"),
                "priority": tool_config.get("priority", 999),
                "description": tool_config.get("description", ""),
                "last_check": status.last_check
            }
        
        return results
    
    def _check_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> ToolStatus:
        """检查单个工具"""
        # 获取测试命令
        test_commands = tool_config.get("test_command", [tool_name, "--version"])
        
        # 尝试运行命令
        try:
            result = subprocess.run(
                test_commands,
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0 or result.returncode == 1:  # 很多工具用返回码1显示版本
                output = result.stdout or result.stderr
                
                # 查找工具路径
                tool_path = shutil.which(tool_name)
                
                # 提取版本号
                version = self._extract_version(output, tool_config.get("version_pattern"))
                
                return ToolStatus(
                    installed=True,
                    version=version,
                    path=tool_path,
                    health="healthy",
                    last_check=time.time()
                )
            else:
                return ToolStatus(
                    installed=False,
                    health="error",
                    last_check=time.time()
                )
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            return ToolStatus(
                installed=False,
                health="error" if isinstance(e, FileNotFoundError) else "warning",
                last_check=time.time()
            )
    
    def _extract_version(self, output: str, pattern: str = None) -> Optional[str]:
        """从输出中提取版本号"""
        if not output:
            return None
        
        import re
        
        # 如果没有指定模式，尝试常见模式
        if not pattern:
            patterns = [
                r'(\d+\.\d+\.\d+)',           # 1.2.3
                r'(\d+\.\d+)',                # 1.2
                r'v(\d+\.\d+\.\d+)',          # v1.2.3
                r'version\s+(\d+\.\d+\.\d+)', # version 1.2.3
                r'Version:\s+(\d+\.\d+\.\d+)' # Version: 1.2.3
            ]
        else:
            patterns = [pattern]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        # 如果没有匹配到，返回前20个字符
        return output[:20].strip()
    
    def get_installation_method(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的安装方法"""
        if tool_name not in self.tool_registry:
            logger.error(f"工具未注册: {tool_name}")
            return None
        
        tool_config = self.tool_registry[tool_name]
        os_key = self.os_platform.value
        
        install_methods = tool_config.get("install_methods", {})
        
        if os_key in install_methods:
            return install_methods[os_key]
        else:
            # 如果没有特定OS的配置，返回第一个
            for key, method in install_methods.items():
                return method
        
        return None
    
    def install_tool(self, tool_name: str, method: str = None) -> ToolInstallation:
        """安装工具"""
        start_time = time.time()
        
        if tool_name not in self.tool_registry:
            return ToolInstallation(
                success=False,
                tool_name=tool_name,
                method="unknown",
                output="",
                duration=time.time() - start_time,
                error=f"工具未注册: {tool_name}"
            )
        
        # 获取安装方法
        install_info = self.get_installation_method(tool_name)
        if not install_info:
            return ToolInstallation(
                success=False,
                tool_name=tool_name,
                method="unknown",
                output="",
                duration=time.time() - start_time,
                error="无可用安装方法"
            )
        
        # 如果指定了方法，使用指定方法
        if method:
            install_method = method
        else:
            install_method = install_info.get("method", InstallMethod.MANUAL.value)
        
        logger.info(f"安装工具 {tool_name}，方法: {install_method}")
        
        try:
            if install_method == InstallMethod.CHOCO.value:
                result = self._install_via_choco(install_info)
            elif install_method == InstallMethod.BREW.value:
                result = self._install_via_brew(install_info)
            elif install_method == InstallMethod.APT.value:
                result = self._install_via_apt(install_info)
            elif install_method == InstallMethod.YUM.value:
                result = self._install_via_yum(install_info)
            elif install_method == InstallMethod.PIP.value:
                result = self._install_via_pip(install_info)
            elif install_method == InstallMethod.GIT.value:
                result = self._install_via_git(install_info)
            elif install_method == InstallMethod.MANUAL.value:
                result = self._install_via_manual(tool_name, install_info)
            elif install_method == InstallMethod.SCRIPT.value:
                result = self._install_via_script(install_info)
            else:
                result = {
                    "success": False,
                    "output": f"不支持的安装方法: {install_method}",
                    "error": "不支持的安装方法"
                }
            
            duration = time.time() - start_time
            
            # 获取安装后的版本
            installed_version = None
            if result.get("success", False):
                # 重新检查工具状态
                tool_config = self.tool_registry[tool_name]
                status = self._check_tool(tool_name, tool_config)
                installed_version = status.version
            
            return ToolInstallation(
                success=result.get("success", False),
                tool_name=tool_name,
                method=install_method,
                output=result.get("output", ""),
                duration=duration,
                error=result.get("error"),
                installed_version=installed_version
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ToolInstallation(
                success=False,
                tool_name=tool_name,
                method=install_method,
                output="",
                duration=duration,
                error=f"安装异常: {str(e)}"
            )
    
    def _install_via_choco(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过Chocolatey安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无Chocolatey命令"}
        
        try:
            # 检查Chocolatey是否可用
            choco_check = subprocess.run(["choco", "--version"], 
                                       capture_output=True, text=True)
            if choco_check.returncode != 0:
                return {
                    "success": False, 
                    "error": "Chocolatey未安装",
                    "output": "请先安装Chocolatey: https://chocolatey.org/install"
                }
            
            # 执行安装
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _install_via_apt(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过APT安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无APT命令"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _install_via_pip(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过PIP安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无PIP命令"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _install_via_manual(self, tool_name: str, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """手动安装"""
        url = install_info.get("url", "")
        manual_guide = install_info.get("manual_guide", "")
        
        if url:
            # 尝试下载
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    # 保存文件
                    filename = url.split("/")[-1]
                    download_path = os.path.join(os.getcwd(), "downloads", filename)
                    os.makedirs(os.path.dirname(download_path), exist_ok=True)
                    
                    with open(download_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 如果是压缩文件，尝试解压
                    if filename.endswith('.zip'):
                        with zipfile.ZipFile(download_path, 'r') as zip_ref:
                            zip_ref.extractall(os.path.dirname(download_path))
                    
                    return {
                        "success": True,
                        "output": f"文件已下载: {download_path}\n请参考指南安装: {manual_guide}",
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "output": f"下载失败: HTTP {response.status_code}",
                        "error": "下载失败"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "output": f"下载异常: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "output": f"无下载URL，请手动安装\n指南: {manual_guide}",
                "error": "无下载URL"
            }
    
    def _install_via_git(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过Git源码安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无Git命令"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时（编译可能较慢）
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _install_via_script(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过脚本安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无脚本命令"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _install_via_brew(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过Homebrew安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无Homebrew命令"}
        
        try:
            # 检查Homebrew是否可用
            brew_check = subprocess.run(["brew", "--version"], 
                                      capture_output=True, text=True)
            if brew_check.returncode != 0:
                return {
                    "success": False, 
                    "error": "Homebrew未安装",
                    "output": "请先安装Homebrew: https://brew.sh/"
                }
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _install_via_yum(self, install_info: Dict[str, Any]) -> Dict[str, Any]:
        """通过YUM安装"""
        command = install_info.get("command", "")
        if not command:
            return {"success": False, "error": "无YUM命令"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "error": None if result.returncode == 0 else f"返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "安装超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def install_core_tools(self) -> Dict[str, ToolInstallation]:
        """安装核心工具"""
        core_tools = ["nmap", "whatweb", "nuclei", "sqlmap"]
        results = {}
        
        for tool_name in core_tools:
            logger.info(f"正在安装核心工具: {tool_name}")
            result = self.install_tool(tool_name)
            results[tool_name] = result
            
            if result.success:
                logger.info(f"✅ {tool_name} 安装成功")
            else:
                logger.warning(f"❌ {tool_name} 安装失败: {result.error}")
        
        return results
    
    def install_by_category(self, category: str) -> Dict[str, ToolInstallation]:
        """按类别安装工具"""
        results = {}
        
        for tool_name, tool_config in self.tool_registry.items():
            if tool_config.get("category") == category:
                logger.info(f"安装 {category} 类别工具: {tool_name}")
                result = self.install_tool(tool_name)
                results[tool_name] = result
        
        return results
    
    def install_by_priority(self, max_priority: int = 2) -> Dict[str, ToolInstallation]:
        """按优先级安装工具（优先级数字越小优先级越高）"""
        results = {}
        
        for tool_name, tool_config in self.tool_registry.items():
            priority = tool_config.get("priority", 999)
            if priority <= max_priority:
                logger.info(f"安装优先级 {priority} 工具: {tool_name}")
                result = self.install_tool(tool_name)
                results[tool_name] = result
        
        return results
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        availability = self.check_tool_availability()
        
        total_tools = len(availability)
        installed_tools = sum(1 for info in availability.values() if info["installed"])
        installation_rate = installed_tools / total_tools if total_tools > 0 else 0
        
        # 按类别统计
        category_stats = {}
        for tool_name, info in availability.items():
            category = info.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "installed": 0}
            
            category_stats[category]["total"] += 1
            if info["installed"]:
                category_stats[category]["installed"] += 1
        
        # 按优先级统计
        priority_stats = {}
        for tool_name, info in availability.items():
            priority = info.get("priority", 999)
            if priority not in priority_stats:
                priority_stats[priority] = {"total": 0, "installed": 0}
            
            priority_stats[priority]["total"] += 1
            if info["installed"]:
                priority_stats[priority]["installed"] += 1
        
        return {
            "total_tools": total_tools,
            "installed_tools": installed_tools,
            "installation_rate": round(installation_rate * 100, 1),
            "category_stats": category_stats,
            "priority_stats": priority_stats,
            "os_platform": self.os_platform.value,
            "timestamp": time.time()
        }
    
    def generate_installation_report(self) -> str:
        """生成安装报告"""
        stats = self.get_tool_statistics()
        availability = self.check_tool_availability()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ClawAI 工具安装报告")
        report_lines.append("=" * 80)
        report_lines.append(f"操作系统: {self.os_platform.value}")
        report_lines.append(f"报告时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 总体统计
        report_lines.append("总体统计:")
        report_lines.append(f"  总工具数: {stats['total_tools']}")
        report_lines.append(f"  已安装: {stats['installed_tools']}")
        report_lines.append(f"  安装率: {stats['installation_rate']}%")
        report_lines.append("")
        
        # 按类别统计
        report_lines.append("按类别统计:")
        for category, cat_stats in stats['category_stats'].items():
            installed = cat_stats['installed']
            total = cat_stats['total']
            rate = installed / total * 100 if total > 0 else 0
            report_lines.append(f"  {category}: {installed}/{total} ({rate:.1f}%)")
        report_lines.append("")
        
        # 工具详情
        report_lines.append("工具详情:")
        for tool_name, info in sorted(availability.items()):
            status = "✅" if info["installed"] else "❌"
            version = info["version"] or "未知"
            category = info["category"]
            priority = info["priority"]
            
            report_lines.append(f"  {status} {tool_name} (优先级: {priority}, 类别: {category})")
            if info["installed"]:
                report_lines.append(f"     版本: {version}, 路径: {info['path']}")
            else:
                report_lines.append(f"     未安装")
        report_lines.append("")
        
        # 建议
        if stats['installation_rate'] < 70:
            report_lines.append("建议:")
            report_lines.append(f"  ⚠ 当前安装率较低 ({stats['installation_rate']}%)")
            report_lines.append(f"  建议运行: manager.install_core_tools()")
            report_lines.append(f"  或: manager.install_by_priority(max_priority=2)")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


def test_tool_manager():
    """测试工具管理器"""
    print("=" * 80)
    print("工具管理器测试 - 第二阶段：工具集成优化")
    print("=" * 80)
    
    try:
        # 创建工具管理器
        manager = ToolManager()
        
        print(f"\n操作系统: {manager.os_platform.value}")
        print(f"已注册工具数: {len(manager.tool_registry)}")
        
        # 测试工具可用性检查
        print("\n1. 检查工具可用性:")
        availability = manager.check_tool_availability()
        
        installed_count = sum(1 for info in availability.values() if info["installed"])
        print(f"   已安装: {installed_count}/{len(availability)}")
        
        # 显示前几个工具状态
        for i, (tool_name, info) in enumerate(list(availability.items())[:5]):
            status = "✓" if info["installed"] else "✗"
            print(f"   {status} {tool_name}: {info['version'] or '未安装'}")
        
        if len(availability) > 5:
            print(f"   ... 还有 {len(availability)-5} 个工具")
        
        # 测试统计信息
        print("\n2. 工具统计信息:")
        stats = manager.get_tool_statistics()
        print(f"   总工具数: {stats['total_tools']}")
        print(f"   安装率: {stats['installation_rate']}%")
        
        # 测试安装方法查询
        print("\n3. 安装方法查询:")
        test_tools = ["nmap", "nuclei", "sqlmap"]
        for tool in test_tools:
            method = manager.get_installation_method(tool)
            if method:
                print(f"   {tool}: {method.get('method', 'unknown')}")
            else:
                print(f"   {tool}: 无可用安装方法")
        
        # 生成报告
        print("\n4. 生成安装报告:")
        report = manager.generate_installation_report()
        print(report[:500] + "..." if len(report) > 500 else report)
        
        print("\n" + "=" * 80)
        print("工具管理器测试完成")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_tool_manager()
    if success:
        print("\n[SUCCESS] 工具管理器测试通过!")
    else:
        print("\n[FAILED] 工具管理器测试失败!")