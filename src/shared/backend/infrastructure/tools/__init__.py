# -*- coding: utf-8 -*-
"""
工具基础设施层
包含工具注册表、统一执行器和适配器
"""

from .tool_registry import (
    ToolResult,
    ToolAdapter,
    ToolRegistry,
    NmapAdapter,
    WhatWebAdapter,
    MockNucleiAdapter,
    create_default_registry
)
from .unified_executor import UnifiedToolExecutor

__all__ = [
    'ToolResult',
    'ToolAdapter',
    'ToolRegistry',
    'NmapAdapter',
    'WhatWebAdapter',
    'MockNucleiAdapter',
    'create_default_registry',
    'UnifiedToolExecutor'
]