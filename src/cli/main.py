#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 主入口
黑客终端风格: 磷光绿 + 纯 ASCII + 干净利落
基于 Click 的命令行框架，支持斜杠命令、TUI 模式和增强 REPL
"""

import os
import sys
import asyncio
import logging
import subprocess
from typing import Optional

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

import click
from rich.console import Console
from rich.text import Text

console = Console()
logger = logging.getLogger(__name__)

# ── 黑客终端调色板 ──
# 主色: 磷光绿  辅色: 琥珀  警告: 红  暗色: 灰绿
GRN  = "rgb(0,255,65)"       # 磷光绿 (主色)
GRNB = "bold rgb(0,255,65)"  # 磷光绿加粗
AMBER = "rgb(255,191,0)"     # 琥珀色
RED  = "rgb(255,60,60)"      # 警告红
REDB = "bold rgb(255,60,60)" # 警告红加粗
DIM  = "rgb(80,110,80)"      # 暗绿灰
DIM2 = "rgb(50,70,50)"       # 更暗
WHT  = "rgb(200,230,200)"    # 淡绿白


def print_banner():
    """黑客终端横幅 — 纯 ASCII, 不依赖 Unicode 框线"""
    console.print()
    # 纯 ASCII Logo
    console.print(Text("    ___ _       _    ___ ___ ", style=GRN))
    console.print(Text("   / __(_)_ __ | |  / __/ __|", style=GRN))
    console.print(Text("  | (__| | '_ \\| |_| (__\\__ \\", style=GRN))
    console.print(Text("   \\___|_| .__/|____\\___|___/", style=GRN))
    console.print(Text("         |_|", style=GRN))
    # 分隔 + 版本
    console.print(Text("    ----------------------------------------", style=DIM))
    console.print(Text("    v2.0 | AI Penetration Testing Assistant", style=DIM))
    console.print()


# ── Click 命令组 ──

@click.group(invoke_without_command=True)
@click.option("-t", "--target", help="设置目标地址")
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.version_option(version="2.0.0", prog_name="clawai")
@click.pass_context
def cli(ctx, target, verbose):
    """ClawAI - AI驱动的渗透测试助手"""
    ctx.ensure_object(dict)
    ctx.obj["target"] = target
    ctx.obj["verbose"] = verbose
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat, target=target)


@cli.command()
@click.option("-t", "--target", help="设置目标地址")
@click.option("-m", "--model", help="指定AI模型")
@click.option("-d", "--debug", is_flag=True, help="调试模式")
@click.option("--session", "session_id", help="加载指定会话 ID")
def chat(target, model, debug, session_id):
    """启动 AI 对话模式（默认）"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    asyncio.run(run_chat_mode(target=target, model=model, debug=debug, session_id=session_id))


@cli.command()
@click.argument("target")
@click.option("--tools", default="nmap,nuclei", help="使用的工具（逗号分隔）")
@click.option("--output", help="输出报告路径")
def scan(target, tools, output):
    """快速扫描模式"""
    asyncio.run(run_scan_mode(target=target, tools=tools, output=output))


@cli.command()
@click.option("-t", "--target", help="设置目标地址")
@click.option("--no-tui", is_flag=True, help="TUI 失败时强制 REPL 模式")
def tui(target, no_tui):
    """启动 Textual TUI 模式"""
    if no_tui:
        asyncio.run(run_chat_mode(target=target))
        return
    try:
        from src.cli.tui.app import run_tui
        asyncio.run(run_tui(target=target))
    except Exception as e:
        console.print(Text(f"  TUI 启动失败: {e}", style=AMBER))
        console.print(Text("  降级到 REPL 模式...", style=DIM))
        asyncio.run(run_chat_mode(target=target))


@cli.command()
@click.argument("action", type=click.Choice(["list", "status", "check"]))
@click.option("--tool", help="指定工具名称")
def tools(action, tool):
    """工具管理"""
    from src.cli.commands.tools import ToolsCommand
    cmd = ToolsCommand()
    cmd.execute([action] + ([f"--tool={tool}"] if tool else []), {"console": console})


@cli.command()
def status():
    """查看系统状态"""
    from src.cli.commands.status import StatusCommand
    cmd = StatusCommand()
    cmd.execute([], {"console": console})


# ── Session 子命令组 ──

@cli.group()
def session():
    """会话管理"""
    pass


@session.command("list")
def session_list():
    from src.cli.commands.session import SessionCommand
    cmd = SessionCommand()
    cmd.execute(["list"], {"console": console})


@session.command("load")
@click.argument("session_id")
@click.option("-m", "--model", help="指定AI模型")
def session_load(session_id, model):
    asyncio.run(run_chat_mode(target=None, model=model, session_id=session_id))


@session.command("delete")
@click.argument("session_id")
def session_delete(session_id):
    from src.cli.commands.session import SessionCommand
    cmd = SessionCommand()
    cmd.execute(["delete", session_id], {"console": console})


@session.command("export")
@click.argument("session_id")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "json", "html"]),
              default="markdown", help="导出格式")
@click.option("-o", "--output", help="输出文件路径")
def session_export(session_id, fmt, output):
    from src.cli.commands.session import SessionCommand
    cmd = SessionCommand()
    cmd.execute(["export", session_id, "--format", fmt] + ([f"--output={output}"] if output else []),
                {"console": console})


# ── REPL 对话模式 ──

async def run_chat_mode(target: Optional[str] = None, model: Optional[str] = None,
                        debug: bool = False, session_id: Optional[str] = None):
    """黑客终端风格 REPL"""
    print_banner()

    # 快捷提示行
    console.print(Text("    /help", style=GRN), Text(" | ", style=DIM2),
                  Text("/nmap", style=GRN), Text(" | ", style=DIM2),
                  Text("!bash", style=AMBER), Text(" | ", style=DIM2),
                  Text("natural language", style=DIM))
    console.print()

    # 首次引导
    from pathlib import Path as _P
    _welcome_path = _P.home() / ".clawai" / ".welcomed"
    if not _welcome_path.exists():
        console.print(Text("    -- ClawAI Quick Start --", style=GRN))
        console.print(Text("    > ", style=GRN), Text("scan example.com", style=WHT))
        console.print(Text("    > ", style=GRN), Text("/nmap 192.168.1.1", style=WHT))
        console.print(Text("    > ", style=GRN), Text("/help", style=WHT))
        console.print()
        _welcome_path.parent.mkdir(parents=True, exist_ok=True)
        _welcome_path.touch()

    if target:
        console.print(Text(f"    [*] target: ", style=GRN), Text(target, style=GRNB))
        console.print()

    # ── 启动时检测未完成会话 ──
    if not session_id:
        try:
            from src.cli.session_store import SessionStore
            _recent = SessionStore().list_sessions()
            # 找到最近的未完成会话（phase 不是 idle/completed）
            _incomplete = [
                s for s in _recent
                if s.get("phase", "idle") not in ("idle", "completed", "")
                and s.get("findings_count", 0) + s.get("messages_count", 0) > 0
            ]
            if _incomplete:
                s0 = _incomplete[0]
                console.print(Text(
                    f"    [!] 发现未完成会话: {s0['session_id'][:24]}",
                    style=AMBER
                ))
                console.print(Text(
                    f"        目标: {s0.get('target') or '-'} | 阶段: {s0.get('phase')} | "
                    f"发现: {s0.get('findings_count', 0)} | 消息: {s0.get('messages_count', 0)}",
                    style=DIM
                ))
                console.print(Text(
                    f"        恢复: /session load {s0['session_id']}  或直接继续新会话",
                    style=DIM
                ))
                console.print()
        except Exception as e:
            logger.debug(f"会话恢复检查失败（不影响启动）: {e}")

    # 初始化 ChatCLI
    from src.cli.chat_cli import ClawAIChatCLI

    config = {}
    if model:
        provider = "deepseek"
        if model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
            provider = "openai"
        elif model.startswith("claude-"):
            provider = "anthropic"
        config["llm"] = {"model_id": model, "provider": provider}

    chat_cli = ClawAIChatCLI(config)

    if session_id:
        if chat_cli.load_session(session_id):
            s = chat_cli.session
            console.print(Text(f"    [+] session: ", style=GRN), Text(session_id, style=GRNB))
            console.print(Text(f"        target: {s.target or '-'} | phase: {s.phase} | findings: {len(s.findings)}", style=DIM))
            console.print()
        else:
            console.print(Text(f"    [-] session not found: {session_id}", style=RED))

    if target:
        chat_cli.set_target(target)

    from src.cli.slash_dispatcher import SlashDispatcher
    from src.cli.commands import get_registry

    registry = get_registry()
    dispatcher = SlashDispatcher(registry, chat_cli)

    # 输入读取：在线程池里用原生 input()，兼容所有终端（Windows cmd/PowerShell/Linux）
    # 不使用 prompt_toolkit，避免 Windows cmd.exe 下的 EOFError 闪退问题
    def _sync_input() -> str:
        try:
            return input("> ")
        except EOFError:
            return "__EOF__"

    async def _read_input() -> str:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_input)
        if result == "__EOF__":
            raise EOFError
        return result

    async def _run_direct_tool(tool_name: str, args: list, chat_cli_obj, cons):
        """直接工具执行"""
        from src.cli.tools import get_tool_registry, ToolResult
        from rich.live import Live
        from rich.text import Text

        registry = get_tool_registry()
        tool_def = registry.lookup(tool_name)
        if not tool_def:
            cons.print(Text(f"    [-] tool not found: {tool_name}", style=RED))
            return

        if not args:
            schema = tool_def.input_schema
            props = schema.get("properties", {})
            required = schema.get("required", [])
            cons.print(Text(f"    /{tool_name}", style=GRNB), Text(f" -- {tool_def.description}", style=DIM))
            cons.print(Text(f"    usage: /{tool_name} " + " ".join(
                f"<{p}>" if p in required else f"[{p}]" for p in props
            ), style=DIM))
            return

        # 构建工具参数
        tgt = args[0]
        tool_args = {"target": tgt}
        if len(args) > 1 and tool_name == "nmap":
            tool_args["scan_type"] = args[1]
        elif len(args) > 1 and tool_name == "nuclei":
            tool_args["templates"] = args[1]
        elif len(args) > 1 and tool_name == "sqlmap":
            tool_args["url"] = args[0]
            tool_args.pop("target", None)

        # 权限检查 — 简洁警告
        if tool_def.is_dangerous:
            from rich.prompt import Prompt
            display = tool_def.format_call_display(tool_args)
            _print_tool_card(cons, tool_name, tool_args, "DANGER", "⚠")
            action = Prompt.ask("    execute?", choices=["y", "n"], default="n")
            if action == "n":
                cons.print(Text("    [-] rejected", style=DIM))
                return

        # 执行 — 统一工具卡片
        _print_tool_card(cons, tool_name, tool_args, "RUNNING", "▶")

        try:
            from src.shared.backend.events import EventBus
            EventBus.get().emit_tool("start", tool_name, args=tool_args)
        except Exception:
            pass

        # Spinner → 纯输出
        from src.cli.spinner import AsyncSpinner, SpinnerMode
        tool_spinner = AsyncSpinner(cons)
        tool_spinner.start(mode=SpinnerMode.TOOL_USE, verb=f"{tool_name}")
        live_output = Text()
        output_started = False

        with Live(tool_spinner.render_line(), console=cons, refresh_per_second=10, vertical_overflow="visible") as live:
            def on_output(line: str):
                nonlocal output_started
                if not output_started:
                    tool_spinner.stop()
                    output_started = True
                live_output.append(line + "\n")
                live.update(live_output)
            result: ToolResult = await tool_def.execute(tool_args, on_output=on_output)

        if not output_started:
            tool_spinner.stop()

        # 结果状态
        _print_tool_status(cons, result)

        try:
            from src.shared.backend.events import EventBus
            EventBus.get().emit_tool("complete", tool_name, result=result.to_dict())
        except Exception:
            pass

        if result.success and result.output:
            chat_cli_obj.session.findings.append({
                "type": f"tool:{tool_name}",
                "output_preview": result.output[:200],
            })
            chat_cli_obj._autosave()

    # ── 主 REPL 循环 ──
    while True:
        try:
            user_input = (await _read_input()).strip()
            if not user_input:
                continue

            result = dispatcher.dispatch(user_input)

            if result.action == "slash_cmd":
                cmd_cls = result.command_meta.load()
                cmd = cmd_cls() if isinstance(cmd_cls, type) else cmd_cls
                output = cmd.execute(result.args, {"chat_cli": chat_cli, "console": console})
                if output == "__EXIT__":
                    chat_cli.save_session()
                    console.print(Text(f"    [*] saved: {chat_cli.session.session_id}", style=DIM))
                    console.print()
                    break
                if output:
                    console.print(output)
                continue

            elif result.action == "bash_cmd":
                output = _run_bash(result.args[0])
                console.print(output)
                continue

            elif result.action == "unknown_slash":
                console.print(Text(f"    [-] unknown: /{result.args[0]}", style=RED))
                if result.passthrough:
                    suggestions = result.passthrough
                    console.print(Text(f"        did you mean: {', '.join(f'/{s}' for s in suggestions)}?", style=DIM))
                continue

            elif result.action == "direct_tool":
                await _run_direct_tool(result.tool_name, result.args, chat_cli, console)
                continue

            # 追加指令
            if user_input.startswith(("追加指令:", "追加:", "add instruction:", "instruct:")):
                _, _, instruction = user_input.partition(":")
                instruction = instruction.strip()
                if instruction:
                    chat_cli.record_intervention("input", instruction)
                    console.print(Text(f"    [*] injected: {instruction}", style=GRN))
                continue

            # 自然语言 → AI
            response = await chat_cli.chat(user_input)
            if not getattr(chat_cli, '_streamed', False):
                console.print(response)

        except EOFError:
            chat_cli.save_session()
            console.print(Text(f"    [*] saved: {chat_cli.session.session_id}", style=DIM))
            break
        except KeyboardInterrupt:
            chat_cli.save_session()
            console.print(Text(f"\n    [*] saved: {chat_cli.session.session_id}", style=DIM))
            break
        except asyncio.CancelledError:
            console.print(Text("\n    [-] cancelled", style=AMBER))
            continue
        except Exception as e:
            logger.error(f"处理失败: {e}")
            # 使用友好的错误处理器
            from src.cli.error_handler import handle_error
            handle_error(e, console)


def _run_bash(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "    [-] timeout (30s)"
    except Exception as e:
        return f"    [-] error: {e}"


def _print_tool_card(console_obj, tool_name: str, args: dict, status: str, icon: str):
    """打印工具执行卡片 - 统一格式

    Args:
        console_obj: rich.Console 实例
        tool_name: 工具名称
        args: 工具参数
        status: "RUNNING", "DANGER", "DONE"
        icon: 图标 "▶", "⚠", "✓"
    """
    from rich.panel import Panel
    from rich.text import Text

    # 格式化参数
    parts = []
    for k, v in args.items():
        if v:
            parts.append(f"{k}={v}")
    arg_str = " ".join(parts) if parts else ""

    # 状态颜色
    color_map = {"RUNNING": GRN, "DANGER": AMBER, "DONE": GRN}
    status_color = color_map.get(status, WHT)

    header = Text(f"{icon} {tool_name}", style=status_color)
    if arg_str:
        header.append(f" {arg_str}", style=DIM)

    panel = Panel(
        Text("", style=""),
        title=header,
        title_align="left",
        border_style=DIM,
        padding=(0, 1),
        expand=False,
    )
    console_obj.print(panel)


def _print_tool_status(console_obj, result: "ToolResult"):
    """打印工具执行状态 - 统一格式"""
    from rich.text import Text

    if result.success:
        console_obj.print(Text(f"    ✓ 完成 {result.duration:.1f}s", style=GRN))
    else:
        console_obj.print(Text(f"    ✗ 失败 {result.duration:.1f}s", style=RED))
        if result.error:
            console_obj.print(Text(f"        {result.error}", style=DIM))


async def run_scan_mode(target: str, tools: str, output: Optional[str]):
    print_banner()
    console.print(Text(f"    [*] target: {target}", style=GRNB))
    console.print(Text(f"    [*] tools: {tools}", style=DIM))
    console.print()

    from src.cli.chat_cli import ClawAIChatCLI
    chat_cli = ClawAIChatCLI()
    chat_cli.set_target(target)

    response = await chat_cli.chat(f"扫描 {target}")
    console.print(f"\n{response}")

    if output:
        report = await chat_cli.chat("生成报告")
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(report)
            console.print(Text(f"    [+] report saved: {output}", style=GRN))
        except Exception as e:
            console.print(Text(f"    [-] save failed: {e}", style=RED))


def main():
    cli()


if __name__ == "__main__":
    main()
