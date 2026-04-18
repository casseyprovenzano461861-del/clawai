# -*- coding: utf-8 -*-
"""
实时扫描 API
将 CLI 扫描引擎暴露为 REST 端点，通过 EventBus → WebSocket 实时推送进度
"""

import uuid
import asyncio
import logging
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局扫描任务注册表
_scan_tasks: Dict[str, Dict[str, Any]] = {}


class ScanStartRequest(BaseModel):
    target: str
    profile: str = "standard"        # quick | standard | deep
    vuln_hint: Optional[str] = None  # sqli | xss | ssrf | ...


class ScanStartResponse(BaseModel):
    scan_id: str
    target: str
    profile: str
    message: str


@router.post("/start", response_model=ScanStartResponse)
async def start_scan(req: ScanStartRequest) -> ScanStartResponse:
    """启动扫描任务，通过 EventBus → WebSocket 实时推送进度"""
    # 基础输入校验
    if not req.target or not req.target.strip():
        raise HTTPException(status_code=400, detail="target 不能为空")
    target = req.target.strip()
    if any(c in target for c in ('\x00', '\n', '\r')):
        raise HTTPException(status_code=400, detail="target 包含非法字符")

    scan_id = str(uuid.uuid4())[:8]

    _scan_tasks[scan_id] = {
        "scan_id": scan_id,
        "target": target,
        "profile": req.profile,
        "status": "starting",
        "findings": [],
        "flags": [],
    }

    asyncio.create_task(_run_scan(scan_id, target, req.profile, req.vuln_hint))

    return ScanStartResponse(
        scan_id=scan_id,
        target=target,
        profile=req.profile,
        message=f"扫描已启动 (id: {scan_id})，通过 WebSocket /ws/per-events 接收实时进度",
    )


@router.get("/{scan_id}")
async def get_scan_status(scan_id: str) -> Dict[str, Any]:
    """查询扫描状态"""
    if scan_id not in _scan_tasks:
        raise HTTPException(status_code=404, detail=f"扫描任务 {scan_id} 不存在")
    # 过滤掉不可序列化的内部引用字段（如 _cli_ref）
    task = _scan_tasks[scan_id]
    return {k: v for k, v in task.items() if not k.startswith("_")}


@router.delete("/{scan_id}")
async def stop_scan(scan_id: str) -> Dict[str, Any]:
    """停止正在运行的扫描"""
    if scan_id not in _scan_tasks:
        raise HTTPException(status_code=404, detail=f"扫描任务 {scan_id} 不存在")

    task_info = _scan_tasks[scan_id]
    cli = task_info.get("_cli_ref")
    if cli and hasattr(cli, "_scan_state") and cli._scan_state:
        try:
            from src.cli.scan_state import ScanState
            cli._scan_state.transition(ScanState.CANCELLED)
        except Exception as exc:
            logger.warning(f"扫描 {scan_id} 取消信号发送失败: {exc}")

    task_info["status"] = "cancelled"
    return {"scan_id": scan_id, "status": "cancelled"}


async def _run_scan(
    scan_id: str,
    target: str,
    profile: str,
    vuln_hint: Optional[str],
) -> None:
    """后台执行扫描（通过 EventBus 推送所有进度事件）"""
    task_info = _scan_tasks[scan_id]

    # 广播扫描开始事件
    _emit(scan_id, "scan_started", {
        "scan_id": scan_id,
        "target": target,
        "profile": profile,
    })

    try:
        # 懒加载 ChatCLI，避免循环导入
        import sys
        _root = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 5))
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from src.cli.chat_cli import ChatCLI

        cli = ChatCLI()
        task_info["_cli_ref"] = cli      # 供 stop_scan 调用
        task_info["status"] = "running"

        # _execute_scan 内部会通过 EventBus 广播所有 TOOL/FINDING/PROGRESS 事件
        result = await cli._execute_scan(
            target=target,
            profile=profile,
            vuln_hint=vuln_hint,
        )

        # 收集 Flag
        flags = getattr(cli, "_last_flags", []) or []
        task_info["flags"] = flags
        task_info["status"] = "completed"

        _emit(scan_id, "scan_completed", {
            "scan_id": scan_id,
            "target": target,
            "flags": flags,
            "findings_count": len(cli.session.findings) if cli.session else 0,
        })

    except asyncio.CancelledError:
        task_info["status"] = "cancelled"
        _emit(scan_id, "scan_cancelled", {"scan_id": scan_id})
    except Exception as exc:
        logger.error(f"扫描 {scan_id} 执行异常: {exc}", exc_info=True)
        task_info["status"] = "error"
        task_info["error"] = str(exc)
        _emit(scan_id, "scan_error", {"scan_id": scan_id, "error": str(exc)})
    finally:
        task_info.pop("_cli_ref", None)


def _emit(scan_id: str, event_type: str, data: Dict[str, Any]) -> None:
    """通过 EventBus 广播扫描生命周期事件"""
    try:
        from src.shared.backend.events import EventBus
        bus = EventBus.get()
        bus.emit_message(
            f"[scan:{scan_id}] {event_type}",
            msg_type="info",
            extra={**data, "scan_event": event_type, "scan_id": scan_id},
        )
    except Exception:
        pass  # EventBus 不可用时静默
