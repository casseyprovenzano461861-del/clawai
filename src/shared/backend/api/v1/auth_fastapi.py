# -*- coding: utf-8 -*-
"""
FastAPI认证API端点
基于现有AuthManager和schemas的完整认证系统
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from backend.auth.authentication import auth_manager, require_auth
from backend.auth.fastapi_permissions import get_current_user, require_authentication
from backend.auth.rbac import rbac_manager, Permission
from backend.schemas.auth import (
    User, UserCreate, UserLogin, Token, TokenPayload,
    UserRole, UserStatus, Permission as AuthPermission
)
from backend.schemas.base import BaseSchema
from backend.database import get_db
from backend.models.user import User as UserModel
from backend.schemas.error import APIError, ErrorCode
from pydantic import Field

# 创建路由器
router = APIRouter(prefix="/auth", tags=["认证管理"])

logger = logging.getLogger(__name__)

# OAuth2方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# 响应模型
class LoginResponse(Token):
    """登录响应"""
    user: User

class RegisterResponse(User):
    """注册响应"""
    message: str = "注册成功"

class MeResponse(User):
    """当前用户信息响应"""
    pass

class RefreshTokenRequest(BaseSchema):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")

class RefreshResponse(Token):
    """刷新令牌响应"""
    pass

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录

    使用用户名和密码进行认证，返回JWT访问令牌和刷新令牌。
    """
    try:
        # 使用AuthManager进行用户认证
        user = auth_manager.authenticate_user(db, login_data.username, login_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=APIError(
                    code=ErrorCode.AUTHENTICATION_ERROR,
                    message="用户名或密码错误",
                    severity="medium"
                ).model_dump()
            )

        # 获取用户权限（通过RBAC系统）
        permissions = rbac_manager.get_user_permissions(user.username)
        permissions_list = [p.value for p in permissions]

        # 创建访问令牌
        access_token = auth_manager.create_access_token(
            user_id=user.id,
            username=user.username,
            permissions=permissions_list
        )

        # 创建刷新令牌
        refresh_token = auth_manager.create_refresh_token(user.id)

        # 转换为响应模型
        user_response = User(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            status=UserStatus.ACTIVE if user.is_active else UserStatus.INACTIVE,
            roles=[UserRole(user.role)] if hasattr(user, 'role') else [UserRole.USER],
            permissions=[AuthPermission(p) for p in permissions_list],
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login_at
        )

        # 计算过期时间
        expires_in = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")) * 60

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            refresh_token=refresh_token,
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="登录失败，请稍后重试",
                severity="high"
            ).model_dump()
        )


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册

    创建新用户账户。默认角色为普通用户。
    """
    try:
        # 检查用户名是否已存在
        existing_user = db.query(UserModel).filter(UserModel.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="用户名已存在",
                    severity="medium"
                ).model_dump()
            )

        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = db.query(UserModel).filter(UserModel.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=APIError(
                        code=ErrorCode.VALIDATION_ERROR,
                        message="邮箱已存在",
                        severity="medium"
                    ).model_dump()
                )

        # 创建用户
        user = UserModel(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )

        # 设置默认角色（如果没有指定）
        if not user_data.roles:
            user.role = "user"

        db.add(user)
        db.commit()
        db.refresh(user)

        # 为新用户分配默认角色（通过RBAC）
        rbac_manager.assign_role_to_user(user.username, "user")

        # 转换为响应模型
        user_response = User(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            permissions=[],  # 新用户默认无特殊权限
            created_at=user.created_at,
            updated_at=user.updated_at
        )

        return RegisterResponse(**user_response.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="注册失败，请稍后重试",
                severity="high"
            ).model_dump()
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    使用刷新令牌获取新的访问令牌。
    """
    try:
        # 验证刷新令牌
        payload = auth_manager.verify_token(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=APIError(
                    code=ErrorCode.AUTHENTICATION_ERROR,
                    message="无效的刷新令牌",
                    severity="medium"
                ).model_dump()
            )

        user_id = int(payload["sub"])
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=APIError(
                    code=ErrorCode.AUTHENTICATION_ERROR,
                    message="用户不存在或已被禁用",
                    severity="medium"
                ).model_dump()
            )

        # 获取用户权限
        permissions = rbac_manager.get_user_permissions(user.username)
        permissions_list = [p.value for p in permissions]

        # 创建新的访问令牌
        access_token = auth_manager.create_access_token(
            user_id=user.id,
            username=user.username,
            permissions=permissions_list
        )

        # 创建新的刷新令牌（可选：刷新令牌可以重用或重新生成）
        new_refresh_token = auth_manager.create_refresh_token(user.id)

        expires_in = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")) * 60

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            refresh_token=new_refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="刷新令牌失败",
                severity="high"
            ).model_dump()
        )


@router.get("/me", response_model=MeResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息

    需要有效的访问令牌。
    """
    try:
        username = current_user.get('username')
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=APIError(
                    code=ErrorCode.AUTHENTICATION_ERROR,
                    message="未认证",
                    severity="medium"
                ).model_dump()
            )

        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message="用户不存在",
                    severity="medium"
                ).model_dump()
            )

        # 获取用户权限
        permissions = rbac_manager.get_user_permissions(username)
        permissions_list = [p.value for p in permissions]

        # 获取用户角色
        roles = rbac_manager.get_user_roles(username)
        roles_list = [UserRole(role) for role in roles if role in [r.value for r in UserRole]]

        return MeResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            status=UserStatus.ACTIVE if user.is_active else UserStatus.INACTIVE,
            roles=roles_list,
            permissions=[AuthPermission(p) for p in permissions_list],
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取用户信息失败",
                severity="high"
            ).model_dump()
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """
    用户登出

    使当前访问令牌失效（客户端应删除令牌）。
    注意：JWT是无状态的，此端点主要用于记录审计日志。
    """
    try:
        username = current_user.get('username')

        # 记录审计日志（如果审计系统可用）
        try:
            from ...audit.manager import get_audit_manager
            from ...schemas.audit import (
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
                resource_type="auth",
                resource_name="logout",
                resource_path="/api/v1/auth/logout"
            )

            event = create_audit_event(
                event_type=AuditEventType.USER_LOGOUT,
                actor=actor,
                action="用户登出",
                description=f"用户 {username} 登出系统",
                resource=resource,
                severity=AuditEventSeverity.INFO,
                status=AuditEventStatus.SUCCESS,
                details={}
            )

            audit_manager = get_audit_manager()
            audit_manager.log_event(event)

        except ImportError:
            # 审计系统不可用，仅记录日志
            logger.info(f"用户登出: {username}")

        return {
            "success": True,
            "message": "登出成功"
        }

    except Exception as e:
        logger.error(f"登出失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="登出失败",
                severity="high"
            ).model_dump()
        )


# 健康检查端点
@router.get("/health")
async def auth_health():
    """认证服务健康检查"""
    return {
        "status": "healthy",
        "service": "auth-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ──────────────────────────────────────────────
# 当前用户资料更新
# ──────────────────────────────────────────────
class UpdateMeRequest(BaseSchema):
    """更新当前用户信息请求"""
    full_name: Optional[str] = Field(None, description="全名")
    email: Optional[str] = Field(None, description="邮箱")
    current_password: Optional[str] = Field(None, description="当前密码（修改密码时必填）")
    new_password: Optional[str] = Field(None, description="新密码")


@router.put("/me", response_model=MeResponse)
async def update_current_user(
    request: Request,
    update_data: UpdateMeRequest,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        username = current_user.get('username')
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="用户不存在", severity="medium").model_dump()
            )

        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.new_password:
            if not update_data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="修改密码需要提供当前密码", severity="medium").model_dump()
                )
            if not auth_manager.verify_password(update_data.current_password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="当前密码错误", severity="medium").model_dump()
                )
            user.password = update_data.new_password

        db.commit()
        db.refresh(user)

        permissions = rbac_manager.get_user_permissions(username)
        roles = rbac_manager.get_user_roles(username)

        return MeResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            status=UserStatus.ACTIVE if user.is_active else UserStatus.INACTIVE,
            roles=[UserRole(r) for r in roles if r in [rv.value for rv in UserRole]],
            permissions=[AuthPermission(p.value) for p in permissions],
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="更新用户信息失败", severity="high").model_dump()
        )


# ──────────────────────────────────────────────
# 用户管理（管理员）
# ──────────────────────────────────────────────
class AdminUserCreate(BaseSchema):
    """管理员创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: str = Field(default="user")


class AdminUserUpdate(BaseSchema):
    """管理员更新用户请求"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


def _require_admin(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """验证管理员权限"""
    role = current_user.get("role", "")
    roles = rbac_manager.get_user_roles(current_user.get("username", ""))
    if role != "admin" and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=APIError(code=ErrorCode.FORBIDDEN, message="需要管理员权限", severity="high").model_dump()
        )
    return current_user


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """获取用户列表（管理员）"""
    _require_admin(current_user)
    try:
        total = db.query(UserModel).count()
        offset = (page - 1) * page_size
        users = db.query(UserModel).offset(offset).limit(page_size).all()

        user_list = []
        for u in users:
            roles = rbac_manager.get_user_roles(u.username)
            user_list.append({
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "roles": roles,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login_at.isoformat() if u.last_login_at else None
            })

        return {
            "users": user_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="获取用户列表失败", severity="high").model_dump()
        )


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """获取用户详情（管理员）"""
    _require_admin(current_user)
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="用户不存在", severity="low").model_dump()
        )
    roles = rbac_manager.get_user_roles(user.username)
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "roles": roles,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login_at.isoformat() if user.last_login_at else None
    }


@router.post("/users")
async def create_user(
    user_data: AdminUserCreate,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """创建用户（管理员）"""
    _require_admin(current_user)
    try:
        existing = db.query(UserModel).filter(UserModel.username == user_data.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="用户名已存在", severity="medium").model_dump()
            )

        user = UserModel(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        rbac_manager.assign_role_to_user(user.username, user_data.role)

        return {"success": True, "message": "用户创建成功", "id": str(user.id), "username": user.username}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="创建用户失败", severity="high").model_dump()
        )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: AdminUserUpdate,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """更新用户信息（管理员）"""
    _require_admin(current_user)
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="用户不存在", severity="low").model_dump()
        )
    try:
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
        if update_data.role is not None:
            user.role = update_data.role
            rbac_manager.assign_role_to_user(user.username, update_data.role)

        db.commit()
        return {"success": True, "message": "用户更新成功"}
    except Exception as e:
        logger.error(f"更新用户失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="更新用户失败", severity="high").model_dump()
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """删除用户（管理员）"""
    _require_admin(current_user)
    # 防止删除自己
    if str(user_id) == str(current_user.get("user_id")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIError(code=ErrorCode.VALIDATION_ERROR, message="不能删除当前登录用户", severity="medium").model_dump()
        )
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="用户不存在", severity="low").model_dump()
        )
    try:
        db.delete(user)
        db.commit()
        return {"success": True, "message": "用户删除成功"}
    except Exception as e:
        logger.error(f"删除用户失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(code=ErrorCode.UNKNOWN_ERROR, message="删除用户失败", severity="high").model_dump()
        )


# 导出路由器
__all__ = ["router"]