# -*- coding: utf-8 -*-
"""
AI Agent 集成器
整合所有 AI Agent 组件，提供统一的入口点
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# 添加路径
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.insert(0, _project_root)

from .core import AIAgentCore, LLMConfig, LLMProvider, create_agent
from .conversation import ConversationManager
from .risk_assessor import RiskAssessor, RiskLevel, RiskAssessment
from .tools.executor import ToolExecutionBridge
from .tools.schemas import TOOL_SCHEMAS
from .per_adapter import PERAdapter
from .modes.chat_mode import ChatMode, ChatModeConfig
from .modes.autonomous_mode import AutonomousMode, AutonomousModeConfig
from .prompts.system_prompt import get_system_prompt

# 尝试导入 UnifiedExecutor
try:
    from ..tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
    UNIFIED_EXECUTOR_AVAILABLE = True
except ImportError:
    try:
        # 尝试另一种导入路径
        import importlib
        tools_module = importlib.import_module('src.shared.backend.tools.unified_executor_final')
        UnifiedExecutor = getattr(tools_module, 'UnifiedExecutor')
        ExecutionStrategy = getattr(tools_module, 'ExecutionStrategy')
        UNIFIED_EXECUTOR_AVAILABLE = True
    except Exception as e:
        logger.warning(f"无法导入 UnifiedExecutor: {e}")
        UNIFIED_EXECUTOR_AVAILABLE = False
        UnifiedExecutor = None
        ExecutionStrategy = None

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    """Agent 模式"""
    CHAT = "chat"           # 对话模式
    AUTONOMOUS = "autonomous"  # 自主模式


@dataclass
class AgentConfig:
    """Agent 配置"""
    # LLM 配置
    provider: str = "deepseek"
    api_key: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 行为配置
    mode: AgentMode = AgentMode.CHAT
    auto_execute_safe: bool = True
    require_confirmation: bool = True
    max_iterations: int = 10
    
    # 功能开关
    enable_simulation: bool = True
    enable_streaming: bool = True
    enable_persistence: bool = True
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """从环境变量创建配置"""
        return cls(
            provider=os.getenv("LLM_PROVIDER", "deepseek"),
            api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("LLM_MODEL", ""),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        )


class AIAgentOrchestrator:
    """AI Agent 编排器
    
    整合所有组件，提供统一的入口点
    """
    
    def __init__(self, config: AgentConfig = None):
        """初始化编排器
        
        Args:
            config: Agent 配置
        """
        self.config = config or AgentConfig.from_env()
        
        # 核心组件
        self.agent_core: Optional[AIAgentCore] = None
        self.conversation: Optional[ConversationManager] = None
        self.tool_bridge: Optional[ToolExecutionBridge] = None
        self.risk_assessor: Optional[RiskAssessor] = None
        self.per_adapter: Optional[PERAdapter] = None
        self.unified_executor: Optional[Any] = None  # UnifiedExecutor 实例
        
        # 执行模式
        self.chat_mode: Optional[ChatMode] = None
        self.autonomous_mode: Optional[AutonomousMode] = None
        
        # 当前模式
        self.current_mode = self.config.mode
        
        # 回调
        self._callbacks: Dict[str, Callable] = {}
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化所有组件"""
        logger.info("初始化 AI Agent 编排器...")
        
        # 1. 创建 LLM 配置
        llm_config = LLMConfig(
            provider=LLMProvider(self.config.provider.lower()),
            model=self.config.model or self._get_default_model(),
            api_key=self.config.api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # 2. 创建风险评估器
        self.risk_assessor = RiskAssessor(
            strict_mode=not self.config.auto_execute_safe
        )
        
        # 3. 创建 UnifiedExecutor（如果可用）
        if UNIFIED_EXECUTOR_AVAILABLE and UnifiedExecutor:
            try:
                self.unified_executor = UnifiedExecutor(
                    max_workers=3,
                    enable_retry=True,
                    max_retries=2,
                    execution_strategy=ExecutionStrategy.INTELLIGENT if ExecutionStrategy else None,
                    enable_security=True,
                    require_real_execution=False,  # 允许回退到模拟
                    enable_strict_security=False
                )
                logger.info("UnifiedExecutor 初始化成功")
            except Exception as e:
                logger.warning(f"UnifiedExecutor 初始化失败: {e}")
                self.unified_executor = None
        
        # 4. 创建工具执行桥接
        self.tool_bridge = ToolExecutionBridge(
            unified_executor=self.unified_executor,
            enable_simulation=self.config.enable_simulation,
            prefer_real_execution=self.unified_executor is not None
        )
        
        # 5. 创建对话管理器
        self.conversation = ConversationManager(
            max_history=20,
            persist_dir="data/sessions" if self.config.enable_persistence else None
        )
        
        # 6. 创建 AI Agent 核心
        self.agent_core = create_agent(
            provider=self.config.provider,
            api_key=self.config.api_key,
            model=self.config.model
        )
        
        # 设置工具执行器
        self.agent_core.set_tool_executor(self.tool_bridge.execute)
        self.agent_core.risk_assessor = self.risk_assessor
        
        # 7. 创建 P-E-R 适配器
        self.per_adapter = PERAdapter(
            max_iterations=self.config.max_iterations
        )
        
        # 8. 创建执行模式
        self.chat_mode = ChatMode(
            agent_core=self.agent_core,
            conversation=self.conversation,
            config=ChatModeConfig(
                auto_execute_safe=self.config.auto_execute_safe,
                require_confirmation=self.config.require_confirmation,
                stream_response=self.config.enable_streaming
            ),
            confirmation_handler=self._handle_confirmation
        )
        
        self.autonomous_mode = AutonomousMode(
            per_adapter=self.per_adapter,
            conversation=self.conversation,
            config=AutonomousModeConfig(
                max_iterations=self.config.max_iterations,
                pause_on_high_risk=self.config.require_confirmation
            ),
            progress_handler=self._handle_progress,
            confirmation_handler=self._handle_confirmation
        )
        
        logger.info("AI Agent 编排器初始化完成")
    
    def _get_default_model(self) -> str:
        """获取默认模型"""
        defaults = {
            "deepseek": "deepseek-chat",
            "openai": "gpt-4",
            "anthropic": "claude-3-opus-20240229",
            "mock": "mock"
        }
        return defaults.get(self.config.provider.lower(), "deepseek-chat")
    
    # ==================== 核心方法 ====================
    
    async def chat(
        self,
        user_input: str,
        stream: bool = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户输入（对话模式）
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
            
        Yields:
            Dict[str, Any]: 处理事件
        """
        if self.current_mode == AgentMode.AUTONOMOUS:
            # 自主模式下的特殊处理
            async for event in self._handle_autonomous_input(user_input):
                yield event
        else:
            # 对话模式
            stream = stream if stream is not None else self.config.enable_streaming
            
            async for event in self.chat_mode.process_message(user_input, stream):
                yield event
    
    async def _handle_autonomous_input(
        self,
        user_input: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理自主模式下的用户输入"""
        input_lower = user_input.lower()
        
        # 检查控制命令
        if "暂停" in input_lower or "pause" in input_lower:
            self.autonomous_mode.pause()
            yield {"type": "info", "message": "已暂停执行"}
        
        elif "继续" in input_lower or "resume" in input_lower:
            self.autonomous_mode.resume()
            yield {"type": "info", "message": "继续执行"}
        
        elif "停止" in input_lower or "stop" in input_lower:
            self.autonomous_mode.stop()
            yield {"type": "info", "message": "已停止执行"}
        
        elif "状态" in input_lower or "status" in input_lower:
            status = self.autonomous_mode.get_status()
            yield {"type": "status", "data": status}
        
        else:
            # 切换到对话模式处理
            self.current_mode = AgentMode.CHAT
            async for event in self.chat_mode.process_message(user_input):
                yield event
    
    async def start_autonomous(
        self,
        target: str,
        goal: str = None,
        mode: str = "full"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """启动自主渗透测试
        
        Args:
            target: 目标地址
            goal: 测试目标描述
            mode: 测试模式
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        self.current_mode = AgentMode.AUTONOMOUS
        
        async for event in self.autonomous_mode.start(target, goal, mode):
            yield event
    
    # ==================== 模式切换 ====================
    
    def set_mode(self, mode: AgentMode):
        """设置执行模式"""
        self.current_mode = mode
        logger.info(f"切换到 {mode.value} 模式")
    
    def get_mode(self) -> AgentMode:
        """获取当前模式"""
        return self.current_mode
    
    # ==================== 会话管理 ====================
    
    def set_target(self, target: str):
        """设置目标"""
        self.conversation.set_target(target)
    
    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        return self.conversation.get_context_summary()
    
    def save_session(self, path: str = None) -> str:
        """保存会话"""
        return self.conversation.save_session(path)
    
    def load_session(self, path: str) -> bool:
        """加载会话"""
        return self.conversation.load_session(path)
    
    def clear_session(self):
        """清空会话"""
        self.conversation.clear_messages()
        self.conversation.update_context(
            target="",
            phase="idle",
            findings=[],
            vulnerabilities=[]
        )
    
    # ==================== 回调设置 ====================
    
    def set_callbacks(
        self,
        on_content: Callable = None,
        on_tool_call: Callable = None,
        on_confirmation: Callable = None,
        on_progress: Callable = None,
        on_error: Callable = None
    ):
        """设置回调函数
        
        Args:
            on_content: 内容输出回调
            on_tool_call: 工具调用回调
            on_confirmation: 确认请求回调
            on_progress: 进度更新回调
            on_error: 错误回调
        """
        self._callbacks = {
            "on_content": on_content,
            "on_tool_call": on_tool_call,
            "on_confirmation": on_confirmation,
            "on_progress": on_progress,
            "on_error": on_error
        }
    
    async def _handle_confirmation(
        self,
        tool_call,
        assessment: RiskAssessment
    ) -> bool:
        """处理确认请求"""
        if "on_confirmation" in self._callbacks and self._callbacks["on_confirmation"]:
            return await self._callbacks["on_confirmation"](tool_call, assessment)
        
        # 默认：高风险操作需要确认
        return assessment.level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def _handle_progress(self, progress):
        """处理进度更新"""
        if "on_progress" in self._callbacks and self._callbacks["on_progress"]:
            self._callbacks["on_progress"](progress)
    
    # ==================== 状态查询 ====================
    
    def get_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        return {
            "mode": self.current_mode.value,
            "context": self.conversation.get_context().to_dict(),
            "session_stats": self.conversation.get_session_stats(),
            "tool_stats": self.tool_bridge.get_stats() if self.tool_bridge else {}
        }
    
    def get_tool_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        if self.tool_bridge:
            return self.tool_bridge.get_stats()
        return {}


# ==================== 便捷函数 ====================

def create_orchestrator(
    provider: str = "deepseek",
    api_key: str = "",
    **kwargs
) -> AIAgentOrchestrator:
    """创建 AI Agent 编排器
    
    Args:
        provider: LLM 提供商
        api_key: API Key
        **kwargs: 其他配置
        
    Returns:
        AIAgentOrchestrator: 编排器实例
    """
    config = AgentConfig(
        provider=provider,
        api_key=api_key,
        **kwargs
    )
    return AIAgentOrchestrator(config)


# ==================== 交互式会话 ====================

async def interactive_session(orchestrator: AIAgentOrchestrator = None):
    """交互式会话
    
    Args:
        orchestrator: 编排器实例
    """
    if orchestrator is None:
        orchestrator = create_orchestrator()
    
    print("\n" + "=" * 60)
    print("ClawAI AI Agent - 交互式会话")
    print("=" * 60)
    print("输入 'help' 查看帮助，'exit' 退出")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # 检查退出
            if user_input.lower() in ["exit", "quit", "退出"]:
                print("\n再见！")
                break
            
            # 处理输入
            print("\nClawAI: ", end="", flush=True)
            
            async for event in orchestrator.chat(user_input):
                event_type = event.get("type")
                
                if event_type == "content":
                    print(event.get("content", ""), end="", flush=True)
                
                elif event_type == "tool_call_start":
                    tool_name = event.get("tool_name", "")
                    print(f"\n[工具调用: {tool_name}]")
                
                elif event_type == "tool_call_result":
                    result = event.get("result", {})
                    if result.get("simulated"):
                        print("  (模拟执行)")
                
                elif event_type == "response_end":
                    pass  # 响应结束
            
            print()  # 换行
            
        except KeyboardInterrupt:
            print("\n\n会话已中断")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            logger.error(f"会话错误: {e}")


# ==================== 测试 ====================

async def test_orchestrator():
    """测试编排器"""
    print("=" * 60)
    print("AI Agent 编排器测试")
    print("=" * 60)
    
    # 创建编排器（Mock 模式）
    orchestrator = create_orchestrator(provider="mock")
    
    # 测试状态
    print("\n1. 初始状态:")
    status = orchestrator.get_status()
    print(f"  模式: {status['mode']}")
    
    # 测试对话
    print("\n2. 对话测试:")
    async for event in orchestrator.chat("帮我扫描 example.com"):
        if event.get("type") == "content":
            print(f"  响应: {event.get('content', '')}")
    
    # 测试上下文
    print("\n3. 上下文:")
    print(f"  {orchestrator.get_context_summary()}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
