# -*- coding: utf-8 -*-
"""
错误处理中间件
统一的错误处理和响应格式化
"""

from typing import Callable, Optional, Dict, Any

from flask import request, jsonify, g
import logging

from backend.shared.exceptions import (
    ClawAIError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ExecutionError,
    create_error_response
)


# 配置日志
logger = logging.getLogger(__name__)


def setup_error_logging(app):
    """
    设置错误日志记录
    
    Args:
        app: Flask应用实例
    """
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.ERROR)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        app.logger.addHandler(file_handler)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    记录错误
    
    Args:
        error: 异常对象
        context: 错误上下文信息
    """
    error_context = context or {}
    
    # 构建错误信息
    error_info = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "endpoint": request.endpoint if request else None,
        "method": request.method if request else None,
        "path": request.path if request else None,
        "user_id": g.get('user', {}).get('id') if hasattr(g, 'user') else None,
        "username": g.get('user', {}).get('username') if hasattr(g, 'user') else None,
        "timestamp": getattr(g, 'request_start_time', None),
        **error_context
    }
    
    # 记录错误
    if isinstance(error, (ValidationError, AuthenticationError, AuthorizationError)):
        logger.warning(f"客户端错误: {error_info}")
    elif isinstance(error, ExecutionError):
        logger.error(f"执行错误: {error_info}")
    else:
        logger.error(f"服务器错误: {error_info}", exc_info=True)


def handle_validation_error(error: ValidationError):
    """
    处理验证错误
    
    Args:
        error: ValidationError异常
        
    Returns:
        Flask响应
    """
    log_error(error, {
        "field": error.field,
        "validation_type": error.validation_type
    })
    
    error_dict, status_code = create_error_response(error)
    return jsonify(error_dict), status_code


def handle_authentication_error(error: AuthenticationError):
    """
    处理认证错误
    
    Args:
        error: AuthenticationError异常
        
    Returns:
        Flask响应
    """
    log_error(error, {
        "auth_type": error.auth_type
    })
    
    error_dict, status_code = create_error_response(error)
    return jsonify(error_dict), status_code


def handle_authorization_error(error: AuthorizationError):
    """
    处理授权错误
    
    Args:
        error: AuthorizationError异常
        
    Returns:
        Flask响应
    """
    log_error(error, {
        "required_permission": error.required_permission
    })
    
    error_dict, status_code = create_error_response(error)
    return jsonify(error_dict), status_code


def handle_execution_error(error: ExecutionError):
    """
    处理执行错误
    
    Args:
        error: ExecutionError异常
        
    Returns:
        Flask响应
    """
    log_error(error, {
        "tool_name": error.tool_name,
        "execution_type": error.execution_type
    })
    
    error_dict, status_code = create_error_response(error)
    return jsonify(error_dict), status_code


def handle_resource_not_found(error: ResourceNotFoundError):
    """
    处理资源未找到错误
    
    Args:
        error: ResourceNotFoundError异常
        
    Returns:
        Flask响应
    """
    log_error(error, {
        "resource_type": error.resource_type,
        "resource_id": error.resource_id
    })
    
    error_dict, status_code = create_error_response(error)
    return jsonify(error_dict), status_code


def handle_not_found(error):
    """
    处理404错误
    
    Args:
        error: 404异常
        
    Returns:
        Flask响应
    """
    resource_not_found = ResourceNotFoundError(
        message="请求的资源不存在",
        resource_type="endpoint",
        resource_id=request.path
    )
    
    return handle_resource_not_found(resource_not_found)


def handle_method_not_allowed(error):
    """
    处理405错误
    
    Args:
        error: 405异常
        
    Returns:
        Flask响应
    """
    error_dict = {
        "error": "method_not_allowed",
        "message": "请求方法不允许",
        "details": {
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "requested_method": request.method,
            "endpoint": request.path
        }
    }
    
    logger.warning(f"方法不允许: {error_dict}")
    
    return jsonify(error_dict), 405


def handle_internal_server_error(error):
    """
    处理500错误
    
    Args:
        error: 内部服务器错误
        
    Returns:
        Flask响应
    """
    # 创建内部服务器错误
    internal_error = ClawAIError(
        message="服务器内部错误",
        error_code="internal_server_error",
        status_code=500
    )
    
    # 记录详细错误信息
    log_error(error, {
        "error_type": "InternalServerError",
        "request_id": getattr(g, 'request_id', None)
    })
    
    # 创建响应
    error_dict, status_code = create_error_response(internal_error)
    
    # 在调试模式下添加堆栈跟踪
    from flask import current_app
    if current_app.debug:
        import traceback
        error_dict["traceback"] = traceback.format_exception(
            type(error), error, error.__traceback__
        )
    
    return jsonify(error_dict), status_code


def error_handler_middleware():
    """
    错误处理中间件
    
    捕获并处理所有未处理的异常
    """
    try:
        # 执行请求处理
        return
    except Exception as e:
        # 处理未捕获的异常
        if isinstance(e, ClawAIError):
            # 如果是自定义异常，直接处理
            if isinstance(e, ValidationError):
                return handle_validation_error(e)
            elif isinstance(e, AuthenticationError):
                return handle_authentication_error(e)
            elif isinstance(e, AuthorizationError):
                return handle_authorization_error(e)
            elif isinstance(e, ExecutionError):
                return handle_execution_error(e)
            elif isinstance(e, ResourceNotFoundError):
                return handle_resource_not_found(e)
            else:
                return handle_internal_server_error(e)
        else:
            # 其他异常转换为内部服务器错误
            return handle_internal_server_error(e)


def setup_request_context():
    """
    设置请求上下文
    
    在请求开始时设置请求ID和开始时间
    """
    import time
    import uuid
    from flask import request, g
    
    # 记录请求开始时间
    g.request_start_time = time.time()
    
    # 生成请求ID
    g.request_id = str(uuid.uuid4())[:8]
    
    # 记录请求信息
    request_info = {
        "request_id": g.request_id,
        "method": request.method,
        "path": request.path,
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string if request.user_agent else None,
        "content_type": request.content_type,
        "content_length": request.content_length
    }
    
    logger.info(f"请求开始: {request_info}")


def request_logging_middleware(response):
    """
    请求日志中间件
    
    记录响应信息
    
    Args:
        response: Flask响应对象
        
    Returns:
        响应对象
    """
    import time
    from flask import request, g
    
    # 计算请求耗时
    request_time = time.time() - g.request_start_time
    
    # 记录响应信息
    response_info = {
        "request_id": g.request_id,
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "response_time": f"{request_time:.3f}s",
        "content_length": response.content_length
    }
    
    # 根据状态码选择日志级别
    if response.status_code >= 500:
        logger.error(f"请求结束: {response_info}")
    elif response.status_code >= 400:
        logger.warning(f"请求结束: {response_info}")
    else:
        logger.info(f"请求结束: {response_info}")
    
    return response


def safe_execute(func: Callable, *args, **kwargs):
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果，如果出错则返回错误响应
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(e)
        
        # 返回错误响应
        error_dict, status_code = create_error_response(e)
        return jsonify(error_dict), status_code


def register_error_handlers(app):
    """
    注册错误处理器到Flask应用
    
    Args:
        app: Flask应用实例
        
    Returns:
        配置好的Flask应用
    """
    # 设置错误日志记录
    setup_error_logging(app)
    
    # 注册自定义异常处理器
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(AuthenticationError, handle_authentication_error)
    app.register_error_handler(AuthorizationError, handle_authorization_error)
    app.register_error_handler(ExecutionError, handle_execution_error)
    app.register_error_handler(ResourceNotFoundError, handle_resource_not_found)
    
    # 注册通用HTTP错误处理器
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(405, handle_method_not_allowed)
    app.register_error_handler(500, handle_internal_server_error)
    
    # 添加中间件
    app.before_request(setup_request_context)
    app.after_request(request_logging_middleware)
    
    return app