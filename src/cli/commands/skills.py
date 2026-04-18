#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skills command — list / info / reload user-defined skills."""

COMMAND_META = {
    "name": "skills",
    "aliases": ["技能", "skill"],
    "category": "local",
    "description_zh": "技能管理：列出技能、查看详情、热重载用户自定义技能",
    "description_en": "Skill management: list skills, show info, reload custom skills",
    "argument_hint": "[list|info <id>|reload]",
}


class SkillsCommand:
    """Manage ClawAI skills without touching the backend."""

    def execute(self, args: list, ctx: dict) -> str:
        from rich.console import Console
        console: Console = ctx.get("console", Console())

        action = args[0].lower() if args else "list"

        try:
            from src.shared.backend.skills import get_skill_registry
            registry = get_skill_registry()
        except Exception as e:
            console.print(f"[red]无法加载 Skills 模块: {e}[/]")
            return ""

        if action == "list":
            self._list(console, registry, args[1:])
        elif action == "info":
            skill_id = args[1] if len(args) > 1 else ""
            self._info(console, registry, skill_id)
        elif action == "reload":
            self._reload(console, registry)
        else:
            console.print(f"[red]未知操作: {action}[/]")
            console.print("用法: /skills [list|info <id>|reload]")

        return ""

    # ── sub-handlers ──────────────────────────────────────────────────────────

    @staticmethod
    def _list(console, registry, extra_args: list):
        """列出所有技能，支持可选过滤词。"""
        from rich.table import Table

        # 可选关键词过滤
        keyword = extra_args[0].lower() if extra_args else ""

        skills = list(registry.skills.values())
        if keyword:
            skills = [
                s for s in skills
                if keyword in s.id.lower()
                or keyword in s.name.lower()
                or keyword in s.description.lower()
                or any(keyword in t.lower() for t in s.tags)
            ]

        if not skills:
            msg = f"未找到匹配 '{keyword}' 的技能" if keyword else "暂无技能"
            console.print(f"[yellow]{msg}[/]")
            return

        # 区分内置 vs 用户自定义
        builtin_ids = getattr(registry, '_builtin_skill_ids', set())

        table = Table(
            title=f"技能列表{'（过滤: ' + keyword + '）' if keyword else ''}",
            border_style="cyan",
            show_lines=False,
        )
        table.add_column("来源", width=4, justify="center")
        table.add_column("ID", style="bold cyan", no_wrap=True)
        table.add_column("名称", style="white")
        table.add_column("类型", style="dim", width=8)
        table.add_column("严重性", width=6)
        table.add_column("描述", style="dim")

        severity_color = {
            "critical": "red",
            "high": "bright_red",
            "medium": "yellow",
            "low": "green",
            "info": "cyan",
        }

        for s in sorted(skills, key=lambda x: (x.id not in builtin_ids, x.id)):
            source = "📦" if s.id in builtin_ids else "✏️ "
            sev = s.severity.lower()
            sev_str = f"[{severity_color.get(sev, 'white')}]{sev}[/]"
            table.add_row(
                source,
                s.id,
                s.name,
                s.type.name.lower(),
                sev_str,
                s.description[:50] + ("…" if len(s.description) > 50 else ""),
            )

        console.print(table)
        builtin_count = sum(1 for s in skills if s.id in builtin_ids)
        user_count = len(skills) - builtin_count
        console.print(
            f"[dim]共 {len(skills)} 个技能 "
            f"（📦 内置 {builtin_count} | ✏️  自定义 {user_count}）[/]"
        )

    @staticmethod
    def _info(console, registry, skill_id: str):
        """显示单个技能的详细信息。"""
        if not skill_id:
            console.print("[red]用法: /skills info <skill_id>[/]")
            return

        skill = registry.get(skill_id)
        if skill is None:
            # 尝试模糊搜索
            suggestions = registry.search(skill_id, top_k=3)
            console.print(f"[red]技能不存在: {skill_id}[/]")
            if suggestions:
                names = ", ".join(s.id for s in suggestions)
                console.print(f"[yellow]你是否想找: {names}[/]")
            return

        from rich.panel import Panel
        from rich.table import Table
        from rich import box

        builtin_ids = getattr(registry, '_builtin_skill_ids', set())
        source = "📦 内置技能" if skill.id in builtin_ids else "✏️  用户自定义"

        # 基本信息
        lines = [
            f"[bold cyan]ID[/]       : {skill.id}",
            f"[bold cyan]名称[/]     : {skill.name}",
            f"[bold cyan]来源[/]     : {source}",
            f"[bold cyan]类型[/]     : {skill.type.name}",
            f"[bold cyan]分类[/]     : {skill.category.name}",
            f"[bold cyan]严重性[/]   : {skill.severity}",
            f"[bold cyan]目标类型[/] : {skill.target_type}",
            f"[bold cyan]执行器[/]   : {skill.executor}",
            f"[bold cyan]作者[/]     : {skill.author}",
            f"[bold cyan]标签[/]     : {', '.join(skill.tags) if skill.tags else '—'}",
        ]
        if skill.cve_id:
            lines.append(f"[bold cyan]CVE[/]      : {skill.cve_id}")
        lines.append(f"\n[bold cyan]描述[/]: {skill.description}")

        console.print(Panel("\n".join(lines), title=f"技能详情: {skill.id}", border_style="cyan"))

        # 参数表
        if skill.parameters:
            ptable = Table(title="参数", border_style="dim", box=box.SIMPLE)
            ptable.add_column("参数名", style="cyan")
            ptable.add_column("类型", style="dim")
            ptable.add_column("必填", justify="center")
            ptable.add_column("默认值", style="dim")
            ptable.add_column("描述")
            for p in skill.parameters:
                required = "✓" if p.required else "—"
                default = str(p.default) if p.default is not None else "—"
                ptable.add_row(p.name, p.type, required, default, p.description)
            console.print(ptable)

        # 代码预览（仅用户自定义技能）
        if skill.id not in builtin_ids and skill.code:
            preview = skill.code[:300]
            if len(skill.code) > 300:
                preview += f"\n… [dim]（共 {len(skill.code)} 字符）[/]"
            console.print(Panel(preview, title="代码预览", border_style="dim"))

    @staticmethod
    def _reload(console, registry):
        """热重载用户自定义技能。"""
        from pathlib import Path

        user_dir = Path.home() / ".clawai" / "skills"
        project_dir = Path.cwd() / ".clawai" / "skills"

        before = len(registry.skills)
        try:
            registry.reload_user_skills()
        except Exception as e:
            console.print(f"[red]重载失败: {e}[/]")
            return

        after = len(registry.skills)
        builtin_count = len(getattr(registry, '_builtin_skill_ids', set()))
        user_count = after - builtin_count
        delta = after - before

        console.print("[green]✓ 用户技能已重载[/]")
        console.print(f"  📂 project: [cyan]{project_dir}[/]")
        console.print(f"  📂 user   : [cyan]{user_dir}[/]")
        console.print(
            f"  [dim]自定义技能: {user_count} 个"
            f"{' (↑' + str(delta) + ')' if delta > 0 else ' (↓' + str(-delta) + ')' if delta < 0 else ''}"
            "[/]"
        )
