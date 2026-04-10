# -*- coding: utf-8 -*-
"""
ClawAI EventBus — Agent（P-E-R）和 UI（TUI/CLI）之间的解耦通信机制

设计原则：
- 单例，全进程共享
- 线程安全
- 订阅者异常不影响其他订阅者
"""

import contextlib
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional


class EventType(Enum):
    """事件类型"""

    # Agent -> UI 事件
    STATE_CHANGED = auto()  # idle / running / paused / completed / error
    MESSAGE = auto()        # 文本消息（info / success / error / warning）
    TOOL = auto()           # 工具调用（start / complete / error）
    FINDING = auto()        # 发现漏洞/关键信息
    FLAG_FOUND = auto()     # 发现 Flag（高优先级，单独事件）
    PROGRESS = auto()       # 进度更新（percent + description）

    # UI -> Agent 事件
    USER_COMMAND = auto()   # pause / resume / stop
    USER_INPUT = auto()     # 用户追加的自然语言指令


@dataclass
class Event:
    """事件容器"""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    """最小化线程安全事件总线（pub/sub）"""

    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Callable[[Event], None]]] = {}
        self._handler_lock = threading.Lock()

    # ------------------------------------------------------------------
    # 单例管理
    # ------------------------------------------------------------------

    @classmethod
    def get(cls) -> "EventBus":
        """获取全局单例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """重置单例（主要用于测试）"""
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # 订阅 / 取消订阅
    # ------------------------------------------------------------------

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """订阅事件

        Args:
            event_type: 要订阅的事件类型
            handler: 事件处理回调
        """
        with self._handler_lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """取消订阅

        Args:
            event_type: 事件类型
            handler: 要移除的回调
        """
        with self._handler_lock:
            if event_type in self._handlers:
                with contextlib.suppress(ValueError):
                    self._handlers[event_type].remove(handler)

    # ------------------------------------------------------------------
    # 发射
    # ------------------------------------------------------------------

    def emit(self, event: Event) -> None:
        """发射事件给所有订阅者

        Args:
            event: 要发射的事件
        """
        with self._handler_lock:
            handlers = self._handlers.get(event.type, []).copy()

        for handler in handlers:
            # 某个订阅者抛异常不影响其他订阅者
            with contextlib.suppress(Exception):
                handler(event)

    # ------------------------------------------------------------------
    # 便利方法
    # ------------------------------------------------------------------

    def emit_state(
        self,
        state: str,
        details: str = "",
        target: Optional[str] = None,
        task: Optional[str] = None,
    ) -> None:
        """发射状态变更事件

        Args:
            state: 新状态（idle / running / paused / completed / error）
            details: 状态说明
            target: 当前目标（IP/URL）
            task: 当前任务描述
        """
        data: dict[str, Any] = {"state": state, "details": details}
        if target is not None:
            data["target"] = target
        if task is not None:
            data["task"] = task
        self.emit(Event(EventType.STATE_CHANGED, data))

    def emit_message(self, text: str, msg_type: str = "info") -> None:
        """发射文本消息事件

        Args:
            text: 消息内容
            msg_type: 消息类型（info / success / error / warning）
        """
        self.emit(Event(EventType.MESSAGE, {"text": text, "type": msg_type}))

    def emit_tool(
        self,
        status: str,
        name: str,
        args: Optional[dict[str, Any]] = None,
        result: Any = None,
    ) -> None:
        """发射工具调用事件

        Args:
            status: 状态（start / complete / error）
            name: 工具名称
            args: 调用参数
            result: 执行结果（status=complete 时填写）
        """
        self.emit(
            Event(
                EventType.TOOL,
                {"status": status, "name": name, "args": args or {}, "result": result},
            )
        )

    def emit_finding(self, title: str, severity: str = "info", detail: str = "") -> None:
        """发射发现事件（漏洞/关键信息）

        Args:
            title: 发现标题
            severity: 严重程度（critical / high / medium / low / info）
            detail: 详细说明
        """
        self.emit(Event(EventType.FINDING, {"title": title, "severity": severity, "detail": detail}))

    def emit_flag(self, flag_value: str, location: str = "", method: str = "") -> None:
        """发射 Flag 发现事件（高优先级）

        Args:
            flag_value: Flag 的值（如 flag{xxxxx}）
            location: 发现位置（文件路径、URL 等）
            method: 利用方式简述
        """
        self.emit(Event(
            EventType.FLAG_FOUND,
            {"flag": flag_value, "location": location, "method": method},
        ))
        # 同时以 FINDING 事件冒泡，确保 UI 订阅者也能感知
        self.emit_finding(
            title=f"⚑ FLAG FOUND: {flag_value}",
            severity="critical",
            detail=f"位置: {location} | 方法: {method}",
        )

    def emit_progress(self, percent: float, description: str = "") -> None:
        """发射进度事件

        Args:
            percent: 完成百分比（0.0 ~ 1.0）
            description: 当前步骤描述
        """
        self.emit(Event(EventType.PROGRESS, {"percent": percent, "description": description}))

    def emit_command(self, command: str) -> None:
        """发射用户命令事件

        Args:
            command: 命令（pause / resume / stop）
        """
        self.emit(Event(EventType.USER_COMMAND, {"command": command}))

    def emit_input(self, text: str) -> None:
        """发射用户输入事件

        Args:
            text: 用户自然语言指令
        """
        self.emit(Event(EventType.USER_INPUT, {"text": text}))
