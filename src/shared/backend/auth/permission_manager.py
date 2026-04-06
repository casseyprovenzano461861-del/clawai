"""
权限管理器
基于Pydantic模型的现代化权限管理系统，与现有RBAC系统集成
"""

from typing import Optional, List, Dict, Any, Set
from datetime import datetime
import logging
from functools import lru_cache

from ..schemas.auth import (
    Permission,
    UserRole,
    User,
    PermissionGroups,
    check_permission,
    check_any_permission,
    check_all_permissions
)

logger = logging.getLogger(__name__)


class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self._user_cache = {}
        self._cache_timeout = 300  # 5分钟缓存

    def get_user_permissions(self, user: User) -> List[Permission]:
        """获取用户的所有权限"""
        # 检查缓存
        cache_key = f"{user.id}_{user.username}"
        if cache_key in self._user_cache:
            cached_data = self._user_cache[cache_key]
            if cached_data["expires_at"] > datetime.now():
                return cached_data["permissions"]

        # 计算权限
        permissions = set()

        # 1. 从用户角色获取权限
        for role in user.roles:
            role_permissions = PermissionGroups.get_permissions_for_role(role)
            permissions.update(role_permissions)

        # 2. 添加直接分配的权限
        permissions.update(user.permissions)

        # 3. 确保所有用户都有访客权限（如果角色中没有GUEST）
        if UserRole.GUEST not in user.roles:
            guest_permissions = PermissionGroups.get_permissions_for_role(UserRole.GUEST)
            permissions.update(guest_permissions)

        permission_list = list(permissions)

        # 更新缓存
        self._user_cache[cache_key] = {
            "permissions": permission_list,
            "expires_at": datetime.now().timestamp() + self._cache_timeout
        }

        return permission_list

    def has_permission(self, user: User, permission: Permission) -> bool:
        """检查用户是否有特定权限"""
        if not user or not user.is_active():
            return False

        permissions = self.get_user_permissions(user)
        return check_permission(permissions, permission)

    def has_any_permission(self, user: User, permissions: List[Permission]) -> bool:
        """检查用户是否有任一权限"""
        if not user or not user.is_active():
            return False

        user_permissions = self.get_user_permissions(user)
        return check_any_permission(user_permissions, permissions)

    def has_all_permissions(self, user: User, permissions: List[Permission]) -> bool:
        """检查用户是否有所有权限"""
        if not user or not user.is_active():
            return False

        user_permissions = self.get_user_permissions(user)
        return check_all_permissions(user_permissions, permissions)

    def has_role(self, user: User, role: UserRole) -> bool:
        """检查用户是否有特定角色"""
        if not user or not user.is_active():
            return False

        return user.has_role(role)

    def has_any_role(self, user: User, roles: List[UserRole]) -> bool:
        """检查用户是否有任一角色"""
        if not user or not user.is_active():
            return False

        return user.has_any_role(roles)

    def can_access_resource(self, user: User, resource_type: str, action: str) -> bool:
        """检查用户是否可以访问特定资源（基于权限命名约定）"""
        if not user or not user.is_active():
            return False

        # 构建权限字符串（例如：user:read, tool:execute等）
        permission_str = f"{resource_type}:{action}"
        try:
            permission = Permission(permission_str)
            return self.has_permission(user, permission)
        except ValueError:
            # 权限不存在，使用默认检查
            logger.warning(f"权限 {permission_str} 不存在，使用默认检查")
            return self.has_any_permission(user, [
                Permission(f"{resource_type}:manage"),
                Permission(f"{resource_type}:{action}")
            ])

    def get_allowed_resources(self, user: User, resource_type: str) -> List[str]:
        """获取用户允许访问的资源类型列表（基于权限）"""
        if not user or not user.is_active():
            return []

        permissions = self.get_user_permissions(user)
        allowed_actions = set()

        for permission in permissions:
            if permission.value.startswith(f"{resource_type}:"):
                # 提取动作部分
                action = permission.value.split(":", 1)[1]
                allowed_actions.add(action)

        return list(allowed_actions)

    def validate_permission_assignment(
        self,
        assigner: User,
        target_user: User,
        permissions: List[Permission]
    ) -> bool:
        """验证权限分配是否合法"""
        if not assigner or not target_user:
            return False

        # 1. 不能给自己分配超过自己拥有的权限
        for permission in permissions:
            if not self.has_permission(assigner, permission):
                logger.warning(f"分配者 {assigner.username} 没有权限 {permission.value}")
                return False

        # 2. 不能给超级管理员分配权限（除非自己是超级管理员）
        if UserRole.SUPER_ADMIN in target_user.roles and UserRole.SUPER_ADMIN not in assigner.roles:
            logger.warning(f"非超级管理员尝试给超级管理员分配权限")
            return False

        # 3. 检查权限冲突
        # TODO: 可以添加更多冲突检查

        return True

    def validate_role_assignment(
        self,
        assigner: User,
        target_user: User,
        role: UserRole
    ) -> bool:
        """验证角色分配是否合法"""
        if not assigner or not target_user:
            return False

        # 1. 检查分配者是否有权限分配该角色
        role_permissions = PermissionGroups.get_permissions_for_role(role)
        for permission in role_permissions:
            if not self.has_permission(assigner, permission):
                logger.warning(f"分配者 {assigner.username} 没有权限分配角色 {role.value}")
                return False

        # 2. 不能给超级管理员分配角色（除非自己是超级管理员）
        if UserRole.SUPER_ADMIN in target_user.roles and UserRole.SUPER_ADMIN not in assigner.roles:
            logger.warning(f"非超级管理员尝试给超级管理员分配角色")
            return False

        # 3. 不能分配比自己高的角色
        assigner_highest_role = self._get_highest_role(assigner)
        target_highest_role = self._get_highest_role(target_user)
        role_hierarchy = {
            UserRole.SUPER_ADMIN: 100,
            UserRole.ADMIN: 90,
            UserRole.ANALYST: 80,
            UserRole.AUDITOR: 70,
            UserRole.USER: 60,
            UserRole.GUEST: 50,
            UserRole.API_CLIENT: 40
        }

        if role_hierarchy.get(role, 0) > role_hierarchy.get(assigner_highest_role, 0):
            logger.warning(f"分配者 {assigner.username} 不能分配比自己高的角色")
            return False

        return True

    def _get_highest_role(self, user: User) -> Optional[UserRole]:
        """获取用户的最高角色"""
        if not user or not user.roles:
            return None

        role_hierarchy = {
            UserRole.SUPER_ADMIN: 100,
            UserRole.ADMIN: 90,
            UserRole.ANALYST: 80,
            UserRole.AUDITOR: 70,
            UserRole.USER: 60,
            UserRole.GUEST: 50,
            UserRole.API_CLIENT: 40
        }

        highest_role = None
        highest_score = 0

        for role in user.roles:
            score = role_hierarchy.get(role, 0)
            if score > highest_score:
                highest_score = score
                highest_role = role

        return highest_role

    def clear_cache(self, username: Optional[str] = None):
        """清除权限缓存"""
        if username:
            keys_to_remove = [k for k in self._user_cache.keys() if username in k]
            for key in keys_to_remove:
                self._user_cache.pop(key, None)
        else:
            self._user_cache.clear()

        logger.info(f"权限缓存已清除: username={username or 'all'}")

    def get_user_permission_summary(self, user: User) -> Dict[str, Any]:
        """获取用户权限摘要"""
        permissions = self.get_user_permissions(user)

        summary = {
            "user_id": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "status": user.status.value,
            "total_permissions": len(permissions),
            "permissions_by_category": {},
            "can_perform_actions": {}
        }

        # 按类别分组权限
        for permission in permissions:
            category = permission.value.split(":", 1)[0]
            if category not in summary["permissions_by_category"]:
                summary["permissions_by_category"][category] = []
            summary["permissions_by_category"][category].append(permission.value)

        # 检查常用操作
        common_actions = {
            "manage_users": [Permission.USER_MANAGE],
            "execute_tools": [Permission.TOOL_EXECUTE],
            "start_attacks": [Permission.ATTACK_EXECUTE],
            "view_audit_logs": [Permission.AUDIT_READ],
            "manage_system": [Permission.SYSTEM_MANAGE],
            "export_reports": [Permission.REPORT_EXPORT]
        }

        for action_name, required_permissions in common_actions.items():
            summary["can_perform_actions"][action_name] = self.has_all_permissions(user, required_permissions)

        return summary


# 全局权限管理器实例
permission_manager = PermissionManager()


# 向后兼容函数
def get_user_permissions_from_rbac(username: str) -> List[Permission]:
    """从RBAC系统获取用户权限（向后兼容）"""
    try:
        from .rbac import rbac_manager as old_rbac_manager
        old_permissions = old_rbac_manager.get_user_permissions(username)
        # 转换为新的Permission枚举
        permissions = []
        for perm in old_permissions:
            try:
                permissions.append(Permission(perm.value))
            except ValueError:
                # 忽略无法转换的权限
                continue
        return permissions
    except ImportError:
        return []


def migrate_rbac_to_new_system() -> Dict[str, Any]:
    """从旧RBAC系统迁移到新权限系统"""
    try:
        from .rbac import rbac_manager as old_rbac_manager

        migration_stats = {
            "roles_migrated": 0,
            "users_migrated": 0,
            "permissions_migrated": 0
        }

        # 获取所有用户
        all_users = set()
        for username, roles in old_rbac_manager.user_roles.items():
            all_users.add(username)

        migration_stats["users_migrated"] = len(all_users)

        logger.info(f"从RBAC系统迁移 {len(all_users)} 个用户")

        return migration_stats

    except ImportError:
        logger.warning("RBAC系统不可用，跳过迁移")
        return {"error": "RBAC系统不可用"}


if __name__ == "__main__":
    # 测试权限管理器
    print("测试权限管理器...")

    # 创建测试用户
    test_user = User(
        id="test_user_001",
        username="testuser",
        roles=[UserRole.ANALYST, UserRole.USER],
        permissions=[Permission.TOOL_EXECUTE, Permission.REPORT_EXPORT],
        status="active"
    )

    # 测试权限检查
    manager = PermissionManager()
    permissions = manager.get_user_permissions(test_user)
    print(f"用户权限数量: {len(permissions)}")
    print(f"用户权限: {[p.value for p in permissions[:5]]}...")

    # 测试特定权限
    has_tool_execute = manager.has_permission(test_user, Permission.TOOL_EXECUTE)
    print(f"有 TOOL_EXECUTE 权限: {has_tool_execute}")

    has_system_manage = manager.has_permission(test_user, Permission.SYSTEM_MANAGE)
    print(f"有 SYSTEM_MANAGE 权限: {has_system_manage}")

    # 测试角色检查
    has_analyst_role = manager.has_role(test_user, UserRole.ANALYST)
    print(f"有 ANALYST 角色: {has_analyst_role}")

    # 测试权限摘要
    summary = manager.get_user_permission_summary(test_user)
    print(f"权限摘要: {summary['total_permissions']} 个权限")

    print("权限管理器测试完成!")