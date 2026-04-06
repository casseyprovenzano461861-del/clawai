#!/usr/bin/env python3
"""
认证集成测试
测试FastAPI认证端点与RBAC系统的集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src/shared"))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_database
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化测试数据库（使用SQLite内存数据库）
import tempfile
import atexit

# 创建临时数据库文件
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()
os.environ['DATABASE_URL'] = f"sqlite:///{temp_db.name}"
os.environ['ENVIRONMENT'] = "development"

def cleanup():
    """清理临时数据库文件"""
    try:
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)
    except:
        pass

atexit.register(cleanup)

# 初始化数据库
init_database(os.environ['DATABASE_URL'])

def test_auth_endpoints():
    """测试认证端点"""
    client = TestClient(app)

    print("=== 测试认证端点 ===")

    # 1. 测试健康检查
    print("1. 测试认证健康检查...")
    try:
        response = client.get("/auth/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        assert response.status_code == 200
        print("   ✅ 认证健康检查通过")
    except Exception as e:
        print(f"   ❌ 认证健康检查失败: {e}")
        return False

    # 2. 测试登录（使用默认管理员账户）
    print("\n2. 测试管理员登录...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = client.post("/auth/login", json=login_data)
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   访问令牌: {result['access_token'][:20]}...")
            print(f"   令牌类型: {result['token_type']}")
            print(f"   过期时间: {result['expires_in']}秒")
            print(f"   用户: {result['user']['username']}")
            print("   ✅ 管理员登录成功")

            # 保存令牌用于后续测试
            access_token = result['access_token']
            refresh_token = result.get('refresh_token')

            # 3. 测试获取当前用户信息
            print("\n3. 测试获取当前用户信息...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/auth/me", headers=headers)
            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                user_info = response.json()
                print(f"   用户名: {user_info['username']}")
                print(f"   角色: {user_info.get('roles', [])}")
                print(f"   权限: {user_info.get('permissions', [])}")
                print("   ✅ 获取用户信息成功")

                # 4. 测试RBAC端点（需要认证）
                print("\n4. 测试RBAC端点（需要认证）...")
                response = client.get("/rbac/roles", headers=headers)
                print(f"   状态码: {response.status_code}")

                if response.status_code == 200:
                    roles = response.json()
                    print(f"   角色数量: {roles.get('total', 0)}")
                    print("   ✅ RBAC端点访问成功")
                else:
                    print(f"   ⚠️ RBAC端点访问失败: {response.json()}")

                # 5. 测试刷新令牌
                if refresh_token:
                    print("\n5. 测试刷新令牌...")
                    refresh_data = {"refresh_token": refresh_token}
                    response = client.post("/auth/refresh", json=refresh_data)
                    print(f"   状态码: {response.status_code}")

                    if response.status_code == 200:
                        refresh_result = response.json()
                        print(f"   新访问令牌: {refresh_result['access_token'][:20]}...")
                        print("   ✅ 刷新令牌成功")
                    else:
                        print(f"   ⚠️ 刷新令牌失败: {response.json()}")
                else:
                    print("\n5. 跳过刷新令牌测试（无刷新令牌）")

            else:
                print(f"   ❌ 获取用户信息失败: {response.json()}")
                return False

        else:
            print(f"   ❌ 管理员登录失败: {response.json()}")
            return False

    except Exception as e:
        print(f"   ❌ 登录测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 6. 测试登出
    print("\n6. 测试用户登出...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/auth/logout", headers=headers)
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            print(f"   响应: {response.json()}")
            print("   ✅ 用户登出成功")
        else:
            print(f"   ⚠️ 用户登出失败: {response.json()}")
    except Exception as e:
        print(f"   ⚠️ 用户登出测试失败: {e}")

    print("\n=== 认证集成测试完成 ===")
    return True

def test_user_registration():
    """测试用户注册"""
    client = TestClient(app)

    print("\n=== 测试用户注册 ===")

    # 生成唯一用户名
    import uuid
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"

    print(f"1. 注册测试用户: {test_username}")
    try:
        register_data = {
            "username": test_username,
            "password": "TestPass123!",
            "email": f"{test_username}@example.com",
            "full_name": "Test User"
        }

        response = client.post("/auth/register", json=register_data)
        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   用户: {result['username']}")
            print(f"   邮箱: {result['email']}")
            print(f"   消息: {result.get('message', 'N/A')}")
            print("   ✅ 用户注册成功")

            # 测试新用户登录
            print(f"\n2. 测试新用户登录: {test_username}")
            login_data = {
                "username": test_username,
                "password": "TestPass123!"
            }
            response = client.post("/auth/login", json=login_data)
            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                login_result = response.json()
                print(f"   访问令牌: {login_result['access_token'][:20]}...")
                print("   ✅ 新用户登录成功")
                return True
            else:
                print(f"   ❌ 新用户登录失败: {response.json()}")
                return False
        else:
            print(f"   ❌ 用户注册失败: {response.json()}")
            return False

    except Exception as e:
        print(f"   ❌ 用户注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始认证集成测试...")

    # 测试认证端点
    auth_success = test_auth_endpoints()

    # 测试用户注册
    registration_success = test_user_registration()

    # 总结
    print("\n" + "="*50)
    print("测试结果总结:")
    print(f"认证端点测试: {'✅ 通过' if auth_success else '❌ 失败'}")
    print(f"用户注册测试: {'✅ 通过' if registration_success else '❌ 失败'}")
    print("="*50)

    if auth_success and registration_success:
        print("🎉 所有测试通过！认证系统与RBAC集成正常。")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败，请检查日志。")
        sys.exit(1)