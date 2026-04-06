"""
Skills library package.
"""

from .base_skill import BaseSkill, SkillContext
from .skill_registry import SkillRegistry, registry
from .nmap_skill import NmapScanSkill
from .whatweb_skill import WhatWebSkill
from .sql_injection_skill import SQLInjectionSkill
from .rce_skill import RCESkill
from .privilege_escalation_skill import PrivilegeEscalationSkill

# 导出所有技能类
__all__ = [
    'BaseSkill',
    'SkillContext',
    'SkillRegistry',
    'registry',
    'NmapScanSkill',
    'WhatWebSkill',
    'SQLInjectionSkill',
    'RCESkill',
    'PrivilegeEscalationSkill'
]

# 自动注册所有技能
def register_all_skills():
    """注册所有技能到全局注册表"""
    from .skill_registry import registry
    
    skills = [
        NmapScanSkill(),
        WhatWebSkill(),
        SQLInjectionSkill(),
        RCESkill(),
        PrivilegeEscalationSkill()
    ]
    
    for skill in skills:
        registry.register_skill(skill)
    
    return len(skills)

# 初始化时自动注册技能
try:
    skills_registered = register_all_skills()
    print(f"[SUCCESS] 已自动注册 {skills_registered} 个技能到全局注册表")
except Exception as e:
    print(f"[WARNING] 技能自动注册失败: {e}")

