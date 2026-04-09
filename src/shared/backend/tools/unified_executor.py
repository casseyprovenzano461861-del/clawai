# -*- coding: utf-8 -*-
"""
unified_executor.py — 兼容性桥接模块

attack_service.py 导入 `UnifiedToolExecutor`，
实际实现在 unified_executor_final.py 中类名为 `UnifiedExecutor`。
此文件做名称桥接，修复静默 ImportError 导致的真实执行链路失效。
"""

from .unified_executor_final import UnifiedExecutor as UnifiedToolExecutor

__all__ = ["UnifiedToolExecutor"]
