# -*- coding: utf-8 -*-
"""
对话模式
AI 建议操作，用户确认后执行
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass

from ..core import AIAgentCore, ChatResponse, ToolCall
from ..conversation import ConversationManager, Message
from ..risk_assessor import RiskAssessment
from ..prompts.system_prompt import get_system_prompt

logger = logging.getLogger(__name__)


@dataclass
class ChatModeConfig:
    """对话模式配置"""
    auto_execute_safe: bool = True       # 自动执行安全操作
    require_confirmation: bool = True     # 高风险操作需要确认
    max_tool_calls_per_turn: int = 5      # 每轮最大工具调用数
    stream_response: bool = True          # 流式响应


class ChatMode:
    """对话模式
    
    特点：
    - AI 分析用户请求，建议操作
    - 用户确认高风险操作后执行
    - 结果实时反馈给用户
    """
    
    def __init__(
        self,
        agent_core: AIAgentCore,
        conversation: ConversationManager,
        config: ChatModeConfig = None,
        confirmation_handler: Callable = None
    ):
        """初始化对话模式
        
        Args:
            agent_core: AI Agent 核心
            conversation: 对话管理器
            config: 配置
            confirmation_handler: 确认处理回调
        """
        self.agent = agent_core
        self.conversation = conversation
        self.config = config or ChatModeConfig()
        self.confirmation_handler = confirmation_handler
        
        # 状态
        self.pending_confirmations: List[Dict[str, Any]] = []
        
        logger.info("对话模式初始化完成")
    
    async def process_message(
        self,
        user_input: str,
        stream: bool = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户消息
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
            
        Yields:
            Dict[str, Any]: 处理事件
        """
        stream = stream if stream is not None else self.config.stream_response
        
        # 添加用户消息
        self.conversation.add_user_message(user_input)
        
        # 获取消息历史
        messages = self.conversation.get_messages_for_llm()
        
        # 获取带上下文的系统提示词
        ctx = self.conversation.get_context()
        system_prompt = get_system_prompt(
            target=ctx.target,
            phase=ctx.phase,
            findings_count=len(ctx.findings),
            vulnerabilities_count=len(ctx.vulnerabilities),
            mode="chat"
        )
        self.agent.set_system_prompt(system_prompt)
        
        if stream:
            async for event in self._process_stream(messages):
                yield event
        else:
            async for event in self._process_sync(messages):
                yield event
    
    async def _process_stream(
        self,
        messages: List[Dict]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理"""
        content_buffer = ""
        tool_calls_buffer: List[ToolCall] = []
        
        # 开始流式响应
        yield {"type": "response_start"}
        
        # 流式获取响应
        async for chunk in self.agent.chat_stream(messages):
            chunk_type = chunk.get("type")
            
            if chunk_type == "content":
                content = chunk.get("content", "")
                content_buffer += content
                yield {"type": "content", "content": content}
            
            elif chunk_type == "tool_call":
                # 收集工具调用
                yield {"type": "tool_call_chunk", "data": chunk}
            
            elif chunk_type == "finish":
                break
        
        # 获取完整的工具调用
        response = self.agent.chat(messages)
        
        # 添加助手消息到历史
        self.conversation.add_assistant_message(
            response.content,
            tool_calls=[tc.to_openai_format() for tc in response.tool_calls]
        )
        
        # 处理工具调用
        if response.tool_calls:
            async for event in self._handle_tool_calls(response.tool_calls):
                yield event
            
            # 工具执行后，获取最终响应
            final_messages = self.conversation.get_messages_for_llm()
            final_response = self.agent.chat(final_messages)
            
            if final_response.content:
                yield {"type": "content", "content": final_response.content}
                self.conversation.add_assistant_message(final_response.content)
        
        yield {"type": "response_end"}
    
    async def _process_sync(
        self,
        messages: List[Dict]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """同步处理"""
        yield {"type": "response_start"}
        
        # 获取响应
        response = self.agent.chat(messages)
        
        # 返回内容
        if response.content:
            yield {"type": "content", "content": response.content}
        
        # 添加到历史
        self.conversation.add_assistant_message(
            response.content,
            tool_calls=[tc.to_openai_format() for tc in response.tool_calls]
        )
        
        # 处理工具调用
        if response.tool_calls:
            async for event in self._handle_tool_calls(response.tool_calls):
                yield event
            
            # 工具执行后，获取最终响应
            final_messages = self.conversation.get_messages_for_llm()
            final_response = self.agent.chat(final_messages)
            
            if final_response.content:
                yield {"type": "content", "content": final_response.content}
                self.conversation.add_assistant_message(final_response.content)
        
        yield {"type": "response_end"}
    
    async def _handle_tool_calls(
        self,
        tool_calls: List[ToolCall]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理工具调用"""
        for tool_call in tool_calls[:self.config.max_tool_calls_per_turn]:
            # 风险评估
            assessment = self.agent.assess_tool_risk(tool_call.name, tool_call.arguments)
            
            # 通知工具调用开始
            yield {
                "type": "tool_call_start",
                "tool_name": tool_call.name,
                "arguments": tool_call.arguments,
                "risk_assessment": assessment.to_dict()
            }
            
            # 检查是否需要确认
            if assessment.needs_confirmation and self.config.require_confirmation:
                # 需要用户确认
                confirmed = await self._request_confirmation(tool_call, assessment)
                
                if not confirmed:
                    yield {
                        "type": "tool_call_cancelled",
                        "tool_name": tool_call.name,
                        "reason": "用户取消"
                    }
                    
                    self.conversation.add_tool_message(
                        content='{"cancelled": true, "reason": "用户取消"}',
                        tool_call_id=tool_call.id,
                        name=tool_call.name
                    )
                    continue
            
            # 执行工具
            yield {"type": "tool_call_executing", "tool_name": tool_call.name}
            
            try:
                result = await self.agent.tool_executor(tool_call.name, tool_call.arguments)
                
                tool_call.result = result.output
                tool_call.status = "completed"
                
                yield {
                    "type": "tool_call_result",
                    "tool_name": tool_call.name,
                    "result": result.to_dict()
                }
                
                # 更新上下文
                self._update_context(tool_call.name, result.output)
                
                # 添加工具结果到历史
                self.conversation.add_tool_message(
                    content=json.dumps(result.output) if isinstance(result.output, dict) else str(result.output),
                    tool_call_id=tool_call.id,
                    name=tool_call.name
                )
                
            except Exception as e:
                tool_call.status = "failed"
                tool_call.error = str(e)
                
                yield {
                    "type": "tool_call_error",
                    "tool_name": tool_call.name,
                    "error": str(e)
                }
                
                self.conversation.add_tool_message(
                    content=f'{{"error": "{str(e)}"}}',
                    tool_call_id=tool_call.id,
                    name=tool_call.name
                )
    
    async def _request_confirmation(
        self,
        tool_call: ToolCall,
        assessment: RiskAssessment
    ) -> bool:
        """请求用户确认"""
        if self.confirmation_handler:
            return await self.confirmation_handler(tool_call, assessment)
        
        # 默认行为：需要外部处理确认
        # 将确认请求加入待处理队列
        confirmation_request = {
            "tool_call": tool_call,
            "assessment": assessment,
            "resolved": False,
            "confirmed": False
        }
        self.pending_confirmations.append(confirmation_request)
        
        return False  # 返回 False 等待外部确认
    
    def confirm_tool_call(self, tool_call_id: str, confirmed: bool):
        """确认工具调用（外部调用）"""
        for req in self.pending_confirmations:
            if req["tool_call"].id == tool_call_id:
                req["resolved"] = True
                req["confirmed"] = confirmed
                return True
        return False
    
    def _update_context(self, tool_name: str, result: Dict[str, Any]):
        """更新上下文"""
        # 根据工具类型更新上下文
        if tool_name == "nmap_scan":
            if result.get("target"):
                self.conversation.set_target(result["target"])
            self.conversation.update_scan_results("nmap", result)
        
        elif tool_name in ["nuclei_scan", "sqlmap_scan"]:
            vulns = result.get("vulnerabilities", [])
            for vuln in vulns:
                self.conversation.add_vulnerability(vuln)
            self.conversation.update_scan_results(tool_name, result)
        
        elif tool_name == "whatweb_scan":
            self.conversation.update_scan_results("whatweb", result)


# ==================== 测试 ====================

async def test_chat_mode():
    """测试对话模式"""
    print("=" * 60)
    print("对话模式测试")
    print("=" * 60)
    
    from ..core import create_agent
    from ..conversation import ConversationManager
    
    # 创建组件
    agent = create_agent(provider="mock")
    conversation = ConversationManager()
    mode = ChatMode(agent, conversation)
    
    # 处理消息
    print("\n处理消息: '帮我扫描 example.com'")
    async for event in mode.process_message("帮我扫描 example.com"):
        if event["type"] == "content":
            print(f"  内容: {event['content']}")
        elif event["type"] == "tool_call_start":
            print(f"  工具调用: {event['tool_name']}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(test_chat_mode())
