# -*- coding: utf-8 -*-
"""
WebSocket API 端点
支持 P-E-R 实时事件推送，并桥接后端 EventBus 到所有 WebSocket 客户端
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器（含 EventBus 桥接）"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._counter = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._eventbus_attached = False
    
    async def connect(self, websocket: WebSocket, client_id: str = None) -> str:
        """接受 WebSocket 连接"""
        await websocket.accept()
        
        if not client_id:
            self._counter += 1
            client_id = f"client_{self._counter}"
        
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket 连接建立: {client_id}")
        
        return client_id
    
    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket 连接断开: {client_id}")
    
    async def send_json(self, client_id: str, data: Dict[str, Any]):
        """发送 JSON 数据"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, data: Dict[str, Any]):
        """广播消息到所有连接"""
        for client_id in list(self.active_connections.keys()):
            await self.send_json(client_id, data)

    # ------------------------------------------------------------------
    # EventBus 桥接
    # ------------------------------------------------------------------

    def attach_eventbus(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """将 EventBus 事件桥接到 WebSocket 广播。

        应在 FastAPI lifespan 启动时调用，传入当前事件循环。
        EventBus 回调在同步线程中执行，通过 run_coroutine_threadsafe
        安全调度到 asyncio 事件循环。

        Args:
            loop: asyncio 事件循环，默认使用当前运行中的循环
        """
        if self._eventbus_attached:
            return

        try:
            from ..events import EventBus, EventType
        except ImportError:
            logger.warning("EventBus 模块未找到，跳过桥接")
            return

        self._loop = loop or asyncio.get_event_loop()
        bus = EventBus.get()

        def _make_handler(serializer):
            """创建线程安全的同步回调"""
            def handler(event):
                if not self.active_connections:
                    return  # 无客户端时静默丢弃
                data = serializer(event)
                try:
                    asyncio.run_coroutine_threadsafe(self.broadcast(data), self._loop)
                except Exception as exc:
                    logger.debug(f"EventBus 广播调度失败: {exc}")
            return handler

        def _serialize_state(event):
            d = {"type": "state_changed", "timestamp": datetime.now().isoformat()}
            d.update(event.data)
            return d

        def _serialize_message(event):
            return {
                "type": "message",
                "text": event.data.get("text", ""),
                "msg_type": event.data.get("type", "info"),
                "timestamp": datetime.now().isoformat(),
            }

        def _serialize_tool(event):
            return {
                "type": "tool_event",
                "status": event.data.get("status", ""),
                "name": event.data.get("name", ""),
                "args": event.data.get("args", {}),
                "result": event.data.get("result"),
                "timestamp": datetime.now().isoformat(),
            }

        def _serialize_finding(event):
            return {
                "type": "finding",
                "vuln_type": event.data.get("vuln_type") or event.data.get("type", ""),
                "title": event.data.get("title", ""),
                "severity": event.data.get("severity", "info"),
                "detail": event.data.get("detail", ""),
                "skill_id": event.data.get("skill_id", ""),
                "evidence": event.data.get("evidence", ""),
                "target": event.data.get("target", ""),
                "timestamp": datetime.now().isoformat(),
            }

        def _serialize_progress(event):
            return {
                "type": "progress",
                "percent": event.data.get("percent", 0.0),
                "description": event.data.get("description", ""),
                "timestamp": datetime.now().isoformat(),
            }

        bus.subscribe(EventType.STATE_CHANGED, _make_handler(_serialize_state))
        bus.subscribe(EventType.MESSAGE, _make_handler(_serialize_message))
        bus.subscribe(EventType.TOOL, _make_handler(_serialize_tool))
        bus.subscribe(EventType.FINDING, _make_handler(_serialize_finding))
        bus.subscribe(EventType.PROGRESS, _make_handler(_serialize_progress))

        self._eventbus_attached = True
        logger.info("EventBus → WebSocket 桥接已建立（5 类事件）")


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/per-events")
async def per_events_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    P-E-R 事件 WebSocket 端点
    
    接收的客户端消息格式：
    {
        "action": "start_per" | "stop_per" | "get_status",
        "target": "目标地址",
        "goal": "测试目标描述",
        "mode": "recon" | "vuln" | "full"
    }
    
    发送的事件格式：
    {
        "type": "start" | "iteration" | "phase" | "plan" | "task_start" | 
                "task_result" | "reflection" | "complete" | "error",
        "timestamp": "ISO时间戳",
        ...事件特定字段
    }
    """
    cid = await manager.connect(websocket, client_id)
    
    try:
        # 发送连接确认
        await manager.send_json(cid, {
            "type": "connected",
            "client_id": cid,
            "timestamp": datetime.now().isoformat(),
            "message": "WebSocket 连接已建立，可以发送 P-E-R 命令"
        })
        
        while True:
            # 接收客户端消息
            try:
                data = await websocket.receive_json()
            except (WebSocketDisconnect, RuntimeError, ValueError):
                # 客户端主动断开、连接已关闭或 JSON 解析失败
                break
            action = data.get("action")
            
            if action == "start_per":
                # 启动 P-E-R 渗透测试
                target = data.get("target")
                goal = data.get("goal")
                mode = data.get("mode", "full")
                
                if not target:
                    await manager.send_json(cid, {
                        "type": "error",
                        "code": "invalid_target",
                        "message": "缺少目标地址",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue

                target = target.strip()
                if any(c in target for c in ('\x00', '\n', '\r')) or len(target) > 500:
                    await manager.send_json(cid, {
                        "type": "error",
                        "code": "invalid_target",
                        "message": "目标地址包含非法字符或过长",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                # 导入并创建 IntelligentPERAgent
                try:
                    from ..ai_agent.intelligent_per import IntelligentPERAgent
                    from ..ai_agent.orchestrator import AIAgentOrchestrator

                    # 通过 Orchestrator 获取完整初始化的工具执行器
                    orchestrator = AIAgentOrchestrator()
                    tool_executor = orchestrator.tool_bridge.execute if orchestrator.tool_bridge else None
                    llm_client = orchestrator.agent_core

                    # 根据 mode 决定迭代次数
                    _mode_iterations = {
                        "recon": 2,
                        "vuln":  3,
                        "full":  5,
                    }
                    _max_iter = _mode_iterations.get(mode, 5)

                    # 创建 P-E-R Agent
                    agent = IntelligentPERAgent(
                        llm_client=llm_client,
                        tool_executor=tool_executor,
                        max_iterations=_max_iter
                    )

                    # 发送开始事件
                    await manager.send_json(cid, {
                        "type": "start",
                        "target": target,
                        "mode": mode,
                        "timestamp": datetime.now().isoformat()
                    })

                    # 执行 P-E-R 循环并推送事件
                    # _disconnected 标志：任意 send 失败时设置，终止 generator 迭代
                    _disconnected = False

                    async def _send(data: dict):
                        nonlocal _disconnected
                        if _disconnected:
                            return
                        try:
                            await manager.send_json(cid, data)
                        except Exception:
                            _disconnected = True

                    async for event in agent.run(target=target, goal=goal, mode=mode):
                        if _disconnected:
                            break
                        event["timestamp"] = datetime.now().isoformat()
                        await _send(event)

                        # task_start → 同时发 tool_event(start) + message，让前端时间线显示
                        if event.get("type") == "task_start":
                            tool_name = event.get("task", "unknown")
                            await _send({
                                "type": "tool_event",
                                "status": "start",
                                "name": tool_name,
                                "args": {},
                                "timestamp": event["timestamp"],
                            })
                            await _send({
                                "type": "message",
                                "text": f"执行任务: {tool_name}",
                                "msg_type": "info",
                                "timestamp": event["timestamp"],
                            })

                        # task_result → 发 tool_event(complete/error) + message + 逐条 finding
                        elif event.get("type") == "task_result":
                            tool_name = event.get("task", "unknown")
                            success = event.get("success", False)
                            raw_findings = event.get('findings') or []
                            findings_count = len(raw_findings)
                            await _send({
                                "type": "tool_event",
                                "status": "complete" if success else "error",
                                "name": tool_name,
                                "args": {},
                                "result": raw_findings,
                                "timestamp": event["timestamp"],
                            })
                            await _send({
                                "type": "message",
                                "text": f"{tool_name} 完成 → 发现 {findings_count} 项" if success else f"{tool_name} 执行失败",
                                "msg_type": "success" if success else "warning",
                                "timestamp": event["timestamp"],
                            })
                            # 逐条发送 finding 事件，让前端 findings state 正确更新
                            # 注意：用 vuln_type 存漏洞类型，避免与消息 type 字段冲突
                            for f in raw_findings:
                                await _send({
                                    "type": "finding",
                                    "vuln_type": f.get("type"),
                                    **{k: v for k, v in f.items() if k != "type"},
                                    "timestamp": event["timestamp"],
                                })

                        # phase → message
                        elif event.get("type") == "phase":
                            await _send({
                                "type": "message",
                                "text": event.get("message", f"阶段: {event.get('phase')}"),
                                "msg_type": "info",
                                "timestamp": event["timestamp"],
                            })

                        # reflection → message
                        elif event.get("type") == "reflection":
                            summary = event.get("summary", "")
                            if summary:
                                await _send({
                                    "type": "message",
                                    "text": f"反思: {summary[:200]}",
                                    "msg_type": "info",
                                    "timestamp": event["timestamp"],
                                })

                        # 如果是完成或错误事件，结束循环
                        if event.get("type") in ["complete", "error"]:
                            break
                    
                except ImportError as e:
                    logger.error(f"P-E-R 模块导入失败: {e}", exc_info=True)
                    await manager.send_json(cid, {
                        "type": "error",
                        "code": "import_error",
                        "message": f"导入模块失败: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"P-E-R 执行失败: {e}", exc_info=True)
                    await manager.send_json(cid, {
                        "type": "error",
                        "code": "execution_error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif action == "stop_per":
                # 停止 P-E-R（未来实现）
                await manager.send_json(cid, {
                    "type": "per_stopped",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif action == "get_status":
                # 获取状态（未来实现）
                await manager.send_json(cid, {
                    "type": "status",
                    "active": False,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif action == "ping":
                # 心跳
                await manager.send_json(cid, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                await manager.send_json(cid, {
                    "type": "error",
                    "message": f"未知操作: {action}",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(cid)
        logger.info(f"客户端断开连接: {cid}")

    except Exception as e:
        logger.error(f"WebSocket 未预期错误: {e}", exc_info=True)
        try:
            await manager.send_json(cid, {
                "type": "error",
                "code": "internal_error",
                "message": "内部错误，连接已关闭",
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass
        manager.disconnect(cid)


@router.websocket("/ws/monitoring")
async def monitoring_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    监控 WebSocket 端点
    
    用于实时监控 Token 预算、Agent 状态等
    """
    cid = await manager.connect(websocket, client_id)
    
    try:
        await manager.send_json(cid, {
            "type": "connected",
            "client_id": cid,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await websocket.receive_json()
            except (WebSocketDisconnect, RuntimeError, ValueError):
                break
            action = data.get("action")
            
            if action == "get_budget":
                # 获取预算状态
                try:
                    from ..config import get_settings
                    settings = get_settings()
                    
                    # 如果有活动的预算管理器，返回状态
                    await manager.send_json(cid, {
                        "type": "budget_status",
                        "enabled": settings.token_budget.enabled,
                        "max_total": settings.token_budget.max_total_tokens,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    await manager.send_json(cid, {
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif action == "ping":
                await manager.send_json(cid, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(cid)
    
    except Exception as e:
        logger.error(f"监控 WebSocket 错误: {e}")
        manager.disconnect(cid)


# 导出
__all__ = ["router", "manager", "ConnectionManager"]
