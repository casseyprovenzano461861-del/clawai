#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 状态栏组件
"""

from typing import Optional
from rich.text import Text
from textual.widgets import Static
from textual.reactive import reactive


class StatusBar(Static):
    """状态栏组件"""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 2;
        content-align: center middle;
    }
    """

    agent_status: reactive[str] = reactive("idle")
    agent_message: reactive[str] = reactive("")
    target: reactive[Optional[str]] = reactive(None)

    def __init__(self):
        super().__init__()
        self.agent_status = "idle"
        self.agent_message = ""
        self.target = None

    def render(self) -> Text:
        """渲染状态栏"""
        text = Text()

        # 状态图标和文字
        status_config = {
            "idle": ("⏸ Idle", "dim"),
            "processing": ("⏳ Processing", "yellow"),
            "scanning": ("🔍 Scanning", "cyan"),
            "analyzing": ("📊 Analyzing", "blue"),
            "waiting": ("⌨️ Waiting", "green"),
            "error": ("❌ Error", "red")
        }

        status_icon, status_color = status_config.get(
            self.agent_status, ("❓ Unknown", "dim")
        )

        text.append(f"{status_icon} ")

        # 附加消息
        if self.agent_message:
            text.append(f"- {self.agent_message} ")

        text.append("│ ")

        # 目标
        if self.target:
            text.append(f"🎯 {self.target}")
        else:
            text.append("No target", style="dim")

        text.append(" │ ")

        # 快捷键提示
        text.append("Ctrl+C", style="bold")
        text.append(" Exit  ")
        text.append("F1", style="bold")
        text.append(" Help")

        return text

    def set_status(self, status: str, message: str = ""):
        """设置状态"""
        self.agent_status = status
        self.agent_message = message

    def set_target(self, target: str):
        """设置目标"""
        self.target = target
