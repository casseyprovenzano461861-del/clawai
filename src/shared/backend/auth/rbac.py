# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
基于角色的访问控制系统
提供细粒度的权限管理和角色控制
"""

from typing import Dict, List, Set, Optional, Any
from enum import Enum
import json
from functools import wraps
from flask import request, jsonify, g

# from config import config  # 不再需要，使用新的配置系统


class Permission(Enum):
    """系统权限枚举"""
    
    # 用户管理权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # 工具管理权限
    TOOL_READ = "tool:read"
    TOOL_WRITE = "tool:write"
    TOOL_EXECUTE = "tool:execute"
    
    # 攻击管理权限
    ATTACK_READ = "attack:read"
    ATTACK_WRITE = "attack:write"
    ATTACK_EXECUTE = "attack:execute"
    
    # 系统管理权限
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_CONFIG = "system:config"
    
    # 审计权限
    AUDIT_READ = "audit:read"
    AUDIT_WRITE = "audit:write"
    
    # 报告权限
    REPORT_READ = "report:read"
    REPORT_WRITE = "report:write"
    REPORT_EXPORT = "report:export"


class Role:
    """角色类"""
    
    def __init__(self, name: str, description: str, permissions: List[Permission]):
        self.name = name
        self.description = description
        self.permissions = set(permissions)
    
    def has_permission(self, permission: Permission) -> bool:
        """检查是否拥有特定权限"""
        return permission in self.permissions
    
    def add_permission(self, permission: Permission) -> None:
        """添加权限"""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """移除权限"""
        self.permissions.discard(permission)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """从字典创建角色"""
        permissions = [Permission(p) for p in data.get("permissions", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            permissions=permissions
        )


class RBACManager:
    """RBAC管理器"""
    
    def __init__(self):
        # 预定义角色
        self.roles = {}
        self.load_default_roles()

        # 用户角色映射
        self.user_roles = {}

        # 权限缓存
        self.permission_cache = {}

        # 初始化默认角色分配
        self.initialize_default_assignments()
    
    def load_default_roles(self):
        """加载默认角色"""
        # 管理员角色
        admin_permissions = list(Permission)
        self.add_role(Role(
            name="admin",
            description="系统管理员，拥有所有权限",
            permissions=admin_permissions
        ))
        
        # 安全分析师角色
        analyst_permissions = [
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
        self.add_role(Role(
            name="analyst",
            description="安全分析师，可以进行攻击测试和查看报告",
            permissions=analyst_permissions
        ))
        
        # 普通用户角色
        user_permissions = [
            Permission.TOOL_READ,
            Permission.TOOL_EXECUTE,
            Permission.ATTACK_READ,
            Permission.ATTACK_EXECUTE,
            Permission.REPORT_READ
        ]
        self.add_role(Role(
            name="user",
            description="普通用户，可以使用工具和执行攻击",
            permissions=user_permissions
        ))
        
        # 访客角色
        guest_permissions = [
            Permission.TOOL_READ,
            Permission.ATTACK_READ,
            Permission.REPORT_READ
        ]
        self.add_role(Role(
            name="guest",
            description="访客，只能查看信息",
            permissions=guest_permissions
        ))
        
        # 审计员角色
        auditor_permissions = [
            Permission.AUDIT_READ,
            Permission.AUDIT_WRITE,
            Permission.REPORT_READ,
            Permission.USER_READ,
            Permission.SYSTEM_READ
        ]
        self.add_role(Role(
            name="auditor",
            description="审计员，可以查看所有审计日志",
            permissions=auditor_permissions
        ))
    
    def add_role(self, role: Role) -> bool:
        """添加角色"""
        if role.name in self.roles:
            return False
        
        self.roles[role.name] = role
        return True
    
    def remove_role(self, role_name: str) -> bool:
        """移除角色"""
        if role_name not in self.roles:
            return False
        
        # 从所有用户中移除这个角色
        for username in list(self.user_roles.keys()):
            if role_name in self.user_roles[username]:
                self.user_roles[username].remove(role_name)
                
                # 如果用户没有角色了，移除该用户
                if not self.user_roles[username]:
                    del self.user_roles[username]
        
        del self.roles[role_name]
        return True
    
    def get_role(self, role_name: str) -> Optional[Role]:
        """获取角色"""
        return self.roles.get(role_name)
    
    def get_all_roles(self) -> List[Role]:
        """获取所有角色"""
        return list(self.roles.values())
    
    def assign_role_to_user(self, username: str, role_name: str) -> bool:
        """为用户分配角色"""
        if role_name not in self.roles:
            return False
        
        if username not in self.user_roles:
            self.user_roles[username] = set()
        
        self.user_roles[username].add(role_name)
        
        # 清除权限缓存
        if username in self.permission_cache:
            del self.permission_cache[username]
        
        return True
    
    def remove_role_from_user(self, username: str, role_name: str) -> bool:
        """从用户移除角色"""
        if username not in self.user_roles:
            return False
        
        if role_name not in self.user_roles[username]:
            return False
        
        self.user_roles[username].remove(role_name)
        
        # 如果用户没有角色了，移除该用户
        if not self.user_roles[username]:
            del self.user_roles[username]
        
        # 清除权限缓存
        if username in self.permission_cache:
            del self.permission_cache[username]
        
        return True
    
    def get_user_roles(self, username: str) -> Set[str]:
        """获取用户的角色"""
        return set(self.user_roles.get(username, set()))
    
    def get_user_permissions(self, username: str) -> Set[Permission]:
        """获取用户的所有权限"""
        # 检查缓存
        if username in self.permission_cache:
            return self.permission_cache[username]
        
        permissions = set()
        user_roles = self.get_user_roles(username)
        
        # 合并所有角色的权限
        for role_name in user_roles:
            role = self.get_role(role_name)
            if role:
                permissions.update(role.permissions)
        
        # 添加访客角色的权限（所有用户都有访客权限）
        guest_role = self.get_role("guest")
        if guest_role:
            permissions.update(guest_role.permissions)
        
        # 缓存结果
        self.permission_cache[username] = permissions
        
        return permissions
    
    def has_permission(self, username: str, permission: Permission) -> bool:
        """检查用户是否有特定权限"""
        if not username:
            return False
        
        permissions = self.get_user_permissions(username)
        return permission in permissions
    
    def has_any_permission(self, username: str, permission_list: List[Permission]) -> bool:
        """检查用户是否有任一权限"""
        if not username:
            return False
        
        permissions = self.get_user_permissions(username)
        return any(p in permissions for p in permission_list)
    
    def has_all_permissions(self, username: str, permission_list: List[Permission]) -> bool:
        """检查用户是否拥有所有权限"""
        if not username:
            return False
        
        permissions = self.get_user_permissions(username)
        return all(p in permissions for p in permission_list)
    
    def get_users_with_role(self, role_name: str) -> List[str]:
        """获取拥有特定角色的所有用户"""
        users = []
        for username, roles in self.user_roles.items():
            if role_name in roles:
                users.append(username)
        return users
    
    def get_users_with_permission(self, permission: Permission) -> List[str]:
        """获取拥有特定权限的所有用户"""
        users = []
        for username in self.user_roles.keys():
            if self.has_permission(username, permission):
                users.append(username)
        return users
    
    def clear_user_cache(self, username: str = None):
        """清除用户权限缓存"""
        if username:
            self.permission_cache.pop(username, None)
        else:
            self.permission_cache.clear()
    
    def load_from_file(self, filepath: str) -> bool:
        """从文件加载RBAC配置"""
        try:
            import os
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载角色
            if "roles" in data:
                for role_data in data["roles"]:
                    role = Role.from_dict(role_data)
                    self.roles[role.name] = role
            
            # 加载用户角色映射
            if "user_roles" in data:
                for username, roles in data["user_roles"].items():
                    self.user_roles[username] = set(roles)
            
            # 清除缓存
            self.permission_cache.clear()
            
            return True
        except Exception:
            return False
    
    def save_to_file(self, filepath: str) -> bool:
        """保存RBAC配置到文件"""
        try:
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                "roles": [role.to_dict() for role in self.roles.values()],
                "user_roles": {username: list(roles) for username, roles in self.user_roles.items()}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False
    
    def initialize_default_assignments(self):
        """初始化默认的角色分配"""
        # 为默认管理员分配admin角色
        self.assign_role_to_user("admin", "admin")
        
        # 为demo用户分配analyst角色
        self.assign_role_to_user("demo", "analyst")


# 全局RBAC管理器实例
rbac_manager = RBACManager()


def require_permission(permission: Permission):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否已认证
            if not hasattr(g, 'user'):
                return jsonify({"error": "未认证"}), 401
            
            username = g.user.get('username')
            
            # 检查权限
            if not rbac_manager.has_permission(username, permission):
                # 记录审计日志
                try:
                    from backend.auth.advanced_auth import auth_system
                    auth_system.audit_logger.log_event(
                        "PERMISSION_DENIED",
                        username,
                        request.endpoint or "unknown",
                        {
                            "required_permission": permission.value,
                            "path": request.path,
                            "method": request.method
                        },
                        success=False
                    )
                except ImportError:
                    pass
                
                return jsonify({"error": "权限不足"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(permissions: List[Permission]):
    """检查任一权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否已认证
            if not hasattr(g, 'user'):
                return jsonify({"error": "未认证"}), 401
            
            username = g.user.get('username')
            
            # 检查权限
            if not rbac_manager.has_any_permission(username, permissions):
                # 记录审计日志
                try:
                    from backend.auth.advanced_auth import auth_system
                    permission_values = [p.value for p in permissions]
                    auth_system.audit_logger.log_event(
                        "PERMISSION_DENIED",
                        username,
                        request.endpoint or "unknown",
                        {
                            "required_permissions": permission_values,
                            "path": request.path,
                            "method": request.method
                        },
                        success=False
                    )
                except ImportError:
                    pass
                
                return jsonify({"error": "权限不足"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_all_permissions(permissions: List[Permission]):
    """检查所有权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否已认证
            if not hasattr(g, 'user'):
                return jsonify({"error": "未认证"}), 401
            
            username = g.user.get('username')
            
            # 检查权限
            if not rbac_manager.has_all_permissions(username, permissions):
                # 记录审计日志
                try:
                    from backend.auth.advanced_auth import auth_system
                    permission_values = [p.value for p in permissions]
                    auth_system.audit_logger.log_event(
                        "PERMISSION_DENIED",
                        username,
                        request.endpoint or "unknown",
                        {
                            "required_permissions": permission_values,
                            "path": request.path,
                            "method": request.method
                        },
                        success=False
                    )
                except ImportError:
                    pass
                
                return jsonify({"error": "权限不足"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def setup_rbac_routes(app):
    """设置RBAC管理路由"""
    
    @app.route('/rbac/roles', methods=['GET'])
    @require_permission(Permission.SYSTEM_READ)
    def get_roles():
        """获取所有角色"""
        try:
            roles = rbac_manager.get_all_roles()
            role_list = [role.to_dict() for role in roles]
            
            return jsonify({
                "roles": role_list,
                "total": len(role_list)
            })
        except Exception as e:
            return jsonify({"error": f"获取角色失败: {str(e)}"}), 500
    
    @app.route('/rbac/roles', methods=['POST'])
    @require_permission(Permission.SYSTEM_WRITE)
    def create_role():
        """创建新角色"""
        try:
            data = request.json
            if not data or 'name' not in data or 'permissions' not in data:
                return jsonify({"error": "需要角色名称和权限列表"}), 400
            
            role_name = data['name']
            description = data.get('description', '')
            
            # 验证权限
            permissions = []
            for perm_str in data['permissions']:
                try:
                    permission = Permission(perm_str)
                    permissions.append(permission)
                except ValueError:
                    return jsonify({"error": f"无效的权限: {perm_str}"}), 400
            
            # 创建角色
            role = Role(
                name=role_name,
                description=description,
                permissions=permissions
            )
            
            success = rbac_manager.add_role(role)
            if not success:
                return jsonify({"error": "角色已存在"}), 400
            
            return jsonify({
                "success": True,
                "role": role.to_dict(),
                "message": f"角色 '{role_name}' 创建成功"
            })
        except Exception as e:
            return jsonify({"error": f"创建角色失败: {str(e)}"}), 500
    
    @app.route('/rbac/roles/<role_name>', methods=['DELETE'])
    @require_permission(Permission.SYSTEM_WRITE)
    def delete_role(role_name):
        """删除角色"""
        try:
            # 禁止删除预定义角色
            predefined_roles = {"admin", "analyst", "user", "guest", "auditor"}
            if role_name in predefined_roles:
                return jsonify({"error": "不能删除预定义角色"}), 400
            
            success = rbac_manager.remove_role(role_name)
            if not success:
                return jsonify({"error": "角色不存在"}), 404
            
            return jsonify({
                "success": True,
                "message": f"角色 '{role_name}' 删除成功"
            })
        except Exception as e:
            return jsonify({"error": f"删除角色失败: {str(e)}"}), 500
    
    @app.route('/rbac/users/<username>/roles', methods=['GET'])
    @require_permission(Permission.USER_READ)
    def get_user_roles(username):
        """获取用户的角色"""
        try:
            # 用户只能查看自己的角色，管理员可以查看所有
            current_user = g.user.get('username')
            if current_user != username and not rbac_manager.has_permission(current_user, Permission.SYSTEM_READ):
                return jsonify({"error": "权限不足"}), 403
            
            roles = rbac_manager.get_user_roles(username)
            
            return jsonify({
                "username": username,
                "roles": list(roles)
            })
        except Exception as e:
            return jsonify({"error": f"获取用户角色失败: {str(e)}"}), 500
    
    @app.route('/rbac/users/<username>/roles', methods=['POST'])
    @require_permission(Permission.USER_WRITE)
    def assign_role_to_user_endpoint(username):
        """为用户分配角色"""
        try:
            data = request.json
            if not data or 'role' not in data:
                return jsonify({"error": "需要角色名称"}), 400
            
            role_name = data['role']
            
            success = rbac_manager.assign_role_to_user(username, role_name)
            if not success:
                return jsonify({"error": "角色不存在或分配失败"}), 400
            
            return jsonify({
                "success": True,
                "message": f"角色 '{role_name}' 已分配给用户 '{username}'"
            })
        except Exception as e:
            return jsonify({"error": f"分配角色失败: {str(e)}"}), 500
    
    @app.route('/rbac/users/<username>/roles/<role_name>', methods=['DELETE'])
    @require_permission(Permission.USER_WRITE)
    def remove_role_from_user_endpoint(username, role_name):
        """从用户移除角色"""
        try:
            # 禁止从admin用户移除admin角色
            if username == "admin" and role_name == "admin":
                return jsonify({"error": "不能移除管理员的管理员角色"}), 400
            
            success = rbac_manager.remove_role_from_user(username, role_name)
            if not success:
                return jsonify({"error": "用户没有这个角色或角色不存在"}), 400
            
            return jsonify({
                "success": True,
                "message": f"角色 '{role_name}' 已从用户 '{username}' 移除"
            })
        except Exception as e:
            return jsonify({"error": f"移除角色失败: {str(e)}"}), 500
    
    @app.route('/rbac/users/<username>/permissions', methods=['GET'])
    @require_permission(Permission.USER_READ)
    def get_user_permissions_endpoint(username):
        """获取用户的所有权限"""
        try:
            # 用户只能查看自己的权限，管理员可以查看所有
            current_user = g.user.get('username')
            if current_user != username and not rbac_manager.has_permission(current_user, Permission.SYSTEM_READ):
                return jsonify({"error": "权限不足"}), 403
            
            permissions = rbac_manager.get_user_permissions(username)
            
            return jsonify({
                "username": username,
                "permissions": [p.value for p in permissions]
            })
        except Exception as e:
            return jsonify({"error": f"获取用户权限失败: {str(e)}"}), 500
    
    @app.route('/rbac/check-permission', methods=['POST'])
    def check_permission():
        """检查当前用户是否有特定权限"""
        try:
            data = request.json
            if not data or 'permission' not in data:
                return jsonify({"error": "需要权限名称"}), 400
            
            # 检查是否已认证
            if not hasattr(g, 'user'):
                return jsonify({"error": "未认证"}), 401
            
            username = g.user.get('username')
            permission_str = data['permission']
            
            try:
                permission = Permission(permission_str)
            except ValueError:
                return jsonify({"error": f"无效的权限: {permission_str}"}), 400
            
            has_perm = rbac_manager.has_permission(username, permission)
            
            return jsonify({
                "username": username,
                "permission": permission.value,
                "has_permission": has_perm
            })
        except Exception as e:
            return jsonify({"error": f"检查权限失败: {str(e)}"}), 500
    
    @app.route('/rbac/stats', methods=['GET'])
    @require_permission(Permission.SYSTEM_READ)
    def get_rbac_stats():
        """获取RBAC统计信息"""
        try:
            stats = {
                "total_roles": len(rbac_manager.roles),
                "total_users_with_roles": len(rbac_manager.user_roles),
                "predefined_roles": ["admin", "analyst", "user", "guest", "auditor"],
                "custom_roles": [name for name in rbac_manager.roles.keys() if name not in ["admin", "analyst", "user", "guest", "auditor"]]
            }
            
            return jsonify(stats)
        except Exception as e:
            return jsonify({"error": f"获取统计信息失败: {str(e)}"}), 500
    
    return app


if __name__ == "__main__":
    # 测试RBAC模块
    print("测试RBAC模块...")
    
    # 测试权限检查
    print("\n1. 权限检查测试:")
    
    # 为测试用户分配角色
    rbac_manager.assign_role_to_user("test_user", "analyst")
    
    # 检查权限
    has_tool_read = rbac_manager.has_permission("test_user", Permission.TOOL_READ)
    has_user_write = rbac_manager.has_permission("test_user", Permission.USER_WRITE)
    
    print(f"  test_user有TOOL_READ权限: {has_tool_read}")
    print(f"  test_user有USER_WRITE权限: {has_user_write}")
    
    # 获取用户权限
    print("\n2. 获取用户所有权限:")
    permissions = rbac_manager.get_user_permissions("test_user")
    print(f"  test_user的权限: {[p.value for p in permissions]}")
    
    # 角色管理
    print("\n3. 角色管理测试:")
    
    # 创建自定义角色
    custom_role = Role(
        name="custom_role",
        description="自定义角色",
        permissions=[Permission.TOOL_READ, Permission.ATTACK_READ]
    )
    rbac_manager.add_role(custom_role)
    
    print(f"  创建自定义角色: {custom_role.name}")
    
    # 为用户分配自定义角色
    rbac_manager.assign_role_to_user("test_user", "custom_role")
    
    # 检查新权限
    has_custom_perms = rbac_manager.has_all_permissions(
        "test_user", 
        [Permission.TOOL_READ, Permission.ATTACK_READ]
    )
    print(f"  test_user拥有自定义角色的所有权限: {has_custom_perms}")
    
    # 获取所有角色
    print("\n4. 获取所有角色:")
    all_roles = rbac_manager.get_all_roles()
    for role in all_roles:
        print(f"  角色: {role.name} - {role.description}")
    
    print("\nRBAC模块测试完成！")