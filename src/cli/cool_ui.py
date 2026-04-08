#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 主入口
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

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, '.env'))
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

console = Console() if RICH_AVAILABLE else None
logger = logging.getLogger(__name__)


def print_banner():
    """打印简洁 Banner"""
    if RICH_AVAILABLE:
        console.clear()
        
        banner = """
    ██████╗██╗     ███████╗ █████╗  ██████╗ ██╗  ██╗
   ██╔════╝██║     ██╔════╝██╔══██╗██╔═══██╗╚██╗██╔╝
   ██║     ██║     █████╗  ███████║██║   ██║ ╚███╔╝ 
   ██║     ██║     ██╔══╝  ██╔══██║██║   ██║ ██╔██╗ 
   ╚██████╗███████╗███████╗██║  ██║╚██████╔╝██╔╝ ██╗
    ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
                AI 渗透测试助手
        """
        console.print(banner, style="bold cyan")
        console.print("─" * 52, style="dim")
        console.print("  Skills: 27  |  Tools: 63  |  P-E-R Mode", style="green")
        console.print()
    else:
        print("\n  ClawAI v2.0 - AI 渗透测试助手\n")


def print_message(role: str, content: str):
    """打印消息"""
    if RICH_AVAILABLE:
        icons = {"user": "👤", "assistant": "🤖", "system": "ℹ️"}
        colors = {"user": "yellow", "assistant": "cyan", "system": "dim"}
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        console.print()
        console.print(f"{icons.get(role, '💬')} {role.title()} [{timestamp}]", style=colors.get(role, "white"))
        console.print(Panel(content, border_style=colors.get(role, "white"), expand=False))
    else:
        print(f"\n[{role}] {content}\n")


async def run_chat_mode(target: Optional[str] = None):
    """运行 AI 对话模式"""
    print_banner()
    
    if RICH_AVAILABLE:
        console.print("  💡 输入目标地址开始测试，或输入 'help' 查看帮助\n", style="dim")
    
    try:
        from src.cli.chat_cli import ClawAIChatCLI
        cli = ClawAIChatCLI()
        
        if target:
            cli.set_target(target)
            if RICH_AVAILABLE:
                console.print(f"  🎯 目标已设置: {target}\n", style="green")
        
        while True:
            try:
                if RICH_AVAILABLE:
                    user_input = console.input("[bold cyan]❯[/] ").strip()
                else:
                    user_input = input("❯ ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit", "bye", "退出"]:
                    if RICH_AVAILABLE:
                        console.print("\n  👋 再见！\n", style="green")
                    else:
                        print("\n  再见！\n")
                    break
                
                # 显示用户消息
                print_message("user", user_input)
                
                # 处理并显示响应
                response = await cli.chat(user_input)
                print_message("assistant", response)
                
            except KeyboardInterrupt:
                if RICH_AVAILABLE:
                    console.print("\n  👋 再见！\n", style="green")
                break
            except Exception as e:
                logger.error(f"处理失败: {e}")
                print_message("system", f"错误: {e}")
    
    except ImportError as e:
        logger.error(f"无法加载 AI 模块: {e}")
        if RICH_AVAILABLE:
            console.print(f"\n  ❌ 无法加载 AI 模块: {e}\n", style="red")
            console.print("  请确保已安装所需依赖: pip install -r requirements.txt\n", style="yellow")
        else:
            print(f"\n  无法加载 AI 模块: {e}\n")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="ClawAI - AI 渗透测试助手")
    parser.add_argument("command", nargs="?", default="chat", help="命令: chat, scan, status")
    parser.add_argument("args", nargs="*", help="命令参数")
    parser.add_argument("-t", "--target", help="目标地址")
    return parser.parse_args()


def main():
    """主入口"""
    args = parse_arguments()
    
    # 设置日志
    logging.basicConfig(level=logging.WARNING)
    
    if args.command == "chat" or args.command is None:
        asyncio.run(run_chat_mode(target=args.target))
    elif args.command == "scan" and args.args:
        target = args.args[0]
        asyncio.run(run_chat_mode(target=target))
    else:
        asyncio.run(run_chat_mode())


if __name__ == "__main__":
    main()
