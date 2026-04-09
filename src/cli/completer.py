# -*- coding: utf-8 -*-
"""
ClawAI CLI 命令补全系统

基于 prompt_toolkit 实现的智能命令补全，支持：
- 内联控制命令（session/pause/resume/stop/追加指令等）
- 意图触发关键词（扫描/scan/报告/report 等）
- session load <id> 动态补全已保存的 session_id
- 中英文混合补全
- 持久化历史（~/.clawai/history）

快速使用
--------
    from src.cli.completer import get_prompt_session

    session = get_prompt_session()
    text = await session.prompt_async("❯ ")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.styles import Style

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 补全候选词表
# ---------------------------------------------------------------------------

# 内联控制命令（完整命令字符串）
_INLINE_COMMANDS: list[tuple[str, str]] = [
    # session 系列
    ("session list",             "列出所有已保存会话"),
    ("sessions",                 "列出所有已保存会话"),
    ("session save",             "手动保存当前会话"),
    ("session load ",            "加载指定会话（后接 session_id）"),
    ("session export markdown",  "导出会话报告（Markdown 格式）"),
    ("session export json",      "导出会话报告（JSON 格式）"),
    ("session export html",      "导出会话报告（HTML 格式）"),
    # 干预控制
    ("pause",                    "暂停 Agent 执行"),
    ("暂停",                      "暂停 Agent 执行"),
    ("resume",                   "恢复 Agent 执行"),
    ("继续",                      "恢复 Agent 执行"),
    ("恢复",                      "恢复 Agent 执行"),
    ("stop",                     "停止 Agent 执行"),
    ("停止",                      "停止 Agent 执行"),
    ("中止",                      "停止 Agent 执行"),
    # 追加指令前缀
    ("追加指令:",                  "向 Agent 追加自然语言指令"),
    ("追加:",                      "向 Agent 追加自然语言指令（简写）"),
    ("add instruction:",         "Append instruction to Agent"),
    ("instruct:",                "Append instruction to Agent (short)"),
    # 帮助/退出
    ("help",                     "显示帮助"),
    ("帮助",                      "显示帮助"),
    ("?",                        "显示帮助"),
    ("exit",                     "退出 ClawAI"),
    ("quit",                     "退出 ClawAI"),
    ("退出",                      "退出 ClawAI"),
    ("bye",                      "退出 ClawAI"),
    ("再见",                      "退出 ClawAI"),
]

# 意图触发关键词（不是完整命令，是对话开头词）
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
    ("export ",     "Export report"),
    ("总结",        "总结发现"),
    ("状态",        "查看当前状态"),
    ("status",      "Check current status"),
    ("配置",        "查看当前配置"),
    ("config",      "Show current config"),
]

# 所有顶层命令词首字（用于快速过滤）
_ALL_CANDIDATES = _INLINE_COMMANDS + _INTENT_KEYWORDS


# ---------------------------------------------------------------------------
# 核心补全器
# ---------------------------------------------------------------------------

class ClawAICompleter(Completer):
    """ClawAI 智能命令补全器

    补全策略：
    1. 空输入 → 展示所有内联命令（最多 20 个）
    2. 'session load ' 结尾 → 动态补全已保存的 session_id
    3. 其他前缀 → 从候选词表中前缀匹配
    """

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        text = document.text_before_cursor

        # ── 动态补全 session_id ──
        if text.lower().startswith("session load "):
            prefix_after_cmd = text[len("session load "):]
            yield from self._complete_session_ids(prefix_after_cmd)
            return

        # ── 空输入：展示常用内联命令 ──
        if not text.strip():
            for cmd, meta in _INLINE_COMMANDS[:20]:
                yield Completion(cmd, start_position=0, display_meta=meta)
            return

        # ── 前缀匹配所有候选词 ──
        text_lower = text.lower()
        for candidate, meta in _ALL_CANDIDATES:
            if candidate.lower().startswith(text_lower):
                # 计算需要补全的字符数
                yield Completion(
                    candidate,
                    start_position=-len(text),
                    display=candidate,
                    display_meta=meta,
                )

    # ------------------------------------------------------------------
    # 动态 session_id 补全
    # ------------------------------------------------------------------

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

CLAWAI_STYLE = Style.from_dict(
    {
        # 提示符颜色
        "prompt":          "bold ansicyan",
        # 补全菜单
        "completion-menu.completion":         "bg:#1e1e2e fg:#cdd6f4",
        "completion-menu.completion.current": "bg:#313244 fg:#89dceb bold",
        "completion-menu.meta":               "bg:#1e1e2e fg:#6c7086",
        "completion-menu.meta.current":       "bg:#313244 fg:#a6adc8",
        # 提示框边框
        "completion-menu.border":             "fg:#313244",
        # 滚动条
        "scrollbar.background":               "bg:#313244",
        "scrollbar.button":                   "bg:#585b70",
    }
)


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def get_prompt_session(history_file: str | Path | None = None):
    """创建带历史记录和补全的 PromptSession

    Args:
        history_file: 历史文件路径。None 则尝试 ~/.clawai/history，
                      失败则回退到内存历史。

    Returns:
        prompt_toolkit.PromptSession
    """
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

    # 尝试持久化历史
    history = _make_history(history_file)

    return PromptSession(
        completer=ClawAICompleter(),
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        style=CLAWAI_STYLE,
        complete_while_typing=True,  # 边输入边补全
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
