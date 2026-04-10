#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 消息列表组件
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from rich.text import Text
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.reactive import reactive


class MessageItem(Static):
    """单条消息组件"""

    DEFAULT_CSS = """
    MessageItem {
        margin: 0 1;
        padding: 0 1;
        width: 1fr;
    }
    MessageItem.user {
        background: #0d1a0d;
    }
    MessageItem.assistant {
        background: $cyber-darker;
    }
    MessageItem.system {
        background: #0a0a1a;
    }
    MessageItem.tool {
        background: #1a1a0a;
    }
    MessageItem.finding {
        background: #1a0d00;
    }
    MessageItem.flag {
        background: #1a0000;
    }
    """

    # 使用 reactive 确保内容变更时自动触发重渲染
    _content: reactive[str] = reactive("", layout=True)

    def __init__(self, role: str, content: str, timestamp: datetime = None, metadata: Dict = None):
        super().__init__()
        self.role = role
        self._content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        self._content = value

    def watch__content(self, new_content: str) -> None:  # noqa: N802
        """reactive 变更时自动调用"""
        self.refresh()

    def render(self) -> Text:
        """渲染消息"""
        text = Text()

        role_markers = {
            "user":      ">>",
            "assistant": "[AI]",
            "system":    "[SYS]",
            "tool":      "[TOOL]",
            "finding":   "[FIND]",
            "flag":      "[FLAG]",
        }
        role_colors = {
            "user":      "cyan",
            "assistant": "green",
            "system":    "magenta",
            "tool":      "yellow",
            "finding":   "dark_orange",
            "flag":      "bright_red",
        }

        marker = role_markers.get(self.role, self.role.upper())
        color = role_colors.get(self.role, "white")
        time_str = self.timestamp.strftime('%H:%M:%S')

        text.append(f"{marker} ", style=f"bold {color}")
        text.append(f"[{time_str}]", style="dim")
        text.append("\n")
        # 流式时显示光标
        display = self._content
        if self.metadata.get("stream_id") and not self._content.endswith("▌"):
            display = self._content + "▌"
        text.append(display)

        return text

    def on_mount(self):
        """挂载时添加角色样式"""
        self.add_class(self.role)


class MessageList(VerticalScroll):
    """消息列表组件（支持流式更新）"""

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        background: $surface;
    }
    """

    def __init__(self):
        super().__init__()
        self.messages: List[MessageItem] = []
        self._stream_counter = 0

    def add_message(self, role: str, content: str, timestamp: datetime = None, metadata: Dict = None):
        """添加消息"""
        msg = MessageItem(role, content, timestamp, metadata)
        self.messages.append(msg)
        self.mount(msg)
        self.scroll_end(animate=False)

    def add_user_message(self, content: str, timestamp: datetime = None):
        self.add_message("user", content, timestamp)

    def add_assistant_message(self, content: str, timestamp: datetime = None, streaming: bool = False) -> int:
        """添加AI响应消息

        Returns:
            流式消息 ID（非流式返回 0）
        """
        stream_id = 0
        if streaming:
            self._stream_counter += 1
            stream_id = self._stream_counter
        msg = MessageItem("assistant", content, timestamp, {"stream_id": stream_id} if streaming else {})
        self.messages.append(msg)
        self.mount(msg)
        self.scroll_end(animate=False)
        return stream_id

    def add_system_message(self, content: str, timestamp: datetime = None):
        self.add_message("system", content, timestamp)

    def add_tool_message(self, tool_name: str, params: Dict, status: str, output: str = None):
        """添加工具执行消息"""
        content = f"[{status.upper()}] {tool_name}"
        if params:
            content += f"\n参数: {params}"
        if output:
            content += f"\n输出: {output[:200]}{'...' if len(output) > 200 else ''}"
        self.add_message("tool", content)

    def add_finding_message(self, title: str, detail: str = "", severity: str = "info"):
        """添加安全发现消息"""
        severity_prefix = {
            "critical": "🔴",
            "high":     "🟠",
            "medium":   "🟡",
            "low":      "🟢",
            "info":     "🔵",
        }.get(severity, "⚪")
        content = f"{severity_prefix} {title}"
        if detail:
            content += f"\n   {detail}"
        self.add_message("finding", content)

    def add_flag_message(self, flag_value: str, location: str = "", method: str = ""):
        """添加 Flag 捕获消息（高优先级）"""
        content = f"⚑ FLAG CAPTURED: {flag_value}"
        if location:
            content += f"\n   位置: {location}"
        if method:
            content += f"\n   方法: {method}"
        self.add_message("flag", content)

    def append_to_message(self, stream_id: int, token: str):
        """流式追加 token 到消息（增量更新）"""
        if not stream_id:
            return
        for msg in self.messages:
            if msg.metadata.get("stream_id") == stream_id:
                msg.content = msg.content + token
                self.scroll_end(animate=False)
                return

    def update_message(self, stream_id: int, content: str):
        """更新流式消息内容（全量替换）"""
        if not stream_id:
            return
        for msg in self.messages:
            if msg.metadata.get("stream_id") == stream_id:
                msg.content = content
                self.scroll_end(animate=False)
                return

    def finalize_message(self, stream_id: int, content: str):
        """完成流式消息（移除光标，锁定内容）"""
        if not stream_id:
            return
        for msg in self.messages:
            if msg.metadata.get("stream_id") == stream_id:
                msg.content = content
                msg.metadata.pop("stream_id", None)
                msg.refresh()
                self.scroll_end(animate=False)
                return

    def clear_messages(self):
        """清空消息"""
        for msg in self.messages:
            msg.remove()
        self.messages.clear()

    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取消息历史"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages[-limit:]
        ]
