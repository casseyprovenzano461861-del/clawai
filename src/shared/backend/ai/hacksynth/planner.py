"""
HackSynth Planner实现 - P1-1任务
基于HackSynth架构的智能规划器，用于生成渗透测试命令序列
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class PlanningPhase(str, Enum):
    """规划阶段枚举"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"


class CommandComplexity(str, Enum):
    """命令复杂性枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolEffectiveness(BaseModel):
    """工具有效性模型"""
    tool_name: str
    success_rate: float = Field(ge=0.0, le=1.0)
    average_time: float = Field(ge=0.0)
    reliability_score: float = Field(ge=0.0, le=1.0)
    last_used: Optional[datetime] = None
    usage_count: int = Field(ge=0, default=0)


class PlanningContext(BaseModel):
    """规划上下文模型"""
    target: str
    target_type: str = "unknown"
    current_phase: PlanningPhase = PlanningPhase.RECONNAISSANCE
    discovered_services: List[str] = Field(default_factory=list)
    open_ports: List[int] = Field(default_factory=list)
    vulnerabilities_found: List[str] = Field(default_factory=list)
    credentials_obtained: List[Dict[str, str]] = Field(default_factory=list)
    previous_commands: List[str] = Field(default_factory=list)
    command_results: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('target')
    def validate_target(cls, v):
        """验证目标地址"""
        if not v or len(v.strip()) == 0:
            raise ValueError("目标地址不能为空")
        return v.strip()


class CommandSuggestion(BaseModel):
    """命令建议模型"""
    command: str
    tool: str
    phase: PlanningPhase
    complexity: CommandComplexity
    estimated_time: float = Field(ge=0.0, description="估计执行时间（秒）")
    success_probability: float = Field(ge=0.0, le=1.0)
    rationale: str
    prerequisites: List[str] = Field(default_factory=list)
    expected_output: Optional[str] = None
    risk_level: str = "low"
    
    @validator('command')
    def validate_command_format(cls, v):
        """验证命令格式"""
        if not v or len(v.strip()) == 0:
            raise ValueError("命令不能为空")
        
        # 检查命令是否包含危险操作
        dangerous_patterns = [
            r"rm\s+-rf",
            r"dd\s+if=",
            r":\(\)\{:\|:\}&\};",
            r"mkfs",
            r"fdisk",
            r"chmod\s+777"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"命令包含危险操作: {pattern}")
        
        return v.strip()


class HackSynthPlanner(ABC):
    """HackSynth Planner抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Planner
        
        Args:
            config: Planner配置
        """
        self.config = config
        self.tool_effectiveness: Dict[str, ToolEffectiveness] = {}
        self.planning_history: List[Dict[str, Any]] = []
        self.learning_enabled = config.get("learning_enabled", True)
        
        # 初始化工具有效性数据
        self._initialize_tool_effectiveness()
        
        logger.info(f"HackSynth Planner初始化完成: {self.__class__.__name__}")
    
    def _initialize_tool_effectiveness(self):
        """初始化工具有效性数据"""
        default_tools = {
            "nmap": ToolEffectiveness(
                tool_name="nmap",
                success_rate=0.95,
                average_time=60.0,
                reliability_score=0.9
            ),
            "whatweb": ToolEffectiveness(
                tool_name="whatweb",
                success_rate=0.90,
                average_time=30.0,
                reliability_score=0.85
            ),
            "nuclei": ToolEffectiveness(
                tool_name="nuclei",
                success_rate=0.85,
                average_time=120.0,
                reliability_score=0.8
            ),
            "sqlmap": ToolEffectiveness(
                tool_name="sqlmap",
                success_rate=0.70,
                average_time=180.0,
                reliability_score=0.75
            ),
            "dirsearch": ToolEffectiveness(
                tool_name="dirsearch",
                success_rate=0.80,
                average_time=90.0,
                reliability_score=0.8
            ),
            "nikto": ToolEffectiveness(
                tool_name="nikto",
                success_rate=0.75,
                average_time=150.0,
                reliability_score=0.7
            ),
            "hydra": ToolEffectiveness(
                tool_name="hydra",
                success_rate=0.60,
                average_time=300.0,
                reliability_score=0.6
            ),
            "metasploit": ToolEffectiveness(
                tool_name="metasploit",
                success_rate=0.65,
                average_time=240.0,
                reliability_score=0.7
            )
        }
        
        self.tool_effectiveness = default_tools
    
    @abstractmethod
    async def generate_plan(
        self,
        context: PlanningContext,
        available_tools: List[str],
        max_suggestions: int = 3
    ) -> List[CommandSuggestion]:
        """
        生成渗透测试计划
        
        Args:
            context: 规划上下文
            available_tools: 可用工具列表
            max_suggestions: 最大建议数量
            
        Returns:
            命令建议列表
        """
        pass
    
    @abstractmethod
    async def evaluate_command(
        self,
        command: str,
        context: PlanningContext
    ) -> Dict[str, Any]:
        """
        评估命令的适用性
        
        Args:
            command: 待评估的命令
            context: 规划上下文
            
        Returns:
            评估结果
        """
        pass
    
    def update_tool_effectiveness(
        self,
        tool_name: str,
        success: bool,
        execution_time: float
    ):
        """
        更新工具有效性数据
        
        Args:
            tool_name: 工具名称
            success: 是否成功
            execution_time: 执行时间（秒）
        """
        if tool_name not in self.tool_effectiveness:
            self.tool_effectiveness[tool_name] = ToolEffectiveness(
                tool_name=tool_name,
                success_rate=0.5,
                average_time=execution_time,
                reliability_score=0.5
            )
        
        tool = self.tool_effectiveness[tool_name]
        
        # 更新使用计数
        tool.usage_count += 1
        tool.last_used = datetime.now()
        
        # 更新成功率（使用指数移动平均）
        alpha = 0.1  # 学习率
        current_success = 1.0 if success else 0.0
        tool.success_rate = (1 - alpha) * tool.success_rate + alpha * current_success
        
        # 更新平均时间
        tool.average_time = (1 - alpha) * tool.average_time + alpha * execution_time
        
        # 更新可靠性分数
        if success:
            tool.reliability_score = min(1.0, tool.reliability_score + 0.05)
        else:
            tool.reliability_score = max(0.0, tool.reliability_score - 0.1)
        
        logger.debug(f"工具有效性更新: {tool_name}, 成功率: {tool.success_rate:.2f}")
    
    def record_planning_decision(
        self,
        context: PlanningContext,
        suggestions: List[CommandSuggestion],
        selected_suggestion: Optional[CommandSuggestion] = None
    ):
        """
        记录规划决策
        
        Args:
            context: 规划上下文
            suggestions: 生成的建议列表
            selected_suggestion: 选择的建议（如果有）
        """
        decision_record = {
            "timestamp": datetime.now().isoformat(),
            "target": context.target,
            "phase": context.current_phase,
            "context_summary": {
                "discovered_services": len(context.discovered_services),
                "open_ports": len(context.open_ports),
                "vulnerabilities_found": len(context.vulnerabilities_found)
            },
            "suggestions_generated": len(suggestions),
            "suggestions": [
                {
                    "command": s.command[:100] + "..." if len(s.command) > 100 else s.command,
                    "tool": s.tool,
                    "complexity": s.complexity,
                    "success_probability": s.success_probability
                }
                for s in suggestions
            ]
        }
        
        if selected_suggestion:
            decision_record["selected_suggestion"] = {
                "command": selected_suggestion.command[:100] + "..." if len(selected_suggestion.command) > 100 else selected_suggestion.command,
                "tool": selected_suggestion.tool,
                "rationale": selected_suggestion.rationale
            }
        
        self.planning_history.append(decision_record)
        
        # 限制历史记录大小
        if len(self.planning_history) > 100:
            self.planning_history = self.planning_history[-100:]
    
    def get_planning_statistics(self) -> Dict[str, Any]:
        """获取规划统计信息"""
        if not self.planning_history:
            return {"total_decisions": 0}
        
        total_decisions = len(self.planning_history)
        phases_count = {}
        tools_used = {}
        
        for record in self.planning_history:
            # 统计阶段
            phase = record.get("phase", "unknown")
            phases_count[phase] = phases_count.get(phase, 0) + 1
            
            # 统计工具使用
            if "selected_suggestion" in record:
                tool = record["selected_suggestion"].get("tool", "unknown")
                tools_used[tool] = tools_used.get(tool, 0) + 1
        
        return {
            "total_decisions": total_decisions,
            "phases_distribution": phases_count,
            "tools_usage": tools_used,
            "tool_effectiveness": {
                tool: {
                    "success_rate": eff.success_rate,
                    "average_time": eff.average_time,
                    "reliability_score": eff.reliability_score,
                    "usage_count": eff.usage_count
                }
                for tool, eff in self.tool_effectiveness.items()
            }
        }
    
    def determine_next_phase(self, context: PlanningContext) -> PlanningPhase:
        """
        确定下一个阶段
        
        Args:
            context: 当前上下文
            
        Returns:
            下一个阶段
        """
        current_phase = context.current_phase
        
        # 基于当前发现决定下一个阶段
        if current_phase == PlanningPhase.RECONNAISSANCE:
            if context.open_ports or context.discovered_services:
                return PlanningPhase.SCANNING
            else:
                return PlanningPhase.RECONNAISSANCE
        
        elif current_phase == PlanningPhase.SCANNING:
            if context.vulnerabilities_found:
                return PlanningPhase.VULNERABILITY_ASSESSMENT
            elif context.discovered_services:
                # 有服务但没发现漏洞，继续扫描
                return PlanningPhase.SCANNING
            else:
                # 没发现服务，回到侦察
                return PlanningPhase.RECONNAISSANCE
        
        elif current_phase == PlanningPhase.VULNERABILITY_ASSESSMENT:
            if any("critical" in vuln.lower() or "high" in vuln.lower() 
                   for vuln in context.vulnerabilities_found):
                return PlanningPhase.EXPLOITATION
            else:
                return PlanningPhase.VULNERABILITY_ASSESSMENT
        
        elif current_phase == PlanningPhase.EXPLOITATION:
            if context.credentials_obtained:
                return PlanningPhase.POST_EXPLOITATION
            else:
                return PlanningPhase.EXPLOITATION
        
        elif current_phase == PlanningPhase.POST_EXPLOITATION:
            # 后渗透阶段可以持续进行
            return PlanningPhase.POST_EXPLOITATION
        
        # 默认返回当前阶段
        return current_phase
    
    def _extract_tool_from_command(self, command: str) -> Optional[str]:
        """从命令中提取工具名称"""
        command_lower = command.lower()
        
        tool_patterns = {
            "nmap": ["nmap "],
            "whatweb": ["whatweb "],
            "sqlmap": ["sqlmap "],
            "nuclei": ["nuclei "],
            "dirsearch": ["dirsearch ", "dirb ", "gobuster "],
            "nikto": ["nikto "],
            "hydra": ["hydra "],
            "metasploit": ["msfconsole", "msf "]
        }
        
        for tool, patterns in tool_patterns.items():
            for pattern in patterns:
                if pattern in command_lower:
                    return tool
        
        return None
    
    def _estimate_command_complexity(self, command: str, tool: Optional[str] = None) -> CommandComplexity:
        """估计命令复杂性"""
        if not tool:
            tool = self._extract_tool_from_command(command)
        
        command_lower = command.lower()
        
        # 基于工具和参数判断复杂性
        high_complexity_tools = {"sqlmap", "metasploit", "hydra"}
        medium_complexity_tools = {"nmap", "nuclei", "nikto", "dirsearch"}
        
        if tool in high_complexity_tools:
            return CommandComplexity.HIGH
        elif tool in medium_complexity_tools:
            # 检查是否有复杂参数
            if any(param in command_lower for param in ["-p-", "--all-ports", "--script=", "-A"]):
                return CommandComplexity.HIGH
            else:
                return CommandComplexity.MEDIUM
        else:
            return CommandComplexity.LOW
    
    def _calculate_success_probability(
        self,
        command: str,
        tool: Optional[str],
        context: PlanningContext
    ) -> float:
        """计算成功概率"""
        base_probability = 0.5
        
        # 基于工具有效性
        if tool and tool in self.tool_effectiveness:
            base_probability = self.tool_effectiveness[tool].success_rate
        
        # 基于阶段调整
        phase_adjustments = {
            PlanningPhase.RECONNAISSANCE: 0.1,
            PlanningPhase.SCANNING: 0.0,
            PlanningPhase.VULNERABILITY_ASSESSMENT: -0.1,
            PlanningPhase.EXPLOITATION: -0.2,
            PlanningPhase.POST_EXPLOITATION: -0.1
        }
        
        adjustment = phase_adjustments.get(context.current_phase, 0.0)
        base_probability += adjustment
        
        # 基于上下文信息调整
        if context.discovered_services:
            base_probability += 0.05
        
        if context.vulnerabilities_found:
            base_probability += 0.1
        
        # 确保在合理范围内
        return max(0.1, min(0.95, base_probability))