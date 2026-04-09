#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 统一配置管理模块
支持从 .env、JSON 配置文件和环境变量读取，并提供动态修改入口。
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 配置文件路径（用户目录下）
CONFIG_DIR = Path.home() / ".clawai"
CONFIG_FILE = CONFIG_DIR / "config.json"

# 默认配置
DEFAULTS = {
    # AI 后端
    "llm_provider": "deepseek",          # deepseek / openai / anthropic
    "llm_model": "deepseek-chat",
    "deepseek_api_key": "",
    "openai_api_key": "",
    "anthropic_api_key": "",

    # 后端服务
    "backend_url": "http://localhost:5000",
    "tool_executor_url": "http://localhost:8082",

    # 超时配置
    "scan_timeout": 300,          # 扫描超时（秒）
    "llm_timeout": 60,            # LLM 请求超时（秒）

    # 会话
    "sessions_dir": str(Path.home() / ".clawai" / "sessions"),
    "max_history": 50,            # 最大对话历史条数

    # 导出
    "export_dir": str(Path.home() / ".clawai" / "exports"),

    # UI
    "ui_mode": "modern",          # modern / tui / basic
    "language": "zh",             # zh / en
}

# 环境变量映射
ENV_MAP = {
    "DEEPSEEK_API_KEY": "deepseek_api_key",
    "OPENAI_API_KEY": "openai_api_key",
    "ANTHROPIC_API_KEY": "anthropic_api_key",
    "CLAWAI_BACKEND_URL": "backend_url",
    "CLAWAI_TOOL_EXECUTOR_URL": "tool_executor_url",
    "CLAWAI_SCAN_TIMEOUT": "scan_timeout",
    "CLAWAI_LLM_TIMEOUT": "llm_timeout",
    "CLAWAI_UI_MODE": "ui_mode",
    "CLAWAI_LANGUAGE": "language",
}


class CLIConfig:
    """CLI 配置管理器（单例）"""

    _instance: Optional["CLIConfig"] = None
    _data: dict = {}

    def __new__(cls) -> "CLIConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def _ensure_loaded(self):
        if not self._loaded:
            self.reload()
            self._loaded = True

    def reload(self):
        """重新加载配置（优先级：环境变量 > 配置文件 > 默认值）"""
        # 1. 默认值
        self._data = dict(DEFAULTS)

        # 2. 从配置文件加载
        self._load_file()

        # 3. 从环境变量覆盖
        self._load_env()

        # 确保目录存在
        self._ensure_dirs()

    def _load_file(self):
        """从 JSON 配置文件加载"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_cfg = json.load(f)
                self._data.update(file_cfg)
            except Exception as e:
                logger.warning(f"配置文件读取失败: {e}")

    def _load_env(self):
        """从环境变量加载"""
        for env_key, cfg_key in ENV_MAP.items():
            val = os.environ.get(env_key)
            if val is not None:
                # 类型转换
                default = DEFAULTS.get(cfg_key)
                if isinstance(default, int):
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                self._data[cfg_key] = val

    def _ensure_dirs(self):
        """确保必要目录存在"""
        for key in ("sessions_dir", "export_dir"):
            path = Path(self._data[key])
            path.mkdir(parents=True, exist_ok=True)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        self._ensure_loaded()
        return self._data.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True):
        """设置配置项，persist=True 时写入配置文件"""
        self._ensure_loaded()
        self._data[key] = value
        if persist:
            self.save()

    def save(self):
        """将当前配置写入文件（不写入纯默认值以保持文件简洁）"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # 只保存与默认值不同的项
        to_save = {k: v for k, v in self._data.items() if v != DEFAULTS.get(k)}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"配置保存失败: {e}")

    def as_dict(self) -> dict:
        self._ensure_loaded()
        return dict(self._data)

    # ---- 常用属性快捷访问 ----

    @property
    def backend_url(self) -> str:
        return self.get("backend_url")

    @property
    def tool_executor_url(self) -> str:
        return self.get("tool_executor_url")

    @property
    def scan_timeout(self) -> int:
        return int(self.get("scan_timeout", 300))

    @property
    def llm_timeout(self) -> int:
        return int(self.get("llm_timeout", 60))

    @property
    def sessions_dir(self) -> Path:
        return Path(self.get("sessions_dir"))

    @property
    def export_dir(self) -> Path:
        return Path(self.get("export_dir"))

    @property
    def llm_provider(self) -> str:
        return self.get("llm_provider", "deepseek")

    @property
    def llm_model(self) -> str:
        return self.get("llm_model", "deepseek-chat")

    @property
    def api_key(self) -> str:
        """根据当前 provider 返回对应的 API Key"""
        provider = self.llm_provider
        if provider == "deepseek":
            return self.get("deepseek_api_key", "")
        elif provider == "openai":
            return self.get("openai_api_key", "")
        elif provider == "anthropic":
            return self.get("anthropic_api_key", "")
        return ""

    def show(self):
        """打印当前配置（隐藏敏感字段）"""
        self._ensure_loaded()
        sensitive = {"deepseek_api_key", "openai_api_key", "anthropic_api_key"}
        print("\n=== ClawAI 配置 ===")
        for k, v in self._data.items():
            if k in sensitive:
                display = ("*" * 8 + v[-4:]) if len(v) > 4 else ("*" * len(v) if v else "(未设置)")
            else:
                display = v
            print(f"  {k}: {display}")
        print()


# 全局单例
_config: Optional[CLIConfig] = None


def get_config() -> CLIConfig:
    """获取全局配置单例"""
    global _config
    if _config is None:
        _config = CLIConfig()
    return _config
