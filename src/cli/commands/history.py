#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 历史记录命令
支持搜索、过滤、导出 REPL 历史命令
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """历史记录条目"""
    timestamp: str
    command: str
    index: int


class HistoryManager:
    """历史记录管理器"""

    def __init__(self, history_path: Optional[Path] = None):
        if history_path is None:
            history_path = Path.home() / ".clawai" / "history"
        self.history_path = history_path
        self.entries: list[HistoryEntry] = []
        self._load()

    def _load(self):
        """加载历史记录"""
        try:
            if self.history_path.exists():
                lines = self.history_path.read_text(encoding="utf-8").splitlines()
                for idx, line in enumerate(lines, 1):
                    if line.strip():
                        self.entries.append(HistoryEntry(
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                            command=line.strip(),
                            index=idx
                        ))
        except Exception as e:
            logger.debug(f"加载历史记录失败: {e}")

    def search(self, keyword: str, limit: int = 20) -> list[HistoryEntry]:
        """搜索历史命令"""
        keyword_lower = keyword.lower()
        results = [
            e for e in self.entries
            if keyword_lower in e.command.lower()
        ]
        return results[:limit]

    def filter_by_prefix(self, prefix: str, limit: int = 10) -> list[HistoryEntry]:
        """按前缀过滤"""
        prefix_lower = prefix.lower()
        results = [
            e for e in self.entries
            if e.command.lower().startswith(prefix_lower)
        ]
        return results[:limit]

    def export(self, output_path: Path, format: str = "txt"):
        """导出历史记录"""
        try:
            if format == "txt":
                content = "\n".join(e.command for e in self.entries)
            elif format == "csv":
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Index", "Timestamp", "Command"])
                for e in self.entries:
                    writer.writerow([e.index, e.timestamp, e.command])
                content = output.getvalue()
            elif format == "json":
                import json
                content = json.dumps([e.__dict__ for e in self.entries], ensure_ascii=False, indent=2)
            else:
                return f"不支持格式: {format}"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            return f"已导出到: {output_path}"
        except Exception as e:
            return f"导出失败: {e}"

    def list_all(self, limit: int = 50) -> list[HistoryEntry]:
        """列出最近的历史"""
        return self.entries[-limit:]


class HistoryCommand:
    """历史记录命令"""

    def __init__(self):
        self.manager = HistoryManager()

    def execute(self, args: list, ctx: dict) -> str:
        """执行历史命令

        用法:
            /history                # 列出最近 50 条
            /history search <关键词>  # 搜索历史
            /history prefix <前缀>    # 按前缀过滤
            /history export <路径>    # 导出历史
        """
        console = ctx.get("console") or Console()

        if not args:
            return self._list(console, limit=50)

        action = args[0].lower()
        if action == "search" and len(args) > 1:
            keyword = " ".join(args[1:])
            return self._search(console, keyword)
        elif action == "prefix" and len(args) > 1:
            prefix = " ".join(args[1:])
            return self._filter_prefix(console, prefix)
        elif action == "export" and len(args) > 1:
            output_path = Path(args[1])
            return self._export(console, output_path)
        else:
            return self._list(console, limit=50)

    def _list(self, console: Console, limit: int = 50) -> str:
        """列出历史"""
        entries = self.manager.list_all(limit)
        if not entries:
            return "暂无历史记录"

        table = Table(title=f"最近 {len(entries)} 条命令", border_style="rgb(80,110,80)", show_header=True)
        table.add_column("索引", style="rgb(0,255,65)", width=6)
        table.add_column("时间", style="rgb(80,110,80)", width=16)
        table.add_column("命令", style="rgb(200,230,200)")

        for e in entries:
            # 截断过长的命令
            cmd = e.command[:80] + "..." if len(e.command) > 80 else e.command
            table.add_row(str(e.index), e.timestamp, cmd)

        console.print(table)
        console.print(Text(f"\n总计 {len(self.manager.entries)} 条历史记录", style="rgb(80,110,80)"))
        console.print(Text("提示: 输入 Ctrl+R 搜索历史，或 /history search <关键词>", style="rgb(255,191,0)"))
        return ""

    def _search(self, console: Console, keyword: str) -> str:
        """搜索历史"""
        results = self.manager.search(keyword, limit=20)
        if not results:
            return f"未找到包含 '{keyword}' 的历史"

        console.print(Text(f"找到 {len(results)} 条匹配结果:", style="rgb(0,255,65)"))
        for e in results:
            cmd = e.command[:80] + "..." if len(e.command) > 80 else e.command
            console.print(Text(f"  [{e.index}] ", style="rgb(80,110,80)"), Text(cmd, style=""))

        return ""

    def _filter_prefix(self, console: Console, prefix: str) -> str:
        """按前缀过滤"""
        results = self.manager.filter_by_prefix(prefix, limit=10)
        if not results:
            return f"未找到以 '{prefix}' 开头的命令"

        console.print(Text(f"找到 {len(results)} 条匹配结果:", style="rgb(0,255,65)"))
        for e in results:
            console.print(Text(f"  {e.command}", style=""))

        return ""

    def _export(self, console: Console, output_path: Path) -> str:
        """导出历史"""
        format = "txt"
        if output_path.suffix == ".csv":
            format = "csv"
        elif output_path.suffix == ".json":
            format = "json"

        result = self.manager.export(output_path, format)
        console.print(Text(result, style="rgb(0,255,65)" if "成功" in result else "rgb(255,60,60)"))
        return ""
