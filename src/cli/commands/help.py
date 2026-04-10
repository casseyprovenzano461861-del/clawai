#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Help command — show available commands or help for a specific command."""

COMMAND_META = {
    "name": "help",
    "aliases": ["帮助", "?"],
    "category": "local",
    "description_zh": "显示帮助信息",
    "description_en": "Show help information",
}


class HelpCommand:
    """Display help for all commands or a specific command."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console
        from rich.table import Table
        from src.cli.commands import get_registry

        console: Console = ctx.get("console", Console())
        registry = get_registry()

        specific = args[0] if args else ""
        if specific:
            return self._show_one(specific, registry, console)
        else:
            return self._show_all(registry, console)

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _show_all(registry, console) -> str:
        from rich.table import Table
        commands = registry.all_commands()
        if not commands:
            console.print("[yellow]暂无可用命令[/]")
            return ""

        table = Table(title="可用命令", border_style="cyan", show_lines=False)
        table.add_column("命令", style="bold cyan", width=14)
        table.add_column("别名", style="dim", width=18)
        table.add_column("类别", width=8)
        table.add_column("参数", style="dim", width=22)
        table.add_column("说明", style="white")

        for cmd in sorted(commands, key=lambda c: (c.category, c.name)):
            aliases = ", ".join(cmd.aliases) if cmd.aliases else "-"
            table.add_row(
                f"/{cmd.name}",
                aliases,
                cmd.category,
                cmd.argument_hint or "-",
                cmd.description_zh,
            )

        console.print(table)
        return ""

    @staticmethod
    def _show_one(name: str, registry, console) -> str:
        # Strip leading slash if present
        name = name.lstrip("/")
        meta = registry.lookup(name)
        if meta is None:
            console.print(f"[red]未找到命令: {name}[/]")
            suggestions = registry.fuzzy_match(name)
            if suggestions:
                console.print(f"[dim]你是不是想用: {', '.join(suggestions)}?[/]")
            return ""

        console.print(f"\n[bold cyan]/{meta.name}[/]")
        if meta.aliases:
            console.print(f"[dim]别名: {', '.join(meta.aliases)}[/]")
        console.print(f"[dim]类别: {meta.category}[/]")
        if meta.argument_hint:
            console.print(f"[dim]参数: {meta.argument_hint}[/]")
        console.print(f"[dim]说明(中文): {meta.description_zh}[/]")
        console.print(f"[dim]Description: {meta.description_en}[/]")
        console.print()
        return ""
