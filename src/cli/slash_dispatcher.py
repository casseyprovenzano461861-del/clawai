#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 斜杠命令分发器
借鉴 cc-haha 的命令路由模式：/cmd → 注册表, !cmd → bash, 其余 → 自然语言

三种输入模式:
  /command args  → 注册表查找，确定性执行
  !command       → 直接执行 bash 命令
  自然语言        → IntentRecognizer → AI 对话
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.cli.commands import CommandMeta, CommandRegistry

logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    """分发结果

    action:
      - "slash_cmd"      → 斜杠命令，command_meta 和 args 已填充
      - "bash_cmd"       → bash 命令，args[0] 是 shell 命令字符串
      - "natural_language" → 自然语言，passthrough 是原始输入
      - "unknown_slash"  → 未识别的斜杠命令，passthrough 是建议列表
    """
    action: str
    command_meta: Optional[CommandMeta] = None
    args: List[str] = field(default_factory=list)
    passthrough: Any = None  # 原始输入或建议列表
    tool_name: Optional[str] = None  # 直接工具执行时的工具名


class SlashDispatcher:
    """斜杠命令分发器

    将用户输入路由到:
    1. /command → CommandRegistry 查找
    2. /tool_name args → 直接执行工具 (如果工具名与命令名匹配)
    3. !command → bash 执行
    4. 其余    → IntentRecognizer (自然语言)
    """

    def __init__(self, registry: CommandRegistry, chat_cli=None):
        self.registry = registry
        self.chat_cli = chat_cli
        self._tool_names: Optional[set] = None

    def _get_tool_names(self) -> set:
        """懒加载工具名集合"""
        if self._tool_names is None:
            try:
                from src.cli.tools import get_tool_registry
                self._tool_names = {t.name for t in get_tool_registry().all_tools()}
            except Exception:
                self._tool_names = set()
        return self._tool_names

    def dispatch(self, raw_input: str) -> DispatchResult:
        """根据输入前缀分发到不同的处理路径

        Args:
            raw_input: 用户原始输入

        Returns:
            DispatchResult 分发结果
        """
        stripped = raw_input.strip()
        if not stripped:
            return DispatchResult("natural_language", passthrough=raw_input)

        # Bash 模式: ! 前缀
        if stripped.startswith("!"):
            bash_cmd = stripped[1:].strip()
            if not bash_cmd:
                return DispatchResult("natural_language", passthrough=raw_input)
            return DispatchResult("bash_cmd", args=[bash_cmd])

        # 斜杠命令: / 前缀
        if stripped.startswith("/"):
            return self._parse_slash(stripped)

        # 自然语言: 透传到 IntentRecognizer
        return DispatchResult("natural_language", passthrough=raw_input)

    def _parse_slash(self, text: str) -> DispatchResult:
        """解析斜杠命令

        格式: /command [args...]
        支持: /help, /scan target.com, /session list, /pause, /exit
              /nmap target, /sqlmap url, /nuclei target (直接工具)
        """
        # 去掉前导 /
        content = text[1:].strip()
        if not content:
            # 只输入了 /，显示帮助
            meta = self.registry.lookup("help")
            if meta:
                return DispatchResult("slash_cmd", command_meta=meta, args=[])
            return DispatchResult("unknown_slash", args=[], passthrough=[])

        parts = content.split()
        cmd_name = parts[0].lower()
        cmd_args = parts[1:]

        # 精确查找命令
        meta = self.registry.lookup(cmd_name)
        if meta:
            return DispatchResult("slash_cmd", command_meta=meta, args=cmd_args)

        # 检查是否匹配工具名 (直接执行工具)
        if cmd_name in self._get_tool_names():
            return DispatchResult("direct_tool", tool_name=cmd_name, args=cmd_args)

        # 未找到，提供模糊建议
        suggestions = self.registry.fuzzy_match(cmd_name)
        return DispatchResult("unknown_slash", args=[cmd_name] + cmd_args,
                             passthrough=suggestions)
