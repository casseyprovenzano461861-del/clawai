# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
高级认证系统
支持多因素认证、JWT管理、速率限制和安全审计
"""

import hashlib
import secrets
import time
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps
from flask import request, jsonify, g
import redis
import pyotp

from config import config


class JWTManager:
    """JWT令牌管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, payload: Dict[str, Any], expires_in: int = 1800) -> str:
        """创建JWT令牌"""
        # 添加标准声明
        payload = payload.copy()
        payload.update({
            "iss": "clawai-auth",
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in,
            "jti": secrets.token_hex(16)  # 唯一标识符
        })
        
        # 头部
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }
        
        # 编码
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(header).encode('utf-8')
        ).rstrip(b'=').decode('utf-8')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode('utf-8')
        ).rstrip(b'=').decode('utf-8')
        
        # 签名
        signature_input = f"{header_encoded}.{payload_encoded}"
        if self.algorithm == "HS256":
            import hmac
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                signature_input.encode('utf-8'),
                hashlib.sha256
            ).digest()
        else:
            raise ValueError(f"不支持的算法: {self.algorithm}")
        
        signature_encoded = base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')
        
        return f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_encoded, payload_encoded, signature_encoded = parts
            
            # 验证签名
            signature_input = f"{header_encoded}.{payload_encoded}"
            if self.algorithm == "HS256":
                import hmac
                expected_signature = hmac.new(
                    self.secret_key.encode('utf-8'),
                    signature_input.encode('utf-8'),
                    hashlib.sha256
                ).digest()
                expected_signature_encoded = base64.urlsafe_b64encode(
                    expected_signature
                ).rstrip(b'=').decode('utf-8')
                
                if not secrets.compare_digest(signature_encoded, expected_signature_encoded):
                    return None
            
            # 解码payload
            padding = 4 - len(payload_encoded) % 4
            if padding != 4:
                payload_encoded += '=' * padding
            
            payload_json = base64.urlsafe_b64decode(payload_encoded).decode('utf-8')
            payload = json.loads(payload_json)
            
            # 检查过期时间
            if payload.get("exp", 0) < int(time.time()):
                return None
            
            return payload
            
        except Exception:
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码JWT令牌（不验证签名）"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            _, payload_encoded, _ = parts
            
            # 解码payload
            padding = 4 - len(payload_encoded) % 4
            if padding != 4:
                payload_encoded += '=' * padding
            
            payload_json = base64.urlsafe_b64decode(payload_encoded).decode('utf-8')
            payload = json.loads(payload_json)
            
            return payload
            
        except Exception:
            return None


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, redis_client=None, default_limits: Dict[str, Tuple[int, int]] = None):
        """
        :param redis_client: Redis客户端（可选）
        :param default_limits: 默认限制配置 {规则名: (请求数, 时间窗口秒数)}
        """
        self.redis = redis_client
        self.default_limits = default_limits or {
            "login": (5, 300),      # 5次/5分钟
            "api": (100, 3600),     # 100次/小时
            "admin": (1000, 3600),  # 1000次/小时
        }
        
        # 内存存储（如果Redis不可用）
        self.memory_store = {}
    
    def _get_key(self, rule: str, identifier: str) -> str:
        """生成存储键"""
        return f"rate_limit:{rule}:{identifier}"
    
    def is_allowed(self, rule: str, identifier: str, limit: int = None, window: int = None) -> bool:
        """检查是否允许请求"""
        if limit is None or window is None:
            default = self.default_limits.get(rule, (60, 3600))
            limit = limit or default[0]
            window = window or default[1]
        
        key = self._get_key(rule, identifier)
        current_time = int(time.time())
        window_start = current_time - window
        
        try:
            if self.redis:
                # 使用Redis
                self.redis.zremrangebyscore(key, 0, window_start)
                count = self.redis.zcard(key)
                
                if count < limit:
                    self.redis.zadd(key, {str(current_time): current_time})
                    self.redis.expire(key, window)
                    return True
                else:
                    return False
            else:
                # 使用内存存储
                if key not in self.memory_store:
                    self.memory_store[key] = []
                
                # 清理过期的请求时间戳
                self.memory_store[key] = [t for t in self.memory_store[key] if t > window_start]
                
                if len(self.memory_store[key]) < limit:
                    self.memory_store[key].append(current_time)
                    return True
                else:
                    return False
        except Exception:
            # 如果出现异常，允许请求（安全故障开放）
            return True
    
    def get_remaining(self, rule: str, identifier: str, limit: int = None, window: int = None) -> int:
        """获取剩余请求次数"""
        if limit is None or window is None:
            default = self.default_limits.get(rule, (60, 3600))
            limit = limit or default[0]
            window = window or default[1]
        
        key = self._get_key(rule, identifier)
        current_time = int(time.time())
        window_start = current_time - window
        
        try:
            if self.redis:
                # 使用Redis
                self.redis.zremrangebyscore(key, 0, window_start)
                count = self.redis.zcard(key)
                return max(0, limit - count)
            else:
                # 使用内存存储
                if key not in self.memory_store:
                    return limit
                
                self.memory_store[key] = [t for t in self.memory_store[key] if t > window_start]
                return max(0, limit - len(self.memory_store[key]))
        except Exception:
            return limit


class AuditLogger:
    """安全审计日志记录器"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or "logs/security_audit.log"
    
    def log_event(self, 
                 event_type: str, 
                 user: str, 
                 action: str, 
                 details: Dict[str, Any] = None,
                 success: bool = True,
                 ip_address: str = None):
        """记录审计事件"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user": user,
                "action": action,
                "details": details or {},
                "success": success,
                "ip_address": ip_address or request.remote_addr if request else "N/A"
            }
            
            # 写入日志文件
            log_dir = "logs"
            import os
            os.makedirs(log_dir, exist_ok=True)
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # 同时打印到控制台（用于调试）
            print(f"[AUDIT] {log_entry['timestamp']} {event_type}: {user} - {action} - {'SUCCESS' if success else 'FAILED'}")
            
        except Exception as e:
            print(f"[AUDIT ERROR] 记录审计日志失败: {str(e)}")


class AdvancedAuthSystem:
    """高级认证系统"""
    
    def __init__(self):
        # JWT管理器
        self.jwt_manager = JWTManager(
            secret_key=config.JWT_SECRET or "clawai_advanced_secret_key_2025",
            algorithm="HS256"
        )
        
        # 速率限制器
        try:
            redis_client = redis.Redis(
                host=config.REDIS_HOST or "localhost",
                port=config.REDIS_PORT or 6379,
                decode_responses=True
            )
            # 测试连接
            redis_client.ping()
        except Exception:
            redis_client = None
        
        self.rate_limiter = RateLimiter(redis_client)
        
        # 审计日志记录器
        self.audit_logger = AuditLogger()
        
        # 用户存储（在实际应用中应该使用数据库）
        self.users = {}
        self.load_default_users()
        
        # MFA配置
        self.mfa_enabled = config.MFA_ENABLED if hasattr(config, 'MFA_ENABLED') else True
    
    def load_default_users(self):
        """加载默认用户"""
        self.users = {
            "admin": {
                "username": "admin",
                "password_hash": self._hash_password("admin123"),
                "role": "admin",
                "mfa_secret": None,  # TOTP密钥
                "mfa_enabled": False,
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "is_active": True,
                "failed_login_attempts": 0,
                "locked_until": None
            },
            "demo": {
                "username": "demo",
                "password_hash": self._hash_password("demo123"),
                "role": "user",
                "mfa_secret": None,
                "mfa_enabled": False,
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "is_active": True,
                "failed_login_attempts": 0,
                "locked_until": None
            }
        }
    
    def _hash_password(self, password: str, salt: str = None) -> str:
        """安全的密码哈希"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # 使用PBKDF2进行哈希
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )
        
        return f"pbkdf2_sha256${salt}${dk.hex()}"
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            if not hashed_password or '$' not in hashed_password:
                # 旧格式的哈希
                return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed_password
            
            # 新格式: pbkdf2_sha256$salt$hash
            algorithm, salt, hash_value = hashed_password.split('$')
            
            if algorithm != "pbkdf2_sha256":
                return False
            
            dk = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            
            return secrets.compare_digest(dk.hex(), hash_value)
        except Exception:
            return False
    
    def generate_mfa_secret(self) -> str:
        """生成MFA密钥"""
        return pyotp.random_base32()
    
    def verify_mfa_code(self, secret: str, code: str) -> bool:
        """验证MFA代码"""
        if not secret or not code:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    def authenticate_user(self, 
                         username: str, 
                         password: str, 
                         mfa_code: str = None) -> Dict[str, Any]:
        """用户认证（支持MFA）"""
        # 检查速率限制
        if not self.rate_limiter.is_allowed("login", username):
            self.audit_logger.log_event(
                "RATE_LIMIT_EXCEEDED",
                username,
                "login",
                {"reason": "too many login attempts"},
                success=False
            )
            return {"error": "登录尝试次数过多，请稍后再试"}
        
        # 获取用户
        user = self.users.get(username)
        if not user:
            self.audit_logger.log_event(
                "LOGIN_FAILED",
                username,
                "authentication",
                {"reason": "user not found"},
                success=False
            )
            return {"error": "用户名或密码错误"}
        
        # 检查账户是否被锁定
        if user.get("locked_until"):
            locked_until = datetime.fromisoformat(user["locked_until"])
            if locked_until > datetime.now():
                remaining = (locked_until - datetime.now()).seconds
                return {"error": f"账户已被锁定，请{remaining}秒后再试"}
            else:
                # 锁定已过期，重置
                user["locked_until"] = None
                user["failed_login_attempts"] = 0
        
        # 检查账户是否激活
        if not user["is_active"]:
            return {"error": "账户已被禁用"}
        
        # 验证密码
        if not self._verify_password(password, user["password_hash"]):
            # 记录失败尝试
            user["failed_login_attempts"] += 1
            
            # 检查是否应该锁定账户
            if user["failed_login_attempts"] >= 5:
                locked_until = datetime.now() + timedelta(minutes=15)
                user["locked_until"] = locked_until.isoformat()
                self.audit_logger.log_event(
                    "ACCOUNT_LOCKED",
                    username,
                    "authentication",
                    {"failed_attempts": user["failed_login_attempts"]},
                    success=False
                )
                return {"error": "账户因多次失败尝试已被锁定15分钟"}
            
            self.audit_logger.log_event(
                "LOGIN_FAILED",
                username,
                "authentication",
                {"reason": "invalid password", "failed_attempts": user["failed_login_attempts"]},
                success=False
            )
            return {"error": "用户名或密码错误"}
        
        # 验证MFA（如果启用）
        if self.mfa_enabled and user.get("mfa_enabled") and user.get("mfa_secret"):
            if not mfa_code:
                # 需要MFA验证
                return {
                    "requires_mfa": True,
                    "message": "需要多因素认证验证"
                }
            
            if not self.verify_mfa_code(user["mfa_secret"], mfa_code):
                self.audit_logger.log_event(
                    "MFA_FAILED",
                    username,
                    "authentication",
                    {"reason": "invalid mfa code"},
                    success=False
                )
                return {"error": "MFA验证码错误"}
        
        # 认证成功
        user["last_login"] = datetime.now().isoformat()
        user["failed_login_attempts"] = 0
        user["locked_until"] = None
        
        self.audit_logger.log_event(
            "LOGIN_SUCCESS",
            username,
            "authentication",
            {"mfa_used": bool(mfa_code)},
            success=True
        )
        
        return {
            "username": user["username"],
            "role": user["role"],
            "mfa_enabled": user.get("mfa_enabled", False)
        }
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        payload = {
            "sub": user_data["username"],
            "role": user_data["role"],
            "mfa_verified": True if user_data.get("mfa_enabled") else None
        }
        
        # 管理员令牌有效期更长
        expires_in = 7200 if user_data["role"] == "admin" else 1800  # 2小时/30分钟
        
        return self.jwt_manager.create_token(payload, expires_in)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        payload = self.jwt_manager.verify_token(token)
        if not payload:
            return None
        
        # 检查用户是否存在且激活
        username = payload.get("sub")
        user = self.users.get(username)
        if not user or not user["is_active"]:
            return None
        
        return payload
    
    def setup_mfa(self, username: str) -> Dict[str, Any]:
        """为用户设置MFA"""
        user = self.users.get(username)
        if not user:
            return {"error": "用户不存在"}
        
        secret = self.generate_mfa_secret()
        user["mfa_secret"] = secret
        user["mfa_enabled"] = True
        
        # 生成TOTP对象用于获取URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name="ClawAI"
        )
        
        self.audit_logger.log_event(
            "MFA_SETUP",
            username,
            "security",
            {"action": "mfa_enabled"},
            success=True
        )
        
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "message": "请使用身份验证应用（如Google Authenticator）扫描二维码"
        }
    
    def disable_mfa(self, username: str) -> bool:
        """禁用用户的MFA"""
        user = self.users.get(username)
        if not user:
            return False
        
        user["mfa_secret"] = None
        user["mfa_enabled"] = False
        
        self.audit_logger.log_event(
            "MFA_DISABLED",
            username,
            "security",
            {"action": "mfa_disabled"},
            success=True
        )
        
        return True


# 全局高级认证系统实例
auth_system = AdvancedAuthSystem()


def require_advanced_auth(f):
    """高级认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查认证是否启用
        if not config.API_AUTH_ENABLED:
            g.user = {"username": "anonymous", "role": "guest", "auth_type": "anonymous"}
            return f(*args, **kwargs)
        
        # 检查Authorization头
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            # 尝试提取Bearer令牌
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
                # 验证令牌
                payload = auth_system.verify_token(token)
                if payload:
                    # 令牌有效，设置用户信息
                    g.user = {
                        "username": payload.get("sub"),
                        "role": payload.get("role", "user"),
                        "auth_type": "jwt",
                        "mfa_verified": payload.get("mfa_verified", False)
                    }
                    
                    # 检查速率限制
                    if not auth_system.rate_limiter.is_allowed("api", g.user["username"]):
                        auth_system.audit_logger.log_event(
                            "API_RATE_LIMIT",
                            g.user["username"],
                            request.endpoint or "unknown",
                            {"method": request.method, "path": request.path},
                            success=False
                        )
                        return jsonify({"error": "API请求频率过高"}), 429
                    
                    return f(*args, **kwargs)
        
        # 没有有效的令牌，返回401
        auth_system.audit_logger.log_event(
            "UNAUTHORIZED_ACCESS",
            "unknown",
            request.endpoint or "unknown",
            {"method": request.method, "path": request.path, "ip": request.remote_addr},
            success=False
        )
        return jsonify({"error": "缺少有效的认证令牌"}), 401
    
    return decorated_function


def require_role(role: str):
    """角色要求装饰器"""
    def decorator(f):
        @wraps(f)
        @require_advanced_auth
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user'):
                return jsonify({"error": "未认证"}), 401
            
            user_role = g.user.get("role", "guest")
            
            # 角色检查逻辑：admin可以访问所有，user只能访问user和guest的
            role_hierarchy = {"admin": 2, "user": 1, "guest": 0}
            
            if role_hierarchy.get(user_role, -1) < role_hierarchy.get(role, 0):
                auth_system.audit_logger.log_event(
                    "INSUFFICIENT_PERMISSIONS",
                    g.user.get("username", "unknown"),
                    request.endpoint or "unknown",
                    {"required_role": role, "user_role": user_role},
                    success=False
                )
                return jsonify({"error": "权限不足"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def setup_advanced_auth_routes(app):
    """设置高级认证路由"""
    
    @app.route('/auth/advanced/login', methods=['POST'])
    def advanced_login():
        """高级用户登录（支持MFA）"""
        try:
            data = request.json
            if not data or 'username' not in data or 'password' not in data:
                return jsonify({"error": "需要用户名和密码"}), 400
            
            username = data['username']
            password = data['password']
            mfa_code = data.get('mfa_code')
            
            # 认证用户
            auth_result = auth_system.authenticate_user(username, password, mfa_code)
            
            if "error" in auth_result:
                return jsonify(auth_result), 401
            
            if auth_result.get("requires_mfa"):
                # 需要MFA验证
                return jsonify(auth_result), 202  # Accepted
            
            # 生成令牌
            access_token = auth_system.create_access_token(auth_result)
            
            return jsonify({
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 7200 if auth_result["role"] == "admin" else 1800,
                "user": auth_result
            })
        
        except Exception as e:
            auth_system.audit_logger.log_event(
                "LOGIN_ERROR",
                "unknown",
                "authentication",
                {"error": str(e)},
                success=False
            )
            return jsonify({"error": f"登录失败: {str(e)}"}), 500
    
    @app.route('/auth/advanced/me', methods=['GET'])
    @require_advanced_auth
    def get_advanced_current_user():
        """获取当前高级用户信息"""
        username = g.user.get('username')
        role = g.user.get('role')
        
        # 如果是匿名用户（认证未启用）
        if g.user.get("auth_type") == "anonymous":
            return jsonify({
                "user": {
                    "username": "anonymous",
                    "role": "guest",
                    "created_at": datetime.now().isoformat(),
                    "is_active": True,
                    "auth_type": "anonymous",
                    "message": "认证功能未启用，使用匿名访问"
                }
            })
        
        # 获取用户信息
        user_data = auth_system.users.get(username)
        if not user_data:
            return jsonify({"error": "用户不存在"}), 404
        
        # 返回用户信息（排除敏感数据）
        user_info = {
            "username": user_data["username"],
            "role": user_data["role"],
            "mfa_enabled": user_data.get("mfa_enabled", False),
            "created_at": user_data["created_at"],
            "last_login": user_data["last_login"],
            "is_active": user_data["is_active"],
            "auth_type": g.user.get("auth_type", "unknown"),
            "mfa_verified": g.user.get("mfa_verified", False)
        }
        
        return jsonify({
            "user": user_info
        })
    
    @app.route('/auth/advanced/mfa/setup', methods=['POST'])
    @require_advanced_auth
    def setup_user_mfa():
        """设置用户MFA"""
        try:
            username = g.user.get('username')
            
            # 只有已认证用户才能设置MFA
            if not username or username == "anonymous":
                return jsonify({"error": "需要认证用户"}), 401
            
            result = auth_system.setup_mfa(username)
            
            if "error" in result:
                return jsonify(result), 400
            
            return jsonify(result)
        
        except Exception as e:
            auth_system.audit_logger.log_event(
                "MFA_SETUP_ERROR",
                g.user.get('username', 'unknown'),
                "security",
                {"error": str(e)},
                success=False
            )
            return jsonify({"error": f"MFA设置失败: {str(e)}"}), 500
    
    @app.route('/auth/advanced/mfa/verify', methods=['POST'])
    @require_advanced_auth
    def verify_mfa():
        """验证MFA代码（用于登录后的验证）"""
        try:
            data = request.json
            if not data or 'mfa_code' not in data:
                return jsonify({"error": "需要MFA验证码"}), 400
            
            username = g.user.get('username')
            user_data = auth_system.users.get(username)
            
            if not user_data or not user_data.get("mfa_secret"):
                return jsonify({"error": "用户未启用MFA"}), 400
            
            mfa_code = data['mfa_code']
            
            if auth_system.verify_mfa_code(user_data["mfa_secret"], mfa_code):
                # 更新用户会话中的MFA验证状态
                g.user["mfa_verified"] = True
                
                auth_system.audit_logger.log_event(
                    "MFA_VERIFIED",
                    username,
                    "security",
                    {"action": "mfa_verification"},
                    success=True
                )
                
                return jsonify({"success": True, "message": "MFA验证成功"})
            else:
                auth_system.audit_logger.log_event(
                    "MFA_VERIFICATION_FAILED",
                    username,
                    "security",
                    {"action": "mfa_verification"},
                    success=False
                )
                return jsonify({"error": "MFA验证码错误"}), 401
        
        except Exception as e:
            auth_system.audit_logger.log_event(
                "MFA_VERIFICATION_ERROR",
                g.user.get('username', 'unknown'),
                "security",
                {"error": str(e)},
                success=False
            )
            return jsonify({"error": f"MFA验证失败: {str(e)}"}), 500
    
    @app.route('/auth/advanced/mfa/disable', methods=['POST'])
    @require_advanced_auth
    def disable_user_mfa():
        """禁用用户MFA"""
        try:
            username = g.user.get('username')
            
            if not username or username == "anonymous":
                return jsonify({"error": "需要认证用户"}), 401
            
            success = auth_system.disable_mfa(username)
            
            if success:
                return jsonify({"success": True, "message": "MFA已禁用"})
            else:
                return jsonify({"error": "禁用MFA失败"}), 400
        
        except Exception as e:
            auth_system.audit_logger.log_event(
                "MFA_DISABLE_ERROR",
                g.user.get('username', 'unknown'),
                "security",
                {"error": str(e)},
                success=False
            )
            return jsonify({"error": f"禁用MFA失败: {str(e)}"}), 500
    
    @app.route('/auth/advanced/stats', methods=['GET'])
    @require_role("admin")
    def get_auth_stats():
        """获取认证统计信息（仅管理员）"""
        try:
            stats = {
                "total_users": len(auth_system.users),
                "active_users": sum(1 for u in auth_system.users.values() if u["is_active"]),
                "mfa_enabled_users": sum(1 for u in auth_system.users.values() if u.get("mfa_enabled")),
                "locked_users": sum(1 for u in auth_system.users.values() if u.get("locked_until") and datetime.fromisoformat(u["locked_until"]) > datetime.now()),
                "rate_limiting_enabled": auth_system.rate_limiter.redis is not None
            }
            
            return jsonify(stats)
        
        except Exception as e:
            return jsonify({"error": f"获取统计信息失败: {str(e)}"}), 500
    
    return app


if __name__ == "__main__":
    # 测试高级认证模块
    print("测试高级认证模块...")
    
    # 创建测试应用
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # 设置路由
    setup_advanced_auth_routes(app)
    
    # 基本测试
    print("\n1. 基本认证测试:")
    
    # 测试认证
    with app.test_client() as client:
        # 测试登录
        response = client.post('/auth/advanced/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response.status_code == 202:
            print("  需要MFA验证 (预期中)")
        elif response.status_code == 200:
            data = response.get_json()
            print(f"  登录成功: {data.get('access_token')[:20]}...")
            
            # 测试获取用户信息
            headers = {'Authorization': f"Bearer {data['access_token']}"}
            response = client.get('/auth/advanced/me', headers=headers)
            print(f"  获取用户信息: {response.status_code}")
        else:
            print(f"  登录失败: {response.status_code}, {response.get_json()}")
    
    print("\n2. 速率限制测试:")
    for i in range(3):
        allowed = auth_system.rate_limiter.is_allowed("test", "test_user", 5, 10)
        print(f"  请求 {i+1}: {'允许' if allowed else '拒绝'}")
    
    print("\n3. 审计日志测试:")
    auth_system.audit_logger.log_event(
        "TEST_EVENT",
        "test_user",
        "test_action",
        {"test": "data"},
        success=True,
        ip_address="127.0.0.1"
    )
    print("  审计日志记录成功")
    
    print("\n高级认证模块测试完成！")