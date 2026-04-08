#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 命令行工具
提供现代化、交互式的命令行界面，支持渗透测试、工具管理和系统监控
"""

import os
import sys
import time
import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.syntax import Syntax

# 初始化控制台
console = Console()


class ClawAICLI:
    """ClawAI命令行工具"""
    
    def __init__(self):
        """初始化ClawAI命令行工具"""
        try:
            from src.shared.backend.core.tool_manager import ToolManager
            from src.shared.backend.ai_core.ai_pentest_engine import AIPentestEngine
            self.tool_manager = ToolManager()
            self.ai_engine = AIPentestEngine()
        except ImportError:
            console.print("[yellow]警告: 无法导入部分模块，将使用模拟数据[/yellow]")
            # 模拟对象
            class MockToolManager:
                def get_tools(self):
                    return [
                        type('Tool', (), {'name': 'nmap', 'status': 'available', 'category': '网络扫描'}),
                        type('Tool', (), {'name': 'sqlmap', 'status': 'available', 'category': 'Web扫描'}),
                        type('Tool', (), {'name': 'metasploit', 'status': 'available', 'category': '漏洞利用'})
                    ]
            
            class MockAIEngine:
                async def run_pentest(self, target, instruction=""):
                    return {
                        "success": True,
                        "message": "测试完成",
                        "vulnerabilities": [
                            {"name": "SQL注入漏洞", "severity": "high", "location": f"http://{target}/api?id=1"},
                            {"name": "XSS漏洞", "severity": "medium", "location": f"http://{target}/search?q=test"}
                        ],
                        "report": {
                            "summary": {
                                "start_time": "2026-04-07 12:00:00",
                                "end_time": "2026-04-07 12:05:00",
                                "status": "completed",
                                "vulnerability_count": 2,
                                "exploit_count": 1
                            },
                            "recommendations": [
                                "修复所有发现的漏洞",
                                "加强输入验证",
                                "更新所有软件和依赖项"
                            ]
                        }
                    }
            
            self.tool_manager = MockToolManager()
            self.ai_engine = MockAIEngine()
        self.current_session = None
    
    def show_banner(self):
        """显示ClawAI横幅"""
        banner = r"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗ ██╗     ███████╗ ██████╗  █████╗ ███╗   ██╗██╗  ██╗██████╗  ║
║   ██╔══██╗██║     ██╔════╝██╔════╝ ██╔══██╗████╗  ██║██║ ██╔╝██╔══██╗ ║
║   ██████╔╝██║     █████╗  ██║  ███╗███████║██╔██╗ ██║█████╔╝ ██████╔╝ ║
║   ██╔═══╝ ██║     ██╔══╝  ██║   ██║██╔══██║██║╚██╗██║██╔═██╗ ██╔══██╗ ║
║   ██║     ███████╗███████╗╚██████╔╝██║  ██║██║ ╚████║██║  ██╗██████╔╝ ║
║   ╚═╝     ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═════╝  ║
║                                                                      ║
║                  AI驱动的渗透测试平台                                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
        """
        console.print(Text(banner, style="bold cyan"))
        console.print(Text("版本: 2.0.0", style="green"))
        console.print()
    
    def show_menu(self):
        """显示主菜单"""
        table = Table(title="ClawAI 主菜单", style="cyan")
        table.add_column("选项", style="bold yellow")
        table.add_column("描述", style="white")
        table.add_column("快捷键", style="green")
        
        table.add_row("1", "开始渗透测试", "p")
        table.add_row("2", "开始AI渗透测试", "a")
        table.add_row("3", "管理工具", "t")
        table.add_row("4", "查看系统状态", "s")
        table.add_row("5", "查看扫描历史", "h")
        table.add_row("6", "退出", "q")
        
        console.print(table)
        console.print()
    
    async def start_penetration_test(self):
        """开始渗透测试"""
        console.print(Panel("[bold cyan]渗透测试[/bold cyan]", expand=False))
        target = Prompt.ask("请输入目标 (IP或域名)")
        
        if not target:
            console.print("[red]目标不能为空[/red]")
            return
        
        # 显示进度
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[bold green]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("开始渗透测试...", total=100)
            
            # 模拟进度
            for i in range(100):
                progress.update(task, advance=1, description=f"正在扫描 {target}...")
                await asyncio.sleep(0.05)
        
        console.print(f"[green]已开始对 {target} 的渗透测试[/green]")
        console.print()
    
    async def start_ai_penetration_test(self):
        """开始AI渗透测试"""
        console.print(Panel("[bold green]AI渗透测试[/bold green]", expand=False))
        target = Prompt.ask("请输入目标 (IP或域名)")
        
        if not target:
            console.print("[red]目标不能为空[/red]")
            return
        
        instruction = Prompt.ask("请输入自定义指令 (可选)", default="")
        
        # 显示进度
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[bold green]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("开始AI渗透测试...", total=100)
            
            # 运行AI渗透测试
            result = await self.ai_engine.run_pentest(target, instruction=instruction)
            
            for i in range(100):
                progress.update(task, advance=1, description=f"正在使用AI分析 {target}...")
                await asyncio.sleep(0.05)
        
        if result.get('status') == 'completed':
            console.print(f"[green]AI渗透测试已完成: {target}[/green]")
            if result.get('vulnerabilities'):
                console.print("[bold yellow]发现的漏洞:[/bold yellow]")
                for vuln in result['vulnerabilities']:
                    console.print(f"  🚩 {vuln['name']} ({vuln['severity']})")
                    console.print(f"    位置: {vuln['location']}")
            if result.get('report'):
                console.print("[bold blue]测试报告:[/bold blue]")
                report = result['report']
                console.print(f"  开始时间: {report['summary']['start_time']}")
                console.print(f"  结束时间: {report['summary']['end_time']}")
                console.print(f"  漏洞数量: {report['summary']['vulnerability_count']}")
                console.print(f"  利用尝试: {report['summary']['exploit_count']}")
                
                if report.get('recommendations'):
                    console.print("[bold cyan]安全建议:[/bold cyan]")
                    for rec in report['recommendations']:
                        console.print(f"  💡 {rec}")
        else:
            console.print(f"[red]AI渗透测试失败: {result.get('error', '未知错误')}[/red]")
        
        console.print()
    
    def manage_tools(self):
        """管理工具"""
        console.print(Panel("[bold purple]工具管理[/bold purple]", expand=False))
        
        # 获取工具列表
        tools = self.tool_manager.get_tools()
        
        table = Table(title="可用工具", style="purple")
        table.add_column("名称", style="bold cyan")
        table.add_column("状态", style="bold green")
        table.add_column("类别", style="bold yellow")
        
        for tool in tools:
            status = "✅ 可用" if tool.status == "available" else "❌ 不可用"
            table.add_row(tool.name, status, tool.category)
        
        console.print(table)
        console.print()
    
    def view_system_status(self):
        """查看系统状态"""
        console.print(Panel("[bold blue]系统状态[/bold blue]", expand=False))
        
        # 模拟系统状态
        status = {
            "API服务器": "✅ 运行中",
            "前端": "✅ 运行中",
            "工具": f"✅ {len(self.tool_manager.get_tools())} 个可用",
            "AI引擎": "✅ 就绪",
            "知识库": "✅ 已更新"
        }
        
        for key, value in status.items():
            console.print(f"[cyan]{key}:[/cyan] [white]{value}[/white]")
        
        console.print()
    
    def view_scan_history(self):
        """查看扫描历史"""
        console.print(Panel("[bold orange]扫描历史[/bold orange]", expand=False))
        
        # 获取会话列表
        sessions = self.pentestgpt.list_sessions()
        
        if not sessions:
            console.print("[gray]未找到扫描历史[/gray]")
        else:
            table = Table(title="扫描会话", style="orange")
            table.add_column("会话ID", style="bold cyan")
            table.add_column("目标", style="bold white")
            table.add_column("状态", style="bold green")
            table.add_column("开始时间", style="bold yellow")
            
            for session in sessions:
                table.add_row(
                    session.session_id,
                    session.target,
                    session.status,
                    session.start_time
                )
            
            console.print(table)
        
        console.print()
    
    async def run(self):
        """运行命令行界面"""
        self.show_banner()
        
        while True:
            self.show_menu()
            choice = Prompt.ask("请输入您的选择", choices=["1", "2", "3", "4", "5", "6", "p", "a", "t", "s", "h", "q"], default="1")
            
            if choice in ["1", "p"]:
                await self.start_penetration_test()
            elif choice in ["2", "a"]:
                await self.start_ai_penetration_test()
            elif choice in ["3", "t"]:
                self.manage_tools()
            elif choice in ["4", "s"]:
                self.view_system_status()
            elif choice in ["5", "h"]:
                self.view_scan_history()
            elif choice in ["6", "q"]:
                console.print("[green]退出ClawAI...[/green]")
                break
            else:
                console.print("[red]无效选择，请重试[/red]")
                console.print()


@click.command()
def cli():
    """ClawAI命令行界面"""
    clawai_cli = ClawAICLI()
    asyncio.run(clawai_cli.run())


if __name__ == "__main__":
    cli()
