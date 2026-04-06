# -*- coding: utf-8 -*-
"""
自定义异常类
统一管理所有自定义异常
"""

from typing import Optional, Dict, Any


class ClawAIError(Exception):
    """ClawAI基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于API响应"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(ClawAIError):
    """验证错误"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        validation_type: str = "general",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=400,
            details=details or {}
        )
        self.field = field
        self.validation_type = validation_type
        self.details["field"] = field
        self.details["validation_type"] = validation_type


class AuthenticationError(ClawAIError):
    """认证错误"""
    
    def __init__(
        self,
        message: str,
        auth_type: str = "bearer",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="authentication_error",
            status_code=401,
            details=details or {}
        )
        self.auth_type = auth_type
        self.details["auth_type"] = auth_type


class AuthorizationError(ClawAIError):
    """授权错误"""
    
    def __init__(
        self,
        message: str,
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="authorization_error",
            status_code=403,
            details=details or {}
        )
        self.required_permission = required_permission
        self.details["required_permission"] = required_permission


class ResourceNotFoundError(ClawAIError):
    """资源未找到错误"""
    
    def __init__(
        self,
        message: str,
        resource_type: str = "resource",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="resource_not_found",
            status_code=404,
            details=details or {}
        )
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details["resource_type"] = resource_type
        self.details["resource_id"] = resource_id


class ExecutionError(ClawAIError):
    """执行错误"""
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        execution_type: str = "tool_execution",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="execution_error",
            status_code=500,
            details=details or {}
        )
        self.tool_name = tool_name
        self.execution_type = execution_type
        self.details["tool_name"] = tool_name
        self.details["execution_type"] = execution_type


class ToolUnavailableError(ExecutionError):
    """工具不可用错误"""
    
    def __init__(
        self,
        tool_name: str,
        reason: str = "tool_not_installed",
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"工具不可用: {tool_name}"
        super().__init__(
            message=message,
            tool_name=tool_name,
            execution_type="tool_availability",
            details=details or {}
        )
        self.error_code = "tool_unavailable"
        self.reason = reason
        self.details["reason"] = reason


class ConfigurationError(ClawAIError):
    """配置错误"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_type: str = "environment",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="configuration_error",
            status_code=500,
            details=details or {}
        )
        self.config_key = config_key
        self.config_type = config_type
        self.details["config_key"] = config_key
        self.details["config_type"] = config_type


class RateLimitError(ClawAIError):
    """速率限制错误"""
    
    def __init__(
        self,
        message: str,
        limit_type: str = "api_rate_limit",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            status_code=429,
            details=details or {}
        )
        self.limit_type = limit_type
        self.retry_after = retry_after
        self.details["limit_type"] = limit_type
        self.details["retry_after"] = retry_after


class ExternalServiceError(ClawAIError):
    """外部服务错误"""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        service_type: str = "external_api",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="external_service_error",
            status_code=502,
            details=details or {}
        )
        self.service_name = service_name
        self.service_type = service_type
        self.details["service_name"] = service_name
        self.details["service_type"] = service_type


def create_error_response(
    error: Exception,
    include_traceback: bool = False
) -> tuple:
    """
    创建统一的错误响应
    
    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪
        
    Returns:
        (响应字典, HTTP状态码)
    """
    import traceback
    
    # 处理自定义异常
    if isinstance(error, ClawAIError):
        error_dict = error.to_dict()
        status_code = error.status_code
    else:
        # 通用错误处理
        error_dict = {
            "error": "internal_server_error",
            "message": str(error)
        }
        status_code = 500
    
    # 添加堆栈跟踪（仅在调试模式下）
    if include_traceback:
        error_dict["traceback"] = traceback.format_exception(
            type(error), error, error.__traceback__
        )
    
    return error_dict, status_code