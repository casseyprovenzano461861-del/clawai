# -*- coding: utf-8 -*-
"""
EventBroker模块 - 事件总线
负责组件之间的通信
"""

from typing import Dict, Any, List, Callable


class EventBroker:
    """事件总线类"""
    
    def __init__(self):
        self._subscribers = {}
    
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def publish(self, event_type: str, data: Dict[str, Any]):
        """发布事件"""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"执行事件回调时出错: {e}")
    
    def get_subscribers(self, event_type: str) -> List[Callable]:
        """获取指定事件类型的订阅者"""
        return self._subscribers.get(event_type, [])
    
    def has_subscribers(self, event_type: str) -> bool:
        """检查是否有订阅者"""
        return event_type in self._subscribers and len(self._subscribers[event_type]) > 0


# 事件类型常量
class EventType:
    """事件类型"""
    # 任务相关事件
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # 节点相关事件
    NODE_STARTED = "node.started"
    NODE_COMPLETED = "node.completed"
    NODE_FAILED = "node.failed"
    
    # 执行相关事件
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    
    # 分析相关事件
    ANALYSIS_COMPLETED = "analysis.completed"
    INTELLIGENCE_GENERATED = "intelligence.generated"
    
    # 系统相关事件
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"
    
    # 代理相关事件
    AGENT_STATUS = "agent.status"
    AGENT_MESSAGE = "agent.message"
    
    # 工具相关事件
    TOOL_EXECUTION = "tool.execution"
    TOOL_START = "tool.start"
    TOOL_COMPLETE = "tool.complete"
    
    # 漏洞相关事件
    VULNERABILITY_FOUND = "vulnerability.found"
    VULNERABILITY_VERIFIED = "vulnerability.verified"
    
    # 会话相关事件
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_COMPLETED = "session.completed"


# 创建全局事件总线实例
event_broker = EventBroker()
