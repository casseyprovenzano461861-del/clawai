"""
审计日志管理器
管理和存储审计事件，提供审计日志的CRUD操作
"""

import json
import gzip
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import threading
import logging
from contextlib import contextmanager
from queue import Queue, Empty

from ..schemas import (
    AuditEvent,
    AuditEventFilters,
    AuditEventPage,
    AuditEventSeverity,
    AuditEventStatus,
    AuditEventType
)

logger = logging.getLogger(__name__)


class AuditStorageBackend:
    """审计存储后端抽象类"""

    def save_event(self, event: AuditEvent) -> str:
        """保存审计事件"""
        raise NotImplementedError

    def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """获取审计事件"""
        raise NotImplementedError

    def search_events(self, filters: AuditEventFilters, page: int = 1, page_size: int = 50) -> AuditEventPage:
        """搜索审计事件"""
        raise NotImplementedError

    def delete_events(self, event_ids: List[str]) -> int:
        """删除审计事件"""
        raise NotImplementedError

    def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """清理旧事件"""
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        raise NotImplementedError


class FileAuditStorage(AuditStorageBackend):
    """文件系统审计存储后端"""

    def __init__(self, storage_dir: str = "logs/audit"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 按日期分目录存储
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.current_dir = self.storage_dir / self.current_date
        self.current_dir.mkdir(exist_ok=True)

        # 索引文件
        self.index_file = self.storage_dir / "index.json"
        self._index = self._load_index()

        # 缓存
        self._cache = {}
        self._cache_size = 1000

        # 线程锁，保护索引和缓存的并发访问
        self._lock = threading.RLock()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """加载索引文件"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载审计索引失败: {e}")
                return {}
        return {}

    def _save_index(self):
        """保存索引文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存审计索引失败: {e}")

    def _get_event_file_path(self, event_id: str) -> Path:
        """获取事件文件路径"""
        # 使用日期目录
        date_dir = self.storage_dir / self.current_date
        date_dir.mkdir(exist_ok=True)
        return date_dir / f"{event_id}.json.gz"

    def _calculate_event_hash(self, event_dict: Dict[str, Any]) -> str:
        """计算事件哈希值，用于完整性验证"""
        # 移除可变字段
        event_copy = event_dict.copy()
        event_copy.pop("event_id", None)
        event_copy.pop("timestamp", None)

        # 计算哈希
        event_str = json.dumps(event_copy, sort_keys=True, default=str)
        return hashlib.sha256(event_str.encode('utf-8')).hexdigest()

    def save_event(self, event: AuditEvent) -> str:
        """保存审计事件到文件系统"""
        try:
            # 确保日期目录是最新的
            today = datetime.now().strftime("%Y-%m-%d")
            if today != self.current_date:
                self.current_date = today
                self.current_dir = self.storage_dir / self.current_date
                self.current_dir.mkdir(exist_ok=True)

            # 转换为字典
            event_dict = event.dict()
            event_id = event_dict["event_id"]

            # 添加哈希值用于完整性验证
            event_dict["_hash"] = self._calculate_event_hash(event_dict)
            event_dict["_saved_at"] = datetime.now().isoformat()

            # 写入压缩的JSON文件
            file_path = self._get_event_file_path(event_id)
            with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                json.dump(event_dict, f, indent=2, default=str)

            # 更新索引
            self._index[event_id] = {
                "event_id": event_id,
                "event_type": event_dict["event_type"],
                "severity": event_dict["event_severity"],
                "status": event_dict["event_status"],
                "timestamp": event_dict["timestamp"],
                "actor": event_dict["actor"],
                "action": event_dict["action"],
                "module": event_dict.get("module"),
                "file_path": str(file_path.relative_to(self.storage_dir)),
                "is_sensitive": event_dict["is_sensitive"],
                "requires_review": event_dict["requires_review"]
            }

            # 保存索引
            self._save_index()

            # 添加到缓存
            if len(self._cache) >= self._cache_size:
                # 移除最旧的缓存项
                oldest_key = next(iter(self._cache))
                self._cache.pop(oldest_key)
            self._cache[event_id] = event_dict

            logger.debug(f"审计事件保存成功: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"保存审计事件失败: {e}")
            raise

    def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """从文件系统获取审计事件"""
        try:
            # 先从缓存查找
            if event_id in self._cache:
                return AuditEvent(**self._cache[event_id])

            # 从索引查找文件路径
            if event_id not in self._index:
                return None

            index_entry = self._index[event_id]
            file_path = self.storage_dir / index_entry["file_path"]

            if not file_path.exists():
                logger.warning(f"审计事件文件不存在: {file_path}")
                return None

            # 读取并解析事件
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                event_dict = json.load(f)

            # 验证哈希值
            stored_hash = event_dict.pop("_hash", None)
            event_dict.pop("_saved_at", None)

            if stored_hash:
                current_hash = self._calculate_event_hash(event_dict)
                if stored_hash != current_hash:
                    logger.error(f"审计事件哈希验证失败: {event_id}")
                    # 仍然返回事件，但记录警告
                    event_dict["_integrity_check"] = "failed"

            event = AuditEvent(**event_dict)

            # 添加到缓存
            if len(self._cache) >= self._cache_size:
                oldest_key = next(iter(self._cache))
                self._cache.pop(oldest_key)
            self._cache[event_id] = event_dict

            return event

        except Exception as e:
            logger.error(f"获取审计事件失败: {e}")
            return None

    def search_events(self, filters: AuditEventFilters, page: int = 1, page_size: int = 50) -> AuditEventPage:
        """搜索审计事件"""
        try:
            # 从索引过滤事件
            filtered_events = []

            # 使用锁保护索引访问
            with self._lock:
                # 复制索引键以避免迭代时修改
                event_ids = list(self._index.keys())

            # 遍历复制的键列表
            for event_id in event_ids:
                # 再次获取锁以读取索引条目
                with self._lock:
                    index_entry = self._index.get(event_id)
                    if not index_entry:
                        continue

                # 应用过滤器
                if not self._matches_filters(index_entry, filters):
                    continue

                # 获取完整事件
                event = self.get_event(event_id)
                if event:
                    filtered_events.append(event)

            # 按时间戳排序（最新的在前）
            filtered_events.sort(key=lambda x: x.timestamp, reverse=True)

            # 分页
            total = len(filtered_events)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            paginated_events = filtered_events[start_idx:end_idx]

            return AuditEventPage(
                events=paginated_events,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1
            )

        except Exception as e:
            logger.error(f"搜索审计事件失败: {e}")
            return AuditEventPage()

    def _matches_filters(self, index_entry: Dict[str, Any], filters: AuditEventFilters) -> bool:
        """检查索引条目是否匹配过滤器"""
        # 事件类型过滤
        if filters.event_types and index_entry.get("event_type") not in filters.event_types:
            return False

        # 严重级别过滤
        if filters.severities and index_entry.get("severity") not in filters.severities:
            return False

        # 状态过滤
        if filters.statuses and index_entry.get("status") not in filters.statuses:
            return False

        # 时间过滤
        if filters.start_time or filters.end_time:
            timestamp = index_entry.get("timestamp")
            if timestamp:
                # 处理datetime对象和字符串两种情况
                if hasattr(timestamp, 'isoformat'):
                    # datetime对象
                    event_time = timestamp
                else:
                    # 字符串
                    try:
                        # 尝试解析ISO格式字符串
                        timestamp_str = str(timestamp).replace("Z", "+00:00")
                        event_time = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        # 如果解析失败，跳过时间过滤
                        event_time = None

                if event_time:
                    if filters.start_time and event_time < filters.start_time:
                        return False
                    if filters.end_time and event_time > filters.end_time:
                        return False

        # 用户过滤
        if filters.user_ids:
            actor = index_entry.get("actor", {})
            if actor.get("user_id") not in filters.user_ids:
                return False

        if filters.usernames:
            actor = index_entry.get("actor", {})
            if actor.get("username") not in filters.usernames:
                return False

        # 敏感操作过滤
        if filters.is_sensitive is not None:
            if index_entry.get("is_sensitive") != filters.is_sensitive:
                return False

        # 需要审核过滤
        if filters.requires_review is not None:
            if index_entry.get("requires_review") != filters.requires_review:
                return False

        # 模块过滤
        if filters.module and index_entry.get("module") != filters.module:
            return False

        # 文本搜索
        if filters.search_text:
            search_text = filters.search_text.lower()
            action = index_entry.get("action", "").lower()
            if search_text not in action:
                return False

        return True

    def delete_events(self, event_ids: List[str]) -> int:
        """删除审计事件"""
        deleted_count = 0
        for event_id in event_ids:
            try:
                if event_id in self._index:
                    index_entry = self._index[event_id]
                    file_path = self.storage_dir / index_entry["file_path"]

                    # 删除文件
                    if file_path.exists():
                        file_path.unlink()

                    # 删除索引条目
                    del self._index[event_id]

                    # 删除缓存
                    if event_id in self._cache:
                        del self._cache[event_id]

                    deleted_count += 1

            except Exception as e:
                logger.error(f"删除审计事件失败 {event_id}: {e}")

        # 保存更新后的索引
        if deleted_count > 0:
            self._save_index()

        return deleted_count

    def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """清理旧事件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")

            deleted_count = 0
            event_ids_to_delete = []

            # 查找旧事件
            for event_id, index_entry in self._index.items():
                event_time = datetime.fromisoformat(index_entry.get("timestamp", "").replace("Z", "+00:00"))
                if event_time < cutoff_date:
                    event_ids_to_delete.append(event_id)

            # 删除事件
            deleted_count = self.delete_events(event_ids_to_delete)

            # 清理旧目录
            for item in self.storage_dir.iterdir():
                if item.is_dir() and item.name < cutoff_str:
                    try:
                        # 删除目录及其内容
                        import shutil
                        shutil.rmtree(item)
                        logger.info(f"清理审计目录: {item}")
                    except Exception as e:
                        logger.error(f"清理审计目录失败 {item}: {e}")

            logger.info(f"清理审计事件完成: 删除了 {deleted_count} 个事件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理旧事件失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            stats = {
                "total_events": len(self._index),
                "storage_dir": str(self.storage_dir),
                "index_file": str(self.index_file),
                "cache_size": len(self._cache),
            }

            # 按类型统计
            type_stats = {}
            for index_entry in self._index.values():
                event_type = index_entry.get("event_type")
                type_stats[event_type] = type_stats.get(event_type, 0) + 1
            stats["events_by_type"] = type_stats

            # 按严重级别统计
            severity_stats = {}
            for index_entry in self._index.values():
                severity = index_entry.get("severity")
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
            stats["events_by_severity"] = severity_stats

            # 按状态统计
            status_stats = {}
            for index_entry in self._index.values():
                status = index_entry.get("status")
                status_stats[status] = status_stats.get(status, 0) + 1
            stats["events_by_status"] = status_stats

            # 按日期统计
            date_stats = {}
            for index_entry in self._index.values():
                timestamp = index_entry.get("timestamp")
                if timestamp:
                    # 处理datetime对象和字符串两种情况
                    if hasattr(timestamp, 'strftime'):
                        # datetime对象
                        date_str = timestamp.strftime("%Y-%m-%d")
                    else:
                        # 字符串
                        try:
                            date_str = str(timestamp).split("T")[0]
                        except:
                            date_str = str(timestamp)[:10]  # 取前10个字符
                    date_stats[date_str] = date_stats.get(date_str, 0) + 1
            stats["events_by_date"] = date_stats

            return stats

        except Exception as e:
            logger.error(f"获取审计统计失败: {e}")
            return {}


class AuditManager:
    """审计管理器"""

    def __init__(self, storage_backend: Optional[AuditStorageBackend] = None):
        self.storage_backend = storage_backend or FileAuditStorage()

        # 异步处理队列
        self._queue = Queue(maxsize=10000)
        self._worker_thread = None
        self._running = False

        # 初始化
        self._start_worker()

    def _start_worker(self):
        """启动后台工作线程"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._running = True
            self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._worker_thread.start()
            logger.info("审计管理器工作线程已启动")

    def _process_queue(self):
        """处理队列中的审计事件"""
        while self._running:
            try:
                # 从队列获取事件，设置超时以避免永久阻塞
                event = self._queue.get(timeout=1.0)
                try:
                    self._save_event_sync(event)
                except Exception as e:
                    logger.error(f"处理审计事件失败: {e}")
                finally:
                    self._queue.task_done()
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"审计工作线程异常: {e}")

    def _save_event_sync(self, event: AuditEvent):
        """同步保存事件"""
        event_id = self.storage_backend.save_event(event)
        logger.debug(f"审计事件保存成功: {event_id}")

    def log_event(self, event: AuditEvent):
        """记录审计事件（异步）"""
        try:
            # 尝试立即添加到队列
            self._queue.put_nowait(event)
        except Exception as e:
            logger.error(f"审计事件入队失败: {e}")
            # 队列已满，同步保存
            self._save_event_sync(event)

    def log_event_sync(self, event: AuditEvent) -> str:
        """同步记录审计事件"""
        return self.storage_backend.save_event(event)

    def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """获取审计事件"""
        return self.storage_backend.get_event(event_id)

    def search_events(self, filters: AuditEventFilters, page: int = 1, page_size: int = 50) -> AuditEventPage:
        """搜索审计事件"""
        return self.storage_backend.search_events(filters, page, page_size)

    def delete_events(self, event_ids: List[str]) -> int:
        """删除审计事件"""
        return self.storage_backend.delete_events(event_ids)

    def cleanup_old_events(self, days_to_keep: int = 90) -> int:
        """清理旧事件"""
        return self.storage_backend.cleanup_old_events(days_to_keep)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.storage_backend.get_stats()

    def stop(self):
        """停止审计管理器"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
            logger.info("审计管理器已停止")

    @contextmanager
    def audit_context(self, actor, action, description=None, **kwargs):
        """审计上下文管理器，自动记录开始和结束"""
        # 从kwargs中提取event_type，避免重复传递
        event_type = kwargs.pop("event_type", AuditEventType.SYSTEM_START)

        start_time = datetime.now()
        start_event = AuditEvent(
            event_id=f"context_{start_time.timestamp()}",
            event_type=event_type,
            actor=actor,
            action=f"开始: {action}",
            description=description,
            **kwargs
        )
        self.log_event(start_event)

        try:
            yield start_event.event_id
        except Exception as e:
            # 记录失败事件
            error_event = AuditEvent(
                event_id=f"error_{datetime.now().timestamp()}",
                event_type=event_type,
                actor=actor,
                action=f"失败: {action}",
                description=f"{description} - 失败: {str(e)}",
                event_status=AuditEventStatus.FAILURE,
                event_severity=AuditEventSeverity.ERROR,
                **kwargs
            )
            self.log_event(error_event)
            raise
        finally:
            # 记录结束事件
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            end_event = AuditEvent(
                event_id=f"end_{end_time.timestamp()}",
                event_type=event_type,
                actor=actor,
                action=f"完成: {action}",
                description=f"{description} - 耗时: {duration_ms}ms",
                duration_ms=duration_ms,
                **kwargs
            )
            self.log_event(end_event)


# 全局审计管理器实例
_global_audit_manager = None


def get_audit_manager() -> AuditManager:
    """获取全局审计管理器"""
    global _global_audit_manager
    if _global_audit_manager is None:
        _global_audit_manager = AuditManager()
    return _global_audit_manager


def init_audit_system(storage_backend: Optional[AuditStorageBackend] = None):
    """初始化审计系统"""
    global _global_audit_manager
    _global_audit_manager = AuditManager(storage_backend)
    return _global_audit_manager