# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI 简化认证模块单元测试
"""

import unittest
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.auth_simple import SimpleAuthManager, auth_manager


class TestSimpleAuthManager(unittest.TestCase):
    """测试简化认证管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.auth_manager = SimpleAuthManager()
    
    def test_password_hashing(self):
        """测试密码哈希"""
        # 测试哈希函数
        password = "test_password123"
        hashed = self.auth_manager._simple_hash(password)
        self.assertIsInstance(hashed, str)
        self.assertEqual(len(hashed), 64)  # SHA256哈希长度
        
        # 测试验证函数
        is_valid = self.auth_manager._verify_password(password, hashed)
        self.assertTrue(is_valid)
        
        # 测试错误密码
        is_invalid = self.auth_manager._verify_password("wrong_password", hashed)
        self.assertFalse(is_invalid)
    
    def test_user_authentication(self):
        """测试用户认证"""
        # 测试管理员认证
        auth_result = self.auth_manager.authenticate_user("admin", "admin123")
        self.assertIsNotNone(auth_result)
        self.assertEqual(auth_result["username"], "admin")
        self.assertEqual(auth_result["role"], "admin")
        
        # 测试demo用户认证
        demo_auth = self.auth_manager.authenticate_user("demo", "demo123")
        self.assertIsNotNone(demo_auth)
        self.assertEqual(demo_auth["username"], "demo")
        self.assertEqual(demo_auth["role"], "user")
        
        # 测试错误密码
        wrong_auth = self.auth_manager.authenticate_user("admin", "wrong_password")
        self.assertIsNone(wrong_auth)
        
        # 测试不存在的用户
        nonexistent_auth = self.auth_manager.authenticate_user("nonexistent_user", "password")
        self.assertIsNone(nonexistent_auth)
    
    def test_token_creation_and_verification(self):
        """测试令牌创建和验证"""
        # 创建访问令牌
        access_token = self.auth_manager.create_access_token("test_user", "user")
        self.assertIsInstance(access_token, str)
        self.assertTrue(len(access_token) > 0)
        self.assertIn('.', access_token)  # 应该包含点号分隔符
        
        # 验证令牌
        payload = self.auth_manager.verify_token(access_token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("sub"), "test_user")
        self.assertEqual(payload.get("role"), "user")
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)
        
        # 测试无效令牌
        invalid_token = "invalid.token.here"
        invalid_payload = self.auth_manager.verify_token(invalid_token)
        self.assertIsNone(invalid_payload)
        
        # 测试格式错误的令牌
        malformed_token = "not_a_valid_token"
        malformed_payload = self.auth_manager.verify_token(malformed_token)
        self.assertIsNone(malformed_payload)
    
    def test_get_user(self):
        """测试获取用户信息"""
        # 获取管理员用户信息
        admin_info = self.auth_manager.get_user("admin")
        self.assertIsNotNone(admin_info)
        self.assertEqual(admin_info["username"], "admin")
        self.assertEqual(admin_info["role"], "admin")
        self.assertTrue(admin_info["is_active"])
        self.assertIn("created_at", admin_info)
        
        # 获取demo用户信息
        demo_info = self.auth_manager.get_user("demo")
        self.assertIsNotNone(demo_info)
        self.assertEqual(demo_info["username"], "demo")
        self.assertEqual(demo_info["role"], "user")
        self.assertTrue(demo_info["is_active"])
        self.assertIn("created_at", demo_info)
        
        # 测试不存在的用户
        nonexistent_user = self.auth_manager.get_user("nonexistent_user")
        self.assertIsNone(nonexistent_user)
    
    def test_default_users(self):
        """测试默认用户"""
        # 检查默认用户是否存在
        self.assertIn("admin", self.auth_manager.users)
        self.assertIn("demo", self.auth_manager.users)
        
        # 检查管理员用户属性
        admin_user = self.auth_manager.users["admin"]
        self.assertEqual(admin_user["role"], "admin")
        self.assertTrue(admin_user["is_active"])
        
        # 检查demo用户属性
        demo_user = self.auth_manager.users["demo"]
        self.assertEqual(demo_user["role"], "user")
        self.assertTrue(demo_user["is_active"])


class TestGlobalAuthManager(unittest.TestCase):
    """测试全局认证管理器实例"""
    
    def test_singleton_instance(self):
        """测试单例实例"""
        # 验证全局实例存在
        self.assertIsNotNone(auth_manager)
        self.assertIsInstance(auth_manager, SimpleAuthManager)
        
        # 验证默认用户存在
        self.assertIn("admin", auth_manager.users)
        self.assertIn("demo", auth_manager.users)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)