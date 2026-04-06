"""\n用户模型\n借鉴RedAgent的用户系统设计\n"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import bcrypt
from typing import Optional, Dict, Any

from .base import BaseModel


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 个人信息
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # 设置和偏好
    preferences = Column(JSON, default=dict, nullable=False)
    
    # 关系
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, username: str, email: str, password: str, **kwargs):
        """初始化用户"""
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        self.set_password(password)
        
        # 设置默认偏好
        self.preferences = {
            "theme": "light",
            "language": "zh-CN",
            "notifications": {
                "email": True,
                "push": True
            }
        }
    
    def set_password(self, password: str):
        """设置密码"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_at = datetime.utcnow()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 移除敏感信息
        if not include_sensitive:
            data.pop('password_hash', None)
            data.pop('is_superuser', None)
        
        # 添加计算字段
        data['is_online'] = self._is_online()
        
        return data
    
    def _is_online(self) -> bool:
        """判断用户是否在线"""
        if not self.last_activity_at:
            return False
        
        # 如果最后活动时间在5分钟内，认为在线
        delta = datetime.utcnow() - self.last_activity_at
        return delta.total_seconds() < 300  # 5分钟
    
    @property
    def role(self) -> str:
        """获取用户角色"""
        if self.is_superuser:
            return "admin"
        elif self.is_verified:
            return "verified_user"
        else:
            return "user"
    
    def has_permission(self, permission: str) -> bool:
        """检查用户权限"""
        # 借鉴RedAgent的权限系统
        permissions = {
            "admin": [
                "user:create", "user:read", "user:update", "user:delete",
                "project:create", "project:read", "project:update", "project:delete",
                "scan:create", "scan:read", "scan:update", "scan:delete",
                "report:create", "report:read", "report:update", "report:delete",
                "system:manage"
            ],
            "verified_user": [
                "user:read:self", "user:update:self",
                "project:create", "project:read:self", "project:update:self", "project:delete:self",
                "scan:create", "scan:read:self", "scan:update:self", "scan:delete:self",
                "report:create", "report:read:self", "report:update:self", "report:delete:self"
            ],
            "user": [
                "user:read:self", "user:update:self",
                "project:create", "project:read:self", "project:update:self",
                "scan:create", "scan:read:self",
                "report:read:self"
            ]
        }
        
        user_permissions = permissions.get(self.role, [])
        return permission in user_permissions


class APIKey(BaseModel):
    """API密钥模型"""
    __tablename__ = "api_keys"
    
    # 基本信息
    name = Column(String(100), nullable=False)
    key = Column(String(64), unique=True, index=True, nullable=False)
    secret_hash = Column(String(255), nullable=False)
    
    # 权限信息
    permissions = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # 使用统计
    usage_count = Column(Integer, default=0, nullable=False)
    rate_limit = Column(Integer, default=100, nullable=False)  # 每分钟请求数
    
    # 外键关系
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="api_keys")
    
    def __init__(self, name: str, user_id: int, **kwargs):
        """初始化API密钥"""
        super().__init__(**kwargs)
        self.name = name
        self.user_id = user_id
        self.key = self._generate_key()
        self.secret_hash = self._generate_secret_hash()
        
        # 默认权限
        self.permissions = [
            "project:read",
            "scan:create",
            "scan:read",
            "report:read"
        ]
    
    def _generate_key(self) -> str:
        """生成API密钥"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    def _generate_secret_hash(self) -> str:
        """生成密钥哈希"""
        import secrets
        import bcrypt
        
        secret = secrets.token_urlsafe(32)
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(secret.encode('utf-8'), salt).decode('utf-8')
    
    def check_secret(self, secret: str) -> bool:
        """验证密钥"""
        return bcrypt.checkpw(secret.encode('utf-8'), self.secret_hash.encode('utf-8'))
    
    def update_last_used(self):
        """更新最后使用时间"""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def has_permission(self, permission: str) -> bool:
        """检查API密钥权限"""
        return permission in self.permissions
    
    def to_dict(self, include_secret: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 移除敏感信息
        if not include_secret:
            data.pop('secret_hash', None)
        
        # 添加计算字段
        data['is_expired'] = self.is_expired()
        data['is_valid'] = self.is_active and not self.is_expired()
        
        return data