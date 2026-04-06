"""
敏感信息日志过滤器
在记录日志时自动脱敏敏感信息
"""

import logging
import json
from typing import Any, Dict, Optional

from ..security.sensitive_data import get_sensitive_data_manager, redact_sensitive_data


class SensitiveDataFilter(logging.Filter):
    """敏感数据日志过滤器"""

    def __init__(self, name: str = ""):
        super().__init__(name)
        self.sensitive_data_manager = get_sensitive_data_manager()
        self.enable_filtering = True
        self.redact_message = True  # 脱敏日志消息
        self.redact_extra = True    # 脱敏额外字段
        self.redact_exceptions = True  # 脱敏异常信息

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录，脱敏敏感信息

        Args:
            record: 日志记录

        Returns:
            是否记录此日志（总是返回True，因为我们只是修改记录）
        """
        if not self.enable_filtering:
            return True

        try:
            # 脱敏日志消息
            if self.redact_message and hasattr(record, 'msg') and record.msg:
                original_msg = record.msg
                if isinstance(original_msg, str):
                    # 脱敏消息中的敏感信息
                    redacted_msg = self.sensitive_data_manager.redact_text(
                        original_msg,
                        f"log.{record.name}.message"
                    )
                    if redacted_msg != original_msg:
                        record.msg = redacted_msg

                # 处理参数化的消息
                if hasattr(record, 'args') and record.args:
                    redacted_args = []
                    for i, arg in enumerate(record.args):
                        if isinstance(arg, str):
                            redacted_arg = self.sensitive_data_manager.redact_text(
                                arg,
                                f"log.{record.name}.args[{i}]"
                            )
                            redacted_args.append(redacted_arg)
                        elif isinstance(arg, dict):
                            redacted_arg = self.sensitive_data_manager.redact_dict(
                                arg,
                                f"log.{record.name}.args[{i}]"
                            )
                            redacted_args.append(redacted_arg)
                        elif isinstance(arg, list):
                            redacted_arg = self.sensitive_data_manager.redact_list(
                                arg,
                                f"log.{record.name}.args[{i}]"
                            )
                            redacted_args.append(redacted_arg)
                        else:
                            redacted_args.append(arg)

                    record.args = tuple(redacted_args)

            # 脱敏额外字段（对于结构化日志）
            if self.redact_extra and hasattr(record, 'extra') and record.extra:
                redacted_extra = self.sensitive_data_manager.redact_dict(
                    record.extra,
                    f"log.{record.name}.extra"
                )
                record.extra = redacted_extra

            # 脱敏异常信息
            if self.redact_exceptions and record.exc_info:
                # 异常信息在formatException中处理
                # 我们可以在格式化时脱敏，但这里我们设置一个标记
                record._exc_info_needs_redaction = True

        except Exception as e:
            # 脱敏失败不应阻止日志记录
            # 记录警告但继续处理
            logging.getLogger(__name__).warning(
                f"敏感信息脱敏失败: {e}",
                exc_info=False
            )

        return True


class SensitiveDataFormatter(logging.Formatter):
    """敏感数据日志格式化器，扩展自基类"""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.sensitive_data_manager = get_sensitive_data_manager()

    def formatException(self, exc_info):
        """
        格式化异常信息，脱敏敏感数据

        Args:
            exc_info: 异常信息

        Returns:
            脱敏后的异常信息字符串
        """
        try:
            # 获取原始的异常信息
            exc_text = super().formatException(exc_info)

            # 脱敏异常信息中的敏感数据
            redacted_exc = self.sensitive_data_manager.redact_text(
                exc_text,
                "log.exception"
            )

            return redacted_exc
        except Exception:
            # 如果脱敏失败，返回原始异常信息
            return super().formatException(exc_info)

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录，确保异常信息被脱敏

        Args:
            record: 日志记录

        Returns:
            格式化后的日志字符串
        """
        # 检查是否需要脱敏异常信息
        if hasattr(record, '_exc_info_needs_redaction') and record._exc_info_needs_redaction:
            # 保存原始异常信息
            original_exc_info = record.exc_info

            try:
                # 临时移除异常信息，避免基类格式化
                record.exc_info = None
                record.exc_text = None

                # 格式化基本消息
                result = super().format(record)

                # 手动添加脱敏后的异常信息
                if original_exc_info:
                    exc_text = self.formatException(original_exc_info)
                    if exc_text:
                        result += "\n" + exc_text

                return result
            finally:
                # 恢复异常信息
                record.exc_info = original_exc_info
                if hasattr(record, '_exc_info_needs_redaction'):
                    del record._exc_info_needs_redaction
        else:
            # 正常格式化
            return super().format(record)


class StructuredSensitiveFormatter(logging.Formatter):
    """结构化敏感数据日志格式化器"""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.sensitive_data_manager = get_sensitive_data_manager()
        self._json_formatter = logging.Formatter(
            fmt='%(message)s',
            datefmt=datefmt
        )

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为结构化JSON"""
        import json
        from datetime import datetime

        # 创建结构化日志条目
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
            "process": record.processName,
        }

        # 添加额外字段
        if hasattr(record, 'extra'):
            # 脱敏额外字段
            redacted_extra = self.sensitive_data_manager.redact_dict(
                record.extra,
                f"log.{record.name}.extra"
            )
            log_entry.update(redacted_extra)

        # 添加异常信息
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            # 脱敏异常信息
            redacted_exc = self.sensitive_data_manager.redact_text(
                exc_text,
                "log.exception"
            )
            log_entry["exception"] = redacted_exc

        # 脱敏整个日志条目（深度脱敏）
        redacted_entry = self.sensitive_data_manager.redact_dict(
            log_entry,
            f"log.{record.name}.entry"
        )

        return json.dumps(redacted_entry, ensure_ascii=False)


def add_sensitive_filter_to_logger(logger: logging.Logger, filter_name: str = "sensitive_data") -> SensitiveDataFilter:
    """
    为日志记录器添加敏感数据过滤器

    Args:
        logger: 日志记录器
        filter_name: 过滤器名称

    Returns:
        添加的过滤器实例
    """
    # 检查是否已存在同名过滤器
    for existing_filter in logger.filters:
        if hasattr(existing_filter, 'name') and existing_filter.name == filter_name:
            # 已存在，返回现有过滤器
            return existing_filter

    # 创建新过滤器
    sensitive_filter = SensitiveDataFilter(name=filter_name)
    logger.addFilter(sensitive_filter)

    # 为所有处理器更新格式化器（如果可能）
    for handler in logger.handlers:
        formatter = handler.formatter
        if formatter:
            # 如果已经是SensitiveDataFormatter，跳过
            if not isinstance(formatter, (SensitiveDataFormatter, StructuredSensitiveFormatter)):
                # 创建新的敏感数据格式化器，保持原有格式
                if hasattr(formatter, '_json_formatter'):
                    # 结构化日志
                    new_formatter = StructuredSensitiveFormatter()
                else:
                    # 传统日志
                    fmt = formatter._fmt if hasattr(formatter, '_fmt') else None
                    datefmt = formatter.datefmt if hasattr(formatter, 'datefmt') else None
                    new_formatter = SensitiveDataFormatter(fmt, datefmt)

                handler.setFormatter(new_formatter)

    return sensitive_filter


def add_sensitive_filter_to_all_loggers(filter_name: str = "sensitive_data") -> Dict[str, SensitiveDataFilter]:
    """
    为所有日志记录器添加敏感数据过滤器

    Args:
        filter_name: 过滤器名称

    Returns:
        添加的过滤器字典 {logger_name: filter_instance}
    """
    added_filters = {}

    # 获取所有已存在的日志记录器
    logger_dict = logging.Logger.manager.loggerDict

    for logger_name, logger_obj in logger_dict.items():
        if isinstance(logger_obj, logging.Logger):
            try:
                filter_instance = add_sensitive_filter_to_logger(logger_obj, filter_name)
                added_filters[logger_name] = filter_instance
            except Exception as e:
                # 记录错误但继续处理其他记录器
                logging.getLogger(__name__).warning(
                    f"为日志记录器 {logger_name} 添加敏感过滤器失败: {e}",
                    exc_info=False
                )

    # 为根日志记录器添加过滤器
    root_logger = logging.getLogger()
    if root_logger not in added_filters:
        try:
            filter_instance = add_sensitive_filter_to_logger(root_logger, filter_name)
            added_filters["root"] = filter_instance
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"为根日志记录器添加敏感过滤器失败: {e}",
                exc_info=False
            )

    return added_filters


def configure_logging_with_sensitive_filter(config: Dict[str, Any]) -> None:
    """
    配置日志系统并自动添加敏感数据过滤器

    Args:
        config: 日志配置
    """
    from .manager import init_logging, get_log_manager

    # 初始化日志系统
    log_manager = init_logging(config)

    # 为所有日志记录器添加敏感过滤器
    added_filters = add_sensitive_filter_to_all_loggers()

    # 记录配置信息
    logger = logging.getLogger(__name__)
    logger.info(
        f"敏感数据日志过滤器已配置，添加到 {len(added_filters)} 个日志记录器",
        extra={"sensitive_filter_count": len(added_filters)}
    )


# 导出常用函数
__all__ = [
    "SensitiveDataFilter",
    "SensitiveDataFormatter",
    "StructuredSensitiveFormatter",
    "add_sensitive_filter_to_logger",
    "add_sensitive_filter_to_all_loggers",
    "configure_logging_with_sensitive_filter",
]