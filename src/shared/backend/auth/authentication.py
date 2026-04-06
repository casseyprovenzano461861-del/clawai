"""
用户认证模块
借鉴RedAgent的认证系统设计
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models.user import User, APIKey

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# HTTP Bearer认证
security = HTTPBearer()


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
    
    def create_access_token(self, user_id: int, username: str, permissions: list) -> str:
        """创建访问令牌"""
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_id),
            "username": username,
            "permissions": permissions,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(self, user_id: int) -> str:
        """创建刷新令牌"""
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not user.check_password(password):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        # 更新最后登录时间
        user.update_last_login()
        db.commit()
        
        return user
    
    def authenticate_api_key(self, db: Session, api_key: str, api_secret: str) -> Optional[APIKey]:
        """API密钥认证"""
        key_record = db.query(APIKey).filter(
            APIKey.key == api_key,
            APIKey.is_active == True
        ).first()
        
        if not key_record:
            return None
        
        if not key_record.check_secret(api_secret):
            return None
        
        if key_record.is_expired():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API密钥已过期"
            )
        
        # 更新最后使用时间
        key_record.update_last_used()
        db.commit()
        
        return key_record
    
    def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """获取当前用户"""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token类型"
            )
        
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        # 更新最后活动时间
        user.update_activity()
        db.commit()
        
        return user
    
    def get_current_api_key(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> APIKey:
        """获取当前API密钥"""
        token = credentials.credentials
        
        # API密钥使用Basic认证格式: base64(key:secret)
        import base64
        try:
            decoded = base64.b64decode(token).decode("utf-8")
            api_key, api_secret = decoded.split(":", 1)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API密钥格式"
            )
        
        key_record = self.authenticate_api_key(db, api_key, api_secret)
        
        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API密钥"
            )
        
        return key_record


# 全局认证管理器实例
auth_manager = AuthManager()


def require_auth(user: User = Depends(auth_manager.get_current_user)):
    """要求用户认证"""
    return user


def require_api_key(api_key: APIKey = Depends(auth_manager.get_current_api_key)):
    """要求API密钥认证"""
    return api_key


def require_permission(permission: str):
    """要求特定权限"""
    def permission_dependency(user: User = Depends(require_auth)):
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission}"
            )
        return user
    return permission_dependency


def require_role(role: str):
    """要求特定角色"""
    def role_dependency(user: User = Depends(require_auth)):
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {role}"
            )
        return user
    return role_dependency


# 常用权限检查函数
def is_admin(user: User = Depends(require_auth)):
    """检查是否为管理员"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


def is_verified_user(user: User = Depends(require_auth)):
    """检查是否为已验证用户"""
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要已验证用户"
        )
    return user