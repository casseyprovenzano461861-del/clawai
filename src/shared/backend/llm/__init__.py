# -*- coding: utf-8 -*-
"""
LLMBackend 抽象层

统一的 LLM 调用接口，支持多提供商可插拔切换。

快速使用：
    from src.shared.backend.llm import create_backend

    # 从环境变量自动选择提供商
    backend = create_backend()

    # 显式指定提供商
    backend = create_backend("openai", api_key="sk-...", model="gpt-4o")
    backend = create_backend("deepseek", api_key="sk-...", model="deepseek-chat")
    backend = create_backend("anthropic", api_key="sk-ant-...", model="claude-3-5-sonnet-20241022")
    backend = create_backend("ollama", model="llama3.2")
    backend = create_backend("mock")

    # 非流式对话
    resp = await backend.chat([{"role": "user", "content": "hello"}])
    print(resp.content)

    # 流式对话
    async for chunk in await backend.stream_chat(messages):
        if chunk.type == "content":
            print(chunk.content, end="", flush=True)
"""

import logging
import os
from typing import Optional

from .base import ChatResponse, LLMBackend, StreamChunk, ToolCall
from .router import ModelRouter, TaskType, RoutingRule, DEFAULT_RULES

__all__ = [
    "LLMBackend",
    "ChatResponse",
    "ToolCall",
    "StreamChunk",
    "ModelRouter",
    "TaskType",
    "RoutingRule",
    "DEFAULT_RULES",
    "create_backend",
    "create_router",
]

logger = logging.getLogger(__name__)


def create_backend(
    provider: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs,
) -> LLMBackend:
    """创建 LLMBackend 实例

    优先级：
    1. 显式传入的 provider 参数
    2. 环境变量 LLM_PROVIDER
    3. 根据可用 API Key 自动推断
    4. 回退到 mock 模式

    Args:
        provider:  提供商名称：openai | deepseek | anthropic | ollama | mock
        api_key:   API 密钥（留空则从环境变量读取）
        model:     模型名称（留空则使用各提供商默认值）
        base_url:  覆盖默认 API 地址
        **kwargs:  其他传给 Backend 构造函数的参数

    Returns:
        LLMBackend 实例
    """
    # 1. 确定 provider
    resolved_provider = (
        provider
        or os.getenv("LLM_PROVIDER", "")
        or _infer_provider()
    ).lower().strip()

    if not resolved_provider:
        resolved_provider = "mock"

    logger.info(f"create_backend: provider={resolved_provider}")

    # 2. 按 provider 实例化
    if resolved_provider in ("openai", "deepseek"):
        return _create_openai_backend(resolved_provider, api_key, model, base_url, **kwargs)

    if resolved_provider == "anthropic":
        return _create_anthropic_backend(api_key, model, base_url, **kwargs)

    if resolved_provider == "ollama":
        return _create_ollama_backend(model, base_url, **kwargs)

    if resolved_provider == "mock":
        from .mock_backend import MockBackend
        return MockBackend(model=model or "mock-model", **kwargs)

    logger.warning(f"未知 provider '{resolved_provider}'，回退到 Mock 模式")
    from .mock_backend import MockBackend
    return MockBackend()


# ---------------------------------------------------------------------------
# 内部工厂辅助
# ---------------------------------------------------------------------------

def _infer_provider() -> str:
    """根据环境变量中的 API Key 推断提供商"""
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    # Ollama 无需 Key，但不默认选择（需显式指定）
    return ""


def _create_openai_backend(
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    **kwargs,
) -> LLMBackend:
    from .openai_backend import OpenAIBackend

    _api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or ""
    if not _api_key:
        logger.warning(f"未找到 {provider.upper()} API Key，回退到 Mock 模式")
        from .mock_backend import MockBackend
        return MockBackend()

    _base_url = base_url or os.getenv("LLM_BASE_URL") or (
        "https://api.deepseek.com/v1" if provider == "deepseek" else None
    )
    _model = model or os.getenv("LLM_MODEL") or (
        "deepseek-chat" if provider == "deepseek" else "gpt-4o-mini"
    )

    return OpenAIBackend(api_key=_api_key, model=_model, base_url=_base_url, **kwargs)


def _create_anthropic_backend(
    api_key: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    **kwargs,
) -> LLMBackend:
    from .anthropic_backend import AnthropicBackend

    _api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or ""
    if not _api_key:
        logger.warning("未找到 ANTHROPIC_API_KEY，回退到 Mock 模式")
        from .mock_backend import MockBackend
        return MockBackend()

    _model = model or os.getenv("LLM_MODEL") or "claude-3-5-sonnet-20241022"
    return AnthropicBackend(api_key=_api_key, model=_model, base_url=base_url, **kwargs)


def _create_ollama_backend(
    model: Optional[str],
    base_url: Optional[str],
    **kwargs,
) -> LLMBackend:
    from .ollama_backend import OllamaBackend

    _model = model or os.getenv("LLM_MODEL") or "llama3.2"
    _base_url = base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
    return OllamaBackend(model=_model, base_url=_base_url, **kwargs)


# ---------------------------------------------------------------------------
# 快速自测
# ---------------------------------------------------------------------------


def create_router(
    smart_provider: Optional[str] = None,
    smart_model: Optional[str] = None,
    cheap_provider: Optional[str] = None,
    cheap_model: Optional[str] = None,
) -> "ModelRouter":
    """创建 ModelRouter 实例（从参数或环境变量读取配置）

    环境变量（优先级低于函数参数）：
        ROUTER_SMART_PROVIDER   smart 模型提供商（默认与主 LLM_PROVIDER 相同）
        ROUTER_SMART_MODEL      smart 模型名称
        ROUTER_CHEAP_PROVIDER   cheap 模型提供商（默认与 smart 相同）
        ROUTER_CHEAP_MODEL      cheap 模型名称（留空 → 退化为单模型模式）

    Args:
        smart_provider: smart 档模型提供商，留空则读 ROUTER_SMART_PROVIDER / LLM_PROVIDER
        smart_model:    smart 档模型名称，留空则读 ROUTER_SMART_MODEL / LLM_MODEL
        cheap_provider: cheap 档模型提供商，留空则读 ROUTER_CHEAP_PROVIDER
        cheap_model:    cheap 档模型名称，留空则读 ROUTER_CHEAP_MODEL

    Returns:
        ModelRouter 实例
    """
    import os

    # --- smart 档 ---
    _smart_provider = (
        smart_provider
        or os.getenv("ROUTER_SMART_PROVIDER")
        or os.getenv("LLM_PROVIDER")
        or _infer_provider()
        or "mock"
    )
    _smart_model = smart_model or os.getenv("ROUTER_SMART_MODEL") or os.getenv("LLM_MODEL")

    smart_backend = create_backend(_smart_provider, model=_smart_model)
    logger.info(f"create_router: smart={_smart_provider}/{smart_backend.model_name}")

    # --- cheap 档 ---
    _cheap_provider = cheap_provider or os.getenv("ROUTER_CHEAP_PROVIDER")
    _cheap_model = cheap_model or os.getenv("ROUTER_CHEAP_MODEL")

    if not _cheap_provider and not _cheap_model:
        # 未配置 cheap，退化为单模型
        logger.info("create_router: cheap 未配置，退化为单模型模式")
        return ModelRouter(smart=smart_backend, cheap=None)

    _cheap_provider = _cheap_provider or _smart_provider
    cheap_backend = create_backend(_cheap_provider, model=_cheap_model)
    logger.info(f"create_router: cheap={_cheap_provider}/{cheap_backend.model_name}")

    return ModelRouter(smart=smart_backend, cheap=cheap_backend)


# ---------------------------------------------------------------------------
# 快速自测
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def _test():
        print("=== LLMBackend 自测 ===")
        backend = create_backend("mock")
        print(f"Provider: {backend.provider_name}, Model: {backend.model_name}")

        # 非流式
        resp = await backend.chat([{"role": "user", "content": "你好"}])
        print(f"[非流式] {resp.content}")

        # 流式
        print("[流式] ", end="")
        async for chunk in backend.stream_chat([{"role": "user", "content": "扫描目标"}]):
            if chunk.type == "content":
                print(chunk.content, end="", flush=True)
            elif chunk.type == "finish":
                print(f" [done: {chunk.finish_reason}]")
        print("=== 自测完成 ===")

    asyncio.run(_test())
