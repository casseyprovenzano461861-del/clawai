# -*- coding: utf-8 -*-
"""
ClawAI 配置文件
统一管理所有配置项
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# 项目内工具目录
EXTERNAL_TOOLS_DIR = BASE_DIR / "external_tools"


class Config:
    """配置基类"""
    
    # ========== 基础配置 ==========
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY")  # 必须通过环境变量设置
    
    # ========== 服务器配置 ==========
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "5000"))
    FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))
    
    # ========== API 配置 ==========
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # 可选，没有则使用规则引擎
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
    DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))
    
    # ========== 工具路径配置 ==========
    # 优先使用环境变量，否则使用项目内工具目录
    NMAP_PATH = r"e:\ClawAI\external_tools\mock_tools\nmap_mock.py"  # 暂时保留mock，nmap未安装
    WHATWEB_PATH = r"C:\Users\67096\AppData\Local\Python\pythoncore-3.14-64\Scripts\whatweb.exe"
    NUCLEI_PATH = r"C:\Users\67096\AppData\Local\Python\pythoncore-3.14-64\Scripts\nuclei.exe"
    SQLMAP_PATH = r"C:\Users\67096\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\sqlmap\sqlmap.py"
    
    # ========== CVE检测配置 ==========
    TARGET_CVES = [
        "S2-045",           # Apache Struts2 S2-045 (CVE-2017-5638)
        "S2-057",           # Apache Struts2 S2-057 (CVE-2018-11776)
        "ThinkPHP-5.0.23-rce",
        "CVE-2023-21839",   # Oracle WebLogic
        "CVE-2017-12615",   # Apache Tomcat
        "CVE-2019-11043",   # PHP
        "CVE-2022-41678",   # Apache ActiveMQ
        "CVE-2017-7504",    # JBoss
        "CVE-2016-4437",    # Apache Shiro
        "fastjson-1.2.24-rce",
        "fastjson-1.2.47-rce",
        "CVE-2022-34265",   # Django
        "Flask-SSTI",
        "CVE-2024-36401",   # GeoServer
    ]
    
    CVE_DETECTION_TIMEOUT = int(os.getenv("CVE_DETECTION_TIMEOUT", "60"))
    CVE_RESULTS_DIR = BASE_DIR / "results"
    
    # ========== 数据库配置 ==========
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/clawai.db")
    
    # ========== 安全配置 ==========
    API_AUTH_ENABLED = os.getenv("API_AUTH_ENABLED", "false").lower() == "true"
    API_SECRET_KEY = os.getenv("API_SECRET_KEY")  # 必须通过环境变量设置
    JWT_SECRET = os.getenv("JWT_SECRET")  # 必须通过环境变量设置
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    SESSION_SECRET = os.getenv("SESSION_SECRET")  # 必须通过环境变量设置
    
    # Redis配置（用于速率限制和会话存储）
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    
    # 多因素认证配置
    MFA_ENABLED = os.getenv("MFA_ENABLED", "true").lower() == "true"
    MFA_ISSUER_NAME = os.getenv("MFA_ISSUER_NAME", "ClawAI")
    
    # 速率限制配置
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_LOGIN_ATTEMPTS = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5"))
    RATE_LIMIT_LOGIN_WINDOW = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW", "300"))
    RATE_LIMIT_API_REQUESTS = int(os.getenv("RATE_LIMIT_API_REQUESTS", "100"))
    RATE_LIMIT_API_WINDOW = int(os.getenv("RATE_LIMIT_API_WINDOW", "3600"))
    
    # 账户安全配置
    ACCOUNT_LOCKOUT_ENABLED = os.getenv("ACCOUNT_LOCKOUT_ENABLED", "true").lower() == "true"
    ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv("ACCOUNT_LOCKOUT_THRESHOLD", "5"))
    ACCOUNT_LOCKOUT_DURATION = int(os.getenv("ACCOUNT_LOCKOUT_DURATION", "900"))  # 15分钟，单位秒
    
    # 用户管理配置
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")  # 必须通过环境变量设置
    REQUIRE_EMAIL_VERIFICATION = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() == "true"
    
    # 输入验证
    MAX_TARGET_LENGTH = int(os.getenv("MAX_TARGET_LENGTH", "255"))
    ALLOWED_TARGET_PATTERNS = [
        r"^[a-zA-Z0-9.-]+$",  # 域名
        r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",  # IP地址
        r"^https?://[a-zA-Z0-9.-]+(:\d+)?(/.*)?$",  # URL
    ]
    
    # ========== 日志配置 ==========
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / "logs" / "clawai.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # ========== 缓存配置 ==========
    CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")
    CACHE_TTL = 3600  # 1小时
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # ========== 性能配置 ==========
    REQUEST_TIMEOUT = 30
    MAX_CONCURRENT_TASKS = 5
    TASK_QUEUE_SIZE = 100
    
    # ========== 功能开关 ==========
    ENABLE_REAL_ATTACK = True
    ENABLE_CVE_DETECTION = True
    ENABLE_AI_ANALYSIS = True
    ENABLE_ATTACK_VISUALIZATION = True
    ENABLE_ATTACK_EVOLUTION = True
    ENABLE_DEFENSE_SIMULATION = True
    ENABLE_REPORT_GENERATION = True
    
    # ========== 邮件配置 ==========
    EMAIL_ENABLED = False
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    
    # ========== 前端配置 ==========
    FRONTEND_THEME = {
        "primary_color": "#3b82f6",  # blue-500
        "secondary_color": "#10b981",  # emerald-500
        "dark_mode": True,
    }
    
    # ========== 开发配置 ==========
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "development")
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """获取所有配置项"""
        settings = {}
        for key in dir(cls):
            if key.isupper() and not key.startswith('_'):
                value = getattr(cls, key)
                settings[key] = value
        return settings
    
    @classmethod
    def print_settings(cls):
        """打印所有配置项"""
        print("=" * 60)
        print("ClawAI 配置设置")
        print("=" * 60)
        
        settings = cls.get_all_settings()
        for key, value in sorted(settings.items()):
            display_value = value
            
            # 隐藏敏感信息
            if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password', 'token']):
                if display_value:
                    if isinstance(display_value, str):
                        display_value = "*" * 8 + display_value[-4:] if len(display_value) > 4 else "*" * 8
                    else:
                        display_value = "*" * 8  # 对于非字符串的敏感值，也显示星号
                else:
                    display_value = "(未设置)"
            
            print(f"{key}: {display_value}")
        
        print("=" * 60)
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """验证配置，返回错误信息列表"""
        errors = []
        
        # 检查必要的安全配置
        required_secrets = [
            ("SECRET_KEY", cls.SECRET_KEY, "应用密钥"),
            ("API_SECRET_KEY", cls.API_SECRET_KEY, "API密钥"),
            ("JWT_SECRET", cls.JWT_SECRET, "JWT密钥"),
            ("SESSION_SECRET", cls.SESSION_SECRET, "会话密钥"),
            ("DEFAULT_ADMIN_PASSWORD", cls.DEFAULT_ADMIN_PASSWORD, "管理员密码"),
        ]
        
        for env_name, value, description in required_secrets:
            if not value:
                errors.append(f"{description}未设置（环境变量: {env_name}）")
        
        # 检查工具路径
        required_tools = [
            ("NMAP_PATH", cls.NMAP_PATH, "Nmap工具路径"),
            ("WHATWEB_PATH", cls.WHATWEB_PATH, "WhatWeb工具路径"),
        ]
        
        for env_name, path, description in required_tools:
            if not path:
                errors.append(f"{description}未设置（环境变量: {env_name}）")
            elif not os.path.exists(path):
                errors.append(f"{description}路径不存在: {path}")
        
        return errors


# 创建配置实例
config = Config()


if __name__ == "__main__":
    # 测试配置
    config.print_settings()
    
    # 验证配置
    print("\n配置验证:")
    errors = config.validate_config()
    if errors:
        print("❌ 发现配置错误:")
        for error in errors:
            print(f"  - {error}")
        
        print("\n💡 解决方案:")
        print("  1. 创建 .env 文件并设置必要的环境变量")
        print("  2. 参考 .env.example 文件中的配置项")
        print("  3. 确保安全工具已正确安装")
    else:
        print("✅ 所有配置验证通过")
    
    # AI配置提示
    if not config.DEEPSEEK_API_KEY:
        print("\nℹ️  提示: DeepSeek API密钥未设置，将使用规则引擎模式")
        print("  如需AI功能，请设置环境变量 DEEPSEEK_API_KEY")
