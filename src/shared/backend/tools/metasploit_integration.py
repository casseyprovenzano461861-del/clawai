#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metasploit集成模块
提供Metasploit框架的基本集成功能
"""

import subprocess
import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MetasploitModuleType(Enum):
    """Metasploit模块类型"""
    EXPLOIT = "exploit"
    AUXILIARY = "auxiliary"
    POST = "post"
    PAYLOAD = "payload"
    ENCODER = "encoder"
    NOP = "nop"


@dataclass
class MetasploitModule:
    """Metasploit模块信息"""
    name: str
    fullname: str
    type: MetasploitModuleType
    description: str
    rank: str
    disclosure_date: Optional[str] = None
    platform: Optional[List[str]] = None
    author: Optional[List[str]] = None
    references: Optional[List[Dict[str, str]]] = None


@dataclass
class ExploitResult:
    """漏洞利用结果"""
    success: bool
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    output: Optional[str] = None
    payload_info: Optional[Dict[str, Any]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class MetasploitIntegration:
    """Metasploit集成类"""
    
    def __init__(self, docker_mode: bool = True, container_name: str = "clawai-metasploit"):
        """
        初始化Metasploit集成
        
        Args:
            docker_mode: 是否使用Docker模式
            container_name: Docker容器名称
        """
        self.docker_mode = docker_mode
        self.container_name = container_name
        self.msfconsole_path = self._find_msfconsole()
        
        if self.msfconsole_path:
            logger.info(f"找到Metasploit: {self.msfconsole_path}")
        else:
            logger.warning("未找到本地Metasploit安装，将使用Docker模式")
            self.docker_mode = True
    
    def _find_msfconsole(self) -> Optional[str]:
        """查找msfconsole可执行文件"""
        # 常见安装路径
        common_paths = [
            "/usr/bin/msfconsole",
            "/opt/metasploit-framework/bin/msfconsole",
            "C:\\metasploit-framework\\bin\\msfconsole.bat",
            "C:\\Program Files\\Metasploit\\bin\\msfconsole.bat",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # 尝试在PATH中查找
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(["where", "msfconsole"], 
                                      capture_output=True, text=True)
            else:  # Linux/Mac
                result = subprocess.run(["which", "msfconsole"], 
                                      capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def start_docker_container(self) -> bool:
        """启动Metasploit Docker容器"""
        if not self.docker_mode:
            return False
        
        try:
            # 检查Docker是否安装
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            
            # 检查容器是否已存在
            check_cmd = ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if self.container_name in result.stdout:
                # 启动已存在的容器
                logger.info(f"启动已存在的容器: {self.container_name}")
                subprocess.run(["docker", "start", self.container_name], check=True)
            else:
                # 创建新容器
                logger.info(f"创建新的Metasploit容器: {self.container_name}")
                cmd = [
                    "docker", "run", "-d",
                    "--name", self.container_name,
                    "-p", "4444:4444",  # 用于反向shell
                    "-p", "8080:8080",  # 用于Web服务
                    "--restart", "unless-stopped",
                    "metasploitframework/metasploit-framework:latest"
                ]
                subprocess.run(cmd, check=True)
            
            # 等待容器启动
            time.sleep(5)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"启动Docker容器失败: {e}")
            return False
        except FileNotFoundError:
            logger.error("Docker未安装")
            return False
    
    def execute_msf_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        执行Metasploit命令
        
        Args:
            command: msfconsole命令
            timeout: 超时时间（秒）
            
        Returns:
            执行结果
        """
        try:
            if self.docker_mode:
                # 在Docker容器中执行命令
                docker_cmd = ["docker", "exec", "-i", self.container_name, "msfconsole", "-q", "-x", command]
                result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            else:
                # 本地执行
                cmd = [self.msfconsole_path, "-q", "-x", command]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"命令执行超时 ({timeout}秒)",
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    def search_exploits(self, search_term: str) -> List[Dict[str, Any]]:
        """
        搜索漏洞利用模块
        
        Args:
            search_term: 搜索关键词
            
        Returns:
            漏洞利用模块列表
        """
        command = f"search name:{search_term} type:exploit"
        result = self.execute_msf_command(command)
        
        if not result["success"]:
            return []
        
        # 解析搜索结果
        exploits = []
        lines = result["output"].split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('=') and not line.startswith('Name'):
                parts = line.split()
                if len(parts) >= 3:
                    exploits.append({
                        "name": parts[0],
                        "disclosure_date": parts[1] if len(parts) > 1 else "",
                        "rank": parts[2] if len(parts) > 2 else "",
                        "description": " ".join(parts[3:]) if len(parts) > 3 else ""
                    })
        
        return exploits
    
    def run_exploit(self, exploit_name: str, target: str, 
                   options: Dict[str, Any] = None) -> ExploitResult:
        """
        运行漏洞利用模块
        
        Args:
            exploit_name: 漏洞利用模块名称
            target: 目标地址
            options: 额外选项
            
        Returns:
            利用结果
        """
        if options is None:
            options = {}
        
        try:
            # 构建命令序列
            commands = [
                f"use {exploit_name}",
                f"set RHOSTS {target}",
            ]
            
            # 添加额外选项
            for key, value in options.items():
                if key not in ["RHOSTS"]:  # 避免重复设置
                    commands.append(f"set {key} {value}")
            
            # 默认设置
            if "RPORT" not in options:
                commands.append("set RPORT 80")
            
            # 执行利用
            commands.append("run")
            
            # 执行所有命令
            full_command = "; ".join(commands)
            result = self.execute_msf_command(full_command, timeout=60)
            
            if result["success"]:
                output = result["output"]
                
                # 检查是否成功建立会话
                session_id = None
                if "Session" in output and "opened" in output:
                    # 尝试提取会话ID
                    for line in output.split('\n'):
                        if "Session" in line and "opened" in line:
                            parts = line.split()
                            for part in parts:
                                if part.isdigit():
                                    session_id = part
                                    break
                
                success = session_id is not None or "succeeded" in output.lower()
                
                return ExploitResult(
                    success=success,
                    session_id=session_id,
                    output=output,
                    timestamp=time.time()
                )
            else:
                return ExploitResult(
                    success=False,
                    error_message=result["error"],
                    output=result["output"],
                    timestamp=time.time()
                )
                
        except Exception as e:
            return ExploitResult(
                success=False,
                error_message=str(e),
                timestamp=time.time()
            )
    
    def run_auxiliary_module(self, module_name: str, target: str,
                           options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        运行辅助模块（扫描、信息收集等）
        
        Args:
            module_name: 模块名称
            target: 目标地址
            options: 额外选项
            
        Returns:
            执行结果
        """
        if options is None:
            options = {}
        
        commands = [
            f"use {module_name}",
            f"set RHOSTS {target}",
        ]
        
        # 添加额外选项
        for key, value in options.items():
            if key not in ["RHOSTS"]:
                commands.append(f"set {key} {value}")
        
        commands.append("run")
        full_command = "; ".join(commands)
        
        result = self.execute_msf_command(full_command, timeout=120)
        
        return {
            "success": result["success"],
            "output": result["output"],
            "error": result["error"],
            "module": module_name,
            "target": target
        }
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取当前活动会话"""
        result = self.execute_msf_command("sessions")
        
        if not result["success"]:
            return []
        
        sessions = []
        lines = result["output"].split('\n')
        
        for line in lines:
            if line.strip() and line[0].isdigit():
                parts = line.split()
                if len(parts) >= 4:
                    sessions.append({
                        "id": parts[0],
                        "type": parts[1],
                        "info": parts[2],
                        "address": parts[3] if len(parts) > 3 else "",
                        "payload": parts[4] if len(parts) > 4 else ""
                    })
        
        return sessions
    
    def interact_with_session(self, session_id: str, command: str = None) -> Dict[str, Any]:
        """
        与会话交互
        
        Args:
            session_id: 会话ID
            command: 要执行的命令（如果为None则进入交互模式）
            
        Returns:
            交互结果
        """
        if command:
            # 执行单个命令
            msf_command = f"sessions -i {session_id} -c '{command}'"
            result = self.execute_msf_command(msf_command, timeout=30)
            
            return {
                "success": result["success"],
                "output": result["output"],
                "error": result["error"],
                "session_id": session_id,
                "command": command
            }
        else:
            # 进入交互模式（简化实现）
            msf_command = f"sessions -i {session_id}"
            result = self.execute_msf_command(msf_command, timeout=10)
            
            return {
                "success": result["success"],
                "output": result["output"],
                "error": result["error"],
                "session_id": session_id,
                "interactive": True
            }
    
    def run_post_exploitation(self, session_id: str, module_name: str,
                            options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        运行后渗透模块
        
        Args:
            session_id: 会话ID
            module_name: 后渗透模块名称
            options: 额外选项
            
        Returns:
            执行结果
        """
        if options is None:
            options = {}
        
        commands = [
            f"use {module_name}",
            f"set SESSION {session_id}",
        ]
        
        # 添加额外选项
        for key, value in options.items():
            if key not in ["SESSION"]:
                commands.append(f"set {key} {value}")
        
        commands.append("run")
        full_command = "; ".join(commands)
        
        result = self.execute_msf_command(full_command, timeout=60)
        
        return {
            "success": result["success"],
            "output": result["output"],
            "error": result["error"],
            "session_id": session_id,
            "module": module_name
        }


# 简化版本 - 用于快速集成
class SimpleMetasploitClient:
    """简化版Metasploit客户端"""
    
    @staticmethod
    def check_metasploit_availability() -> Dict[str, Any]:
        """检查Metasploit可用性"""
        try:
            # 尝试执行简单命令
            cmd = ["msfconsole", "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            available = result.returncode == 0 or "Framework" in result.stdout
            
            return {
                "available": available,
                "version": result.stdout.strip() if available else None,
                "docker_required": not available
            }
        except:
            return {
                "available": False,
                "version": None,
                "docker_required": True
            }
    
    @staticmethod
    def run_quick_scan(target: str) -> Dict[str, Any]:
        """快速扫描目标"""
        # 这是一个简化实现，实际应该调用Metasploit模块
        return {
            "success": True,
            "scan_type": "metasploit_quick_scan",
            "target": target,
            "results": {
                "ports": [80, 443, 22, 3389],
                "services": {
                    "80": "http",
                    "443": "https",
                    "22": "ssh",
                    "3389": "rdp"
                },
                "vulnerabilities": [
                    {"port": 80, "service": "http", "vuln": "可能的Web漏洞"},
                    {"port": 3389, "service": "rdp", "vuln": "可能的RDP漏洞"}
                ]
            },
            "timestamp": time.time(),
            "note": "这是Metasploit扫描的模拟结果，实际需要安装Metasploit"
        }


# 测试函数
def test_metasploit_integration():
    """测试Metasploit集成"""
    print("测试Metasploit集成...")
    
    # 检查可用性
    availability = SimpleMetasploitClient.check_metasploit_availability()
    print(f"Metasploit可用性: {availability}")
    
    if availability["available"]:
        # 创建集成实例
        msf = MetasploitIntegration(docker_mode=False)
        
        # 搜索漏洞
        exploits = msf.search_exploits("eternalblue")
        print(f"找到EternalBlue漏洞: {len(exploits)}个")
        
        if exploits:
            for exploit in exploits[:3]:
                print(f"  - {exploit['name']}: {exploit['description']}")
    else:
        print("Metasploit不可用，建议使用Docker安装")
        print("安装命令: docker pull metasploitframework/metasploit-framework")
        
        # 模拟扫描
        scan_result = SimpleMetasploitClient.run_quick_scan("example.com")
        print(f"模拟扫描结果: {scan_result}")


if __name__ == "__main__":
    test_metasploit_integration()