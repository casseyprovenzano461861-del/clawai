#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 工具输出显示组件
"""

from typing import Dict, Any, Optional
from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from textual.widgets import Static
from textual.containers import Vertical


class ToolOutput(Static):
    """工具执行输出显示组件"""

    DEFAULT_CSS = """
    ToolOutput {
        margin: 0 1;
        padding: 0 1;
        background: $surface-darken-2;
        border: solid $warning;
        width: 1fr;
    }
    ToolOutput.running {
        border: solid $primary;
    }
    ToolOutput.completed {
        border: solid $success;
    }
    ToolOutput.failed {
        border: solid $error;
    }
    """

    def __init__(self, tool_name: str, params: Dict[str, Any] = None):
        super().__init__()
        self.tool_name = tool_name
        self.params = params or {}
        self.status = "pending"
        self.output = ""
        self.start_time = None
        self.end_time = None

    def render(self):
        """渲染工具输出"""
        text = Text()

        # 工具名称和状态
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌"
        }
        icon = status_icons.get(self.status, "❓")

        text.append(f"{icon} {self.tool_name}\n", style="bold")

        # 参数
        if self.params:
            text.append("参数: ", style="dim")
            params_str = ", ".join(f"{k}={v}" for k, v in self.params.items() if v)
            text.append(f"{params_str}\n", style="cyan")

        # 输出
        if self.output:
            text.append("\n")
            # 限制输出长度
            output_display = self.output[:500]
            if len(self.output) > 500:
                output_display += "..."
            text.append(output_display, style="white")

        return text

    def set_status(self, status: str):
        """设置状态"""
        self.status = status
        # 移除旧的状态样式
        for s in ["running", "completed", "failed"]:
            self.remove_class(s)
        # 添加新的状态样式
        self.add_class(status)
        self.refresh()

    def set_output(self, output: str):
        """设置输出"""
        self.output = output
        self.refresh()

    def append_output(self, text: str):
        """追加输出"""
        self.output += text
        self.refresh()


class ToolOutputPanel(Vertical):
    """工具输出面板"""

    DEFAULT_CSS = """
    ToolOutputPanel {
        height: auto;
        max-height: 15;
        background: $surface-darken-1;
    }
    """

    def __init__(self):
        super().__init__()
        self.tool_outputs: Dict[str, ToolOutput] = {}

    def start_tool(self, tool_name: str, params: Dict[str, Any] = None):
        """开始工具执行"""
        tool_output = ToolOutput(tool_name, params)
        tool_output.set_status("running")
        self.tool_outputs[tool_name] = tool_output
        self.mount(tool_output)
        return tool_output

    def update_tool(self, tool_name: str, output: str = None, status: str = None):
        """更新工具状态"""
        if tool_name in self.tool_outputs:
            tool = self.tool_outputs[tool_name]
            if output:
                tool.append_output(output)
            if status:
                tool.set_status(status)

    def complete_tool(self, tool_name: str, output: str = None, success: bool = True):
        """完成工具执行"""
        if tool_name in self.tool_outputs:
            tool = self.tool_outputs[tool_name]
            if output:
                tool.set_output(output)
            tool.set_status("completed" if success else "failed")

    def clear(self):
        """清空所有输出"""
        for tool in self.tool_outputs.values():
            tool.remove()
        self.tool_outputs.clear()
