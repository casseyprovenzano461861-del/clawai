#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 命令注册表
借鉴 cc-haha 的命令注册模式：懒加载、自动发现、模糊匹配

每种命令定义 COMMAND_META 元数据（模块级别，导入即加载）
和 Command 类（仅在执行时才加载实现代码）
"""

import difflib
import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class CommandMeta:
    """命令元数据（轻量级，导入即加载）"""
    name: str
    description_zh: str
    description_en: str
    category: str  # "local" | "prompt" | "local_jsx"
    aliases: List[str] = field(default_factory=list)
    module_path: str = ""  # 懒加载模块路径
    argument_hint: str = ""  # 参数提示，如 "[list|save|load]"
    is_hidden: bool = False

    _impl_class: Optional[Type] = field(default=None, repr=False, init=False)

    def load(self) -> Any:
        """懒加载命令实现类"""
        if self._impl_class is not None:
            return self._impl_class

        if not self.module_path:
            raise RuntimeError(f"命令 {self.name} 没有配置 module_path")

        try:
            module = importlib.import_module(self.module_path)
            # 查找 Command 子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                        and attr_name.endswith("Command")
                        and attr_name != "Command"):
                    self._impl_class = attr
                    return attr
            # 回退: 使用模块本身
            if hasattr(module, "execute"):
                self._impl_class = module
                return module
            raise RuntimeError(f"模块 {self.module_path} 中未找到 Command 类")
        except ImportError as e:
            raise RuntimeError(f"加载命令 {self.name} 失败: {e}")


class CommandRegistry:
    """命令注册表（单例）

    职责:
    - 注册命令元数据
    - 按名称/别名查找命令
    - 懒加载命令实现
    - 模糊匹配建议
    """

    _instance: Optional["CommandRegistry"] = None

    def __init__(self):
        self._commands: Dict[str, CommandMeta] = {}
        self._aliases: Dict[str, str] = {}  # alias -> canonical name
        self._loaded = False

    @classmethod
    def get(cls) -> "CommandRegistry":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, meta: CommandMeta) -> None:
        """注册命令元数据"""
        self._commands[meta.name] = meta
        for alias in meta.aliases:
            self._aliases[alias.lower()] = meta.name
        logger.debug(f"注册命令: /{meta.name} ({meta.category})")

    def lookup(self, name: str) -> Optional[CommandMeta]:
        """查找命令（精确 → 别名 → 模糊）"""
        name_lower = name.lower()

        # 1. 精确匹配
        if name_lower in self._commands:
            return self._commands[name_lower]

        # 2. 别名匹配
        if name_lower in self._aliases:
            canonical = self._aliases[name_lower]
            return self._commands.get(canonical)

        # 3. 模糊匹配
        all_names = list(self._commands.keys()) + list(self._aliases.keys())
        matches = difflib.get_close_matches(name_lower, all_names, n=1, cutoff=0.6)
        if matches:
            match = matches[0]
            if match in self._commands:
                return self._commands[match]
            if match in self._aliases:
                return self._commands.get(self._aliases[match])

        return None

    def fuzzy_match(self, name: str, n: int = 3) -> List[str]:
        """返回模糊匹配的命令名称（用于建议）"""
        all_names = list(self._commands.keys())
        return difflib.get_close_matches(name.lower(), all_names, n=n, cutoff=0.5)

    def all_commands(self) -> List[CommandMeta]:
        """返回所有非隐藏命令"""
        return [m for m in self._commands.values() if not m.is_hidden]

    def discover(self) -> None:
        """自动发现 src/cli/commands/ 目录下的命令模块"""
        if self._loaded:
            return

        import pkgutil
        from src.cli import commands as commands_pkg

        package_path = commands_pkg.__path__
        for importer, modname, ispkg in pkgutil.iter_modules(package_path):
            if modname.startswith("_"):
                continue
            full_module = f"src.cli.commands.{modname}"
            try:
                module = importlib.import_module(full_module)
                # Register the primary COMMAND_META
                if hasattr(module, "COMMAND_META"):
                    meta_dict = module.COMMAND_META
                    meta = CommandMeta(
                        name=meta_dict["name"],
                        description_zh=meta_dict.get("description_zh", ""),
                        description_en=meta_dict.get("description_en", ""),
                        category=meta_dict.get("category", "local"),
                        aliases=meta_dict.get("aliases", []),
                        module_path=full_module,
                        argument_hint=meta_dict.get("argument_hint", ""),
                        is_hidden=meta_dict.get("is_hidden", False),
                    )
                    self.register(meta)

                # Register additional *_META dicts (e.g. PAUSE_META, RESUME_META)
                for attr_name in dir(module):
                    if attr_name == "COMMAND_META" or not attr_name.endswith("_META"):
                        continue
                    extra_dict = getattr(module, attr_name)
                    if not isinstance(extra_dict, dict) or "name" not in extra_dict:
                        continue
                    extra_meta = CommandMeta(
                        name=extra_dict["name"],
                        description_zh=extra_dict.get("description_zh", ""),
                        description_en=extra_dict.get("description_en", ""),
                        category=extra_dict.get("category", "local"),
                        aliases=extra_dict.get("aliases", []),
                        module_path=extra_dict.get("module_path", full_module),
                        argument_hint=extra_dict.get("argument_hint", ""),
                        is_hidden=extra_dict.get("is_hidden", False),
                    )
                    self.register(extra_meta)
            except Exception as e:
                logger.warning(f"发现命令模块 {modname} 失败: {e}")

        self._loaded = True
        logger.debug(f"命令发现完成: {len(self._commands)} 个命令")


def get_registry() -> CommandRegistry:
    """获取已初始化的命令注册表"""
    registry = CommandRegistry.get()
    registry.discover()
    return registry


# 导出历史记录管理器供其他模块使用
from src.cli.commands.history import HistoryManager

def get_history_manager() -> HistoryManager:
    """获取历史记录管理器实例"""
    return HistoryManager()
