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


class MessageItem(Static):
    """单条消息组件"""

    DEFAULT_CSS = """
    MessageItem {
        margin: 0 1;
        padding: 0 1;
        width: 1fr;
    }
    MessageItem.user {
        background: $surface-darken-1;
    }
    MessageItem.assistant {
        background: $surface;
    }
    MessageItem.system {
        background: $primary-darken-2;
    }
    MessageItem.tool {
        background: $warning-darken-2;
    }
    """

    def __init__(self, role: str, content: str, timestamp: datetime = None, metadata: Dict = None):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def render(self) -> Text:
        """渲染消息"""
        text = Text()

        # 角色标识
        role_icons = {
            "user": "👤 You",
            "assistant": "🤖 ClawAI",
            "system": "⚙️ System",
            "tool": "🔧 Tool"
        }

        icon = role_icons.get(self.role, self.role)
        time_str = self.timestamp.strftime('%H:%M:%S')

        # 使用Text的append方法，避免Style对象
        text.append(f"{icon} ")
        text.append(f"[{time_str}]", style="dim")
        text.append("\n")
        text.append(self.content)

        return text

    def on_mount(self):
        """挂载时添加角色样式"""
        self.add_class(self.role)


class MessageList(VerticalScroll):
    """消息列表组件"""

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        background: $surface;
    }
    """

    def __init__(self):
        super().__init__()
        self.messages: List[MessageItem] = []

    def add_message(self, role: str, content: str, timestamp: datetime = None, metadata: Dict = None):
        """添加消息"""
        msg = MessageItem(role, content, timestamp, metadata)
        self.messages.append(msg)
        self.mount(msg)
        # 滚动到底部
        self.scroll_end(animate=False)

    def add_user_message(self, content: str, timestamp: datetime = None):
        """添加用户消息"""
        self.add_message("user", content, timestamp)

    def add_assistant_message(self, content: str, timestamp: datetime = None):
        """添加AI响应消息"""
        self.add_message("assistant", content, timestamp)

    def add_system_message(self, content: str, timestamp: datetime = None):
        """添加系统消息"""
        self.add_message("system", content, timestamp)

    def add_tool_message(self, tool_name: str, params: Dict, status: str, output: str = None):
        """添加工具执行消息"""
        content = f"[{status.upper()}] {tool_name}"
        if params:
            content += f"\n参数: {params}"
        if output:
            content += f"\n输出: {output[:200]}{'...' if len(output) > 200 else ''}"
        self.add_message("tool", content)

    def clear_messages(self):
        """清空消息"""
        for msg in self.messages:
            msg.remove()
        self.messages.clear()

    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取消息历史"""
        history = []
        for msg in self.messages[-limit:]:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        return history
