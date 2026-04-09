"""Scan state machine for tracking and controlling scan progress."""

from __future__ import annotations

import enum
import threading
from typing import Optional


class ScanState(enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


# Valid state transitions
_TRANSITIONS = {
    (ScanState.IDLE, ScanState.RUNNING),
    (ScanState.RUNNING, ScanState.COMPLETED),
    (ScanState.RUNNING, ScanState.ERROR),
    (ScanState.RUNNING, ScanState.PAUSED),
    (ScanState.PAUSED, ScanState.RUNNING),
    (ScanState.PAUSED, ScanState.COMPLETED),
    (ScanState.PAUSED, ScanState.ERROR),
    (ScanState.ERROR, ScanState.IDLE),
    (ScanState.COMPLETED, ScanState.IDLE),
}


class ScanStateMachine:
    """Thread-safe scan state machine with iteration tracking."""

    def __init__(self) -> None:
        self._state = ScanState.IDLE
        self._lock = threading.Lock()
        self._current_iteration = 0
        self._max_iterations = 0
        self._current_tool: Optional[str] = None
        self._current_phase: Optional[str] = None
        self._target: Optional[str] = None

    @property
    def state(self) -> ScanState:
        return self._state

    @property
    def current_iteration(self) -> int:
        return self._current_iteration

    @property
    def max_iterations(self) -> int:
        return self._max_iterations

    @property
    def current_tool(self) -> Optional[str]:
        return self._current_tool

    @property
    def current_phase(self) -> Optional[str]:
        return self._current_phase

    @property
    def target(self) -> Optional[str]:
        return self._target

    def transition(self, new_state: ScanState) -> None:
        with self._lock:
            key = (self._state, new_state)
            if key not in _TRANSITIONS:
                raise ValueError(f"Invalid state transition: {self._state.value} -> {new_state.value}")
            self._state = new_state
            if new_state == ScanState.IDLE:
                self._current_iteration = 0
                self._max_iterations = 0
                self._current_tool = None
                self._current_phase = None
                self._target = None

    def start(self, target: str, max_iterations: int) -> None:
        self._target = target
        self._max_iterations = max_iterations
        self.transition(ScanState.RUNNING)

    def set_iteration(self, iteration: int, phase: str, tool: Optional[str] = None) -> None:
        with self._lock:
            self._current_iteration = iteration
            self._current_phase = phase
            self._current_tool = tool

    def is_running(self) -> bool:
        return self._state in (ScanState.RUNNING, ScanState.PAUSED)

    def pause(self) -> None:
        """暂停扫描"""
        self.transition(ScanState.PAUSED)

    def resume(self) -> None:
        """恢复扫描"""
        self.transition(ScanState.RUNNING)

    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._state == ScanState.PAUSED

    def format_status(self) -> str:
        if self._state == ScanState.IDLE:
            return "就绪"
        if self._state == ScanState.RUNNING:
            parts = [f"扫描 {self.target or '?'}"]
            if self._current_iteration > 0:
                parts.append(f"[{self._current_iteration}/{self._max_iterations}]")
            if self._current_phase:
                parts.append(self._current_phase)
            return " ".join(parts)
        if self._state == ScanState.PAUSED:
            return f"已暂停 [{self._current_iteration}/{self._max_iterations}]"
        if self._state == ScanState.COMPLETED:
            return "扫描完成"
        if self._state == ScanState.ERROR:
            return "扫描出错"
        return self._state.value
