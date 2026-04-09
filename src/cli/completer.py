# -*- coding: utf-8 -*-
"""
ClawAI CLI 命令补全系统

基于 prompt_toolkit 实现的智能命令补全，支持：
- /斜杠命令（从 CommandRegistry 动态获取）
- !bash 模式提示
- 意图触发关键词（扫描/scan/报告/report 等）
- session load <id> 动态补全已保存的 session_id
- 中英文混合补全
- 持久化历史（~/.clawai/history）

快速使用
--------
    from src.cli.completer import get_prompt_session

    session = get_prompt_session(registry=registry)
    text = await session.prompt_async("❯ ")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.styles import Style

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 意图触发关键词（自然语言开头词，不是完整命令）
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: list[tuple[str, str]] = [
    ("扫描 ",       "标准扫描（5轮）"),
    ("快速扫描 ",   "快速扫描（3轮: nmap + whatweb）"),
    ("深度扫描 ",   "深度扫描（10轮: 全工具）"),
    ("scan ",       "Standard scan"),
    ("test ",       "Test target"),
    ("测试 ",       "测试目标"),
    ("探测 ",       "探测目标"),
    ("检查 ",       "检查目标"),
    ("分析",        "AI 分析当前发现"),
    ("analyze",     "AI analyze findings"),
    ("评估",        "评估安全风险"),
    ("利用",        "列出可利用的漏洞"),
    ("exploit",     "List exploitable vulns"),
    ("报告",        "生成渗透测试报告"),
    ("report",      "Generate report"),
    ("导出",        "导出报告"),
    ("总结",        "总结发现"),
    ("状态",        "查看当前状态"),
    ("status",      "Check current status"),
    ("配置",        "查看当前配置"),
    ("config",      "Show current config"),
]


# ---------------------------------------------------------------------------
# 核心补全器（注册表驱动）
# ---------------------------------------------------------------------------

class ClawAICompleter(Completer):
    """ClawAI 智能命令补全器（注册表驱动）

    补全策略：
    1. / 前缀 → 从 CommandRegistry 获取斜杠命令补全
    2. ! 前缀 → bash 模式提示
    3. 'session load ' 结尾 → 动态补全已保存的 session_id
    4. 其他前缀 → 从意图关键词表中前缀匹配
    """

    def __init__(self, registry=None):
        self.registry = registry

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor

        # ── /斜杠命令补全 ──
        if text.startswith("/"):
            yield from self._complete_slash(text)
            return

        # ── !bash 模式提示 ──
        if text == "!":
            yield Completion(
                "! ", start_position=-1,
                display="!command",
                display_meta="执行 bash 命令",
            )
            return

        # ── 动态补全 session_id ──
        if text.lower().startswith("session load "):
            prefix_after_cmd = text[len("session load "):]
            yield from self._complete_session_ids(prefix_after_cmd)
            return

        # ── 意图关键词前缀匹配 ──
        text_lower = text.lower()
        for candidate, meta in _INTENT_KEYWORDS:
            if candidate.lower().startswith(text_lower):
                yield Completion(
                    candidate,
                    start_position=-len(text),
                    display=candidate,
                    display_meta=meta,
                )

    def _complete_slash(self, text: str) -> Iterable[Completion]:
        """从注册表获取 /command 补全 + 工具名补全"""
        if not self.registry:
            return

        prefix = text[1:].lower()  # 去掉 / 前缀

        # /session 子命令补全
        if prefix.startswith("session "):
            sub_prefix = prefix[len("session "):]
            subs = [("list", "列出所有已保存会话"), ("save", "手动保存当前会话"),
                    ("load ", "加载指定会话"), ("export", "导出会话报告"),
                    ("delete ", "删除指定会话")]
            for sub, desc in subs:
                if sub.startswith(sub_prefix):
                    yield Completion(
                        f"/session {sub}", start_position=-len(text),
                        display=f"/session {sub}", display_meta=desc,
                    )
            return

        # 从注册表获取所有命令
        for meta in self.registry.all_commands():
            name = meta.name
            if name.startswith(prefix):
                display = f"/{name}"
                hint = meta.argument_hint
                if hint:
                    display += f" {hint}"
                yield Completion(
                    f"/{name} ",
                    start_position=-len(text),
                    display=display,
                    display_meta=meta.description_zh,
                )

        # 补全工具名 (直接工具执行)
        try:
            from src.cli.tools import get_tool_registry
            tool_registry = get_tool_registry()
            for tool in tool_registry.all_tools():
                if tool.name.startswith(prefix) and tool.name not in {
                    m.name for m in self.registry.all_commands()
                }:
                    display = f"/{tool.name}"
                    # 标记危险/只读
                    tag = "⚠危险" if tool.is_dangerous else ("只读" if tool.is_readonly else "")
                    meta_text = f"[工具] {tool.description[:40]}{'  ' + tag if tag else ''}"
                    yield Completion(
                        f"/{tool.name} ",
                        start_position=-len(text),
                        display=display,
                        display_meta=meta_text,
                    )
        except Exception:
            pass

    def _complete_session_ids(self, prefix: str) -> Iterable[Completion]:
        """列出已保存的 session_id 供补全"""
        try:
            from src.cli.session_store import SessionStore

            sessions = SessionStore().list_sessions()
            for s in sessions:
                sid = s.get("session_id", "")
                if sid.startswith(prefix):
                    target = s.get("target") or ""
                    meta = f"{target}  {s.get('updated_at', '')[:10]}" if target else s.get("updated_at", "")[:10]
                    yield Completion(
                        sid,
                        start_position=-len(prefix),
                        display=sid,
                        display_meta=meta,
                    )
        except Exception as e:
            logger.debug(f"session_id 补全失败: {e}")


# ---------------------------------------------------------------------------
# prompt_toolkit 样式
# ---------------------------------------------------------------------------

NEON_CYAN = "#00ff41"

CLAWAI_STYLE = Style.from_dict(
    {
        "prompt":          f"bold {NEON_CYAN}",
        "completion-menu.completion":         "bg:#0a0f0a fg:#b0d0b0",
        "completion-menu.completion.current": "bg:#0a1f0a fg:#00ff41 bold",
        "completion-menu.meta":               "bg:#0a0f0a fg:#507050",
        "completion-menu.meta.current":       "bg:#0a1f0a fg:#00ff41",
        "completion-menu.border":             "fg:#1a3a1a",
        "scrollbar.background":               "bg:#0a1f0a",
        "scrollbar.button":                   "bg:#00ff41",
    }
)


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def get_prompt_session(
    history_file: str | Path | None = None,
    registry=None,
):
    """创建带历史记录和补全的 PromptSession

    Args:
        history_file: 历史文件路径。None 则尝试 ~/.clawai/history。
        registry: CommandRegistry 实例。None 则自动获取。

    Returns:
        prompt_toolkit.PromptSession
    """
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

    # 懒加载注册表
    if registry is None:
        try:
            from src.cli.commands import get_registry
            registry = get_registry()
        except Exception:
            pass

    history = _make_history(history_file)

    return PromptSession(
        completer=ClawAICompleter(registry=registry),
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        style=CLAWAI_STYLE,
        complete_while_typing=True,
        enable_history_search=True,  # Ctrl-R 搜索历史
        mouse_support=False,
    )


def _make_history(history_file: str | Path | None):
    """创建历史对象（优先文件持久化，失败回退内存）"""
    if history_file is None:
        try:
            history_path = Path.home() / ".clawai" / "history"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            return FileHistory(str(history_path))
        except Exception as e:
            logger.debug(f"无法创建历史文件，使用内存历史: {e}")
            return InMemoryHistory()

    try:
        path = Path(history_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        return FileHistory(str(path))
    except Exception as e:
        logger.debug(f"历史文件 {history_file} 创建失败，使用内存历史: {e}")
        return InMemoryHistory()
