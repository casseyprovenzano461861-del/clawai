"""
敏感数据脱敏管理器
P0-9: 敏感信息脱敏处理

提供统一的敏感信息脱敏功能，防止敏感信息在日志、审计记录和API响应中泄露。
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Pattern, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class SensitiveDataType(str, Enum):
    """敏感数据类型枚举"""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    SECRET = "secret"
    PRIVATE_KEY = "private_key"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"  # 社会安全号码
    PHONE = "phone"
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    JWT_TOKEN = "jwt_token"
    DATABASE_URL = "database_url"
    SSH_KEY = "ssh_key"
    AWS_KEY = "aws_key"
    AZURE_KEY = "azure_key"
    GCP_KEY = "gcp_key"
    OPENAI_KEY = "openai_key"


@dataclass
class SensitivePattern:
    """敏感信息模式定义"""
    name: str
    pattern: str
    data_type: SensitiveDataType
    replacement: str = "***REDACTED***"
    description: str = ""
    priority: int = 10  # 优先级，数字越小优先级越高
    compiled_pattern: Optional[Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """编译正则表达式模式"""
        try:
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            logger.error(f"正则表达式编译失败: {self.pattern}, 错误: {e}")
            # 使用一个安全的回退模式
            self.compiled_pattern = re.compile(r"$^")  # 永远不匹配


class SensitiveDataManager:
    """敏感数据管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化敏感数据管理器

        Args:
            config: 配置字典，可以包含自定义模式等
        """
        self.config = config or {}
        self.patterns: List[SensitivePattern] = []
        self._initialize_patterns()

        # 敏感字段名（不基于模式，基于字段名）
        self.sensitive_field_names = {
            "password", "pwd", "passwd", "secret", "token", "api_key", "api-key",
            "secret_key", "secret-key", "jwt", "access_token", "refresh_token",
            "private_key", "private-key", "ssh_key", "ssh-key", "aws_key",
            "aws-key", "azure_key", "azure-key", "gcp_key", "gcp-key",
            "openai_key", "openai-key", "database_url", "db_url",
            "credit_card", "credit-card", "cc_number", "ssn", "social_security",
            "phone", "telephone", "mobile", "email", "username"
        }

        # 配置选项
        self.enable_field_name_detection = self.config.get("enable_field_name_detection", True)
        self.enable_pattern_detection = self.config.get("enable_pattern_detection", True)
        self.redaction_string = self.config.get("redaction_string", "***REDACTED***")
        self.max_context_chars = self.config.get("max_context_chars", 50)  # 保留的上下文字符数

        logger.info(f"敏感数据管理器初始化完成，加载了 {len(self.patterns)} 个模式")

    def _initialize_patterns(self) -> None:
        """初始化敏感信息模式"""
        patterns = [
            # API密钥模式
            SensitivePattern(
                name="openai_api_key",
                pattern=r'sk-[a-zA-Z0-9]{24,}',
                data_type=SensitiveDataType.OPENAI_KEY,
                replacement="sk-***",
                description="OpenAI API密钥",
                priority=1
            ),
            SensitivePattern(
                name="generic_api_key",
                pattern=r'[aA][pP][iI][_-]?[kK]e[yY]\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?',
                data_type=SensitiveDataType.API_KEY,
                replacement='api_key=***',
                description="通用API密钥",
                priority=5
            ),

            # 认证令牌模式
            SensitivePattern(
                name="jwt_token",
                pattern=r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
                data_type=SensitiveDataType.JWT_TOKEN,
                replacement="JWT_TOKEN",
                description="JWT令牌",
                priority=2
            ),
            SensitivePattern(
                name="bearer_token",
                pattern=r'[bB]earer\s+[a-zA-Z0-9._-]{20,}',
                data_type=SensitiveDataType.TOKEN,
                replacement="Bearer ***",
                description="Bearer令牌",
                priority=3
            ),

            # 密码模式
            SensitivePattern(
                name="password_field",
                pattern=r'[pP]assword\s*[=:]\s*["\']?([^"\'\s]{4,})["\']?',
                data_type=SensitiveDataType.PASSWORD,
                replacement='password=***',
                description="密码字段",
                priority=4
            ),
            SensitivePattern(
                name="pwd_field",
                pattern=r'[pP]wd\s*[=:]\s*["\']?([^"\'\s]{4,})["\']?',
                data_type=SensitiveDataType.PASSWORD,
                replacement='pwd=***',
                description="密码字段缩写",
                priority=4
            ),

            # 密钥模式
            SensitivePattern(
                name="secret_field",
                pattern=r'[sS]ecret\s*[=:]\s*["\']?([^"\'\s]{8,})["\']?',
                data_type=SensitiveDataType.SECRET,
                replacement='secret=***',
                description="密钥字段",
                priority=4
            ),

            # 私钥模式
            SensitivePattern(
                name="private_key",
                pattern=r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----[\s\S]*?-----END \1 PRIVATE KEY-----',
                data_type=SensitiveDataType.PRIVATE_KEY,
                replacement='***PRIVATE_KEY***',
                description="私钥文件",
                priority=1
            ),
            SensitivePattern(
                name="ssh_key",
                pattern=r'[sS][sS][hH][_-]?[kK]e[yY]\s*[=:]\s*["\']?([^"\'\s]{20,})["\']?',
                data_type=SensitiveDataType.SSH_KEY,
                replacement='ssh_key=***',
                description="SSH密钥",
                priority=5
            ),

            # 数据库连接字符串
            SensitivePattern(
                name="postgres_url",
                pattern=r'postgres(ql)?://[^:@]+:[^@]+@',
                data_type=SensitiveDataType.DATABASE_URL,
                replacement='postgres://***:***@',
                description="PostgreSQL连接字符串",
                priority=3
            ),
            SensitivePattern(
                name="mysql_url",
                pattern=r'mysql://[^:@]+:[^@]+@',
                data_type=SensitiveDataType.DATABASE_URL,
                replacement='mysql://***:***@',
                description="MySQL连接字符串",
                priority=3
            ),
            SensitivePattern(
                name="redis_url",
                pattern=r'redis://[^:@]+:[^@]+@',
                data_type=SensitiveDataType.DATABASE_URL,
                replacement='redis://***:***@',
                description="Redis连接字符串",
                priority=3
            ),

            # 云服务密钥
            SensitivePattern(
                name="aws_key",
                pattern=r'AKIA[0-9A-Z]{16}',
                data_type=SensitiveDataType.AWS_KEY,
                replacement='AKIA***',
                description="AWS访问密钥",
                priority=2
            ),
            SensitivePattern(
                name="azure_key",
                pattern=r'[aA]zure[_-]?[kK]e[yY]\s*[=:]\s*["\']?([^"\'\s]{32,})["\']?',
                data_type=SensitiveDataType.AZURE_KEY,
                replacement='azure_key=***',
                description="Azure密钥",
                priority=5
            ),
            SensitivePattern(
                name="gcp_key",
                pattern=r'AIza[0-9A-Za-z-_]{35}',
                data_type=SensitiveDataType.GCP_KEY,
                replacement='AIza***',
                description="GCP API密钥",
                priority=2
            ),

            # 个人身份信息 (PII)
            SensitivePattern(
                name="credit_card",
                pattern=r'\b(?:\d[ -]*?){13,16}\b',
                data_type=SensitiveDataType.CREDIT_CARD,
                replacement='***CREDIT_CARD***',
                description="信用卡号",
                priority=3
            ),
            SensitivePattern(
                name="ssn",
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                data_type=SensitiveDataType.SSN,
                replacement='***SSN***',
                description="社会安全号码",
                priority=3
            ),
            SensitivePattern(
                name="phone",
                pattern=r'\b\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
                data_type=SensitiveDataType.PHONE,
                replacement='***PHONE***',
                description="电话号码",
                priority=4
            ),
            SensitivePattern(
                name="email",
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                data_type=SensitiveDataType.EMAIL,
                replacement='***EMAIL***',
                description="电子邮件地址",
                priority=5
            ),

            # IP地址（在某些上下文中可能是敏感的）
            SensitivePattern(
                name="ip_address",
                pattern=r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                data_type=SensitiveDataType.IP_ADDRESS,
                replacement='***IP***',
                description="IP地址",
                priority=10  # 低优先级，因为IP地址不总是敏感的
            ),
        ]

        # 按优先级排序
        self.patterns = sorted(patterns, key=lambda x: x.priority)

    def redact_text(self, text: str, context: Optional[str] = None) -> str:
        """
        脱敏文本中的敏感信息

        Args:
            text: 要脱敏的文本
            context: 上下文信息，用于日志记录

        Returns:
            脱敏后的文本
        """
        if not text or not isinstance(text, str):
            return text

        redacted = text

        # 使用模式检测
        if self.enable_pattern_detection:
            for pattern in self.patterns:
                if pattern.compiled_pattern:
                    try:
                        redacted = pattern.compiled_pattern.sub(pattern.replacement, redacted)
                    except Exception as e:
                        logger.warning(f"模式脱敏失败: {pattern.name}, 错误: {e}")

        # 如果文本完全未改变，返回原文本
        if redacted == text:
            return text

        # 记录脱敏操作（如果需要）
        if context:
            logger.debug(f"敏感信息脱敏: 上下文={context}, 原长度={len(text)}, 脱敏后长度={len(redacted)}")

        return redacted

    def redact_dict(self, data: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        脱敏字典中的敏感信息

        Args:
            data: 要脱敏的字典
            context: 上下文信息

        Returns:
            脱敏后的字典
        """
        if not data or not isinstance(data, dict):
            return data

        redacted = {}

        for key, value in data.items():
            # 检查键名是否敏感
            key_lower = str(key).lower()
            is_sensitive_key = False

            if self.enable_field_name_detection:
                # 检查是否是完全匹配的敏感字段名
                for sensitive_name in self.sensitive_field_names:
                    if sensitive_name in key_lower:
                        is_sensitive_key = True
                        break

            # 处理值
            if is_sensitive_key:
                # 敏感字段名，直接脱敏
                redacted[key] = self.redaction_string
                if context:
                    logger.debug(f"敏感字段脱敏: 上下文={context}, 字段={key}")
            elif isinstance(value, str):
                # 字符串值，使用模式脱敏
                redacted_value = self.redact_text(value, f"{context}.{key}" if context else key)
                redacted[key] = redacted_value
            elif isinstance(value, dict):
                # 嵌套字典，递归处理
                redacted[key] = self.redact_dict(value, f"{context}.{key}" if context else key)
            elif isinstance(value, list):
                # 列表，处理每个元素
                redacted[key] = self.redact_list(value, f"{context}.{key}" if context else key)
            else:
                # 其他类型，直接复制
                redacted[key] = value

        return redacted

    def redact_list(self, data: List[Any], context: Optional[str] = None) -> List[Any]:
        """
        脱敏列表中的敏感信息

        Args:
            data: 要脱敏的列表
            context: 上下文信息

        Returns:
            脱敏后的列表
        """
        if not data or not isinstance(data, list):
            return data

        redacted = []

        for i, item in enumerate(data):
            item_context = f"{context}[{i}]" if context else f"item[{i}]"

            if isinstance(item, str):
                redacted_item = self.redact_text(item, item_context)
                redacted.append(redacted_item)
            elif isinstance(item, dict):
                redacted_item = self.redact_dict(item, item_context)
                redacted.append(redacted_item)
            elif isinstance(item, list):
                redacted_item = self.redact_list(item, item_context)
                redacted.append(redacted_item)
            else:
                redacted.append(item)

        return redacted

    def redact_json(self, json_str: str, context: Optional[str] = None) -> str:
        """
        脱敏JSON字符串中的敏感信息

        Args:
            json_str: JSON字符串
            context: 上下文信息

        Returns:
            脱敏后的JSON字符串
        """
        if not json_str or not isinstance(json_str, str):
            return json_str

        try:
            # 解析JSON
            data = json.loads(json_str)

            # 脱敏
            if isinstance(data, dict):
                redacted_data = self.redact_dict(data, context)
            elif isinstance(data, list):
                redacted_data = self.redact_list(data, context)
            else:
                redacted_data = data

            # 重新序列化
            return json.dumps(redacted_data, ensure_ascii=False)
        except json.JSONDecodeError:
            # 如果不是有效的JSON，直接脱敏文本
            return self.redact_text(json_str, context)
        except Exception as e:
            logger.error(f"JSON脱敏失败: {context}, 错误: {e}")
            return json_str

    def is_sensitive(self, text: str) -> Tuple[bool, List[str]]:
        """
        检测文本中是否包含敏感信息

        Args:
            text: 要检测的文本

        Returns:
            (是否敏感, 敏感类型列表)
        """
        if not text or not isinstance(text, str):
            return False, []

        sensitive_types = []

        # 检查模式
        for pattern in self.patterns:
            if pattern.compiled_pattern and pattern.compiled_pattern.search(text):
                sensitive_types.append(pattern.data_type.value)

        # 检查敏感字段名
        if self.enable_field_name_detection:
            for sensitive_name in self.sensitive_field_names:
                if sensitive_name in text.lower():
                    # 避免重复添加
                    if "field_name" not in sensitive_types:
                        sensitive_types.append("sensitive_field_name")
                    break

        return len(sensitive_types) > 0, sensitive_types

    def add_custom_pattern(self, pattern: SensitivePattern) -> None:
        """
        添加自定义敏感信息模式

        Args:
            pattern: 敏感信息模式
        """
        # 编译模式
        pattern.__post_init__()

        # 添加到模式列表并重新排序
        self.patterns.append(pattern)
        self.patterns = sorted(self.patterns, key=lambda x: x.priority)

        logger.info(f"添加自定义敏感模式: {pattern.name}, 优先级: {pattern.priority}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取管理器统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "total_patterns": len(self.patterns),
            "pattern_types": {},
            "sensitive_field_names_count": len(self.sensitive_field_names),
            "config": {
                "enable_field_name_detection": self.enable_field_name_detection,
                "enable_pattern_detection": self.enable_pattern_detection,
                "redaction_string": self.redaction_string,
                "max_context_chars": self.max_context_chars,
            }
        }

        # 统计各种类型的模式数量
        for pattern in self.patterns:
            data_type = pattern.data_type.value
            if data_type not in stats["pattern_types"]:
                stats["pattern_types"][data_type] = 0
            stats["pattern_types"][data_type] += 1

        return stats


# 全局敏感数据管理器实例
_sensitive_data_manager: Optional[SensitiveDataManager] = None


def get_sensitive_data_manager() -> SensitiveDataManager:
    """
    获取全局敏感数据管理器实例

    Returns:
        敏感数据管理器实例
    """
    global _sensitive_data_manager
    if _sensitive_data_manager is None:
        _sensitive_data_manager = SensitiveDataManager()
    return _sensitive_data_manager


def redact_sensitive_data(data: Any, context: Optional[str] = None) -> Any:
    """
    脱敏数据的快捷函数

    Args:
        data: 要脱敏的数据（字符串、字典、列表等）
        context: 上下文信息

    Returns:
        脱敏后的数据
    """
    manager = get_sensitive_data_manager()

    if isinstance(data, str):
        return manager.redact_text(data, context)
    elif isinstance(data, dict):
        return manager.redact_dict(data, context)
    elif isinstance(data, list):
        return manager.redact_list(data, context)
    else:
        return data


# 兼容性函数，保持与现有代码的兼容
def filter_sensitive_data(text: str) -> str:
    """
    过滤敏感信息（兼容现有代码）

    Args:
        text: 要过滤的文本

    Returns:
        过滤后的文本
    """
    return get_sensitive_data_manager().redact_text(text, "compatibility")


if __name__ == "__main__":
    # 测试敏感数据管理器
    logging.basicConfig(level=logging.INFO)

    manager = SensitiveDataManager()

    # 测试文本脱敏
    test_text = """
    API调用: api_key='sk-abc123def456ghi789jkl012mno345pqr678stu901'
    用户登录: username='john', password='secret123'
    数据库连接: postgres://admin:admin123@localhost:5432/mydb
    令牌: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
    信用卡: 4111-1111-1111-1111
    电话号码: +1-555-123-4567
    """

    print("原始文本:")
    print(test_text)
    print("\n脱敏后文本:")
    redacted_text = manager.redact_text(test_text, "test")
    print(redacted_text)

    # 测试字典脱敏
    test_dict = {
        "user": {
            "username": "john",
            "password": "secret123",
            "api_key": "sk-abc123def456",
            "email": "john@example.com"
        },
        "database": {
            "url": "postgres://admin:admin123@localhost:5432/mydb",
            "password": "db_secret"
        },
        "tokens": [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "Bearer abc123def456"
        ]
    }

    print("\n原始字典:")
    print(json.dumps(test_dict, indent=2))
    print("\n脱敏后字典:")
    redacted_dict = manager.redact_dict(test_dict, "test_dict")
    print(json.dumps(redacted_dict, indent=2))

    # 测试敏感信息检测
    is_sensitive, types = manager.is_sensitive(test_text)
    print(f"\n文本包含敏感信息: {is_sensitive}")
    print(f"敏感类型: {types}")

    # 显示统计信息
    print("\n管理器统计:")
    print(json.dumps(manager.get_stats(), indent=2))