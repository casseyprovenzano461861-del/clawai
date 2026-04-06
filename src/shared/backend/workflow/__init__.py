# -*- coding: utf-8 -*-
"""
AI工作流模块
基于AI的渗透测试工作流引擎
"""

__version__ = "1.0.0"
__author__ = "ClawAI Team"

from .ai_workflow import WorkflowStage, WorkflowContext

# 兼容：部分版本未实现 AIWorkflowEngine
try:
    from .ai_workflow import AIWorkflowEngine  # type: ignore
except ImportError:
    AIWorkflowEngine = None  # type: ignore
from .penetration_stages import (
    ReconnaissanceStage,
    ScanningStage,
    VulnerabilityAnalysisStage,
    ExploitationStage,
    PostExploitationStage,
    ReportingStage
)
from .decision_points import (
    TargetAnalysisDecision,
    ToolSelectionDecision,
    AttackPathDecision,
    RiskAssessmentDecision,
    AIDecisionSystem
)

__all__ = [
    "WorkflowStage",
    "WorkflowContext",
    "ReconnaissanceStage",
    "ScanningStage",
    "VulnerabilityAnalysisStage",
    "ExploitationStage",
    "PostExploitationStage",
    "ReportingStage",
    "TargetAnalysisDecision",
    "ToolSelectionDecision",
    "AttackPathDecision",
    "RiskAssessmentDecision",
    "AIDecisionSystem",
]

if AIWorkflowEngine is not None:
    __all__.insert(0, "AIWorkflowEngine")
