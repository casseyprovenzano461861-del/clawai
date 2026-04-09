#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI CLI 会话持久化模块
支持将 Session 对象保存/加载到本地 JSON 文件。
存储目录：~/.clawai/sessions/
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.cli.config import get_config

logger = logging.getLogger(__name__)


def _dt_to_str(v: Any) -> Any:
    """将 datetime 递归序列化为字符串"""
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _dt_to_str(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [_dt_to_str(i) for i in v]
    return v


class SessionStore:
    """会话持久化存储"""

    def __init__(self):
        self._dir = get_config().sessions_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

    # ------------------------------------------------------------------
    # 保存
    # ------------------------------------------------------------------

    def save(self, session) -> bool:
        """
        保存 Session 对象（chat_cli.Session dataclass）到 JSON 文件。
        如果传入的是普通 dict 也可以。
        返回是否成功。
        """
        try:
            if hasattr(session, "__dataclass_fields__"):
                data = self._serialize_session(session)
            elif isinstance(session, dict):
                data = session
            else:
                raise TypeError(f"不支持的类型: {type(session)}")

            path = self._path(data["session_id"])
            with open(path, "w", encoding="utf-8") as f:
                json.dump(_dt_to_str(data), f, ensure_ascii=False, indent=2)
            logger.debug(f"会话已保存: {path}")
            return True
        except Exception as e:
            logger.error(f"会话保存失败: {e}")
            return False

    def _serialize_session(self, session) -> Dict[str, Any]:
        """将 Session dataclass 序列化为 dict"""
        messages = []
        for msg in session.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, "isoformat") else str(msg.timestamp),
                "metadata": msg.metadata,
            })

        return {
            "session_id": session.session_id,
            "target": session.target,
            "phase": session.phase,
            "findings": session.findings,
            "messages": messages,
            "interventions": getattr(session, "interventions", []),
            "created_at": session.created_at.isoformat() if hasattr(session.created_at, "isoformat") else str(session.created_at),
            "updated_at": session.updated_at.isoformat() if hasattr(session.updated_at, "isoformat") else str(session.updated_at),
        }

    # ------------------------------------------------------------------
    # 加载
    # ------------------------------------------------------------------

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """按 session_id 加载会话，返回 dict（含 messages/findings 等）"""
        path = self._path(session_id)
        if not path.exists():
            logger.warning(f"会话文件不存在: {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"会话加载失败: {e}")
            return None

    def load_as_session(self, session_id: str):
        """加载会话并还原为 Session dataclass，返回 Session 或 None"""
        data = self.load(session_id)
        if data is None:
            return None
        return self._deserialize_session(data)

    def _deserialize_session(self, data: Dict[str, Any]):
        """将 dict 还原为 Session dataclass"""
        try:
            from src.cli.chat_cli import Session, Message
            from datetime import datetime

            def parse_dt(s):
                if s is None:
                    return datetime.now()
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    return datetime.now()

            messages = []
            for m in data.get("messages", []):
                msg = Message(
                    role=m["role"],
                    content=m["content"],
                    timestamp=parse_dt(m.get("timestamp")),
                    metadata=m.get("metadata", {}),
                )
                messages.append(msg)

            session = Session(
                session_id=data["session_id"],
                target=data.get("target"),
                phase=data.get("phase", "idle"),
                findings=data.get("findings", []),
                messages=messages,
                interventions=data.get("interventions", []),
                created_at=parse_dt(data.get("created_at")),
                updated_at=parse_dt(data.get("updated_at")),
            )
            return session
        except Exception as e:
            logger.error(f"会话反序列化失败: {e}")
            return None

    # ------------------------------------------------------------------
    # 列表 / 删除
    # ------------------------------------------------------------------

    def list_sessions(self) -> List[Dict[str, Any]]:
        """返回所有已保存会话的摘要列表，按更新时间倒序"""
        results = []
        for path in sorted(self._dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append({
                    "session_id": data.get("session_id", path.stem),
                    "target": data.get("target", ""),
                    "phase": data.get("phase", ""),
                    "findings_count": len(data.get("findings", [])),
                    "messages_count": len(data.get("messages", [])),
                    "interventions_count": len(data.get("interventions", [])),
                    "start_time": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception:
                continue
        return results

    def delete(self, session_id: str) -> bool:
        """删除会话文件"""
        path = self._path(session_id)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"删除会话失败: {e}")
        return False

    def delete_all(self) -> int:
        """删除全部会话，返回删除数量"""
        count = 0
        for path in self._dir.glob("*.json"):
            try:
                path.unlink()
                count += 1
            except Exception:
                pass
        return count
