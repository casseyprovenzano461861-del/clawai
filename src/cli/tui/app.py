#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI TUI - 主应用
基于 Textual 框架的富文本终端界面，支持流式 LLM 输出和 EventBus 实时更新
"""

import asyncio
import logging
import threading
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
        width: 64;
        height: 28;
        background: #0a0e17;
        border: thick #00ff41;
        padding: 1 2;
        color: #c0d0c0;
    }
    HelpScreen Label {
        margin: 0 0;
    }
    HelpScreen #title {
        text-align: center;
        text-style: bold;
        color: #00ff41;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Label("C L A W A I", id="title"),
            Label("AI 驱动的自动化渗透测试系统", id="subtitle"),
            Label(""),
            Label("[命令列表]"),
            Label("  /help          - 显示帮助"),
            Label("  /scan <目标>  - 安全扫描"),
            Label("  /session list  - 会话列表"),
            Label("  /pause         - 暂停扫描"),
            Label("  /resume        - 继续扫描"),
            Label("  /exit          - 退出"),
            Label(""),
            Label("[Bash 模式]"),
            Label("  !command       - 执行bash命令"),
            Label(""),
            Label("[自然语言]"),
            Label("  scan 192.168.1.1   - AI自动扫描"),
            Label("  analyze            - AI分析发现"),
            Label("  report             - 生成报告"),
            Label(""),
            Label("[快捷键]"),
            Label("  Ctrl+C - 退出   F1 - 帮助"),
            Label(""),
            Label("按任意键关闭"),
            id="help_container"
        )

    def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()


class ClawAIChatApp(App):
    """ClawAI 对话式 TUI 应用（流式 + EventBus）"""

    CSS_PATH = Path(__file__).parent / "styles.tcss"

    TITLE = "ClawAI :: Pentest Terminal"

    BINDINGS = [
        Binding("f1", "show_help", "HELP"),
        Binding("ctrl+c", "quit", "EXIT", priority=True),
    ]

    def __init__(self, target: Optional[str] = None, config: dict = None):
        super().__init__()
        self.initial_target = target
        self.config = config or {}
        self.chat_cli = None
        self._processing = False
        self._dispatcher = None
        # 流式输出缓冲队列：工作线程 → Textual 主线程
        self._stream_queue: asyncio.Queue = None
        self._active_stream_id: int = 0

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

        # 初始化异步队列
        self._stream_queue = asyncio.Queue()

        # 初始化 ChatCLI
        self.chat_cli = ClawAIChatCLI(self.config)

        # 设置回调（旧接口兼容）
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
            welcome_msg = (
                f"ClawAI 渗透测试终端 v1.0\n"
                f"模型: {model} ({llm_type})\n"
                f"输入 /help 查看命令，! 执行Bash，或直接用自然语言与AI对话"
            )
        else:
            welcome_msg = (
                "ClawAI 渗透测试终端 v1.0\n"
                "输入 /help 查看命令，! 执行Bash，或直接用自然语言与AI对话\n\n"
                "[警告] 演示模式 - 未配置 API Key"
            )

        message_list.add_system_message(welcome_msg)

        # 初始目标
        if self.initial_target:
            self.chat_cli.set_target(self.initial_target)
            self.query_one(StatusBar).set_target(self.initial_target)
            message_list.add_system_message(f"已设置目标: {self.initial_target}")

        # 聚焦输入框
        from src.cli.tui.widgets.chat_input import ChatInput
        self.query_one(ChatInput).focus()

        # 启动流式队列消费协程
        asyncio.create_task(self._consume_stream_queue())

    def _subscribe_eventbus(self) -> None:
        """订阅 EventBus 全量事件"""
        bus = EventBus.get()
        bus.subscribe(EventType.TOOL, self._on_tool_event)
        bus.subscribe(EventType.STATE_CHANGED, self._on_state_event)

        # 新增：MESSAGE 事件 → 显示到消息列表
        try:
            bus.subscribe(EventType.MESSAGE, self._on_message_event)
        except Exception:
            pass

        # 新增：FINDING 事件 → 显示安全发现
        try:
            bus.subscribe(EventType.FINDING, self._on_finding_event)
        except Exception:
            pass

        # 新增：FLAG_FOUND 事件 → 高亮显示 Flag
        try:
            bus.subscribe(EventType.FLAG_FOUND, self._on_flag_event)
        except Exception:
            pass

        # 新增：PROGRESS 事件 → 更新状态栏
        try:
            bus.subscribe(EventType.PROGRESS, self._on_progress_event)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────
    # EventBus 回调（可能从非 Textual 线程调用，必须用 call_from_thread）
    # ──────────────────────────────────────────────────────────

    def _safe_call(self, fn, *args, **kwargs):
        """线程安全地在 Textual 主线程执行回调"""
        try:
            self.call_from_thread(fn, *args, **kwargs)
        except Exception as e:
            logger.debug(f"call_from_thread 失败: {e}")

    def _on_tool_event(self, event: "Event") -> None:
        status = event.data.get("status", "")
        name = event.data.get("name", "")
        self._safe_call(self._update_tool_panel, status, name, event.data)

    def _update_tool_panel(self, status: str, name: str, data: dict) -> None:
        from src.cli.tui.widgets.tool_output import ToolOutputPanel
        tool_panel = self.query_one(ToolOutputPanel)
        if status == "start":
            tool_panel.start_tool(name, data.get("args"))
        elif status == "complete":
            tool_panel.complete_tool(name, success=True)
        elif status == "failed":
            tool_panel.complete_tool(name, success=False)

    def _on_state_event(self, event: "Event") -> None:
        self._safe_call(self._update_status_bar,
                        event.data.get("state", "idle"),
                        event.data.get("details", ""))

    def _update_status_bar(self, state: str, details: str) -> None:
        from src.cli.tui.widgets.status_bar import StatusBar
        self.query_one(StatusBar).set_status(state, details)

    def _on_message_event(self, event: "Event") -> None:
        text = event.data.get("text", "")
        msg_type = event.data.get("type", "info")
        if text:
            self._safe_call(self._append_message_from_event, text, msg_type)

    def _append_message_from_event(self, text: str, msg_type: str) -> None:
        from src.cli.tui.widgets.message_list import MessageList
        ml = self.query_one(MessageList)
        # 若是活跃流式消息则追加；否则作为新 system 消息
        if self._active_stream_id:
            ml.append_to_message(self._active_stream_id, text)
        else:
            ml.add_system_message(text)

    def _on_finding_event(self, event: "Event") -> None:
        title = event.data.get("title", "")
        detail = event.data.get("detail", "")
        severity = event.data.get("severity", "info")
        if title:
            self._safe_call(self._add_finding, title, detail, severity)

    def _add_finding(self, title: str, detail: str, severity: str) -> None:
        from src.cli.tui.widgets.message_list import MessageList
        self.query_one(MessageList).add_finding_message(title, detail, severity)

    def _on_flag_event(self, event: "Event") -> None:
        flag = event.data.get("flag", "")
        location = event.data.get("location", "")
        method = event.data.get("method", "")
        if flag:
            self._safe_call(self._add_flag, flag, location, method)

    def _add_flag(self, flag: str, location: str, method: str) -> None:
        from src.cli.tui.widgets.message_list import MessageList
        from src.cli.tui.widgets.status_bar import StatusBar
        self.query_one(MessageList).add_flag_message(flag, location, method)
        self.query_one(StatusBar).set_status("flag_found", f"FLAG: {flag[:30]}")

    def _on_progress_event(self, event: "Event") -> None:
        # 兼容两种 PROGRESS 数据格式：
        # 1. emit_progress(percent, description)  → percent / description
        # 2. _execute_scan emit("PROGRESS", ...)  → iteration / phase
        iteration = event.data.get("iteration", 0)
        phase = event.data.get("phase", "")
        description = event.data.get("description", "")
        if description:
            detail = description
        elif iteration:
            detail = f"第 {iteration} 轮 · {phase}"
        else:
            detail = phase
        self._safe_call(self._update_status_bar, "scanning", detail)

    # ──────────────────────────────────────────────────────────
    # 旧回调（向下兼容）
    # ──────────────────────────────────────────────────────────

    def _handle_chat_message(self, role: str, content: str):
        from src.cli.tui.widgets.message_list import MessageList
        message_list = self.query_one(MessageList)
        if role == "system":
            message_list.add_system_message(content)
        elif role == "assistant":
            message_list.add_assistant_message(content)
        elif role == "user":
            message_list.add_user_message(content)

    def _handle_tool_execution(self, tool_name: str, params: dict, status: str):
        from src.cli.tui.widgets.tool_output import ToolOutputPanel
        tool_panel = self.query_one(ToolOutputPanel)
        if status == "running":
            tool_panel.start_tool(tool_name, params)
        elif status == "completed":
            tool_panel.complete_tool(tool_name, success=True)
        elif status == "failed":
            tool_panel.complete_tool(tool_name, success=False)

    def _handle_status_change(self, status: str, message: str):
        from src.cli.tui.widgets.status_bar import StatusBar
        self.query_one(StatusBar).set_status(status, message)

    # ──────────────────────────────────────────────────────────
    # 输入处理
    # ──────────────────────────────────────────────────────────

    def on_chat_input_submitted(self, event) -> None:
        """处理输入提交"""
        if self._processing:
            return
        text = event.text
        if not text.strip():
            return

        from src.cli.tui.widgets.message_list import MessageList
        self.query_one(MessageList).add_user_message(text)
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

    # ──────────────────────────────────────────────────────────
    # 真正的流式对话（token 逐步推入 MessageList）
    # ──────────────────────────────────────────────────────────

    async def _stream_chat(self, text: str) -> None:
        """流式 LLM 对话：token 实时推入 TUI MessageList"""
        from src.cli.tui.widgets.message_list import MessageList
        from src.cli.tui.widgets.status_bar import StatusBar

        message_list = self.query_one(MessageList)
        status_bar = self.query_one(StatusBar)

        # 创建流式占位消息
        stream_id = message_list.add_assistant_message("", streaming=True)
        self._active_stream_id = stream_id
        full_text = ""

        try:
            status_bar.set_status("thinking", "思考中...")

            # 记录用户消息到 session
            self.chat_cli.session.add_message("user", text)

            if not self.chat_cli.agent:
                full_text = "模拟模式: AI 未配置。请设置 API Key。"
                message_list.update_message(stream_id, full_text)
                return

            # 判断是否使用工具调用模式（OpenAI/DeepSeek）
            llm_type = self.chat_cli.agent.llm_client.get("type", "")
            if llm_type in ("openai", "deepseek"):
                # 工具调用模式：通过 _chat_with_tools_tui 获取流式回调
                full_text = await self._chat_with_tools_tui(text, stream_id)
            else:
                # 其他 provider：generate_text_stream 逐 token 推入
                full_text = await self._stream_generic(text, stream_id)

            # 同步到 session
            if full_text:
                self.chat_cli.session.add_message("assistant", full_text)

            # 更新状态栏目标
            if self.chat_cli.session.target:
                status_bar.set_target(self.chat_cli.session.target)

        except Exception as e:
            logger.error(f"流式对话失败: {e}")
            full_text = f"错误: {e}"
            message_list.update_message(stream_id, full_text)
            status_bar.set_status("error", str(e))

        finally:
            message_list.finalize_message(stream_id, full_text)
            self._active_stream_id = 0
            status_bar.set_status("idle", "")

    async def _stream_generic(self, text: str, stream_id: int) -> str:
        """非 OpenAI provider 的流式输出（通过 asyncio.Queue 桥接工作线程与主线程）"""
        from src.cli.tui.widgets.message_list import MessageList

        message_list = self.query_one(MessageList)
        full_text = ""
        token_queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        # 构建消息历史
        from src.cli.prompts.chat_system import CHAT_SYSTEM_PROMPT
        import platform as _plat
        system_prompt = CHAT_SYSTEM_PROMPT.format(
            platform=f"{_plat.system()} {_plat.release()}"
        )
        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.chat_cli.session.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": text})

        stream_error = None

        def _produce():
            nonlocal stream_error
            try:
                for token in self.chat_cli.agent.generate_text_stream(messages):
                    loop.call_soon_threadsafe(token_queue.put_nowait, token)
            except Exception as e:
                stream_error = e
            finally:
                loop.call_soon_threadsafe(token_queue.put_nowait, None)  # sentinel

        # 在线程池中执行阻塞式流式生成
        thread = threading.Thread(target=_produce, daemon=True)
        thread.start()

        # 在主线程消费 token
        while True:
            token = await token_queue.get()
            if token is None:
                break
            full_text += token
            message_list.append_to_message(stream_id, token)

        if stream_error:
            logger.error(f"LLM stream error: {stream_error}")
            full_text = f"AI 响应失败: {stream_error}"
            message_list.update_message(stream_id, full_text)

        return full_text

    async def _chat_with_tools_tui(self, text: str, stream_id: int) -> str:
        """OpenAI/DeepSeek 工具调用模式的 TUI 版本（无 console.print，全部走 MessageList）"""
        from src.cli.tui.widgets.message_list import MessageList
        from src.cli.tui.widgets.tool_output import ToolOutputPanel
        from src.cli.tools import get_tool_registry, ToolResult
        from src.cli.prompts.chat_system import CHAT_SYSTEM_PROMPT
        import platform as _plat
        import json as _json

        message_list = self.query_one(MessageList)
        tool_panel = self.query_one(ToolOutputPanel)

        system_prompt = CHAT_SYSTEM_PROMPT.format(
            platform=f"{_plat.system()} {_plat.release()}"
        )
        messages = [{"role": "system", "content": system_prompt}]
        for msg in self.chat_cli.session.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": text})

        tool_registry = get_tool_registry()
        openai_tools = tool_registry.get_openai_schemas()
        client = self.chat_cli.agent.llm_client["client"]
        model_id = self.chat_cli.agent.model_id
        loop = asyncio.get_event_loop()

        max_tool_rounds = 5
        full_response = ""

        for round_num in range(max_tool_rounds):
            text_parts = []
            tool_calls_map = {}
            stream_error = None
            token_queue: asyncio.Queue = asyncio.Queue()

            def _stream_llm():
                nonlocal stream_error
                try:
                    stream = client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        tools=openai_tools,
                        temperature=self.chat_cli.agent.temperature,
                        max_tokens=self.chat_cli.agent.max_new_tokens,
                        stream=True,
                    )
                    for chunk in stream:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if not delta:
                            continue
                        if delta.content:
                            loop.call_soon_threadsafe(
                                token_queue.put_nowait, ("text", delta.content)
                            )
                        if delta.tool_calls:
                            for tc_delta in delta.tool_calls:
                                loop.call_soon_threadsafe(
                                    token_queue.put_nowait, ("tool_delta", tc_delta)
                                )
                except Exception as e:
                    stream_error = e
                finally:
                    loop.call_soon_threadsafe(token_queue.put_nowait, None)

            thread = threading.Thread(target=_stream_llm, daemon=True)
            thread.start()

            # 消费 token，实时更新 MessageList
            while True:
                item = await token_queue.get()
                if item is None:
                    break
                kind, payload = item
                if kind == "text":
                    text_parts.append(payload)
                    full_response += payload
                    message_list.append_to_message(stream_id, payload)
                elif kind == "tool_delta":
                    tc_delta = payload
                    idx = tc_delta.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc_delta.id:
                        tool_calls_map[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_map[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc_delta.function.arguments

            if stream_error:
                logger.error(f"LLM 调用失败: {stream_error}")
                return f"AI 响应失败: {stream_error}"

            assistant_content = "".join(text_parts)

            # 无工具调用 → 返回最终结果
            if not tool_calls_map:
                return assistant_content

            # 构建 assistant 消息（含 tool_calls）
            tool_calls_list = []
            for idx in sorted(tool_calls_map.keys()):
                tc_info = tool_calls_map[idx]
                tool_calls_list.append({
                    "id": tc_info["id"],
                    "type": "function",
                    "function": {"name": tc_info["name"], "arguments": tc_info["arguments"]},
                })

            msg_dict = {"role": "assistant", "content": assistant_content or None}
            if tool_calls_list:
                msg_dict["tool_calls"] = tool_calls_list
            messages.append(msg_dict)

            # 执行工具调用
            for tc_info in tool_calls_list:
                tool_name = tc_info["function"]["name"]
                tool_args_str = tc_info["function"]["arguments"]
                call_id = tc_info["id"]

                try:
                    tool_args = _json.loads(tool_args_str)
                except _json.JSONDecodeError:
                    tool_args = {}

                tool_def = tool_registry.lookup(tool_name)
                if not tool_def:
                    message_list.add_system_message(f"未知工具: {tool_name}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": f"错误: 未知工具 {tool_name}",
                    })
                    continue

                # 危险工具提示（TUI 中以系统消息方式）
                if tool_def.is_dangerous:
                    display = tool_def.format_call_display(tool_args)
                    message_list.add_system_message(f"[危险操作] {display}\n（TUI 自动执行，请确认授权范围）")

                # 显示工具开始
                tool_panel.start_tool(tool_name, tool_args)

                # 执行工具（非阻塞）
                output_parts = []

                def on_output(line: str):
                    output_parts.append(line)

                result: ToolResult = await tool_def.execute(tool_args, on_output=on_output)

                if result.success:
                    tool_panel.complete_tool(tool_name, output=result.output[:200], success=True)
                else:
                    tool_panel.complete_tool(tool_name, success=False)
                    message_list.add_system_message(f"工具错误 [{tool_name}]: {result.error}")

                # 记录发现
                if result.success and result.output:
                    self.chat_cli.session.findings.append({
                        "type": f"tool:{tool_name}",
                        "output_preview": result.output[:200],
                    })

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result.to_text()[:4000],
                })

        return full_response or "工具调用轮次已达上限，请继续描述你的需求。"

    # ──────────────────────────────────────────────────────────
    # 流式队列消费（从外部线程写入 stream_queue 的 token）
    # ──────────────────────────────────────────────────────────

    async def _consume_stream_queue(self) -> None:
        """持续消费 _stream_queue 中的 token（供外部 EventBus 流式注入）"""
        from src.cli.tui.widgets.message_list import MessageList

        while True:
            try:
                item = await self._stream_queue.get()
                if item is None:
                    continue
                kind = item.get("kind")
                if kind == "token" and self._active_stream_id:
                    ml = self.query_one(MessageList)
                    ml.append_to_message(self._active_stream_id, item.get("text", ""))
            except Exception as e:
                logger.debug(f"stream_queue 消费失败: {e}")
                await asyncio.sleep(0.05)

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
