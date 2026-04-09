# -*- coding: utf-8 -*-
"""
认证 API 路由 (FastAPI)
提供登录、登出、令牌刷新、当前用户信息、注册等端点
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

from backend.auth.authentication import auth_manager
from backend.auth.fastapi_permissions import get_current_user, require_authentication
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["认证管理"])

_bearer = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# 请求 / 响应模型
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")

    @validator("username")
    def _strip_username(cls, v: str) -> str:
        return v.strip()


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    email: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)

    @validator("username")
    def _username_chars(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v.strip()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class UserInfoResponse(BaseModel):
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    roles: list
    last_login: Optional[str]


# ---------------------------------------------------------------------------
# 端点
# ---------------------------------------------------------------------------


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(body: LoginRequest, request: Request, db=Depends(get_db)):
    """用户名 + 密码登录，返回 access_token 和 refresh_token。"""
    from backend.models.user import User as UserModel

    # 查询用户
    user: Optional[UserModel] = (
        db.query(UserModel).filter(UserModel.username == body.username).first()
    )

    if not user:
        logger.warning("登录失败：用户不存在 username=%s ip=%s",
                       body.username, request.client.host if request.client else "unknown")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "用户名或密码错误"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_disabled", "message": "账户已被禁用"},
        )

    if not user.check_password(body.password):
        logger.warning("登录失败：密码错误 username=%s ip=%s",
                       body.username, request.client.host if request.client else "unknown")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "用户名或密码错误"},
        )

    # 更新最后登录时间
    user.update_last_login()
    db.commit()

    payload = {
        "sub": user.username,
        "user_id": str(user.id) if user.id else "",
        "is_superuser": user.is_superuser,
        "role": user.role,
    }
    access_token = auth_manager.create_access_token(payload)
    refresh_token = auth_manager.create_refresh_token({"sub": user.username})

    logger.info("用户登录成功 username=%s", user.username)

    import os
    expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expire_minutes * 60,
    )


@router.post("/logout", summary="用户登出")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
):
    """登出（客户端丢弃令牌即可；服务端无状态，此端点返回成功确认）。"""
    return {"success": True, "message": "已登出"}


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(body: RefreshRequest):
    """用 refresh_token 换取新的 access_token。"""
    payload = auth_manager.verify_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "refresh_token 无效或已过期"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "令牌中缺少用户信息"},
        )

    new_access = auth_manager.create_access_token({"sub": username})
    new_refresh = auth_manager.create_refresh_token({"sub": username})

    import os
    expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=expire_minutes * 60,
    )


@router.get("/me", response_model=UserInfoResponse, summary="获取当前用户信息")
async def get_me(
    current_user: Dict[str, Any] = Depends(require_authentication),
    db=Depends(get_db),
):
    """返回当前已认证用户的基本信息。"""
    from backend.models.user import User as UserModel
    from backend.auth.rbac import rbac_manager

    username = current_user.get("username") or current_user.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "无法识别当前用户"},
        )

    user: Optional[UserModel] = (
        db.query(UserModel).filter(UserModel.username == username).first()
    )

    if not user:
        # 令牌有效但数据库中无此用户（已删除场景）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "user_not_found", "message": "用户不存在"},
        )

    roles = list(rbac_manager.get_user_roles(username))

    return UserInfoResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=roles,
        last_login=user.last_login_at.isoformat() if user.last_login_at else None,
    )


@router.post("/register", response_model=Dict[str, Any], summary="注册新用户",
             status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db=Depends(get_db)):
    """注册新用户账户。"""
    from backend.models.user import User as UserModel

    # 检查用户名是否已存在
    existing = db.query(UserModel).filter(UserModel.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "username_exists", "message": "用户名已被占用"},
        )

    # 检查邮箱唯一性
    if body.email:
        existing_email = db.query(UserModel).filter(UserModel.email == body.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "email_exists", "message": "邮箱已被注册"},
            )

    email = body.email or f"{body.username}@clawai.local"
    new_user = UserModel(
        username=body.username,
        email=email,
        password=body.password,
    )
    if body.full_name:
        new_user.full_name = body.full_name

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("新用户注册成功 username=%s ip=%s",
                body.username, request.client.host if request.client else "unknown")

    return {
        "success": True,
        "message": "注册成功",
        "username": new_user.username,
        "email": new_user.email,
    }


@router.get("/status", summary="检查认证状态")
async def auth_status(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
):
    """无需认证的端点，检查当前令牌是否有效。"""
    if not credentials:
        return {"authenticated": False, "message": "未提供令牌"}

    payload = auth_manager.verify_token(credentials.credentials)
    if not payload:
        return {"authenticated": False, "message": "令牌无效或已过期"}

    return {
        "authenticated": True,
        "username": payload.get("sub"),
        "expires_at": payload.get("exp"),
    }


__all__ = ["router"]
