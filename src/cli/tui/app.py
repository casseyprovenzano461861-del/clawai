#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 主应用
基于 Textual 框架的富文本终端界面，支持流式 LLM 输出和 EventBus 实时更新
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Header, Footer, Label
from textual.screen import ModalScreen
from textual import events

logger = logging.getLogger(__name__)

# EventBus 可用性检查
_EVENTBUS_AVAILABLE = False
try:
    from src.shared.backend.events import EventBus, EventType, Event
    _EVENTBUS_AVAILABLE = True
except ImportError:
    pass


class HelpScreen(ModalScreen):
    """帮助屏幕"""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Container {
        width: 60;
        height: 28;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    HelpScreen Label {
        margin: 0 0;
    }
    HelpScreen #title {
        text-align: center;
        text-style: bold;
        color: $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Label("ClawAI 帮助", id="title"),
            Label(""),
            Label("斜杠命令:"),
            Label("  /help          - 显示此帮助"),
            Label("  /scan <target> - 安全扫描"),
            Label("  /session list  - 列出会话"),
            Label("  /pause         - 暂停扫描"),
            Label("  /resume        - 恢复扫描"),
            Label("  /exit          - 退出"),
            Label(""),
            Label("Bash 模式:"),
            Label("  !command       - 执行 bash 命令"),
            Label(""),
            Label("自然语言:"),
            Label("  扫描 192.168.1.1  - AI 理解后扫描"),
            Label("  分析              - AI 分析发现"),
            Label("  报告              - 生成报告"),
            Label(""),
            Label("快捷键:"),
            Label("  Ctrl+C  - 退出  F1 - 帮助"),
            Label(""),
            Label("按任意键关闭"),
            id="help_container"
        )

    def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()


class ClawAIChatApp(App):
    """ClawAI 对话式 TUI 应用（流式 + EventBus）"""

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
        self._dispatcher = None

    def compose(self) -> ComposeResult:
        """构建 UI 布局"""
        yield Header(show_clock=True)

        with Container(id="main_container"):
            from src.cli.tui.widgets.message_list import MessageList
            from src.cli.tui.widgets.tool_output import ToolOutputPanel
            from src.cli.tui.widgets.status_bar import StatusBar
            from src.cli.tui.widgets.chat_input import ChatInput

            yield MessageList()
            yield ToolOutputPanel()
            yield StatusBar()
            yield ChatInput()

        yield Footer()

    def on_mount(self) -> None:
        """应用挂载时初始化"""
        from src.cli.chat_cli import ClawAIChatCLI
        from src.cli.tui.widgets.message_list import MessageList
        from src.cli.tui.widgets.status_bar import StatusBar
        from src.cli.slash_dispatcher import SlashDispatcher
        from src.cli.commands import get_registry

        # 初始化 ChatCLI
        self.chat_cli = ClawAIChatCLI(self.config)

        # 设置回调
        self.chat_cli.on_message = self._handle_chat_message
        self.chat_cli.on_tool_execution = self._handle_tool_execution
        self.chat_cli.on_status_change = self._handle_status_change

        # 初始化斜杠命令分发器
        try:
            registry = get_registry()
            self._dispatcher = SlashDispatcher(registry, self.chat_cli)
        except Exception as e:
            logger.debug(f"斜杠分发器初始化失败: {e}")

        # 订阅 EventBus
        if _EVENTBUS_AVAILABLE:
            self._subscribe_eventbus()

        # 欢迎消息
        message_list = self.query_one(MessageList)

        if self.chat_cli.agent:
            llm_type = self.chat_cli.agent.llm_client.get("type", "unknown")
            model = self.chat_cli.agent.model_id if hasattr(self.chat_cli.agent, 'model_id') else "unknown"
            welcome_msg = f"欢迎使用 ClawAI！\nAI模型: {model} ({llm_type})\n输入 /help 查看命令，! 执行 bash，自然语言对话 AI"
        else:
            welcome_msg = "欢迎使用 ClawAI！\n输入 /help 查看命令，! 执行 bash，自然语言对话 AI\n\n⚠️ 当前运行在模拟模式"

        message_list.add_system_message(welcome_msg)

        # 初始目标
        if self.initial_target:
            self.chat_cli.set_target(self.initial_target)
            self.query_one(StatusBar).set_target(self.initial_target)
            message_list.add_system_message(f"目标已设置: {self.initial_target}")

        # 聚焦输入框
        from src.cli.tui.widgets.chat_input import ChatInput
        self.query_one(ChatInput).focus()

    def _subscribe_eventbus(self) -> None:
        """订阅 EventBus 事件"""
        bus = EventBus.get()
        bus.subscribe(EventType.TOOL, self._on_tool_event)
        bus.subscribe(EventType.STATE_CHANGED, self._on_state_event)

    def _on_tool_event(self, event: "Event") -> None:
        """工具事件回调"""
        from src.cli.tui.widgets.tool_output import ToolOutputPanel
        tool_panel = self.query_one(ToolOutputPanel)
        status = event.data.get("status", "")
        name = event.data.get("name", "")
        if status == "start":
            tool_panel.start_tool(name, event.data.get("args"))
        elif status == "complete":
            tool_panel.complete_tool(name, success=True)
        elif status == "failed":
            tool_panel.complete_tool(name, success=False)

    def _on_state_event(self, event: "Event") -> None:
        """状态变化事件回调"""
        from src.cli.tui.widgets.status_bar import StatusBar
        status_bar = self.query_one(StatusBar)
        status_bar.set_status(event.data.get("state", "idle"), event.data.get("details", ""))

    def on_chat_input_submitted(self, event) -> None:
        """处理输入提交"""
        if self._processing:
            return

        text = event.text
        if not text.strip():
            return

        # 显示用户消息
        from src.cli.tui.widgets.message_list import MessageList
        message_list = self.query_one(MessageList)
        message_list.add_user_message(text)

        # 异步处理
        asyncio.create_task(self._process_input(text))

    async def _process_input(self, text: str) -> None:
        """处理用户输入（支持斜杠命令和流式对话）"""
        self._processing = True
        from src.cli.tui.widgets.message_list import MessageList
        from src.cli.tui.widgets.status_bar import StatusBar
        from src.cli.tui.widgets.tool_output import ToolOutputPanel

        status_bar = self.query_one(StatusBar)
        message_list = self.query_one(MessageList)
        status_bar.set_status("processing", "处理中...")

        try:
            # 斜杠命令分发
            if self._dispatcher:
                result = self._dispatcher.dispatch(text)

                if result.action == "slash_cmd":
                    cmd_cls = result.command_meta.load()
                    cmd = cmd_cls() if isinstance(cmd_cls, type) else cmd_cls
                    output = cmd.execute(result.args, {"chat_cli": self.chat_cli, "console": None})
                    if output and output != "__EXIT__":
                        message_list.add_assistant_message(output)
                    elif output == "__EXIT__":
                        self.exit()
                        return
                    status_bar.set_status("idle", "")
                    return

                elif result.action == "bash_cmd":
                    import subprocess
                    try:
                        proc = subprocess.run(
                            result.args[0], shell=True, capture_output=True, text=True, timeout=30
                        )
                        output = proc.stdout or "(no output)"
                        if proc.stderr:
                            output += f"\n[stderr] {proc.stderr}"
                        message_list.add_system_message(f"$ {result.args[0]}\n{output}")
                    except subprocess.TimeoutExpired:
                        message_list.add_system_message("命令超时 (30s)")
                    except Exception as e:
                        message_list.add_system_message(f"执行错误: {e}")
                    status_bar.set_status("idle", "")
                    return

                elif result.action == "unknown_slash":
                    msg = f"未知命令: /{result.args[0]}"
                    if result.passthrough:
                        msg += f"\n你是否指: {', '.join(f'/{s}' for s in result.passthrough)}"
                    message_list.add_system_message(msg)
                    status_bar.set_status("idle", "")
                    return

            # 自然语言 → 流式 AI 对话
            await self._stream_chat(text)

        except Exception as e:
            logger.error(f"处理输入失败: {e}")
            message_list.add_system_message(f"错误: {e}")
            status_bar.set_status("error", str(e))

        finally:
            self._processing = False

    async def _stream_chat(self, text: str) -> None:
        """流式 LLM 对话"""
        from src.cli.tui.widgets.message_list import MessageList
        from src.cli.tui.widgets.status_bar import StatusBar

        message_list = self.query_one(MessageList)
        status_bar = self.query_one(StatusBar)

        # 创建流式消息占位
        stream_id = message_list.add_assistant_message("", streaming=True)
        full_text = ""

        try:
            # 通过 ChatCLI 处理（支持流式）
            status_bar.set_status("thinking", "思考中...")

            # 记录用户消息
            self.chat_cli.session.add_message("user", text)

            if self.chat_cli.agent:
                # 尝试流式输出
                try:
                    from src.cli.stream_renderer import MarkdownStream
                    # 使用 ChatCLI 的流式 chat
                    response = await self.chat_cli.chat(text)
                    full_text = response or ""

                    if getattr(self.chat_cli, '_streamed', False):
                        # 流式已在控制台渲染，需要从 session 获取完整文本
                        if self.chat_cli.session.messages:
                            full_text = self.chat_cli.session.messages[-1].content
                    else:
                        full_text = response or ""

                    message_list.update_message(stream_id, full_text)
                except Exception as e:
                    full_text = f"AI 响应失败: {e}"
                    message_list.update_message(stream_id, full_text)
            else:
                full_text = "模拟模式: AI 未配置。请设置 API Key。"
                message_list.update_message(stream_id, full_text)

            # 更新状态栏
            if self.chat_cli.session.target:
                status_bar.set_target(self.chat_cli.session.target)

        except Exception as e:
            logger.error(f"流式对话失败: {e}")
            full_text = f"错误: {e}"
            message_list.update_message(stream_id, full_text)
            status_bar.set_status("error", str(e))

        finally:
            message_list.finalize_message(stream_id, full_text)
            status_bar.set_status("idle", "")

    def _handle_chat_message(self, role: str, content: str):
        """消息回调"""
        from src.cli.tui.widgets.message_list import MessageList
        message_list = self.query_one(MessageList)
        if role == "system":
            message_list.add_system_message(content)
        elif role == "assistant":
            message_list.add_assistant_message(content)
        elif role == "user":
            message_list.add_user_message(content)

    def _handle_tool_execution(self, tool_name: str, params: dict, status: str):
        """工具执行回调"""
        from src.cli.tui.widgets.tool_output import ToolOutputPanel
        tool_panel = self.query_one(ToolOutputPanel)
        if status == "running":
            tool_panel.start_tool(tool_name, params)
        elif status == "completed":
            tool_panel.complete_tool(tool_name, success=True)
        elif status == "failed":
            tool_panel.complete_tool(tool_name, success=False)

    def _handle_status_change(self, status: str, message: str):
        """状态变化回调"""
        from src.cli.tui.widgets.status_bar import StatusBar
        status_bar = self.query_one(StatusBar)
        status_bar.set_status(status, message)

    def action_show_help(self) -> None:
        """显示帮助"""
        self.push_screen(HelpScreen())

    def action_quit(self) -> None:
        """退出应用"""
        if self.chat_cli:
            self.chat_cli.save_session()
        self.exit()


async def run_tui(target: Optional[str] = None, config: dict = None):
    """运行 TUI 应用"""
    app = ClawAIChatApp(target=target, config=config)
    await app.run_async()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tui())
