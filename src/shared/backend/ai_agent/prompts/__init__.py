# -*- coding: utf-8 -*-
"""
提示词模块
"""

from .system_prompt import AI_AGENT_SYSTEM_PROMPT, get_system_prompt, get_simple_prompt
from .manager import PromptManager, PromptContext, PromptLanguage, create_prompt_manager

__all__ = [
    'AI_AGENT_SYSTEM_PROMPT',
    'get_system_prompt',
    'get_simple_prompt',
    'PromptManager',
    'PromptContext',
    'PromptLanguage',
    'create_prompt_manager'
]
