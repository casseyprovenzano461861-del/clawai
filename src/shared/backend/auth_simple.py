# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
简化的认证模块
移除复杂的bcrypt依赖，使用简单的认证机制
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify, g

from config import config


class SimpleAuthManager:
    """简化认证管理器"""
    
    def __init__(self):
        self.jwt_secret = config.JWT_SECRET or "clawai_simple_secret_key"
        self.access_token_expire = timedelta(minutes=30)
        
        # 简化的用户存储
        self.users = {
            "admin": {
                "username": "admin",
                "password_hash": self._simple_hash("admin123"),
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "is_active": True
            },
            "demo": {
                "username": "demo",
                "password_hash": self._simple_hash("demo123"),
                "role": "user",
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }
        }
    
    def _simple_hash(self, password: str) -> str:
        """简单的密码哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self._simple_hash(password) == hashed_password
    
    def create_access_token(self, username: str, role: str = "user") -> str:
        """创建简单的访问令牌（模拟JWT）"""
        import time
        import json
        import base64
        
        payload = {
            "sub": username,
            "role": role,
            "exp": int(time.time()) + 1800,  # 30分钟过期
            "iat": int(time.time())
        }
        
        # 简单的base64编码，不是真正的JWT
        payload_json = json.dumps(payload)
        encoded = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
        
        # 添加简单的签名
        signature = hashlib.sha256((encoded + self.jwt_secret).encode('utf-8')).hexdigest()[:16]
        
        return f"{encoded}.{signature}"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            import time
            import json
            import base64
            
            if not token or '.' not in token:
                return None
            
            encoded, signature = token.split('.', 1)
            
            # 验证签名
            expected_signature = hashlib.sha256((encoded + self.jwt_secret).encode('utf-8')).hexdigest()[:16]
            if signature != expected_signature:
                return None
            
            # 解码payload
            payload_json = base64.b64decode(encoded).decode('utf-8')
            payload = json.loads(payload_json)
            
            # 检查过期时间
            if payload.get("exp", 0) < int(time.time()):
                return None
            
            return payload
            
        except Exception:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        user = self.users.get(username)
        if not user:
            return None
        
        if not user["is_active"]:
            return None
        
        if not self._verify_password(password, user["password_hash"]):
            return None
        
        return {
            "username": user["username"],
            "role": user["role"]
        }
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        user = self.users.get(username)
        if not user:
            return None
        
        return {
            "username": user["username"],
            "role": user["role"],
            "created_at": user["created_at"],
            "is_active": user["is_active"]
        }


# 全局认证管理器实例
auth_manager = SimpleAuthManager()


def require_auth(f):
    """简化的认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查Authorization头
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            # 尝试提取Bearer令牌
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
                # 验证令牌
                payload = auth_manager.verify_token(token)
                if payload:
                    # 令牌有效，设置用户信息
                    g.user = {
                        "username": payload.get("sub"),
                        "role": payload.get("role", "user")
                    }
                    return f(*args, **kwargs)
        
        # 如果没有有效的令牌，检查认证是否启用
        if config.API_AUTH_ENABLED:
            # 认证已启用但没有有效令牌，返回401
            return jsonify({"error": "缺少有效的认证令牌"}), 401
        else:
            # 认证未启用，使用匿名用户
            g.user = {"username": "anonymous", "role": "guest"}
            return f(*args, **kwargs)
    
    return decorated_function


def setup_auth_routes(app):
    """设置简化的认证路由"""
    
    @app.route('/auth/login', methods=['POST'])
    def login():
        """用户登录"""
        try:
            data = request.json
            if not data or 'username' not in data or 'password' not in data:
                return jsonify({"error": "需要用户名和密码"}), 400
            
            username = data['username']
            password = data['password']
            
            # 认证用户
            user = auth_manager.authenticate_user(username, password)
            if not user:
                return jsonify({"error": "用户名或密码错误"}), 401
            
            # 生成令牌
            access_token = auth_manager.create_access_token(user['username'], user['role'])
            
            return jsonify({
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 1800,  # 30分钟
                "user": user
            })
        
        except Exception as e:
            return jsonify({"error": f"登录失败: {str(e)}"}), 500
    
    @app.route('/auth/me', methods=['GET'])
    @require_auth
    def get_current_user():
        """获取当前用户信息"""
        username = g.user.get('username')
        role = g.user.get('role')
        
        # 如果是匿名用户（认证未启用）
        if username == "anonymous" and role == "guest":
            return jsonify({
                "user": {
                    "username": "anonymous",
                    "role": "guest",
                    "created_at": datetime.now().isoformat(),
                    "is_active": True,
                    "message": "认证功能未启用，使用匿名访问"
                }
            })
        
        # 直接从用户存储中获取用户信息
        user_data = auth_manager.users.get(username)
        if not user_data:
            return jsonify({"error": "用户不存在"}), 404
        
        # 返回用户信息（排除密码哈希）
        user_info = {
            "username": user_data["username"],
            "role": user_data["role"],
            "created_at": user_data["created_at"],
            "is_active": user_data["is_active"]
        }
        
        return jsonify({
            "user": user_info
        })
    
    return app


if __name__ == "__main__":
    # 测试简化认证模块
    print("测试简化认证模块...")
    
    # 认证测试
    auth_result = auth_manager.authenticate_user("admin", "admin123")
    print(f"管理员认证结果: {auth_result}")
    
    # 生成令牌
    if auth_result:
        access_token = auth_manager.create_access_token(auth_result["username"], auth_result["role"])
        print(f"访问令牌: {access_token}")
        
        # 验证令牌
        payload = auth_manager.verify_token(access_token)
        print(f"令牌验证: {payload}")
    
    print("简化认证模块测试完成！")