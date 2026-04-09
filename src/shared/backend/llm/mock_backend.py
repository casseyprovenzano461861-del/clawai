# -*- coding: utf-8 -*-
"""
Mock Backend — 测试与开发用

无需 API Key，立即可用。
返回可预测的模拟响应，适合单元测试和功能演示。
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from .base import ChatResponse, LLMBackend, StreamChunk, ToolCall


class MockBackend(LLMBackend):
    """Mock 后端：不调用任何外部服务，返回固定模拟响应"""

    def __init__(
        self,
        model: str = "mock-model",
        response_template: Optional[str] = None,
        stream_delay: float = 0.01,
    ):
        """
        Args:
            model:             模型名称标识
            response_template: 固定返回的响应文本（None 则根据输入智能生成）
            stream_delay:      流式输出每个字符的延迟秒数（模拟打字效果）
        """
        self._model = model
        self._response_template = response_template
        self._stream_delay = stream_delay

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
        content = self._generate_response(messages, tools)
        return ChatResponse(
            content=content,
            tool_calls=[],
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": len(content.split()), "total_tokens": 10 + len(content.split())},
            model=self._model,
            cost_usd=0.0,
        )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        content = self._generate_response(messages, tools)
        for char in content:
            yield StreamChunk(type="content", content=char)
            if self._stream_delay > 0:
                await asyncio.sleep(self._stream_delay)
        yield StreamChunk(type="finish", finish_reason="stop")

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def supports_function_calling(self) -> bool:
        return False

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "mock"

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
    ) -> str:
        if self._response_template:
            return self._response_template

        # 根据最后一条用户消息生成回复
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = str(msg.get("content", "")).lower()
                break

        if any(kw in last_user_msg for kw in ["扫描", "scan", "nmap"]):
            return "[Mock] 扫描任务已接收。正在对目标执行端口扫描，请稍候..."
        if any(kw in last_user_msg for kw in ["漏洞", "vuln", "exploit"]):
            return "[Mock] 检测到潜在漏洞。建议对 80/443 端口的 Web 服务进行深度测试。"
        if any(kw in last_user_msg for kw in ["报告", "report"]):
            return "[Mock] 渗透测试报告已生成。发现 2 个高危漏洞，3 个中危漏洞。"
        if any(kw in last_user_msg for kw in ["你好", "hi", "hello"]):
            return "[Mock] 你好！我是 ClawAI 的 Mock 助手（测试模式），当前未连接真实 LLM 服务。"

        return f"[Mock 模式] 已收到请求。当前未配置真实 LLM 提供商，请在 .env 中设置 API Key。"
