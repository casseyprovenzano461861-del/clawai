# -*- coding: utf-8 -*-
"""
对话管理器
管理多轮对话、上下文和会话持久化
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息"""
    role: str                                      # system/user/assistant/tool
    content: str                                   # 消息内容
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # 工具调用（assistant 消息）
    tool_call_id: str = ""                        # 工具调用ID（tool 消息）
    name: str = ""                                # 名称（tool 消息的工具名）
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 消息格式"""
        msg = {"role": self.role, "content": self.content}
        
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        
        if self.name:
            msg["name"] = self.name
        
        return msg
    
    @classmethod
    def from_openai_format(cls, data: Dict[str, Any]) -> "Message":
        """从 OpenAI 格式创建"""
        return cls(
            role=data.get("role", ""),
            content=data.get("content", ""),
            tool_calls=data.get("tool_calls", []),
            tool_call_id=data.get("tool_call_id", ""),
            name=data.get("name", ""),
            timestamp=datetime.now().isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(**data)


@dataclass
class ConversationContext:
    """对话上下文"""
    target: str = ""                              # 当前目标
    phase: str = "idle"                           # 当前阶段
    findings: List[str] = field(default_factory=list)  # 发现列表
    scan_results: Dict[str, Any] = field(default_factory=dict)  # 扫描结果
    vulnerabilities: List[Dict] = field(default_factory=list)  # 漏洞列表
    current_task: str = ""                        # 当前任务
    mode: str = "chat"                            # 模式: chat/autonomous
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """从字典创建"""
        return cls(**data)


@dataclass
class Session:
    """会话"""
    id: str                                       # 会话ID
    created_at: str                               # 创建时间
    updated_at: str                               # 更新时间
    messages: List[Message] = field(default_factory=list)  # 消息列表
    context: ConversationContext = field(default_factory=ConversationContext)  # 上下文
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context.to_dict(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            context=ConversationContext.from_dict(data.get("context", {})),
            metadata=data.get("metadata", {})
        )


class ConversationManager:
    """对话管理器
    
    负责：
    1. 消息历史管理
    2. 上下文维护
    3. 会话持久化
    4. 消息格式化
    """
    
    def __init__(
        self,
        session_id: str = None,
        max_history: int = 20,
        persist_dir: str = None
    ):
        """初始化对话管理器
        
        Args:
            session_id: 会话ID，如果为空则自动生成
            max_history: 最大历史消息数量
            persist_dir: 持久化目录
        """
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.max_history = max_history
        self.persist_dir = persist_dir or "data/sessions"
        
        # 创建会话
        now = datetime.now().isoformat()
        self.session = Session(
            id=self.session_id,
            created_at=now,
            updated_at=now
        )
        
        # 确保持久化目录存在
        if self.persist_dir:
            os.makedirs(self.persist_dir, exist_ok=True)
        
        logger.info(f"对话管理器初始化完成，会话ID: {self.session_id}")
    
    # ==================== 消息管理 ====================
    
    def add_message(
        self,
        role: str,
        content: str,
        tool_calls: List[Dict] = None,
        tool_call_id: str = "",
        name: str = "",
        metadata: Dict = None
    ) -> Message:
        """添加消息到历史
        
        Args:
            role: 角色 (system/user/assistant/tool)
            content: 内容
            tool_calls: 工具调用列表
            tool_call_id: 工具调用ID
            name: 名称
            metadata: 元数据
            
        Returns:
            Message: 创建的消息对象
        """
        message = Message(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            tool_call_id=tool_call_id,
            name=name,
            metadata=metadata or {}
        )
        
        self.session.messages.append(message)
        self.session.updated_at = datetime.now().isoformat()
        
        # 检查是否需要截断历史
        self._trim_history()
        
        logger.debug(f"添加消息: {role} -> {content[:50]}...")
        
        return message
    
    def add_user_message(self, content: str, metadata: Dict = None) -> Message:
        """添加用户消息"""
        return self.add_message("user", content, metadata=metadata)
    
    def add_assistant_message(
        self,
        content: str,
        tool_calls: List[Dict] = None,
        metadata: Dict = None
    ) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content, tool_calls=tool_calls, metadata=metadata)
    
    def add_tool_message(
        self,
        content: str,
        tool_call_id: str,
        name: str = "",
        metadata: Dict = None
    ) -> Message:
        """添加工具消息"""
        return self.add_message(
            "tool", content, 
            tool_call_id=tool_call_id, 
            name=name, 
            metadata=metadata
        )
    
    def add_system_message(self, content: str, metadata: Dict = None) -> Message:
        """添加系统消息"""
        return self.add_message("system", content, metadata=metadata)
    
    def get_messages(self) -> List[Message]:
        """获取所有消息"""
        return self.session.messages
    
    def get_messages_for_llm(self, include_system: bool = True) -> List[Dict[str, Any]]:
        """获取格式化的消息历史（用于 LLM 调用）
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            List[Dict]: OpenAI 格式的消息列表
        """
        messages = []
        for msg in self.session.messages:
            # 跳过系统消息（通常由 Agent Core 单独处理）
            if msg.role == "system" and not include_system:
                continue
            messages.append(msg.to_openai_format())
        
        return messages
    
    def get_last_message(self) -> Optional[Message]:
        """获取最后一条消息"""
        if self.session.messages:
            return self.session.messages[-1]
        return None
    
    def get_last_user_message(self) -> Optional[Message]:
        """获取最后的用户消息"""
        for msg in reversed(self.session.messages):
            if msg.role == "user":
                return msg
        return None
    
    def clear_messages(self):
        """清空消息历史"""
        self.session.messages.clear()
        self.session.updated_at = datetime.now().isoformat()
        logger.info("消息历史已清空")
    
    # ==================== 上下文管理 ====================
    
    def update_context(self, **kwargs):
        """更新上下文
        
        Args:
            **kwargs: 要更新的上下文字段
        """
        for key, value in kwargs.items():
            if hasattr(self.session.context, key):
                setattr(self.session.context, key, value)
        
        self.session.updated_at = datetime.now().isoformat()
        logger.debug(f"更新上下文: {kwargs}")
    
    def set_target(self, target: str):
        """设置目标"""
        self.update_context(target=target, phase="target_set")
    
    def set_phase(self, phase: str):
        """设置阶段"""
        self.update_context(phase=phase)
    
    def add_finding(self, finding: str):
        """添加发现"""
        self.session.context.findings.append(finding)
        self.session.updated_at = datetime.now().isoformat()
    
    def add_vulnerability(self, vuln: Dict):
        """添加漏洞"""
        self.session.context.vulnerabilities.append(vuln)
        self.session.updated_at = datetime.now().isoformat()
    
    def update_scan_results(self, tool: str, results: Dict):
        """更新扫描结果"""
        self.session.context.scan_results[tool] = results
        self.session.updated_at = datetime.now().isoformat()
    
    def get_context(self) -> ConversationContext:
        """获取上下文"""
        return self.session.context
    
    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        ctx = self.session.context
        parts = []
        
        if ctx.target:
            parts.append(f"目标: {ctx.target}")
        
        if ctx.phase:
            parts.append(f"阶段: {ctx.phase}")
        
        if ctx.findings:
            parts.append(f"发现: {len(ctx.findings)}项")
        
        if ctx.vulnerabilities:
            parts.append(f"漏洞: {len(ctx.vulnerabilities)}个")
        
        return " | ".join(parts) if parts else "无上下文"
    
    # ==================== 会话持久化 ====================
    
    def save_session(self, path: str = None) -> str:
        """保存会话到文件
        
        Args:
            path: 文件路径，如果为空则使用默认路径
            
        Returns:
            str: 保存的文件路径
        """
        if not path:
            path = os.path.join(self.persist_dir, f"{self.session_id}.json")
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.session.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"会话已保存: {path}")
            return path
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            raise
    
    def load_session(self, path: str = None) -> bool:
        """从文件加载会话
        
        Args:
            path: 文件路径，如果为空则使用默认路径
            
        Returns:
            bool: 是否加载成功
        """
        if not path:
            path = os.path.join(self.persist_dir, f"{self.session_id}.json")
        
        if not os.path.exists(path):
            logger.warning(f"会话文件不存在: {path}")
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.session = Session.from_dict(data)
            self.session_id = self.session.id
            
            logger.info(f"会话已加载: {path}, 消息数: {len(self.session.messages)}")
            return True
            
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
            return False
    
    def delete_session(self, path: str = None) -> bool:
        """删除会话文件
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否删除成功
        """
        if not path:
            path = os.path.join(self.persist_dir, f"{self.session_id}.json")
        
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"会话文件已删除: {path}")
                return True
            except Exception as e:
                logger.error(f"删除会话文件失败: {e}")
                return False
        
        return False
    
    @classmethod
    def list_sessions(cls, persist_dir: str = "data/sessions") -> List[Dict[str, Any]]:
        """列出所有会话
        
        Args:
            persist_dir: 持久化目录
            
        Returns:
            List[Dict]: 会话列表
        """
        sessions = []
        
        if not os.path.exists(persist_dir):
            return sessions
        
        for filename in os.listdir(persist_dir):
            if filename.endswith('.json'):
                path = os.path.join(persist_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        "id": data.get("id", ""),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": len(data.get("messages", [])),
                        "target": data.get("context", {}).get("target", ""),
                        "path": path
                    })
                    
                except Exception as e:
                    logger.warning(f"读取会话文件失败 {filename}: {e}")
        
        # 按更新时间倒序排序
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return sessions
    
    # ==================== 辅助方法 ====================
    
    def _trim_history(self):
        """截断历史消息，保持在最大数量以内"""
        if len(self.session.messages) > self.max_history:
            # 保留系统消息（如果有）
            system_messages = [m for m in self.session.messages if m.role == "system"]
            other_messages = [m for m in self.session.messages if m.role != "system"]
            
            # 截断其他消息
            if len(other_messages) > self.max_history - len(system_messages):
                other_messages = other_messages[-(self.max_history - len(system_messages)):]
            
            self.session.messages = system_messages + other_messages
            logger.debug(f"截断历史消息，当前数量: {len(self.session.messages)}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        role_counts = {}
        for msg in self.session.messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1
        
        return {
            "session_id": self.session_id,
            "created_at": self.session.created_at,
            "updated_at": self.session.updated_at,
            "total_messages": len(self.session.messages),
            "role_counts": role_counts,
            "context": self.session.context.to_dict()
        }
    
    def export_to_markdown(self, path: str = None) -> str:
        """导出会话为 Markdown 格式
        
        Args:
            path: 导出路径
            
        Returns:
            str: Markdown 内容
        """
        lines = [
            f"# ClawAI 会话记录",
            f"",
            f"- 会话ID: {self.session_id}",
            f"- 创建时间: {self.session.created_at}",
            f"- 更新时间: {self.session.updated_at}",
            f"- {self.get_context_summary()}",
            f"",
            f"## 对话历史",
            f""
        ]
        
        role_names = {
            "system": "系统",
            "user": "用户",
            "assistant": "助手",
            "tool": "工具"
        }
        
        for msg in self.session.messages:
            role = role_names.get(msg.role, msg.role)
            lines.append(f"### {role}")
            lines.append(f"```\n{msg.content}\n```")
            
            if msg.tool_calls:
                lines.append(f"**工具调用:**")
                for tc in msg.tool_calls:
                    func = tc.get("function", {})
                    lines.append(f"- {func.get('name', '')}({func.get('arguments', '')})")
            
            lines.append("")
        
        content = "\n".join(lines)
        
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"会话已导出: {path}")
        
        return content


# ==================== 测试 ====================

def test_conversation_manager():
    """测试对话管理器"""
    print("=" * 60)
    print("对话管理器测试")
    print("=" * 60)
    
    # 创建管理器
    manager = ConversationManager(session_id="test_session")
    
    # 添加消息
    print("\n1. 添加消息:")
    manager.add_system_message("你是 ClawAI 渗透测试助手")
    manager.add_user_message("帮我扫描 example.com")
    manager.add_assistant_message("好的，我来帮你扫描 example.com", tool_calls=[
        {"id": "call_1", "type": "function", "function": {"name": "nmap_scan", "arguments": '{"target": "example.com"}'}}
    ])
    manager.add_tool_message('{"ports": [{"port": 80, "service": "http"}]}', "call_1", "nmap_scan")
    
    print(f"消息数量: {len(manager.get_messages())}")
    
    # 测试上下文
    print("\n2. 上下文管理:")
    manager.set_target("example.com")
    manager.set_phase("scanning")
    manager.add_finding("端口 80 开放，运行 HTTP 服务")
    manager.add_vulnerability({"type": "SQL注入", "severity": "high", "url": "/page?id=1"})
    
    print(f"上下文摘要: {manager.get_context_summary()}")
    
    # 测试格式化
    print("\n3. LLM 格式化消息:")
    for msg in manager.get_messages_for_llm():
        print(f"  {msg['role']}: {msg['content'][:50]}..." if len(msg.get('content', '')) > 50 else f"  {msg}")
    
    # 测试统计
    print("\n4. 会话统计:")
    stats = manager.get_session_stats()
    print(f"  总消息数: {stats['total_messages']}")
    print(f"  角色分布: {stats['role_counts']}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_conversation_manager()
