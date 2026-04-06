"""
ClawAI 数据服务认证模块
提供用户认证、授权和JWT令牌管理
"""

from .password import (
    verify_password,
    get_password_hash,
    is_password_strong,
    generate_secure_password,
    needs_rehash
)

from .jwt_token import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
    refresh_access_token,
    create_token_pair,
    get_token_expiration,
    validate_token_strength,
    TokenPayload,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH
)

from .routes import (
    router as auth_router,
    get_current_user,
    get_current_active_user,
    require_admin,
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    ChangePasswordRequest
)

__all__ = [
    # 密码工具
    "verify_password",
    "get_password_hash",
    "is_password_strong",
    "generate_secure_password",
    "needs_rehash",

    # JWT工具
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    "refresh_access_token",
    "create_token_pair",
    "get_token_expiration",
    "validate_token_strength",
    "TokenPayload",
    "TOKEN_TYPE_ACCESS",
    "TOKEN_TYPE_REFRESH",

    # 路由和依赖
    "auth_router",
    "get_current_user",
    "get_current_active_user",
    "require_admin",

    # Pydantic模型
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "UserResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest"
]