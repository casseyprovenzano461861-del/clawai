"""
审计日志API
提供审计日志的查询和管理接口
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import Response
import logging

from ..schemas import (
    AuditEvent,
    AuditEventFilters,
    AuditEventPage,
    AuditEventType,
    AuditEventSeverity,
    AuditEventStatus,
    APIError
)
from .manager import get_audit_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "禁止访问"},
        500: {"description": "服务器内部错误"}
    }
)


async def get_current_user(request: Request):
    """获取当前认证用户"""
    try:
        from ..auth.fastapi_permissions import get_current_user as auth_get_user
        user = await auth_get_user(request)
        if user:
            return user
    except Exception as e:
        logger.debug(f"JWT认证失败: {e}")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=APIError(
            code="UNAUTHORIZED",
            message="未认证，请提供有效的JWT令牌",
            severity="error"
        ).dict()
    )


def require_admin_role(current_user=Depends(get_current_user)):
    """要求管理员角色"""
    role = current_user.get("role", "guest")
    if role not in ("admin", "administrator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=APIError(
                code="FORBIDDEN",
                message=f"需要管理员权限，当前角色: {role}",
                severity="error"
            ).dict()
        )
    return current_user


@router.get("/events", response_model=AuditEventPage)
async def search_events(
    event_types: Optional[List[AuditEventType]] = Query(None, description="事件类型过滤"),
    severities: Optional[List[AuditEventSeverity]] = Query(None, description="严重级别过滤"),
    statuses: Optional[List[AuditEventStatus]] = Query(None, description="状态过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    user_ids: Optional[List[str]] = Query(None, description="用户ID过滤"),
    usernames: Optional[List[str]] = Query(None, description="用户名过滤"),
    ip_addresses: Optional[List[str]] = Query(None, description="IP地址过滤"),
    resource_types: Optional[List[str]] = Query(None, description="资源类型过滤"),
    resource_ids: Optional[List[str]] = Query(None, description="资源ID过滤"),
    module: Optional[str] = Query(None, description="模块过滤"),
    is_sensitive: Optional[bool] = Query(None, description="敏感操作过滤"),
    requires_review: Optional[bool] = Query(None, description="需要审核过滤"),
    search_text: Optional[str] = Query(None, description="搜索文本"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页大小"),
    _current_user=Depends(get_current_user)
):
    """
    搜索审计事件

    支持多种过滤条件，返回分页的审计事件列表。
    只有具有适当权限的用户才能访问审计日志。
    """
    try:
        # 构建过滤器
        filters = AuditEventFilters(
            event_types=event_types,
            severities=severities,
            statuses=statuses,
            start_time=start_time,
            end_time=end_time,
            user_ids=user_ids,
            usernames=usernames,
            ip_addresses=ip_addresses,
            resource_types=resource_types,
            resource_ids=resource_ids,
            module=module,
            is_sensitive=is_sensitive,
            requires_review=requires_review,
            search_text=search_text
        )

        # 搜索事件
        audit_manager = get_audit_manager()
        result = audit_manager.search_events(filters, page, page_size)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_SEARCH_ERROR",
                message=f"搜索审计事件失败: {str(e)}",
                severity="error"
            ).dict()
        )


@router.get("/events/{event_id}", response_model=AuditEvent)
async def get_event(
    event_id: str,
    _current_user=Depends(get_current_user)
):
    """
    获取单个审计事件

    根据事件ID获取审计事件的详细信息。
    """
    try:
        audit_manager = get_audit_manager()
        event = audit_manager.get_event(event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code="AUDIT_EVENT_NOT_FOUND",
                    message=f"审计事件 {event_id} 不存在",
                    severity="error"
                ).dict()
            )

        return event

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_GET_ERROR",
                message=f"获取审计事件失败: {str(e)}",
                severity="error"
            ).dict()
        )


@router.delete("/events")
async def delete_events(
    event_ids: List[str],
    _current_user=Depends(require_admin_role)
):
    """
    删除审计事件

    批量删除指定的审计事件。需要管理员权限。
    """
    try:
        if not event_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code="INVALID_REQUEST",
                    message="未指定要删除的事件ID",
                    severity="warning"
                ).dict()
            )

        audit_manager = get_audit_manager()
        deleted_count = audit_manager.delete_events(event_ids)

        return {
            "message": f"成功删除 {deleted_count} 个审计事件",
            "deleted_count": deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_DELETE_ERROR",
                message=f"删除审计事件失败: {str(e)}",
                severity="error"
            ).dict()
        )


@router.post("/cleanup")
async def cleanup_events(
    days_to_keep: int = Query(90, ge=1, le=365, description="保留天数"),
    _current_user=Depends(require_admin_role)
):
    """
    清理旧审计事件

    自动清理指定天数前的审计事件。需要管理员权限。
    """
    try:
        audit_manager = get_audit_manager()
        deleted_count = audit_manager.cleanup_old_events(days_to_keep)

        return {
            "message": f"清理完成，删除了 {deleted_count} 个旧审计事件",
            "deleted_count": deleted_count,
            "days_to_keep": days_to_keep
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_CLEANUP_ERROR",
                message=f"清理审计事件失败: {str(e)}",
                severity="error"
            ).dict()
        )


@router.get("/stats")
async def get_audit_stats(
    _current_user=Depends(get_current_user)
):
    """
    获取审计统计信息

    返回审计系统的统计信息，包括事件数量、按类型分布等。
    """
    try:
        audit_manager = get_audit_manager()
        stats = audit_manager.get_stats()

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_STATS_ERROR",
                message=f"获取审计统计失败: {str(e)}",
                severity="error"
            ).dict()
        )


@router.get("/export")
async def export_events(
    event_types: Optional[List[AuditEventType]] = Query(None, description="事件类型过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    format: str = Query("json", description="导出格式（json或csv）"),
    _current_user=Depends(require_admin_role)
):
    """
    导出审计事件

    导出审计事件为JSON或CSV格式。需要管理员权限。
    """
    try:
        filters = AuditEventFilters(
            event_types=event_types,
            start_time=start_time,
            end_time=end_time
        )

        audit_manager = get_audit_manager()

        # 获取所有匹配的事件（不分页）
        result = audit_manager.search_events(filters, page=1, page_size=1000000)

        if format.lower() == "csv":
            # 转换为CSV格式
            import io
            import csv

            output = io.StringIO()
            writer = csv.writer(output)

            # 写入表头
            writer.writerow([
                "事件ID", "事件类型", "严重级别", "状态", "时间戳",
                "用户ID", "用户名", "IP地址", "操作", "描述", "模块", "是否敏感"
            ])

            # 写入数据
            for event in result.events:
                writer.writerow([
                    event.event_id,
                    event.event_type.value,
                    event.event_severity.value,
                    event.event_status.value,
                    event.timestamp.isoformat(),
                    event.actor.user_id or "",
                    event.actor.username or "",
                    event.actor.ip_address or "",
                    event.action,
                    event.description or "",
                    event.module or "",
                    "是" if event.is_sensitive else "否"
                ])

            csv_content = output.getvalue()
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=audit_events.csv"
                }
            )

        else:
            # JSON格式
            events_data = [event.dict() for event in result.events]
            import json
            json_content = json.dumps(events_data, indent=2, default=str)

            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": "attachment; filename=audit_events.json"
                }
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_EXPORT_ERROR",
                message=f"导出审计事件失败: {str(e)}",
                severity="error"
            ).dict()
        )


@router.post("/review/{event_id}")
async def review_event(
    event_id: str,
    approved: bool = Query(..., description="审核结果（通过/拒绝）"),
    notes: Optional[str] = Query(None, description="审核备注"),
    _current_user=Depends(require_admin_role)
):
    """
    审核审计事件

    审核需要人工审核的审计事件。需要管理员权限。
    """
    try:
        audit_manager = get_audit_manager()
        event = audit_manager.get_event(event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code="AUDIT_EVENT_NOT_FOUND",
                    message=f"审计事件 {event_id} 不存在",
                    severity="error"
                ).dict()
            )

        if not event.requires_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIError(
                    code="NOT_REQUIRE_REVIEW",
                    message="该审计事件不需要审核",
                    severity="warning"
                ).dict()
            )

        # 更新审核信息（这里简化处理，实际应该保存到存储）
        event.reviewed_by = _current_user.get("username", "unknown")
        event.reviewed_at = datetime.now()
        event.review_notes = notes

        # 重新保存事件
        audit_manager.log_event_sync(event)

        return {
            "message": f"审计事件 {event_id} 已审核",
            "event_id": event_id,
            "approved": approved,
            "reviewed_by": event.reviewed_by,
            "reviewed_at": event.reviewed_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code="AUDIT_REVIEW_ERROR",
                message=f"审核审计事件失败: {str(e)}",
                severity="error"
            ).dict()
        )