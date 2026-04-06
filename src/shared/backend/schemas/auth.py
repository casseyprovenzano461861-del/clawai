"""
认证和授权数据模型
定义用户、角色、权限和令牌的Pydantic模型
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re

from .base import BaseSchema, IDMixin, TimestampMixin


class Permission(str, Enum):
    """系统权限枚举"""

    # 用户管理权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"

    # 工具管理权限
    TOOL_READ = "tool:read"
    TOOL_WRITE = "tool:write"
    TOOL_EXECUTE = "tool:execute"
    TOOL_MANAGE = "tool:manage"

    # 攻击管理权限
    ATTACK_READ = "attack:read"
    ATTACK_WRITE = "attack:write"
    ATTACK_EXECUTE = "attack:execute"
    ATTACK_MANAGE = "attack:manage"

    # 系统管理权限
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MANAGE = "system:manage"

    # 审计权限
    AUDIT_READ = "audit:read"
    AUDIT_WRITE = "audit:write"
    AUDIT_MANAGE = "audit:manage"

    # 报告权限
    REPORT_READ = "report:read"
    REPORT_WRITE = "report:write"
    REPORT_EXPORT = "report:export"
    REPORT_MANAGE = "report:manage"

    # 配置权限
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    CONFIG_MANAGE = "config:manage"

    # 安全权限
    SECURITY_READ = "security:read"
    SECURITY_WRITE = "security:write"
    SECURITY_MANAGE = "security:manage"


class UserRole(str, Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    USER = "user"
    GUEST = "guest"
    API_CLIENT = "api_client"


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING = "pending"


class User(BaseSchema, IDMixin, TimestampMixin):
    """用户模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    roles: List[UserRole] = Field(default_factory=list, description="用户角色")
    permissions: List[Permission] = Field(default_factory=list, description="用户权限列表")

    # 安全信息（不包含在API响应中）
    hashed_password: Optional[str] = Field(None, exclude=True, description="哈希密码")
    password_reset_token: Optional[str] = Field(None, exclude=True, description="密码重置令牌")
    password_reset_expires: Optional[datetime] = Field(None, exclude=True, description="密码重置过期时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_attempts: int = Field(default=0, description="登录尝试次数")

    @validator('username')
    def validate_username(cls, v):
        """验证用户名"""
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线、连字符和点')
        return v

    @validator('email')
    def validate_email(cls, v):
        """验证邮箱"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('邮箱格式无效')
        return v

    def has_role(self, role: UserRole) -> bool:
        """检查用户是否拥有特定角色"""
        return role in self.roles

    def has_any_role(self, roles: List[UserRole]) -> bool:
        """检查用户是否拥有任一角色"""
        return any(role in self.roles for role in roles)

    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否拥有特定权限"""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """检查用户是否拥有任一权限"""
        return any(permission in self.permissions for permission in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """检查用户是否拥有所有权限"""
        return all(permission in self.permissions for permission in permissions)

    def is_active(self) -> bool:
        """检查用户是否活跃"""
        return self.status == UserStatus.ACTIVE

    def is_suspended(self) -> bool:
        """检查用户是否被暂停"""
        return self.status == UserStatus.SUSPENDED

    def is_locked(self) -> bool:
        """检查用户是否被锁定"""
        return self.status == UserStatus.LOCKED


class UserCreate(BaseSchema):
    """用户创建模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    password: str = Field(..., min_length=8, description="密码")
    roles: List[UserRole] = Field(default=[UserRole.USER], description="用户角色")

    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码至少需要8个字符')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码至少需要一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码至少需要一个小写字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码至少需要一个数字')
        return v


class UserUpdate(BaseSchema):
    """用户更新模型"""
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    status: Optional[UserStatus] = Field(None, description="用户状态")
    roles: Optional[List[UserRole]] = Field(None, description="用户角色")


class UserLogin(BaseSchema):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserPasswordChange(BaseSchema):
    """用户密码修改模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., description="新密码")


class Role(BaseSchema, IDMixin, TimestampMixin):
    """角色模型"""
    name: str = Field(..., min_length=3, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: List[Permission] = Field(default_factory=list, description="角色权限")
    is_system: bool = Field(default=False, description="是否为系统角色")
    is_default: bool = Field(default=False, description="是否为默认角色")

    @validator('name')
    def validate_name(cls, v):
        """验证角色名称"""
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('角色名称只能包含字母、数字、下划线和连字符')
        return v


class RoleCreate(BaseSchema):
    """角色创建模型"""
    name: str = Field(..., min_length=3, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: List[Permission] = Field(default_factory=list, description="角色权限")
    is_default: bool = Field(default=False, description="是否为默认角色")


class RoleUpdate(BaseSchema):
    """角色更新模型"""
    description: Optional[str] = Field(None, description="角色描述")
    permissions: Optional[List[Permission]] = Field(None, description="角色权限")
    is_default: Optional[bool] = Field(None, description="是否为默认角色")


class PermissionCheck(BaseSchema):
    """权限检查模型"""
    permission: Permission = Field(..., description="要检查的权限")
    resource_id: Optional[str] = Field(None, description="资源ID")
    resource_type: Optional[str] = Field(None, description="资源类型")


class Token(BaseSchema):
    """令牌模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")


class TokenPayload(BaseSchema):
    """令牌载荷模型"""
    sub: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[UserRole] = Field(default_factory=list, description="用户角色")
    permissions: List[Permission] = Field(default_factory=list, description="用户权限")
    exp: datetime = Field(..., description="过期时间")
    iat: datetime = Field(..., description="签发时间")
    type: str = Field(default="access", description="令牌类型")


class APIKey(BaseSchema, IDMixin, TimestampMixin):
    """API密钥模型"""
    name: str = Field(..., min_length=3, max_length=100, description="密钥名称")
    key_id: str = Field(..., description="密钥ID")
    hashed_key: str = Field(..., exclude=True, description="哈希密钥")
    user_id: str = Field(..., description="用户ID")
    permissions: List[Permission] = Field(default_factory=list, description="密钥权限")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")
    is_active: bool = Field(default=True, description="是否激活")

    @validator('name')
    def validate_name(cls, v):
        """验证密钥名称"""
        if not re.match(r'^[a-zA-Z0-9_\- ]+$', v):
            raise ValueError('密钥名称只能包含字母、数字、下划线、连字符和空格')
        return v


class APIKeyCreate(BaseSchema):
    """API密钥创建模型"""
    name: str = Field(..., min_length=3, max_length=100, description="密钥名称")
    permissions: List[Permission] = Field(default_factory=list, description="密钥权限")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="有效期（天）")


class APIKeyResponse(BaseSchema):
    """API密钥响应模型"""
    id: str = Field(..., description="密钥ID")
    name: str = Field(..., description="密钥名称")
    key_id: str = Field(..., description="密钥ID")
    key: str = Field(..., description="密钥（仅在创建时返回）")
    user_id: str = Field(..., description="用户ID")
    permissions: List[Permission] = Field(default_factory=list, description="密钥权限")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    is_active: bool = Field(default=True, description="是否激活")


class LoginHistory(BaseSchema, IDMixin, TimestampMixin):
    """登录历史模型"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    success: bool = Field(..., description="是否成功")
    failure_reason: Optional[str] = Field(None, description="失败原因")


class AuthResponse(BaseSchema):
    """认证响应模型"""
    user: User = Field(..., description="用户信息")
    token: Token = Field(..., description="访问令牌")


# 权限组定义
class PermissionGroups:
    """权限组定义，用于批量分配权限"""

    # 系统管理权限组
    SYSTEM_ADMIN = [
        Permission.USER_MANAGE,
        Permission.TOOL_MANAGE,
        Permission.ATTACK_MANAGE,
        Permission.SYSTEM_MANAGE,
        Permission.AUDIT_MANAGE,
        Permission.REPORT_MANAGE,
        Permission.CONFIG_MANAGE,
        Permission.SECURITY_MANAGE
    ]

    # 安全分析师权限组
    SECURITY_ANALYST = [
        Permission.USER_READ,
        Permission.TOOL_READ,
        Permission.TOOL_EXECUTE,
        Permission.ATTACK_READ,
        Permission.ATTACK_WRITE,
        Permission.ATTACK_EXECUTE,
        Permission.REPORT_READ,
        Permission.REPORT_WRITE,
        Permission.REPORT_EXPORT,
        Permission.AUDIT_READ
    ]

    # 普通用户权限组
    REGULAR_USER = [
        Permission.TOOL_READ,
        Permission.TOOL_EXECUTE,
        Permission.ATTACK_READ,
        Permission.ATTACK_EXECUTE,
        Permission.REPORT_READ
    ]

    # 审计员权限组
    AUDITOR = [
        Permission.AUDIT_READ,
        Permission.AUDIT_WRITE,
        Permission.REPORT_READ,
        Permission.USER_READ,
        Permission.SYSTEM_READ
    ]

    # 访客权限组
    GUEST = [
        Permission.TOOL_READ,
        Permission.ATTACK_READ,
        Permission.REPORT_READ
    ]

    # 角色到权限组的映射
    ROLE_PERMISSIONS = {
        UserRole.SUPER_ADMIN: SYSTEM_ADMIN,
        UserRole.ADMIN: SYSTEM_ADMIN,
        UserRole.ANALYST: SECURITY_ANALYST,
        UserRole.AUDITOR: AUDITOR,
        UserRole.USER: REGULAR_USER,
        UserRole.GUEST: GUEST,
        UserRole.API_CLIENT: REGULAR_USER
    }

    @classmethod
    def get_permissions_for_role(cls, role: UserRole) -> List[Permission]:
        """获取角色的权限"""
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def get_permissions_for_roles(cls, roles: List[UserRole]) -> List[Permission]:
        """获取多个角色的权限"""
        permissions = set()
        for role in roles:
            permissions.update(cls.get_permissions_for_role(role))
        return list(permissions)


# 权限检查帮助函数
def check_permission(
    user_permissions: List[Permission],
    required_permission: Permission,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> bool:
    """检查用户是否有指定权限"""
    return required_permission in user_permissions


def check_any_permission(
    user_permissions: List[Permission],
    required_permissions: List[Permission],
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> bool:
    """检查用户是否有任一指定权限"""
    return any(p in user_permissions for p in required_permissions)


def check_all_permissions(
    user_permissions: List[Permission],
    required_permissions: List[Permission],
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> bool:
    """检查用户是否有所有指定权限"""
    return all(p in user_permissions for p in required_permissions)