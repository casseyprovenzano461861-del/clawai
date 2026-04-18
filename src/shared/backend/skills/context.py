"""
SkillContext — 依赖注入上下文（参考 Claude Code ToolUseContext 设计）

Skill 执行时通过 context 参数感知 session 状态、findings、phase 等信息，
而不仅仅依赖孤立的 params Dict。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class SkillContext:
    """Skill 执行上下文，由调用方构建并注入到 SkillExecutor.execute()。"""

    # --- session 基本信息 ---
    session_id: str = ""
    target: str = ""
    phase: str = "recon"  # recon / exploit / post

    # --- 已发现的 findings（只读快照，防止 Skill 意外修改 session 状态）---
    findings_snapshot: List[Dict[str, Any]] = field(default_factory=list)

    # --- 已触发过的 Skills（防重复触发）---
    dispatched_skills: Set[str] = field(default_factory=set)

    # --- abort 控制（threading.Event，因为 _execute_* 是同步阻塞调用）---
    abort_event: threading.Event = field(default_factory=threading.Event)

    # --- 扩展元数据（调用方自由填充）---
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------

    def is_aborted(self) -> bool:
        """检查是否已收到中止信号。"""
        return self.abort_event.is_set()

    def abort(self) -> None:
        """发出中止信号，通知正在执行的 Skill 尽快退出。"""
        self.abort_event.set()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 JSON-safe dict，可注入 subprocess 执行的 Python code 前缀。

        Python Skill code 中可通过 ``__skill_context__`` 全局变量读取：

        .. code-block:: python

            ctx = globals().get("__skill_context__", {})
            target = ctx.get("target", "")
            phase  = ctx.get("phase", "recon")
        """
        return {
            "session_id": self.session_id,
            "target": self.target,
            "phase": self.phase,
            "findings_count": len(self.findings_snapshot),
            "findings_snapshot": self.findings_snapshot,
            "dispatched_skills": list(self.dispatched_skills),
            "metadata": self.metadata,
        }

    # ------------------------------------------------------------------
    # 工厂方法
    # ------------------------------------------------------------------

    @classmethod
    def empty(cls) -> "SkillContext":
        """返回空 context，用于无状态场景（兼容旧调用）。"""
        return cls()

    @classmethod
    def from_session(
        cls,
        session_id: str,
        target: str,
        phase: str = "recon",
        findings: Optional[List[Dict[str, Any]]] = None,
        dispatched_skills: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "SkillContext":
        """从 session 字段快速构建 SkillContext。"""
        return cls(
            session_id=session_id,
            target=target,
            phase=phase,
            findings_snapshot=list(findings) if findings else [],
            dispatched_skills=set(dispatched_skills) if dispatched_skills else set(),
            metadata=metadata or {},
        )
