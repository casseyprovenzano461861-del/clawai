"""
认证管理器
提供 JWT 令牌生成、验证和密码哈希功能
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)

# HTTPBearer 实例（供 api.py 和 fastapi_permissions.py 使用）
security = HTTPBearer(auto_error=False)

# JWT 配置
_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET", "dev-jwt-secret-not-for-production")
_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthenticationManager:
    """认证管理器 - 提供 JWT 令牌操作和密码哈希"""

    def __init__(self):
        self._secret_key = _SECRET_KEY
        self._algorithm = _ALGORITHM
        self._access_expire_minutes = _ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_expire_days = _REFRESH_TOKEN_EXPIRE_DAYS

        # 延迟初始化密码上下文（避免 passlib 导入失败阻断启动）
        self._pwd_context = None

    def _get_pwd_context(self):
        if self._pwd_context is None:
            try:
                from passlib.context import CryptContext
                self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            except ImportError:
                logger.warning("passlib not available, password hashing disabled")
        return self._pwd_context

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """生成访问令牌"""
        try:
            from jose import jwt as jose_jwt
        except ImportError:
            logger.error("python-jose not installed, cannot create JWT tokens")
            return ""

        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=self._access_expire_minutes))
        to_encode.update({"exp": expire, "type": "access"})
        return jose_jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """生成刷新令牌"""
        try:
            from jose import jwt as jose_jwt
        except ImportError:
            return ""

        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self._refresh_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jose_jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌，返回 payload dict；失败返回空 dict"""
        if not token:
            return {}
        try:
            from jose import jwt as jose_jwt, JWTError
            payload = jose_jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return payload
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return {}

    def hash_password(self, password: str) -> str:
        """哈希密码"""
        ctx = self._get_pwd_context()
        if ctx:
            return ctx.hash(password)
        # passlib 不可用时拒绝密码操作，而非回退到不安全的哈希
        raise RuntimeError("passlib 未安装，无法安全哈希密码。请安装 passlib[bcrypt]")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        ctx = self._get_pwd_context()
        if ctx:
            try:
                return ctx.verify(plain_password, hashed_password)
            except Exception:
                return False
        # passlib 不可用时拒绝密码操作
        raise RuntimeError("passlib 未安装，无法安全验证密码。请安装 passlib[bcrypt]")


# 全局单例
auth_manager = AuthenticationManager()
