# -*- coding: utf-8 -*-
"""
AI核心模块
基于大模型的自动化渗透测试AI核心
"""

__version__ = "1.0.0"
__author__ = "ClawAI Team"

from .llm_orchestrator import LLMOrchestrator
from .prompt_engineer import PromptEngineer
from .multi_model_decision import MultiModelDecisionSystem, ModelDecision, DecisionResult, DecisionStatus, ModelConfidence
from .cache_system import AICacheSystem
from .explanation_system import RuleEngineExplanationSystem, Explanation, ExplanationType
from .learning_system import AILearningSystem, LearningRecord, LearningPhase, LearningStrategy, ModelPerformanceMetrics
from .smart_orchestrator import SmartOrchestrator, TaskStatus, TaskPriority, TaskResource, ExecutionTask, TaskResult

__all__ = [
    "LLMOrchestrator",
    "PromptEngineer", 
    "MultiModelDecisionSystem",
    "ModelDecision",
    "DecisionResult", 
    "DecisionStatus",
    "ModelConfidence",
    "AICacheSystem",
    "RuleEngineExplanationSystem",
    "Explanation",
    "ExplanationType",
    "AILearningSystem",
    "LearningRecord",
    "LearningPhase",
    "LearningStrategy",
    "ModelPerformanceMetrics",
    "SmartOrchestrator",
    "TaskStatus",
    "TaskPriority",
    "TaskResource",
    "ExecutionTask",
    "TaskResult"
]
