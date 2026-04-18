#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session management command — list / save / load / export / delete sessions."""

COMMAND_META = {
    "name": "session",
    "aliases": ["sessions", "会话"],
    "category": "local",
    "description_zh": "会话管理：查看、保存、加载、导出、对比、删除会话",
    "description_en": "Session management: list, save, load, export, compare, delete sessions",
    "argument_hint": "[list|save|load|export|compare|delete]",
}


class SessionCommand:
    """Handle session sub-commands."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console
        from rich.table import Table

        console: Console = ctx.get("console", Console())
        action = args[0].lower() if args else "list"
        rest = args[1] if len(args) > 1 else ""

        if action in ("list", ""):
            return self._list(console)
        elif action == "save":
            return self._save(ctx, console)
        elif action == "load":
            return self._load(rest.strip(), ctx, console)
        elif action == "export":
            return self._export(rest.strip(), console)
        elif action == "compare":
            return self._compare(rest.strip(), console)
        elif action == "delete":
            return self._delete(rest.strip(), console)
        else:
            console.print(f"[red]未知操作: {action}[/]")
            console.print("用法: session [list|save|load|export|compare|delete]")
            return ""

    # -- sub-handlers ----------------------------------------------------------

    def _list(self, console) -> str:
        from rich.table import Table
        from src.cli.session_store import SessionStore

        sessions = SessionStore().list_sessions()
        if not sessions:
            console.print("[yellow]暂无保存的会话。[/]")
            console.print("[dim]提示: 执行扫描后会话会自动保存到 ~/.clawai/sessions/[/]")
            return ""

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
        console.print("[dim]session load <id>   加载会话[/]")
        console.print("[dim]session export <id> 导出报告[/]")
        console.print("[dim]session compare <id1> <id2> 对比两次扫描[/]")
        console.print("[dim]session delete <id> 删除会话[/]")
        return ""

    def _save(self, ctx, console) -> str:
        chat_cli = ctx.get("chat_cli")
        if chat_cli and chat_cli.save_session():
            console.print(f"[green]会话已保存: {chat_cli.session.session_id}[/]")
        else:
            console.print("[red]保存失败[/]")
        return ""

    def _load(self, session_id: str, ctx, console) -> str:
        if not session_id:
            console.print("[red]请指定会话 ID: session load <id>[/]")
            return ""
        chat_cli = ctx.get("chat_cli")
        if chat_cli and chat_cli.load_session(session_id):
            s = chat_cli.session
            console.print(f"[green]已切换到会话: {session_id}[/]")
            console.print(f"[dim]   目标: {s.target or '未设置'}  阶段: {s.phase}  发现: {len(s.findings)} 条[/]")
        else:
            console.print(f"[red]未找到会话: {session_id}[/]")
        return ""

    def _export(self, rest: str, console) -> str:
        from src.cli.session_store import SessionStore
        from src.cli.exporter import export_session

        # rest might be "<id>" or "<id> <format>" or just "<format>" (use current session)
        parts = rest.split()
        session_id = ""
        fmt = "markdown"

        if parts:
            # If the last part looks like a format, use it
            if parts[-1] in ("json", "html", "markdown"):
                fmt = parts[-1]
                session_id = " ".join(parts[:-1])
            else:
                session_id = rest

        if not session_id:
            console.print("[red]请指定会话 ID: session export <id> [format][/]")
            return ""

        data = SessionStore().load(session_id)
        if data is None:
            console.print(f"[red]未找到会话: {session_id}[/]")
            return ""

        try:
            path = export_session(data, fmt=fmt)
            console.print(f"[green]报告已导出:[/] {path}")
        except Exception as e:
            console.print(f"[red]导出失败: {e}[/]")
        return ""

    def _compare(self, rest: str, console) -> str:
        from src.cli.session_store import SessionStore
        from src.cli.exporter import compare_sessions

        parts = rest.split()
        if len(parts) < 2:
            console.print("[red]请指定两个会话 ID: session compare <id1> <id2>[/]")
            return ""

        id1, id2 = parts[0], parts[1]
        store = SessionStore()
        data1 = store.load(id1)
        data2 = store.load(id2)

        if data1 is None:
            console.print(f"[red]未找到会话: {id1}[/]")
            return ""
        if data2 is None:
            console.print(f"[red]未找到会话: {id2}[/]")
            return ""

        try:
            path = compare_sessions(data1, data2)
            console.print(f"[green]对比报告已生成:[/] {path}")
        except Exception as e:
            console.print(f"[red]对比失败: {e}[/]")
        return ""

    def _delete(self, session_id: str, console) -> str:
        from src.cli.session_store import SessionStore
        from rich.prompt import Confirm

        if not session_id:
            console.print("[red]请指定会话 ID: session delete <id>[/]")
            return ""

        store = SessionStore()

        if session_id.lower() == "all":
            confirm = Confirm.ask("[bold red]确认删除所有会话？此操作不可撤销[/]")
            if confirm:
                count = store.delete_all()
                console.print(f"[green]已删除 {count} 个会话。[/]")
            else:
                console.print("[yellow]已取消。[/]")
            return ""

        data = store.load(session_id)
        if data is None:
            console.print(f"[red]未找到会话: {session_id}[/]")
            return ""

        target = data.get("target") or "未知"
        confirm = Confirm.ask(f"确认删除会话 [cyan]{session_id}[/] (目标: {target})")
        if confirm:
            if store.delete(session_id):
                console.print(f"[green]已删除会话: {session_id}[/]")
            else:
                console.print(f"[red]删除失败: {session_id}[/]")
        else:
            console.print("[yellow]已取消。[/]")
        return ""
