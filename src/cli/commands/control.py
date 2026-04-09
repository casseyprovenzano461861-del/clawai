#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Control command — pause / resume / stop an active scan."""

COMMAND_META = {
    "name": "control",
    "aliases": [],
    "category": "local",
    "description_zh": "扫描控制：暂停、恢复、停止当前扫描",
    "description_en": "Scan control: pause, resume, or stop the active scan",
    "argument_hint": "[pause|resume|stop]",
}


class ControlCommand:
    """Control scan execution: pause, resume, stop."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console

        console: Console = ctx.get("console", Console())
        action = args[0].lower() if args else ""

        if action in ("pause", "暂停"):
            self._pause(ctx, console)
        elif action in ("resume", "继续", "恢复"):
            self._resume(ctx, console)
        elif action in ("stop", "停止", "中止"):
            self._stop(ctx, console)
        else:
            console.print("[red]未知操作[/]")
            console.print("用法: control [pause|resume|stop]")
            console.print("[dim]也可以直接使用 pause / resume / stop 命令[/]")

        return ""

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _pause(ctx, console):
        chat_cli = ctx.get("chat_cli")
        if chat_cli:
            chat_cli.record_intervention("command", "pause")
            scan_state = getattr(chat_cli, '_scan_state', None)
            if scan_state:
                scan_state.pause()
                console.print("[yellow]已暂停扫描，输入 resume 继续[/]")
            else:
                console.print("[dim]当前无活跃扫描[/]")

    @staticmethod
    def _resume(ctx, console):
        chat_cli = ctx.get("chat_cli")
        if chat_cli:
            chat_cli.record_intervention("command", "resume")
            scan_state = getattr(chat_cli, '_scan_state', None)
            if scan_state:
                scan_state.resume()
                console.print("[green]已恢复扫描[/]")
            else:
                console.print("[dim]当前无活跃扫描[/]")

    @staticmethod
    def _stop(ctx, console):
        chat_cli = ctx.get("chat_cli")
        if chat_cli:
            chat_cli.record_intervention("command", "stop")
            console.print("[red]⏹ 已发送停止指令[/]")


# ---------------------------------------------------------------------------
# Sub-command aliases — each registers independently in the command registry
# so that "pause", "resume", "stop" work as top-level commands.
# ---------------------------------------------------------------------------

PAUSE_META = {
    "name": "pause",
    "aliases": ["暂停"],
    "category": "local",
    "description_zh": "暂停当前扫描",
    "description_en": "Pause the active scan",
    "module_path": "src.cli.commands.control",
}

RESUME_META = {
    "name": "resume",
    "aliases": ["继续", "恢复"],
    "category": "local",
    "description_zh": "恢复已暂停的扫描",
    "description_en": "Resume a paused scan",
    "module_path": "src.cli.commands.control",
}

STOP_META = {
    "name": "stop",
    "aliases": ["停止", "中止"],
    "category": "local",
    "description_zh": "停止当前扫描",
    "description_en": "Stop the active scan",
    "module_path": "src.cli.commands.control",
}
