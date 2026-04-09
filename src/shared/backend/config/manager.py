"""
配置管理器
统一配置管理系统，基于Pydantic模型
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml
import json

from ..schemas import AppConfig, Environment, LogLevel


class ConfigManager:
    """配置管理器类"""

    def __init__(self, env_file: Optional[str] = None, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            env_file: 环境变量文件路径
            config_file: 配置文件路径（YAML/JSON）
        """
        self._config: Optional[AppConfig] = None
        self._env_file = env_file
        self._config_file = config_file
        self._override_values: Dict[str, Any] = {}

        # 加载环境变量
        self._load_environment()

        # 加载配置
        self._load_config()

    def _load_environment(self) -> None:
        """加载环境变量"""
        # 首先加载.env文件（如果存在）
        if self._env_file and os.path.exists(self._env_file):
            load_dotenv(self._env_file)
        else:
            # 尝试默认位置
            default_env = Path.cwd() / '.env'
            if default_env.exists():
                load_dotenv(default_env)
            else:
                # 加载项目根目录的.env文件
                project_env = Path(__file__).parent.parent.parent.parent / '.env'
                if project_env.exists():
                    load_dotenv(project_env)

        # 设置默认环境变量（如果未设置）
        os.environ.setdefault('ENVIRONMENT', 'development')
        os.environ.setdefault('LOG_LEVEL', 'info')

    def _load_config(self) -> None:
        """加载配置文件"""
        config_data = {}

        # 1. 从配置文件加载（如果存在）
        if self._config_file and os.path.exists(self._config_file):
            config_data.update(self._load_config_file(self._config_file))
        else:
            # 尝试默认配置文件位置
            config_paths = [
                Path.cwd() / 'config' / 'config.yaml',
                Path.cwd() / 'config' / 'config.json',
                Path.cwd() / 'config.yaml',
                Path.cwd() / 'config.json',
                Path(__file__).parent.parent.parent.parent / 'config' / 'config.yaml',
                Path(__file__).parent.parent.parent.parent / 'config' / 'config.json',
            ]

            for config_path in config_paths:
                if config_path.exists():
                    config_data.update(self._load_config_file(config_path))
                    break

        # 2. 从环境变量加载
        env_config = self._load_from_environment()
        config_data.update(env_config)

        # 3. 应用覆盖值
        config_data.update(self._override_values)

        # 4. 创建配置对象
        self._config = AppConfig(**config_data)

    def _load_config_file(self, file_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        file_path = Path(file_path)
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    # 尝试根据内容判断
                    content = f.read()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # 尝试YAML
                        f.seek(0)
                        return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {e}")
            return {}

    def _load_from_environment(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}

        # 环境
        env = os.getenv('ENVIRONMENT', 'development')
        config['environment'] = Environment(env.lower())

        # 日志级别
        log_level = os.getenv('LOG_LEVEL', 'info')
        config['logging'] = {'level': LogLevel(log_level.lower())}

        # 服务器配置
        server_config = {}
        if host := os.getenv('SERVER_HOST'):
            server_config['host'] = host
        if port := os.getenv('SERVER_PORT'):
            server_config['port'] = int(port)
        if workers := os.getenv('SERVER_WORKERS'):
            server_config['workers'] = int(workers)
        config['server'] = server_config

        # 数据库配置
        db_config = {}
        if db_url := os.getenv('DATABASE_URL'):
            db_config['url'] = db_url
        if db_type := os.getenv('DATABASE_TYPE'):
            db_config['type'] = db_type
        config['database'] = db_config

        # 安全配置
        security_config = {}
        if secret_key := os.getenv('SECRET_KEY'):
            security_config['secret_key'] = secret_key
        if jwt_secret := os.getenv('JWT_SECRET') or os.getenv('JWT_SECRET_KEY'):
            security_config['jwt_secret'] = jwt_secret
        if cors_origins := os.getenv('CORS_ORIGINS'):
            security_config['cors_origins'] = cors_origins.split(',')
        config['security'] = security_config

        # LLM配置
        llm_config = {}
        if api_key := os.getenv('OPENAI_API_KEY'):
            llm_config['api_key'] = api_key
        if model := os.getenv('LLM_MODEL'):
            llm_config['model'] = model
        config['llm'] = llm_config

        # 工具配置
        tool_config = {}
        if tools_dir := os.getenv('TOOLS_DIR'):
            tool_config['tools_dir'] = tools_dir
        if tool_timeout := os.getenv('TOOL_TIMEOUT'):
            tool_config['timeout'] = int(tool_timeout)
        config['tool'] = tool_config

        return config

    def get_config(self) -> AppConfig:
        """获取配置对象"""
        if self._config is None:
            self._load_config()
        return self._config

    def update_config(self, **kwargs) -> None:
        """更新配置"""
        if self._config is None:
            self._load_config()

        # 更新配置对象
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                # 尝试嵌套更新
                parts = key.split('.')
                obj = self._config
                for part in parts[:-1]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        break
                else:
                    if hasattr(obj, parts[-1]):
                        setattr(obj, parts[-1], value)

    def override(self, **kwargs) -> None:
        """临时覆盖配置值"""
        self._override_values.update(kwargs)
        self._load_config()  # 重新加载配置

    def save_to_file(self, file_path: Path, format: str = 'yaml') -> None:
        """保存配置到文件"""
        if self._config is None:
            self._load_config()

        config_dict = self._config.model_dump(mode='json')

        with open(file_path, 'w', encoding='utf-8') as f:
            if format.lower() in ['yaml', 'yml']:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif format.lower() == 'json':
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的格式: {format}")

    def validate(self) -> bool:
        """验证配置"""
        try:
            self.get_config()
            return True
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()

    @property
    def is_production(self) -> bool:
        """是否生产环境"""
        return self.get_config().environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """是否开发环境"""
        return self.get_config().environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """是否测试环境"""
        return self.get_config().environment == Environment.TESTING


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """获取配置对象（快捷方式）"""
    return get_config_manager().get_config()