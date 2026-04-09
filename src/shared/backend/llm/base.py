# -*- coding: utf-8 -*-
"""
LLMBackend 抽象层 — 核心数据类与抽象基类

提供统一接口，隔离具体 LLM 提供商（OpenAI、DeepSeek、Anthropic、Ollama 等），
使上层业务代码（P-E-R 框架）无需感知底层 SDK 差异。
"""

import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """工具调用（Function Call）"""
    id: str
    name: str
    arguments: Dict[str, Any]

    def to_openai_format(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }

    @classmethod
    def from_openai_format(cls, data: Dict[str, Any]) -> "ToolCall":
        fn = data.get("function", {})
        raw_args = fn.get("arguments", "{}")
        try:
            arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            arguments = {}
        return cls(id=data.get("id", ""), name=fn.get("name", ""), arguments=arguments)


@dataclass
class ChatResponse:
    """LLM 单次完整响应"""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)  # prompt/completion/total_tokens
    model: str = ""
    cost_usd: float = 0.0  # 成本追踪（部分提供商支持）


@dataclass
class StreamChunk:
    """流式响应的单个块"""
    type: str           # "content" | "tool_call_delta" | "finish" | "error"
    content: str = ""
    tool_call_delta: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------

class LLMBackend(ABC):
    """
    LLM 后端抽象基类。

    所有具体提供商（OpenAI、DeepSeek、Anthropic、Ollama、Mock）均继承此类，
    实现 `chat` 和 `stream_chat` 两个核心方法。

    示例：
        backend = create_backend("openai", api_key="...", model="gpt-4o")
        resp = await backend.chat([{"role": "user", "content": "hello"}])
        print(resp.content)
    """

    # ------------------------------------------------------------------
    # 必须实现的接口
    # ------------------------------------------------------------------

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        """非流式对话

        Args:
            messages:    OpenAI 格式消息列表
            tools:       Function Calling 工具定义（可选）
            temperature: 采样温度
            max_tokens:  最大生成 token 数

        Returns:
            ChatResponse
        """
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """流式对话（异步生成器）

        用法：
            async for chunk in backend.stream_chat(messages):
                if chunk.type == "content":
                    print(chunk.content, end="")

        Yields:
            StreamChunk（type="content" 表示文本增量，"finish" 表示结束）

        注意：实现此方法时直接使用 yield，调用方不需要 await。
        """
        # 子类实现须带 yield，使其成为异步生成器
        yield  # type: ignore[misc]

    # ------------------------------------------------------------------
    # 可选覆盖的属性
    # ------------------------------------------------------------------

    @property
    def supports_function_calling(self) -> bool:
        """是否支持 Function Calling / Tool Use"""
        return True

    @property
    def model_name(self) -> str:
        """当前使用的模型名称"""
        return ""

    @property
    def provider_name(self) -> str:
        """提供商名称（openai / deepseek / anthropic / ollama / mock）"""
        return "unknown"
