# -*- coding: utf-8 -*-
"""
聊天 API
供前端作战室 AI 对话使用，支持项目上下文注入 + 流式输出（SSE）
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["AI对话"])


# ── Pydantic Schemas ─────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str     # user | assistant
    content: str


class ChatMessageRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    project_id: Optional[str] = None
    history: List[HistoryMessage] = []
    stream: bool = True   # 默认流式


# ── LLM 客户端 ───────────────────────────────────────────────────

def _build_messages(body: ChatMessageRequest) -> List[Dict]:
    system = body.system_prompt or (
        "你是一个专业的渗透测试 AI 助手，擅长漏洞分析、攻击路径规划、安全建议。"
        "请用中文回答，回答简洁专业，善用 Markdown 格式。"
    )
    messages = [{"role": "system", "content": system}]
    for h in body.history[-8:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": body.message})
    return messages


def _get_openai_client():
    """直接构造 openai.AsyncOpenAI 用于流式调用"""
    try:
        from openai import AsyncOpenAI
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        if not api_key:
            return None, None
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        return client, model
    except Exception as e:
        logger.warning(f"AsyncOpenAI 初始化失败: {e}")
        return None, None


def _get_sync_llm():
    """同步 LLMClient，用于降级非流式"""
    try:
        from backend.ai_agent.core import LLMClient, LLMConfig, LLMProvider
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "mock"
        base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        provider_str = os.getenv("LLM_PROVIDER", "deepseek").lower()
        provider_map = {
            "deepseek": LLMProvider.DEEPSEEK,
            "openai": LLMProvider.OPENAI,
            "mock": LLMProvider.MOCK,
        }
        provider = provider_map.get(provider_str, LLMProvider.DEEPSEEK)
        if api_key == "mock":
            provider = LLMProvider.MOCK
        config = LLMConfig(provider=provider, model=model, api_key=api_key,
                           base_url=base_url, temperature=0.7, max_tokens=2048)
        return LLMClient(config)
    except Exception as e:
        logger.warning(f"sync LLMClient 失败: {e}")
        return None


# ── SSE 生成器 ───────────────────────────────────────────────────

def _sse(data: str) -> str:
    """格式化单条 SSE 消息"""
    return f"data: {json.dumps({'text': data}, ensure_ascii=False)}\n\n"

def _sse_done() -> str:
    return "data: [DONE]\n\n"

def _sse_error(msg: str) -> str:
    return f"data: {json.dumps({'error': msg}, ensure_ascii=False)}\n\n"


async def _stream_openai(client, model: str, messages: List[Dict]) -> AsyncGenerator[str, None]:
    """使用 AsyncOpenAI 流式调用"""
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield _sse(delta.content)
        yield _sse_done()
    except Exception as e:
        logger.error(f"流式调用失败: {e}")
        yield _sse_error(str(e))
        # 降级：规则回复
        rule = _rule_reply(messages[-1].get("content", ""))
        for ch in rule:
            yield _sse(ch)
        yield _sse_done()


async def _stream_rule(message: str) -> AsyncGenerator[str, None]:
    """规则回复，逐字符模拟流式"""
    import asyncio
    reply = _rule_reply(message)
    # 按词（4字）分块，模拟打字效果
    chunk_size = 4
    for i in range(0, len(reply), chunk_size):
        yield _sse(reply[i:i+chunk_size])
        await asyncio.sleep(0.02)
    yield _sse_done()


# ── 端点 ────────────────────────────────────────────────────────

@router.post("/message", summary="发送聊天消息（支持流式）")
async def send_message(body: ChatMessageRequest):
    """
    接收用户消息，返回 AI 回复。
    stream=true（默认）时返回 SSE 流；stream=false 时返回 JSON。
    """
    messages = _build_messages(body)

    if not body.stream:
        # ── 非流式（兼容旧调用）────────────────────────────────
        sync_client = _get_sync_llm()
        if sync_client:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, lambda: sync_client.chat(messages))
                reply = resp.content or "（AI 未返回内容）"
            except Exception as e:
                logger.error(f"非流式 LLM 失败: {e}")
                reply = _rule_reply(body.message)
        else:
            reply = _rule_reply(body.message)
        return {"response": reply, "project_id": body.project_id,
                "timestamp": datetime.utcnow().isoformat() + "Z"}

    # ── 流式 SSE ─────────────────────────────────────────────────
    async_client, model = _get_openai_client()

    if async_client:
        gen = _stream_openai(async_client, model, messages)
    else:
        gen = _stream_rule(body.message)

    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _rule_reply(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ["漏洞", "vuln", "cve"]):
        return "根据项目上下文，建议优先修复 Critical 和 High 级别漏洞。可使用【发起扫描】页面运行 Nuclei 进行漏洞验证。"
    if any(k in msg for k in ["路径", "攻击", "attack"]):
        return "建议攻击路径：信息收集（Nmap）→ 目录枚举（DirSearch）→ 漏洞扫描（Nuclei/SQLMap）→ 后渗透（Metasploit）。"
    if any(k in msg for k in ["sql", "注入", "inject"]):
        return "SQL 注入测试建议：使用 SQLMap 自动检测，payload 可尝试 `' OR 1=1--`、时间盲注 `sleep(5)` 等。"
    if any(k in msg for k in ["扫描", "scan", "nmap"]):
        return "建议先用 Nmap 进行端口扫描：`nmap -sV -sC <target>`，然后根据开放服务选择对应的漏洞扫描工具。"
    if any(k in msg for k in ["报告", "report"]):
        return "可以点击底部【一键生成】按钮导出该项目的渗透测试报告，支持 Markdown 和 HTML 格式。"
    return "我已收到你的消息。请确保后端 LLM 配置（DEEPSEEK_API_KEY）已在 .env 中设置，以获得完整的 AI 回复能力。"
