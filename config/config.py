# -*- coding: utf-8 -*-
"""
ClawAI 配置模块 - 兼容层
提供向后兼容的配置接口，同时使用新的Pydantic配置管理系统
"""

import os
import warnings
from typing import Any

# 尝试导入新的配置管理器
try:
    from src.shared.backend.config.manager import get_config
    from src.shared.backend.schemas import AppConfig

    _config: AppConfig = get_config()
    _using_new_config = True

except ImportError as e:
    warnings.warn(f"无法导入新的配置管理器: {e}，使用旧版配置")
    _using_new_config = False

    # 回退到旧版配置
    from dotenv import load_dotenv
    load_dotenv()


def _get_new_config_value(key: str, default: Any = None) -> Any:
    """从新配置系统中获取值"""
    if not _using_new_config:
        return default

    # 映射旧键名到新配置路径
    key_mapping = {
        'SERVER_HOST': ('server', 'host'),
        'BACKEND_PORT': ('server', 'port'),
        'FRONTEND_PORT': None,  # 新配置中没有对应项
        'DEBUG': ('server', 'reload'),  # 近似映射
        'ENABLE_REAL_ATTACK': ('security', 'enable_real_attack'),
        'SECRET_KEY': ('security', 'secret_key'),
        'JWT_SECRET': ('security', 'jwt_secret'),
        'JWT_ALGORITHM': ('security', 'jwt_algorithm'),
        'JWT_EXPIRATION_HOURS': ('security', 'jwt_expiration_hours'),
        'API_AUTH_ENABLED': ('security', 'api_auth_enabled'),
        'MFA_ENABLED': ('security', 'mfa_enabled'),
        'REDIS_HOST': ('cache', 'redis_host'),
        'REDIS_PORT': ('cache', 'redis_port'),
        'DATABASE_URL': ('database', 'url'),
        'OPENAI_API_KEY': ('llm', 'api_key'),
        'ANTHROPIC_API_KEY': None,  # 新配置中需要扩展支持
        'DEFAULT_LLM_PROVIDER': ('llm', 'provider'),
        'DEFAULT_MODEL': ('llm', 'model'),
        'CACHE_TYPE': ('cache', 'type'),
        'CACHE_DEFAULT_TIMEOUT': ('cache', 'default_timeout'),
        'TOOL_TIMEOUT': ('tool', 'timeout'),
        'MAX_CONCURRENT_TOOLS': ('tool', 'max_concurrent_tools'),
        'LOG_LEVEL': ('logging', 'level'),
        'LOG_FILE': ('logging', 'file'),
        'PROJECT_NAME': ('project_name',),
        'PROJECT_VERSION': ('project_version',),
        'PROJECT_DESCRIPTION': ('project_description',),
        'NEO4J_AUTH': ('graph', 'neo4j_auth'),
        'NEO4J_URI': ('graph', 'neo4j_uri'),
    }

    if key not in key_mapping:
        return default

    mapping = key_mapping[key]
    if mapping is None:
        return default

    try:
        value = _config
        for attr in mapping:
            value = getattr(value, attr)
        return value
    except AttributeError:
        return default


def _get_old_config_value(key: str, default: Any = None) -> Any:
    """从环境变量获取旧版配置值"""
    env_key = key
    if key in ['BACKEND_PORT', 'FRONTEND_PORT', 'REDIS_PORT', 'JWT_EXPIRATION_HOURS',
               'CACHE_DEFAULT_TIMEOUT', 'TOOL_TIMEOUT', 'MAX_CONCURRENT_TOOLS']:
        return int(os.getenv(env_key, default)) if os.getenv(env_key) else default
    elif key in ['DEBUG', 'ENABLE_REAL_ATTACK', 'API_AUTH_ENABLED', 'MFA_ENABLED']:
        return os.getenv(env_key, str(default)).lower() == 'true'
    else:
        return os.getenv(env_key, default)


# 动态生成配置变量
SERVER_HOST = _get_new_config_value('SERVER_HOST') or _get_old_config_value('SERVER_HOST', '0.0.0.0')
BACKEND_PORT = _get_new_config_value('BACKEND_PORT') or _get_old_config_value('BACKEND_PORT', 5000)
FRONTEND_PORT = _get_old_config_value('FRONTEND_PORT', 3000)  # 仅旧版支持
DEBUG = _get_new_config_value('DEBUG') or _get_old_config_value('DEBUG', False)

# 安全配置
ENABLE_REAL_ATTACK = _get_new_config_value('ENABLE_REAL_ATTACK') or _get_old_config_value('ENABLE_REAL_ATTACK', False)
SECRET_KEY = _get_new_config_value('SECRET_KEY') or _get_old_config_value('SECRET_KEY', 'your-secret-key-here-change-in-production')
JWT_SECRET = _get_new_config_value('JWT_SECRET') or _get_old_config_value('JWT_SECRET', 'clawai_jwt_secret_key_2025_change_in_production')
JWT_ALGORITHM = _get_new_config_value('JWT_ALGORITHM') or _get_old_config_value('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = _get_new_config_value('JWT_EXPIRATION_HOURS') or _get_old_config_value('JWT_EXPIRATION_HOURS', 24)
API_AUTH_ENABLED = _get_new_config_value('API_AUTH_ENABLED') or _get_old_config_value('API_AUTH_ENABLED', True)
MFA_ENABLED = _get_new_config_value('MFA_ENABLED') or _get_old_config_value('MFA_ENABLED', False)

# Redis配置
REDIS_HOST = _get_new_config_value('REDIS_HOST') or _get_old_config_value('REDIS_HOST', 'localhost')
REDIS_PORT = _get_new_config_value('REDIS_PORT') or _get_old_config_value('REDIS_PORT', 6379)

# 数据库配置
DATABASE_URL = _get_new_config_value('DATABASE_URL') or _get_old_config_value('DATABASE_URL', 'sqlite:///clawai.db')

# Neo4j图数据库配置
NEO4J_AUTH = _get_new_config_value('NEO4J_AUTH') or _get_old_config_value('NEO4J_AUTH', 'neo4j/password')
NEO4J_URI = _get_new_config_value('NEO4J_URI') or _get_old_config_value('NEO4J_URI', 'bolt://localhost:7687')

# AI/LLM 配置
OPENAI_API_KEY = _get_new_config_value('OPENAI_API_KEY') or _get_old_config_value('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = _get_old_config_value('ANTHROPIC_API_KEY', '')  # 仅旧版支持
DEFAULT_LLM_PROVIDER = _get_new_config_value('DEFAULT_LLM_PROVIDER') or _get_old_config_value('DEFAULT_LLM_PROVIDER', 'openai')
DEFAULT_MODEL = _get_new_config_value('DEFAULT_MODEL') or _get_old_config_value('DEFAULT_MODEL', 'gpt-4')

# 缓存配置
CACHE_TYPE = _get_new_config_value('CACHE_TYPE') or _get_old_config_value('CACHE_TYPE', 'memory')
CACHE_DEFAULT_TIMEOUT = _get_new_config_value('CACHE_DEFAULT_TIMEOUT') or _get_old_config_value('CACHE_DEFAULT_TIMEOUT', 300)

# 工具配置
TOOL_TIMEOUT = _get_new_config_value('TOOL_TIMEOUT') or _get_old_config_value('TOOL_TIMEOUT', 30)
MAX_CONCURRENT_TOOLS = _get_new_config_value('MAX_CONCURRENT_TOOLS') or _get_old_config_value('MAX_CONCURRENT_TOOLS', 5)

# 日志配置
LOG_LEVEL = _get_new_config_value('LOG_LEVEL') or _get_old_config_value('LOG_LEVEL', 'INFO')
LOG_FILE = _get_new_config_value('LOG_FILE') or _get_old_config_value('LOG_FILE', 'logs/clawai.log')

# 项目信息
PROJECT_NAME = _get_new_config_value('PROJECT_NAME') or "ClawAI - 智能安全评估系统"
PROJECT_VERSION = _get_new_config_value('PROJECT_VERSION') or "2.0"
PROJECT_DESCRIPTION = _get_new_config_value('PROJECT_DESCRIPTION') or "基于规则引擎和AI辅助的安全评估工具"


class Config:
    """配置类，提供所有配置参数的访问（兼容层）"""

    def __init__(self):
        self.SERVER_HOST = SERVER_HOST
        self.BACKEND_PORT = BACKEND_PORT
        self.FRONTEND_PORT = FRONTEND_PORT
        self.DEBUG = DEBUG
        self.ENABLE_REAL_ATTACK = ENABLE_REAL_ATTACK
        self.SECRET_KEY = SECRET_KEY
        self.JWT_SECRET = JWT_SECRET
        self.JWT_ALGORITHM = JWT_ALGORITHM
        self.JWT_EXPIRATION_HOURS = JWT_EXPIRATION_HOURS
        self.API_AUTH_ENABLED = API_AUTH_ENABLED
        self.MFA_ENABLED = MFA_ENABLED
        self.REDIS_HOST = REDIS_HOST
        self.REDIS_PORT = REDIS_PORT
        self.DATABASE_URL = DATABASE_URL
        self.NEO4J_AUTH = NEO4J_AUTH
        self.NEO4J_URI = NEO4J_URI
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
        self.DEFAULT_LLM_PROVIDER = DEFAULT_LLM_PROVIDER
        self.DEFAULT_MODEL = DEFAULT_MODEL
        self.CACHE_TYPE = CACHE_TYPE
        self.CACHE_DEFAULT_TIMEOUT = CACHE_DEFAULT_TIMEOUT
        self.TOOL_TIMEOUT = TOOL_TIMEOUT
        self.MAX_CONCURRENT_TOOLS = MAX_CONCURRENT_TOOLS
        self.LOG_LEVEL = LOG_LEVEL
        self.LOG_FILE = LOG_FILE
        self.PROJECT_NAME = PROJECT_NAME
        self.PROJECT_VERSION = PROJECT_VERSION
        self.PROJECT_DESCRIPTION = PROJECT_DESCRIPTION

        # 添加新配置系统的引用
        if _using_new_config:
            self._new_config = _config
        else:
            self._new_config = None

    def to_dict(self):
        """转换为字典"""
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}

    def get_new_config(self):
        """获取新的配置对象（如果可用）"""
        return self._new_config


# 创建全局配置实例
config = Config()

if __name__ == "__main__":
    # 打印配置信息
    print("=" * 80)
    print("ClawAI 配置信息")
    print("=" * 80)
    print(f"配置系统: {'新版Pydantic配置' if _using_new_config else '旧版环境变量配置'}")
    print("=" * 80)

    for key, value in vars(config).items():
        if key.startswith('_'):
            continue

        if 'KEY' in key and value:
            # 隐藏敏感信息
            print(f"{key}: {'*' * 8}{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"{key}: {value}")

    print("=" * 80)

    if _using_new_config and config._new_config:
        print("\n新配置系统详情:")
        print(f"环境: {config._new_config.environment}")
        print(f"使用Docker隔离: {config._new_config.tool.use_docker}")
        print(f"LLM提供商: {config._new_config.llm.provider}")