#!/usr/bin/env python3
"""
FastAPI权限系统
基于RBAC的FastAPI权限依赖和装饰器
"""

from typing import List, Optional, Callable
from fastapi import Depends, HTTPException, Request, status
from functools import wraps

from ..schemas.auth import (
    Permission, UserRole, User, TokenPayload,
    check_permission, check_any_permission, check_all_permissions
)
from .permission_manager import permission_manager
from .rbac import rbac_manager  # 保持向后兼容

# 尝试导入错误模型，如果失败则使用简单版本
try:
    from ..schemas.error import APIError, ErrorCode, ErrorSeverity
    # 如果导入成功，使用标准的严重性枚举
    DEFAULT_SEVERITY = ErrorSeverity.MEDIUM
except ImportError:
    # 简单回退实现
    from enum import Enum

    class ErrorCode(str, Enum):
        UNAUTHORIZED = "unauthorized"
        FORBIDDEN = "forbidden"
        # 向后兼容的别名
        AUTHENTICATION_ERROR = "unauthorized"
        PERMISSION_DENIED = "forbidden"

    class ErrorSeverity(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    DEFAULT_SEVERITY = ErrorSeverity.MEDIUM

    class APIError(BaseModel):
        code: str
        message: str
        severity: str = DEFAULT_SEVERITY

        def model_dump(self):
            return {"code": self.code, "message": self.message, "severity": self.severity}

        def dict(self):
            return self.model_dump()


async def permission_dependency(
    permission: Permission,
    request: Request
) -> bool:
    """权限依赖函数"""
    # 从请求中获取当前用户
    current_user = request.state.user if hasattr(request.state, 'user') else None

    if not current_user:
        # 尝试通过令牌获取用户
        current_user = await get_current_user(request)

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=APIError(
                code=ErrorCode.UNAUTHORIZED,
                message="未认证",
                severity=DEFAULT_SEVERITY
            ).model_dump()
        )

    username = current_user.get('username')

    # 检查权限
    if not rbac_manager.has_permission(username, permission):
        # 记录审计日志（如果审计系统可用）
        try:
            from ..audit.manager import get_audit_manager
            from ..schemas.audit import (
                AuditActor, AuditResource, AuditEventType,
                AuditEventSeverity, AuditEventStatus, create_audit_event
            )

            actor = AuditActor(
                user_id=str(current_user.get('user_id')),
                username=username,
                role=current_user.get('role'),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )

            resource = AuditResource(
                resource_type="api_endpoint",
                resource_name=request.url.path,
                resource_path=request.url.path,
                resource_metadata={
                    "method": request.method,
                    "endpoint": request.url.path
                }
            )

            event = create_audit_event(
                event_type=AuditEventType.ACCESS_DENIED,
                actor=actor,
                action=f"权限拒绝: {permission.value}",
                description=f"用户 {username} 尝试访问 {request.method} {request.url.path} 但权限不足",
                resource=resource,
                severity=AuditEventSeverity.WARNING,
                status=AuditEventStatus.FAILURE,
                details={
                    "required_permission": permission.value,
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": current_user.get('user_id'),
                    "user_role": current_user.get('role')
                },
                module="auth",
                is_sensitive=True
            )

            audit_manager = get_audit_manager()
            audit_manager.log_event(event)

        except ImportError:
            # 审计系统不可用，跳过审计日志
            pass

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=APIError(
                code=ErrorCode.FORBIDDEN,
                message=f"权限不足: 需要 {permission.value} 权限",
                severity=DEFAULT_SEVERITY
            ).model_dump()
        )

    return True


async def any_permission_dependency(
    permissions: List[Permission],
    request: Request
) -> bool:
    """任意权限依赖函数"""
    current_user = request.state.user if hasattr(request.state, 'user') else None

    if not current_user:
        # 尝试通过令牌获取用户
        current_user = await get_current_user(request)

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=APIError(
                code=ErrorCode.UNAUTHORIZED,
                message="未认证",
                severity=DEFAULT_SEVERITY
            ).model_dump()
        )

    username = current_user.get('username')

    # 检查权限
    if not rbac_manager.has_any_permission(username, permissions):
        permission_values = [p.value for p in permissions]

        # 记录审计日志
        try:
            from ..audit.manager import get_audit_manager
            from ..schemas.audit import (
                AuditActor, AuditResource, AuditEventType,
                AuditEventSeverity, AuditEventStatus, create_audit_event
            )

            actor = AuditActor(
                user_id=str(current_user.get('user_id')),
                username=username,
                role=current_user.get('role'),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )

            resource = AuditResource(
                resource_type="api_endpoint",
                resource_name=request.url.path,
                resource_path=request.url.path
            )

            event = create_audit_event(
                event_type=AuditEventType.ACCESS_DENIED,
                actor=actor,
                action=f"权限拒绝: 需要任一权限 {permission_values}",
                description=f"用户 {username} 尝试访问 {request.method} {request.url.path} 但权限不足",
                resource=resource,
                severity=AuditEventSeverity.WARNING,
                status=AuditEventStatus.FAILURE,
                details={
                    "required_permissions": permission_values,
                    "method": request.method,
                    "path": request.url.path
                },
                module="auth",
                is_sensitive=True
            )

            audit_manager = get_audit_manager()
            audit_manager.log_event(event)

        except ImportError:
            pass

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=APIError(
                code=ErrorCode.FORBIDDEN,
                message=f"权限不足: 需要以下任一权限 {permission_values}",
                severity=DEFAULT_SEVERITY
            ).model_dump()
        )

    return True


async def all_permissions_dependency(
    permissions: List[Permission],
    request: Request
) -> bool:
    """所有权限依赖函数"""
    current_user = request.state.user if hasattr(request.state, 'user') else None

    if not current_user:
        # 尝试通过令牌获取用户
        current_user = await get_current_user(request)

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=APIError(
                code=ErrorCode.UNAUTHORIZED,
                message="未认证",
                severity=DEFAULT_SEVERITY
            ).model_dump()
        )

    username = current_user.get('username')

    # 检查权限
    if not rbac_manager.has_all_permissions(username, permissions):
        permission_values = [p.value for p in permissions]

        # 记录审计日志
        try:
            from ..audit.manager import get_audit_manager
            from ..schemas.audit import (
                AuditActor, AuditResource, AuditEventType,
                AuditEventSeverity, AuditEventStatus, create_audit_event
            )

            actor = AuditActor(
                user_id=str(current_user.get('user_id')),
                username=username,
                role=current_user.get('role'),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent')
            )

            resource = AuditResource(
                resource_type="api_endpoint",
                resource_name=request.url.path,
                resource_path=request.url.path
            )

            event = create_audit_event(
                event_type=AuditEventType.ACCESS_DENIED,
                actor=actor,
                action=f"权限拒绝: 需要所有权限 {permission_values}",
                description=f"用户 {username} 尝试访问 {request.method} {request.url.path} 但权限不足",
                resource=resource,
                severity=AuditEventSeverity.WARNING,
                status=AuditEventStatus.FAILURE,
                details={
                    "required_permissions": permission_values,
                    "method": request.method,
                    "path": request.url.path
                },
                module="auth",
                is_sensitive=True
            )

            audit_manager = get_audit_manager()
            audit_manager.log_event(event)

        except ImportError:
            pass

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=APIError(
                code=ErrorCode.FORBIDDEN,
                message=f"权限不足: 需要以下所有权限 {permission_values}",
                severity=DEFAULT_SEVERITY
            ).model_dump()
        )

    return True


# 快捷函数
def require_permission(permission: Permission):
    """权限检查装饰器（FastAPI依赖）"""
    async def permission_checker(request: Request):
        return await permission_dependency(permission, request)
    return permission_checker


def require_any_permission(permissions: List[Permission]):
    """检查任一权限装饰器（FastAPI依赖）"""
    async def any_permission_checker(request: Request):
        return await any_permission_dependency(permissions, request)
    return any_permission_checker


def require_all_permissions(permissions: List[Permission]):
    """检查所有权限装饰器（FastAPI依赖）"""
    async def all_permissions_checker(request: Request):
        return await all_permissions_dependency(permissions, request)
    return all_permissions_checker


# FastAPI RBAC API路由依赖
def setup_fastapi_rbac_routes():
    """设置FastAPI RBAC管理路由（待实现）"""
    # 注意：现有RBAC路由是基于Flask的
    # 如果需要，可以在这里添加FastAPI版本的路由
    pass


# 用户认证依赖
async def get_current_user(request: Request):
    """获取当前用户依赖"""
    # 首先检查是否已经在request.state中设置了用户
    user = getattr(request.state, 'user', None)

    if user:
        return user

    # 尝试从Authorization头中提取JWT令牌
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    if token:
        try:
            # 检查 token 黑名单（已登出的 token）
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            try:
                from ..api.v1.auth_fastapi import _token_blacklist
                if token_hash in _token_blacklist:
                    return None
            except ImportError:
                pass

            # 尝试使用auth_manager验证令牌
            from .authentication import auth_manager
            payload = auth_manager.verify_token(token)

            # 提取用户信息（sub = username，user_id 单独字段）
            username = payload.get("sub") or payload.get("username", "")
            raw_uid = payload.get("user_id") or payload.get("sub", "0")
            try:
                user_id = int(raw_uid)
            except (ValueError, TypeError):
                user_id = 0
            role = payload.get("role", "user")

            # 从数据库获取完整用户信息（如果需要）
            # 暂时使用payload中的信息
            user = {
                "user_id": user_id,
                "username": username,
                "role": role,
                "permissions": payload.get("permissions", [])
            }

            # 存储到request.state
            request.state.user = user
            return user

        except Exception as e:
            # 令牌验证失败，返回None（将导致401错误）
            pass

    # 如果没有令牌或验证失败，返回None
    # 注意：这会导致require_authentication抛出401错误
    return None


async def require_authentication(request: Request):
    """认证检查依赖"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=APIError(
                code=ErrorCode.UNAUTHORIZED,
                message="未认证",
                severity=DEFAULT_SEVERITY
            ).dict()
        )
    return user


# 角色检查快捷函数
def require_role(role_name: str):
    """角色检查依赖"""
    async def role_checker(request: Request):
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证"
            )

        if user.get('role') != role_name:
            # 检查用户是否被分配了这个角色
            user_roles = rbac_manager.get_user_roles(user.get('username'))
            if role_name not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=APIError(
                        code=ErrorCode.FORBIDDEN,
                        message=f"需要角色: {role_name}",
                        severity=DEFAULT_SEVERITY
                    ).dict()
                )

        return True

    return Depends(role_checker)


def require_any_role(role_names: List[str]):
    """任意角色检查依赖"""
    async def role_checker(request: Request):
        user = await get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证"
            )

        user_role = user.get('role')
        user_roles = rbac_manager.get_user_roles(user.get('username'))

        has_role = (user_role in role_names) or any(role in user_roles for role in role_names)

        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.FORBIDDEN,
                    message=f"需要以下任一角色: {', '.join(role_names)}",
                    severity=DEFAULT_SEVERITY
                ).dict()
            )

        return True

    return Depends(role_checker)


# 测试函数
def test_fastapi_permissions():
    """测试FastAPI权限系统"""
    print("测试FastAPI权限系统...")

    # 测试权限枚举
    print(f"权限数量: {len(list(Permission))}")

    # 测试RBAC管理器
    print(f"预定义角色数量: {len(rbac_manager.roles)}")

    # 测试用户权限
    test_user = "demo"
    permissions = rbac_manager.get_user_permissions(test_user)
    print(f"用户 '{test_user}' 的权限: {[p.value for p in permissions]}")

    # 测试权限检查
    has_tool_execute = rbac_manager.has_permission(test_user, Permission.TOOL_EXECUTE)
    print(f"用户 '{test_user}' 有 TOOL_EXECUTE 权限: {has_tool_execute}")

    print("FastAPI权限系统测试完成!")


if __name__ == "__main__":
    test_fastapi_permissions()