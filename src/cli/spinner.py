#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI Spinner 动画
黑客终端风格: 磷光绿 Braille 旋转 + 简洁状态

1. Braille 点阵旋转 (纯 ASCII 终端兼容)
2. 简洁动词 [processing] [scanning] [executing]
3. 停顿检测: 变红
4. 计时器
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable

from rich.text import Text
from rich.console import Console

# ── 调色板 ──
GRN   = "rgb(0,255,65)"
AMBER = "rgb(255,191,0)"
RED   = "rgb(255,60,60)"
DIM   = "rgb(80,110,80)"

# ── 旋转帧 ──
BRAILLE_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

# ── 动词 ──
VERBS = [
    "processing", "analyzing", "scanning", "computing",
    "decoding", "decrypting", "parsing", "querying",
    "resolving", "thinking", "inferring", "deducing",
]

TOOL_VERBS = [
    "executing", "running", "invoking", "launching", "firing",
]


class SpinnerMode(Enum):
    REQUESTING = "requesting"
    RESPONDING = "responding"
    TOOL_USE = "tool_use"
    THINKING = "thinking"


MODE_COLOR = {
    SpinnerMode.REQUESTING: GRN,
    SpinnerMode.RESPONDING: GRN,
    SpinnerMode.TOOL_USE: GRN,
    SpinnerMode.THINKING: AMBER,
}


@dataclass
class SpinnerState:
    mode: SpinnerMode = SpinnerMode.REQUESTING
    verb: str = ""
    start_time: float = 0.0
    last_output_time: float = 0.0
    frame_index: int = 0
    is_stalled: bool = False


class AsyncSpinner:
    """黑客终端风格异步 Spinner"""

    FRAME_INTERVAL = 0.08  # 80ms — 快速旋转
    STALL_THRESHOLD = 3.0

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._state = SpinnerState()
        self._task: Optional[asyncio.Task] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, mode: SpinnerMode = SpinnerMode.REQUESTING,
              verb: Optional[str] = None) -> None:
        if self._running:
            return
        self._state = SpinnerState(
            mode=mode,
            verb=verb or self._pick_verb(mode),
            start_time=time.time(),
            last_output_time=time.time(),
        )
        self._running = True
        self._task = asyncio.ensure_future(self._spin_loop())

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    def update_output(self, text: str = "") -> None:
        self._state.last_output_time = time.time()
        self._state.is_stalled = False

    def set_mode(self, mode: SpinnerMode, verb: Optional[str] = None) -> None:
        self._state.mode = mode
        if verb:
            self._state.verb = verb

    def render_line(self) -> Text:
        """渲染一行 spinner"""
        now = time.time()
        elapsed = now - self._state.start_time
        state = self._state

        # 旋转字符
        frame = state.frame_index % len(BRAILLE_FRAMES)
        ch = BRAILLE_FRAMES[frame]

        # 停顿检测
        time_since_output = now - state.last_output_time
        if time_since_output > self.STALL_THRESHOLD and state.mode != SpinnerMode.THINKING:
            state.is_stalled = True

        # 颜色
        color = RED if state.is_stalled else MODE_COLOR.get(state.mode, GRN)

        # 构建: ⠋ [scanning...] (3s)
        result = Text()
        result.append(ch, style=f"bold {color}")
        result.append(" [", style=DIM)
        result.append(state.verb, style=color)
        dots = "." * (int(now * 3) % 4)  # 动态省略号
        result.append(dots, style=DIM)
        result.append("]", style=DIM)
        result.append(f" ({elapsed:.0f}s)", style=DIM)

        if state.is_stalled:
            result.append(" STALL", style=f"bold {RED}")

        return result

    def _pick_verb(self, mode: SpinnerMode) -> str:
        if mode == SpinnerMode.TOOL_USE:
            return random.choice(TOOL_VERBS)
        return random.choice(VERBS)

    async def _spin_loop(self) -> None:
        while self._running:
            self._state.frame_index += 1
            await asyncio.sleep(self.FRAME_INTERVAL)


async def spin_while_waiting(coro, console: Optional[Console] = None,
                            mode: SpinnerMode = SpinnerMode.REQUESTING,
                            verb: Optional[str] = None):
    from rich.live import Live
    _console = console or Console()
    spinner = AsyncSpinner(_console)
    spinner.start(mode=mode, verb=verb)
    try:
        with Live(spinner.render_line, console=_console, refresh_per_second=12,
                  vertical_overflow="visible"):
            result = await coro
            return result
    finally:
        spinner.stop()
