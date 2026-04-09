#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exit command — save session and signal the REPL to quit."""

COMMAND_META = {
    "name": "exit",
    "aliases": ["quit", "bye", "退出", "再见"],
    "category": "local",
    "description_zh": "保存会话并退出",
    "description_en": "Save session and exit",
}


class ExitCommand:
    """Save the current session and return the special exit signal."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console

        console: Console = ctx.get("console", Console())
        chat_cli = ctx.get("chat_cli")

        if chat_cli:
            chat_cli.save_session()
            console.print(f"[dim]会话已保存: {chat_cli.session.session_id}[/]")

        console.print("[green]再见！[/]")
        return "__EXIT__"
