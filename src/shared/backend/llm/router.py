# -*- coding: utf-8 -*-
"""
ModelRouter — 多模型成本优化路由器

根据任务类型自动选择合适的 LLM（smart / cheap），在保证质量的前提下最小化 API 调用成本。

设计原则
--------
* **两档模型**：smart（高质量，贵）和 cheap（快速，便宜），通过环境变量或构造参数配置。
* **任务类型映射**：不同 PER 阶段对模型能力的要求差异明显：
    - PLANNING     → smart   （规划需要复杂推理，不省）
    - REFLECTION   → smart   （深度分析同上）
    - EXECUTION    → cheap   （执行策略相对简单）
    - TOOL_SELECT  → cheap   （工具选择，低复杂度）
    - CHAT         → cheap   （对话，优先响应速度）
* **可覆盖**：任何调用都可以显式指定 tier="smart"|"cheap" 强制使用某档。
* **成本追踪**：累计各档模型的 token 消耗和 USD 成本，通过 get_stats() 查询。
* **LLMBackend 子类**：实现标准 chat/stream_chat 接口，可直接传入 LLMIntegration。

快速使用
--------
    from src.shared.backend.llm.router import ModelRouter, TaskType
    from src.shared.backend.llm import create_backend

    router = ModelRouter(
        smart=create_backend("deepseek", model="deepseek-chat"),
        cheap=create_backend("deepseek", model="deepseek-chat"),   # 相同时退化为单模型
    )

    # 路由 chat 接口
    resp = await router.chat(messages, task_type=TaskType.EXECUTION)

    # 获取成本报告
    stats = router.get_stats()
    print(f"总成本: ${stats['total_cost_usd']:.6f}")

环境变量配置（由 create_router() 读取）
--------------------------------------
    ROUTER_SMART_PROVIDER=deepseek        # smart 模型提供商
    ROUTER_SMART_MODEL=deepseek-chat      # smart 模型名称
    ROUTER_CHEAP_PROVIDER=deepseek        # cheap 模型提供商（留空则复用 smart）
    ROUTER_CHEAP_MODEL=deepseek-chat      # cheap 模型名称（留空则复用 smart）
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from .base import ChatResponse, LLMBackend, StreamChunk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 任务类型 & 路由规则
# ---------------------------------------------------------------------------

class TaskType(Enum):
    """P-E-R 各阶段及通用对话的任务类型标签"""
    PLANNING = auto()       # 规划：将目标分解为子任务图（需要复杂推理）
    REFLECTION = auto()     # 反思：分析执行结果、提取规律（需要深度分析）
    EXECUTION = auto()      # 执行：生成具体工具调用策略（相对简单）
    TOOL_SELECT = auto()    # 工具选择：从候选列表中选最合适的工具（低复杂度）
    CHAT = auto()           # 普通对话：用户问答（优先速度/成本）


@dataclass
class RoutingRule:
    """某任务类型对应的路由参数"""
    tier: str           # "smart" | "cheap"
    temperature: float
    max_tokens: int
    description: str    # 便于日志/调试


# 默认路由表：可通过 ModelRouter(rules=...) 覆盖
DEFAULT_RULES: Dict[TaskType, RoutingRule] = {
    TaskType.PLANNING:    RoutingRule("smart", temperature=0.7, max_tokens=4096, description="规划-复杂推理"),
    TaskType.REFLECTION:  RoutingRule("smart", temperature=0.5, max_tokens=4096, description="反思-深度分析"),
    TaskType.EXECUTION:   RoutingRule("cheap", temperature=0.3, max_tokens=2048, description="执行-简单策略"),
    TaskType.TOOL_SELECT: RoutingRule("cheap", temperature=0.2, max_tokens=1024, description="工具选择-低复杂度"),
    TaskType.CHAT:        RoutingRule("cheap", temperature=0.7, max_tokens=2048, description="对话-速度优先"),
}


# ---------------------------------------------------------------------------
# 成本统计
# ---------------------------------------------------------------------------

@dataclass
class TierStats:
    """单档模型的调用统计"""
    calls: int = 0
    tokens_prompt: int = 0
    tokens_completion: int = 0
    cost_usd: float = 0.0

    @property
    def tokens_total(self) -> int:
        return self.tokens_prompt + self.tokens_completion

    def absorb(self, response: ChatResponse) -> None:
        """从一次 ChatResponse 中累积统计数据"""
        self.calls += 1
        usage = response.usage or {}
        self.tokens_prompt += usage.get("prompt_tokens", 0)
        self.tokens_completion += usage.get("completion_tokens", 0)
        self.cost_usd += response.cost_usd


# ---------------------------------------------------------------------------
# ModelRouter
# ---------------------------------------------------------------------------

class ModelRouter(LLMBackend):
    """多模型成本优化路由器

    继承 LLMBackend，可直接传入 LLMIntegration。

    Parameters
    ----------
    smart:
        高质量（贵）模型后端，用于 PLANNING / REFLECTION。
    cheap:
        快速（便宜）模型后端，用于 EXECUTION / TOOL_SELECT / CHAT。
        若不提供则退化为单模型模式（所有任务都用 smart）。
    rules:
        自定义路由表，不提供则使用 DEFAULT_RULES。
    """

    def __init__(
        self,
        smart: LLMBackend,
        cheap: Optional[LLMBackend] = None,
        rules: Optional[Dict[TaskType, RoutingRule]] = None,
    ) -> None:
        self._smart = smart
        self._cheap = cheap or smart          # 没有 cheap 则退化为单模型
        self._single_model = cheap is None
        self._rules: Dict[TaskType, RoutingRule] = rules or dict(DEFAULT_RULES)

        # 成本统计
        self._stats: Dict[str, TierStats] = {
            "smart": TierStats(),
            "cheap": TierStats(),
        }
        self._total_calls = 0

    # ------------------------------------------------------------------
    # 路由核心
    # ------------------------------------------------------------------

    def resolve(
        self,
        task_type: TaskType = TaskType.CHAT,
        tier: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple["LLMBackend", float, int, str]:
        """解析路由，返回 (backend, temperature, max_tokens, tier_name)

        Args:
            task_type:   任务类型标签（决定使用哪档模型及默认参数）
            tier:        显式强制指定档位 "smart"|"cheap"，优先于 task_type
            temperature: 若不为 None，覆盖路由表中的 temperature
            max_tokens:  若不为 None，覆盖路由表中的 max_tokens

        Returns:
            (backend, resolved_temperature, resolved_max_tokens, tier_name)
        """
        rule = self._rules.get(task_type, self._rules[TaskType.CHAT])

        # 强制指定 tier 时覆盖规则
        resolved_tier = tier if tier in ("smart", "cheap") else rule.tier

        backend = self._smart if resolved_tier == "smart" else self._cheap
        resolved_temp = temperature if temperature is not None else rule.temperature
        resolved_tokens = max_tokens if max_tokens is not None else rule.max_tokens

        logger.debug(
            f"ModelRouter.resolve: task={task_type.name} tier={resolved_tier} "
            f"model={backend.model_name} temp={resolved_temp} max_tokens={resolved_tokens}"
        )
        return backend, resolved_temp, resolved_tokens, resolved_tier

    # ------------------------------------------------------------------
    # LLMBackend 接口实现（支持 task_type 扩展参数）
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        *,
        task_type: TaskType = TaskType.CHAT,
        tier: Optional[str] = None,
    ) -> ChatResponse:
        """路由化非流式对话

        除标准参数外，额外接受：
            task_type: 任务类型，决定路由目标
            tier:      强制指定 "smart"|"cheap"（可选）

        注意：temperature/max_tokens 若不是调用方默认值（0.7/4096），
        则以调用方显式传入值为准；否则使用路由表默认值。
        """
        backend, resolved_temp, resolved_tokens, tier_name = self.resolve(
            task_type=task_type,
            tier=tier,
            # 只有调用方显式偏离默认值时才覆盖路由表
            temperature=temperature if temperature != 0.7 else None,
            max_tokens=max_tokens if max_tokens != 4096 else None,
        )

        self._total_calls += 1
        response = await backend.chat(
            messages,
            tools=tools,
            temperature=resolved_temp,
            max_tokens=resolved_tokens,
        )

        # 累积统计
        self._stats[tier_name].absorb(response)
        return response

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        *,
        task_type: TaskType = TaskType.CHAT,
        tier: Optional[str] = None,
    ) -> AsyncIterator[StreamChunk]:
        """路由化流式对话"""
        backend, resolved_temp, resolved_tokens, _ = self.resolve(
            task_type=task_type,
            tier=tier,
            temperature=temperature if temperature != 0.7 else None,
            max_tokens=max_tokens if max_tokens != 4096 else None,
        )
        self._total_calls += 1
        async for chunk in backend.stream_chat(
            messages,
            tools=tools,
            temperature=resolved_temp,
            max_tokens=resolved_tokens,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # LLMBackend 属性
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        if self._single_model:
            return self._smart.provider_name
        return f"router({self._smart.provider_name}/{self._cheap.provider_name})"

    @property
    def model_name(self) -> str:
        if self._single_model:
            return self._smart.model_name
        return f"smart={self._smart.model_name},cheap={self._cheap.model_name}"

    @property
    def supports_function_calling(self) -> bool:
        return self._smart.supports_function_calling

    # ------------------------------------------------------------------
    # 统计 & 报告
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """返回成本与调用统计"""
        s = self._stats["smart"]
        c = self._stats["cheap"]
        return {
            "total_calls": self._total_calls,
            "smart": {
                "calls": s.calls,
                "tokens_prompt": s.tokens_prompt,
                "tokens_completion": s.tokens_completion,
                "tokens_total": s.tokens_total,
                "cost_usd": round(s.cost_usd, 6),
                "model": self._smart.model_name,
            },
            "cheap": {
                "calls": c.calls,
                "tokens_prompt": c.tokens_prompt,
                "tokens_completion": c.tokens_completion,
                "tokens_total": c.tokens_total,
                "cost_usd": round(c.cost_usd, 6),
                "model": self._cheap.model_name,
            },
            "total_cost_usd": round(s.cost_usd + c.cost_usd, 6),
            "total_tokens": s.tokens_total + c.tokens_total,
            # 成本节省估算：若全用 smart 的花费 vs 实际花费
            "savings_estimate_usd": round(
                (s.cost_usd / s.calls * self._total_calls if s.calls else 0) - (s.cost_usd + c.cost_usd), 6
            ) if self._total_calls and not self._single_model else 0.0,
        }

    def cost_report(self) -> str:
        """返回人类可读的成本报告字符串"""
        stats = self.get_stats()
        lines = [
            "=== ModelRouter 成本报告 ===",
            f"总调用次数: {stats['total_calls']}",
            f"总Token消耗: {stats['total_tokens']:,}",
            f"总成本(USD): ${stats['total_cost_usd']:.6f}",
            "",
            f"[Smart - {stats['smart']['model']}]",
            f"  调用次数: {stats['smart']['calls']}",
            f"  Token:   {stats['smart']['tokens_total']:,}",
            f"  成本:    ${stats['smart']['cost_usd']:.6f}",
            "",
            f"[Cheap  - {stats['cheap']['model']}]",
            f"  调用次数: {stats['cheap']['calls']}",
            f"  Token:   {stats['cheap']['tokens_total']:,}",
            f"  成本:    ${stats['cheap']['cost_usd']:.6f}",
        ]
        if not self._single_model:
            lines.append(f"\n预计节省(USD): ${stats['savings_estimate_usd']:.6f}")
        return "\n".join(lines)
