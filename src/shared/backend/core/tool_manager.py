# -*- coding: utf-8 -*-
"""
ToolManager模块 - 工具管理器
负责安全工具的执行和管理
"""

import subprocess
import concurrent.futures
import os
import yaml
from typing import List, Optional, Dict, Any


class ToolManager:
    """工具管理器类"""
    
    def __init__(self):
        self.tools = {}
        self.tool_categories = {
            "network_scanner": "网络扫描工具",
            "web_scanner": "Web扫描工具",
            "exploitation": "漏洞利用工具",
            "reconnaissance": "信息收集工具",
            "password_cracking": "密码破解工具",
            "security_assessment": "安全评估工具"
        }
        # 加载工具配置
        self._load_tools()
    
    def _load_tools(self):
        """加载工具配置"""
        # 先尝试从YAML配置文件加载工具
        self._load_tools_from_yaml()
        
        # 如果没有YAML文件，使用默认工具配置
        if not self.tools:
            self._load_default_tools()
    
    def _load_tools_from_yaml(self):
        """从YAML配置文件加载工具"""
        tools_dir = "tools"
        if os.path.exists(tools_dir):
            for filename in os.listdir(tools_dir):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    tool_path = os.path.join(tools_dir, filename)
                    try:
                        with open(tool_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f)
                            if config and config.get("enabled", True):
                                tool_name = config.get("name")
                                if tool_name:
                                    # 确定工具类别
                                    category = self._get_tool_category(tool_name)
                                    
                                    # 获取工具路径
                                    tool_executable = config.get("execution", {}).get("executable", tool_name)
                                    tool_base_args = config.get("execution", {}).get("base_args", [])
                                    
                                    # 构建完整的工具路径
                                    if tool_executable and isinstance(tool_executable, str):
                                        # 如果是相对路径，转换为绝对路径
                                        if not os.path.isabs(tool_executable):
                                            tool_executable = os.path.join(os.getcwd(), tool_executable)
                                    else:
                                        tool_executable = tool_name
                                    
                                    # 创建工具配置
                                    tool_config = {
                                        "path": tool_executable,
                                        "description": config.get("description", config.get("short_description", "")),
                                        "category": category,
                                        "params": config.get("parameters", []),
                                        "config": config
                                    }
                                    self.tools[tool_name] = tool_config
                    except Exception as e:
                        print(f"加载工具配置文件 {filename} 失败: {e}")
    
    def _get_tool_category(self, tool_name):
        """根据工具名称确定类别"""
        category_map = {
            "nmap": "network_scanner",
            "masscan": "network_scanner",
            "rustscan": "network_scanner",
            "unicornscan": "network_scanner",
            "sqlmap": "web_scanner",
            "nuclei": "web_scanner",
            "gobuster": "web_scanner",
            "dirsearch": "web_scanner",
            "httpx": "web_scanner",
            "arachni": "web_scanner",
            "w3af": "web_scanner",
            "wfuzz": "web_scanner",
            "metasploit": "exploitation",
            "msfvenom": "exploitation",
            "searchsploit": "exploitation",
            "subfinder": "reconnaissance",
            "amass": "reconnaissance",
            "theHarvester": "reconnaissance",
            "recon-ng": "reconnaissance",
            "hashcat": "password_cracking",
            "john": "password_cracking",
            "hydra": "password_cracking",
            "medusa": "password_cracking",
            "nikto": "security_assessment",
            "wafw00f": "security_assessment",
            "testssl.sh": "security_assessment"
        }
        return category_map.get(tool_name, "web_scanner")
    
    def _load_default_tools(self):
        """加载默认工具配置"""
        self.tools = {
            # 网络扫描工具
            "nmap": {
                "path": "nmap",
                "description": "网络扫描工具",
                "category": "network_scanner",
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP或域名", "required": True},
                    {"name": "ports", "type": "string", "description": "端口范围", "required": False},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "masscan": {
                "path": "masscan",
                "description": "高速网络扫描工具",
                "category": "network_scanner",
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP或网段", "required": True},
                    {"name": "ports", "type": "string", "description": "端口范围", "required": True},
                    {"name": "rate", "type": "string", "description": "扫描速率", "required": False}
                ]
            },
            "rustscan": {
                "path": "rustscan",
                "description": "快速端口扫描工具",
                "category": "network_scanner",
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP或域名", "required": True},
                    {"name": "ports", "type": "string", "description": "端口范围", "required": False}
                ]
            },
            
            # Web扫描工具
            "sqlmap": {
                "path": "sqlmap",
                "description": "SQL注入工具",
                "category": "web_scanner",
                "params": [
                    {"name": "url", "type": "string", "description": "目标URL", "required": True},
                    {"name": "param", "type": "string", "description": "参数名", "required": False},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "nuclei": {
                "path": "nuclei",
                "description": "漏洞扫描工具",
                "category": "web_scanner",
                "params": [
                    {"name": "target", "type": "string", "description": "目标URL或文件", "required": True},
                    {"name": "templates", "type": "string", "description": "模板路径", "required": False},
                    {"name": "severity", "type": "string", "description": "严重程度过滤", "required": False}
                ]
            },
            "gobuster": {
                "path": "gobuster",
                "description": "目录爆破工具",
                "category": "web_scanner",
                "params": [
                    {"name": "url", "type": "string", "description": "目标URL", "required": True},
                    {"name": "wordlist", "type": "string", "description": "字典路径", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "dirsearch": {
                "path": "dirsearch",
                "description": "目录扫描工具",
                "category": "web_scanner",
                "params": [
                    {"name": "url", "type": "string", "description": "目标URL", "required": True},
                    {"name": "wordlist", "type": "string", "description": "字典路径", "required": False},
                    {"name": "extensions", "type": "string", "description": "文件扩展名", "required": False}
                ]
            },
            "httpx": {
                "path": "httpx",
                "description": "HTTP探测工具",
                "category": "web_scanner",
                "params": [
                    {"name": "targets", "type": "string", "description": "目标列表", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            
            # 漏洞利用工具
            "metasploit": {
                "path": "msfconsole",
                "description": "渗透测试框架",
                "category": "exploitation",
                "params": [
                    {"name": "command", "type": "string", "description": "MSF命令", "required": True}
                ]
            },
            "msfvenom": {
                "path": "msfvenom",
                "description": " payload生成工具",
                "category": "exploitation",
                "params": [
                    {"name": "payload", "type": "string", "description": "Payload类型", "required": True},
                    {"name": "options", "type": "string", "description": "选项", "required": False}
                ]
            },
            
            # 子域名枚举工具
            "subfinder": {
                "path": "subfinder",
                "description": "子域名枚举工具",
                "category": "reconnaissance",
                "params": [
                    {"name": "domain", "type": "string", "description": "目标域名", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "amass": {
                "path": "amass",
                "description": "子域名枚举工具",
                "category": "reconnaissance",
                "params": [
                    {"name": "domain", "type": "string", "description": "目标域名", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            
            # 密码破解工具
            "hashcat": {
                "path": "hashcat",
                "description": "密码破解工具",
                "category": "password_cracking",
                "params": [
                    {"name": "hashfile", "type": "string", "description": "哈希文件", "required": True},
                    {"name": "wordlist", "type": "string", "description": "字典路径", "required": True},
                    {"name": "mode", "type": "string", "description": "破解模式", "required": False}
                ]
            },
            "john": {
                "path": "john",
                "description": "密码破解工具",
                "category": "password_cracking",
                "params": [
                    {"name": "hashfile", "type": "string", "description": "哈希文件", "required": True},
                    {"name": "wordlist", "type": "string", "description": "字典路径", "required": False}
                ]
            },
            
            # 安全评估工具
            "nikto": {
                "path": "nikto",
                "description": "Web服务器扫描工具",
                "category": "security_assessment",
                "params": [
                    {"name": "target", "type": "string", "description": "目标URL", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "wafw00f": {
                "path": "wafw00f",
                "description": "WAF检测工具",
                "category": "security_assessment",
                "params": [
                    {"name": "target", "type": "string", "description": "目标URL", "required": True}
                ]
            },
            "testssl.sh": {
                "path": "testssl.sh",
                "description": "SSL/TLS安全测试工具",
                "category": "security_assessment",
                "params": [
                    {"name": "target", "type": "string", "description": "目标域名或IP", "required": True}
                ]
            },
            "arachni": {
                "path": "arachni",
                "description": "Web应用安全扫描工具",
                "category": "security_assessment",
                "params": [
                    {"name": "target", "type": "string", "description": "目标URL", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "w3af": {
                "path": "w3af_console",
                "description": "Web应用攻击和审计框架",
                "category": "security_assessment",
                "params": [
                    {"name": "target", "type": "string", "description": "目标URL", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            
            # 网络扫描工具（新增）
            "unicornscan": {
                "path": "unicornscan",
                "description": "异步网络扫描工具",
                "category": "network_scanner",
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP或网段", "required": True},
                    {"name": "ports", "type": "string", "description": "端口范围", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            
            # Web扫描工具（新增）
            "wfuzz": {
                "path": "wfuzz",
                "description": "Web模糊测试工具",
                "category": "web_scanner",
                "params": [
                    {"name": "url", "type": "string", "description": "目标URL", "required": True},
                    {"name": "wordlist", "type": "string", "description": "字典路径", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            
            # 漏洞利用工具（新增）
            "exploitdb": {
                "path": "searchsploit",
                "description": "漏洞数据库搜索工具",
                "category": "exploitation",
                "params": [
                    {"name": "query", "type": "string", "description": "搜索关键词", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            
            # 信息收集工具（新增）
            "theHarvester": {
                "path": "theHarvester",
                "description": "电子邮件和子域名收集工具",
                "category": "reconnaissance",
                "params": [
                    {"name": "domain", "type": "string", "description": "目标域名", "required": True},
                    {"name": "source", "type": "string", "description": "数据源", "required": False},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "recon-ng": {
                "path": "recon-ng",
                "description": "Web侦察框架",
                "category": "reconnaissance",
                "params": [
                    {"name": "command", "type": "string", "description": "Recon-ng命令", "required": True}
                ]
            },
            
            # 密码破解工具（新增）
            "hydra": {
                "path": "hydra",
                "description": "网络认证破解工具",
                "category": "password_cracking",
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP", "required": True},
                    {"name": "service", "type": "string", "description": "服务类型", "required": True},
                    {"name": "wordlist", "type": "string", "description": "密码字典", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            },
            "medusa": {
                "path": "medusa",
                "description": "并行网络登录破解工具",
                "category": "password_cracking",
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP", "required": True},
                    {"name": "service", "type": "string", "description": "服务类型", "required": True},
                    {"name": "wordlist", "type": "string", "description": "密码字典", "required": True},
                    {"name": "flags", "type": "string", "description": "额外参数", "required": False}
                ]
            }
        }
    
    def execute_tool(self, tool_name: str, args: List[str], timeout: int = 60) -> str:
        """执行工具
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            timeout: 超时时间（秒）
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具 {tool_name} 不存在")
        
        tool_path = self.tools[tool_name]["path"]
        
        try:
            # 构建命令
            cmd = [tool_path] + args
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # 返回输出
            if result.returncode != 0:
                return f"执行失败: {result.stderr}"
            return result.stdout
        
        except FileNotFoundError:
            return f"工具 {tool_name} 未安装"
        except subprocess.TimeoutExpired:
            return f"工具执行超时 (超过 {timeout} 秒)"
        except Exception as e:
            return f"执行工具时出错: {str(e)}"
    
    def get_tool_info(self, tool_name: str) -> Optional[dict]:
        """获取工具信息"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[dict]:
        """列出所有工具"""
        return [
            {"name": name, "description": info["description"]}
            for name, info in self.tools.items()
        ]
    
    def add_tool(self, tool_name: str, tool_path: str, description: str, category: str = "web_scanner", params: list = None):
        """添加工具"""
        self.tools[tool_name] = {
            "path": tool_path,
            "description": description,
            "category": category,
            "params": params or []
        }
    
    def add_custom_tool(self, tool_config: dict):
        """添加自定义工具"""
        tool_name = tool_config.get("name")
        if not tool_name:
            return {"error": "工具名称不能为空"}
        
        tool_path = tool_config.get("path")
        if not tool_path:
            return {"error": "工具路径不能为空"}
        
        description = tool_config.get("description", "自定义工具")
        category = tool_config.get("category", "web_scanner")
        params = tool_config.get("params", [])
        
        self.tools[tool_name] = {
            "path": tool_path,
            "description": description,
            "category": category,
            "params": params,
            "custom": True
        }
        
        return {"success": True, "message": f"自定义工具 {tool_name} 添加成功"}
    
    def remove_tool(self, tool_name: str):
        """移除工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]
    
    def list_tools_by_category(self, category: str) -> List[dict]:
        """按类别列出工具"""
        return [
            {"name": name, "description": info["description"]}
            for name, info in self.tools.items()
            if info.get("category") == category
        ]
    
    def get_tool_categories(self) -> dict:
        """获取工具类别"""
        return self.tool_categories
    
    def get_tool_params(self, tool_name: str) -> Optional[List[dict]]:
        """获取工具参数信息"""
        tool_info = self.tools.get(tool_name)
        return tool_info.get("params", []) if tool_info else None
    
    def check_tool_installed(self, tool_name: str) -> bool:
        """检查工具是否安装"""
        if tool_name not in self.tools:
            return False
        
        tool_path = self.tools[tool_name]["path"]
        if not tool_path:
            return False
        
        # 对于Python脚本，我们需要使用python命令来执行
        if tool_path.endswith(".py"):
            try:
                result = subprocess.run(
                    ["python", tool_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, TypeError):
                return False
        # 对于Shell脚本，我们需要使用bash或cmd来执行
        elif tool_path.endswith(".sh"):
            try:
                result = subprocess.run(
                    ["bash", tool_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, TypeError):
                return False
        # 对于可执行文件，直接执行
        else:
            try:
                result = subprocess.run(
                    [tool_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False
                )
                return result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, TypeError, OSError):
                return False
    
    def get_tool_version(self, tool_name: str) -> Optional[str]:
        """获取工具版本
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具版本字符串，若工具未安装则返回None
        """
        if tool_name not in self.tools:
            return None
        
        tool_path = self.tools[tool_name]["path"]
        if not tool_path:
            return None
        
        # 对于Python脚本，我们需要使用python命令来执行
        if tool_path.endswith(".py"):
            try:
                result = subprocess.run(
                    ["python", tool_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, TypeError):
                return None
        # 对于Shell脚本，我们需要使用bash或cmd来执行
        elif tool_path.endswith(".sh"):
            try:
                result = subprocess.run(
                    ["bash", tool_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, TypeError):
                return None
        # 对于可执行文件，直接执行
        else:
            try:
                result = subprocess.run(
                    [tool_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, TypeError, OSError):
                return None
        
        if result.returncode != 0:
            return None
        
        # 解析版本信息
        output = result.stdout.strip()
        import re
        
        # 通用版本匹配
        version_match = re.search(r'\b(\d+\.\d+(?:\.\d+)*)\b', output)
        if version_match:
            return version_match.group(1)
        
        # 特殊工具的版本匹配
        if tool_name == "nmap":
            match = re.search(r'Nmap version (\d+\.\d+[\d.-]+)', output)
            if match:
                return match.group(1)
        elif tool_name == "sqlmap":
            match = re.search(r'sqlmap/([\d.]+)', output)
            if match:
                return match.group(1)
        elif tool_name == "nuclei":
            match = re.search(r'Nuclei\s+v([\d.]+)', output)
            if match:
                return match.group(1)
        
        return output.split('\n')[0] if output else None
    
    def check_tool_update(self, tool_name: str) -> Dict[str, Any]:
        """检查工具更新
        
        Args:
            tool_name: 工具名称
            
        Returns:
            包含当前版本和最新版本信息的字典
        """
        current_version = self.get_tool_version(tool_name)
        
        # 模拟最新版本信息（实际应从官方源获取）
        latest_versions = {
            "nmap": "7.94",
            "sqlmap": "1.7.2",
            "nuclei": "3.2.4",
            "gobuster": "3.6.0",
            "subfinder": "2.6.4",
            "amass": "3.23.2",
            "masscan": "1.3.2",
            "rustscan": "2.1.1",
            "dirsearch": "0.4.2",
            "httpx": "1.6.2",
            "metasploit": "6.3.53",
            "msfvenom": "6.3.53",
            "hashcat": "6.2.6",
            "john": "1.9.0",
            "nikto": "2.1.6",
            "wafw00f": "2.2.1",
            "testssl.sh": "3.2rc6",
            "arachni": "1.5.1",
            "w3af": "2.1.0",
            "unicornscan": "0.4.7",
            "wfuzz": "3.1.0",
            "exploitdb": "2024-07-01",
            "theHarvester": "4.6.0",
            "recon-ng": "5.1.2",
            "hydra": "9.5",
            "medusa": "2.2"}
        
        latest_version = latest_versions.get(tool_name, "未知")
        
        # 简单的版本比较
        is_outdated = False
        if current_version and latest_version != "未知":
            try:
                # 简单的版本比较逻辑
                current_parts = [int(part) for part in re.sub(r'[^0-9.]', '', current_version).split('.') if part]
                latest_parts = [int(part) for part in re.sub(r'[^0-9.]', '', latest_version).split('.') if part]
                
                for i in range(max(len(current_parts), len(latest_parts))):
                    current = current_parts[i] if i < len(current_parts) else 0
                    latest = latest_parts[i] if i < len(latest_parts) else 0
                    if latest > current:
                        is_outdated = True
                        break
                    elif latest < current:
                        break
            except Exception:
                pass
        
        return {
            "tool": tool_name,
            "current_version": current_version,
            "latest_version": latest_version,
            "is_outdated": is_outdated
        }
    
    def get_tool_versions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有工具的版本信息
        
        Returns:
            工具版本信息字典
        """
        versions = {}
        for tool_name in self.tools:
            try:
                versions[tool_name] = {
                    "installed": self.check_tool_installed(tool_name),
                    "version": self.get_tool_version(tool_name),
                    "update_info": self.check_tool_update(tool_name)
                }
            except Exception as e:
                # 处理执行错误，将工具标记为未安装
                versions[tool_name] = {
                    "installed": False,
                    "version": None,
                    "update_info": {
                        "tool": tool_name,
                        "current_version": None,
                        "latest_version": "未知",
                        "is_outdated": False
                    }
                }
        return versions
    
    def check_all_updates(self) -> List[Dict[str, Any]]:
        """检查所有工具的更新
        
        Returns:
            需要更新的工具列表
        """
        outdated_tools = []
        for tool_name in self.tools:
            update_info = self.check_tool_update(tool_name)
            if update_info["is_outdated"]:
                outdated_tools.append(update_info)
        return outdated_tools
    
    def execute_tool_with_params(self, tool_name: str, params: dict, timeout: int = 300) -> str:
        """使用参数执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            timeout: 超时时间（秒）
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            return f"工具 {tool_name} 不存在"
        
        tool_info = self.tools[tool_name]
        tool_path = tool_info["path"]
        tool_params = tool_info.get("params", [])
        
        # 构建命令参数
        cmd_args = []
        
        # 添加默认参数
        if tool_info.get("config") and tool_info["config"].get("args"):
            cmd_args.extend(tool_info["config"]["args"])
        
        # 检查必需参数
        for param_info in tool_params:
            param_name = param_info["name"]
            if param_info.get("required") and param_name not in params:
                return f"缺少必需参数: {param_name}"
            
            if param_name in params:
                # 根据参数格式构建参数
                param_value = params[param_name]
                param_format = param_info.get("format", "positional")
                
                # 确保参数值是字符串
                if not isinstance(param_value, str):
                    param_value = str(param_value)
                
                if param_format == "positional":
                    # 位置参数
                    cmd_args.append(param_value)
                elif param_format == "flag":
                    # 带标志的参数
                    flag = param_info.get("flag")
                    if flag:
                        cmd_args.extend([flag, param_value])
                elif param_format == "template":
                    # 模板参数
                    template = param_info.get("template")
                    if template:
                        formatted_value = template.replace("{value}", param_value)
                        cmd_args.append(formatted_value)
                elif param_format == "bool":
                    # 布尔参数
                    if param_value.lower() == "true" and param_info.get("flag"):
                        cmd_args.append(param_info["flag"])
        
        # 执行工具
        try:
            cmd = [tool_path] + cmd_args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                return f"执行失败: {result.stderr}"
            return result.stdout
        
        except FileNotFoundError:
            return f"工具 {tool_name} 未安装"
        except subprocess.TimeoutExpired:
            return f"工具执行超时 (超过 {timeout} 秒)"
        except Exception as e:
            return f"执行工具时出错: {str(e)}"
    
    def get_supported_scan_scenarios(self) -> List[dict]:
        """获取支持的扫描场景"""
        return [
            {
                "name": "网络扫描",
                "description": "扫描目标网络的开放端口和服务",
                "tools": ["nmap", "masscan", "rustscan"],
                "params": [
                    {"name": "target", "type": "string", "description": "目标IP或域名", "required": True},
                    {"name": "ports", "type": "string", "description": "端口范围", "required": False}
                ]
            },
            {
                "name": "Web应用扫描",
                "description": "扫描Web应用的漏洞和敏感信息",
                "tools": ["nuclei", "gobuster", "dirsearch", "nikto"],
                "params": [
                    {"name": "url", "type": "string", "description": "目标URL", "required": True},
                    {"name": "wordlist", "type": "string", "description": "字典路径", "required": False}
                ]
            },
            {
                "name": "SQL注入测试",
                "description": "测试Web应用的SQL注入漏洞",
                "tools": ["sqlmap"],
                "params": [
                    {"name": "url", "type": "string", "description": "目标URL", "required": True},
                    {"name": "param", "type": "string", "description": "参数名", "required": False}
                ]
            },
            {
                "name": "子域名枚举",
                "description": "枚举目标域名的子域名",
                "tools": ["subfinder", "amass", "theHarvester"],
                "params": [
                    {"name": "domain", "type": "string", "description": "目标域名", "required": True}
                ]
            },
            {
                "name": "SSL/TLS安全测试",
                "description": "测试目标网站的SSL/TLS配置",
                "tools": ["testssl.sh"],
                "params": [
                    {"name": "target", "type": "string", "description": "目标域名", "required": True}
                ]
            },
            {
                "name": "WAF检测",
                "description": "检测目标网站是否使用WAF",
                "tools": ["wafw00f"],
                "params": [
                    {"name": "target", "type": "string", "description": "目标URL", "required": True}
                ]
            }
        ]
    
    def execute_tools_in_parallel(self, tool_tasks: List[Dict[str, Any]], max_workers: int = 10, overall_timeout: int = 600) -> Dict[str, str]:
        """并行执行多个工具
        
        Args:
            tool_tasks: 工具任务列表，每个任务包含tool_name、params和可选的timeout
            max_workers: 最大并行工作数
            overall_timeout: 整体超时时间（秒）
            
        Returns:
            工具执行结果字典，键为工具名称，值为执行结果
        """
        results = {}
        
        def _execute_task(task):
            tool_name = task["tool_name"]
            params = task.get("params", {})
            timeout = task.get("timeout", 300)
            try:
                return tool_name, self.execute_tool_with_params(tool_name, params, timeout)
            except Exception as e:
                return tool_name, f"执行失败: {str(e)}"
        
        # 动态调整最大工作数，基于CPU核心数
        import os
        cpu_count = os.cpu_count() or 4
        adjusted_workers = min(max_workers, cpu_count * 2)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=adjusted_workers) as executor:
            future_to_task = {executor.submit(_execute_task, task): task for task in tool_tasks}
            try:
                for future in concurrent.futures.as_completed(future_to_task, timeout=overall_timeout):
                    task = future_to_task[future]
                    try:
                        tool_name, result = future.result()
                        results[tool_name] = result
                    except Exception as e:
                        tool_name = task["tool_name"]
                        results[tool_name] = f"执行失败: {str(e)}"
            except concurrent.futures.TimeoutError:
                # 处理整体超时
                for future, task in future_to_task.items():
                    if not future.done():
                        future.cancel()
                        tool_name = task["tool_name"]
                        results[tool_name] = f"执行超时 (超过整体超时时间 {overall_timeout} 秒)"
        
        return results
    
    def execute_scan_scenario(self, scenario_name: str, params: Dict[str, Any], max_workers: int = 10, overall_timeout: int = 600) -> Dict[str, str]:
        """执行扫描场景
        
        Args:
            scenario_name: 扫描场景名称
            params: 场景参数
            max_workers: 最大并行工作数
            overall_timeout: 整体超时时间（秒）
            
        Returns:
            工具执行结果字典
        """
        scenarios = self.get_supported_scan_scenarios()
        target_scenario = None
        
        for scenario in scenarios:
            if scenario["name"] == scenario_name:
                target_scenario = scenario
                break
        
        if not target_scenario:
            return {"error": f"扫描场景 {scenario_name} 不存在"}
        
        # 构建工具任务
        tool_tasks = []
        for tool_name in target_scenario["tools"]:
            # 转换场景参数为工具参数
            tool_params = {}
            for param in target_scenario["params"]:
                param_name = param["name"]
                if param_name in params:
                    tool_params[param_name] = params[param_name]
            
            # 根据工具类型设置不同的超时时间
            timeout = 300  # 默认超时时间
            if tool_name in ["sqlmap", "nmap"]:
                timeout = 600  # 长时间运行的工具
            elif tool_name in ["masscan", "rustscan"]:
                timeout = 180  # 快速扫描工具
            
            tool_tasks.append({
                "tool_name": tool_name,
                "params": tool_params,
                "timeout": timeout
            })
        
        # 并行执行工具
        return self.execute_tools_in_parallel(tool_tasks, max_workers, overall_timeout)
    
    def execute_tool_chain(self, tool_chain: List[Dict[str, Any]], max_workers: int = 5, overall_timeout: int = 600) -> Dict[str, Any]:
        """执行工具链
        
        Args:
            tool_chain: 工具链配置，包含工具名称和参数
            max_workers: 最大并行工作数
            overall_timeout: 整体超时时间（秒）
            
        Returns:
            工具链执行结果
        """
        results = {}
        previous_output = {}
        
        for i, tool_config in enumerate(tool_chain):
            tool_name = tool_config.get("tool")
            tool_params = tool_config.get("params", {})
            timeout = tool_config.get("timeout", 300)
            
            # 替换参数中的变量，使用前一个工具的输出
            for param_name, param_value in tool_params.items():
                if isinstance(param_value, str) and param_value.startswith("$"):
                    # 提取变量名，如 $previous.output.port
                    var_path = param_value[1:].split(".")
                    var_value = previous_output
                    
                    try:
                        for part in var_path:
                            var_value = var_value.get(part)
                        if var_value is not None:
                            tool_params[param_name] = var_value
                    except:
                        pass
            
            try:
                logger.info(f"执行工具链步骤 {i+1}: {tool_name}")
                result = self.execute_tool_with_params(tool_name, tool_params, timeout)
                results[tool_name] = result
                
                # 解析结果，作为下一个工具的输入
                try:
                    # 尝试解析JSON结果
                    previous_output = json.loads(result)
                except:
                    # 如果不是JSON，保持原始结果
                    previous_output = {"output": result}
                    
            except Exception as e:
                logger.error(f"执行工具链步骤 {i+1} 时出错: {e}")
                results[tool_name] = f"执行失败: {str(e)}"
                # 可以选择继续执行或停止
                if tool_config.get("stop_on_error", True):
                    break
        
        return {
            "tool_chain": tool_chain,
            "results": results,
            "status": "completed" if all("执行失败" not in str(v) for v in results.values()) else "failed"
        }
        scenarios = self.get_supported_scan_scenarios()
        target_scenario = None
        
        for scenario in scenarios:
            if scenario["name"] == scenario_name:
                target_scenario = scenario
                break
        
        if not target_scenario:
            return {"error": f"扫描场景 {scenario_name} 不存在"}
        
        # 构建工具任务
        tool_tasks = []
        for tool_name in target_scenario["tools"]:
            # 转换场景参数为工具参数
            tool_params = {}
            for param in target_scenario["params"]:
                param_name = param["name"]
                if param_name in params:
                    tool_params[param_name] = params[param_name]
            
            # 根据工具类型设置不同的超时时间
            timeout = 300  # 默认超时时间
            if tool_name in ["sqlmap", "nmap"]:
                timeout = 600  # 长时间运行的工具
            elif tool_name in ["masscan", "rustscan"]:
                timeout = 180  # 快速扫描工具
            
            tool_tasks.append({
                "tool_name": tool_name,
                "params": tool_params,
                "timeout": timeout
            })
        
        # 并行执行工具
        return self.execute_tools_in_parallel(tool_tasks, max_workers, overall_timeout)
