# -*- coding: utf-8 -*-
"""
FastAPI RBAC管理API路由
基于现有Flask版本转换
"""

import re
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator

from backend.auth.rbac import Permission, rbac_manager, Role
from backend.auth.fastapi_permissions import (
    require_permission, require_authentication,
    get_current_user, require_role
)
from backend.schemas.error import APIError, ErrorCode
from backend.security.validation_integration import (
    secure_string_validator, get_secure_validator, secure_model
)
from backend.security.input_validation import ValidationSeverity

# 创建路由器
router = APIRouter(prefix="/rbac", tags=["RBAC管理"])


# 请求/响应模型
class RoleCreateRequest(BaseModel):
    """创建角色请求"""
    name: str = Field(..., description="角色名称", min_length=1, max_length=50)
    description: str = Field("", description="角色描述", max_length=200)
    permissions: List[str] = Field(..., description="权限列表")

    @validator('name')
    def validate_name(cls, v):
        """验证角色名称"""
        if not v:
            raise ValueError("角色名称不能为空")

        # 检查是否只包含允许的字符
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError("角色名称只能包含字母、数字、下划线和连字符")

        # 安全验证：检查恶意输入
        validator_instance = get_secure_validator()
        threats, severity = validator_instance._detect_threats(v)

        if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
            raise ValueError(f"角色名称包含高危威胁: {', '.join(threats)}")

        return v

    @validator('description')
    def validate_description(cls, v):
        """验证角色描述"""
        if v:
            # 安全验证：检查恶意输入
            validator_instance = get_secure_validator()
            threats, severity = validator_instance._detect_threats(v)

            if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                raise ValueError(f"角色描述包含高危威胁: {', '.join(threats)}")

        return v

    @validator('permissions')
    def validate_permissions(cls, v):
        """验证权限列表"""
        if not v:
            raise ValueError("权限列表不能为空")

        # 检查每个权限字符串
        validator_instance = get_secure_validator()
        for perm_str in v:
            # 验证权限格式
            try:
                # 尝试转换为Permission枚举
                Permission(perm_str)
            except ValueError:
                raise ValueError(f"无效的权限: {perm_str}")

            # 安全验证：检查恶意输入
            threats, severity = validator_instance._detect_threats(perm_str)
            if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
                raise ValueError(f"权限字符串包含高危威胁: {', '.join(threats)}")

        return v

class RoleResponse(BaseModel):
    """角色响应"""
    name: str
    description: str
    permissions: List[str]

class RoleListResponse(BaseModel):
    """角色列表响应"""
    roles: List[RoleResponse]
    total: int

class AssignRoleRequest(BaseModel):
    """分配角色请求"""
    role: str = Field(..., description="角色名称", min_length=1, max_length=50)

    @validator('role')
    def validate_role(cls, v):
        """验证角色名称"""
        if not v:
            raise ValueError("角色名称不能为空")

        # 检查是否只包含允许的字符
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError("角色名称只能包含字母、数字、下划线和连字符")

        # 安全验证：检查恶意输入
        validator_instance = get_secure_validator()
        threats, severity = validator_instance._detect_threats(v)

        if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
            raise ValueError(f"角色名称包含高危威胁: {', '.join(threats)}")

        return v

class UserRolesResponse(BaseModel):
    """用户角色响应"""
    username: str
    roles: List[str]

class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    username: str
    permissions: List[str]

class CheckPermissionRequest(BaseModel):
    """检查权限请求"""
    permission: str = Field(..., description="权限名称", min_length=1, max_length=100)

    @validator('permission')
    def validate_permission(cls, v):
        """验证权限名称"""
        if not v:
            raise ValueError("权限名称不能为空")

        # 尝试转换为Permission枚举以验证格式
        try:
            Permission(v)
        except ValueError:
            raise ValueError(f"无效的权限格式: {v}")

        # 安全验证：检查恶意输入
        validator_instance = get_secure_validator()
        threats, severity = validator_instance._detect_threats(v)

        if threats and severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
            raise ValueError(f"权限名称包含高危威胁: {', '.join(threats)}")

        return v

class CheckPermissionResponse(BaseModel):
    """检查权限响应"""
    username: str
    permission: str
    has_permission: bool

class RBACStatsResponse(BaseModel):
    """RBAC统计响应"""
    total_roles: int
    total_users_with_roles: int
    predefined_roles: List[str]
    custom_roles: List[str]


@router.get("/roles", response_model=RoleListResponse)
async def get_roles(
    request: Request,
    _has_permission: bool = Depends(require_permission(Permission.SYSTEM_READ))
):
    """获取所有角色"""
    try:
        roles = rbac_manager.get_all_roles()
        role_list = [RoleResponse(
            name=role.name,
            description=role.description,
            permissions=[p.value for p in role.permissions]
        ) for role in roles]

        return RoleListResponse(
            roles=role_list,
            total=len(role_list)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"获取角色失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.post("/roles", response_model=Dict[str, Any])
async def create_role(
    request: Request,
    role_data: RoleCreateRequest,
    _has_permission: bool = Depends(require_permission(Permission.SYSTEM_WRITE))
):
    """创建新角色"""
    try:
        role_name = role_data.name
        description = role_data.description

        # 验证权限
        permissions = []
        for perm_str in role_data.permissions:
            try:
                permission = Permission(perm_str)
                permissions.append(permission)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=APIError(
                        code=ErrorCode.VALIDATION_ERROR,
                        message=f"无效的权限: {perm_str}",
                        severity="error"
                    ).model_dump()
                )

        # 检查角色是否已存在
        if role_name in rbac_manager.roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="角色已存在",
                    severity="error"
                ).model_dump()
            )

        # 创建角色
        role = Role(
            name=role_name,
            description=description,
            permissions=permissions
        )

        success = rbac_manager.add_role(role)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="角色创建失败",
                    severity="error"
                ).model_dump()
            )

        return {
            "success": True,
            "role": {
                "name": role.name,
                "description": role.description,
                "permissions": [p.value for p in role.permissions]
            },
            "message": f"角色 '{role_name}' 创建成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"创建角色失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.delete("/roles/{role_name}", response_model=Dict[str, Any])
async def delete_role(
    request: Request,
    role_name: str,
    _has_permission: bool = Depends(require_permission(Permission.SYSTEM_WRITE))
):
    """删除角色"""
    try:
        # 禁止删除预定义角色
        predefined_roles = {"admin", "analyst", "user", "guest", "auditor"}
        if role_name in predefined_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="不能删除预定义角色",
                    severity="error"
                ).model_dump()
            )

        success = rbac_manager.remove_role(role_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message="角色不存在",
                    severity="error"
                ).model_dump()
            )

        return {
            "success": True,
            "message": f"角色 '{role_name}' 删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"删除角色失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.get("/users/{username}/roles", response_model=UserRolesResponse)
async def get_user_roles(
    request: Request,
    username: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取用户的角色"""
    try:
        # 用户只能查看自己的角色，管理员可以查看所有
        current_username = current_user.get('username')
        if current_username != username and not rbac_manager.has_permission(current_username, Permission.SYSTEM_READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.PERMISSION_DENIED,
                    message="权限不足",
                    severity="error"
                ).model_dump()
            )

        roles = rbac_manager.get_user_roles(username)

        return UserRolesResponse(
            username=username,
            roles=list(roles)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"获取用户角色失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.post("/users/{username}/roles", response_model=Dict[str, Any])
async def assign_role_to_user_endpoint(
    request: Request,
    username: str,
    assign_data: AssignRoleRequest,
    _has_permission: bool = Depends(require_permission(Permission.USER_WRITE))
):
    """为用户分配角色"""
    try:
        role_name = assign_data.role

        success = rbac_manager.assign_role_to_user(username, role_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="角色不存在或分配失败",
                    severity="error"
                ).model_dump()
            )

        return {
            "success": True,
            "message": f"角色 '{role_name}' 已分配给用户 '{username}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"分配角色失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.delete("/users/{username}/roles/{role_name}", response_model=Dict[str, Any])
async def remove_role_from_user_endpoint(
    request: Request,
    username: str,
    role_name: str,
    _has_permission: bool = Depends(require_permission(Permission.USER_WRITE))
):
    """从用户移除角色"""
    try:
        # 禁止从admin用户移除admin角色
        if username == "admin" and role_name == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="不能移除管理员的管理员角色",
                    severity="error"
                ).model_dump()
            )

        success = rbac_manager.remove_role_from_user(username, role_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="用户没有这个角色或角色不存在",
                    severity="error"
                ).model_dump()
            )

        return {
            "success": True,
            "message": f"角色 '{role_name}' 已从用户 '{username}' 移除"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"移除角色失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.get("/users/{username}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions_endpoint(
    request: Request,
    username: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取用户的所有权限"""
    try:
        # 用户只能查看自己的权限，管理员可以查看所有
        current_username = current_user.get('username')
        if current_username != username and not rbac_manager.has_permission(current_username, Permission.SYSTEM_READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=APIError(
                    code=ErrorCode.PERMISSION_DENIED,
                    message="权限不足",
                    severity="error"
                ).model_dump()
            )

        permissions = rbac_manager.get_user_permissions(username)

        return UserPermissionsResponse(
            username=username,
            permissions=[p.value for p in permissions]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"获取用户权限失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.post("/check-permission", response_model=CheckPermissionResponse)
async def check_permission(
    request: Request,
    check_data: CheckPermissionRequest,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """检查当前用户是否有特定权限"""
    try:
        username = current_user.get('username')
        permission_str = check_data.permission

        try:
            permission = Permission(permission_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"无效的权限: {permission_str}",
                    severity="error"
                ).model_dump()
            )

        has_perm = rbac_manager.has_permission(username, permission)

        return CheckPermissionResponse(
            username=username,
            permission=permission.value,
            has_permission=has_perm
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"检查权限失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


@router.get("/stats", response_model=RBACStatsResponse)
async def get_rbac_stats(
    request: Request,
    _has_permission: bool = Depends(require_permission(Permission.SYSTEM_READ))
):
    """获取RBAC统计信息"""
    try:
        stats = RBACStatsResponse(
            total_roles=len(rbac_manager.roles),
            total_users_with_roles=len(rbac_manager.user_roles),
            predefined_roles=["admin", "analyst", "user", "guest", "auditor"],
            custom_roles=[name for name in rbac_manager.roles.keys() if name not in ["admin", "analyst", "user", "guest", "auditor"]]
        )

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=f"获取统计信息失败: {str(e)}",
                severity="error"
            ).model_dump()
        )


# 导出路由器
__all__ = ["router"]