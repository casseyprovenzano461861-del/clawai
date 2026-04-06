"""
密码哈希和验证工具
使用passlib的bcrypt进行安全密码哈希
"""

import os
from passlib.context import CryptContext
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# 密码上下文配置
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # 适当的工作因子
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        布尔值，表示密码是否匹配
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    return pwd_context.hash(password)


def is_password_strong(password: str) -> Tuple[bool, Optional[str]]:
    """
    检查密码强度

    Args:
        password: 密码字符串

    Returns:
        (是否强密码, 错误消息)
    """
    if len(password) < 8:
        return False, "密码长度至少8个字符"

    if len(password) > 128:
        return False, "密码长度不能超过128个字符"

    # 检查字符类型
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password)

    if not has_lower:
        return False, "密码必须包含小写字母"

    if not has_upper:
        return False, "密码必须包含大写字母"

    if not has_digit:
        return False, "密码必须包含数字"

    if not has_special:
        return False, "密码必须包含特殊字符"

    # 检查常见弱密码
    weak_passwords = [
        "password", "12345678", "qwerty", "admin123", "letmein",
        "welcome", "monkey", "sunshine", "password1"
    ]

    if password.lower() in weak_passwords:
        return False, "密码太常见，请使用更复杂的密码"

    return True, None


def generate_secure_password(length: int = 16) -> str:
    """
    生成安全随机密码

    Args:
        length: 密码长度

    Returns:
        随机生成的密码
    """
    import secrets
    import string

    if length < 12:
        length = 12

    # 字符集
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        strong, _ = is_password_strong(password)
        if strong:
            return password


def needs_rehash(hashed_password: str) -> bool:
    """
    检查密码是否需要重新哈希（例如，当哈希算法更新时）

    Args:
        hashed_password: 哈希后的密码

    Returns:
        布尔值，表示是否需要重新哈希
    """
    return pwd_context.needs_update(hashed_password)