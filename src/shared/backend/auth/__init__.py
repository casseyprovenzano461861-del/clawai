"""
ClawAI 认证和授权模块
包含RBAC权限系统和FastAPI集成
"""

from .rbac import Permission, Role, RBACManager, rbac_manager

__all__ = [
    "Permission",
    "Role",
    "RBACManager",
    "rbac_manager"
]