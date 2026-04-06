# -*- coding: utf-8 -*-
"""
工具注册表
管理所有安全工具适配器，提供统一的工具访问接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_mode: str = "real"  # real, simulated, mock
    raw_output: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_mode": self.execution_mode,
            "execution_time": self.execution_time,
            "has_raw_output": bool(self.raw_output)
        }


class ToolAdapter(ABC):
    """工具适配器基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.available = False
        self._check_availability()
    
    @abstractmethod
    def _check_availability(self) -> bool:
        """检查工具是否可用"""
        pass
    
    @abstractmethod
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行工具"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "available": self.available,
            "adapter_type": self.__class__.__name__
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._adapters: Dict[str, ToolAdapter] = {}
    
    def register(self, adapter: ToolAdapter) -> None:
        """注册工具适配器"""
        self._adapters[adapter.name] = adapter
        print(f"注册工具适配器: {adapter.name} ({adapter.description})")
    
    def get(self, name: str) -> Optional[ToolAdapter]:
        """获取工具适配器"""
        return self._adapters.get(name)
    
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """列出所有工具信息"""
        return {
            name: adapter.get_info()
            for name, adapter in self._adapters.items()
        }
    
    def list_available(self) -> Dict[str, ToolAdapter]:
        """列出所有可用的工具"""
        return {
            name: adapter
            for name, adapter in self._adapters.items()
            if adapter.available
        }
    
    def execute(self, name: str, target: str, **kwargs) -> ToolResult:
        """执行指定工具"""
        adapter = self.get(name)
        if not adapter:
            return ToolResult(
                success=False,
                data={},
                error=f"工具未找到: {name}",
                execution_mode="error"
            )
        
        if not adapter.available:
            return ToolResult(
                success=False,
                data={},
                error=f"工具不可用: {name}",
                execution_mode="error"
            )
        
        try:
            return adapter.execute(target, **kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=f"执行错误: {str(e)}",
                execution_mode="error"
            )
    
    def has_tool(self, name: str) -> bool:
        """检查是否有指定工具"""
        return name in self._adapters
    
    def is_available(self, name: str) -> bool:
        """检查工具是否可用"""
        adapter = self.get(name)
        return adapter.available if adapter else False


# ==================== 具体工具适配器 ====================

import subprocess
import json
import re
import time
from typing import Tuple


class NmapAdapter(ToolAdapter):
    """Nmap适配器"""
    
    def __init__(self, path: str = "nmap"):
        super().__init__("nmap", "端口扫描工具")
        self.path = path
        self.timeout = 300
    
    def _check_availability(self) -> bool:
        """检查nmap是否可用"""
        try:
            result = subprocess.run(
                [self.path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.available = result.returncode == 0
            return self.available
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self.available = False
            return False
    
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行nmap扫描"""
        start_time = time.time()
        
        try:
            # 清理目标格式
            if target.startswith("http://"):
                target = target.replace("http://", "")
            elif target.startswith("https://"):
                target = target.replace("https://", "")
            
            # 获取端口参数
            ports = kwargs.get("ports", "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017")
            
            # 构建命令
            cmd = [
                self.path,
                "-sT",           # TCP连接扫描
                "-p", ports,
                "-T4",           # 较快扫描速度
                "--open",        # 只显示开放端口
                "-n",            # 不进行DNS解析
                "--host-timeout", "2m",
                target
            ]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    data={"target": target, "ports": []},
                    error=f"nmap命令执行失败: {result.returncode}",
                    execution_mode="real",
                    raw_output=result.stderr[:500] if result.stderr else "",
                    execution_time=execution_time
                )
            
            # 解析输出
            ports_data = self._parse_output(result.stdout)
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "ports": ports_data,
                    "scan_type": "TCP连接扫描"
                },
                error=None,
                execution_mode="real",
                raw_output=result.stdout[:1000],
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"target": target, "ports": []},
                error="nmap扫描超时",
                execution_mode="real",
                execution_time=self.timeout
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={"target": target, "ports": []},
                error=f"执行错误: {str(e)}",
                execution_mode="real",
                execution_time=time.time() - start_time
            )
    
    def _parse_output(self, output: str) -> List[Dict[str, Any]]:
        """解析nmap输出"""
        ports = []
        port_pattern = r'(\d+)/tcp\s+(\w+)\s+(\S+)'
        lines = output.split('\n')
        in_port_section = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('PORT') and 'STATE' in line and 'SERVICE' in line:
                in_port_section = True
                continue
            
            if not in_port_section:
                continue
            
            if not line or line.startswith('---'):
                continue
            
            match = re.match(port_pattern, line)
            if match:
                port_num = int(match.group(1))
                state = match.group(2)
                service = match.group(3)
                
                if state == 'open':
                    ports.append({
                        "port": port_num,
                        "service": service,
                        "state": state
                    })
        
        return ports


class WhatWebAdapter(ToolAdapter):
    """WhatWeb适配器"""
    
    def __init__(self, path: str = "whatweb"):
        super().__init__("whatweb", "Web指纹识别工具")
        self.path = path
        self.timeout = 120
    
    def _check_availability(self) -> bool:
        """检查whatweb是否可用"""
        try:
            result = subprocess.run(
                [self.path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.available = result.returncode == 0
            return self.available
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self.available = False
            return False
    
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行whatweb扫描"""
        start_time = time.time()
        
        try:
            # 确保目标有http/https前缀
            if not (target.startswith("http://") or target.startswith("https://")):
                target = f"http://{target}"
            
            # 构建命令
            cmd = [
                self.path,
                "-a", "3",           # 攻击级别3
                "--log-json", "-",   # JSON输出
                "--no-errors",       # 忽略错误
                target
            ]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    data={"target": target, "fingerprint": {}},
                    error=f"whatweb命令执行失败: {result.returncode}",
                    execution_mode="real",
                    raw_output=result.stderr[:500] if result.stderr else "",
                    execution_time=execution_time
                )
            
            # 解析输出
            fingerprint = self._parse_output(result.stdout)
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "fingerprint": fingerprint
                },
                error=None,
                execution_mode="real",
                raw_output=result.stdout[:1000],
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"target": target, "fingerprint": {}},
                error="whatweb扫描超时",
                execution_mode="real",
                execution_time=self.timeout
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={"target": target, "fingerprint": {}},
                error=f"执行错误: {str(e)}",
                execution_mode="real",
                execution_time=time.time() - start_time
            )
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """解析whatweb输出"""
        fingerprint = {
            "web_server": "",
            "language": [],
            "framework": [],
            "cms": [],
            "other": [],
            "attack_surface": []
        }
        
        try:
            # 尝试解析JSON输出
            data = json.loads(output)
            if not data:
                return fingerprint
            
            plugins = data[0].get("plugins", {})
            
            # 技术栈映射
            tech_map = {
                'nginx': 'web_server', 'apache': 'web_server', 'iis': 'web_server',
                'php': 'language', 'python': 'language', 'node': 'language', 'java': 'language',
                'django': 'framework', 'laravel': 'framework', 'spring': 'framework',
                'wordpress': 'cms', 'joomla': 'cms', 'drupal': 'cms'
            }
            
            for plugin_name, plugin_data in plugins.items():
                if isinstance(plugin_data, dict):
                    # 确定技术类别
                    category = "other"
                    for keyword, cat in tech_map.items():
                        if keyword in plugin_name.lower():
                            category = cat
                            break
                    
                    if category == "web_server" and not fingerprint["web_server"]:
                        string_data = plugin_data.get("string", [])
                        if string_data:
                            fingerprint["web_server"] = string_data[0]
                    elif category != "web_server":
                        tech_info = plugin_name
                        version = plugin_data.get("version", [])
                        if version:
                            tech_info += f" {version[0]}"
                        if tech_info not in fingerprint[category]:
                            fingerprint[category].append(tech_info)
            
            # 生成攻击面分析
            fingerprint["attack_surface"] = self._generate_attack_surface(fingerprint)
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试文本解析
            fingerprint = self._parse_whatweb_text(output)
        
        return fingerprint
    
    def _parse_whatweb_text(self, output: str) -> Dict[str, Any]:
        """解析whatweb文本输出"""
        fingerprint = {
            "web_server": "",
            "language": [],
            "framework": [],
            "cms": [],
            "other": [],
            "attack_surface": []
        }
        
        for line in output.split('\n'):
            line = line.strip()
            
            # 提取服务器信息
            server_match = re.search(r'Server\[(.*?)\]', line)
            if server_match and not fingerprint["web_server"]:
                fingerprint["web_server"] = server_match.group(1)
            
            # 提取技术信息
            tech_match = re.search(r'([A-Z][a-zA-Z]+)\[(.*?)\]', line)
            if tech_match:
                tech_name = tech_match.group(1)
                if tech_name in ['HTTPServer', 'Title', 'IP', 'Country']:
                    continue
                
                # 简单分类
                tech_lower = tech_name.lower()
                if 'nginx' in tech_lower or 'apache' in tech_lower or 'iis' in tech_lower:
                    if not fingerprint["web_server"]:
                        fingerprint["web_server"] = tech_name
                elif 'php' in tech_lower or 'python' in tech_lower or 'java' in tech_lower:
                    if tech_name not in fingerprint["language"]:
                        fingerprint["language"].append(tech_name)
                elif 'wordpress' in tech_lower or 'joomla' in tech_lower or 'drupal' in tech_lower:
                    if tech_name not in fingerprint["cms"]:
                        fingerprint["cms"].append(tech_name)
                else:
                    if tech_name not in fingerprint["other"]:
                        fingerprint["other"].append(tech_name)
        
        # 生成攻击面分析
        fingerprint["attack_surface"] = self._generate_attack_surface(fingerprint)
        
        return fingerprint
    
    def _generate_attack_surface(self, fingerprint: Dict[str, Any]) -> List[str]:
        """生成攻击面分析"""
        attack_paths = []
        
        # Web服务器攻击路径
        if fingerprint["web_server"]:
            server = fingerprint["web_server"].lower()
            if 'nginx' in server:
                attack_paths.append("Nginx服务器可能存在配置错误，导致目录遍历或请求走私攻击")
            elif 'apache' in server:
                attack_paths.append("Apache服务器可能存在.htaccess配置漏洞，导致权限绕过或文件泄露")
            elif 'iis' in server:
                attack_paths.append("IIS服务器可能存在解析漏洞，导致短文件名泄露或权限配置错误")
        
        # 编程语言攻击路径
        for lang in fingerprint["language"]:
            if len(attack_paths) >= 3:
                break
            lang_lower = lang.lower()
            if 'php' in lang_lower:
                attack_paths.append("PHP环境可能存在文件上传漏洞，结合远程代码执行(RCE)实现系统控制")
            elif 'python' in lang_lower:
                attack_paths.append("Python应用可能存在反序列化漏洞，导致远程代码执行或数据泄露")
            elif 'java' in lang_lower:
                attack_paths.append("Java应用可能存在反序列化漏洞，结合XXE攻击实现远程代码执行")
        
        # CMS攻击路径
        for cms in fingerprint["cms"]:
            if len(attack_paths) >= 3:
                break
            cms_lower = cms.lower()
            if 'wordpress' in cms_lower:
                attack_paths.append("WordPress系统可能存在插件或主题漏洞，结合弱口令攻击实现权限提升")
            elif 'joomla' in cms_lower:
                attack_paths.append("Joomla系统可能存在组件漏洞，导致SQL注入或文件上传攻击")
            elif 'drupal' in cms_lower:
                attack_paths.append("Drupal系统可能存在模块漏洞，导致远程代码执行或权限提升攻击")
        
        # 补充通用攻击路径
        if len(attack_paths) < 3:
            generic = [
                "系统可能存在弱口令漏洞，导致未授权访问或权限提升",
                "应用可能存在信息泄露漏洞，暴露敏感配置或用户数据",
                "服务可能存在配置错误，导致权限绕过或服务暴露"
            ]
            for path in generic:
                if len(attack_paths) >= 3:
                    break
                if path not in attack_paths:
                    attack_paths.append(path)
        
        return attack_paths


class SqlmapAdapter(ToolAdapter):
    """Sqlmap适配器"""
    
    def __init__(self, path: str = "sqlmap"):
        super().__init__("sqlmap", "SQL注入检测工具")
        self.path = path
        self.timeout = 600
    
    def _check_availability(self) -> bool:
        """检查sqlmap是否可用"""
        try:
            result = subprocess.run(
                [self.path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.available = result.returncode == 0
            return self.available
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self.available = False
            return False
    
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行sqlmap扫描"""
        start_time = time.time()
        
        try:
            # 确保目标有http/https前缀
            if not (target.startswith("http://") or target.startswith("https://")):
                target = f"http://{target}"
            
            # 获取参数
            test_level = kwargs.get("test_level", 1)
            
            # 构建命令
            cmd = [
                self.path,
                "-u", target,
                "--batch",  # 批处理模式
                "--level", str(test_level),
                "--risk", "1",  # 低风险
                "--timeout", "30",
                "--flush-session",
                "--smart"  # 智能模式
            ]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    data={"target": target, "injections": []},
                    error=f"sqlmap命令执行失败: {result.returncode}",
                    execution_mode="real",
                    raw_output=result.stderr[:500] if result.stderr else "",
                    execution_time=execution_time
                )
            
            # 解析输出
            injections = self._parse_output(result.stdout)
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "injections": injections,
                    "scan_type": "SQL注入检测"
                },
                error=None,
                execution_mode="real",
                raw_output=result.stdout[:1000],
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"target": target, "injections": []},
                error="sqlmap扫描超时",
                execution_mode="real",
                execution_time=self.timeout
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={"target": target, "injections": []},
                error=f"执行错误: {str(e)}",
                execution_mode="real",
                execution_time=time.time() - start_time
            )
    
    def _parse_output(self, output: str) -> List[Dict[str, Any]]:
        """解析sqlmap输出"""
        injections = []
        
        # 查找注入点
        injection_patterns = [
            r'Parameter: (.+?) \(.+?\)\s+Type: (.+?)\s+Title: (.+?)\s+Payload: (.+)',
            r'\[INFO\] testing for (.+?) injection',
            r'\[CRITICAL\] (.+?) vulnerable to (.+?) injection'
        ]
        
        for line in output.split('\n'):
            line = line.strip()
            
            for pattern in injection_patterns:
                match = re.search(pattern, line)
                if match:
                    if len(match.groups()) >= 3:
                        injections.append({
                            "parameter": match.group(1) if len(match.groups()) > 0 else "unknown",
                            "type": match.group(2) if len(match.groups()) > 1 else "unknown",
                            "description": match.group(3) if len(match.groups()) > 2 else "SQL injection found",
                            "payload": match.group(4) if len(match.groups()) > 3 else ""
                        })
                    break
        
        return injections


class Wafw00fAdapter(ToolAdapter):
    """Wafw00f适配器"""
    
    def __init__(self, path: str = "wafw00f"):
        super().__init__("wafw00f", "WAF检测工具")
        self.path = path
        self.timeout = 120
    
    def _check_availability(self) -> bool:
        """检查wafw00f是否可用"""
        try:
            result = subprocess.run(
                [self.path, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.available = result.returncode == 0 or result.returncode == 1
            return self.available
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self.available = False
            return False
    
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行wafw00f扫描"""
        start_time = time.time()
        
        try:
            # 确保目标有http/https前缀
            if not (target.startswith("http://") or target.startswith("https://")):
                target = f"http://{target}"
            
            # 构建命令
            cmd = [self.path, target]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            
            # 解析输出
            waf_detected, waf_type = self._parse_output(result.stdout)
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "waf_detected": waf_detected,
                    "waf_type": waf_type
                },
                error=None,
                execution_mode="real",
                raw_output=result.stdout[:1000],
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"target": target, "waf_detected": False, "waf_type": None},
                error="wafw00f扫描超时",
                execution_mode="real",
                execution_time=self.timeout
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={"target": target, "waf_detected": False, "waf_type": None},
                error=f"执行错误: {str(e)}",
                execution_mode="real",
                execution_time=time.time() - start_time
            )
    
    def _parse_output(self, output: str) -> Tuple[bool, Optional[str]]:
        """解析wafw00f输出"""
        waf_detected = False
        waf_type = None
        
        # 查找WAF检测结果
        waf_patterns = [
            r'is behind (.+?) WAF',
            r'is protected by (.+?)',
            r'(.+?) detected'
        ]
        
        for line in output.split('\n'):
            line = line.strip().lower()
            
            if "no waf detected" in line or "not behind a waf" in line:
                waf_detected = False
                waf_type = None
                break
            
            for pattern in waf_patterns:
                match = re.search(pattern, line)
                if match:
                    waf_detected = True
                    waf_type = match.group(1).strip()
                    break
            
            if waf_detected:
                break
        
        return waf_detected, waf_type


class NucleiAdapter(ToolAdapter):
    """Nuclei适配器（真实执行版本）"""
    
    def __init__(self, path: str = "nuclei"):
        super().__init__("nuclei", "漏洞扫描工具")
        self.path = path
        self.timeout = 600
    
    def _check_availability(self) -> bool:
        """检查nuclei是否可用"""
        try:
            result = subprocess.run(
                [self.path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.available = result.returncode == 0
            return self.available
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self.available = False
            return False
    
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行nuclei扫描"""
        start_time = time.time()
        
        try:
            # 确保目标有http/https前缀
            if not (target.startswith("http://") or target.startswith("https://")):
                target = f"http://{target}"
            
            # 获取参数
            templates = kwargs.get("templates", "cves/")
            
            # 构建命令
            cmd = [self.path, "-u", target]
            
            if templates:
                cmd.extend(["-t", templates])
            
            cmd.extend(["-json", "-silent", "-timeout", "30"])
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            execution_time = time.time() - start_time
            
            vulnerabilities = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            import json as json_module
                            vuln_data = json_module.loads(line)
                            vulnerabilities.append(vuln_data)
                        except json_module.JSONDecodeError:
                            continue
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "vulnerabilities": vulnerabilities,
                    "scan_type": "漏洞扫描"
                },
                error=None,
                execution_mode="real",
                raw_output=result.stdout[:2000],
                execution_time=execution_time
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data={"target": target, "vulnerabilities": []},
                error="nuclei扫描超时",
                execution_mode="real",
                execution_time=self.timeout
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data={"target": target, "vulnerabilities": []},
                error=f"执行错误: {str(e)}",
                execution_mode="real",
                execution_time=time.time() - start_time
            )


class MockNucleiAdapter(ToolAdapter):
    """Nuclei模拟适配器（真实实现需要安装nuclei）"""
    
    def __init__(self):
        super().__init__("nuclei", "漏洞扫描工具（模拟）")
    
    def _check_availability(self) -> bool:
        """总是返回可用（模拟模式）"""
        self.available = True
        return True
    
    def execute(self, target: str, **kwargs) -> ToolResult:
        """执行模拟nuclei扫描"""
        start_time = time.time()
        
        try:
            # 模拟扫描结果
            vulnerabilities = []
            
            # 根据目标生成不同的模拟漏洞
            if "wordpress" in target.lower():
                vulnerabilities = [
                    {"name": "WordPress XSS Vulnerability", "severity": "medium", "cve": "CVE-2023-1234"},
                    {"name": "WordPress RCE via Plugin", "severity": "critical", "cve": "CVE-2023-5678"}
                ]
            elif "joomla" in target.lower():
                vulnerabilities = [
                    {"name": "Joomla SQL Injection", "severity": "high", "cve": "CVE-2022-1234"},
                    {"name": "Joomla File Upload", "severity": "critical", "cve": "CVE-2022-5678"}
                ]
            else:
                vulnerabilities = [
                    {"name": "Generic XSS Vulnerability", "severity": "low", "cve": None},
                    {"name": "Information Disclosure", "severity": "medium", "cve": None}
                ]
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "vulnerabilities": vulnerabilities,
                    "scan_type": "模拟漏洞扫描"
                },
                error=None,
                execution_mode="simulated",
                raw_output="模拟模式：未执行真实nuclei扫描",
                execution_time=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data={"target": target, "vulnerabilities": []},
                error=f"模拟执行错误: {str(e)}",
                execution_mode="simulated",
                execution_time=time.time() - start_time
            )


def create_default_registry() -> ToolRegistry:
    """创建默认工具注册表"""
    registry = ToolRegistry()
    
    # 注册真实工具适配器
    registry.register(NmapAdapter())
    registry.register(WhatWebAdapter())
    
    # 尝试注册Sqlmap适配器
    sqlmap_adapter = SqlmapAdapter()
    if sqlmap_adapter.available:
        registry.register(sqlmap_adapter)
    
    # 尝试注册Wafw00f适配器
    wafw00f_adapter = Wafw00fAdapter()
    if wafw00f_adapter.available:
        registry.register(wafw00f_adapter)
    
    # 尝试注册Nuclei适配器，如果不可用则使用模拟版本
    nuclei_adapter = NucleiAdapter()
    if nuclei_adapter.available:
        registry.register(nuclei_adapter)
    else:
        # 使用模拟版本
        registry.register(MockNucleiAdapter())
    
    return registry
