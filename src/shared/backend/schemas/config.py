"""
配置相关Pydantic模型
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseSchema


class Environment(str, Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CacheType(str, Enum):
    """缓存类型枚举"""
    MEMORY = "memory"
    REDIS = "redis"
    FILESYSTEM = "filesystem"


class DatabaseType(str, Enum):
    """数据库类型枚举"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"


class ServerConfig(BaseSchema):
    """服务器配置模型"""
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    workers: int = Field(default=1, ge=1, description="工作进程数")
    reload: bool = Field(default=False, description="是否启用热重载")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")


class DatabaseConfig(BaseSchema):
    """数据库配置模型"""
    type: DatabaseType = Field(default=DatabaseType.SQLITE, description="数据库类型")
    url: str = Field(default="sqlite:///./clawai.db", description="数据库连接URL")
    pool_size: int = Field(default=5, ge=1, le=50, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, description="最大溢出连接数")
    echo: bool = Field(default=False, description="是否输出SQL日志")


class SecurityConfig(BaseSchema):
    """安全配置模型"""
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        min_length=32,
        description="密钥"
    )
    jwt_secret: str = Field(
        default="your-jwt-secret-change-this-in-production",
        min_length=32,
        description="JWT密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT算法")
    jwt_expiration_hours: int = Field(default=24, ge=1, description="JWT过期时间（小时）")
    api_auth_enabled: bool = Field(default=True, description="是否启用API认证")
    enable_real_attack: bool = Field(default=False, description="是否启用真实攻击")
    mfa_enabled: bool = Field(default=False, description="是否启用多因素认证")
    cors_origins: list[str] = Field(default_factory=lambda: ["*"], description="CORS允许的源")


class CacheConfig(BaseSchema):
    """缓存配置模型"""
    type: CacheType = Field(default=CacheType.MEMORY, description="缓存类型")
    default_timeout: int = Field(default=300, ge=1, description="默认超时时间（秒）")
    redis_host: str = Field(default="localhost", description="Redis主机")
    redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis端口")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    redis_db: int = Field(default=0, ge=0, description="Redis数据库")


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"
    MOCK = "mock"


class LLMConfig(BaseSchema):
    """LLM配置模型"""
    provider: LLMProvider = Field(default=LLMProvider.OPENAI, description="LLM提供商")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    model: str = Field(default="gpt-4", description="模型名称")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=2000, ge=1, le=100000, description="最大token数")
    timeout: int = Field(default=60, ge=1, description="请求超时时间（秒）")


class ToolConfig(BaseSchema):
    """工具配置模型"""
    timeout: int = Field(default=30, ge=1, le=3600, description="工具超时时间（秒）")
    max_concurrent_tools: int = Field(default=5, ge=1, le=50, description="最大并发工具数")
    use_docker: bool = Field(default=True, description="是否使用Docker隔离")
    tools_dir: str = Field(default="./tools/penetration", description="工具目录")
    auto_install: bool = Field(default=False, description="是否自动安装工具")


class LoggingConfig(BaseSchema):
    """日志配置模型"""
    level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    file: Optional[str] = Field(default=None, description="日志文件路径")
    max_size: int = Field(default=10485760, description="最大文件大小（字节）")
    backup_count: int = Field(default=5, description="备份文件数量")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )


class AppConfig(BaseSchema):
    """应用配置模型"""
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="环境")
    project_name: str = Field(default="ClawAI", description="项目名称")
    project_version: str = Field(default="2.0.0", description="项目版本")
    project_description: str = Field(default="智能安全评估系统", description="项目描述")

    server: ServerConfig = Field(default_factory=ServerConfig, description="服务器配置")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="安全配置")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="缓存配置")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM配置")
    tool: ToolConfig = Field(default_factory=ToolConfig, description="工具配置")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")

    @validator('security')
    def validate_security(cls, v, values):
        """验证安全配置"""
        if values.get('environment') == Environment.PRODUCTION:
            if v.secret_key == "your-secret-key-change-this-in-production":
                raise ValueError("生产环境必须修改密钥")
            if v.jwt_secret == "your-jwt-secret-change-this-in-production":
                raise ValueError("生产环境必须修改JWT密钥")
            if v.cors_origins == ["*"]:
                raise ValueError("生产环境不能使用'*'作为CORS源")
        return v