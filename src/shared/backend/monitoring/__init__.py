"""
监控模块
提供系统监控、指标收集和告警功能
"""

__all__ = ['metrics', 'AlertLevel', 'Alert', 'SystemMetrics', 'AlertManager', 'ComprehensiveMonitor']

# 导出指标模块
from . import metrics

# 保留原始类的导入以避免破坏现有代码
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"        # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"      # 错误
    CRITICAL = "critical" # 严重


@dataclass
class Alert:
    """告警信息"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "metadata": self.metadata
        }


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    thread_count: int
    open_files: int
    connections: int

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_percent": round(self.memory_percent, 2),
            "memory_used_mb": round(self.memory_used_mb, 2),
            "memory_total_mb": round(self.memory_total_mb, 2),
            "disk_percent": round(self.disk_percent, 2),
            "disk_used_gb": round(self.disk_used_gb, 2),
            "disk_total_gb": round(self.disk_total_gb, 2),
            "network_sent_mb": round(self.network_sent_mb, 2),
            "network_recv_mb": round(self.network_recv_mb, 2),
            "process_count": self.process_count,
            "thread_count": self.thread_count,
            "open_files": self.open_files,
            "connections": self.connections
        }


class AlertManager:
    """告警管理器（简化版本）"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        logger.info("AlertManager 初始化完成")

    def create_alert(self, level: AlertLevel, title: str, message: str, source: str, metadata: Dict[str, Any] = None) -> Alert:
        """创建告警"""
        import time
        from datetime import datetime

        alert_id = f"alert_{int(time.time())}_{len(self.alerts)}"

        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.alerts[alert_id] = alert
        logger.info(f"告警已创建 - {level}: {title}")

        return alert


class ComprehensiveMonitor:
    """
    综合监控系统（简化版本）
    """

    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.alert_manager = AlertManager()
        logger.info(f"ComprehensiveMonitor 初始化完成 - 收集间隔: {collection_interval}s")