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
        background: #0a0e17;
        color: #00ff41;
        padding: 0 2;
        content-align: center middle;
        border-top: solid #1a3a1a;
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

        # Status markers - hacker terminal style
        status_config = {
            "idle":        ("IDLE",  "dim"),
            "processing":  ("PROC",  "yellow"),
            "scanning":    ("SCAN",  "cyan"),
            "analyzing":   ("ANLYZ", "blue"),
            "waiting":     ("WAIT",  "green"),
            "thinking":    ("THINK", "cyan"),
            "flag_found":  ("FLAG",  "bright_red"),
            "error":       ("ERR",   "red"),
        }

        status_marker, status_color = status_config.get(
            self.agent_status, ("????", "dim")
        )

        text.append(f"[", style="dim")
        text.append(f"{status_marker}", style=f"bold {status_color}")
        text.append(f"] ", style="dim")

        # Message
        if self.agent_message:
            text.append(f"{self.agent_message} ", style=status_color)

        text.append("| ", style="dim")

        # Target
        if self.target:
            text.append(f"TGT:", style="bold cyan")
            text.append(f" {self.target}", style="cyan")
        else:
            text.append("No target", style="dim")

        text.append(" | ", style="dim")

        # Keybindings
        text.append("Ctrl+C", style="bold")
        text.append(" Exit  ", style="dim")
        text.append("F1", style="bold")
        text.append(" Help", style="dim")

        return text

    def set_status(self, status: str, message: str = ""):
        """设置状态"""
        self.agent_status = status
        self.agent_message = message

    def set_target(self, target: str):
        """设置目标"""
        self.target = target
