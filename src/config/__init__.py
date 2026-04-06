"""
统一配置管理系统
整合所有模块的配置，提供类型安全的配置访问
"""

from typing import Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 导入现有的配置模型（如果可用）
try:
    from shared.backend.schemas.config import (
        AppConfig,
        ServerConfig,
        DatabaseConfig,
        SecurityConfig,
        LoggingConfig,
        MonitoringConfig,
        LLMConfig,
        ToolConfig
    )
    HAS_EXISTING_CONFIG = True
except ImportError:
    HAS_EXISTING_CONFIG = False


class ModuleConfig(BaseSettings):
    """模块基础配置"""
    enabled: bool = Field(default=True, description="是否启用模块")
    config: Dict[str, Any] = Field(default_factory=dict, description="模块特定配置")


class UnifiedSettings(BaseSettings):
    """
    统一配置设置
    整合所有模块和服务的配置
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    # 应用基础配置
    app_name: str = Field(default="ClawAI", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")

    # 服务器配置
    server_host: str = Field(default="0.0.0.0", description="服务器主机")
    server_port: int = Field(default=8000, description="服务器端口")
    server_reload: bool = Field(default=False, description="热重载")

    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./clawai.db",
        description="数据库连接URL"
    )
    database_pool_size: int = Field(default=10, description="数据库连接池大小")
    database_echo: bool = Field(default=False, description="SQL日志")

    # Redis配置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    redis_enabled: bool = Field(default=True, description="是否启用Redis")

    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="应用密钥"
    )
    jwt_secret: str = Field(
        default="your-jwt-secret-change-this-in-production",
        description="JWT密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_expire_minutes: int = Field(default=1440, description="JWT过期时间(分钟)")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    enable_json_logging: bool = Field(default=False, description="是否启用JSON日志")

    # 模块配置
    modules: Dict[str, ModuleConfig] = Field(
        default_factory=lambda: {
            "api_gateway": ModuleConfig(enabled=True),
            "ai_engine": ModuleConfig(enabled=True),
            "tool_executor": ModuleConfig(enabled=True),
            "data_service": ModuleConfig(enabled=True),
        },
        description="模块配置"
    )

    # LLM配置
    llm_provider: str = Field(default="deepseek", description="LLM提供商")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API密钥")
    llm_base_url: Optional[str] = Field(default=None, description="LLM基础URL")
    llm_model: str = Field(default="deepseek-chat", description="LLM模型")

    # 工具配置
    tools_dir: str = Field(default="./tools/penetration", description="工具目录")
    tool_timeout: int = Field(default=300, description="工具执行超时时间(秒)")
    enable_container_isolation: bool = Field(
        default=True,
        description="是否启用容器隔离"
    )

    # 监控配置
    enable_metrics: bool = Field(default=True, description="是否启用指标监控")
    metrics_port: int = Field(default=9090, description="指标端口")
    enable_health_checks: bool = Field(default=True, description="是否启用健康检查")

    # 审计配置
    enable_audit_log: bool = Field(default=True, description="是否启用审计日志")
    audit_storage_dir: str = Field(
        default="./data/audit",
        description="审计日志存储目录"
    )
    audit_retention_days: int = Field(default=30, description="审计日志保留天数")

    def get_module_config(self, module_name: str) -> ModuleConfig:
        """
        获取模块配置

        Args:
            module_name: 模块名称

        Returns:
            模块配置
        """
        return self.modules.get(module_name, ModuleConfig(enabled=False))

    def is_module_enabled(self, module_name: str) -> bool:
        """
        检查模块是否启用

        Args:
            module_name: 模块名称

        Returns:
            是否启用
        """
        module_config = self.get_module_config(module_name)
        return module_config.enabled

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（排除敏感信息）

        Returns:
            配置字典
        """
        data = self.model_dump()

        # 脱敏敏感信息
        sensitive_fields = ["secret_key", "jwt_secret", "llm_api_key"]
        for field in sensitive_fields:
            if field in data and data[field]:
                data[field] = "***REDACTED***"

        return data

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            是否有效
        """
        # 基础验证
        if not self.app_name:
            raise ValueError("应用名称不能为空")

        if self.server_port < 1 or self.server_port > 65535:
            raise ValueError(f"无效的端口号: {self.server_port}")

        if self.environment not in ["development", "testing", "production"]:
            raise ValueError(f"无效的环境: {self.environment}")

        # 生产环境安全检查
        if self.environment == "production":
            if self.debug:
                raise ValueError("生产环境不能启用调试模式")

            if self.secret_key.startswith("your-secret-key"):
                raise ValueError("生产环境必须设置唯一的密钥")

            if self.jwt_secret.startswith("your-jwt-secret"):
                raise ValueError("生产环境必须设置唯一的JWT密钥")

        return True


# 全局配置实例
_settings_instance: Optional[UnifiedSettings] = None


def get_settings() -> UnifiedSettings:
    """
    获取全局配置实例

    Returns:
        配置实例
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = UnifiedSettings()
        try:
            _settings_instance.validate_config()
        except ValueError as e:
            # 记录警告但不终止应用
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"配置验证警告: {e}")
    return _settings_instance


def init_settings(config_file: Optional[str] = None) -> UnifiedSettings:
    """
    初始化配置

    Args:
        config_file: 配置文件路径

    Returns:
        配置实例
    """
    global _settings_instance

    # 如果已有实例，返回现有实例
    if _settings_instance is not None:
        return _settings_instance

    # 从环境变量和配置文件加载配置
    if config_file:
        # 使用指定的配置文件
        _settings_instance = UnifiedSettings(_env_file=config_file)
    else:
        # 使用默认的.env文件
        _settings_instance = UnifiedSettings()

    # 验证配置
    try:
        _settings_instance.validate_config()
    except ValueError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"配置验证失败: {e}")
        # 在生产环境中，可能需要终止应用
        if _settings_instance.environment == "production":
            raise

    return _settings_instance


# 导出常用函数和类
__all__ = [
    "UnifiedSettings",
    "ModuleConfig",
    "get_settings",
    "init_settings",
]