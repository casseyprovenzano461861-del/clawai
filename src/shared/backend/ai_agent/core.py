# -*- coding: utf-8 -*-
"""
AI Agent 核心模块
提供 AI 驱动的对话和工具调用能力
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .risk_assessor import RiskAssessor, RiskLevel, RiskAssessment
from .tools.schemas import TOOL_SCHEMAS, get_tool_schema

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM 提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider = LLMProvider.DEEPSEEK
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def to_openai_config(self) -> Dict[str, Any]:
        """转换为 OpenAI 客户端配置"""
        config = {
            "api_key": self.api_key,
        }
        if self.base_url:
            config["base_url"] = self.base_url
        elif self.provider == LLMProvider.DEEPSEEK:
            config["base_url"] = "https://api.deepseek.com/v1"
        return config


@dataclass
class ToolCall:
    """工具调用"""
    id: str                           # 调用ID
    name: str                         # 工具名称
    arguments: Dict[str, Any]         # 参数
    status: str = "pending"           # pending/executing/completed/failed
    result: Optional[Dict[str, Any]] = None  # 执行结果
    error: Optional[str] = None       # 错误信息
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI 格式"""
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False)
            }
        }
    
    @classmethod
    def from_openai_format(cls, data: Dict[str, Any]) -> "ToolCall":
        """从 OpenAI 格式创建"""
        function = data.get("function", {})
        arguments_str = function.get("arguments", "{}")
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}
        
        return cls(
            id=data.get("id", ""),
            name=function.get("name", ""),
            arguments=arguments,
            status="pending"
        )


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str                              # 文本内容
    tool_calls: List[ToolCall] = field(default_factory=list)  # 工具调用
    finish_reason: str = "stop"               # 结束原因
    usage: Dict[str, int] = field(default_factory=dict)       # Token 使用量
    model: str = ""                           # 使用的模型
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "tool_calls": [tc.to_openai_format() for tc in self.tool_calls],
            "finish_reason": self.finish_reason,
            "usage": self.usage,
            "model": self.model
        }


class LLMClient:
    """LLM 客户端封装"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        if self.config.provider == LLMProvider.MOCK:
            # Mock 模式，不需要实际客户端
            self.client = None
            logger.info("LLM 客户端: Mock 模式")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(**self.config.to_openai_config())
            logger.info(f"LLM 客户端初始化成功: {self.config.provider.value}")
        except ImportError:
            logger.warning("openai 包未安装，使用 Mock 模式")
            self.config.provider = LLMProvider.MOCK
        except Exception as e:
            logger.error(f"LLM 客户端初始化失败: {e}")
            self.config.provider = LLMProvider.MOCK
    
    def chat(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> ChatResponse:
        """同步聊天
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Returns:
            ChatResponse: 聊天响应
        """
        if self.config.provider == LLMProvider.MOCK:
            return self._mock_chat(messages, tools)
        
        try:
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            params.update(kwargs)
            
            response = self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            
            # 解析工具调用
            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append(ToolCall.from_openai_format({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }))
            
            return ChatResponse(
                content=choice.message.content or "",
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                model=response.model
            )
            
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return ChatResponse(
                content=f"抱歉，AI 服务暂时不可用: {str(e)}",
                finish_reason="error"
            )
    
    async def chat_stream(
        self, 
        messages: List[Dict], 
        tools: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 流式响应块
        """
        if self.config.provider == LLMProvider.MOCK:
            async for chunk in self._mock_chat_stream(messages, tools):
                yield chunk
            return
        
        try:
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            
            params.update(kwargs)
            
            stream = self.client.chat.completions.create(**params)
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # 内容块
                if delta.content:
                    yield {
                        "type": "content",
                        "content": delta.content,
                        "delta": True
                    }
                
                # 工具调用块
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        yield {
                            "type": "tool_call",
                            "tool_calls": [{
                                "id": tc.id if tc.id else "",
                                "index": tc.index if tc.index is not None else 0,
                                "function": {
                                    "name": tc.function.name if tc.function else "",
                                    "arguments": tc.function.arguments if tc.function else ""
                                }
                            }],
                            "delta": True
                        }
                
                # 结束
                if chunk.choices[0].finish_reason:
                    yield {
                        "type": "finish",
                        "finish_reason": chunk.choices[0].finish_reason
                    }
                    
        except Exception as e:
            logger.error(f"流式调用失败: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def _mock_chat(self, messages: List[Dict], tools: List[Dict]) -> ChatResponse:
        """Mock 模式聊天"""
        last_message = messages[-1] if messages else {}
        user_content = last_message.get("content", "")
        
        # 简单的意图识别
        if "扫描" in user_content or "scan" in user_content.lower():
            return ChatResponse(
                content="好的，我来帮您进行扫描。不过当前是模拟模式，无法实际执行扫描操作。",
                tool_calls=[],
                finish_reason="stop"
            )
        
        return ChatResponse(
            content=f"[模拟模式] 收到您的消息。当前 LLM 服务未配置，请设置 API Key。",
            finish_reason="stop"
        )
    
    async def _mock_chat_stream(
        self, 
        messages: List[Dict], 
        tools: List[Dict]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Mock 模式流式聊天"""
        response = self._mock_chat(messages, tools)
        
        # 模拟流式输出
        for char in response.content:
            yield {
                "type": "content",
                "content": char,
                "delta": True
            }
            await asyncio.sleep(0.02)  # 模拟打字效果
        
        yield {
            "type": "finish",
            "finish_reason": "stop"
        }


class AIAgentCore:
    """AI Agent 核心
    
    负责：
    1. LLM 客户端管理
    2. 对话生成
    3. 工具调用解析和执行
    4. 风险评估
    5. 流式响应处理
    """
    
    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tool_executor: Optional[Callable] = None,
        risk_assessor: Optional[RiskAssessor] = None,
        system_prompt: str = "",
        strict_mode: bool = False
    ):
        """初始化 AI Agent 核心
        
        Args:
            llm_config: LLM 配置
            tool_executor: 工具执行器回调函数
            risk_assessor: 风险评估器
            system_prompt: 系统提示词
            strict_mode: 严格模式
        """
        self.llm_config = llm_config or LLMConfig()
        self.llm_client = LLMClient(self.llm_config)
        self.tool_executor = tool_executor
        self.risk_assessor = risk_assessor or RiskAssessor(strict_mode=strict_mode)
        self.system_prompt = system_prompt
        self.strict_mode = strict_mode
        
        # 工具调用回调
        self._on_tool_call_start: Optional[Callable] = None
        self._on_tool_call_end: Optional[Callable] = None
        self._on_confirmation_required: Optional[Callable] = None
        
        logger.info(f"AIAgentCore 初始化完成，模型: {self.llm_config.model}")
    
    # ==================== 回调设置 ====================
    
    def set_callbacks(
        self,
        on_tool_call_start: Callable = None,
        on_tool_call_end: Callable = None,
        on_confirmation_required: Callable = None
    ):
        """设置回调函数
        
        Args:
            on_tool_call_start: 工具调用开始回调
            on_tool_call_end: 工具调用结束回调
            on_confirmation_required: 需要确认回调
        """
        self._on_tool_call_start = on_tool_call_start
        self._on_tool_call_end = on_tool_call_end
        self._on_confirmation_required = on_confirmation_required
    
    # ==================== 核心方法 ====================
    
    def chat(
        self, 
        messages: List[Dict], 
        tools: List[Dict] = None,
        **kwargs
    ) -> ChatResponse:
        """同步聊天
        
        Args:
            messages: 消息列表
            tools: 可用工具列表
            **kwargs: 其他参数
            
        Returns:
            ChatResponse: 聊天响应
        """
        # 添加系统提示词
        if self.system_prompt:
            messages = self._add_system_prompt(messages)
        
        return self.llm_client.chat(messages, tools or TOOL_SCHEMAS, **kwargs)
    
    async def chat_stream(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天
        
        Args:
            messages: 消息列表
            tools: 可用工具列表
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 流式响应块
        """
        # 添加系统提示词
        if self.system_prompt:
            messages = self._add_system_prompt(messages)
        
        async for chunk in self.llm_client.chat_stream(messages, tools or TOOL_SCHEMAS, **kwargs):
            yield chunk
    
    async def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        auto_execute: bool = True,
        max_tool_calls: int = 5
    ) -> ChatResponse:
        """带工具调用的聊天
        
        Args:
            messages: 消息列表
            tools: 可用工具列表
            auto_execute: 是否自动执行工具
            max_tool_calls: 最大工具调用次数
            
        Returns:
            ChatResponse: 最终响应
        """
        tools = tools or TOOL_SCHEMAS
        tool_call_count = 0
        
        while tool_call_count < max_tool_calls:
            # 调用 LLM
            response = self.chat(messages, tools)
            
            # 如果没有工具调用，返回结果
            if not response.tool_calls:
                return response
            
            # 处理工具调用
            messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [tc.to_openai_format() for tc in response.tool_calls]
            })
            
            for tool_call in response.tool_calls:
                tool_call_count += 1
                
                # 风险评估
                assessment = self.risk_assessor.assess(tool_call.name, tool_call.arguments)
                
                # 需要确认
                if assessment.needs_confirmation and self._on_confirmation_required:
                    confirmed = await self._on_confirmation_required(assessment)
                    if not confirmed:
                        # 用户拒绝
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"error": "用户取消了此操作"})
                        })
                        continue
                
                # 执行工具
                if auto_execute and self.tool_executor:
                    if self._on_tool_call_start:
                        self._on_tool_call_start(tool_call)
                    
                    try:
                        tool_call.status = "executing"
                        result = await self.tool_executor(tool_call.name, tool_call.arguments)
                        tool_call.result = result
                        tool_call.status = "completed"
                    except Exception as e:
                        tool_call.status = "failed"
                        tool_call.error = str(e)
                        result = {"error": str(e)}
                    
                    if self._on_tool_call_end:
                        self._on_tool_call_end(tool_call)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                else:
                    # 没有执行器，返回工具调用信息
                    return response
        
        # 达到最大调用次数，获取最终响应
        return self.chat(messages, tools)
    
    # ==================== 辅助方法 ====================
    
    def _add_system_prompt(self, messages: List[Dict]) -> List[Dict]:
        """添加系统提示词到消息列表
        
        Args:
            messages: 原始消息列表
            
        Returns:
            List[Dict]: 添加系统提示词后的消息列表
        """
        # 检查是否已有系统消息
        for msg in messages:
            if msg.get("role") == "system":
                # 更新系统消息
                msg["content"] = self.system_prompt + "\n\n" + msg.get("content", "")
                return messages
        
        # 添加新的系统消息
        return [{"role": "system", "content": self.system_prompt}] + messages
    
    def assess_tool_risk(self, tool_name: str, params: Dict[str, Any]) -> RiskAssessment:
        """评估工具调用风险
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            RiskAssessment: 风险评估结果
        """
        return self.risk_assessor.assess(tool_name, params)
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示词
        
        Args:
            prompt: 系统提示词
        """
        self.system_prompt = prompt
    
    def set_tool_executor(self, executor: Callable):
        """设置工具执行器
        
        Args:
            executor: 工具执行器回调函数
        """
        self.tool_executor = executor


# ==================== 工厂函数 ====================

def create_agent(
    provider: str = "deepseek",
    api_key: str = "",
    model: str = "",
    **kwargs
) -> AIAgentCore:
    """创建 AI Agent 实例
    
    Args:
        provider: LLM 提供商
        api_key: API Key
        model: 模型名称
        **kwargs: 其他参数
        
    Returns:
        AIAgentCore: AI Agent 实例
    """
    provider_map = {
        "deepseek": LLMProvider.DEEPSEEK,
        "openai": LLMProvider.OPENAI,
        "anthropic": LLMProvider.ANTHROPIC,
        "local": LLMProvider.LOCAL,
        "mock": LLMProvider.MOCK
    }
    
    default_models = {
        LLMProvider.DEEPSEEK: "deepseek-chat",
        LLMProvider.OPENAI: "gpt-4",
        LLMProvider.ANTHROPIC: "claude-3-opus-20240229",
        LLMProvider.LOCAL: "local-model",
        LLMProvider.MOCK: "mock"
    }
    
    llm_provider = provider_map.get(provider.lower(), LLMProvider.DEEPSEEK)
    
    config = LLMConfig(
        provider=llm_provider,
        model=model or default_models.get(llm_provider, ""),
        api_key=api_key,
        **kwargs
    )
    
    return AIAgentCore(llm_config=config)


# ==================== 测试 ====================

async def test_agent():
    """测试 AI Agent"""
    print("=" * 60)
    print("AI Agent 测试")
    print("=" * 60)
    
    # 创建 Mock 模式的 Agent
    agent = create_agent(provider="mock")
    
    # 测试同步聊天
    print("\n1. 同步聊天测试:")
    messages = [{"role": "user", "content": "帮我扫描 example.com"}]
    response = agent.chat(messages)
    print(f"响应: {response.content}")
    
    # 测试流式聊天
    print("\n2. 流式聊天测试:")
    async for chunk in agent.chat_stream(messages):
        if chunk.get("type") == "content":
            print(chunk["content"], end="", flush=True)
    print()
    
    # 测试风险评估
    print("\n3. 风险评估测试:")
    assessment = agent.assess_tool_risk("sqlmap_scan", {"target": "http://example.com"})
    print(f"工具: sqlmap_scan")
    print(f"风险等级: {assessment.level.value}")
    print(f"需要确认: {assessment.needs_confirmation}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(test_agent())
