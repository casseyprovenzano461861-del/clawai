"""
扩展工具管理器
借鉴 LuaN1aoAgent 的 MCP 工具设计
支持元认知工具、网络工具、执行工具等
"""

import os
import json
import asyncio
import logging
import subprocess
import tempfile
import shutil
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """工具分类"""
    META = "meta"                    # 元认知工具
    CONTROL = "control"              # 控制工具
    INTELLIGENCE = "intelligence"    # 情报收集
    RECONNAISSANCE = "reconnaissance" # 侦察工具
    SCANNING = "scanning"            # 扫描工具
    EXPLOITATION = "exploitation"    # 利用工具
    NETWORK = "network"              # 网络工具
    EXECUTION = "execution"          # 执行工具


class ToolType(Enum):
    """工具类型"""
    BUILTIN = "builtin"      # 内置工具
    EXTERNAL = "external"    # 外部命令工具
    MCP = "mcp"             # MCP协议工具


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    required: bool = False
    default: Any = None
    description: str = ""
    enum: List[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    
    def validate(self, value: Any) -> bool:
        """验证参数值"""
        if value is None:
            return not self.required
        
        # 类型检查
        type_mapping = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_type = type_mapping.get(self.type)
        if expected_type and not isinstance(value, expected_type):
            # 允许整数转浮点等情况
            if self.type == "integer" and isinstance(value, (int, float)):
                pass
            else:
                return False
        
        # 枚举检查
        if self.enum and value not in self.enum:
            return False
        
        # 范围检查
        if self.min is not None and isinstance(value, (int, float)):
            if value < self.min:
                return False
        if self.max is not None and isinstance(value, (int, float)):
            if value > self.max:
                return False
        
        return True


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    category: str
    description: str
    type: str
    enabled: bool = True
    dangerous: bool = False
    command: Optional[str] = None
    parameters: Dict[str, ToolParameter] = field(default_factory=dict)
    return_type: str = "object"
    tags: List[str] = field(default_factory=list)
    security: Dict[str, Any] = field(default_factory=dict)
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的JSON Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    name: {
                        "type": param.type,
                        "description": param.description,
                        **({"enum": param.enum} if param.enum else {}),
                        **({"default": param.default} if param.default is not None else {})
                    }
                    for name, param in self.parameters.items()
                },
                "required": [name for name, param in self.parameters.items() if param.required]
            },
            "returns": self.return_type,
            "tags": self.tags
        }


class ExtendedToolManager:
    """
    扩展工具管理器
    
    功能：
    - 从配置文件加载工具定义
    - 执行内置工具和外部工具
    - 参数验证
    - 安全检查
    - 结果格式化
    """
    
    def __init__(self, config_path: Optional[str] = None, tools_dir: str = "./tools/penetration"):
        """
        初始化扩展工具管理器
        
        Args:
            config_path: 工具配置文件路径
            tools_dir: 外部工具目录
        """
        self.tools_dir = Path(tools_dir)
        self.tools: Dict[str, ToolDefinition] = {}
        
        # HTTP客户端（持久化会话）
        self._http_client = httpx.AsyncClient(verify=False, timeout=30.0)
        
        # 思考历史
        self._think_history: List[Dict[str, Any]] = []
        
        # 加载工具配置
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "tools_extended.json"
        
        self._load_config(config_path)
        
        logger.info(f"扩展工具管理器初始化完成，加载了 {len(self.tools)} 个工具")
    
    def _load_config(self, config_path: str):
        """加载工具配置"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"工具配置文件不存在: {config_path}")
            self._load_default_tools()
            return
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for name, tool_config in config.get("tools", {}).items():
                parameters = {}
                for param_name, param_config in tool_config.get("parameters", {}).items():
                    parameters[param_name] = ToolParameter(
                        name=param_name,
                        type=param_config.get("type", "string"),
                        required=param_config.get("required", False),
                        default=param_config.get("default"),
                        description=param_config.get("description", ""),
                        enum=param_config.get("enum"),
                        min=param_config.get("min"),
                        max=param_config.get("max")
                    )
                
                self.tools[name] = ToolDefinition(
                    name=name,
                    category=tool_config.get("category", "network"),
                    description=tool_config.get("description", ""),
                    type=tool_config.get("type", "builtin"),
                    enabled=tool_config.get("enabled", True),
                    dangerous=tool_config.get("dangerous", False),
                    command=tool_config.get("command"),
                    parameters=parameters,
                    return_type=tool_config.get("return_type", "object"),
                    tags=tool_config.get("tags", []),
                    security=tool_config.get("security", {})
                )
            
            logger.info(f"从配置文件加载了 {len(self.tools)} 个工具")
            
        except Exception as e:
            logger.error(f"加载工具配置失败: {e}")
            self._load_default_tools()
    
    def _load_default_tools(self):
        """加载默认工具集"""
        default_tools = {
            "http_request": ToolDefinition(
                name="http_request",
                category="network",
                description="HTTP请求工具",
                type="builtin",
                parameters={
                    "url": ToolParameter("url", "string", required=True),
                    "method": ToolParameter("method", "string", default="GET"),
                    "headers": ToolParameter("headers", "object"),
                    "data": ToolParameter("data", "object"),
                    "timeout": ToolParameter("timeout", "integer", default=10)
                }
            ),
            "shell_exec": ToolDefinition(
                name="shell_exec",
                category="execution",
                description="Shell命令执行",
                type="builtin",
                dangerous=True,
                parameters={
                    "command": ToolParameter("command", "string", required=True),
                    "timeout": ToolParameter("timeout", "integer", default=300)
                }
            ),
            "think": ToolDefinition(
                name="think",
                category="meta",
                description="结构化思考工具",
                type="builtin",
                parameters={
                    "analysis": ToolParameter("analysis", "string", required=True),
                    "problem": ToolParameter("problem", "string", required=True),
                    "reasoning_steps": ToolParameter("reasoning_steps", "array", required=True),
                    "conclusion": ToolParameter("conclusion", "string", required=True)
                }
            )
        }
        
        self.tools.update(default_tools)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None, enabled_only: bool = True) -> List[ToolDefinition]:
        """列出所有工具"""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        return tools
    
    def validate_params(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证工具参数
        
        Returns:
            包含 'valid' 和可能的 'errors' 的字典
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return {"valid": False, "errors": [f"工具 {tool_name} 不存在"]}
        
        errors = []
        
        # 检查必需参数
        for param_name, param_def in tool.parameters.items():
            if param_def.required and param_name not in params:
                errors.append(f"缺少必需参数: {param_name}")
        
        # 验证参数值
        for param_name, value in params.items():
            if param_name in tool.parameters:
                param_def = tool.parameters[param_name]
                if not param_def.validate(value):
                    errors.append(f"参数 {param_name} 的值无效")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    async def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"工具 {tool_name} 不存在"}
        
        if not tool.enabled:
            return {"success": False, "error": f"工具 {tool_name} 已禁用"}
        
        # 验证参数
        validation = self.validate_params(tool_name, kwargs)
        if not validation["valid"]:
            return {"success": False, "error": "; ".join(validation["errors"])}
        
        # 安全检查
        if tool.dangerous:
            logger.warning(f"执行危险工具: {tool_name}")
        
        # 根据工具类型执行
        try:
            if tool.type == "builtin":
                return await self._execute_builtin(tool_name, **kwargs)
            elif tool.type == "external":
                return await self._execute_external(tool_name, **kwargs)
            else:
                return {"success": False, "error": f"未知工具类型: {tool.type}"}
                
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_builtin(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行内置工具"""
        
        # ==================== 元认知工具 ====================
        
        if tool_name == "think":
            return self._tool_think(**kwargs)
        
        elif tool_name == "formulate_hypotheses":
            return self._tool_formulate_hypotheses(**kwargs)
        
        elif tool_name == "reflect_on_failure":
            return self._tool_reflect_on_failure(**kwargs)
        
        # ==================== 控制工具 ====================
        
        elif tool_name == "complete_mission":
            return self._tool_complete_mission(**kwargs)
        
        elif tool_name == "halt_task":
            return self._tool_halt_task(**kwargs)
        
        # ==================== 网络工具 ====================
        
        elif tool_name == "http_request":
            return await self._tool_http_request(**kwargs)
        
        # ==================== 情报工具 ====================
        
        elif tool_name == "web_search":
            return await self._tool_web_search(**kwargs)
        
        elif tool_name == "retrieve_knowledge":
            return await self._tool_retrieve_knowledge(**kwargs)
        
        else:
            return {"success": False, "error": f"未实现的内置工具: {tool_name}"}
    
    async def _execute_external(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行外部工具"""
        tool = self.tools.get(tool_name)
        if not tool or not tool.command:
            return {"success": False, "error": "工具命令未定义"}
        
        # 构建命令
        cmd = self._build_command(tool, kwargs)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "tool": tool_name,
                "command": " ".join(cmd),
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "returncode": process.returncode
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"工具 {tool_name} 未安装",
                "error_type": "TOOL_MISSING"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "RUNTIME"
            }
    
    def _build_command(self, tool: ToolDefinition, params: Dict[str, Any]) -> List[str]:
        """构建命令行"""
        cmd_parts = tool.command.split()
        cmd = []
        
        for part in cmd_parts:
            cmd.append(part)
        
        # 添加参数
        for param_name, value in params.items():
            if value is None:
                continue
            
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{param_name}")
            elif isinstance(value, (list, dict)):
                cmd.append(f"--{param_name}")
                cmd.append(json.dumps(value))
            else:
                cmd.append(f"--{param_name}")
                cmd.append(str(value))
        
        return cmd
    
    # ==================== 内置工具实现 ====================
    
    def _tool_think(self, analysis: str, problem: str, reasoning_steps: List[str], conclusion: str) -> Dict[str, Any]:
        """结构化思考工具"""
        entry = {
            "type": "structured_thought",
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "problem": problem,
            "reasoning_steps": reasoning_steps,
            "conclusion": conclusion
        }
        
        self._think_history.append(entry)
        
        return {
            "success": True,
            "message": "结构化思考过程已记录",
            "recorded_thought": entry
        }
    
    def _tool_formulate_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """假设生成工具"""
        return {
            "success": True,
            "status": "假设已记录，请选择置信度最高的假设进行验证",
            "hypotheses": hypotheses,
            "timestamp": datetime.now().isoformat()
        }
    
    def _tool_reflect_on_failure(self, failed_action: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """失败反思工具"""
        return {
            "success": True,
            "status": "反思已记录，请分析失败原因并提出修正方案",
            "reflection": {
                "failed_action": failed_action,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _tool_complete_mission(self, reason: str, evidence: str) -> Dict[str, Any]:
        """任务完成信号"""
        return {
            "success": True,
            "message": "任务完成信号已发送",
            "reason": reason,
            "evidence": evidence,
            "timestamp": datetime.now().isoformat()
        }
    
    def _tool_halt_task(self, reason: str) -> Dict[str, Any]:
        """任务终止"""
        return {
            "success": True,
            "message": "任务终止信号已发送",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _tool_http_request(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        data: Any = None,
        timeout: int = 10,
        allow_redirects: bool = True
    ) -> Dict[str, Any]:
        """HTTP请求工具"""
        try:
            response = await self._http_client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                content=json.dumps(data) if isinstance(data, (dict, list)) else data,
                timeout=timeout,
                follow_redirects=allow_redirects
            )
            
            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "cookies": dict(response.cookies),
                "url": str(response.url)
            }
            
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": f"请求超时 ({timeout}s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """网络搜索工具"""
        try:
            # 使用 DuckDuckGo
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            
            return {
                "success": True,
                "query": query,
                "results": results
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "请安装 duckduckgo-search: pip install duckduckgo-search"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_retrieve_knowledge(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """知识检索工具"""
        # 这里可以集成 RAG 系统
        return {
            "success": True,
            "query": query,
            "results": [],
            "message": "知识检索功能待实现，请配置 RAG 服务"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        total = len(self.tools)
        enabled = sum(1 for t in self.tools.values() if t.enabled)
        dangerous = sum(1 for t in self.tools.values() if t.dangerous)
        
        return {
            "total_tools": total,
            "enabled_tools": enabled,
            "dangerous_tools": dangerous,
            "status": "healthy"
        }


# 全局实例
_extended_tool_manager: Optional[ExtendedToolManager] = None


def get_extended_tool_manager(config_path: Optional[str] = None) -> ExtendedToolManager:
    """获取扩展工具管理器实例"""
    global _extended_tool_manager
    
    if _extended_tool_manager is None:
        _extended_tool_manager = ExtendedToolManager(config_path=config_path)
    
    return _extended_tool_manager


__all__ = [
    "ExtendedToolManager",
    "ToolDefinition",
    "ToolParameter",
    "ToolCategory",
    "ToolType",
    "get_extended_tool_manager"
]
