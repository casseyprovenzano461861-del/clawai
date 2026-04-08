#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 主应用
基于Textual框架的富文本终端界面
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Label
from textual.screen import ModalScreen
from textual import events

from src.cli.chat_cli import ClawAIChatCLI, Intent
from src.cli.tui.widgets.chat_input import ChatInput
from src.cli.tui.widgets.message_list import MessageList
from src.cli.tui.widgets.status_bar import StatusBar
from src.cli.tui.widgets.tool_output import ToolOutputPanel

logger = logging.getLogger(__name__)


class HelpScreen(ModalScreen):
    """帮助屏幕"""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Container {
        width: 60;
        height: 25;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    HelpScreen Label {
        margin: 1 0;
    }
    HelpScreen #title {
        text-align: center;
        text-style: bold;
        color: $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Label("🤖 ClawAI 帮助", id="title"),
            Label(""),
            Label("基本命令:"),
            Label("  扫描 <目标>    - 对目标进行渗透测试"),
            Label("  状态           - 查看当前状态"),
            Label("  报告           - 生成测试报告"),
            Label("  帮助           - 显示此帮助"),
            Label("  退出           - 退出程序"),
            Label(""),
            Label("快捷键:"),
            Label("  Ctrl+C        - 退出"),
            Label("  F1            - 帮助"),
            Label("  Enter         - 发送消息"),
            Label(""),
            Label("按任意键关闭"),
            id="help_container"
        )

    def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()


class ClawAIChatApp(App):
    """ClawAI 对话式TUI应用"""

    CSS_PATH = Path(__file__).parent / "styles.tcss"

    TITLE = "ClawAI - AI驱动的渗透测试助手"

    BINDINGS = [
        Binding("f1", "show_help", "帮助"),
        Binding("ctrl+c", "quit", "退出", priority=True),
    ]

    def __init__(self, target: Optional[str] = None, config: dict = None):
        super().__init__()
        self.initial_target = target
        self.config = config or {}
        self.chat_cli = None
        self._processing = False

    def compose(self) -> ComposeResult:
        """构建UI布局"""
        yield Header(show_clock=True)

        with Container(id="main_container"):
            # 消息列表
            yield MessageList()

            # 工具输出面板
            yield ToolOutputPanel()

            # 状态栏
            yield StatusBar()

            # 输入框
            yield ChatInput()

        yield Footer()

    def on_mount(self) -> None:
        """应用挂载时初始化"""
        # 初始化聊天CLI
        self.chat_cli = ClawAIChatCLI(self.config)

        # 设置回调
        self.chat_cli.on_message = self._handle_chat_message
        self.chat_cli.on_tool_execution = self._handle_tool_execution
        self.chat_cli.on_status_change = self._handle_status_change

        # 欢迎消息
        message_list = self.query_one(MessageList)

        # 检查AI状态
        if self.chat_cli.agent:
            llm_type = self.chat_cli.agent.llm_client.get("type", "unknown")
            model = self.chat_cli.agent.model_id if hasattr(self.chat_cli.agent, 'model_id') else "unknown"
            welcome_msg = f"欢迎使用 ClawAI！我是你的渗透测试助手。\nAI模型: {model} ({llm_type})\n输入目标地址开始测试，或输入 '帮助' 查看更多信息。"
        else:
            welcome_msg = "欢迎使用 ClawAI！我是你的渗透测试助手。\n输入目标地址开始测试，或输入 '帮助' 查看更多信息。\n\n⚠️ 当前运行在模拟模式。输入'帮助'查看如何配置AI。"

        message_list.add_system_message(welcome_msg)

        # 如果有初始目标
        if self.initial_target:
            self.chat_cli.set_target(self.initial_target)
            self.query_one(StatusBar).set_target(self.initial_target)
            message_list.add_system_message(f"目标已设置: {self.initial_target}")

        # 聚焦输入框
        self.query_one(ChatInput).focus()

    def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """处理输入提交"""
        if self._processing:
            return

        text = event.text
        if not text.strip():
            return

        # 显示用户消息
        message_list = self.query_one(MessageList)
        message_list.add_user_message(text)

        # 异步处理
        asyncio.create_task(self._process_input(text))

    async def _process_input(self, text: str) -> None:
        """处理用户输入"""
        self._processing = True
        status_bar = self.query_one(StatusBar)
        status_bar.set_status("processing", "处理中...")

        try:
            # 调用聊天CLI处理
            response = await self.chat_cli.chat(text)

            # 显示AI响应
            message_list = self.query_one(MessageList)
            message_list.add_assistant_message(response)

            # 更新状态栏目标
            if self.chat_cli.session.target:
                status_bar.set_target(self.chat_cli.session.target)

        except Exception as e:
            logger.error(f"处理输入失败: {e}")
            message_list = self.query_one(MessageList)
            message_list.add_system_message(f"错误: {str(e)}")
            status_bar.set_status("error", str(e))

        finally:
            self._processing = False
            status_bar.set_status("idle", "")

    def _handle_chat_message(self, role: str, content: str):
        """消息回调"""
        message_list = self.query_one(MessageList)
        if role == "system":
            message_list.add_system_message(content)
        elif role == "assistant":
            message_list.add_assistant_message(content)
        elif role == "user":
            message_list.add_user_message(content)

    def _handle_tool_execution(self, tool_name: str, params: dict, status: str):
        """工具执行回调"""
        tool_panel = self.query_one(ToolOutputPanel)
        if status == "running":
            tool_panel.start_tool(tool_name, params)
        elif status == "completed":
            tool_panel.complete_tool(tool_name, success=True)
        elif status == "failed":
            tool_panel.complete_tool(tool_name, success=False)

    def _handle_status_change(self, status: str, message: str):
        """状态变化回调"""
        status_bar = self.query_one(StatusBar)
        status_bar.set_status(status, message)

    def action_show_help(self) -> None:
        """显示帮助"""
        self.push_screen(HelpScreen())

    def action_quit(self) -> None:
        """退出应用"""
        self.exit()


# 默认CSS样式
DEFAULT_CSS = """
Screen {
    background: $surface;
}

#main_container {
    layout: vertical;
    height: 1fr;
}

Header {
    background: $primary;
    color: $text;
}

Footer {
    background: $primary-darken-1;
}

MessageList {
    height: 1fr;
    background: $surface;
}

ToolOutputPanel {
    height: auto;
    max-height: 10;
    dock: bottom;
}

ChatInput {
    dock: bottom;
    height: 3;
    background: $surface-darken-1;
}

StatusBar {
    dock: bottom;
    height: 1;
}
"""


async def run_tui(target: Optional[str] = None, config: dict = None):
    """运行TUI应用"""
    # 创建样式文件（如果不存在）
    css_path = Path(__file__).parent / "styles.tcss"
    if not css_path.exists():
        css_path.write_text(DEFAULT_CSS, encoding="utf-8")

    app = ClawAIChatApp(target=target, config=config)
    await app.run_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tui())
