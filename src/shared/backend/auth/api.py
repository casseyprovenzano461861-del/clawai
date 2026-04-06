#!/usr/bin/env python3
"""
FastAPI RBAC API路由
基于角色的访问控制管理API
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .authentication import auth_manager, security
from .rbac import Permission, rbac_manager, require_permission as rbac_require_permission
from ..schemas.auth import (
    RoleCreate, RoleUpdate, UserRoleAssignment, PermissionCheck,
    Permission, UserRole, APIError, ErrorCode
)
from ..database import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rbac", tags=["RBAC管理"])

# 权限检查装饰器适配器（用于API端点）
async def require_permission_dep(permission: Permission, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """权限检查依赖"""
    # 验证令牌
    token = credentials.credentials
    payload = auth_manager.verify_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token类型"
        )

    username = payload.get("username")

    # 检查权限
    if not rbac_manager.has_permission(username, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=APIError(
                code=ErrorCode.FORBIDDEN,
                message=f"权限不足: 需要 {permission.value} 权限",
                severity="medium"
            ).dict()
        )

    return True


# 角色管理API
@router.get("/roles", summary="获取所有角色")
async def get_roles(
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_READ))
):
    """获取系统中定义的所有角色"""
    try:
        roles = rbac_manager.get_all_roles()
        role_list = [role.to_dict() for role in roles]

        return {
            "roles": role_list,
            "total": len(role_list)
        }
    except Exception as e:
        logger.error(f"获取角色失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色失败"
        )


@router.get("/roles/{role_name}", summary="获取角色详情")
async def get_role(
    role_name: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_READ))
):
    """获取特定角色的详细信息"""
    role = rbac_manager.get_role(role_name)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色 '{role_name}' 不存在"
        )

    return role.to_dict()


@router.post("/roles", summary="创建新角色", status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_WRITE))
):
    """创建新角色"""
    # 检查角色是否已存在
    if rbac_manager.get_role(role_data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"角色 '{role_data.name}' 已存在"
        )

    # 转换权限字符串为Permission枚举
    permissions = []
    for perm_str in role_data.permissions:
        try:
            permissions.append(Permission(perm_str))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的权限: '{perm_str}'"
            )

    # 创建角色
    from .rbac import Role
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=permissions
    )

    success = rbac_manager.add_role(role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建角色失败"
        )

    return {
        "message": f"角色 '{role_data.name}' 创建成功",
        "role": role.to_dict()
    }


@router.put("/roles/{role_name}", summary="更新角色")
async def update_role(
    role_name: str,
    role_data: RoleUpdate,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_WRITE))
):
    """更新现有角色"""
    # 检查角色是否存在
    existing_role = rbac_manager.get_role(role_name)
    if not existing_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色 '{role_name}' 不存在"
        )

    # 转换权限字符串为Permission枚举（如果提供了权限）
    permissions = None
    if role_data.permissions is not None:
        permissions = []
        for perm_str in role_data.permissions:
            try:
                permissions.append(Permission(perm_str))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的权限: '{perm_str}'"
                )

    # 更新角色
    if role_data.description is not None:
        existing_role.description = role_data.description

    if permissions is not None:
        existing_role.permissions = set(permissions)

    # 注意：直接更新角色对象，因为rbac_manager.add_role只是添加新角色
    # 角色已经存在于roles字典中，我们直接修改它

    return {
        "message": f"角色 '{role_name}' 更新成功",
        "role": existing_role.to_dict()
    }


@router.delete("/roles/{role_name}", summary="删除角色")
async def delete_role(
    role_name: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_WRITE))
):
    """删除角色"""
    # 检查角色是否存在
    if not rbac_manager.get_role(role_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色 '{role_name}' 不存在"
        )

    # 删除角色
    success = rbac_manager.remove_role(role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除角色失败"
        )

    return {
        "message": f"角色 '{role_name}' 删除成功"
    }


# 用户角色分配API
@router.get("/users/{username}/roles", summary="获取用户的角色")
async def get_user_roles(
    username: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.USER_READ))
):
    """获取指定用户的所有角色"""
    user_roles = rbac_manager.get_user_roles(username)

    # 获取角色详情
    roles = []
    for role_name in user_roles:
        role = rbac_manager.get_role(role_name)
        if role:
            roles.append(role.to_dict())

    return {
        "username": username,
        "roles": roles,
        "role_names": list(user_roles)
    }


@router.post("/users/{username}/roles", summary="为用户分配角色")
async def assign_role_to_user(
    username: str,
    assignment: UserRoleAssignment,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.USER_WRITE))
):
    """为用户分配角色"""
    # 检查角色是否存在
    if not rbac_manager.get_role(assignment.role_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色 '{assignment.role_name}' 不存在"
        )

    # 分配角色
    success = rbac_manager.assign_role_to_user(username, assignment.role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配角色失败"
        )

    return {
        "message": f"角色 '{assignment.role_name}' 已分配给用户 '{username}'",
        "username": username,
        "role": assignment.role_name
    }


@router.delete("/users/{username}/roles/{role_name}", summary="移除用户的角色")
async def remove_role_from_user(
    username: str,
    role_name: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.USER_WRITE))
):
    """从用户移除角色"""
    # 检查用户是否有这个角色
    user_roles = rbac_manager.get_user_roles(username)
    if role_name not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 '{username}' 没有角色 '{role_name}'"
        )

    # 移除角色
    success = rbac_manager.remove_role_from_user(username, role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="移除角色失败"
        )

    return {
        "message": f"角色 '{role_name}' 已从用户 '{username}' 移除",
        "username": username,
        "role": role_name
    }


# 权限检查API
@router.post("/check", summary="检查权限")
async def check_permission(
    check: PermissionCheck,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """检查当前用户是否有特定权限"""
    # 验证令牌
    token = credentials.credentials
    payload = auth_manager.verify_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token类型"
        )

    username = payload.get("username")

    # 转换权限字符串为Permission枚举
    try:
        permission = Permission(check.permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的权限: '{check.permission}'"
        )

    # 检查权限
    has_permission = rbac_manager.has_permission(username, permission)

    return {
        "username": username,
        "permission": check.permission,
        "has_permission": has_permission,
        "timestamp": payload.get("iat")
    }


@router.get("/permissions", summary="获取所有权限")
async def get_permissions():
    """获取系统中定义的所有权限"""
    permissions = [p.value for p in Permission]

    # 按类别分组
    grouped = {}
    for perm in permissions:
        category = perm.split(":", 1)[0]
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(perm)

    return {
        "permissions": permissions,
        "grouped_permissions": grouped,
        "total": len(permissions)
    }


@router.get("/users/{username}/permissions", summary="获取用户的所有权限")
async def get_user_permissions(
    username: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.USER_READ))
):
    """获取指定用户的所有权限"""
    permissions = rbac_manager.get_user_permissions(username)

    return {
        "username": username,
        "permissions": [p.value for p in permissions],
        "permission_objects": [{"value": p.value, "name": p.name} for p in permissions],
        "total": len(permissions)
    }


# 角色用户查询API
@router.get("/roles/{role_name}/users", summary="获取拥有特定角色的所有用户")
async def get_users_with_role(
    role_name: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_READ))
):
    """获取拥有特定角色的所有用户"""
    # 检查角色是否存在
    if not rbac_manager.get_role(role_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"角色 '{role_name}' 不存在"
        )

    users = rbac_manager.get_users_with_role(role_name)

    return {
        "role": role_name,
        "users": users,
        "count": len(users)
    }


@router.get("/permissions/{permission}/users", summary="获取拥有特定权限的所有用户")
async def get_users_with_permission(
    permission: str,
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_READ))
):
    """获取拥有特定权限的所有用户"""
    # 转换权限字符串为Permission枚举
    try:
        perm_obj = Permission(permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的权限: '{permission}'"
        )

    users = rbac_manager.get_users_with_permission(perm_obj)

    return {
        "permission": permission,
        "users": users,
        "count": len(users)
    }


# 导入/导出API
@router.post("/import", summary="导入RBAC配置")
async def import_rbac_config(
    config: Dict[str, Any],
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_CONFIG))
):
    """导入RBAC配置"""
    # 注意：这个实现是简化的，实际应该从文件导入
    try:
        # 保存到临时文件然后加载
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            temp_file = f.name

        success = rbac_manager.load_from_file(temp_file)

        # 清理临时文件
        import os
        os.unlink(temp_file)

        if success:
            return {"message": "RBAC配置导入成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RBAC配置导入失败"
            )

    except Exception as e:
        logger.error(f"导入RBAC配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入RBAC配置失败: {str(e)}"
        )


@router.get("/export", summary="导出RBAC配置")
async def export_rbac_config(
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_READ))
):
    """导出RBAC配置"""
    try:
        # 保存到临时文件然后读取
        import tempfile
        import json

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False).name

        success = rbac_manager.save_to_file(temp_file)

        if success:
            with open(temp_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 清理临时文件
            import os
            os.unlink(temp_file)

            return config
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RBAC配置导出失败"
            )

    except Exception as e:
        logger.error(f"导出RBAC配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出RBAC配置失败: {str(e)}"
        )


# 默认角色分配（仅用于开发/测试）
@router.post("/default-assignments", summary="恢复默认角色分配")
async def restore_default_assignments(
    _has_permission: bool = Depends(lambda: require_permission_dep(Permission.SYSTEM_CONFIG))
):
    """恢复默认的角色分配（仅用于开发/测试环境）"""
    try:
        # 重新初始化默认分配
        rbac_manager.initialize_default_assignments()

        return {
            "message": "默认角色分配已恢复",
            "assignments": {
                "admin": ["admin"],
                "demo": ["analyst"]
            }
        }
    except Exception as e:
        logger.error(f"恢复默认角色分配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复默认角色分配失败: {str(e)}"
        )