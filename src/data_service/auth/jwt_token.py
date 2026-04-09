"""
JWT令牌工具
用于生成、验证和刷新JWT令牌
"""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
import jwt as pyjwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET", "clawai-jwt-secret-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 令牌类型
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class TokenPayload:
    """JWT令牌载荷"""

    def __init__(
        self,
        sub: str,  # 用户标识
        user_id: int,
        username: str,
        role: str = "user",
        token_type: str = TOKEN_TYPE_ACCESS,
        exp: Optional[float] = None,
        iat: Optional[float] = None,
        **extra
    ):
        self.sub = sub
        self.user_id = user_id
        self.username = username
        self.role = role
        self.token_type = token_type
        self.exp = exp or (time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        self.iat = iat or time.time()
        self.extra = extra

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        payload = {
            "sub": self.sub,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "token_type": self.token_type,
            "exp": self.exp,
            "iat": self.iat,
            **self.extra
        }
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """从字典创建"""
        return cls(
            sub=data.get("sub"),
            user_id=data.get("user_id"),
            username=data.get("username"),
            role=data.get("role", "user"),
            token_type=data.get("token_type", TOKEN_TYPE_ACCESS),
            exp=data.get("exp"),
            iat=data.get("iat"),
            **{k: v for k, v in data.items() if k not in ["sub", "user_id", "username", "role", "token_type", "exp", "iat"]}
        )


def create_access_token(
    user_id: int,
    username: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
    extra_data: Dict[str, Any] = None
) -> str:
    """
    创建访问令牌

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        expires_delta: 过期时间增量
        extra_data: 额外数据

    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = TokenPayload(
        sub=f"user:{user_id}",
        user_id=user_id,
        username=username,
        role=role,
        token_type=TOKEN_TYPE_ACCESS,
        exp=expire.timestamp(),
        **(extra_data or {})
    )

    encoded_jwt = pyjwt.encode(payload.to_dict(), SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    user_id: int,
    username: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None,
    extra_data: Dict[str, Any] = None
) -> str:
    """
    创建刷新令牌

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        expires_delta: 过期时间增量
        extra_data: 额外数据

    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = TokenPayload(
        sub=f"user:{user_id}",
        user_id=user_id,
        username=username,
        role=role,
        token_type=TOKEN_TYPE_REFRESH,
        exp=expire.timestamp(),
        **(extra_data or {})
    )

    encoded_jwt = pyjwt.encode(payload.to_dict(), SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = TOKEN_TYPE_ACCESS) -> Optional[TokenPayload]:
    """
    验证JWT令牌

    Args:
        token: JWT令牌字符串
        token_type: 令牌类型 (access/refresh)

    Returns:
        令牌载荷或None
    """
    try:
        payload_dict = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        payload = TokenPayload.from_dict(payload_dict)

        # 检查令牌类型
        if payload.token_type != token_type:
            logger.warning(f"令牌类型不匹配: 期望 {token_type}, 实际 {payload.token_type}")
            return None

        # 检查过期时间
        if payload.exp < time.time():
            logger.warning("令牌已过期")
            return None

        return payload

    except ExpiredSignatureError:
        logger.error("JWT验证失败: 令牌已过期")
        return None
    except InvalidTokenError as e:
        logger.error(f"JWT验证失败: {e}")
        return None
    except Exception as e:
        logger.error(f"令牌验证异常: {e}")
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT令牌（不验证签名和过期时间）

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的载荷或None
    """
    try:
        # 注意：这里不验证签名，仅用于调试或特定场景
        # 生产环境应始终使用verify_token
        payload_dict = pyjwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload_dict
    except InvalidTokenError as e:
        logger.error(f"JWT解码失败: {e}")
        return None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    使用刷新令牌获取新的访问令牌

    Args:
        refresh_token: 刷新令牌

    Returns:
        新的访问令牌或None
    """
    payload = verify_token(refresh_token, TOKEN_TYPE_REFRESH)
    if not payload:
        return None

    # 创建新的访问令牌
    new_access_token = create_access_token(
        user_id=payload.user_id,
        username=payload.username,
        role=payload.role,
        extra_data=payload.extra
    )

    return new_access_token


def create_token_pair(
    user_id: int,
    username: str,
    role: str = "user",
    extra_data: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    创建访问令牌和刷新令牌对

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        extra_data: 额外数据

    Returns:
        包含access_token和refresh_token的字典
    """
    access_token = create_access_token(user_id, username, role, extra_data=extra_data)
    refresh_token = create_refresh_token(user_id, username, role, extra_data=extra_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 秒
    }


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    获取令牌过期时间

    Args:
        token: JWT令牌

    Returns:
        过期时间或None
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


def validate_token_strength(token: str) -> Tuple[bool, Optional[str]]:
    """
    验证令牌强度（检查是否使用弱密钥等）

    Args:
        token: JWT令牌

    Returns:
        (是否安全, 错误消息)
    """
    # 检查密钥强度
    if len(SECRET_KEY) < 32:
        return False, "JWT密钥太短，建议至少32个字符"

    # 检查算法
    if ALGORITHM not in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]:
        return False, f"不支持的JWT算法: {ALGORITHM}"

    # 检查令牌长度（基本验证）
    if len(token) < 50:
        return False, "令牌长度异常，可能无效"

    return True, None