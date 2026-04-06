"""
认证相关API路由
用户注册、登录、令牌管理等
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from .password import verify_password, get_password_hash, is_password_strong, generate_secure_password
from .jwt_token import create_token_pair, verify_token, refresh_access_token, TokenPayload

# 导入主应用中的数据库模型
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import User, get_db

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# Pydantic模型
class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名至少3个字符')
        if len(v) > 50:
            raise ValueError('用户名不能超过50个字符')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

    @validator('password')
    def validate_password(cls, v):
        strong, message = is_password_strong(v)
        if not strong:
            raise ValueError(message)
        return v

    @validator('confirm_password')
    def validate_passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user_id: int
    username: str
    role: str


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str
    new_password: str
    confirm_new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        strong, message = is_password_strong(v)
        if not strong:
            raise ValueError(message)
        return v

    @validator('confirm_new_password')
    def validate_passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v


# 依赖函数
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已禁用"
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已禁用")
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# API端点
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已注册"
            )

        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role="user",  # 默认角色
            is_active=True,
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"用户注册成功: {new_user.username} (ID: {new_user.id})")

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        # 查找用户
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 验证密码
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 检查用户是否激活
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已禁用"
            )

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()

        # 创建令牌对
        token_pair = create_token_pair(
            user_id=user.id,
            username=user.username,
            role=user.role,
            extra_data={"email": user.email}
        )

        logger.info(f"用户登录成功: {user.username}")

        return TokenResponse(
            **token_pair,
            user_id=user.id,
            username=user.username,
            role=user.role
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/refresh", response_model=Dict[str, str])
async def refresh_token(
    refresh_request: RefreshTokenRequest
):
    """刷新访问令牌"""
    try:
        new_access_token = refresh_access_token(refresh_request.refresh_token)
        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        # 验证当前密码
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="当前密码错误"
            )

        # 检查新密码是否与旧密码相同
        if verify_password(password_data.new_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码不能与旧密码相同"
            )

        # 更新密码
        new_hashed_password = get_password_hash(password_data.new_password)
        current_user.hashed_password = new_hashed_password
        db.commit()

        logger.info(f"用户密码修改成功: {current_user.username}")

        return {
            "message": "密码修改成功",
            "username": current_user.username
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"密码修改失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user)
):
    """用户登出（客户端应删除令牌）"""
    # JWT是无状态的，服务器端无需操作
    # 客户端应删除存储的令牌
    return {"message": "登出成功"}


@router.get("/validate")
async def validate_token(
    token: str = Depends(oauth2_scheme)
):
    """验证令牌有效性"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供令牌"
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效令牌"
        )

    return {
        "valid": True,
        "user_id": payload.user_id,
        "username": payload.username,
        "role": payload.role,
        "expires_at": datetime.fromtimestamp(payload.exp).isoformat()
    }


@router.post("/generate-password")
async def generate_password():
    """生成安全随机密码"""
    password = generate_secure_password()
    return {
        "password": password,
        "strength": "strong",
        "length": len(password)
    }


# 管理员端点
@router.get("/admin/users", dependencies=[Depends(require_admin)])
async def list_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取所有用户列表（仅管理员）"""
    try:
        users = db.query(User).offset(skip).limit(limit).all()

        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })

        return {
            "users": user_list,
            "count": len(user_list),
            "total": db.query(User).count()
        }

    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.put("/admin/users/{user_id}/status", dependencies=[Depends(require_admin)])
async def update_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """更新用户状态（仅管理员）"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        user.is_active = is_active
        db.commit()

        action = "启用" if is_active else "禁用"
        logger.info(f"用户状态更新: {user.username} -> {action}")

        return {
            "message": f"用户状态更新成功: {action}",
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败: {str(e)}"
        )