# -*- coding: utf-8 -*-
"""
共享模块
包含跨层共享的组件
"""

from .exceptions import (
    ClawAIError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ExecutionError,
    ToolUnavailableError,
    ConfigurationError,
    RateLimitError,
    ExternalServiceError,
    create_error_response
)

__all__ = [
    'ClawAIError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'ResourceNotFoundError',
    'ExecutionError',
    'ToolUnavailableError',
    'ConfigurationError',
    'RateLimitError',
    'ExternalServiceError',
    'create_error_response'
]