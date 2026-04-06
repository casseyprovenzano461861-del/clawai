"""
错误处理器
统一错误处理系统，用于FastAPI应用
"""

import logging
import traceback
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from ..schemas.error import (
    APIError,
    ValidationErrorResponse,
    NotFoundResponse,
    UnauthorizedResponse,
    ForbiddenResponse,
    ToolExecutionErrorResponse,
    ErrorCode,
    ErrorSeverity
)
from ..security.sensitive_data import get_sensitive_data_manager, redact_sensitive_data


logger = logging.getLogger(__name__)


class ErrorHandler:
    """错误处理器类"""

    def __init__(self, app: Optional[FastAPI] = None):
        """
        初始化错误处理器

        Args:
            app: FastAPI应用实例
        """
        self.app = app
        if app:
            self.setup_handlers(app)

    def setup_handlers(self, app: FastAPI) -> None:
        """设置错误处理器"""
        # 验证错误
        app.add_exception_handler(
            RequestValidationError,
            self.handle_validation_error
        )

        # Pydantic验证错误
        app.add_exception_handler(
            ValidationError,
            self.handle_validation_error
        )

        # HTTP异常
        app.add_exception_handler(
            status.HTTP_404_NOT_FOUND,
            self.handle_404_not_found
        )

        app.add_exception_handler(
            status.HTTP_401_UNAUTHORIZED,
            self.handle_401_unauthorized
        )

        app.add_exception_handler(
            status.HTTP_403_FORBIDDEN,
            self.handle_403_forbidden
        )

        # 通用异常
        app.add_exception_handler(
            Exception,
            self.handle_generic_error
        )

    async def handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """处理验证错误"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        sensitive_data_manager = get_sensitive_data_manager()

        # 获取并脱敏错误列表
        raw_errors = exc.errors()
        sanitized_errors = []

        for error in raw_errors:
            # 深度复制错误字典以避免修改原始数据
            sanitized_error = error.copy()

            # 脱敏输入值（如果存在）
            if "input" in sanitized_error and sanitized_error["input"] is not None:
                if isinstance(sanitized_error["input"], str):
                    sanitized_error["input"] = sensitive_data_manager.redact_text(
                        sanitized_error["input"],
                        f"validation.error.input.{'.'.join(map(str, sanitized_error.get('loc', [])))}"
                    )
                elif isinstance(sanitized_error["input"], dict):
                    sanitized_error["input"] = sensitive_data_manager.redact_dict(
                        sanitized_error["input"],
                        f"validation.error.input.{'.'.join(map(str, sanitized_error.get('loc', [])))}"
                    )

            # 脱敏错误消息（如果包含敏感信息）
            if "msg" in sanitized_error and isinstance(sanitized_error["msg"], str):
                sanitized_error["msg"] = sensitive_data_manager.redact_text(
                    sanitized_error["msg"],
                    f"validation.error.msg.{'.'.join(map(str, sanitized_error.get('loc', [])))}"
                )

            sanitized_errors.append(sanitized_error)

        # 记录错误（使用脱敏后的错误）
        logger.warning(
            f"请求验证失败: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "client": request.client.host if request.client else "unknown",
                "error_count": len(sanitized_errors)
                # 注意：不记录完整的错误详情，可能包含敏感信息
            }
        )

        # 构建错误响应（使用脱敏后的错误）
        error_response = ValidationErrorResponse.from_validation_error(
            errors=sanitized_errors,
            request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.to_dict()
        )

    async def handle_404_not_found(
        self,
        request: Request,
        exc: Any
    ) -> JSONResponse:
        """处理404未找到错误"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # 记录错误
        logger.warning(
            f"资源未找到: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "client": request.client.host if request.client else "unknown"
            }
        )

        # 尝试从请求路径提取资源信息
        path = str(request.url.path)
        resource_parts = [p for p in path.split('/') if p]
        resource_type = resource_parts[-1] if resource_parts else "resource"
        resource_id = "unknown"

        # 构建错误响应
        error_response = NotFoundResponse.create(
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response.to_dict()
        )

    async def handle_401_unauthorized(
        self,
        request: Request,
        exc: Any
    ) -> JSONResponse:
        """处理401未授权错误"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # 记录错误
        logger.warning(
            f"未授权访问: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "client": request.client.host if request.client else "unknown"
            }
        )

        error_response = UnauthorizedResponse.create(
            message="认证失败，请提供有效的访问令牌",
            request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.to_dict()
        )

    async def handle_403_forbidden(
        self,
        request: Request,
        exc: Any
    ) -> JSONResponse:
        """处理403禁止访问错误"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # 记录错误
        logger.warning(
            f"禁止访问: {request.method} {request.url}",
            extra={
                "request_id": request_id,
                "client": request.client.host if request.client else "unknown"
            }
        )

        error_response = ForbiddenResponse.create(
            message="没有访问权限",
            request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response.to_dict()
        )

    async def handle_generic_error(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """处理通用错误"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        sensitive_data_manager = get_sensitive_data_manager()

        # 脱敏异常消息
        exc_message = str(exc)
        redacted_exc_message = sensitive_data_manager.redact_text(
            exc_message,
            f"error.generic.exception.{exc.__class__.__name__}"
        )

        # 获取并脱敏堆栈跟踪
        error_traceback = traceback.format_exc()
        redacted_traceback = sensitive_data_manager.redact_text(
            error_traceback,
            "error.generic.traceback"
        )

        # 记录错误详情（使用脱敏后的信息）
        logger.error(
            f"未处理的异常: {exc.__class__.__name__}: {redacted_exc_message}",
            extra={
                "request_id": request_id,
                "client": request.client.host if request.client else "unknown",
                "traceback": redacted_traceback[:500] if redacted_traceback else None  # 限制长度
            }
        )

        # 根据异常类型确定错误代码和严重性
        error_code = ErrorCode.UNKNOWN_ERROR
        severity = ErrorSeverity.HIGH
        message = "服务器内部错误"

        if isinstance(exc, ConnectionError):
            error_code = ErrorCode.DATABASE_CONNECTION_ERROR
            message = "数据库连接失败"
        elif isinstance(exc, TimeoutError):
            error_code = ErrorCode.TOOL_TIMEOUT
            message = "请求超时"
        elif "tool" in str(exc).lower():
            error_code = ErrorCode.TOOL_EXECUTION_FAILED
            # 使用脱敏后的异常消息
            message = f"工具执行失败: {redacted_exc_message}"

        # 构建错误响应（使用脱敏后的异常消息）
        error_response = APIError(
            code=error_code,
            message=message,
            details=[
                {
                    "field": None,
                    "message": redacted_exc_message,  # 脱敏后的消息
                    "value": None
                }
            ],
            severity=severity,
            request_id=request_id,
            retryable=True if error_code in [
                ErrorCode.DATABASE_CONNECTION_ERROR,
                ErrorCode.TOOL_TIMEOUT
            ] else False,
            retry_after=60 if error_code == ErrorCode.TOOL_TIMEOUT else None
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.to_dict()
        )

    def create_error_response(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[list] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """创建错误响应"""
        sensitive_data_manager = get_sensitive_data_manager()

        # 脱敏错误消息
        redacted_message = sensitive_data_manager.redact_text(
            message,
            f"error.response.message.{code.value}"
        )

        # 脱敏错误详情
        redacted_details = []
        if details:
            for i, detail in enumerate(details):
                if isinstance(detail, dict):
                    # 深度复制并脱敏每个字段
                    redacted_detail = detail.copy()

                    # 脱敏消息字段
                    if "message" in redacted_detail and isinstance(redacted_detail["message"], str):
                        redacted_detail["message"] = sensitive_data_manager.redact_text(
                            redacted_detail["message"],
                            f"error.response.details[{i}].message"
                        )

                    # 脱敏值字段
                    if "value" in redacted_detail and redacted_detail["value"] is not None:
                        if isinstance(redacted_detail["value"], str):
                            redacted_detail["value"] = sensitive_data_manager.redact_text(
                                redacted_detail["value"],
                                f"error.response.details[{i}].value"
                            )
                        elif isinstance(redacted_detail["value"], dict):
                            redacted_detail["value"] = sensitive_data_manager.redact_dict(
                                redacted_detail["value"],
                                f"error.response.details[{i}].value"
                            )
                        elif isinstance(redacted_detail["value"], list):
                            redacted_detail["value"] = sensitive_data_manager.redact_list(
                                redacted_detail["value"],
                                f"error.response.details[{i}].value"
                            )

                    redacted_details.append(redacted_detail)
                elif isinstance(detail, str):
                    # 字符串详情，直接脱敏
                    redacted_details.append(sensitive_data_manager.redact_text(
                        detail,
                        f"error.response.details[{i}]"
                    ))
                else:
                    # 其他类型，保留原样
                    redacted_details.append(detail)

        error_response = APIError(
            code=code,
            message=redacted_message,
            details=redacted_details,
            severity=severity,
            request_id=request_id
        )

        return JSONResponse(
            status_code=status_code,
            content=error_response.to_dict()
        )


# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler(app: Optional[FastAPI] = None) -> ErrorHandler:
    """获取错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(app)
    elif app and _error_handler.app != app:
        _error_handler.setup_handlers(app)
        _error_handler.app = app

    return _error_handler


def setup_error_handlers(app: FastAPI) -> None:
    """设置错误处理器（快捷方式）"""
    get_error_handler(app)