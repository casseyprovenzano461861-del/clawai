#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 错误处理和恢复建议
提供用户友好的错误提示和可操作的恢复建议
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"
    AUTH = "auth"
    TOOL = "tool"
    PERMISSION = "permission"
    SYNTAX = "syntax"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorSuggestion:
    """错误建议"""
    action: str
    command: Optional[str] = None
    description: str = ""


class ErrorHandler:
    """错误处理器 - 生成友好的错误消息和恢复建议"""

    # 错误模式 → 分类 + 建议
    ERROR_PATTERNS = {
        # 网络错误
        "Connection refused": {
            "category": ErrorCategory.NETWORK,
            "suggestions": [
                ErrorSuggestion(
                    action="检查目标地址是否正确",
                    command="/status"
                ),
                ErrorSuggestion(
                    action="检查防火墙设置",
                    description="确保目标端口可访问"
                ),
                ErrorSuggestion(
                    action="尝试 ping 目标",
                    command="!ping -c 3 example.com"
                ),
            ]
        },
        "timeout": {
            "category": ErrorCategory.TIMEOUT,
            "suggestions": [
                ErrorSuggestion(
                    action="增加超时时间",
                    description="使用 --timeout 选项"
                ),
                ErrorSuggestion(
                    action="检查网络连接",
                    command="!ping example.com"
                ),
            ]
        },
        "Connection timed out": {
            "category": ErrorCategory.NETWORK,
            "suggestions": [
                ErrorSuggestion(
                    action="检查网络连接",
                    command="!ping example.com"
                ),
                ErrorSuggestion(
                    action="稍后重试",
                    description="目标可能暂时不可用"
                ),
            ]
        },
        "Client network socket disconnected": {
            "category": ErrorCategory.NETWORK,
            "suggestions": [
                ErrorSuggestion(
                    action="检查代理设置",
                    description="如果使用 VPN 或代理，请确保连接稳定"
                ),
                ErrorSuggestion(
                    action="检查网络连接",
                    command="!ping example.com"
                ),
            ]
        },

        # 认证错误
        "401": {
            "category": ErrorCategory.AUTH,
            "suggestions": [
                ErrorSuggestion(
                    action="检查 API Key",
                    description="在 .env 文件中配置正确的 API Key"
                ),
                ErrorSuggestion(
                    action="查看配置",
                    command="/config"
                ),
            ]
        },
        "403": {
            "category": ErrorCategory.AUTH,
            "suggestions": [
                ErrorSuggestion(
                    action="检查访问权限",
                    description="确认您有权限访问该目标"
                ),
                ErrorSuggestion(
                    action="设置 Cookie",
                    description="使用 /cookie 命令设置认证 Cookie"
                ),
            ]
        },
        "unauthorized": {
            "category": ErrorCategory.AUTH,
            "suggestions": [
                ErrorSuggestion(
                    action="重新登录",
                    description="可能需要重新获取认证信息"
                ),
            ]
        },
        "API key": {
            "category": ErrorCategory.AUTH,
            "suggestions": [
                ErrorSuggestion(
                    action="配置 API Key",
                    description="在 .env 文件中设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY"
                ),
                ErrorSuggestion(
                    action="查看配置",
                    command="/config"
                ),
            ]
        },

        # 工具错误
        "command not found": {
            "category": ErrorCategory.TOOL,
            "suggestions": [
                ErrorSuggestion(
                    action="检查工具是否安装",
                    description="使用 /tools check 命令检查工具状态"
                ),
                ErrorSuggestion(
                    action="查看可用工具",
                    command="/tools list"
                ),
            ]
        },
        "tool not found": {
            "category": ErrorCategory.TOOL,
            "suggestions": [
                ErrorSuggestion(
                    action="查看可用命令",
                    command="/help"
                ),
            ]
        },
        "subprocess": {
            "category": ErrorCategory.TOOL,
            "suggestions": [
                ErrorSuggestion(
                    action="检查后端服务",
                    description="确保后端服务已启动: python start.py --backend"
                ),
                ErrorSuggestion(
                    action="查看系统状态",
                    command="/status"
                ),
            ]
        },

        # 权限错误
        "Permission denied": {
            "category": ErrorCategory.PERMISSION,
            "suggestions": [
                ErrorSuggestion(
                    action="使用管理员权限",
                    description="在 Windows 上以管理员身份运行"
                ),
                ErrorSuggestion(
                    action="检查文件权限",
                    description="确保有权限访问目标路径"
                ),
            ]
        },
        "Access is denied": {
            "category": ErrorCategory.PERMISSION,
            "suggestions": [
                ErrorSuggestion(
                    action="使用管理员权限",
                    description="在 Windows 上以管理员身份运行"
                ),
            ]
        },

        # 语法错误
        "invalid syntax": {
            "category": ErrorCategory.SYNTAX,
            "suggestions": [
                ErrorSuggestion(
                    action="检查命令格式",
                    description="使用 /help 查看正确的命令格式"
                ),
                ErrorSuggestion(
                    action="查看命令示例",
                    command="/help"
                ),
            ]
        },
        "unexpected token": {
            "category": ErrorCategory.SYNTAX,
            "suggestions": [
                ErrorSuggestion(
                    action="检查输入格式",
                    description="确保使用正确的引号和转义"
                ),
            ]
        },
    }

    @classmethod
    def analyze(cls, error_message: str) -> tuple[ErrorCategory, List[ErrorSuggestion]]:
        """分析错误消息，返回分类和建议

        Args:
            error_message: 错误消息文本

        Returns:
            (ErrorCategory, List[ErrorSuggestion])
        """
        error_lower = error_message.lower()

        # 遍历错误模式，找到匹配项
        for pattern, config in cls.ERROR_PATTERNS.items():
            if pattern.lower() in error_lower:
                return config["category"], config["suggestions"]

        # 未匹配模式
        return ErrorCategory.UNKNOWN, [
            ErrorSuggestion(
                action="查看日志",
                description="使用 -v 选项获取详细日志"
            ),
            ErrorSuggestion(
                action="查看帮助",
                command="/help"
            ),
        ]

    @classmethod
    def format_message(cls, error_message: str, include_suggestions: bool = True) -> str:
        """格式化错误消息

        Args:
            error_message: 原始错误消息
            include_suggestions: 是否包含恢复建议

        Returns:
            格式化后的错误消息
        """
        from rich.text import Text

        category, suggestions = cls.analyze(error_message)

        # 错误分类图标
        icons = {
            ErrorCategory.NETWORK: "🌐",
            ErrorCategory.AUTH: "🔑",
            ErrorCategory.TOOL: "🔧",
            ErrorCategory.PERMISSION: "🔒",
            ErrorCategory.SYNTAX: "❓",
            ErrorCategory.TIMEOUT: "⏱️",
            ErrorCategory.UNKNOWN: "⚠️",
        }
        icon = icons.get(category, "⚠️")

        # 构建输出
        lines = [f"\n{icon} {error_message}\n"]

        if include_suggestions:
            lines.append("💡 恢复建议:")
            for i, sugg in enumerate(suggestions[:3], 1):  # 最多显示 3 条建议
                lines.append(f"  {i}. {sugg.action}")
                if sugg.command:
                    lines.append(f"     命令: {sugg.command}")
                if sugg.description:
                    lines.append(f"     说明: {sugg.description}")

        return "\n".join(lines)


def handle_error(error: Exception, console=None) -> str:
    """处理异常并返回友好的错误消息

    Args:
        error: 异常对象
        console: rich.Console 实例（可选）

    Returns:
        格式化的错误消息
    """
    error_message = str(error)

    # 根据异常类型特殊处理
    if isinstance(error, (ConnectionError, OSError)):
        error_message = f"连接错误: {error_message}"
    elif isinstance(error, TimeoutError):
        error_message = f"超时错误: {error_message}"
    elif isinstance(error, PermissionError):
        error_message = f"权限错误: {error_message}"

    formatted = ErrorHandler.format_message(error_message)

    if console:
        from rich.text import Text
        console.print(Text(formatted, style="rgb(255,60,60)"))

    return formatted
