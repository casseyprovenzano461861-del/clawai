"""
工具管理器 - 借鉴CyberStrikeAI的工具管理方式
统一管理所有安全工具的执行和配置
"""

import os
import json
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

# 安全模块导入
try:
    from ..security.sanitize import safe_execute, SecurityError, filter_sensitive_data
except ImportError:
    # 回退方案，如果安全模块不可用
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from backend.security.sanitize import safe_execute, SecurityError, filter_sensitive_data

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """工具状态枚举"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"


class ToolCategory(Enum):
    """工具分类枚举"""
    RECON = "reconnaissance"  # 侦察
    SCANNING = "scanning"  # 扫描
    EXPLOITATION = "exploitation"  # 利用
    POST_EXPLOITATION = "post_exploitation"  # 后渗透
    REPORTING = "reporting"  # 报告


@dataclass
class ToolConfig:
    """工具配置类"""
    name: str
    description: str
    command: str
    category: ToolCategory
    required: bool = False
    timeout: int = 300  # 默认5分钟
    output_format: str = "text"  # text, json, xml
    parameters: Dict[str, Any] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.dependencies is None:
            self.dependencies = []


class ToolManager:
    """工具管理器"""
    
    def __init__(self, tools_dir: str = "./tools"):
        self.tools_dir = tools_dir
        self.tools: Dict[str, ToolConfig] = {}
        self.tool_status: Dict[str, ToolStatus] = {}
        self.load_tools()
        
    def load_tools(self):
        """加载工具配置"""
        # 从配置文件加载工具
        tools_config = self._load_tools_config()
        
        for tool_name, config in tools_config.items():
            try:
                tool_config = ToolConfig(
                    name=tool_name,
                    description=config.get("description", ""),
                    command=config.get("command", tool_name),
                    category=ToolCategory(config.get("category", "reconnaissance")),
                    required=config.get("required", False),
                    timeout=config.get("timeout", 300),
                    output_format=config.get("output_format", "text"),
                    parameters=config.get("parameters", {}),
                    dependencies=config.get("dependencies", [])
                )
                self.tools[tool_name] = tool_config
                self._check_tool_availability(tool_name)
                logger.info(f"加载工具: {tool_name} - {self.tool_status[tool_name].value}")
            except Exception as e:
                logger.error(f"加载工具 {tool_name} 失败: {e}")
                self.tool_status[tool_name] = ToolStatus.UNAVAILABLE
    
    def _load_tools_config(self) -> Dict[str, Any]:
        """加载工具配置文件"""
        config_path = os.path.join(self.tools_dir, "tools.json")
        
        # 如果配置文件不存在，使用默认配置
        if not os.path.exists(config_path):
            return self._get_default_tools_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载工具配置文件失败: {e}")
            return self._get_default_tools_config()
    
    def _get_default_tools_config(self) -> Dict[str, Any]:
        """获取默认工具配置"""
        return {
            "nmap": {
                "description": "网络扫描工具",
                "command": "nmap",
                "category": "reconnaissance",
                "required": True,
                "timeout": 600,
                "output_format": "xml",
                "parameters": {
                    "ports": "1-1000",
                    "scripts": "default"
                }
            },
            "sqlmap": {
                "description": "SQL注入检测工具",
                "command": "python sqlmap.py",
                "category": "exploitation",
                "required": True,
                "timeout": 900,
                "output_format": "text",
                "parameters": {
                    "risk": 3,
                    "level": 5
                }
            },
            "nikto": {
                "description": "Web服务器扫描工具",
                "command": "nikto.pl",
                "category": "scanning",
                "required": False,
                "timeout": 300,
                "output_format": "text"
            },
            "dirsearch": {
                "description": "Web路径扫描工具",
                "command": "python dirsearch.py",
                "category": "scanning",
                "required": False,
                "timeout": 600,
                "output_format": "text"
            }
        }
    
    def _check_tool_availability(self, tool_name: str):
        """检查工具是否可用"""
        tool_config = self.tools.get(tool_name)
        if not tool_config:
            self.tool_status[tool_name] = ToolStatus.UNAVAILABLE
            return
        
        try:
            # 检查命令是否在PATH中
            if shutil.which(tool_config.command.split()[0]):
                self.tool_status[tool_name] = ToolStatus.AVAILABLE
            else:
                self.tool_status[tool_name] = ToolStatus.NOT_INSTALLED
        except Exception:
            self.tool_status[tool_name] = ToolStatus.UNAVAILABLE
    
    def execute_tool(self, tool_name: str, target: str, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"工具 {tool_name} 未配置"
            }
        
        if self.tool_status.get(tool_name) != ToolStatus.AVAILABLE:
            return {
                "success": False,
                "error": f"工具 {tool_name} 不可用，状态: {self.tool_status.get(tool_name)}"
            }
        
        tool_config = self.tools[tool_name]
        
        try:
            # 构建命令
            command = self._build_command(tool_config, target, kwargs)
            
            # 创建临时目录存储输出
            with tempfile.TemporaryDirectory() as tmpdir:
                output_file = os.path.join(tmpdir, "output.txt")
                
                # 执行命令（安全版本）
                returncode, stdout, stderr = safe_execute(
                    command,
                    timeout=tool_config.timeout,
                    cwd=tmpdir
                )
                
                # 解析输出
                output = self._parse_output(stdout, tool_config.output_format)

                return {
                    "success": True,
                    "tool": tool_name,
                    "target": target,
                    "command": command,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": returncode,
                    "output": output,
                    "execution_time": 0  # 可以添加计时功能
                }
                
        except TimeoutError:
            return {
                "success": False,
                "error": f"工具 {tool_name} 执行超时 ({tool_config.timeout}秒)"
            }
        except SecurityError as e:
            return {
                "success": False,
                "error": f"工具 {tool_name} 安全违规: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"工具 {tool_name} 执行失败: {str(e)}"
            }
    
    def _build_command(self, tool_config: ToolConfig, target: str, params: Dict[str, Any]) -> List[str]:
        """构建命令参数列表（安全版本）"""
        # 分割基础命令
        cmd_parts = tool_config.command.split()

        # 验证命令名称
        if not cmd_parts:
            raise SecurityError(f"无效的命令: {tool_config.command}")

        # 添加目标参数（替换占位符）
        cmd_args = []
        for part in cmd_parts:
            if "{target}" in part:
                # 安全验证目标
                if not target or ';' in target or '&' in target or '|' in target:
                    raise SecurityError(f"无效的目标地址: {target}")
                cmd_args.append(part.replace("{target}", target))
            else:
                cmd_args.append(part)

        # 添加用户参数
        for key, value in params.items():
            if isinstance(value, bool) and value:
                cmd_args.append(f"--{key}")
            elif isinstance(value, (int, float)):
                cmd_args.append(f"--{key}")
                cmd_args.append(str(value))
            elif isinstance(value, str):
                # 验证字符串参数
                if ';' in value or '&' in value or '|' in value or '$' in value:
                    logger.warning(f"参数包含潜在危险字符: {key}={value}")
                cmd_args.append(f"--{key}")
                cmd_args.append(value)

        # 添加默认参数
        for key, value in tool_config.parameters.items():
            if key not in params:
                if isinstance(value, bool) and value:
                    cmd_args.append(f"--{key}")
                elif isinstance(value, (int, float, str)):
                    cmd_args.append(f"--{key}")
                    if not isinstance(value, bool):
                        cmd_args.append(str(value))

        return cmd_args
    
    def _parse_output(self, stdout: str, output_format: str) -> Any:
        """解析工具输出"""
        if output_format == "json":
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {"raw_output": stdout}
        elif output_format == "xml":
            # 简单处理，返回原始XML
            return {"raw_xml": stdout}
        else:
            # 文本格式，返回原始输出
            return stdout
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools_list = []
        for name, config in self.tools.items():
            tools_list.append({
                "name": name,
                "description": config.description,
                "category": config.category.value,
                "status": self.tool_status.get(name, ToolStatus.UNAVAILABLE).value,
                "required": config.required,
                "command": config.command
            })
        return tools_list
    
    def get_tool_categories(self) -> Dict[str, List[str]]:
        """按分类获取工具"""
        categories = {}
        for category in ToolCategory:
            categories[category.value] = []
        
        for name, config in self.tools.items():
            categories[config.category.value].append(name)
        
        return categories
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        total_tools = len(self.tools)
        available_tools = sum(1 for status in self.tool_status.values() 
                            if status == ToolStatus.AVAILABLE)
        required_tools = sum(1 for tool in self.tools.values() if tool.required)
        available_required = sum(1 for name, tool in self.tools.items() 
                               if tool.required and self.tool_status.get(name) == ToolStatus.AVAILABLE)
        
        return {
            "total_tools": total_tools,
            "available_tools": available_tools,
            "availability_rate": round(available_tools / total_tools * 100, 2) if total_tools > 0 else 0,
            "required_tools": required_tools,
            "available_required_tools": available_required,
            "required_availability_rate": round(available_required / required_tools * 100, 2) if required_tools > 0 else 100,
            "status": "healthy" if available_required == required_tools else "degraded"
        }