"""
审计日志系统
提供完整的审计日志功能，包括事件记录、存储、查询和报告
"""

from .manager import (
    AuditStorageBackend,
    FileAuditStorage,
    AuditManager,
    get_audit_manager,
    init_audit_system
)

from .api import router as audit_router
from .middleware import AuditMiddleware, setup_audit_middleware

__all__ = [
    # 管理器
    "AuditStorageBackend",
    "FileAuditStorage",
    "AuditManager",
    "get_audit_manager",
    "init_audit_system",

    # API
    "audit_router",

    # 中间件
    "AuditMiddleware",
    "setup_audit_middleware",
]

# 版本信息
__version__ = "1.0.0"
__author__ = "ClawAI Team"
__description__ = "ClawAI 审计日志系统"