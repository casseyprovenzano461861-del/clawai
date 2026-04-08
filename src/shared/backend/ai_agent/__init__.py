# -*- coding: utf-8 -*-
"""
ClawAI AI Agent 模块
提供 AI 驱动的交互式渗透测试能力
"""

from .core import AIAgentCore, LLMConfig, LLMProvider, create_agent, ToolCall
from .conversation import ConversationManager, Message
from .risk_assessor import RiskAssessor, RiskLevel, RiskAssessment
from .per_adapter import PERAdapter
from .orchestrator import AIAgentOrchestrator, AgentConfig, AgentMode, create_orchestrator
from .context_analyzer import ContextGapAnalyzer, GapAnalysisResult, analyze_context_gaps
from .rag_client import RAGClient, KnowledgeBase, create_rag_client
from .budget_manager import BudgetManager, BudgetPhase, create_budget_manager

# 工具执行
from .tools.executor import ToolExecutionBridge, ToolResult

# 提示词管理
from .prompts import PromptManager, PromptContext, PromptLanguage, create_prompt_manager

__all__ = [
    # Core
    'AIAgentCore',
    'LLMConfig',
    'LLMProvider',
    'create_agent',
    'ToolCall',
    
    # Tool Execution
    'ToolExecutionBridge', 
    'ToolResult',
    
    # Conversation
    'ConversationManager',
    'Message',
    
    # Risk
    'RiskAssessor',
    'RiskLevel',
    'RiskAssessment',
    
    # PER
    'PERAdapter',
    
    # Orchestrator
    'AIAgentOrchestrator',
    'AgentConfig',
    'AgentMode',
    'create_orchestrator',
    
    # Context Analysis
    'ContextGapAnalyzer',
    'GapAnalysisResult',
    'analyze_context_gaps',
    
    # RAG
    'RAGClient',
    'KnowledgeBase',
    'create_rag_client',
    
    # Budget
    'BudgetManager',
    'BudgetPhase',
    'create_budget_manager',
    
    # Prompts
    'PromptManager',
    'PromptContext',
    'PromptLanguage',
    'create_prompt_manager'
]
