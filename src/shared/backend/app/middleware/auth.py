# -*- coding: utf-8 -*-
"""
认证中间件
处理JWT认证和用户上下文
"""

from typing import Optional, Dict, Any, Tuple
from functools import wraps

from flask import request, g, jsonify
import jwt

from backend.shared.exceptions import AuthenticationError, AuthorizationError


def authentication_middleware():
    """
    认证中间件
    
    在请求前执行，验证JWT令牌并设置用户上下文
    """
    # 跳过认证的路径
    skip_paths = ['/api/v1/auth/login', '/api/v1/auth/register', '/api/health', '/api/v1/health']
    
    if request.path in skip_paths:
        return
    
    # 检查认证头
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise AuthenticationError("缺少认证头", auth_type="bearer")
    
    # 验证Bearer令牌格式
    if not auth_header.startswith('Bearer '):
        raise AuthenticationError("认证头格式错误，应为'Bearer <token>'", auth_type="bearer")
    
    token = auth_header.split(' ')[1]
    
    try:
        # 验证JWT令牌
        # 这里需要从配置获取密钥和算法
        from config import config
        
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        
        # 设置用户上下文
        g.user = {
            'id': payload.get('sub'),
            'username': payload.get('username'),
            'role': payload.get('role', 'user'),
            'permissions': payload.get('permissions', [])
        }
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("令牌已过期", auth_type="bearer")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"无效令牌: {str(e)}", auth_type="bearer")
    except Exception as e:
        raise AuthenticationError(f"认证失败: {str(e)}", auth_type="bearer")


def require_auth(f):
    """
    需要认证的装饰器
    
    Args:
        f: 视图函数
        
    Returns:
        包装后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            authentication_middleware()
            return f(*args, **kwargs)
        except AuthenticationError as e:
            # 如果认证失败，返回401
            from backend.shared.exceptions import create_error_response
            error_dict, status_code = create_error_response(e)
            return jsonify(error_dict), status_code
    
    return decorated_function


def require_permission(permission: str):
    """
    需要特定权限的装饰器
    
    Args:
        permission: 需要的权限
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.get('user')
            if not user:
                raise AuthenticationError("用户未认证", auth_type="bearer")
            
            user_permissions = user.get('permissions', [])
            user_role = user.get('role', 'user')
            
            # 检查权限
            if permission not in user_permissions and user_role != 'admin':
                raise AuthorizationError(
                    f"缺少权限: {permission}",
                    required_permission=permission
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def require_role(role: str):
    """
    需要特定角色的装饰器
    
    Args:
        role: 需要的角色
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.get('user')
            if not user:
                raise AuthenticationError("用户未认证", auth_type="bearer")
            
            user_role = user.get('role', 'user')
            
            # 检查角色
            if user_role != role and user_role != 'admin':
                # 管理员可以访问所有角色
                raise AuthorizationError(
                    f"需要角色: {role}，当前角色: {user_role}",
                    required_permission=f"role:{role}"
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    获取当前用户信息
    
    Returns:
        当前用户信息，如果未认证则返回None
    """
    return g.get('user')


def get_current_user_id() -> Optional[str]:
    """
    获取当前用户ID
    
    Returns:
        当前用户ID，如果未认证则返回None
    """
    user = get_current_user()
    return user.get('id') if user else None


def get_current_username() -> Optional[str]:
    """
    获取当前用户名
    
    Returns:
        当前用户名，如果未认证则返回None
    """
    user = get_current_user()
    return user.get('username') if user else None


def get_current_role() -> Optional[str]:
    """
    获取当前用户角色
    
    Returns:
        当前用户角色，如果未认证则返回None
    """
    user = get_current_user()
    return user.get('role') if user else None


def has_permission(permission: str) -> bool:
    """
    检查当前用户是否有指定权限
    
    Args:
        permission: 权限名称
        
    Returns:
        是否有权限
    """
    user = get_current_user()
    if not user:
        return False
    
    user_permissions = user.get('permissions', [])
    user_role = user.get('role', 'user')
    
    # 管理员有所有权限
    if user_role == 'admin':
        return True
    
    return permission in user_permissions


def has_role(role: str) -> bool:
    """
    检查当前用户是否有指定角色
    
    Args:
        role: 角色名称
        
    Returns:
        是否有角色
    """
    user = get_current_user()
    if not user:
        return False
    
    user_role = user.get('role', 'user')
    
    # 管理员可以扮演所有角色
    if user_role == 'admin':
        return True
    
    return user_role == role


def setup_auth_routes(app):
    """
    设置认证路由中间件
    
    Args:
        app: Flask应用实例
        
    Returns:
        配置后的Flask应用实例
    """
    # 注册认证中间件
    @app.before_request
    def before_request():
        try:
            authentication_middleware()
        except AuthenticationError:
            # 允许认证错误通过，将由视图函数处理
            pass
    
    return app