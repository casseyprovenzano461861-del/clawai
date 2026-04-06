# -*- coding: utf-8 -*-
"""
实时监控API端点
提供系统指标、活跃扫描、事件日志和WebSocket支持
"""

import asyncio
import json
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import logging

from backend.auth.fastapi_permissions import require_authentication, get_current_user
from backend.schemas.error import APIError, ErrorCode

router = APIRouter(prefix="/api/v1/monitor", tags=["实时监控"])

logger = logging.getLogger(__name__)

# 内存中维护活跃扫描和事件（生产环境应使用Redis或数据库）
_active_scans: Dict[str, Dict[str, Any]] = {}
_recent_events: List[Dict[str, Any]] = []
_ws_connections: List[WebSocket] = []

MAX_EVENTS = 500


def _get_system_resources() -> Dict[str, Any]:
    """获取系统资源使用情况"""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        return {
            "cpu": round(cpu, 1),
            "memory": round(mem.percent, 1),
            "disk": round(disk.percent, 1),
            "network_in": net.bytes_recv,
            "network_out": net.bytes_sent,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.warning(f"获取系统资源失败: {e}")
        return {
            "cpu": 0.0,
            "memory": 0.0,
            "disk": 0.0,
            "network_in": 0,
            "network_out": 0,
            "timestamp": datetime.now().isoformat()
        }


def _add_event(event_type: str, message: str, severity: str = "info", data: Dict = None):
    """添加监控事件"""
    event = {
        "id": f"evt-{len(_recent_events) + 1}",
        "type": event_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    _recent_events.append(event)
    if len(_recent_events) > MAX_EVENTS:
        _recent_events.pop(0)
    return event


@router.get("/stats")
async def get_monitor_stats(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取监控统计数据"""
    try:
        resources = _get_system_resources()
        return {
            "success": True,
            "data": {
                "active_scans": len(_active_scans),
                "total_events": len(_recent_events),
                "system_load": resources["cpu"],
                "memory_usage": resources["memory"],
                "disk_usage": resources["disk"],
                "network_in": resources["network_in"],
                "network_out": resources["network_out"],
                "uptime": _get_uptime(),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"获取监控统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取监控统计失败",
                severity="high"
            ).model_dump()
        )


@router.get("/active-scans")
async def get_active_scans(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取活跃扫描列表"""
    try:
        scans = list(_active_scans.values())
        return {
            "success": True,
            "data": scans,
            "count": len(scans)
        }
    except Exception as e:
        logger.error(f"获取活跃扫描失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取活跃扫描失败",
                severity="high"
            ).model_dump()
        )


@router.get("/recent-events")
async def get_recent_events(
    limit: int = Query(50, ge=1, le=200, description="返回事件数量"),
    severity: Optional[str] = Query(None, description="按严重级别过滤"),
    event_type: Optional[str] = Query(None, description="按事件类型过滤"),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取最近事件列表"""
    try:
        events = list(reversed(_recent_events))  # 最新在前

        if severity:
            events = [e for e in events if e.get("severity") == severity]
        if event_type:
            events = [e for e in events if e.get("type") == event_type]

        return {
            "success": True,
            "data": events[:limit],
            "total": len(events),
            "limit": limit
        }
    except Exception as e:
        logger.error(f"获取最近事件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取最近事件失败",
                severity="high"
            ).model_dump()
        )


@router.get("/system-resources")
async def get_system_resources(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取系统资源实时数据"""
    try:
        current = _get_system_resources()
        return {
            "success": True,
            "data": {
                "current": current,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取系统资源失败",
                severity="high"
            ).model_dump()
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    timeframe: str = Query("1h", description="时间范围: 1h, 6h, 24h, 7d"),
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取性能指标历史数据"""
    try:
        # 生成模拟历史数据（生产环境应从时序数据库获取）
        now = datetime.now()
        timeframe_map = {"1h": 60, "6h": 360, "24h": 1440, "7d": 10080}
        minutes = timeframe_map.get(timeframe, 60)
        points = min(60, minutes)
        interval = minutes / points

        history = []
        for i in range(points):
            ts = now - timedelta(minutes=interval * (points - i))
            res = _get_system_resources()
            history.append({
                "timestamp": ts.isoformat(),
                "cpu": res["cpu"],
                "memory": res["memory"],
                "disk": res["disk"]
            })

        return {
            "success": True,
            "data": {
                "timeframe": timeframe,
                "history": history,
                "current": _get_system_resources()
            }
        }
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取性能指标失败",
                severity="high"
            ).model_dump()
        )


@router.post("/scans/{scan_id}/stop")
async def stop_scan(
    scan_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """停止指定扫描"""
    try:
        if scan_id not in _active_scans:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"扫描 {scan_id} 不存在或已完成",
                    severity="low"
                ).model_dump()
            )

        scan = _active_scans.pop(scan_id)
        scan["status"] = "stopped"
        scan["stopped_at"] = datetime.now().isoformat()

        _add_event("scan_stopped", f"扫描 {scan_id} 已被用户停止", "warning", {"scan_id": scan_id})

        # 广播给WebSocket客户端
        await _broadcast_event({
            "type": "scan_stopped",
            "scan_id": scan_id,
            "timestamp": datetime.now().isoformat()
        })

        return {"success": True, "message": f"扫描 {scan_id} 已停止", "scan": scan}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止扫描失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="停止扫描失败",
                severity="high"
            ).model_dump()
        )


@router.get("/scans/{scan_id}")
async def get_scan_detail(
    scan_id: str,
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """获取扫描详情"""
    try:
        scan = _active_scans.get(scan_id)
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APIError(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"扫描 {scan_id} 不存在",
                    severity="low"
                ).model_dump()
            )
        return {"success": True, "data": scan}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="获取扫描详情失败",
                severity="high"
            ).model_dump()
        )


@router.get("/events")
async def stream_events(
    current_user: Dict[str, Any] = Depends(require_authentication)
):
    """SSE事件流端点"""
    async def event_generator():
        last_count = len(_recent_events)
        while True:
            current_count = len(_recent_events)
            if current_count > last_count:
                new_events = _recent_events[last_count:]
                for event in new_events:
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                last_count = current_count
            # 每5秒发送一次心跳
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


async def _broadcast_event(data: Dict):
    """广播事件给所有WebSocket客户端"""
    disconnected = []
    for ws in _ws_connections:
        try:
            await ws.send_json(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _ws_connections.remove(ws)


def _get_uptime() -> str:
    """获取系统运行时间"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except Exception:
        return "unknown"


# WebSocket端点（挂载在主app，此处提供处理逻辑）
async def handle_monitor_websocket(websocket: WebSocket):
    """WebSocket监控连接处理器（在main.py中注册为 /ws/monitor）"""
    await websocket.accept()
    _ws_connections.append(websocket)
    logger.info(f"WebSocket客户端连接: {websocket.client}")

    try:
        # 发送初始数据
        await websocket.send_json({
            "type": "connected",
            "message": "实时监控连接成功",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            # 定期推送系统状态
            resources = _get_system_resources()
            await websocket.send_json({
                "type": "metrics_update",
                "data": {
                    "system": resources,
                    "active_scans": len(_active_scans),
                    "total_events": len(_recent_events)
                },
                "timestamp": datetime.now().isoformat()
            })

            # 等待客户端消息或超时
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                data = json.loads(msg)
                # 处理客户端消息（如ping）
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except asyncio.TimeoutError:
                pass  # 正常超时，继续推送

    except WebSocketDisconnect:
        logger.info(f"WebSocket客户端断开: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket处理出错: {e}")
    finally:
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)


__all__ = ["router", "handle_monitor_websocket", "_active_scans", "_add_event"]
