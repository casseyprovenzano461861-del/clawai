"""
错误处理相关Pydantic模型
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .base import BaseSchema


class ErrorCode(str, Enum):
    """错误代码枚举"""
    # 通用错误
    UNKNOWN_ERROR = "unknown_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"

    # 认证错误
    INVALID_CREDENTIALS = "invalid_credentials"
    EXPIRED_TOKEN = "expired_token"
    INVALID_TOKEN = "invalid_token"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"

    # 工具执行错误
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_NOT_INSTALLED = "tool_not_installed"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    TOOL_TIMEOUT = "tool_timeout"

    # 配置错误
    CONFIGURATION_ERROR = "configuration_error"
    MISSING_CONFIGURATION = "missing_configuration"

    # 数据库错误
    DATABASE_ERROR = "database_error"
    DATABASE_CONNECTION_ERROR = "database_connection_error"

    # AI/LLM错误
    LLM_ERROR = "llm_error"
    LLM_RATE_LIMITED = "llm_rate_limited"
    LLM_PROVIDER_ERROR = "llm_provider_error"


class ErrorSeverity(str, Enum):
    """错误严重性枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorDetail(BaseSchema):
    """错误详情模型"""
    field: Optional[str] = Field(default=None, description="字段名称")
    message: str = Field(..., description="错误消息")
    value: Optional[Any] = Field(default=None, description="错误值")


class APIError(BaseSchema):
    """API错误响应模型"""
    code: ErrorCode = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: List[ErrorDetail] = Field(default_factory=list, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    severity: ErrorSeverity = Field(default=ErrorSeverity.MEDIUM, description="错误严重性")
    request_id: Optional[str] = Field(default=None, description="请求ID")
    documentation_url: Optional[str] = Field(default=None, description="文档URL")
    retryable: bool = Field(default=False, description="是否可重试")
    retry_after: Optional[int] = Field(default=None, description="重试等待时间（秒）")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": [detail.model_dump() for detail in self.details],
                "timestamp": self.timestamp.isoformat(),
                "severity": self.severity,
                "request_id": self.request_id,
                "documentation_url": self.documentation_url,
                "retryable": self.retryable,
                "retry_after": self.retry_after
            }
        }


class ValidationErrorResponse(APIError):
    """验证错误响应模型"""

    @classmethod
    def from_validation_error(
        cls,
        errors: List[Dict[str, Any]],
        request_id: Optional[str] = None
    ) -> "ValidationErrorResponse":
        """从验证错误创建响应"""
        details = []
        for error in errors:
            field = error.get("loc", [None])[-1]
            msg = error.get("msg", "验证失败")
            value = error.get("input")
            details.append(ErrorDetail(
                field=field,
                message=msg,
                value=value
            ))

        return cls(
            code=ErrorCode.VALIDATION_ERROR,
            message="请求数据验证失败",
            details=details,
            severity=ErrorSeverity.LOW,
            request_id=request_id
        )


class NotFoundResponse(APIError):
    """未找到错误响应模型"""

    @classmethod
    def create(
        cls,
        resource_type: str,
        resource_id: str,
        request_id: Optional[str] = None
    ) -> "NotFoundResponse":
        """创建未找到错误"""
        return cls(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource_type} '{resource_id}' 未找到",
            severity=ErrorSeverity.LOW,
            request_id=request_id
        )


class UnauthorizedResponse(APIError):
    """未授权错误响应模型"""

    @classmethod
    def create(
        cls,
        message: str = "认证失败",
        request_id: Optional[str] = None
    ) -> "UnauthorizedResponse":
        """创建未授权错误"""
        return cls(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id
        )


class ForbiddenResponse(APIError):
    """禁止访问错误响应模型"""

    @classmethod
    def create(
        cls,
        message: str = "没有访问权限",
        request_id: Optional[str] = None
    ) -> "ForbiddenResponse":
        """创建禁止访问错误"""
        return cls(
            code=ErrorCode.FORBIDDEN,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id
        )


class ToolExecutionErrorResponse(APIError):
    """工具执行错误响应模型"""

    @classmethod
    def create(
        cls,
        tool_name: str,
        error_message: str,
        request_id: Optional[str] = None
    ) -> "ToolExecutionErrorResponse":
        """创建工具执行错误"""
        return cls(
            code=ErrorCode.TOOL_EXECUTION_FAILED,
            message=f"工具 '{tool_name}' 执行失败: {error_message}",
            severity=ErrorSeverity.HIGH,
            request_id=request_id
        )