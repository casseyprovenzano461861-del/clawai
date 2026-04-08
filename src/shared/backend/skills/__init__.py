# -*- coding: utf-8 -*-
"""
Skills 库模块

提供 AI 可自动调用的渗透测试技能
包括：POC、Exploit 脚本、利用方法等

整合自优秀项目:
- CyberStrikeAI: 知识型 Skills (XXE, SSRF, 文件上传等)
- PentestGPT: 实战 Exploit (Flag检测, OpenSSH枚举)
- NeuroSploit: PoC生成器, WAF绕过, Payload变异
"""

from .core import (
    Skill,
    SkillType,
    SkillCategory,
    SkillParameter,
    SkillExecutor,
)

from .registry import (
    SkillRegistry,
    get_skill_registry,
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
    # 注册表
    "SkillRegistry",
    "get_skill_registry",
    # 扩展功能
    "PayloadMutator",
    "WAF_SIGNATURES",
    "FLAG_PATTERNS",
    "get_waf_bypass_payloads",
]
