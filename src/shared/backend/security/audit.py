# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
安全审计系统
提供全面的安全审计、监控和报告功能
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import hashlib
import threading
from collections import defaultdict

from config import config


class AuditEventType(Enum):
    """审计事件类型枚举"""
    
    # 认证相关事件
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_LOCKED = "login_locked"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_REVOKED = "token_revoked"
    
    # MFA相关事件
    MFA_SETUP = "mfa_setup"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"
    MFA_DISABLED = "mfa_disabled"
    
    # 权限相关事件
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # 安全相关事件
    SECURITY_ALERT = "security_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    INJECTION_ATTEMPT = "injection_attempt"
    MALICIOUS_INPUT = "malicious_input"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # 系统操作事件
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIG_CHANGE = "config_change"
    DATABASE_BACKUP = "database_backup"
    DATABASE_RESTORE = "database_restore"
    
    # 攻击相关事件
    ATTACK_STARTED = "attack_started"
    ATTACK_COMPLETED = "attack_completed"
    ATTACK_FAILED = "attack_failed"
    TOOL_EXECUTION = "tool_execution"
    CVE_DETECTION = "cve_detection"
    
    # 用户操作事件
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PASSWORD_CHANGED = "password_changed"
    PROFILE_UPDATED = "profile_updated"
    
    # API访问事件
    API_CALL = "api_call"
    API_ERROR = "api_error"
    API_UNAUTHORIZED = "api_unauthorized"
    
    # 审计系统事件
    AUDIT_LOG_CLEARED = "audit_log_cleared"
    AUDIT_LOG_EXPORTED = "audit_log_exported"
    AUDIT_LOG_TAMPERED = "audit_log_tampered"


class AuditSeverity(Enum):
    """审计事件严重性级别"""
    
    DEBUG = "debug"        # 调试信息
    INFO = "info"          # 普通信息
    NOTICE = "notice"      # 需要注意
    WARNING = "warning"    # 警告
    ERROR = "error"        # 错误
    CRITICAL = "critical"  # 严重


class AuditEntry:
    """审计日志条目"""
    
    def __init__(self, 
                 event_type: AuditEventType,
                 user: str,
                 action: str,
                 details: Dict[str, Any] = None,
                 severity: AuditSeverity = AuditSeverity.INFO,
                 ip_address: str = None,
                 user_agent: str = None,
                 request_id: str = None):
        
        self.id = self._generate_id()
        self.timestamp = datetime.now().isoformat()
        self.event_type = event_type
        self.user = user
        self.action = action
        self.details = details or {}
        self.severity = severity
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_id = request_id
        self.success = severity in [AuditSeverity.DEBUG, AuditSeverity.INFO, AuditSeverity.NOTICE]
        
        # 计算哈希用于完整性验证
        self.hash = self._calculate_hash()
    
    def _generate_id(self) -> str:
        """生成唯一标识符"""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_hash(self) -> str:
        """计算条目哈希值"""
        content = f"{self.id}{self.timestamp}{self.event_type.value}{self.user}{self.action}"
        if self.details:
            content += json.dumps(self.details, sort_keys=True)
        
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def verify_integrity(self) -> bool:
        """验证条目完整性"""
        return self.hash == self._calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "user": self.user,
            "action": self.action,
            "details": self.details,
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "success": self.success,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEntry':
        """从字典创建审计条目"""
        entry = cls(
            event_type=AuditEventType(data["event_type"]),
            user=data["user"],
            action=data["action"],
            details=data.get("details", {}),
            severity=AuditSeverity(data["severity"]),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            request_id=data.get("request_id")
        )
        
        # 恢复ID和时间戳
        entry.id = data["id"]
        entry.timestamp = data["timestamp"]
        entry.hash = data["hash"]
        
        return entry


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, 
                 log_file: str = None,
                 enable_real_time: bool = True,
                 enable_compression: bool = True,
                 retention_days: int = 90):
        
        self.log_file = log_file or "logs/security_audit.jsonl"
        self.enable_real_time = enable_real_time
        self.enable_compression = enable_compression
        self.retention_days = retention_days
        
        # 内存中的日志缓冲区
        self.buffer = []
        self.buffer_lock = threading.Lock()
        self.buffer_size = 100
        
        # 统计信息
        self.stats = {
            "total_entries": 0,
            "by_event_type": defaultdict(int),
            "by_severity": defaultdict(int),
            "by_user": defaultdict(int),
            "last_entry_time": None
        }
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # 自动清理旧日志
        self._cleanup_old_logs()
        
        # 启动后台处理线程
        if enable_real_time:
            self._start_background_processing()
    
    def _start_background_processing(self):
        """启动后台处理线程"""
        def process_buffer():
            while True:
                time.sleep(5)  # 每5秒处理一次
                self._flush_buffer()
        
        thread = threading.Thread(target=process_buffer, daemon=True)
        thread.start()
    
    def _cleanup_old_logs(self):
        """清理旧的审计日志"""
        try:
            log_dir = os.path.dirname(self.log_file)
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for filename in os.listdir(log_dir):
                if filename.startswith("security_audit") and filename.endswith(".jsonl"):
                    filepath = os.path.join(log_dir, filename)
                    
                    # 获取文件修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if mtime < cutoff_date:
                        os.remove(filepath)
                        self._log_system_event(f"清理旧日志文件: {filename}")
                        
        except Exception as e:
            print(f"清理旧日志失败: {str(e)}")
    
    def _log_system_event(self, message: str):
        """记录系统事件"""
        print(f"[AUDIT SYSTEM] {message}")
    
    def log_event(self,
                  event_type: AuditEventType,
                  user: str,
                  action: str,
                  details: Dict[str, Any] = None,
                  severity: AuditSeverity = AuditSeverity.INFO,
                  ip_address: str = None,
                  user_agent: str = None,
                  request_id: str = None) -> AuditEntry:
        """记录审计事件"""
        try:
            # 从请求中获取信息
            from flask import request
            if request and ip_address is None:
                ip_address = request.remote_addr
            if request and user_agent is None:
                user_agent = request.headers.get('User-Agent')
            
            # 创建审计条目
            entry = AuditEntry(
                event_type=event_type,
                user=user,
                action=action,
                details=details,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id
            )
            
            # 添加到缓冲区
            with self.buffer_lock:
                self.buffer.append(entry)
                
                # 更新统计信息
                self._update_stats(entry)
                
                # 如果缓冲区满了，立即刷新
                if len(self.buffer) >= self.buffer_size:
                    self._flush_buffer()
            
            # 实时输出到控制台
            if self.enable_real_time:
                self._print_entry(entry)
            
            return entry
            
        except Exception as e:
            print(f"记录审计事件失败: {str(e)}")
            
            # 创建错误条目
            error_entry = AuditEntry(
                event_type=AuditEventType.AUDIT_LOG_TAMPERED,
                user="system",
                action="audit_logging_error",
                details={"error": str(e)},
                severity=AuditSeverity.ERROR
            )
            return error_entry
    
    def _update_stats(self, entry: AuditEntry):
        """更新统计信息"""
        self.stats["total_entries"] += 1
        self.stats["by_event_type"][entry.event_type.value] += 1
        self.stats["by_severity"][entry.severity.value] += 1
        self.stats["by_user"][entry.user] += 1
        self.stats["last_entry_time"] = entry.timestamp
    
    def _print_entry(self, entry: AuditEntry):
        """打印审计条目到控制台"""
        color_map = {
            AuditSeverity.DEBUG: "\033[90m",    # 灰色
            AuditSeverity.INFO: "\033[92m",     # 绿色
            AuditSeverity.NOTICE: "\033[94m",   # 蓝色
            AuditSeverity.WARNING: "\033[93m",  # 黄色
            AuditSeverity.ERROR: "\033[91m",    # 红色
            AuditSeverity.CRITICAL: "\033[95m"  # 品红
        }
        
        reset = "\033[0m"
        color = color_map.get(entry.severity, "\033[92m")
        
        timestamp = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        user_display = entry.user[:15] + "..." if len(entry.user) > 15 else entry.user
        
        print(f"{color}[{timestamp}] {entry.event_type.value.upper()}: {user_display} - {entry.action}{reset}")
    
    def _flush_buffer(self):
        """将缓冲区内容写入文件"""
        with self.buffer_lock:
            if not self.buffer:
                return
            
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    for entry in self.buffer:
                        f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + '\n')
                
                # 清空缓冲区
                self.buffer.clear()
                
            except Exception as e:
                print(f"写入审计日志失败: {str(e)}")
    
    def get_recent_entries(self, 
                          limit: int = 100,
                          event_type: AuditEventType = None,
                          user: str = None,
                          severity: AuditSeverity = None,
                          start_time: datetime = None,
                          end_time: datetime = None) -> List[AuditEntry]:
        """获取最近的审计条目"""
        entries = []
        count = 0
        
        try:
            if not os.path.exists(self.log_file):
                return entries
            
            # 从文件末尾开始读取
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 读取整个文件
                lines = f.readlines()
                
                # 从后往前处理
                for line in reversed(lines):
                    if count >= limit:
                        break
                    
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry.from_dict(data)
                        
                        # 应用过滤器
                        if event_type and entry.event_type != event_type:
                            continue
                        if user and entry.user != user:
                            continue
                        if severity and entry.severity != severity:
                            continue
                        if start_time and datetime.fromisoformat(entry.timestamp) < start_time:
                            continue
                        if end_time and datetime.fromisoformat(entry.timestamp) > end_time:
                            continue
                        
                        # 验证完整性
                        if not entry.verify_integrity():
                            entry.details["integrity_error"] = "Hash verification failed"
                            entry.severity = AuditSeverity.WARNING
                        
                        entries.append(entry)
                        count += 1
                        
                    except json.JSONDecodeError:
                        continue
            
            # 添加缓冲区中的条目
            with self.buffer_lock:
                for entry in self.buffer:
                    if count >= limit:
                        break
                    
                    # 应用过滤器
                    if event_type and entry.event_type != event_type:
                        continue
                    if user and entry.user != user:
                        continue
                    if severity and entry.severity != severity:
                        continue
                    if start_time and datetime.fromisoformat(entry.timestamp) < start_time:
                        continue
                    if end_time and datetime.fromisoformat(entry.timestamp) > end_time:
                        continue
                    
                    entries.append(entry)
                    count += 1
            
            # 按时间戳排序
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            print(f"读取审计日志失败: {str(e)}")
        
        return entries
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取审计统计信息"""
        # 从文件中读取额外的统计信息
        stats = self.stats.copy()
        
        try:
            # 分析日志文件
            if os.path.exists(self.log_file):
                event_counts = defaultdict(int)
                severity_counts = defaultdict(int)
                user_counts = defaultdict(int)
                
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            event_counts[data["event_type"]] += 1
                            severity_counts[data["severity"]] += 1
                            user_counts[data["user"]] += 1
                        except:
                            continue
                
                # 合并内存中的统计信息
                for event_type, count in event_counts.items():
                    stats["by_event_type"][event_type] += count
                
                for severity, count in severity_counts.items():
                    stats["by_severity"][severity] += count
                
                for user, count in user_counts.items():
                    stats["by_user"][user] += count
        
        except Exception as e:
            print(f"获取审计统计信息失败: {str(e)}")
        
        return stats
    
    def export_logs(self, 
                   output_file: str,
                   start_time: datetime = None,
                   end_time: datetime = None,
                   event_types: List[str] = None) -> bool:
        """导出审计日志"""
        try:
            entries = []
            
            # 获取符合条件的条目
            for event_type in (event_types or []):
                try:
                    audit_event_type = AuditEventType(event_type)
                    entries.extend(self.get_recent_entries(
                        limit=10000,
                        event_type=audit_event_type,
                        start_time=start_time,
                        end_time=end_time
                    ))
                except ValueError:
                    continue
            
            # 如果没有指定事件类型，获取所有条目
            if not entries:
                entries = self.get_recent_entries(
                    limit=10000,
                    start_time=start_time,
                    end_time=end_time
                )
            
            # 转换为字典列表
            export_data = [entry.to_dict() for entry in entries]
            
            # 添加导出元数据
            export_metadata = {
                "export_time": datetime.now().isoformat(),
                "total_entries": len(export_data),
                "time_range": {
                    "start": start_time.isoformat() if start_time else "unknown",
                    "end": end_time.isoformat() if end_time else "unknown"
                },
                "event_types": event_types or ["all"]
            }
            
            export_content = {
                "metadata": export_metadata,
                "entries": export_data
            }
            
            # 写入文件
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_content, f, ensure_ascii=False, indent=2)
            
            # 记录导出事件
            self.log_event(
                event_type=AuditEventType.AUDIT_LOG_EXPORTED,
                user="system",
                action="export_audit_logs",
                details={
                    "output_file": output_file,
                    "entry_count": len(export_data)
                },
                severity=AuditSeverity.INFO
            )
            
            return True
            
        except Exception as e:
            print(f"导出审计日志失败: {str(e)}")
            return False
    
    def clear_logs(self, older_than_days: int = 30) -> bool:
        """清理指定天数前的审计日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            # 获取要保留的条目
            entries_to_keep = self.get_recent_entries(
                limit=100000,
                start_time=cutoff_date
            )
            
            # 如果没有需要保留的条目，直接删除文件
            if not entries_to_keep:
                if os.path.exists(self.log_file):
                    os.remove(self.log_file)
            else:
                # 写入保留的条目到新文件
                temp_file = self.log_file + ".temp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    for entry in entries_to_keep:
                        f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + '\n')
                
                # 替换原文件
                os.replace(temp_file, self.log_file)
            
            # 记录清理事件
            self.log_event(
                event_type=AuditEventType.AUDIT_LOG_CLEARED,
                user="system",
                action="clear_audit_logs",
                details={
                    "older_than_days": older_than_days,
                    "entries_kept": len(entries_to_keep)
                },
                severity=AuditSeverity.INFO
            )
            
            return True
            
        except Exception as e:
            print(f"清理审计日志失败: {str(e)}")
            return False
    
    def verify_log_integrity(self) -> Dict[str, Any]:
        """验证审计日志的完整性"""
        results = {
            "total_entries": 0,
            "valid_entries": 0,
            "invalid_entries": 0,
            "invalid_details": []
        }
        
        try:
            if not os.path.exists(self.log_file):
                return results
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    results["total_entries"] += 1
                    
                    try:
                        data = json.loads(line.strip())
                        entry = AuditEntry.from_dict(data)
                        
                        if entry.verify_integrity():
                            results["valid_entries"] += 1
                        else:
                            results["invalid_entries"] += 1
                            results["invalid_details"].append({
                                "line": line_number,
                                "id": entry.id,
                                "reason": "hash_mismatch"
                            })
                            
                    except json.JSONDecodeError:
                        results["invalid_entries"] += 1
                        results["invalid_details"].append({
                            "line": line_number,
                            "reason": "json_decode_error"
                        })
                    except Exception as e:
                        results["invalid_entries"] += 1
                        results["invalid_details"].append({
                            "line": line_number,
                            "reason": str(e)
                        })
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def search_entries(self, 
                      query: str,
                      search_fields: List[str] = None) -> List[AuditEntry]:
        """搜索审计条目"""
        entries = []
        
        if not query:
            return entries
        
        if search_fields is None:
            search_fields = ["user", "action", "details", "ip_address"]
        
        try:
            # 搜索文件中的条目
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            entry = AuditEntry.from_dict(data)
                            
                            # 在指定字段中搜索
                            for field in search_fields:
                                if field == "details":
                                    # 搜索details字典中的所有值
                                    if any(query.lower() in str(value).lower() 
                                           for value in entry.details.values()):
                                        entries.append(entry)
                                        break
                                else:
                                    value = getattr(entry, field, "")
                                    if value and query.lower() in str(value).lower():
                                        entries.append(entry)
                                        break
                                        
                        except:
                            continue
            
            # 搜索缓冲区中的条目
            with self.buffer_lock:
                for entry in self.buffer:
                    for field in search_fields:
                        if field == "details":
                            if any(query.lower() in str(value).lower() 
                                   for value in entry.details.values()):
                                entries.append(entry)
                                break
                        else:
                            value = getattr(entry, field, "")
                            if value and query.lower() in str(value).lower():
                                entries.append(entry)
                                break
        
        except Exception as e:
            print(f"搜索审计条目失败: {str(e)}")
        
        # 按时间戳排序
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        return entries


# 全局审计日志记录器实例
audit_logger = AuditLogger()


def setup_audit_routes(app):
    """设置审计管理路由"""
    
    @app.route('/audit/entries', methods=['GET'])
    def get_audit_entries():
        """获取审计条目"""
        try:
            # 获取查询参数
            limit = request.args.get('limit', 100, type=int)
            event_type = request.args.get('event_type')
            user = request.args.get('user')
            severity = request.args.get('severity')
            
            # 时间范围
            start_time_str = request.args.get('start_time')
            end_time_str = request.args.get('end_time')
            
            start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
            end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
            
            # 转换枚举类型
            audit_event_type = None
            if event_type:
                try:
                    audit_event_type = AuditEventType(event_type)
                except ValueError:
                    return jsonify({"error": f"无效的事件类型: {event_type}"}), 400
            
            audit_severity = None
            if severity:
                try:
                    audit_severity = AuditSeverity(severity)
                except ValueError:
                    return jsonify({"error": f"无效的严重性级别: {severity}"}), 400
            
            # 获取条目
            entries = audit_logger.get_recent_entries(
                limit=limit,
                event_type=audit_event_type,
                user=user,
                severity=audit_severity,
                start_time=start_time,
                end_time=end_time
            )
            
            # 转换为字典列表
            entry_list = [entry.to_dict() for entry in entries]
            
            return jsonify({
                "entries": entry_list,
                "total": len(entry_list)
            })
            
        except Exception as e:
            return jsonify({"error": f"获取审计条目失败: {str(e)}"}), 500
    
    @app.route('/audit/stats', methods=['GET'])
    def get_audit_stats():
        """获取审计统计信息"""
        try:
            stats = audit_logger.get_statistics()
            
            return jsonify({
                "statistics": stats
            })
            
        except Exception as e:
            return jsonify({"error": f"获取审计统计信息失败: {str(e)}"}), 500
    
    @app.route('/audit/export', methods=['POST'])
    def export_audit_logs():
        """导出审计日志"""
        try:
            data = request.json or {}
            
            output_file = data.get('output_file', f"logs/audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # 时间范围
            start_time_str = data.get('start_time')
            end_time_str = data.get('end_time')
            
            start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
            end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
            
            # 事件类型
            event_types = data.get('event_types')
            
            # 导出日志
            success = audit_logger.export_logs(
                output_file=output_file,
                start_time=start_time,
                end_time=end_time,
                event_types=event_types
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "审计日志导出成功",
                    "output_file": output_file
                })
            else:
                return jsonify({"error": "审计日志导出失败"}), 500
                
        except Exception as e:
            return jsonify({"error": f"导出审计日志失败: {str(e)}"}), 500
    
    @app.route('/audit/verify', methods=['GET'])
    def verify_audit_logs():
        """验证审计日志完整性"""
        try:
            results = audit_logger.verify_log_integrity()
            
            return jsonify({
                "integrity_check": results
            })
            
        except Exception as e:
            return jsonify({"error": f"验证审计日志失败: {str(e)}"}), 500
    
    @app.route('/audit/search', methods=['POST'])
    def search_audit_logs():
        """搜索审计日志"""
        try:
            data = request.json
            if not data or 'query' not in data:
                return jsonify({"error": "需要搜索查询"}), 400
            
            query = data['query']
            search_fields = data.get('search_fields', ["user", "action", "details", "ip_address"])
            
            entries = audit_logger.search_entries(query, search_fields)
            
            entry_list = [entry.to_dict() for entry in entries]
            
            return jsonify({
                "results": entry_list,
                "total": len(entry_list),
                "query": query
            })
            
        except Exception as e:
            return jsonify({"error": f"搜索审计日志失败: {str(e)}"}), 500
    
    @app.route('/audit/alerts', methods=['GET'])
    def get_security_alerts():
        """获取安全警报"""
        try:
            # 获取最近的安全相关事件
            security_events = [
                AuditEventType.SECURITY_ALERT,
                AuditEventType.SUSPICIOUS_ACTIVITY,
                AuditEventType.BRUTE_FORCE_ATTEMPT,
                AuditEventType.INJECTION_ATTEMPT,
                AuditEventType.MALICIOUS_INPUT,
                AuditEventType.RATE_LIMIT_EXCEEDED
            ]
            
            alerts = []
            for event_type in security_events:
                entries = audit_logger.get_recent_entries(
                    limit=20,
                    event_type=event_type,
                    severity=AuditSeverity.WARNING
                )
                alerts.extend(entries)
            
            # 按时间戳排序
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            alert_list = [entry.to_dict() for entry in alerts[:50]]  # 限制数量
            
            return jsonify({
                "alerts": alert_list,
                "total": len(alert_list),
                "high_priority_count": sum(1 for alert in alert_list 
                                          if alert.get("severity") in ["error", "critical"])
            })
            
        except Exception as e:
            return jsonify({"error": f"获取安全警报失败: {str(e)}"}), 500
    
    return app


# 审计装饰器
def audit_event(event_type: AuditEventType, 
               action: str = None,
               severity: AuditSeverity = AuditSeverity.INFO,
               capture_details: bool = True):
    """审计事件装饰器"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, g
            
            # 获取用户信息
            user = "anonymous"
            if hasattr(g, 'user'):
                user = g.user.get('username', 'anonymous')
            
            # 执行函数并记录结果
            try:
                result = func(*args, **kwargs)
                
                # 记录成功事件
                details = {}
                if capture_details:
                    # 安全地捕获请求数据
                    try:
                        if request and request.method in ['POST', 'PUT']:
                            request_data = request.json or request.form.to_dict()
                            # 隐藏敏感信息
                            for key in ['password', 'token', 'secret', 'key']:
                                if key in request_data:
                                    request_data[key] = "***REDACTED***"
                            details["request_data"] = request_data
                    except:
                        pass
                
                audit_logger.log_event(
                    event_type=event_type,
                    user=user,
                    action=action or func.__name__,
                    details=details,
                    severity=severity,
                    ip_address=request.remote_addr if request else None,
                    user_agent=request.headers.get('User-Agent') if request else None
                )
                
                return result
                
            except Exception as e:
                # 记录失败事件
                details = {"error": str(e)}
                
                audit_logger.log_event(
                    event_type=event_type,
                    user=user,
                    action=action or func.__name__,
                    details=details,
                    severity=AuditSeverity.ERROR,
                    ip_address=request.remote_addr if request else None,
                    user_agent=request.headers.get('User-Agent') if request else None
                )
                
                raise
        
        return wrapper
    
    return decorator


if __name__ == "__main__":
    # 测试审计模块
    print("测试审计模块...")
    
    # 创建测试条目
    print("\n1. 创建测试审计条目:")
    
    test_entry = audit_logger.log_event(
        event_type=AuditEventType.SECURITY_ALERT,
        user="test_user",
        action="test_action",
        details={"test": "data", "count": 42},
        severity=AuditSeverity.INFO
    )
    
    print(f"  创建测试条目: {test_entry.id}")
    
    # 获取最近条目
    print("\n2. 获取最近条目:")
    recent_entries = audit_logger.get_recent_entries(limit=5)
    print(f"  获取到 {len(recent_entries)} 个条目")
    
    # 获取统计信息
    print("\n3. 获取统计信息:")
    stats = audit_logger.get_statistics()
    print(f"  总条目数: {stats['total_entries']}")
    
    # 验证完整性
    print("\n4. 验证日志完整性:")
    integrity_results = audit_logger.verify_log_integrity()
    print(f"  有效条目: {integrity_results['valid_entries']}")
    print(f"  无效条目: {integrity_results['invalid_entries']}")
    
    # 测试搜索功能
    print("\n5. 测试搜索功能:")
    search_results = audit_logger.search_entries("test")
    print(f"  搜索到 {len(search_results)} 个结果")
    
    print("\n审计模块测试完成！")