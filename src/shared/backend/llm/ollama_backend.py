# -*- coding: utf-8 -*-
"""
Ollama 本地模型 Backend

调用本地运行的 Ollama REST API，不依赖任何第三方 LLM SDK。
默认地址：http://localhost:11434

支持的模型示例：
- llama3.2, llama3.1
- mistral, mistral-nemo
- deepseek-r1, deepseek-coder
- gemma2, phi3

使用前请确保 Ollama 已启动：
    ollama serve
    ollama pull <model_name>
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from .base import ChatResponse, LLMBackend, StreamChunk, ToolCall

logger = logging.getLogger(__name__)


class OllamaBackend(LLMBackend):
    """Ollama 本地模型后端（纯 HTTP，不依赖额外 SDK）"""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        """
        Args:
            model:    Ollama 模型名称（需已 pull）
            base_url: Ollama 服务地址
            timeout:  请求超时秒数（本地模型较慢，默认 120s）
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

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
        try:
            import aiohttp
        except ImportError:
            # 回退到同步请求
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._sync_chat(messages, tools, temperature, max_tokens),
            )

        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=False)

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            ) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Ollama 返回错误 {resp.status}: {text}")
                        return ChatResponse(
                            content=f"[Ollama 错误 {resp.status}] {text}",
                            finish_reason="error",
                        )
                    data = await resp.json()
                    return self._parse_response(data)

        except Exception as e:
            logger.error(f"OllamaBackend.chat 失败: {e}")
            return ChatResponse(content=f"[Ollama 调用失败] {e}", finish_reason="error")

    def _sync_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
    ) -> ChatResponse:
        import urllib.request

        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=False)

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return self._parse_response(data)
        except Exception as e:
            logger.error(f"OllamaBackend._sync_chat 失败: {e}")
            return ChatResponse(content=f"[Ollama 调用失败] {e}", finish_reason="error")

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        try:
            import aiohttp
            async for chunk in self._aiohttp_stream(messages, tools, temperature, max_tokens):
                yield chunk
        except ImportError:
            # 回退：用非流式输出模拟
            resp = await self.chat(messages, tools, temperature, max_tokens)
            for char in resp.content:
                yield StreamChunk(type="content", content=char)
                await asyncio.sleep(0)
            yield StreamChunk(type="finish", finish_reason=resp.finish_reason)

    async def _aiohttp_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[StreamChunk]:
        import aiohttp

        url = f"{self._base_url}/api/chat"
        payload = self._build_payload(messages, tools, temperature, max_tokens, stream=True)

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            ) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        yield StreamChunk(type="error", error=f"Ollama 错误 {resp.status}: {text}")
                        return

                    async for line in resp.content:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line.decode("utf-8"))
                        except json.JSONDecodeError:
                            continue

                        msg = data.get("message", {})
                        content = msg.get("content", "")
                        if content:
                            yield StreamChunk(type="content", content=content)

                        if data.get("done"):
                            yield StreamChunk(type="finish", finish_reason="stop")
                            break

        except Exception as e:
            yield StreamChunk(type="error", error=str(e))

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        # Ollama 从 0.2+ 支持 tools（需模型支持）
        if tools:
            payload["tools"] = tools
        return payload

    def _parse_response(self, data: Dict[str, Any]) -> ChatResponse:
        msg = data.get("message", {})
        content = msg.get("content", "")
        finish_reason = "stop" if data.get("done") else "length"

        # 解析工具调用（Ollama >= 0.2 格式）
        tool_calls: List[ToolCall] = []
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            arguments = fn.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"call_{len(tool_calls)}"),
                    name=fn.get("name", ""),
                    arguments=arguments,
                )
            )

        usage = {}
        if "prompt_eval_count" in data:
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            }

        return ChatResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            model=self._model,
            cost_usd=0.0,  # 本地模型无成本
        )

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def supports_function_calling(self) -> bool:
        # 取决于模型是否支持，保守返回 True 由调用方决定
        return True

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "ollama"
