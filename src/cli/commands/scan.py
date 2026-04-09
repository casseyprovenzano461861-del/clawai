#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan command — expand into an LLM interaction to scan a target."""

COMMAND_META = {
    "name": "scan",
    "aliases": ["扫描", "测试", "test", "探测"],
    "category": "prompt",
    "description_zh": "对目标执行安全扫描",
    "description_en": "Perform security scan on a target",
    "argument_hint": "<target>",
}


class ScanCommand:
    """Delegate scanning to the chat CLI with a scan prompt."""

    def execute(self, args: list, ctx: dict) -> str:
        import asyncio
        from rich.console import Console

        console: Console = ctx.get("console", Console())
        target = " ".join(args)

        if not target:
            console.print("[red]请指定扫描目标: scan <target>[/]")
            console.print("[dim]示例: scan 192.168.1.1[/]")
            return ""

        chat_cli = ctx.get("chat_cli")
        if not chat_cli:
            console.print("[red]Chat CLI 未初始化[/]")
            return ""

        # chat() is async — run it in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're already inside an async context; schedule the coroutine
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = pool.submit(asyncio.run, chat_cli.chat(f"扫描 {target}")).result()
        except RuntimeError:
            # No running loop — safe to use asyncio.run()
            response = asyncio.run(chat_cli.chat(f"扫描 {target}"))

        return response
