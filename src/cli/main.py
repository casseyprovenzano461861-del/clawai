#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 主入口
提供命令行界面，支持对话式交互和快速命令
"""

import os
import sys
import argparse
import asyncio
import logging
from typing import Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

from rich.console import Console
from rich.text import Text
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)


def print_banner():
    """打印横幅"""
    from rich.text import Text
    
    banner = r"""
    ██████╗██╗     ███████╗ █████╗  ██████╗ ██╗  ██╗
   ██╔════╝██║     ██╔════╝██╔══██╗██╔═══██╗╚██╗██╔╝
   ██║     ██║     █████╗  ███████║██║   ██║ ╚███╔╝ 
   ██║     ██║     ██╔══╝  ██╔══██║██║   ██║ ██╔██╗ 
   ╚██████╗███████╗███████╗██║  ██║╚██████╔╝██╔╝ ██╗
    ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
                 [ AI 渗透测试助手 ]
    """
    text = Text(banner, style="bold cyan")
    console.print(text)
    console.print(Text("━" * 55, style="dim"))
    console.print(Text("⚡ 版本 2.0  ⚡ Skills: 27  ⚡ Tools: 63", style="green"))
    console.print()


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        prog="clawai",
        description="ClawAI - AI驱动的渗透测试助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动对话模式（默认）
  clawai
  clawai chat

  # 带目标启动
  clawai --target example.com
  clawai chat -t 192.168.1.1

  # 快速扫描模式
  clawai scan example.com

  # 工具管理
  clawai tools list
  clawai tools status

  # 查看状态
  clawai status

  # 会话管理
  clawai session list
  clawai session load <session_id>
  clawai session delete <session_id>
  clawai session delete all
  clawai session export <session_id> -f html
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # chat 子命令（默认）
    chat_parser = subparsers.add_parser("chat", help="启动AI对话模式")
    chat_parser.add_argument("-t", "--target", type=str, help="设置目标地址")
    chat_parser.add_argument("-m", "--model", type=str, help="指定AI模型")
    chat_parser.add_argument("-d", "--debug", action="store_true", help="调试模式")

    # scan 子命令
    scan_parser = subparsers.add_parser("scan", help="快速扫描模式")
    scan_parser.add_argument("target", type=str, help="目标地址")
    scan_parser.add_argument("--tools", type=str, default="nmap,nuclei",
                            help="使用的工具（逗号分隔）")
    scan_parser.add_argument("--output", type=str, help="输出报告路径")

    # tools 子命令
    tools_parser = subparsers.add_parser("tools", help="工具管理")
    tools_parser.add_argument("action", choices=["list", "status", "check"],
                             help="工具操作")
    tools_parser.add_argument("--tool", type=str, help="指定工具")

    # status 子命令
    status_parser = subparsers.add_parser("status", help="查看系统状态")

    # session 子命令
    session_parser = subparsers.add_parser("session", help="会话管理")
    session_sub = session_parser.add_subparsers(dest="session_action", help="会话操作")

    # session list
    session_sub.add_parser("list", help="列出所有已保存会话")

    # session load
    load_p = session_sub.add_parser("load", help="加载会话并进入对话模式")
    load_p.add_argument("session_id", type=str, help="会话 ID")
    load_p.add_argument("-m", "--model", type=str, help="指定AI模型")

    # session delete
    del_p = session_sub.add_parser("delete", help="删除指定会话")
    del_p.add_argument("session_id", type=str, help="会话 ID（或 'all' 删除全部）")

    # session export
    exp_p = session_sub.add_parser("export", help="导出会话报告")
    exp_p.add_argument("session_id", type=str, help="会话 ID")
    exp_p.add_argument("-f", "--format", choices=["markdown", "json", "html"],
                       default="markdown", help="导出格式（默认 markdown）")
    exp_p.add_argument("-o", "--output", type=str, help="输出文件路径（不含扩展名）")

    # 全局参数
    parser.add_argument("-t", "--target", type=str, help="设置目标地址（快捷方式）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    return parser.parse_args()


async def run_chat_mode(target: Optional[str] = None, model: Optional[str] = None,
                        debug: bool = False, session_id: Optional[str] = None):
    """运行 AI 对话模式"""
    print_banner()

    console.print("[dim]输入目标地址开始测试，或输入 'help' 查看帮助[/]")
    console.print("[dim]提示: Tab 键补全命令，↑↓ 键浏览历史，Ctrl-R 搜索历史[/]")
    console.print()

    # 首次使用引导
    from pathlib import Path as _P
    _welcome_path = _P.home() / ".clawai" / ".welcomed"
    if not _welcome_path.exists():
        console.print(Panel(
            "[bold green]欢迎使用 ClawAI![/]\n\n"
            "快速开始:\n"
            "  1. [cyan]扫描 192.168.1.1[/] — 对目标执行安全扫描\n"
            "  2. [cyan]快速扫描 example.com[/] — 3轮快速扫描\n"
            "  3. [cyan]help[/] — 查看所有命令\n"
            "  4. [cyan]配置[/] — 查看当前 AI 配置\n\n"
            "[dim]输入 Tab 键可自动补全命令[/]",
            title="新手指南",
            border_style="green",
            expand=False,
        ))
        console.print()
        _welcome_path.parent.mkdir(parents=True, exist_ok=True)
        _welcome_path.touch()

    if target:
        console.print(f"[green]🎯 目标已设置: {target}[/]")
        console.print()

    # 使用真正的 AI 对话系统
    from src.cli.chat_cli import ClawAIChatCLI

    config = {}
    if model:
        # 根据 model 名称推断 provider
        provider = "deepseek"
        if model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
            provider = "openai"
        elif model.startswith("claude-"):
            provider = "anthropic"
        config["llm"] = {"model_id": model, "provider": provider}

    cli = ClawAIChatCLI(config)

    # 恢复历史会话
    if session_id:
        if cli.load_session(session_id):
            s = cli.session
            console.print(f"[green]✅ 已加载会话: [bold]{session_id}[/][/]")
            console.print(f"[dim]   目标: {s.target or '未设置'}  阶段: {s.phase}  发现: {len(s.findings)} 条  消息: {len(s.messages)} 条[/]")
            console.print()
        else:
            console.print(f"[red]⚠️ 未找到会话 {session_id}，已创建新会话。[/]")

    if target:
        cli.set_target(target)

    # 初始化 prompt_toolkit PromptSession（带补全+历史）
    _prompt_session = None
    try:
        from src.cli.completer import get_prompt_session
        _prompt_session = get_prompt_session()
        logger.debug("命令补全已启用 (prompt_toolkit)")
    except Exception as e:
        logger.debug(f"命令补全初始化失败，使用基础输入: {e}")

    async def _read_input() -> str:
        """读取用户输入，优先使用 PromptSession，失败回退 console.input()"""
        if _prompt_session is not None:
            try:
                return await _prompt_session.prompt_async("❯ ")
            except (EOFError, KeyboardInterrupt):
                raise
            except Exception:
                pass
        # fallback
        return console.input("[bold cyan]❯[/] ")

    while True:
        try:
            user_input = (await _read_input()).strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye", "退出"]:
                # 退出前自动保存
                cli.save_session()
                console.print(f"\n[dim]会话已保存: {cli.session.session_id}[/]")
                console.print("\n[green]👋 再见！[/]")
                break

            # ---- 内联 session 命令 ----
            cmd_lower = user_input.lower().strip()

            if cmd_lower in ("session list", "sessions"):
                _session_list()
                continue

            if cmd_lower == "session save":
                if cli.save_session():
                    console.print(f"[green]✅ 会话已保存: {cli.session.session_id}[/]")
                else:
                    console.print("[red]保存失败[/]")
                continue

            if cmd_lower.startswith("session export"):
                parts = cmd_lower.split()
                fmt = parts[2] if len(parts) >= 3 and parts[2] in ("json", "html", "markdown") else "markdown"
                _session_export(cli.session.session_id, fmt, None)
                continue

            if cmd_lower.startswith("session load "):
                sid = user_input.split(None, 2)[2].strip()
                if cli.load_session(sid):
                    s = cli.session
                    console.print(f"[green]✅ 已切换到会话: {sid}[/]")
                    console.print(f"[dim]   目标: {s.target or '未设置'}  阶段: {s.phase}  发现: {len(s.findings)} 条[/]")
                else:
                    console.print(f"[red]未找到会话: {sid}[/]")
                continue

            # ---- 用户干预控制命令 ----
            if cmd_lower in ("pause", "暂停"):
                cli.record_intervention("command", "pause")
                if getattr(cli, '_scan_state', None):
                    cli._scan_state.pause()
                    console.print("[yellow]已暂停扫描，输入 resume 继续[/]")
                else:
                    console.print("[dim]当前无活跃扫描[/]")
                continue

            if cmd_lower in ("resume", "继续", "恢复"):
                cli.record_intervention("command", "resume")
                if getattr(cli, '_scan_state', None):
                    cli._scan_state.resume()
                    console.print("[green]已恢复扫描[/]")
                else:
                    console.print("[dim]当前无活跃扫描[/]")
                continue

            if cmd_lower in ("stop", "停止", "中止"):
                cli.record_intervention("command", "stop")
                console.print("[red]⏹ 已发送停止指令[/]")
                continue

            if cmd_lower.startswith(("追加指令:", "追加:", "add instruction:", "instruct:")):
                _, _, instruction = user_input.partition(":")
                instruction = instruction.strip()
                if instruction:
                    cli.record_intervention("input", instruction)
                    console.print(f"[cyan]📝 干预指令已记录: {instruction}[/]")
                continue
            # ---- end 内联命令 ----

            # 显示用户消息
            console.print(f"\n[yellow]👤 You[/]")
            console.print(Panel(user_input, border_style="yellow", expand=False))

            # 处理并显示响应
            response = await cli.chat(user_input)
            if getattr(cli, '_streamed', False):
                # 流式已渲染完毕，仅打印分隔线
                console.print()
            else:
                console.print(f"\n[cyan]ClawAI[/]")
                console.print(Panel(response, border_style="cyan", expand=False))

        except EOFError:
            break
        except KeyboardInterrupt:
            cli.save_session()
            console.print(f"\n[dim]会话已保存: {cli.session.session_id}[/]")
            console.print("[green]再见！[/]")
            break
        except asyncio.CancelledError:
            console.print("\n[yellow]操作已取消[/]\n")
            continue
        except Exception as e:
            logger.error(f"处理失败: {e}")
            console.print(f"\n[red]错误: {e}[/]\n")


async def run_scan_mode(target: str, tools: str, output: Optional[str]):
    """运行快速扫描模式"""
    print_banner()
    console.print(f"[bold cyan]目标:[/] {target}")
    console.print(f"[bold cyan]工具:[/] {tools}")
    console.print()

    from src.cli.chat_cli import ClawAIChatCLI

    cli = ClawAIChatCLI()
    cli.set_target(target)

    # 执行扫描
    response = await cli.chat(f"扫描 {target}")
    console.print(f"\n[bold green]结果:[/]\n{response}")

    # 如果需要输出报告
    if output:
        report = await cli.chat("生成报告")
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(report)
            console.print(f"\n[green]报告已保存到: {output}[/]")
        except Exception as e:
            console.print(f"\n[red]保存报告失败: {e}[/]")


def run_tools_action(action: str, tool: Optional[str]):
    """运行工具管理"""
    print_banner()

    try:
        import requests
    except ImportError:
        console.print("[red]需要安装 requests 库[/]")
        return

    base_url = get_config().backend_url

    try:
        if action == "list":
            response = requests.get(f"{base_url}/api/v1/tools", timeout=5)
            if response.status_code == 200:
                tools = response.json()
                console.print("[bold]可用工具:[/]")
                for t in tools:
                    status = "✅" if t.get('available') else "❌"
                    console.print(f"  {status} {t['name']}: {t.get('description', '')}")
            else:
                console.print(f"[red]获取工具列表失败: {response.status_code}[/]")

        elif action == "status":
            response = requests.get(f"{base_url}/api/v1/tools/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                console.print("[bold]工具状态:[/]")
                for name, info in status.items():
                    installed = "✅ 已安装" if info.get('installed') else "❌ 未安装"
                    version = info.get('version', '未知')
                    console.print(f"  {name}: {installed}, 版本: {version}")
            else:
                console.print(f"[red]获取工具状态失败: {response.status_code}[/]")

        elif action == "check":
            response = requests.get(f"{base_url}/api/v1/tools/check", timeout=5)
            if response.status_code == 200:
                console.print("[green]工具检查完成[/]")
            else:
                console.print(f"[red]工具检查失败: {response.status_code}[/]")

    except requests.exceptions.ConnectionError:
        console.print("[red]无法连接到后端服务。请确保服务已启动。[/]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/]")


def run_status():
    """运行状态检查"""
    print_banner()

    try:
        import requests
    except ImportError:
        console.print("[red]需要安装 requests 库[/]")
        return

    from src.cli.config import get_config
    base_url = get_config().backend_url

    try:
        # 检查后端
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            console.print("[bold green]✅ 后端服务: 运行正常[/]")
            console.print(f"  状态: {health.get('status')}")
            console.print(f"  版本: {health.get('version')}")
        else:
            console.print("[bold red]❌ 后端服务: 异常[/]")

        # 检查前端
        try:
            requests.get("http://localhost:5173", timeout=5)
            console.print("[bold green]✅ 前端服务: 运行正常[/]")
        except Exception:
            console.print("[bold yellow]⚠️ 前端服务: 未运行[/]")

    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ 后端服务: 未启动[/]")
        console.print("[bold yellow]⚠️ 前端服务: 未运行[/]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/]")


def run_session_action(args):
    """处理 session 子命令"""
    from rich.table import Table
    from src.cli.session_store import SessionStore

    action = getattr(args, "session_action", None)

    if action is None or action == "list":
        _session_list()
    elif action == "load":
        asyncio.run(run_chat_mode(
            target=None,
            model=getattr(args, "model", None),
            session_id=args.session_id,
        ))
    elif action == "delete":
        _session_delete(args.session_id)
    elif action == "export":
        _session_export(args.session_id, args.format, getattr(args, "output", None))
    else:
        console.print(f"[red]未知操作: {action}[/]")
        console.print("用法: clawai session <list|load|delete|export>")


def _session_list():
    """列出所有已保存会话"""
    from rich.table import Table
    from src.cli.session_store import SessionStore

    sessions = SessionStore().list_sessions()
    if not sessions:
        console.print("[yellow]暂无保存的会话。[/]")
        console.print("[dim]提示: 执行扫描后会话会自动保存到 ~/.clawai/sessions/[/]")
        return

    table = Table(title=f"已保存会话 ({len(sessions)} 个)", border_style="cyan")
    table.add_column("会话 ID", style="bold cyan", no_wrap=True)
    table.add_column("目标", style="white")
    table.add_column("阶段", style="yellow")
    table.add_column("发现数", style="bold red", justify="right")
    table.add_column("消息数", justify="right")
    table.add_column("干预数", style="magenta", justify="right")
    table.add_column("更新时间", style="dim")

    for s in sessions:
        table.add_row(
            s.get("session_id", ""),
            s.get("target", "-") or "-",
            s.get("phase", "-"),
            str(s.get("findings_count", 0)),
            str(s.get("messages_count", 0)),
            str(s.get("interventions_count", 0)),
            s.get("updated_at", "")[:19],
        )

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]clawai session load <session_id>   加载会话[/]")
    console.print("[dim]clawai session export <session_id> 导出报告[/]")
    console.print("[dim]clawai session delete <session_id> 删除会话[/]")


def _session_delete(session_id: str):
    """删除会话"""
    from src.cli.session_store import SessionStore
    from rich.prompt import Confirm

    store = SessionStore()

    if session_id.lower() == "all":
        confirm = Confirm.ask("[bold red]确认删除所有会话？此操作不可撤销[/]")
        if confirm:
            count = store.delete_all()
            console.print(f"[green]已删除 {count} 个会话。[/]")
        else:
            console.print("[yellow]已取消。[/]")
        return

    data = store.load(session_id)
    if data is None:
        console.print(f"[red]未找到会话: {session_id}[/]")
        return

    target = data.get("target") or "未知"
    confirm = Confirm.ask(f"确认删除会话 [cyan]{session_id}[/] (目标: {target})")
    if confirm:
        if store.delete(session_id):
            console.print(f"[green]已删除会话: {session_id}[/]")
        else:
            console.print(f"[red]删除失败: {session_id}[/]")
    else:
        console.print("[yellow]已取消。[/]")


def _session_export(session_id: str, fmt: str, output: Optional[str]):
    """导出会话报告"""
    from src.cli.session_store import SessionStore
    from src.cli.exporter import export_session
    from pathlib import Path

    data = SessionStore().load(session_id)
    if data is None:
        console.print(f"[red]未找到会话: {session_id}[/]")
        return

    export_dir = Path(output).parent if output else None
    filename = Path(output).stem if output else None

    try:
        path = export_session(data, fmt=fmt, filename=filename, export_dir=export_dir)
        console.print(f"[green]✅ 报告已导出:[/] {path}")
    except Exception as e:
        console.print(f"[red]导出失败: {e}[/]")


def main():
    """主入口"""
    args = parse_arguments()

    # 设置日志级别
    if getattr(args, 'verbose', False) or getattr(args, 'debug', False):
        logging.basicConfig(level=logging.DEBUG)

    # 处理全局target参数
    target = getattr(args, 'target', None)

    # 根据命令执行
    if args.command == "chat":
        asyncio.run(run_chat_mode(
            target=args.target,
            model=getattr(args, 'model', None),
            debug=getattr(args, 'debug', False)
        ))
    elif args.command == "scan":
        asyncio.run(run_scan_mode(
            target=args.target,
            tools=args.tools,
            output=getattr(args, 'output', None)
        ))
    elif args.command == "tools":
        run_tools_action(args.action, getattr(args, 'tool', None))
    elif args.command == "status":
        run_status()
    elif args.command == "session":
        run_session_action(args)
    else:
        # 默认进入对话模式
        asyncio.run(run_chat_mode(target=target))


def cli():
    """CLI入口点（供setup.py使用）"""
    main()


if __name__ == "__main__":
    main()
