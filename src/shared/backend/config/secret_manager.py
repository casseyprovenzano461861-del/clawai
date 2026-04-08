# -*- coding: utf-8 -*-
"""
API Key 安全管理器
使用 Fernet 对称加密存储敏感信息
"""

import os
import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretManager:
    """
    敏感信息安全管理器

    使用 Fernet 对称加密存储 API Key 等敏感信息
    支持从环境变量、加密文件、内存存储中读取
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        encrypted_file: Optional[str] = None
    ):
        """
        初始化安全管理器

        Args:
            secret_key: 加密密钥（如果不提供，从环境变量 CLAWAI_SECRET_KEY 读取）
            encrypted_file: 加密存储文件路径
        """
        self._secret_key = secret_key or os.getenv("CLAWAI_SECRET_KEY")
        self._encrypted_file = encrypted_file or os.getenv(
            "CLAWAI_SECRETS_FILE",
            str(Path.home() / ".clawai" / "secrets.enc")
        )
        self._fernet: Optional[Fernet] = None
        self._memory_cache: Dict[str, str] = {}

        # 初始化加密器
        self._init_fernet()

    def _init_fernet(self) -> None:
        """初始化 Fernet 加密器"""
        if self._secret_key:
            try:
                # 从密钥派生 Fernet 密钥
                key = self._derive_key(self._secret_key)
                self._fernet = Fernet(key)
                logger.debug("Fernet 加密器初始化成功")
            except Exception as e:
                logger.warning(f"Fernet 初始化失败: {e}")
                self._fernet = None
        else:
            logger.info("未配置 CLAWAI_SECRET_KEY，敏感信息将仅存储在内存中")

    def _derive_key(self, password: str, salt: bytes = b"ClawAI_Secret_Salt_2024") -> bytes:
        """
        从密码派生加密密钥

        Args:
            password: 密码字符串
            salt: 盐值

        Returns:
            Fernet 兼容的密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串

        Args:
            plaintext: 明文字符串

        Returns:
            加密后的字符串（Base64编码）
        """
        if not self._fernet:
            raise RuntimeError("Fernet 加密器未初始化，请设置 CLAWAI_SECRET_KEY")

        encrypted = self._fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串

        Args:
            ciphertext: 密文字符串（Base64编码）

        Returns:
            解密后的明文
        """
        if not self._fernet:
            raise RuntimeError("Fernet 加密器未初始化，请设置 CLAWAI_SECRET_KEY")

        decrypted = self._fernet.decrypt(ciphertext.encode())
        return decrypted.decode()

    def store_api_key(self, provider: str, api_key: str) -> None:
        """
        存储 API Key

        Args:
            provider: 提供商名称（如 deepseek, openai, azure）
            api_key: API Key 明文
        """
        # 内存缓存
        self._memory_cache[f"api_key_{provider}"] = api_key

        # 如果支持加密，写入加密文件
        if self._fernet:
            try:
                encrypted = self.encrypt(api_key)
                self._save_to_file(provider, encrypted)
                logger.info(f"API Key 已加密存储: {provider}")
            except Exception as e:
                logger.error(f"存储 API Key 失败: {e}")

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        获取 API Key

        优先级：内存缓存 -> 加密文件 -> 环境变量

        Args:
            provider: 提供商名称

        Returns:
            API Key 明文或 None
        """
        # 1. 检查内存缓存
        cache_key = f"api_key_{provider}"
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # 2. 检查加密文件
        if self._fernet:
            try:
                encrypted = self._load_from_file(provider)
                if encrypted:
                    decrypted = self.decrypt(encrypted)
                    self._memory_cache[cache_key] = decrypted
                    return decrypted
            except Exception as e:
                logger.warning(f"读取加密文件失败: {e}")

        # 3. 检查环境变量（兼容现有配置）
        env_key = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        if api_key:
            self._memory_cache[cache_key] = api_key
            return api_key

        # 兼容特殊变量名
        special_envs = {
            "deepseek": ["DEEPSEEK_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "azure": ["AZURE_OPENAI_API_KEY"],
        }
        for env_name in special_envs.get(provider.lower(), []):
            api_key = os.getenv(env_name)
            if api_key:
                self._memory_cache[cache_key] = api_key
                return api_key

        return None

    def delete_api_key(self, provider: str) -> bool:
        """
        删除 API Key

        Args:
            provider: 提供商名称

        Returns:
            是否成功删除
        """
        # 清除内存缓存
        cache_key = f"api_key_{provider}"
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        # 清除文件存储
        if self._fernet:
            try:
                self._delete_from_file(provider)
                return True
            except Exception as e:
                logger.error(f"删除 API Key 失败: {e}")
                return False

        return True

    def list_stored_providers(self) -> list:
        """
        列出已存储的提供商

        Returns:
            提供商名称列表
        """
        providers = set()

        # 从内存缓存获取
        for key in self._memory_cache:
            if key.startswith("api_key_"):
                providers.add(key[8:])

        # 从文件获取
        if self._fernet:
            try:
                data = self._load_all_from_file()
                providers.update(data.keys())
            except Exception:
                pass

        return list(providers)

    def _save_to_file(self, provider: str, encrypted_value: str) -> None:
        """保存到加密文件"""
        import json

        file_path = Path(self._encrypted_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有数据
        data = {}
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            except Exception:
                pass

        # 更新数据
        data[provider] = encrypted_value

        # 写入文件
        with open(file_path, 'w') as f:
            json.dump(data, f)

        logger.debug(f"已保存到文件: {file_path}")

    def _load_from_file(self, provider: str) -> Optional[str]:
        """从文件读取"""
        import json

        file_path = Path(self._encrypted_file)
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get(provider)
        except Exception:
            return None

    def _load_all_from_file(self) -> Dict[str, str]:
        """从文件读取所有数据"""
        import json

        file_path = Path(self._encrypted_file)
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _delete_from_file(self, provider: str) -> None:
        """从文件删除"""
        import json

        file_path = Path(self._encrypted_file)
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            if provider in data:
                del data[provider]

            with open(file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"删除失败: {e}")


# 全局实例
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """获取全局安全管理器实例"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


def store_api_key(provider: str, api_key: str) -> None:
    """快捷方法：存储 API Key"""
    get_secret_manager().store_api_key(provider, api_key)


def get_api_key(provider: str) -> Optional[str]:
    """快捷方法：获取 API Key"""
    return get_secret_manager().get_api_key(provider)
