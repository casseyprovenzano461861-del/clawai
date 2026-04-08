# -*- coding: utf-8 -*-
"""
增强的统一配置系统
支持多模型提供商、RAG 配置、工具路径外部化
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM 提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


class LLMProviderConfig(BaseSettings):
    """单个 LLM 提供商配置"""
    base_url: str = ""
    default_model: str = ""
    models: List[str] = Field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60

    model_config = SettingsConfigDict(extra="allow")


class RAGConfig(BaseSettings):
    """RAG 配置"""
    enabled: bool = Field(default=True, description="是否启用 RAG")
    qdrant_host: str = Field(default="localhost", description="Qdrant 主机")
    qdrant_port: int = Field(default=16333, description="Qdrant 端口")
    qdrant_grpc_port: int = Field(default=16334, description="Qdrant gRPC 端口")
    embedding_model: str = Field(
        default="BAAI/bge-small-zh-v1.5",
        description="嵌入模型"
    )
    collection_name: str = Field(
        default="security_knowledge",
        description="集合名称"
    )
    chunk_size: int = Field(default=500, description="文本块大小")
    chunk_overlap: int = Field(default=50, description="文本块重叠")
    top_k: int = Field(default=5, description="检索返回数量")
    score_threshold: float = Field(default=0.7, description="相似度阈值")


class TokenBudgetConfig(BaseSettings):
    """Token 预算配置"""
    enabled: bool = Field(default=True, description="是否启用预算管理")
    max_total_tokens: int = Field(default=100000, description="总 Token 预算")
    max_per_phase: Dict[str, int] = Field(
        default_factory=lambda: {
            "planning": 5000,
            "execution": 2000,
            "reflection": 3000
        },
        description="每阶段预算"
    )
    warning_threshold: float = Field(default=0.8, description="警告阈值")
    auto_throttle: bool = Field(default=True, description="自动限流")


class EnhancedSettings(BaseSettings):
    """
    增强的统一配置设置

    整合：
    - 多模型提供商支持
    - RAG 配置
    - Token 预算管理
    - 工具路径外部化
    - API Key 安全管理
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== 基础配置 ====================
    app_name: str = Field(default="ClawAI", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")

    # ==================== 服务器配置 ====================
    server_host: str = Field(default="0.0.0.0", description="服务器主机")
    server_port: int = Field(default=8000, description="服务器端口")
    server_reload: bool = Field(default=False, description="热重载")

    # ==================== 数据库配置 ====================
    database_url: str = Field(
        default="sqlite:///./clawai.db",
        description="数据库连接URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )

    # ==================== 安全配置 ====================
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="应用密钥"
    )
    jwt_secret: str = Field(
        default="your-jwt-secret-change-this-in-production",
        description="JWT密钥"
    )
    clawai_secret_key: Optional[str] = Field(
        default=None,
        description="敏感信息加密密钥"
    )

    # ==================== LLM 多模型配置 ====================
    active_provider: str = Field(
        default="deepseek",
        description="当前使用的提供商"
    )
    active_model: str = Field(
        default="deepseek-chat",
        description="当前使用的模型"
    )

    llm_providers: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "deepseek": {
                "base_url": "https://api.deepseek.com",
                "default_model": "deepseek-chat",
                "models": ["deepseek-chat", "deepseek-coder"],
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "openai": {
                "base_url": "https://api.openai.com",
                "default_model": "gpt-4",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "azure": {
                "base_url": "",
                "default_model": "gpt-4",
                "models": ["gpt-4", "gpt-35-turbo"],
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "anthropic": {
                "base_url": "https://api.anthropic.com",
                "default_model": "claude-3-opus-20240229",
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                "max_tokens": 4096,
                "temperature": 0.7
            }
        },
        description="LLM 提供商配置"
    )

    # ==================== RAG 配置 ====================
    rag: RAGConfig = Field(
        default_factory=RAGConfig,
        description="RAG 配置"
    )

    # ==================== Token 预算配置 ====================
    token_budget: TokenBudgetConfig = Field(
        default_factory=TokenBudgetConfig,
        description="Token 预算配置"
    )

    # ==================== 工具配置 ====================
    tools_dir: str = Field(default="./tools/penetration", description="工具目录")
    tool_timeout: int = Field(default=300, description="工具执行超时时间(秒)")
    tool_paths_file: str = Field(
        default="config/tool_paths.yaml",
        description="工具路径配置文件"
    )
    tool_paths: Dict[str, str] = Field(
        default_factory=dict,
        description="工具路径映射"
    )

    # ==================== 日志配置 ====================
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: Optional[str] = Field(default=None, description="日志文件路径")

    # ==================== 监控配置 ====================
    enable_metrics: bool = Field(default=True, description="是否启用指标监控")
    enable_health_checks: bool = Field(default=True, description="是否启用健康检查")

    # ==================== 方法 ====================

    def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        获取提供商配置

        Args:
            provider: 提供商名称，默认使用 active_provider

        Returns:
            提供商配置字典
        """
        provider_name = provider or self.active_provider
        return self.llm_providers.get(provider_name, {})

    def get_active_model_config(self) -> Dict[str, Any]:
        """获取当前活动模型的配置"""
        provider_config = self.get_provider_config()
        return {
            "provider": self.active_provider,
            "model": self.active_model,
            "base_url": provider_config.get("base_url", ""),
            "max_tokens": provider_config.get("max_tokens", 4096),
            "temperature": provider_config.get("temperature", 0.7),
        }

    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """
        获取工具路径

        Args:
            tool_name: 工具名称

        Returns:
            工具路径或 None
        """
        # 优先使用运行时加载的路径
        if tool_name in self.tool_paths:
            return self.tool_paths[tool_name]

        # 从配置文件加载
        self._load_tool_paths()

        return self.tool_paths.get(tool_name)

    def _load_tool_paths(self) -> None:
        """从配置文件加载工具路径"""
        if self.tool_paths:  # 已加载
            return

        config_path = Path(self.tool_paths_file)
        if not config_path.is_absolute():
            # 尝试多个位置
            search_paths = [
                Path.cwd() / self.tool_paths_file,
                Path(__file__).parent.parent.parent.parent.parent / self.tool_paths_file,
                Path.home() / ".clawai" / "tool_paths.yaml",
            ]
            for p in search_paths:
                if p.exists():
                    config_path = p
                    break

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    self.tool_paths = data.get("tools", {})
                logger.debug(f"已加载工具路径配置: {config_path}")
            except Exception as e:
                logger.warning(f"加载工具路径配置失败: {e}")

    def switch_provider(self, provider: str, model: Optional[str] = None) -> bool:
        """
        切换 LLM 提供商

        Args:
            provider: 提供商名称
            model: 模型名称（可选）

        Returns:
            是否成功切换
        """
        if provider not in self.llm_providers:
            logger.error(f"未知的提供商: {provider}")
            return False

        self.active_provider = provider

        if model:
            if model in self.llm_providers[provider].get("models", []):
                self.active_model = model
            else:
                logger.warning(f"模型 {model} 不在提供商 {provider} 的模型列表中")
                self.active_model = self.llm_providers[provider].get("default_model", "")
        else:
            self.active_model = self.llm_providers[provider].get("default_model", "")

        logger.info(f"已切换到 {provider}/{self.active_model}")
        return True

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """
        获取 API Key（通过 SecretManager）

        Args:
            provider: 提供商名称，默认使用 active_provider

        Returns:
            API Key 或 None
        """
        from .secret_manager import get_api_key
        provider_name = provider or self.active_provider
        return get_api_key(provider_name)

    def to_dict(self, safe: bool = True) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            safe: 是否脱敏敏感信息

        Returns:
            配置字典
        """
        data = self.model_dump()

        if safe:
            # 脱敏敏感信息
            sensitive_fields = ["secret_key", "jwt_secret", "clawai_secret_key"]
            for field in sensitive_fields:
                if field in data and data[field]:
                    data[field] = "***REDACTED***"

        return data

    def validate_for_production(self) -> List[str]:
        """
        验证生产环境配置

        Returns:
            错误消息列表（空列表表示验证通过）
        """
        errors = []

        if self.debug:
            errors.append("生产环境不能启用调试模式")

        if self.secret_key.startswith("your-secret-key"):
            errors.append("生产环境必须设置唯一的应用密钥")

        if self.jwt_secret.startswith("your-jwt-secret"):
            errors.append("生产环境必须设置唯一的JWT密钥")

        # 检查 API Key
        from .secret_manager import get_api_key
        api_key = get_api_key(self.active_provider)
        if not api_key:
            errors.append(f"未配置 {self.active_provider} 的 API Key")

        return errors


# ==================== 全局实例管理 ====================

_settings_instance: Optional[EnhancedSettings] = None


def get_settings() -> EnhancedSettings:
    """获取全局配置实例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = EnhancedSettings()
    return _settings_instance


def init_settings(
    config_file: Optional[str] = None,
    **overrides
) -> EnhancedSettings:
    """
    初始化配置

    Args:
        config_file: 配置文件路径
        **overrides: 配置覆盖项

    Returns:
        配置实例
    """
    global _settings_instance

    if _settings_instance is not None:
        return _settings_instance

    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)
                overrides = {**data, **overrides}

    _settings_instance = EnhancedSettings(**overrides)

    # 验证生产环境配置
    if _settings_instance.environment == "production":
        errors = _settings_instance.validate_for_production()
        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            raise ValueError(f"生产环境配置验证失败: {errors}")

    return _settings_instance


def reload_settings() -> EnhancedSettings:
    """重新加载配置"""
    global _settings_instance
    _settings_instance = None
    return get_settings()


# 导出
__all__ = [
    "EnhancedSettings",
    "RAGConfig",
    "TokenBudgetConfig",
    "LLMProviderConfig",
    "LLMProvider",
    "get_settings",
    "init_settings",
    "reload_settings"
]
