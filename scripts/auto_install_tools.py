# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 智能工具安装自动化脚本
跨平台支持：Windows、Linux、MacOS
按优先级分层安装核心安全工具
"""

import os
import sys
import platform
import subprocess
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import urllib.request
import zipfile
import tarfile
import tempfile

class ToolInstaller:
    """智能工具安装器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux"
        self.is_mac = self.system == "darwin"
        
        # 工具优先级定义
        self.tools_priority = {
            "P0": {  # 核心工具，必需，100%真实执行
                "nmap": {
                    "description": "端口扫描工具",
                    "check_command": ["nmap", "--version"],
                    "install_methods": {
                        "windows": self._install_nmap_windows,
                        "linux": self._install_nmap_linux,
                        "mac": self._install_nmap_mac
                    }
                },
                "whatweb": {
                    "description": "Web指纹识别工具",
                    "check_command": ["whatweb", "--version"],
                    "install_methods": {
                        "windows": self._install_whatweb_windows,
                        "linux": self._install_whatweb_linux,
                        "mac": self._install_whatweb_mac
                    }
                },
                "httpx": {
                    "description": "HTTP探测与存活检测",
                    "check_command": ["httpx", "--version"],
                    "install_methods": {
                        "windows": self._install_httpx_windows,
                        "linux": self._install_httpx_linux,
                        "mac": self._install_httpx_mac
                    }
                },
                "nuclei": {
                    "description": "漏洞扫描工具",
                    "check_command": ["nuclei", "--version"],
                    "install_methods": {
                        "windows": self._install_nuclei_windows,
                        "linux": self._install_nuclei_linux,
                        "mac": self._install_nuclei_mac
                    }
                }
            },
            "P1": {  # 重要工具，优先安装，90%真实执行
                "sqlmap": {
                    "description": "SQL注入检测工具",
                    "check_command": ["sqlmap", "--version"],
                    "install_methods": {
                        "windows": self._install_sqlmap_windows,
                        "linux": self._install_sqlmap_linux,
                        "mac": self._install_sqlmap_mac
                    }
                },
                "nikto": {
                    "description": "Web服务器漏洞扫描器",
                    "check_command": ["nikto", "--version"],
                    "install_methods": {
                        "windows": self._install_nikto_windows,
                        "linux": self._install_nikto_linux,
                        "mac": self._install_nikto_mac
                    }
                },
                "masscan": {
                    "description": "高速端口扫描器",
                    "check_command": ["masscan", "--version"],
                    "install_methods": {
                        "windows": self._install_masscan_windows,
                        "linux": self._install_masscan_linux,
                        "mac": self._install_masscan_mac
                    }
                }
            },
            "P2": {  # 辅助工具，推荐安装，70%真实执行
                "wafw00f": {
                    "description": "WAF检测工具",
                    "check_command": ["wafw00f", "--version"],
                    "install_methods": {
                        "windows": self._install_wafw00f_windows,
                        "linux": self._install_wafw00f_linux,
                        "mac": self._install_wafw00f_mac
                    }
                },
                "subfinder": {
                    "description": "子域名枚举工具",
                    "check_command": ["subfinder", "--version"],
                    "install_methods": {
                        "windows": self._install_subfinder_windows,
                        "linux": self._install_subfinder_linux,
                        "mac": self._install_subfinder_mac
                    }
                },
                "amass": {
                    "description": "深度子域名枚举工具",
                    "check_command": ["amass", "--version"],
                    "install_methods": {
                        "windows": self._install_amass_windows,
                        "linux": self._install_amass_linux,
                        "mac": self._install_amass_mac
                    }
                }
            }
        }
        
        # 安装统计
        self.installation_stats = {
            "total": 0,
            "installed": 0,
            "failed": 0,
            "skipped": 0,
            "details": {}
        }
    
    def check_tool_installed(self, tool_name: str, check_command: List[str]) -> bool:
        """检查工具是否已安装"""
        try:
            result = subprocess.run(
                check_command,
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )
            # 返回码为0或1通常表示命令可用
            is_available = result.returncode == 0 or result.returncode == 1
            if not is_available:
                # 尝试使用where/which命令
                if self.is_windows:
                    result = subprocess.run(
                        ["where", tool_name],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                else:
                    result = subprocess.run(
                        ["which", tool_name],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                is_available = result.returncode == 0
            
            return is_available
        except Exception:
            return False
    
    def run_command(self, command: List[str], description: str = "") -> Tuple[bool, str]:
        """执行命令并返回结果"""
        try:
            print(f"  [执行] 执行: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                return True, "成功"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"失败 (返回码: {result.returncode}): {error_msg[:200]}"
        except subprocess.TimeoutExpired:
            return False, "超时"
        except Exception as e:
            return False, f"异常: {str(e)}"
    
    def download_file(self, url: str, dest_path: str) -> bool:
        """下载文件"""
        try:
            print(f"  [下载] 下载: {url}")
            with urllib.request.urlopen(url) as response:
                with open(dest_path, 'wb') as f:
                    f.write(response.read())
            return True
        except Exception as e:
            print(f"  [失败] 下载失败: {e}")
            return False
    
    def extract_archive(self, archive_path: str, extract_dir: str) -> bool:
        """解压归档文件"""
        try:
            print(f"  [文件] 解压: {archive_path}")
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)
            elif archive_path.endswith('.tar'):
                with tarfile.open(archive_path, 'r:') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                print(f"  [警告]  不支持的文件格式: {archive_path}")
                return False
            return True
        except Exception as e:
            print(f"  [失败] 解压失败: {e}")
            return False
    
    # ========== 平台特定的安装方法 ==========
    
    # Nmap 安装方法
    def _install_nmap_windows(self) -> Tuple[bool, str]:
        """Windows安装nmap"""
        # 方法1: 使用chocolatey
        success, msg = self.run_command(
            ["choco", "install", "nmap", "-y"],
            "通过Chocolatey安装nmap"
        )
        if success:
            return True, "通过Chocolatey安装成功"
        
        # 方法2: 下载安装包
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "nmap-setup.exe")
        
        if self.download_file("https://nmap.org/dist/nmap-7.94-setup.exe", installer_path):
            success, msg = self.run_command(
                [installer_path, "/S"],
                "运行nmap安装程序"
            )
            if success:
                return True, "安装包安装成功"
        
        return False, "所有安装方法都失败"
    
    def _install_nmap_linux(self) -> Tuple[bool, str]:
        """Linux安装nmap"""
        if shutil.which("apt-get"):
            return self.run_command(["sudo", "apt-get", "update", "-y"], "更新包列表")
            return self.run_command(["sudo", "apt-get", "install", "nmap", "-y"], "安装nmap")
        elif shutil.which("yum"):
            return self.run_command(["sudo", "yum", "install", "nmap", "-y"], "安装nmap")
        elif shutil.which("dnf"):
            return self.run_command(["sudo", "dnf", "install", "nmap", "-y"], "安装nmap")
        else:
            return False, "不支持的包管理器"
    
    def _install_nmap_mac(self) -> Tuple[bool, str]:
        """Mac安装nmap"""
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "nmap"], "通过Homebrew安装nmap")
        else:
            return False, "请先安装Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    
    # WhatWeb 安装方法
    def _install_whatweb_windows(self) -> Tuple[bool, str]:
        """Windows安装whatweb"""
        # WhatWeb是Ruby工具，需要先安装Ruby
        if not shutil.which("ruby"):
            # 安装Ruby
            success, msg = self.run_command(
                ["choco", "install", "ruby", "-y"],
                "安装Ruby"
            )
            if not success:
                return False, f"Ruby安装失败: {msg}"
        
        # 安装WhatWeb
        return self.run_command(
            ["gem", "install", "whatweb"],
            "通过gem安装whatweb"
        )
    
    def _install_whatweb_linux(self) -> Tuple[bool, str]:
        """Linux安装whatweb"""
        if shutil.which("apt-get"):
            return self.run_command(["sudo", "apt-get", "install", "whatweb", "-y"], "安装whatweb")
        elif shutil.which("git"):
            # 从源码安装
            clone_dir = os.path.join(tempfile.gettempdir(), "whatweb")
            success, msg = self.run_command(
                ["git", "clone", "https://github.com/urbanadventurer/WhatWeb.git", clone_dir],
                "克隆WhatWeb仓库"
            )
            if success:
                # 添加到PATH
                whatweb_path = os.path.join(clone_dir, "whatweb")
                if os.path.exists(whatweb_path):
                    # 创建符号链接或复制到/usr/local/bin
                    try:
                        subprocess.run(["sudo", "cp", whatweb_path, "/usr/local/bin/whatweb"], check=True)
                        subprocess.run(["sudo", "chmod", "+x", "/usr/local/bin/whatweb"], check=True)
                        return True, "从源码安装成功"
                    except Exception as e:
                        return False, f"安装失败: {e}"
            return False, msg
        else:
            return False, "不支持的系统"
    
    def _install_whatweb_mac(self) -> Tuple[bool, str]:
        """Mac安装whatweb"""
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "whatweb"], "通过Homebrew安装whatweb")
        else:
            return False, "请先安装Homebrew"
    
    # HTTPX 安装方法
    def _install_httpx_windows(self) -> Tuple[bool, str]:
        """Windows安装httpx"""
        # Go工具，下载预编译二进制
        temp_dir = tempfile.gettempdir()
        binary_path = os.path.join(temp_dir, "httpx.exe")
        
        if self.download_file("https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_1.3.4_windows_amd64.zip", 
                            binary_path + ".zip"):
            if self.extract_archive(binary_path + ".zip", temp_dir):
                # 复制到系统目录
                extracted_exe = None
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower() == "httpx.exe":
                            extracted_exe = os.path.join(root, file)
                            break
                
                if extracted_exe and os.path.exists(extracted_exe):
                    system_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
                    dest_path = os.path.join(system_dir, "httpx.exe")
                    try:
                        shutil.copy2(extracted_exe, dest_path)
                        return True, "安装成功"
                    except Exception as e:
                        # 尝试复制到当前目录
                        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        dest_path = os.path.join(project_dir, "httpx.exe")
                        try:
                            shutil.copy2(extracted_exe, dest_path)
                            return True, "安装到项目目录成功"
                        except Exception as e2:
                            return False, f"复制失败: {e2}"
        
        return False, "安装失败"
    
    def _install_httpx_linux(self) -> Tuple[bool, str]:
        """Linux安装httpx"""
        return self.run_command(
            ["go", "install", "-v", "github.com/projectdiscovery/httpx/cmd/httpx@latest"],
            "通过go install安装httpx"
        )
    
    def _install_httpx_mac(self) -> Tuple[bool, str]:
        """Mac安装httpx"""
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "httpx"], "通过Homebrew安装httpx")
        else:
            return self._install_httpx_linux()
    
    # Nuclei 安装方法
    def _install_nuclei_windows(self) -> Tuple[bool, str]:
        """Windows安装nuclei"""
        # 使用go安装
        if shutil.which("go"):
            return self.run_command(
                ["go", "install", "-v", "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"],
                "通过go install安装nuclei"
            )
        
        # 下载预编译二进制
        temp_dir = tempfile.gettempdir()
        binary_path = os.path.join(temp_dir, "nuclei.exe")
        
        if self.download_file("https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_3.0.0_windows_amd64.zip", 
                            binary_path + ".zip"):
            if self.extract_archive(binary_path + ".zip", temp_dir):
                # 查找并复制nuclei.exe
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower() == "nuclei.exe":
                            extracted_exe = os.path.join(root, file)
                            system_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
                            dest_path = os.path.join(system_dir, "nuclei.exe")
                            try:
                                shutil.copy2(extracted_exe, dest_path)
                                return True, "安装成功"
                            except Exception:
                                # 复制到项目目录
                                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                dest_path = os.path.join(project_dir, "nuclei.exe")
                                try:
                                    shutil.copy2(extracted_exe, dest_path)
                                    return True, "安装到项目目录成功"
                                except Exception as e:
                                    return False, f"复制失败: {e}"
        
        return False, "安装失败"
    
    def _install_nuclei_linux(self) -> Tuple[bool, str]:
        """Linux安装nuclei"""
        return self.run_command(
            ["go", "install", "-v", "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"],
            "通过go install安装nuclei"
        )
    
    def _install_nuclei_mac(self) -> Tuple[bool, str]:
        """Mac安装nuclei"""
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "nuclei"], "通过Homebrew安装nuclei")
        else:
            return self._install_nuclei_linux()
    
    # 其他工具的安装方法（简化实现）
    def _install_sqlmap_windows(self) -> Tuple[bool, str]:
        return self.run_command(["pip", "install", "sqlmap"], "通过pip安装sqlmap")
    
    def _install_sqlmap_linux(self) -> Tuple[bool, str]:
        return self.run_command(["pip3", "install", "sqlmap"], "通过pip3安装sqlmap")
    
    def _install_sqlmap_mac(self) -> Tuple[bool, str]:
        return self.run_command(["pip3", "install", "sqlmap"], "通过pip3安装sqlmap")
    
    def _install_nikto_windows(self) -> Tuple[bool, str]:
        # Nikto是Perl脚本，需要Perl环境
        if not shutil.which("perl"):
            success, msg = self.run_command(["choco", "install", "strawberryperl", "-y"], "安装Perl")
            if not success:
                return False, f"Perl安装失败: {msg}"
        
        # 下载Nikto
        temp_dir = tempfile.gettempdir()
        nikto_dir = os.path.join(temp_dir, "nikto")
        os.makedirs(nikto_dir, exist_ok=True)
        
        if self.download_file("https://github.com/sullo/nikto/archive/master.zip", os.path.join(nikto_dir, "nikto.zip")):
            if self.extract_archive(os.path.join(nikto_dir, "nikto.zip"), nikto_dir):
                # 查找nikto.pl
                for root, dirs, files in os.walk(nikto_dir):
                    for file in files:
                        if file == "nikto.pl":
                            nikto_pl = os.path.join(root, file)
                            # 复制到系统目录
                            system_dir = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
                            dest_path = os.path.join(system_dir, "nikto.pl")
                            try:
                                shutil.copy2(nikto_pl, dest_path)
                                # 创建批处理文件
                                bat_path = os.path.join(system_dir, "nikto.bat")
                                with open(bat_path, 'w') as f:
                                    f.write('@echo off\n')
                                    f.write(f'perl "{dest_path}" %*\n')
                                return True, "安装成功"
                            except Exception as e:
                                return False, f"复制失败: {e}"
        
        return False, "安装失败"
    
    def _install_nikto_linux(self) -> Tuple[bool, str]:
        if shutil.which("apt-get"):
            return self.run_command(["sudo", "apt-get", "install", "nikto", "-y"], "安装nikto")
        elif shutil.which("git"):
            return self.run_command(
                ["git", "clone", "https://github.com/sullo/nikto.git", "/tmp/nikto"],
                "克隆nikto仓库"
            )
        return False, "不支持的系统"
    
    def _install_nikto_mac(self) -> Tuple[bool, str]:
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "nikto"], "通过Homebrew安装nikto")
        return False, "请先安装Homebrew"
    
    # 简化其他安装方法
    def _install_masscan_windows(self) -> Tuple[bool, str]:
        return self.run_command(["choco", "install", "masscan", "-y"], "通过Chocolatey安装masscan")
    
    def _install_masscan_linux(self) -> Tuple[bool, str]:
        if shutil.which("apt-get"):
            return self.run_command(["sudo", "apt-get", "install", "masscan", "-y"], "安装masscan")
        return False, "不支持的包管理器"
    
    def _install_masscan_mac(self) -> Tuple[bool, str]:
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "masscan"], "通过Homebrew安装masscan")
        return False, "请先安装Homebrew"
    
    def _install_wafw00f_windows(self) -> Tuple[bool, str]:
        return self.run_command(["pip", "install", "wafw00f"], "通过pip安装wafw00f")
    
    def _install_wafw00f_linux(self) -> Tuple[bool, str]:
        return self.run_command(["pip3", "install", "wafw00f"], "通过pip3安装wafw00f")
    
    def _install_wafw00f_mac(self) -> Tuple[bool, str]:
        return self.run_command(["pip3", "install", "wafw00f"], "通过pip3安装wafw00f")
    
    def _install_subfinder_windows(self) -> Tuple[bool, str]:
        if shutil.which("go"):
            return self.run_command(
                ["go", "install", "-v", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"],
                "通过go install安装subfinder"
            )
        return False, "需要安装Go"
    
    def _install_subfinder_linux(self) -> Tuple[bool, str]:
        return self.run_command(
            ["go", "install", "-v", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"],
            "通过go install安装subfinder"
        )
    
    def _install_subfinder_mac(self) -> Tuple[bool, str]:
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "subfinder"], "通过Homebrew安装subfinder")
        return self._install_subfinder_linux()
    
    def _install_amass_windows(self) -> Tuple[bool, str]:
        if shutil.which("go"):
            return self.run_command(
                ["go", "install", "-v", "github.com/owasp-amass/amass/v4@master"],
                "通过go install安装amass"
            )
        return False, "需要安装Go"
    
    def _install_amass_linux(self) -> Tuple[bool, str]:
        return self.run_command(
            ["go", "install", "-v", "github.com/owasp-amass/amass/v4@master"],
            "通过go install安装amass"
        )
    
    def _install_amass_mac(self) -> Tuple[bool, str]:
        if shutil.which("brew"):
            return self.run_command(["brew", "install", "amass"], "通过Homebrew安装amass")
        return self._install_amass_linux()
    
    # ========== 主安装逻辑 ==========
    
    def install_tool(self, tool_name: str, tool_info: Dict) -> Tuple[bool, str, str]:
        """安装单个工具"""
        print(f"\n[工具] 处理工具: {tool_name} ({tool_info['description']})")
        
        # 检查是否已安装
        if self.check_tool_installed(tool_name, tool_info["check_command"]):
            print(f"  [成功] {tool_name} 已安装")
            return True, "已安装", "skipped"
        
        # 获取安装方法
        system_key = "windows" if self.is_windows else "mac" if self.is_mac else "linux"
        install_methods = tool_info["install_methods"]
        
        if system_key not in install_methods:
            print(f"  [警告]  不支持的系统: {system_key}")
            return False, f"不支持的系统: {system_key}", "failed"
        
        install_method = install_methods[system_key]
        
        try:
            print(f"  [安装] 开始安装 {tool_name}...")
            success, message = install_method()
            
            if success:
                print(f"  [成功] {tool_name} 安装成功")
                # 验证安装
                if self.check_tool_installed(tool_name, tool_info["check_command"]):
                    return True, f"安装成功: {message}", "installed"
                else:
                    print(f"  [警告]  安装后验证失败，但安装过程成功")
                    return True, f"安装完成但验证失败: {message}", "installed_with_warning"
            else:
                print(f"  [失败] {tool_name} 安装失败: {message}")
                return False, f"安装失败: {message}", "failed"
                
        except Exception as e:
            error_msg = f"安装异常: {str(e)}"
            print(f"  [失败] {tool_name} 安装异常: {error_msg}")
            return False, error_msg, "failed"
    
    def install_all_tools(self, priority_levels: List[str] = None) -> Dict:
        """安装所有指定优先级的工具"""
        if priority_levels is None:
            priority_levels = ["P0", "P1", "P2"]
        
        print("=" * 80)
        print("ClawAI 智能工具安装器")
        print("=" * 80)
        print(f"系统检测: {platform.system()} {platform.release()}")
        print(f"Python版本: {platform.python_version()}")
        print("=" * 80)
        
        for priority in priority_levels:
            if priority not in self.tools_priority:
                continue
                
            tools = self.tools_priority[priority]
            print(f"\n{'='*60}")
            print(f"优先级 {priority} 工具安装")
            print(f"{'='*60}")
            
            for tool_name, tool_info in tools.items():
                self.installation_stats["total"] += 1
                
                success, message, status = self.install_tool(tool_name, tool_info)
                
                self.installation_stats["details"][tool_name] = {
                    "success": success,
                    "message": message,
                    "status": status,
                    "priority": priority,
                    "description": tool_info["description"]
                }
                
                if success:
                    self.installation_stats["installed"] += 1
                elif status == "skipped":
                    self.installation_stats["skipped"] += 1
                else:
                    self.installation_stats["failed"] += 1
        
        return self.installation_stats
    
    def generate_report(self) -> Dict:
        """生成安装报告"""
        total = self.installation_stats["total"]
        installed = self.installation_stats["installed"]
        failed = self.installation_stats["failed"]
        skipped = self.installation_stats["skipped"]
        
        if total > 0:
            success_rate = (installed / total) * 100
        else:
            success_rate = 0
        
        report = {
            "summary": {
                "total_tools": total,
                "installed": installed,
                "failed": failed,
                "skipped": skipped,
                "success_rate": success_rate,
                "system": platform.system(),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "details": self.installation_stats["details"],
            "recommendations": []
        }
        
        # 生成建议
        if failed > 0:
            failed_tools = []
            for tool_name, detail in self.installation_stats["details"].items():
                if not detail["success"] and detail["status"] != "skipped":
                    failed_tools.append(f"{tool_name}: {detail['message']}")
            
            if failed_tools:
                report["recommendations"].append({
                    "type": "manual_installation",
                    "tools": failed_tools,
                    "suggestion": "请手动安装以上工具，或检查网络连接和权限"
                })
        
        # P0工具安装状态检查
        p0_tools = []
        for tool_name in self.tools_priority["P0"].keys():
            if tool_name in self.installation_stats["details"]:
                detail = self.installation_stats["details"][tool_name]
                if not detail["success"] or detail["status"] == "failed":
                    p0_tools.append(tool_name)
        
        if p0_tools:
            report["recommendations"].append({
                "type": "critical_tools",
                "tools": p0_tools,
                "suggestion": "P0核心工具安装失败，将影响真实执行能力，请优先解决"
            })
        
        return report
    
    def save_report(self, report: Dict, filepath: str = None):
        """保存安装报告"""
        if filepath is None:
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(reports_dir, f"tool_installation_report_{timestamp}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[文档] 报告已保存: {filepath}")
        return filepath

def main():
    """主函数"""
    try:
        installer = ToolInstaller()
        
        # 安装所有工具（按优先级）
        print("开始安装工具...")
        stats = installer.install_all_tools()
        
        # 生成报告
        print("\n" + "=" * 80)
        print("安装完成!")
        print("=" * 80)
        
        report = installer.generate_report()
        
        # 显示摘要
        summary = report["summary"]
        print(f"\n[统计] 安装摘要:")
        print(f"  总工具数: {summary['total_tools']}")
        print(f"  已安装/跳过: {summary['installed'] + summary['skipped']}")
        print(f"  失败: {summary['failed']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        
        if summary['failed'] > 0:
            print(f"\n[警告]  有 {summary['failed']} 个工具安装失败:")
            for tool_name, detail in report["details"].items():
                if not detail["success"] and detail["status"] != "skipped":
                    print(f"  [失败] {tool_name}: {detail['message']}")
        
        # 保存报告
        report_file = installer.save_report(report)
        
        print(f"\n[成功] 安装过程完成!")
        print(f"[列表] 详细报告: {report_file}")
        
        # 检查P0核心工具状态
        p0_installed = 0
        p0_total = len(installer.tools_priority["P0"])
        
        for tool_name in installer.tools_priority["P0"].keys():
            if tool_name in report["details"]:
                detail = report["details"][tool_name]
                if detail["success"] or detail["status"] == "skipped":
                    p0_installed += 1
        
        print(f"\n[目标] P0核心工具安装状态: {p0_installed}/{p0_total}")
        if p0_installed < p0_total:
            print("[警告]  建议安装所有P0核心工具以获得最佳真实执行能力")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[中断]  安装被用户中断")
        return 1
    except Exception as e:
        print(f"\n[失败] 安装过程发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())