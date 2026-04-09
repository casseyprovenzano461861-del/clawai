#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tools command — list / status / check security tools via backend API."""

COMMAND_META = {
    "name": "tools",
    "aliases": ["工具"],
    "category": "local",
    "description_zh": "工具管理：查看可用工具列表、状态、检查",
    "description_en": "Tool management: list, check status, verify tools",
    "argument_hint": "[list|status|check]",
}


class ToolsCommand:
    """Query the backend for tool information."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console
        from src.cli.config import get_config

        console: Console = ctx.get("console", Console())
        action = args[0].lower() if args else "list"

        try:
            import requests
        except ImportError:
            console.print("[red]需要安装 requests 库[/]")
            return ""

        base_url = get_config().backend_url

        try:
            if action == "list":
                self._list(console, base_url, requests)
            elif action == "status":
                self._status(console, base_url, requests)
            elif action == "check":
                self._check(console, base_url, requests)
            else:
                console.print(f"[red]未知操作: {action}[/]")
                console.print("用法: tools [list|status|check]")
        except requests.exceptions.ConnectionError:
            console.print("[red]无法连接到后端服务。请确保服务已启动。[/]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/]")

        return ""

    # -- sub-handlers ----------------------------------------------------------

    @staticmethod
    def _list(console, base_url, requests):
        response = requests.get(f"{base_url}/api/v1/tools", timeout=5)
        if response.status_code == 200:
            tools = response.json()
            from rich.table import Table
            table = Table(title="可用工具", border_style="cyan")
            table.add_column("状态", width=3)
            table.add_column("名称", style="bold cyan")
            table.add_column("说明", style="white")
            for t in tools:
                status = "✅" if t.get('available') else "❌"
                table.add_row(status, t['name'], t.get('description', ''))
            console.print(table)
        else:
            console.print(f"[red]获取工具列表失败: {response.status_code}[/]")

    @staticmethod
    def _status(console, base_url, requests):
        response = requests.get(f"{base_url}/api/v1/tools/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            from rich.table import Table
            table = Table(title="工具状态", border_style="cyan")
            table.add_column("工具", style="bold cyan")
            table.add_column("安装状态")
            table.add_column("版本", style="dim")
            for name, info in status.items():
                installed = "✅ 已安装" if info.get('installed') else "❌ 未安装"
                version = info.get('version', '未知')
                table.add_row(name, installed, version)
            console.print(table)
        else:
            console.print(f"[red]获取工具状态失败: {response.status_code}[/]")

    @staticmethod
    def _check(console, base_url, requests):
        response = requests.get(f"{base_url}/api/v1/tools/check", timeout=5)
        if response.status_code == 200:
            console.print("[green]工具检查完成[/]")
        else:
            console.print(f"[red]工具检查失败: {response.status_code}[/]")
