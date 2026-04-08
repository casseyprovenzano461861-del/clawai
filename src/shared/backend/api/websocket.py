# -*- coding: utf-8 -*-
"""
WebSocket API 端点
支持 P-E-R 实时事件推送
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
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._counter = 0
    
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
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "start_per":
                # 启动 P-E-R 渗透测试
                target = data.get("target")
                goal = data.get("goal")
                mode = data.get("mode", "full")
                
                if not target:
                    await manager.send_json(cid, {
                        "type": "error",
                        "message": "缺少目标地址",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                # 导入并创建 IntelligentPERAgent
                try:
                    from ..ai_agent.intelligent_per import IntelligentPERAgent
                    from ..ai_agent.orchestrator import create_agent
                    from ..config import get_settings
                    
                    settings = get_settings()
                    
                    # 创建 Agent
                    agent_core = create_agent(
                        provider=settings.active_provider,
                        model=settings.active_model
                    )
                    
                    # 创建 P-E-R Agent
                    agent = IntelligentPERAgent(
                        llm_client=agent_core,
                        tool_executor=None,  # 需要传入工具执行器
                        max_iterations=5
                    )
                    
                    # 发送开始事件
                    await manager.send_json(cid, {
                        "type": "per_started",
                        "target": target,
                        "mode": mode,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # 执行 P-E-R 循环并推送事件
                    async for event in agent.run(target=target, goal=goal, mode=mode):
                        event["timestamp"] = datetime.now().isoformat()
                        await manager.send_json(cid, event)
                        
                        # 如果是完成或错误事件，结束循环
                        if event.get("type") in ["complete", "error"]:
                            break
                    
                except ImportError as e:
                    await manager.send_json(cid, {
                        "type": "error",
                        "message": f"导入模块失败: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"P-E-R 执行失败: {e}")
                    await manager.send_json(cid, {
                        "type": "error",
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
        logger.error(f"WebSocket 错误: {e}")
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
            data = await websocket.receive_json()
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
