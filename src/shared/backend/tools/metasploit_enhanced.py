# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强版Metasploit工具模块
整合metasploit_integration.py和metasploit.py的功能
基于BaseTool框架，支持真实执行与模拟执行的自动切换
"""

import subprocess
import json
import re
import sys
import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 导入工具基类
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.tools.base_tool import (
    BaseTool, ToolExecutionMode, ToolCategory, 
    ToolPriority, ToolExecutionResult, register_tool
)

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


@register_tool
class MetasploitEnhancedTool(BaseTool):
    """增强版Metasploit工具类"""
    
    def __init__(self):
        super().__init__(
            tool_name="metasploit_enhanced",
            command="msfconsole",
            description="渗透测试框架（增强版）",
            category=ToolCategory.POST_EXPLOITATION,
            priority=ToolPriority.CRITICAL,
            requires_installation=True,
            fallback_to_simulated=True
        )
        
        self.docker_mode = True
        self.container_name = "clawai-metasploit"
        self.docker_image = "metasploitframework/metasploit-framework:latest"
        self.msfconsole_path = self._find_msfconsole()
        
        if self.msfconsole_path:
            logger.info(f"找到本地Metasploit: {self.msfconsole_path}")
            self.docker_mode = False
        else:
            logger.info("未找到本地Metasploit，将使用Docker模式")
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
    
    def check_installation(self) -> Tuple[bool, str]:
        """检查Metasploit安装状态"""
        if self.docker_mode:
            # 检查Docker是否可用
            try:
                subprocess.run(["docker", "--version"], capture_output=True, check=True)
                return True, "Docker可用，Metasploit可通过Docker运行"
            except:
                return False, "Docker不可用，无法运行Metasploit"
        else:
            # 检查本地安装
            if self.msfconsole_path and os.path.exists(self.msfconsole_path):
                return True, f"本地Metasploit已安装: {self.msfconsole_path}"
            else:
                return False, "本地Metasploit未安装"
    
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
                    "-p", "55553:55553",  # MSF RPC API
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
    
    def run(self, target: str = None, **kwargs) -> Dict[str, Any]:
        """
        运行Metasploit工具（BaseTool接口实现）
        
        Args:
            target: 目标地址
            **kwargs: 额外参数
            
        Returns:
            执行结果字典
        """
        # 默认执行搜索命令
        command = kwargs.get("command", "search")
        result = self.execute(command, target, **kwargs)
        
        # 转换为字典格式
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error_message,
            "execution_mode": result.execution_mode.value,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
    
    def execute(self, command: str, target: str = None, **kwargs) -> ToolExecutionResult:
        """
        执行Metasploit命令
        
        Args:
            command: 命令类型 (search, exploit, auxiliary, sessions, post)
            target: 目标地址
            **kwargs: 额外参数
            
        Returns:
            工具执行结果
        """
        try:
            # 检查安装状态
            installed, message = self.check_installation()
            if not installed:
                return self._simulate_execution(command, target, **kwargs)
            
            # 根据命令类型执行
            if command == "search":
                return self._execute_search(kwargs.get("search_term", ""))
            elif command == "exploit":
                return self._execute_exploit(target, kwargs.get("module", ""), kwargs.get("options", {}))
            elif command == "auxiliary":
                return self._execute_auxiliary(target, kwargs.get("module", ""), kwargs.get("options", {}))
            elif command == "sessions":
                return self._execute_sessions()
            elif command == "post":
                return self._execute_post(kwargs.get("session_id", ""), kwargs.get("module", ""), kwargs.get("options", {}))
            else:
                return ToolExecutionResult(
                    success=False,
                    output="",
                    error=f"未知命令: {command}",
                    execution_mode=ToolExecutionMode.ERROR,
                    execution_time=0.0
                )
                
        except Exception as e:
            logger.error(f"Metasploit执行失败: {e}")
            return self._simulate_execution(command, target, **kwargs)
    
    def _execute_search(self, search_term: str) -> ToolExecutionResult:
        """执行搜索命令"""
        start_time = time.time()
        
        if not search_term:
            search_term = "type:exploit"
        
        command = f"search {search_term}"
        result = self.execute_msf_command(command, timeout=60)
        
        if result["success"]:
            # 解析搜索结果
            modules = self._parse_search_results(result["output"])
            
            return ToolExecutionResult(
                success=True,
                output=json.dumps({"modules": modules}, ensure_ascii=False, indent=2),
                error_message=result["error"],
                execution_mode=ToolExecutionMode.REAL,
                execution_time=time.time() - start_time,
                metadata={
                    "module_count": len(modules),
                    "search_term": search_term
                }
            )
        else:
            return self._simulate_search(search_term)
    
    def _execute_exploit(self, target: str, module: str, options: Dict[str, Any]) -> ToolExecutionResult:
        """执行漏洞利用命令"""
        start_time = time.time()
        
        if not target or not module:
            return ToolExecutionResult(
                success=False,
                output="",
                error="需要提供目标地址和模块名称",
                execution_mode=ToolExecutionMode.ERROR,
                execution_time=time.time() - start_time
            )
        
        # 构建命令序列
        commands = [
            f"use {module}",
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
        result = self.execute_msf_command(full_command, timeout=120)
        
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
            
            return ToolExecutionResult(
                success=success,
                output=output,
                error_message=result["error"],
                execution_mode=ToolExecutionMode.REAL,
                execution_time=time.time() - start_time,
                metadata={
                    "session_id": session_id,
                    "module": module,
                    "target": target
                }
            )
        else:
            return self._simulate_exploit(target, module, options)
    
    def _execute_auxiliary(self, target: str, module: str, options: Dict[str, Any]) -> ToolExecutionResult:
        """执行辅助模块命令"""
        start_time = time.time()
        
        if not target or not module:
            return ToolExecutionResult(
                success=False,
                output="",
                error="需要提供目标地址和模块名称",
                execution_mode=ToolExecutionMode.ERROR,
                execution_time=time.time() - start_time
            )
        
        commands = [
            f"use {module}",
            f"set RHOSTS {target}",
        ]
        
        # 添加额外选项
        for key, value in options.items():
            if key not in ["RHOSTS"]:
                commands.append(f"set {key} {value}")
        
        commands.append("run")
        full_command = "; ".join(commands)
        
        result = self.execute_msf_command(full_command, timeout=120)
        
        if result["success"]:
            return ToolExecutionResult(
                success=True,
                output=result["output"],
                error=result["error"],
                execution_mode=ToolExecutionMode.REAL,
                execution_time=time.time() - start_time,
                metadata={
                    "module": module,
                    "target": target
                }
            )
        else:
            return self._simulate_auxiliary(target, module, options)
    
    def _execute_sessions(self) -> ToolExecutionResult:
        """获取会话列表"""
        start_time = time.time()
        
        result = self.execute_msf_command("sessions", timeout=30)
        
        if result["success"]:
            sessions = self._parse_sessions(result["output"])
            
            return ToolExecutionResult(
                success=True,
                output=json.dumps({"sessions": sessions}, ensure_ascii=False, indent=2),
                error=result["error"],
                execution_mode=ToolExecutionMode.REAL,
                execution_time=time.time() - start_time,
                metadata={
                    "session_count": len(sessions)
                }
            )
        else:
            return self._simulate_sessions()
    
    def _execute_post(self, session_id: str, module: str, options: Dict[str, Any]) -> ToolExecutionResult:
        """执行后渗透模块"""
        start_time = time.time()
        
        if not session_id or not module:
            return ToolExecutionResult(
                success=False,
                output="",
                error="需要提供会话ID和模块名称",
                execution_mode=ToolExecutionMode.ERROR,
                execution_time=time.time() - start_time
            )
        
        commands = [
            f"use {module}",
            f"set SESSION {session_id}",
        ]
        
        # 添加额外选项
        for key, value in options.items():
            if key not in ["SESSION"]:
                commands.append(f"set {key} {value}")
        
        commands.append("run")
        full_command = "; ".join(commands)
        
        result = self.execute_msf_command(full_command, timeout=60)
        
        if result["success"]:
            return ToolExecutionResult(
                success=True,
                output=result["output"],
                error=result["error"],
                execution_mode=ToolExecutionMode.REAL,
                execution_time=time.time() - start_time,
                metadata={
                    "session_id": session_id,
                    "module": module
                }
            )
        else:
            return self._simulate_post(session_id, module, options)
    
    def _parse_search_results(self, output: str) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        modules = []
        lines = output.split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('=') and not line.startswith('Name'):
                parts = line.split()
                if len(parts) >= 3:
                    modules.append({
                        "name": parts[0],
                        "disclosure_date": parts[1] if len(parts) > 1 else "",
                        "rank": parts[2] if len(parts) > 2 else "",
                        "description": " ".join(parts[3:]) if len(parts) > 3 else ""
                    })
        
        return modules
    
    def _parse_sessions(self, output: str) -> List[Dict[str, Any]]:
        """解析会话列表"""
        sessions = []
        lines = output.split('\n')
        
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
    
    def _simulate_execution(self, command: str, target: str = None, **kwargs) -> ToolExecutionResult:
        """模拟执行（当真实执行不可用时）"""
        start_time = time.time()
        
        if command == "search":
            return self._simulate_search(kwargs.get("search_term", ""))
        elif command == "exploit":
            return self._simulate_exploit(target, kwargs.get("module", ""), kwargs.get("options", {}))
        elif command == "auxiliary":
            return self._simulate_auxiliary(target, kwargs.get("module", ""), kwargs.get("options", {}))
        elif command == "sessions":
            return self._simulate_sessions()
        elif command == "post":
            return self._simulate_post(kwargs.get("session_id", ""), kwargs.get("module", ""), kwargs.get("options", {}))
        else:
            return ToolExecutionResult(
                success=False,
                output="",
                error=f"未知命令: {command}",
                execution_mode=ToolExecutionMode.ERROR,
                execution_time=time.time() - start_time
            )
    
    def _simulate_search(self, search_term: str) -> ToolExecutionResult:
        """模拟搜索命令"""
        start_time = time.time()
        
        # 模拟搜索结果
        modules = [
            {
                "name": "exploit/windows/smb/ms17_010_eternalblue",
                "disclosure_date": "2017-03-14",
                "rank": "excellent",
                "description": "MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption"
            },
            {
                "name": "exploit/multi/http/apache_struts2_rest_xstream",
                "disclosure_date": "2017-03-07",
                "rank": "excellent",
                "description": "Apache Struts2 REST Plugin XStream RCE"
            },
            {
                "name": "exploit/multi/http/apache_struts2_namespace_ognl",
                "disclosure_date": "2018-08-22",
                "rank": "excellent",
                "description": "Apache Struts2 Namespace OGNL Injection"
            }
        ]
        
        return ToolExecutionResult(
            success=True,
            output=json.dumps({"modules": modules}, ensure_ascii=False, indent=2),
            error_message="",
            execution_mode=ToolExecutionMode.SIMULATED,
            execution_time=time.time() - start_time,
            metadata={
                "module_count": len(modules),
                "search_term": search_term,
                "note": "模拟结果 - 实际需要安装Metasploit"
            }
        )
    
    def _simulate_exploit(self, target: str, module: str, options: Dict[str, Any]) -> ToolExecutionResult:
        """模拟漏洞利用命令"""
        start_time = time.time()
        
        # 模拟利用结果
        success = random.random() > 0.3  # 70%成功率
        session_id = str(random.randint(1, 100)) if success else None
        
        output = f"""
[*] Started reverse TCP handler on 0.0.0.0:4444 
[*] {target}:445 - Using auxiliary/scanner/smb/smb_ms17_010 as check
[+] {target}:445 - Host is likely VULNERABLE to MS17-010! - Windows 7 Professional 7601 Service Pack 1 x64 (64-bit)
[*] {target}:445 - Scanned 1 of 1 hosts (100% complete)
[*] {target}:445 - Connecting to target for exploitation.
[+] {target}:445 - Connection established for exploitation.
[+] {target}:445 - Target OS selected valid for OS indicated by SMB reply
[*] {target}:445 - CORE raw buffer dump (42 bytes)
[*] {target}:445 - 0x00000000  57 69 6e 64 6f 77 73 20 37 20 50 72 6f 66 65 73  Windows 7 Profes
[*] {target}:445 - 0x00000010  73 69 6f 6e 61 6c 20 37 36 30 31 20 53 65 72 76  sional 7601 Serv
[*] {target}:445 - 0x00000020  69 63 65 20 50 61 63 6b 20 31                    ice Pack 1      
[+] {target}:445 - Target arch selected valid for arch indicated by DCE/RPC reply
[*] {target}:445 - Trying exploit with 12 Groom Allocations.
[*] {target}:445 - Sending all but last fragment of exploit packet
[*] {target}:445 - Starting non-paged pool grooming
[+] {target}:445 - Sending SMBv2 buffers
[+] {target}:445 - Closing SMBv1 connection creating free hole adjacent to SMBv2 buffer.
[*] {target}:445 - Sending final SMBv2 buffers.
[*] {target}:445 - Sending last fragment of exploit packet!
[*] {target}:445 - Receiving response from exploit packet
"""
        
        if success:
            output += f"\n[+] {target}:445 - ETERNALBLUE overwrite completed successfully (0xC000000D)!\n"
            output += f"[*] {target}:445 - Sending egg to corrupted connection.\n"
            output += f"[*] {target}:445 - Triggering free of corrupted buffer.\n"
            output += f"[*] Command shell session {session_id} opened (192.168.1.100:4444 -> {target}:49158) at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            output += f"\n[-] {target}:445 - Exploit failed: Target not vulnerable or patched\n"
        
        return ToolExecutionResult(
            success=success,
            output=output,
            error="",
            execution_mode=ToolExecutionMode.SIMULATED,
            execution_time=time.time() - start_time,
            metadata={
                "session_id": session_id,
                "module": module,
                "target": target,
                "note": "模拟结果 - 实际需要安装Metasploit"
            }
        )
    
    def _simulate_auxiliary(self, target: str, module: str, options: Dict[str, Any]) -> ToolExecutionResult:
        """模拟辅助模块命令"""
        start_time = time.time()
        
        output = f"""
[*] Scanning {target}...
[+] Port 80/tcp open  http    Apache httpd 2.4.41
[+] Port 443/tcp open  ssl/http Apache httpd 2.4.41
[+] Port 22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5
[+] Port 3389/tcp open  ms-wbt-server Microsoft Terminal Services
[+] Found 4 open ports on {target}
[+] Service detection complete
[+] HTTP Title: Test Server
[+] SSL Certificate: CN=test.com
"""
        
        return ToolExecutionResult(
            success=True,
            output=output,
            error="",
            execution_mode=ToolExecutionMode.SIMULATED,
            execution_time=time.time() - start_time,
            metadata={
                "module": module,
                "target": target,
                "note": "模拟结果 - 实际需要安装Metasploit"
            }
        )
    
    def _simulate_sessions(self) -> ToolExecutionResult:
        """模拟会话列表"""
        start_time = time.time()
        
        sessions = [
            {
                "id": "1",
                "type": "meterpreter",
                "info": "x64/windows",
                "address": "192.168.1.100:4444",
                "payload": "windows/x64/meterpreter/reverse_tcp"
            },
            {
                "id": "2",
                "type": "shell",
                "info": "cmd/unix",
                "address": "10.0.0.5:4444",
                "payload": "cmd/unix/reverse_bash"
            }
        ]
        
        return ToolExecutionResult(
            success=True,
            output=json.dumps({"sessions": sessions}, ensure_ascii=False, indent=2),
            error="",
            execution_mode=ToolExecutionMode.SIMULATED,
            execution_time=time.time() - start_time,
            metadata={
                "session_count": len(sessions),
                "note": "模拟结果 - 实际需要安装Metasploit"
            }
        )
    
    def _simulate_post(self, session_id: str, module: str, options: Dict[str, Any]) -> ToolExecutionResult:
        """模拟后渗透模块"""
        start_time = time.time()
        
        output = f"""
[*] Running module against session {session_id}
[+] Session {session_id} is a Meterpreter session
[+] Gathering system info...
[+] OS: Windows 10 Professional (build 19044)
[+] Architecture: x64
[+] Current user: Administrator
[+] Is admin: Yes
[+] UAC enabled: No
[+] Gathering network info...
[+] IP addresses: 192.168.1.100, 10.0.0.5
[+] Gathering process list...
[+] Found 45 running processes
[+] Gathering installed software...
[+] Found 32 installed applications
"""
        
        return ToolExecutionResult(
            success=True,
            output=output,
            error="",
            execution_mode=ToolExecutionMode.SIMULATED,
            execution_time=time.time() - start_time,
            metadata={
                "session_id": session_id,
                "module": module,
                "note": "模拟结果 - 实际需要安装Metasploit"
            }
        )


# 测试函数
def test_metasploit_enhanced():
    """测试增强版Metasploit工具"""
    print("测试增强版Metasploit工具...")
    
    # 创建工具实例
    tool = MetasploitEnhancedTool()
    
    # 检查安装状态
    installed, message = tool.check_installation()
    print(f"安装状态: {installed} - {message}")
    
    # 测试搜索功能
    print("\n测试搜索功能...")
    result = tool.execute("search", search_term="eternalblue")
    print(f"搜索成功: {result.success}")
    print(f"执行模式: {result.execution_mode}")
    print(f"模块数量: {result.metadata.get('module_count', 0)}")
    
    # 测试模拟利用
    print("\n测试模拟利用功能...")
    result = tool.execute("exploit", target="192.168.1.100", module="exploit/windows/smb/ms17_010_eternalblue")
    print(f"利用成功: {result.success}")
    print(f"会话ID: {result.metadata.get('session_id', '无')}")
    
    # 测试会话列表
    print("\n测试会话列表功能...")
    result = tool.execute("sessions")
    print(f"获取会话成功: {result.success}")
    print(f"会话数量: {result.metadata.get('session_count', 0)}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    import random
    test_metasploit_enhanced()
