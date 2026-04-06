"""
Pydantic 模型模块
导出所有Pydantic模型
"""

from .base import (
    BaseSchema,
    TimestampMixin,
    IDMixin,
    PaginationParams,
    PaginatedResponse
)

from .attack import (
    AttackMode,
    RuleEngineMode,
    AttackRequest,
    ToolSeverity,
    AttackStep,
    RuleEngineDecision,
    TargetAnalysis,
    AttackResponse,
    AttackStatus,
    AttackStatusResponse
)

from .tool import (
    ToolCategory,
    ToolStatus,
    ToolExecuteRequest,
    ToolExecutionResult,
    ToolInfo,
    ToolHealthCheck,
    ToolsListResponse,
    ToolCategoryResponse
)

from .config import (
    Environment,
    LogLevel,
    CacheType,
    DatabaseType,
    ServerConfig,
    DatabaseConfig,
    SecurityConfig,
    CacheConfig,
    LLMProvider,
    LLMConfig,
    ToolConfig,
    LoggingConfig,
    AppConfig
)

from .error import (
    ErrorCode,
    ErrorSeverity,
    ErrorDetail,
    APIError,
    ValidationErrorResponse,
    NotFoundResponse,
    UnauthorizedResponse,
    ForbiddenResponse,
    ToolExecutionErrorResponse
)

from .audit import (
    AuditEventType,
    AuditEventSeverity,
    AuditEventStatus,
    AuditActor,
    AuditResource,
    AuditEvent,
    AuditEventFilters,
    AuditEventPage,
    AuditEventTemplates
)

from .auth import (
    Permission,
    UserRole,
    UserStatus,
    User,
    UserCreate,
    UserUpdate,
    UserLogin,
    UserPasswordChange,
    Role,
    RoleCreate,
    RoleUpdate,
    PermissionCheck,
    Token,
    TokenPayload,
    APIKey,
    APIKeyCreate,
    APIKeyResponse,
    LoginHistory,
    AuthResponse,
    PermissionGroups,
    check_permission,
    check_any_permission,
    check_all_permissions
)

__all__ = [
    # base
    "BaseSchema",
    "TimestampMixin",
    "IDMixin",
    "PaginationParams",
    "PaginatedResponse",

    # attack
    "AttackMode",
    "RuleEngineMode",
    "AttackRequest",
    "ToolSeverity",
    "AttackStep",
    "RuleEngineDecision",
    "TargetAnalysis",
    "AttackResponse",
    "AttackStatus",
    "AttackStatusResponse",

    # tool
    "ToolCategory",
    "ToolStatus",
    "ToolExecuteRequest",
    "ToolExecutionResult",
    "ToolInfo",
    "ToolHealthCheck",
    "ToolsListResponse",
    "ToolCategoryResponse",

    # config
    "Environment",
    "LogLevel",
    "CacheType",
    "DatabaseType",
    "ServerConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "CacheConfig",
    "LLMProvider",
    "LLMConfig",
    "ToolConfig",
    "LoggingConfig",
    "AppConfig",

    # error
    "ErrorCode",
    "ErrorSeverity",
    "ErrorDetail",
    "APIError",
    "ValidationErrorResponse",
    "NotFoundResponse",
    "UnauthorizedResponse",
    "ForbiddenResponse",
    "ToolExecutionErrorResponse",

    # audit
    "AuditEventType",
    "AuditEventSeverity",
    "AuditEventStatus",
    "AuditActor",
    "AuditResource",
    "AuditEvent",
    "AuditEventFilters",
    "AuditEventPage",
    "AuditEventTemplates",

    # auth
    "Permission",
    "UserRole",
    "UserStatus",
    "User",
    "UserCreate",
    "UserUpdate",
    "UserLogin",
    "UserPasswordChange",
    "Role",
    "RoleCreate",
    "RoleUpdate",
    "PermissionCheck",
    "Token",
    "TokenPayload",
    "APIKey",
    "APIKeyCreate",
    "APIKeyResponse",
    "LoginHistory",
    "AuthResponse",
    "PermissionGroups",
    "check_permission",
    "check_any_permission",
    "check_all_permissions",
]