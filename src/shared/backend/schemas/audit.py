"""
审计日志数据模型
定义审计事件的结构化数据格式
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """审计事件类型"""
    # 用户认证相关
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_ROLE_CHANGE = "user_role_change"

    # 配置变更
    CONFIG_CREATE = "config_create"
    CONFIG_UPDATE = "config_update"
    CONFIG_DELETE = "config_delete"
    CONFIG_EXPORT = "config_export"
    CONFIG_IMPORT = "config_import"

    # 工具执行
    TOOL_EXECUTE = "tool_execute"
    TOOL_SCHEDULE = "tool_schedule"
    TOOL_CANCEL = "tool_cancel"
    TOOL_RESULT_VIEW = "tool_result_view"
    TOOL_RESULT_DELETE = "tool_result_delete"

    # 安全扫描
    SCAN_START = "scan_start"
    SCAN_STOP = "scan_stop"
    SCAN_PAUSE = "scan_pause"
    SCAN_RESUME = "scan_resume"
    SCAN_RESULT_EXPORT = "scan_result_export"

    # 权限管理
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_CREATE = "role_create"
    ROLE_UPDATE = "role_update"
    ROLE_DELETE = "role_delete"

    # 数据操作
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

    # 安全事件
    SECURITY_ALERT = "security_alert"
    SECURITY_INCIDENT = "security_incident"
    SECURITY_BREACH = "security_breach"
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # 系统操作
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    SYSTEM_UPGRADE = "system_upgrade"


class AuditEventSeverity(str, Enum):
    """审计事件严重级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEventStatus(str, Enum):
    """审计事件状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    CANCELLED = "cancelled"


class AuditActor(BaseModel):
    """审计操作执行者"""
    user_id: Optional[str] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    role: Optional[str] = Field(None, description="用户角色")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    session_id: Optional[str] = Field(None, description="会话ID")


class AuditResource(BaseModel):
    """审计操作资源"""
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    resource_name: Optional[str] = Field(None, description="资源名称")
    resource_path: Optional[str] = Field(None, description="资源路径")
    resource_metadata: Dict[str, Any] = Field(default_factory=dict, description="资源元数据")


class AuditEvent(BaseModel):
    """审计事件基础模型"""
    # 事件标识
    event_id: str = Field(..., description="事件唯一ID")
    event_type: AuditEventType = Field(..., description="事件类型")
    event_severity: AuditEventSeverity = Field(default=AuditEventSeverity.INFO, description="事件严重级别")
    event_status: AuditEventStatus = Field(default=AuditEventStatus.SUCCESS, description="事件状态")

    # 时间信息
    timestamp: datetime = Field(default_factory=datetime.now, description="事件发生时间")
    duration_ms: Optional[int] = Field(None, description="操作持续时间（毫秒）")

    # 操作者和资源
    actor: AuditActor = Field(..., description="操作执行者")
    resource: Optional[AuditResource] = Field(None, description="操作资源")
    target: Optional[AuditResource] = Field(None, description="操作目标（如果有）")

    # 操作详情
    action: str = Field(..., description="操作描述")
    description: Optional[str] = Field(None, description="详细描述")
    details: Dict[str, Any] = Field(default_factory=dict, description="操作详情数据")

    # 上下文信息
    correlation_id: Optional[str] = Field(None, description="关联ID（用于追踪相关事件）")
    request_id: Optional[str] = Field(None, description="请求ID")
    module: Optional[str] = Field(None, description="所属模块")

    # 结果信息
    result_code: Optional[str] = Field(None, description="结果代码")
    result_message: Optional[str] = Field(None, description="结果消息")
    result_data: Optional[Dict[str, Any]] = Field(None, description="结果数据")

    # 审计元数据
    is_sensitive: bool = Field(default=False, description="是否为敏感操作")
    requires_review: bool = Field(default=False, description="是否需要人工审核")
    reviewed_by: Optional[str] = Field(None, description="审核人")
    reviewed_at: Optional[datetime] = Field(None, description="审核时间")
    review_notes: Optional[str] = Field(None, description="审核备注")


class AuditEventFilters(BaseModel):
    """审计事件查询过滤器"""
    event_types: Optional[List[AuditEventType]] = Field(None, description="事件类型过滤")
    severities: Optional[List[AuditEventSeverity]] = Field(None, description="严重级别过滤")
    statuses: Optional[List[AuditEventStatus]] = Field(None, description="状态过滤")

    # 时间过滤
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

    # 操作者过滤
    user_ids: Optional[List[str]] = Field(None, description="用户ID过滤")
    usernames: Optional[List[str]] = Field(None, description="用户名过滤")
    ip_addresses: Optional[List[str]] = Field(None, description="IP地址过滤")

    # 资源过滤
    resource_types: Optional[List[str]] = Field(None, description="资源类型过滤")
    resource_ids: Optional[List[str]] = Field(None, description="资源ID过滤")

    # 其他过滤
    module: Optional[str] = Field(None, description="模块过滤")
    is_sensitive: Optional[bool] = Field(None, description="敏感操作过滤")
    requires_review: Optional[bool] = Field(None, description="需要审核过滤")

    # 文本搜索
    search_text: Optional[str] = Field(None, description="搜索文本（在action/description/details中搜索）")


class AuditEventPage(BaseModel):
    """审计事件分页结果"""
    events: List[AuditEvent] = Field(default_factory=list, description="审计事件列表")
    total: int = Field(0, description="总事件数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(50, description="每页大小")
    total_pages: int = Field(0, description="总页数")


# 预定义的审计事件模板
class AuditEventTemplates:
    """审计事件模板"""

    @staticmethod
    def user_login(
        user_id: str,
        username: str,
        ip_address: str,
        user_agent: str,
        status: AuditEventStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """用户登录事件模板"""
        return AuditEvent(
            event_id=f"login_{datetime.now().timestamp()}",
            event_type=AuditEventType.USER_LOGIN,
            event_severity=AuditEventSeverity.INFO,
            event_status=status,
            actor=AuditActor(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent
            ),
            action=f"用户登录: {username}",
            description=f"用户 {username} 尝试登录系统",
            details=details or {},
            module="authentication",
            is_sensitive=True
        )

    @staticmethod
    def tool_execute(
        user_id: str,
        username: str,
        tool_name: str,
        target: str,
        status: AuditEventStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """工具执行事件模板"""
        return AuditEvent(
            event_id=f"tool_exec_{datetime.now().timestamp()}",
            event_type=AuditEventType.TOOL_EXECUTE,
            event_severity=AuditEventSeverity.INFO,
            event_status=status,
            actor=AuditActor(user_id=user_id, username=username),
            resource=AuditResource(
                resource_type="tool",
                resource_name=tool_name,
                resource_metadata={"tool_name": tool_name}
            ),
            target=AuditResource(
                resource_type="target",
                resource_name=target,
                resource_metadata={"target": target}
            ),
            action=f"执行工具: {tool_name}",
            description=f"用户 {username} 执行工具 {tool_name} 对目标 {target} 进行扫描",
            details=details or {},
            module="tool_executor",
            is_sensitive=True
        )

    @staticmethod
    def config_update(
        user_id: str,
        username: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        status: AuditEventStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """配置更新事件模板"""
        return AuditEvent(
            event_id=f"config_update_{datetime.now().timestamp()}",
            event_type=AuditEventType.CONFIG_UPDATE,
            event_severity=AuditEventSeverity.WARNING,
            event_status=status,
            actor=AuditActor(user_id=user_id, username=username),
            resource=AuditResource(
                resource_type="configuration",
                resource_name=config_key,
                resource_metadata={"config_key": config_key}
            ),
            action=f"更新配置: {config_key}",
            description=f"用户 {username} 将配置 {config_key} 从 {old_value} 更新为 {new_value}",
            details={
                "config_key": config_key,
                "old_value": str(old_value),
                "new_value": str(new_value),
                **(details or {})
            },
            module="configuration",
            is_sensitive=True
        )

    @staticmethod
    def security_alert(
        alert_type: str,
        severity: AuditEventSeverity,
        source: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """安全告警事件模板"""
        return AuditEvent(
            event_id=f"security_alert_{datetime.now().timestamp()}",
            event_type=AuditEventType.SECURITY_ALERT,
            event_severity=severity,
            event_status=AuditEventStatus.SUCCESS,
            actor=AuditActor(),
            action=f"安全告警: {alert_type}",
            description=description,
            details={
                "alert_type": alert_type,
                "source": source,
                **(details or {})
            },
            module="security",
            is_sensitive=True,
            requires_review=True
        )


# 审计事件辅助函数
def create_audit_event(
    event_type: AuditEventType,
    actor: AuditActor,
    action: str,
    description: Optional[str] = None,
    resource: Optional[AuditResource] = None,
    target: Optional[AuditResource] = None,
    severity: AuditEventSeverity = AuditEventSeverity.INFO,
    status: AuditEventStatus = AuditEventStatus.SUCCESS,
    details: Optional[Dict[str, Any]] = None,
    module: Optional[str] = None,
    is_sensitive: bool = False,
    requires_review: bool = False
) -> AuditEvent:
    """创建审计事件的快捷函数"""
    return AuditEvent(
        event_id=f"{event_type.value}_{datetime.now().timestamp()}_{id(actor)}",
        event_type=event_type,
        event_severity=severity,
        event_status=status,
        actor=actor,
        resource=resource,
        target=target,
        action=action,
        description=description,
        details=details or {},
        module=module,
        is_sensitive=is_sensitive,
        requires_review=requires_review
    )