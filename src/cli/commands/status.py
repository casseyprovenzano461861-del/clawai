#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Status command — check backend and frontend health."""

COMMAND_META = {
    "name": "status",
    "aliases": ["状态", "进度"],
    "category": "local",
    "description_zh": "查看系统状态：后端服务、前端服务运行情况",
    "description_en": "Check system status: backend and frontend service health",
}


class StatusCommand:
    """Check backend and frontend service health."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console
        from rich.table import Table
        from src.cli.config import get_config

        console: Console = ctx.get("console", Console())

        try:
            import requests
        except ImportError:
            console.print("[red]需要安装 requests 库[/]")
            return ""

        base_url = get_config().backend_url

        table = Table(title="系统状态", border_style="cyan", show_header=True)
        table.add_column("服务", style="bold")
        table.add_column("状态")
        table.add_column("详情", style="dim")

        # Check backend
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                table.add_row(
                    "后端服务",
                    "[green]✅ 运行正常[/]",
                    f"状态: {health.get('status', 'ok')}  版本: {health.get('version', '未知')}",
                )
            else:
                table.add_row("后端服务", "[red]❌ 异常[/]", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            table.add_row("后端服务", "[red]❌ 未启动[/]", f"地址: {base_url}")
        except Exception as e:
            table.add_row("后端服务", "[red]❌ 错误[/]", str(e))

        # Check frontend
        try:
            requests.get("http://localhost:5173", timeout=5)
            table.add_row("前端服务", "[green]✅ 运行正常[/]", "http://localhost:5173")
        except Exception:
            table.add_row("前端服务", "[yellow]⚠️ 未运行[/]", "http://localhost:5173")

        console.print(table)
        return ""
