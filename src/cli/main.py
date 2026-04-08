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

    # 全局参数
    parser.add_argument("-t", "--target", type=str, help="设置目标地址（快捷方式）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    return parser.parse_args()


async def run_chat_mode(target: Optional[str] = None, model: Optional[str] = None,
                        debug: bool = False):
    """运行 AI 对话模式"""
    print_banner()
    
    console.print("[dim]输入目标地址开始测试，或输入 'help' 查看帮助[/]")
    console.print()
    
    if target:
        console.print(f"[green]🎯 目标已设置: {target}[/]")
        console.print()
    
    # 使用真正的 AI 对话系统
    from src.cli.chat_cli import ClawAIChatCLI
    
    config = {}
    if model:
        config["llm"] = {"model_id": model}
    
    cli = ClawAIChatCLI(config)
    
    if target:
        cli.set_target(target)
    
    while True:
        try:
            user_input = console.input("[bold cyan]❯[/] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye", "退出"]:
                console.print("\n[green]👋 再见！[/]")
                break
            
            # 显示用户消息
            console.print(f"\n[yellow]👤 You[/]")
            console.print(Panel(user_input, border_style="yellow", expand=False))
            
            # 处理并显示响应
            response = await cli.chat(user_input)
            console.print(f"\n[cyan]🤖 ClawAI[/]")
            console.print(Panel(response, border_style="cyan", expand=False))
            
        except KeyboardInterrupt:
            console.print("\n[green]👋 再见！[/]")
            break
        except Exception as e:
            logger.error(f"处理失败: {e}")
            console.print(f"\n[red]错误: {e}[/]\n")


async def run_simple_mode(target: Optional[str] = None, config: dict = None):
    """炫酷对话模式"""
    try:
        # 尝试使用炫酷版 UI
        from src.cli.cool_ui import CoolClawAIChat
        chat = CoolClawAIChat(target=target)
        chat.run()
    except ImportError as e:
        logger.warning(f"炫酷UI不可用: {e}，使用基础模式")
        await _run_basic_mode(target, config)


async def _run_basic_mode(target: Optional[str] = None, config: dict = None):
    """基础REPL模式（回退用）"""
    from src.cli.chat_cli import ClawAIChatCLI

    cli = ClawAIChatCLI(config)
    if target:
        cli.set_target(target)

    console.print("[dim]基础对话模式 - 输入 'exit' 退出，'help' 查看帮助[/]")
    console.print()

    while True:
        try:
            user_input = console.input("[bold cyan]❯[/] [bold]ClawAI[/] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("[green]👋 再见！[/]")
                break

            if user_input.lower() in ["help", "帮助", "?"]:
                console.print(cli._get_help_text())
                continue

            # 处理输入
            response = await cli.chat(user_input)
            console.print(f"\n[bold green]🤖 ClawAI:[/] {response}\n")

        except KeyboardInterrupt:
            console.print("\n[red]已取消[/]")
            break
        except Exception as e:
            console.print(f"\n[red]错误: {e}[/]\n")
            logger.error(f"处理失败: {e}")


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

    base_url = "http://localhost:5000"

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

    base_url = "http://localhost:5000"

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
        except:
            console.print("[bold yellow]⚠️ 前端服务: 未运行[/]")

    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ 后端服务: 未启动[/]")
        console.print("[bold yellow]⚠️ 前端服务: 未运行[/]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/]")


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
    else:
        # 默认进入对话模式
        asyncio.run(run_chat_mode(target=target))


def cli():
    """CLI入口点（供setup.py使用）"""
    main()


if __name__ == "__main__":
    main()
