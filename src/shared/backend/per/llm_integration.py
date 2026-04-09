# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：LLM集成桥接模块

支持两种后端：
1. 新版 LLMBackend（src/shared/backend/llm/）— 推荐，支持多提供商
2. 旧版 LLMClient（ai_agent/core.py）— 向下兼容

使用新版：
    from src.shared.backend.llm import create_backend
    backend = create_backend("deepseek")
    integration = LLMIntegration(backend)

使用旧版（向下兼容）：
    from src.shared.backend.ai_agent.core import LLMClient, LLMConfig
    client = LLMClient(LLMConfig(...))
    integration = LLMIntegration(client)
"""

import json
import logging
import asyncio
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

# TaskType 供调用方使用（从这里 re-export，避免多层导入）
try:
    from src.shared.backend.llm.router import TaskType
except ImportError:
    TaskType = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 调用响应的统一封装"""
    success: bool
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    model: str = ""
    cost_usd: float = 0.0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class _LegacyClientAdapter:
    """将旧版 LLMClient 适配为新版 LLMBackend 接口（内部使用）"""

    def __init__(self, legacy_client):
        self._client = legacy_client

    async def chat(self, messages, tools=None, temperature=0.7, max_tokens=4096):
        """将新版异步接口转为旧版同步调用"""
        from src.shared.backend.llm.base import ChatResponse, ToolCall

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.chat(messages, tools=tools, temperature=temperature, max_tokens=max_tokens),
        )

        tool_calls = []
        for tc in getattr(response, "tool_calls", []):
            tool_calls.append(
                ToolCall(
                    id=getattr(tc, "id", ""),
                    name=getattr(tc, "name", ""),
                    arguments=getattr(tc, "arguments", {}),
                )
            )

        return ChatResponse(
            content=getattr(response, "content", "") or "",
            tool_calls=tool_calls,
            finish_reason=getattr(response, "finish_reason", "stop"),
            usage=getattr(response, "usage", {}) or {},
            model=getattr(response, "model", ""),
        )

    @property
    def provider_name(self):
        return "legacy"

    @property
    def model_name(self):
        config = getattr(self._client, "config", None)
        return getattr(config, "model", "") if config else ""


class LLMIntegration:
    """LLM 集成层

    将 LLMBackend（新版）或 LLMClient（旧版）封装为 PER 模块的统一调用接口，提供：
    - 异步调用 call_llm_async()
    - 同步调用 call_llm()（在事件循环中运行异步版本）
    - JSON 解析 parse_json_response()
    - 调用统计 get_stats()
    """

    def __init__(self, backend_or_client):
        """
        Args:
            backend_or_client: LLMBackend 实例（新版）或 LLMClient 实例（旧版，自动适配）
        """
        # 检测是否为新版 LLMBackend
        try:
            from src.shared.backend.llm.base import LLMBackend
            if isinstance(backend_or_client, LLMBackend):
                self._backend = backend_or_client
                self.llm_client = None  # 保持向下兼容属性
                logger.info(f"LLMIntegration: 使用新版 LLMBackend ({backend_or_client.provider_name}/{backend_or_client.model_name})")
            else:
                # 旧版 LLMClient，包装为适配器
                self._backend = _LegacyClientAdapter(backend_or_client)
                self.llm_client = backend_or_client
                logger.info("LLMIntegration: 使用旧版 LLMClient（兼容模式）")
        except ImportError:
            # llm 模块未就绪，直接用旧版
            self._backend = _LegacyClientAdapter(backend_or_client)
            self.llm_client = backend_or_client

        # 调用统计
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
        }

    # ------------------------------------------------------------------
    # 异步调用（主接口，使用新版 LLMBackend）
    # ------------------------------------------------------------------

    async def call_llm_async(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        task_type=None,  # TaskType | None
    ) -> LLMResponse:
        """异步调用 LLM

        Args:
            messages:   OpenAI 格式消息列表
            tools:      OpenAI Function Calling 工具定义（可选）
            temperature: 采样温度
            max_tokens:  最大生成 token 数
            task_type:   任务类型标签（TaskType 枚举），供 ModelRouter 路由使用

        Returns:
            LLMResponse
        """
        self._stats["total_calls"] += 1

        try:
            # 若底层是 ModelRouter，马上传入 task_type
            try:
                from src.shared.backend.llm.router import ModelRouter
                if isinstance(self._backend, ModelRouter) and task_type is not None:
                    response = await self._backend.chat(
                        messages,
                        tools=tools,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        task_type=task_type,
                    )
                else:
                    response = await self._backend.chat(
                        messages,
                        tools=tools,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
            except ImportError:
                response = await self._backend.chat(
                    messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            tool_calls_raw = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                for tc in getattr(response, "tool_calls", [])
            ]

            usage = getattr(response, "usage", {}) or {}
            self._stats["total_tokens"] += usage.get("total_tokens", 0)
            self._stats["successful_calls"] += 1

            return LLMResponse(
                success=True,
                content=getattr(response, "content", "") or "",
                tool_calls=tool_calls_raw,
                usage=usage,
                model=getattr(response, "model", ""),
                cost_usd=getattr(response, "cost_usd", 0.0),
            )

        except Exception as e:
            self._stats["failed_calls"] += 1
            logger.error(f"LLM 调用失败: {e}")
            return LLMResponse(
                success=False,
                content="",
                error=str(e),
            )

    # ------------------------------------------------------------------
    # 同步调用（向下兼容，内部运行异步版本）
    # ------------------------------------------------------------------

    def call_llm(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        task_type=None,  # TaskType | None
    ) -> LLMResponse:
        """同步调用 LLM（向下兼容接口，优先使用 call_llm_async）"""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.call_llm_async(messages, tools=tools, temperature=temperature, max_tokens=max_tokens, task_type=task_type),
                )
                return future.result()
        except RuntimeError:
            return asyncio.run(
                self.call_llm_async(messages, tools=tools, temperature=temperature, max_tokens=max_tokens, task_type=task_type)
            )

    # ------------------------------------------------------------------
    # JSON 解析
    # ------------------------------------------------------------------

    def parse_json_response(self, content: str) -> Any:
        """从 LLM 响应文本中解析 JSON

        尝试多种策略：
        1. 直接解析
        2. 提取 ```json ... ``` 代码块
        3. 使用正则找到第一个 JSON 对象/数组

        Returns:
            解析出的 Python 对象，失败时返回 {"parse_error": "...", "raw": content}
        """
        if not content:
            return {"parse_error": "空响应", "raw": ""}

        # 策略1: 直接解析
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # 策略2: 提取 ```json ... ``` 代码块
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 策略3: 找第一个 JSON 数组或对象
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = content.find(start_char)
            if start == -1:
                continue
            # 从 start 向后找平衡括号
            depth = 0
            for i in range(start, len(content)):
                if content[i] == start_char:
                    depth += 1
                elif content[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        candidate = content[start: i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        logger.warning(f"无法解析 LLM 响应为 JSON，前200字符: {content[:200]}")
        return {"parse_error": "无法解析 JSON", "raw": content[:500]}

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """返回调用统计"""
        total = self._stats["total_calls"]
        success = self._stats["successful_calls"]
        base = {
            "total_calls": total,
            "successful_calls": success,
            "failed_calls": self._stats["failed_calls"],
            "success_rate": success / total if total > 0 else 0.0,
            "total_tokens": self._stats["total_tokens"],
        }
        # 如果底层是 ModelRouter，附加路由器的成本统计
        try:
            from src.shared.backend.llm.router import ModelRouter
            if isinstance(self._backend, ModelRouter):
                base["router"] = self._backend.get_stats()
        except ImportError:
            pass
        return base


# ------------------------------------------------------------------
# 工厂函数
# ------------------------------------------------------------------

def create_llm_integration(backend_or_client=None) -> LLMIntegration:
    """创建 LLMIntegration 实例

    优先使用新版 LLMBackend；若未提供则从环境变量自动构建。
    也兼容传入旧版 LLMClient。

    Args:
        backend_or_client: LLMBackend（推荐）或旧版 LLMClient；
                           若为 None 则从环境变量自动构建

    Returns:
        LLMIntegration
    """
    if backend_or_client is not None:
        return LLMIntegration(backend_or_client)

    # 优先尝试新版 LLMBackend
    try:
        from src.shared.backend.llm import create_router
        router = create_router()   # 从环境变量自动配置
        logger.info(f"自动构建 ModelRouter: {router.provider_name}")
        return LLMIntegration(router)
    except Exception as e:
        logger.debug(f"ModelRouter 构建失败，回退到单模型: {e}")

    try:
        from src.shared.backend.llm import create_backend
        backend = create_backend()  # 从环境变量自动选择 provider
        logger.info(f"自动构建 LLMBackend: {backend.provider_name}/{backend.model_name}")
        return LLMIntegration(backend)
    except Exception as e:
        logger.warning(f"新版 LLMBackend 构建失败，回退到旧版: {e}")

    # 回退：尝试旧版 LLMClient
    try:
        import os
        from src.shared.backend.ai_agent.core import LLMClient, LLMConfig, LLMProvider

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or ""
        base_url = os.getenv("LLM_BASE_URL", "")
        model = os.getenv("LLM_MODEL", "deepseek-chat")

        if not api_key:
            config = LLMConfig(provider=LLMProvider.MOCK)
            logger.warning("未找到 API Key，使用 Mock LLM 模式")
        else:
            config = LLMConfig(
                provider=LLMProvider.OPENAI if "openai" in base_url.lower() else LLMProvider.DEEPSEEK,
                model=model,
                api_key=api_key,
                base_url=base_url,
            )

        client = LLMClient(config)
        logger.info(f"回退构建旧版 LLMClient: {config.provider.value}/{config.model}")
        return LLMIntegration(client)

    except Exception as e:
        logger.error(f"LLMIntegration 构建失败，使用 Mock 模式: {e}")
        from src.shared.backend.llm.mock_backend import MockBackend
        return LLMIntegration(MockBackend())
