"""
tests/unit/test_auth.py

AuthenticationManager 单元测试
覆盖 JWT 令牌生成/验证、密码哈希/验证、边界情况
"""

import os
import time
import pytest
from datetime import timedelta


# 设置已知密钥，确保测试确定性
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-for-unit-tests"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["JWT_REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

from src.shared.backend.auth.authentication import AuthenticationManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth():
    """每次测试使用独立的 AuthenticationManager 实例"""
    return AuthenticationManager()


# ---------------------------------------------------------------------------
# JWT 令牌生成
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCreateAccessToken:
    """create_access_token 测试"""

    def test_returns_non_empty_string(self, auth):
        token = auth.create_access_token({"sub": "user1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_type_access(self, auth):
        token = auth.create_access_token({"sub": "user1"})
        payload = auth.verify_token(token)
        assert payload.get("type") == "access"

    def test_preserves_custom_claims(self, auth):
        token = auth.create_access_token({"sub": "user1", "role": "admin"})
        payload = auth.verify_token(token)
        assert payload["sub"] == "user1"
        assert payload["role"] == "admin"

    def test_contains_exp_claim(self, auth):
        token = auth.create_access_token({"sub": "user1"})
        payload = auth.verify_token(token)
        assert "exp" in payload

    def test_custom_expires_delta(self, auth):
        delta = timedelta(minutes=5)
        token = auth.create_access_token({"sub": "user1"}, expires_delta=delta)
        payload = auth.verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "user1"

    def test_does_not_mutate_input_data(self, auth):
        data = {"sub": "user1"}
        original = data.copy()
        auth.create_access_token(data)
        assert data == original


@pytest.mark.unit
class TestCreateRefreshToken:
    """create_refresh_token 测试"""

    def test_returns_non_empty_string(self, auth):
        token = auth.create_refresh_token({"sub": "user1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_type_refresh(self, auth):
        token = auth.create_refresh_token({"sub": "user1"})
        payload = auth.verify_token(token)
        assert payload.get("type") == "refresh"

    def test_preserves_custom_claims(self, auth):
        token = auth.create_refresh_token({"sub": "user1", "session": "abc"})
        payload = auth.verify_token(token)
        assert payload["sub"] == "user1"
        assert payload["session"] == "abc"

    def test_contains_exp_claim(self, auth):
        token = auth.create_refresh_token({"sub": "user1"})
        payload = auth.verify_token(token)
        assert "exp" in payload


# ---------------------------------------------------------------------------
# JWT 令牌验证
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestVerifyToken:
    """verify_token 测试"""

    def test_valid_access_token(self, auth):
        token = auth.create_access_token({"sub": "user1"})
        payload = auth.verify_token(token)
        assert payload["sub"] == "user1"
        assert payload["type"] == "access"

    def test_valid_refresh_token(self, auth):
        token = auth.create_refresh_token({"sub": "user1"})
        payload = auth.verify_token(token)
        assert payload["sub"] == "user1"
        assert payload["type"] == "refresh"

    def test_empty_string_returns_empty_dict(self, auth):
        result = auth.verify_token("")
        assert result == {}

    def test_none_token_returns_empty_dict(self, auth):
        result = auth.verify_token(None)
        assert result == {}

    def test_malformed_token_returns_empty_dict(self, auth):
        result = auth.verify_token("not.a.valid.token")
        assert result == {}

    def test_random_string_returns_empty_dict(self, auth):
        result = auth.verify_token("completely_invalid_token_string")
        assert result == {}

    def test_wrong_secret_returns_empty_dict(self):
        """用不同密钥创建的 token 无法验证"""
        auth_a = AuthenticationManager()
        auth_a._secret_key = "secret_key_A_that_is_long_enough_for_hs256"

        auth_b = AuthenticationManager()
        auth_b._secret_key = "secret_key_B_that_is_long_enough_for_hs256"

        token = auth_a.create_access_token({"sub": "user1"})
        result = auth_b.verify_token(token)
        assert result == {}

    def test_expired_token_returns_empty_dict(self, auth):
        """已过期的令牌返回空 dict"""
        token = auth.create_access_token(
            {"sub": "user1"},
            expires_delta=timedelta(seconds=-1),
        )
        result = auth.verify_token(token)
        assert result == {}


# ---------------------------------------------------------------------------
# 令牌类型区分
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenTypeDistinction:
    """验证 access 和 refresh 令牌类型可区分"""

    def test_access_and_refresh_are_different(self, auth):
        access = auth.create_access_token({"sub": "user1"})
        refresh = auth.create_refresh_token({"sub": "user1"})
        assert access != refresh

    def test_can_distinguish_type_from_payload(self, auth):
        access = auth.create_access_token({"sub": "user1"})
        refresh = auth.create_refresh_token({"sub": "user1"})

        access_payload = auth.verify_token(access)
        refresh_payload = auth.verify_token(refresh)

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


# ---------------------------------------------------------------------------
# 密码哈希
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestHashPassword:
    """hash_password 测试"""

    def test_returns_non_empty_string(self, auth):
        hashed = auth.hash_password("secure_password")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_different_passwords_produce_different_hashes(self, auth):
        h1 = auth.hash_password("password1")
        h2 = auth.hash_password("password2")
        assert h1 != h2

    def test_same_password_produces_different_hashes(self, auth):
        """bcrypt 自动加盐，相同密码产生不同哈希"""
        h1 = auth.hash_password("same_password")
        h2 = auth.hash_password("same_password")
        assert h1 != h2


@pytest.mark.unit
class TestVerifyPassword:
    """verify_password 测试"""

    def test_correct_password(self, auth):
        hashed = auth.hash_password("my_password")
        assert auth.verify_password("my_password", hashed) is True

    def test_wrong_password(self, auth):
        hashed = auth.hash_password("my_password")
        assert auth.verify_password("wrong_password", hashed) is False

    def test_empty_plain_password(self, auth):
        hashed = auth.hash_password("")
        assert auth.verify_password("", hashed) is True

    def test_empty_hash_returns_false(self, auth):
        assert auth.verify_password("any_password", "") is False

    def test_malformed_hash_returns_false(self, auth):
        assert auth.verify_password("password", "not_a_bcrypt_hash") is False
