#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 聊天输入组件（支持多行、斜杠命令提示）
"""

from textual.widgets import TextArea
from textual.message import Message
from textual import events


class ChatInput(TextArea):
    """聊天输入框

    - Enter 发送消息
    - Shift+Enter 插入换行（多行输入）
    - 输入 / 显示斜杠命令提示
    - 输入 ! 显示 bash 模式提示
    """

    DEFAULT_CSS = """
    ChatInput {
        dock: bottom;
        height: 3;
        background: #0a0e17;
        border: tall #00ff41;
        border-title-color: #00ff41;
        padding: 0 1;
        color: #00ff41;
    }
    ChatInput:focus {
        border: double #00d4ff;
    }
    """

    class Submitted(Message):
        """输入提交消息"""
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def __init__(self, placeholder: str = ">>_ "):
        super().__init__(placeholder=placeholder)
        self.placeholder = placeholder

    def on_key(self, event: events.Key) -> None:
        """按键处理"""
        # Shift+Enter: 插入换行（多行输入）
        if event.key == "shift+enter":
            # TextArea 默认处理换行
            return

        # Enter: 发送消息
        if event.key == "enter":
            event.prevent_default()
            text = self.text.strip()
            if text:
                self.post_message(self.Submitted(text))
                self.clear()
