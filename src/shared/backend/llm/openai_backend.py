# -*- coding: utf-8 -*-
"""
OpenAI / DeepSeek Backend

通过 base_url 参数同时支持：
- OpenAI  (https://api.openai.com/v1)
- DeepSeek (https://api.deepseek.com/v1)
- 其他兼容 OpenAI API 的服务

依赖：openai >= 1.0.0
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from .base import ChatResponse, LLMBackend, StreamChunk, ToolCall

logger = logging.getLogger(__name__)

# DeepSeek 模型每 1k token 的参考成本（USD），仅供估算
_COST_PER_1K: Dict[str, float] = {
    "deepseek-chat": 0.00014,
    "deepseek-reasoner": 0.00055,
    "gpt-4o": 0.005,
    "gpt-4o-mini": 0.00015,
    "gpt-4": 0.03,
    "gpt-3.5-turbo": 0.0005,
}


class OpenAIBackend(LLMBackend):
    """OpenAI / DeepSeek / 兼容 OpenAI API 的后端实现"""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """
        Args:
            api_key:  API 密钥
            model:    模型名称
            base_url: 覆盖默认 API 地址（留空则使用 OpenAI 官方地址）
            timeout:  请求超时秒数
        """
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
            from openai import OpenAI

            kwargs: Dict[str, Any] = {
                "api_key": self._api_key,
                "timeout": self._timeout,
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url

            client = OpenAI(**kwargs)
            logger.info(f"OpenAIBackend 初始化: model={self._model}, base_url={self._base_url or 'default'}")
            return client
        except ImportError:
            logger.error("openai 包未安装，请执行: pip install openai")
            return None

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
                content="[错误] openai 包未安装，无法调用 LLM",
                finish_reason="error",
            )

        # OpenAI SDK 是同步的，在线程池中运行避免阻塞事件循环
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
            params: Dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = self._client.chat.completions.create(**params)
            choice = response.choices[0]

            # 解析工具调用
            tool_calls: List[ToolCall] = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append(
                        ToolCall.from_openai_format(
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        )
                    )

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            cost = self._estimate_cost(usage.get("total_tokens", 0))

            return ChatResponse(
                content=choice.message.content or "",
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage=usage,
                model=response.model,
                cost_usd=cost,
            )

        except Exception as e:
            logger.error(f"OpenAIBackend.chat 失败: {e}")
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
            yield StreamChunk(type="error", error="openai 包未安装")
            return

        # 同步流转异步队列
        import queue
        import threading

        q: queue.Queue = queue.Queue()
        _SENTINEL = object()

        def _run_stream():
            try:
                params: Dict[str, Any] = {
                    "model": self._model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                if tools:
                    params["tools"] = tools
                    params["tool_choice"] = "auto"

                stream = self._client.chat.completions.create(**params)
                for chunk in stream:
                    q.put(chunk)
            except Exception as e:
                q.put(e)
            finally:
                q.put(_SENTINEL)

        thread = threading.Thread(target=_run_stream, daemon=True)
        thread.start()

        loop = asyncio.get_event_loop()
        while True:
            item = await loop.run_in_executor(None, q.get)
            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                yield StreamChunk(type="error", error=str(item))
                break

            # 解析 chunk
            choice = item.choices[0] if item.choices else None
            if choice is None:
                continue

            delta = choice.delta
            if delta.content:
                yield StreamChunk(type="content", content=delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    yield StreamChunk(
                        type="tool_call_delta",
                        tool_call_delta={
                            "index": tc.index if tc.index is not None else 0,
                            "id": tc.id or "",
                            "name": (tc.function.name or "") if tc.function else "",
                            "arguments": (tc.function.arguments or "") if tc.function else "",
                        },
                    )

            if choice.finish_reason:
                yield StreamChunk(type="finish", finish_reason=choice.finish_reason)
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
        if self._base_url and "deepseek" in self._base_url:
            return "deepseek"
        return "openai"

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _estimate_cost(self, total_tokens: int) -> float:
        """基于 token 数量估算成本（USD）"""
        rate = _COST_PER_1K.get(self._model, 0.001)
        return round(total_tokens / 1000 * rate, 6)
