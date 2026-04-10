#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 工具定义框架
借鉴 cc-haha 的 Tool 接口: name, input_schema, execute, is_dangerous, is_readonly

核心概念:
- ToolDefinition: 工具元数据 + 执行方法
- ToolResult: 工具执行结果
- ToolRegistry: 工具注册表 (懒加载 + 自动发现)
- execute_streaming: 异步流式执行, 逐行输出
"""

import asyncio
import logging
import shlex
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0

    def to_text(self) -> str:
        """转为 LLM 可读的文本"""
        if self.success:
            return self.output or "(工具执行成功，无输出)"
        return f"[工具执行失败] {self.error}\n{self.output}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output[:2000],  # 截断防止过长
            "error": self.error,
            "duration": self.duration,
        }


@dataclass
class ToolDefinition:
    """工具定义 (借鉴 cc-haha 的 Tool 接口)

    属性:
        name: 工具名 (如 "nmap", "bash")
        description: 给 LLM 的描述
        input_schema: OpenAI function calling 兼容的 JSON Schema
        is_dangerous: 需要用户确认才能执行
        is_readonly: 只读操作, 可自动执行
        timeout: 默认超时秒数
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    is_dangerous: bool = False
    is_readonly: bool = False
    timeout: int = 120

    async def execute(self, args: Dict[str, Any], on_output: Optional[Callable[[str], None]] = None) -> ToolResult:
        """执行工具, 通过 on_output 回调实时输出

        子类必须覆盖此方法
        """
        raise NotImplementedError(f"工具 {self.name} 未实现 execute()")

    def get_openai_schema(self) -> Dict[str, Any]:
        """生成 OpenAI function calling 格式的工具定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            }
        }

    def format_call_display(self, args: Dict[str, Any]) -> str:
        """格式化工具调用显示 (给用户看)"""
        if self.name == "bash":
            return args.get("command", "")
        target = args.get("target", "")
        extra = " ".join(f"{k}={v}" for k, v in args.items() if k not in ("target",) and v)
        return f"{self.name} {target} {extra}".strip()


async def execute_streaming(
    cmd: List[str],
    on_output: Optional[Callable[[str], None]] = None,
    timeout: int = 120,
) -> ToolResult:
    """异步流式执行命令, 逐行输出

    Args:
        cmd: 命令列表 (如 ["nmap", "-sV", "192.168.1.1"])
        on_output: 输出回调 (每行调用一次)
        timeout: 超时秒数

    Returns:
        ToolResult
    """
    import time
    start = time.time()
    lines = []

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        async def _read_output():
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors='replace').rstrip()
                lines.append(decoded)
                if on_output:
                    on_output(decoded)

        try:
            await asyncio.wait_for(_read_output(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            elapsed = time.time() - start
            return ToolResult(
                success=False,
                output="\n".join(lines),
                error=f"命令超时 ({timeout}s)",
                duration=elapsed,
            )

        await proc.wait()
        elapsed = time.time() - start
        output = "\n".join(lines)

        if proc.returncode == 0:
            return ToolResult(success=True, output=output, duration=elapsed)
        else:
            return ToolResult(
                success=False,
                output=output,
                error=f"退出码 {proc.returncode}",
                duration=elapsed,
            )

    except FileNotFoundError:
        elapsed = time.time() - start
        return ToolResult(
            success=False,
            output="",
            error=f"命令未找到: {cmd[0]}",
            duration=elapsed,
        )
    except Exception as e:
        elapsed = time.time() - start
        return ToolResult(
            success=False,
            output="\n".join(lines),
            error=str(e),
            duration=elapsed,
        )


def _linux_to_win(command: str) -> str:
    """Auto-translate common Linux shell patterns to Windows cmd equivalents.

    This is a safety net for when the LLM generates Linux-style commands
    despite the platform hint in the system prompt.
    """
    import re

    # 2>/dev/null -> 2>nul
    command = command.replace("2>/dev/null", "2>nul")
    command = command.replace("2>/dev/tty", "CON")

    # ping -c N -> ping -n N
    command = re.sub(r'\bping\s+-c\s+(\d+)', r'ping -n \1', command)

    # cat -> type (standalone only, not in paths like /etc/passwd)
    command = re.sub(r'\bcat\s+', 'type ', command)

    # grep -> findstr (basic cases)
    command = re.sub(r'\bgrep\s+', 'findstr ', command)

    # head -N -> powershell or just skip (cmd has no head)
    command = re.sub(r'\bhead\s+-(\d+)\b', r'powershell -c "$input | Select-Object -First \1"', command)

    # tail -N
    command = re.sub(r'\btail\s+-(\d+)\b', r'powershell -c "$input | Select-Object -Last \1"', command)

    # which -> where
    command = re.sub(r'\bwhich\s+', 'where ', command)

    # rm -f -> del /f /q (basic)
    command = re.sub(r'\brm\s+-rf\s+', r'del /s /q ', command)
    command = re.sub(r'\brm\s+-f\s+', r'del /q ', command)

    return command


async def execute_shell_streaming(
    command: str,
    on_output: Optional[Callable[[str], None]] = None,
    timeout: int = 120,
) -> ToolResult:
    """异步流式执行 shell 命令字符串, 支持 pipes, redirects, || 等

    Unlike execute_streaming which takes a list and uses subprocess_exec,
    this runs the command through a shell to properly handle shell operators.

    Args:
        command: Shell command string (e.g. "curl -s http://x | grep ok")
        on_output: Output callback (called per line)
        timeout: Timeout in seconds

    Returns:
        ToolResult
    """
    import time
    import sys
    start = time.time()
    lines = []

    # Auto-translate common Linux patterns on Windows
    if sys.platform == "win32":
        command = _linux_to_win(command)

    try:
        if sys.platform == "win32":
            proc = await asyncio.create_subprocess_exec(
                "cmd.exe", "/c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                "/bin/bash", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

        async def _read_output():
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors='replace').rstrip()
                lines.append(decoded)
                if on_output:
                    on_output(decoded)

        try:
            await asyncio.wait_for(_read_output(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            elapsed = time.time() - start
            return ToolResult(
                success=False,
                output="\n".join(lines),
                error=f"命令超时 ({timeout}s)",
                duration=elapsed,
            )

        await proc.wait()
        elapsed = time.time() - start
        output = "\n".join(lines)

        if proc.returncode == 0:
            return ToolResult(success=True, output=output, duration=elapsed)
        else:
            return ToolResult(
                success=False,
                output=output,
                error=f"退出码 {proc.returncode}",
                duration=elapsed,
            )

    except Exception as e:
        elapsed = time.time() - start
        return ToolResult(
            success=False,
            output="\n".join(lines),
            error=str(e),
            duration=elapsed,
        )


class ToolRegistry:
    """工具注册表"""

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._loaded = False

    @classmethod
    def get(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def lookup(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def all_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 OpenAI function calling schema"""
        return [t.get_openai_schema() for t in self._tools.values()]

    def discover(self) -> None:
        """自动发现 src/cli/tools/ 下的工具"""
        if self._loaded:
            return

        import importlib
        import pkgutil
        from src.cli import tools as tools_pkg

        for importer, modname, ispkg in pkgutil.iter_modules(tools_pkg.__path__):
            if modname.startswith("_"):
                continue
            try:
                module = importlib.import_module(f"src.cli.tools.{modname}")
                if hasattr(module, "TOOL"):
                    self.register(module.TOOL)
            except Exception as e:
                logger.debug(f"发现工具 {modname} 失败: {e}")

        self._loaded = True


def get_tool_registry() -> ToolRegistry:
    """获取已初始化的工具注册表"""
    registry = ToolRegistry.get()
    registry.discover()
    return registry
