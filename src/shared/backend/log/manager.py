"""
日志管理器
统一日志系统，支持结构化日志和日志轮转
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from ..schemas import LogLevel
from .sensitive_filter import (
    SensitiveDataFilter,
    SensitiveDataFormatter,
    StructuredSensitiveFormatter
)


class StructuredFormatter(StructuredSensitiveFormatter):
    """结构化日志格式化器（继承自StructuredSensitiveFormatter以保持向后兼容性）"""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        # 调用父类初始化，但忽略fmt和datefmt，因为StructuredSensitiveFormatter不使用它们
        super().__init__()


class LogManager:
    """日志管理器类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志管理器

        Args:
            config: 日志配置
        """
        self.config = config or {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._loggers: Dict[str, logging.Logger] = {}

        # 设置默认配置
        self._setup_defaults()

        # 初始化日志系统
        self._init_logging()

    def _setup_defaults(self):
        """设置默认配置"""
        defaults = {
            "level": LogLevel.INFO,
            "file": None,
            "max_size": 10 * 1024 * 1024,  # 10MB
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "output_json": False,
            "enable_console": True,
            "enable_file": True,
        }

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _init_logging(self):
        """初始化日志系统"""
        # 清除现有的handlers
        logging.root.handlers.clear()

        # 设置根日志级别
        log_level = getattr(logging, self.config["level"].upper(), logging.INFO)
        logging.root.setLevel(log_level)

        # 创建handlers
        handlers = []

        # 控制台handler
        if self.config.get("enable_console", True):
            console_handler = self._create_console_handler()
            handlers.append(console_handler)

        # 文件handler
        if self.config.get("enable_file", True) and self.config.get("file"):
            file_handler = self._create_file_handler()
            handlers.append(file_handler)

        # 为根日志添加handlers
        for handler in handlers:
            logging.root.addHandler(handler)

    def _create_console_handler(self) -> logging.Handler:
        """创建控制台handler"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = self._create_formatter()
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config["level"].upper(), logging.INFO))
        return handler

    def _create_file_handler(self) -> logging.Handler:
        """创建文件handler"""
        log_file = Path(self.config["file"])

        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # 创建轮转文件handler
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.config["max_size"],
            backupCount=self.config["backup_count"],
            encoding='utf-8'
        )

        formatter = self._create_formatter()
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config["level"].upper(), logging.INFO))
        return handler

    def _create_formatter(self) -> logging.Formatter:
        """创建格式化器"""
        fmt = self.config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        datefmt = self.config.get("datefmt", "%Y-%m-%d %H:%M:%S")

        if self.config.get("output_json", False):
            return StructuredSensitiveFormatter()
        else:
            return SensitiveDataFormatter(fmt, datefmt)

    def get_logger(self, name: str, extra_config: Optional[Dict[str, Any]] = None) -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志记录器名称
            extra_config: 额外配置

        Returns:
            logging.Logger实例
        """
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)

        # 应用额外配置
        if extra_config:
            if "level" in extra_config:
                logger.setLevel(getattr(logging, extra_config["level"].upper(), logging.INFO))

        self._loggers[name] = logger
        return logger

    def update_config(self, **kwargs):
        """更新日志配置"""
        self.config.update(kwargs)
        self._init_logging()  # 重新初始化

    def setup_module_logger(self, module_name: str, level: Optional[str] = None):
        """
        设置模块日志记录器

        Args:
            module_name: 模块名称
            level: 日志级别
        """
        logger = self.get_logger(module_name)

        if level:
            logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # 移除现有的handlers（避免重复）
        logger.handlers.clear()

        # 继承根日志的配置
        logger.propagate = True

        return logger

    def log_with_context(self, logger: logging.Logger, level: str, message: str,
                         extra: Optional[Dict[str, Any]] = None, **kwargs):
        """
        记录带上下文的日志

        Args:
            logger: 日志记录器
            level: 日志级别
            message: 日志消息
            extra: 额外上下文信息
            **kwargs: 其他字段
        """
        log_method = getattr(logger, level.lower(), logger.info)

        log_context = extra or {}
        log_context.update(kwargs)

        # 创建LogRecord的extra字段
        if log_context:
            # 对于结构化日志，我们可以添加额外字段
            if hasattr(logger.handlers[0].formatter, '_json_formatter'):
                record = logger.makeRecord(
                    logger.name,
                    getattr(logging, level.upper()),
                    "",  # fn
                    0,   # lno
                    message,
                    (),  # args
                    None,
                    extra=log_context
                )
                # 标记为JSON输出
                record.output_json = True
                logger.handle(record)
            else:
                # 传统日志，将上下文添加到消息中
                context_str = " ".join([f"{k}={v}" for k, v in log_context.items()])
                full_message = f"{message} [{context_str}]" if context_str else message
                log_method(full_message)
        else:
            log_method(message)

    def shutdown(self):
        """关闭日志系统"""
        logging.shutdown()


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def init_logging(config: Optional[Dict[str, Any]] = None) -> LogManager:
    """初始化日志系统"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager(config)
    return _log_manager


def get_log_manager() -> LogManager:
    """获取日志管理器"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器（快捷方式）"""
    return get_log_manager().get_logger(name)