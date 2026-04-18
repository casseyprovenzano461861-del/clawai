# -*- coding: utf-8 -*-
"""
Skills 库模块

提供 AI 可自动调用的渗透测试技能
包括：POC、Exploit 脚本、利用方法等
"""

from .core import (
    Skill,
    SkillType,
    SkillCategory,
    SkillParameter,
    SkillExecutor,
)

from .context import SkillContext

from .registry import (
    SkillRegistry,
    get_skill_registry,
)

from .markdown_loader import (
    parse_skill_markdown,
    load_skills_from_dir,
)

from .extended_skills import (
    PayloadMutator,
    WAF_SIGNATURES,
    FLAG_PATTERNS,
    get_waf_bypass_payloads,
)

__all__ = [
    # 核心类
    "Skill",
    "SkillType",
    "SkillCategory",
    "SkillParameter",
    "SkillExecutor",
    # 依赖注入上下文
    "SkillContext",
    # 注册表
    "SkillRegistry",
    "get_skill_registry",
    # Markdown 加载器
    "parse_skill_markdown",
    "load_skills_from_dir",
    # 扩展功能
    "PayloadMutator",
    "WAF_SIGNATURES",
    "FLAG_PATTERNS",
    "get_waf_bypass_payloads",
]
