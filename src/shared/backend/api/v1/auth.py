# -*- coding: utf-8 -*-
"""
认证API蓝图 - 简化版本
"""

from flask import Blueprint, request, jsonify
import time
import jwt

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    用户登录
    
    POST /api/v1/auth/login
    Body: {
        "username": "admin",
        "password": "admin123"
    }
    """
    try:
        data = request.json
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                "error": "missing_credentials",
                "message": "缺少用户名或密码"
            }), 400
        
        username = data['username']
        password = data['password']
        
        # 简化验证：只检查默认管理员账户
        # 实际项目中应该使用数据库验证
        if username == "admin" and password == "admin123":
            # 生成JWT令牌
            from config import config
            
            payload = {
                "sub": "admin_user_id",
                "username": username,
                "role": "admin",
                "permissions": ["attack", "view_history", "manage_tools"],
                "iat": int(time.time()),
                "exp": int(time.time()) + config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
            token = jwt.encode(
                payload,
                config.JWT_SECRET,
                algorithm=config.JWT_ALGORITHM
            )
            
            return jsonify({
                "access_token": token,
                "token_type": "bearer",
                "expires_in": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "id": "admin_user_id",
                    "username": username,
                    "role": "admin",
                    "permissions": payload["permissions"]
                }
            })
        else:
            return jsonify({
                "error": "invalid_credentials",
                "message": "用户名或密码错误"
            }), 401
            
    except Exception as e:
        return jsonify({
            "error": "login_failed",
            "message": f"登录失败: {str(e)}"
        }), 500


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """
    用户注册
    
    POST /api/v1/auth/register
    Body: {
        "username": "newuser",
        "password": "password123",
        "email": "user@example.com"
    }
    """
    try:
        data = request.json
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                "error": "missing_credentials",
                "message": "缺少用户名或密码"
            }), 400
        
        username = data['username']
        password = data['password']
        email = data.get('email')
        
        # 简化注册：总是成功
        # 实际项目中应该检查用户是否已存在并存储到数据库
        
        return jsonify({
            "message": "注册成功",
            "user": {
                "username": username,
                "email": email,
                "role": "user",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": "registration_failed",
            "message": f"注册失败: {str(e)}"
        }), 500


@auth_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """
    获取当前用户信息
    
    GET /api/v1/auth/me
    Header: Authorization: Bearer <token>
    """
    # 简化版本：直接从认证中间件获取用户信息
    # 实际项目中应该验证JWT令牌
    from flask import g
    
    if hasattr(g, 'user'):
        return jsonify(g.user)
    else:
        return jsonify({
            "error": "not_authenticated",
            "message": "用户未认证"
        }), 401