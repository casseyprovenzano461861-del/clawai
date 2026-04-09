# -*- coding: utf-8 -*-
"""
Anthropic Claude Backend

使用 anthropic SDK 直连，处理与 OpenAI 格式的消息差异：
- 系统消息单独传入（system 参数），不放在 messages 列表
- 工具调用使用 tool_use / tool_result 格式

依赖：anthropic >= 0.20.0
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Tuple

from .base import ChatResponse, LLMBackend, StreamChunk, ToolCall

logger = logging.getLogger(__name__)

# Anthropic 模型每 1k token 的参考成本（USD）
_COST_PER_1K_INPUT: Dict[str, float] = {
    "claude-3-5-sonnet-20241022": 0.003,
    "claude-3-5-haiku-20241022": 0.0008,
    "claude-3-opus-20240229": 0.015,
    "claude-3-sonnet-20240229": 0.003,
    "claude-3-haiku-20240307": 0.00025,
}
_COST_PER_1K_OUTPUT: Dict[str, float] = {
    "claude-3-5-sonnet-20241022": 0.015,
    "claude-3-5-haiku-20241022": 0.004,
    "claude-3-opus-20240229": 0.075,
    "claude-3-sonnet-20240229": 0.015,
    "claude-3-haiku-20240307": 0.00125,
}


class AnthropicBackend(LLMBackend):
    """Anthropic Claude 后端实现"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._timeout = timeout
        self._client = self._build_client()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _build_client(self):
        try:
            import anthropic

            kwargs: Dict[str, Any] = {
                "api_key": self._api_key,
                "timeout": self._timeout,
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url

            client = anthropic.Anthropic(**kwargs)
            logger.info(f"AnthropicBackend 初始化: model={self._model}")
            return client
        except ImportError:
            logger.error("anthropic 包未安装，请执行: pip install anthropic")
            return None

    # ------------------------------------------------------------------
    # 消息格式转换
    # ------------------------------------------------------------------

    @staticmethod
    def _split_system(messages: List[Dict[str, Any]]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """将 OpenAI 格式的 system 消息提取出来，其余转换为 Anthropic 格式"""
        system_parts: List[str] = []
        anthropic_messages: List[Dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(content)
            elif role == "tool":
                # OpenAI tool result → Anthropic tool_result
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.get("tool_call_id", ""),
                                "content": content,
                            }
                        ],
                    }
                )
            elif role == "assistant" and msg.get("tool_calls"):
                # OpenAI assistant with tool_calls → Anthropic tool_use
                blocks: List[Dict[str, Any]] = []
                if content:
                    blocks.append({"type": "text", "text": content})
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    import json

                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": fn.get("name", ""),
                            "input": args,
                        }
                    )
                anthropic_messages.append({"role": "assistant", "content": blocks})
            else:
                anthropic_messages.append({"role": role, "content": content})

        system = "\n\n".join(system_parts) if system_parts else None
        return system, anthropic_messages

    @staticmethod
    def _convert_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将 OpenAI Function Calling 工具定义转为 Anthropic tool 格式"""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") != "function":
                continue
            fn = tool.get("function", {})
            anthropic_tools.append(
                {
                    "name": fn.get("name", ""),
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                }
            )
        return anthropic_tools

    # ------------------------------------------------------------------
    # 核心接口
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        if self._client is None:
            return ChatResponse(
                content="[错误] anthropic 包未安装，无法调用 Claude",
                finish_reason="error",
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sync_chat(messages, tools, temperature, max_tokens),
        )

    def _sync_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
    ) -> ChatResponse:
        try:
            system, anthropic_messages = self._split_system(messages)

            params: Dict[str, Any] = {
                "model": self._model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system:
                params["system"] = system
            if tools:
                params["tools"] = self._convert_tools(tools)

            response = self._client.messages.create(**params)

            # 解析内容和工具调用
            text_parts: List[str] = []
            tool_calls: List[ToolCall] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input or {},
                        )
                    )

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }

            cost = self._estimate_cost(
                response.usage.input_tokens if response.usage else 0,
                response.usage.output_tokens if response.usage else 0,
            )

            return ChatResponse(
                content="".join(text_parts),
                tool_calls=tool_calls,
                finish_reason=response.stop_reason or "stop",
                usage=usage,
                model=response.model,
                cost_usd=cost,
            )

        except Exception as e:
            logger.error(f"AnthropicBackend.chat 失败: {e}")
            return ChatResponse(
                content=f"[LLM 调用失败] {e}",
                finish_reason="error",
            )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        if self._client is None:
            yield StreamChunk(type="error", error="anthropic 包未安装")
            return

        import queue
        import threading

        q: queue.Queue = queue.Queue()
        _SENTINEL = object()

        def _run_stream():
            try:
                system, anthropic_messages = self._split_system(messages)
                params: Dict[str, Any] = {
                    "model": self._model,
                    "messages": anthropic_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                if system:
                    params["system"] = system
                if tools:
                    params["tools"] = self._convert_tools(tools)

                with self._client.messages.stream(**params) as stream:
                    for text in stream.text_stream:
                        q.put(("content", text))
                    q.put(("finish", stream.get_final_message().stop_reason or "stop"))
            except Exception as e:
                q.put(("error", str(e)))
            finally:
                q.put(_SENTINEL)

        thread = threading.Thread(target=_run_stream, daemon=True)
        thread.start()

        loop = asyncio.get_event_loop()
        while True:
            item = await loop.run_in_executor(None, q.get)
            if item is _SENTINEL:
                break
            event_type, data = item
            if event_type == "content":
                yield StreamChunk(type="content", content=data)
            elif event_type == "finish":
                yield StreamChunk(type="finish", finish_reason=data)
                break
            elif event_type == "error":
                yield StreamChunk(type="error", error=data)
                break

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def supports_function_calling(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        in_rate = _COST_PER_1K_INPUT.get(self._model, 0.003)
        out_rate = _COST_PER_1K_OUTPUT.get(self._model, 0.015)
        return round(input_tokens / 1000 * in_rate + output_tokens / 1000 * out_rate, 6)
