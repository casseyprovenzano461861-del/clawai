# -*- coding: utf-8 -*-
"""
配置模块

提供统一的配置管理系统，包括：
- EnhancedSettings: 增强的统一配置
- SecretManager: API Key 安全管理
- ConfigManager: 兼容旧配置管理器
"""

from .unified_settings import (
    EnhancedSettings,
    RAGConfig,
    TokenBudgetConfig,
    LLMProviderConfig,
    LLMProvider,
    get_settings,
    init_settings,
    reload_settings
)

from .secret_manager import (
    SecretManager,
    get_secret_manager,
    store_api_key,
    get_api_key
)

# 保留旧的 ConfigManager 以向后兼容
from .manager import (
    ConfigManager,
    get_config_manager,
    get_config
)

__all__ = [
    # 新配置系统
    "EnhancedSettings",
    "RAGConfig",
    "TokenBudgetConfig",
    "LLMProviderConfig",
    "LLMProvider",
    "get_settings",
    "init_settings",
    "reload_settings",

    # 安全管理
    "SecretManager",
    "get_secret_manager",
    "store_api_key",
    "get_api_key",

    # 兼容旧系统
    "ConfigManager",
    "get_config_manager",
    "get_config",
]
