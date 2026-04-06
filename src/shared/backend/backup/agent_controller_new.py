# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
攻击Agent控制器 - 基于Skills体系的实时决策Agent
集成SkillRegistry、decision_engine、evolution_engine
实现目标驱动、行为风格、决策扰动、记忆机制、行为日志
"""

import json
import random
import logging
import sys
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 动态导入现有模块
try:
    # 相对导入（当作为模块导入时）
    from .skills.skill_registry import SkillRegistry
    from .skills.base_skill import SkillContext
    from .decision_engine import DecisionEngine
    from .evolution_engine import EvolutionEngine, EvolutionResult
except ImportError:
    # 绝对导入（当直接运行时）
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.skills.skill_registry import SkillRegistry
    from backend.skills.base_skill import SkillContext
    from backend.decision_engine import DecisionEngine
    from backend.evolution_engine import EvolutionEngine, EvolutionResult

logger = logging.getLogger(__name__)


class AttackGoal(Enum):
    """攻击目标类型"""
    GET_SHELL = "get_shell"              # 获取系统Shell
    DATA_EXFILTRATION = "data_exfiltration"  # 数据窃取
    PRIVILEGE_ESCALATION = "privilege_escalation"  # 权限提升


class AgentStyle(Enum):
    """Agent行为风格"""
    STEALTH = "stealth"      # 隐蔽优先，低检测
    AGGRESSIVE = "aggressive"  # 激进优先，高成功率
    BALANCED = "balanced"    # 平衡模式


@dataclass
class FailureMemory:
    """失败记忆条目"""
    timestamp: str
    target: str
    skill_name: str
    skill_type: str
    failure_type: str  # waf, ids, permission, payload, other
    failure_reason: str
    detected_by: str  # 检测机制
    avoidance_strategy: str  # 避免策略
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "target": self.target,
            "skill_name": self.skill_name,
            "skill_type": self.skill_type,
            "failure_type": self.failure_type,
            "failure_reason": self.failure_reason,
            "detected_by": self.detected_by,
            "avoidance_strategy": self.avoidance_strategy
        }


@dataclass
class AgentAction:
    """Agent行为日志条目"""
    step: int
    timestamp: str
    action_type: str  # perceive, select, execute, update, adjust, memory
    description: str
    target_info: str
    result: str
    confidence: float
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "description": self.description,
            "target_info": self.target_info,
            "result": self.result,
            "confidence": self.confidence,
            "details": self.details or {}
        }


@dataclass
class AgentResult:
    """Agent最终结果"""
    success: bool
    goal: str
    style: str
    final_context: Dict[str, Any]
    total_steps: int
    evolution_rounds: int
    final_score: float
    agent_actions: List[Dict[str, Any]]
    failure_memories: List[Dict[str, Any]]
    decision_perturbation: float
    execution_summary: str
    skills_executed: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "goal": self.goal,
            "style": self.style,
            "final_context": self.final_context,
            "total_steps": self.total_steps,
            "evolution_rounds": self.evolution_rounds,
            "final_score": self.final_score,
            "agent_actions": self.agent_actions,
            "failure_memories": self.failure_memories,
            "decision_perturbation": self.decision_perturbation,
            "execution_summary": self.execution_summary,
            "skills_executed": self.skills_executed,
            "rule_engine_behavior_analysis": self._generate_rule_engine_behavior_analysis()
        }
    
    def _generate_rule_engine_behavior_analysis(self) -> str:
        """生成规则引擎行为分析"""
        if self.style == "stealth":
            style_desc = "隐蔽型黑客：优先规避检测，采用低干扰策略"
        elif self.style == "aggressive":
            style_desc = "激进型黑客：追求高成功率，采用强力攻击"
        else:
            style_desc = "平衡型黑客：兼顾成功率和隐蔽性"
        
        if self.goal == "get_shell":
            goal_desc = "目标：获取系统控制权（Shell）"
        elif self.goal == "data_exfiltration":
            goal_desc = "目标：窃取敏感数据"
        else:
            goal_desc = "目标：提升系统权限"
        
        evolution_desc = f"经过{self.evolution_rounds}轮进化" if self.evolution_rounds > 1 else "首轮攻击成功"
        skills_desc = f"执行技能: {', '.join(self.skills_executed[:3])}" if self.skills_executed else "未执行技能"
        
        return f"{style_desc} | {goal_desc} | {evolution_desc} | {skills_desc} | 最终评分：{self.final_score:.1f}/10"


class AgentController:
    """攻击Agent控制器 - 基于Skills体系的实时决策Agent"""
    
    def __init__(self, 
                 goal: AttackGoal = AttackGoal.GET_SHELL,
                 style: AgentStyle = AgentStyle.BALANCED,
                 enable_perturbation: bool = True,
                 max_evolution_rounds: int = 3,
                 max_iterations: int = 20):
        """
        初始化Agent控制器
        
        Args:
            goal: 攻击目标
            style: 行为风格
            enable_perturbation: 是否启用决策扰动
            max_evolution_rounds: 最大进化轮次
            max_iterations: 最大决策迭代次数
        """
        self.goal = goal
        self.style = style
        self.enable_perturbation = enable_perturbation
        self.max_evolution_rounds = max_evolution_rounds
        self.max_iterations = max_iterations
        
        # 初始化组件
        self.skill_registry = SkillRegistry()
        self.decision_engine = DecisionEngine()
        self.evolution_engine = EvolutionEngine(max_evolution_rounds=max_evolution_rounds)
        
        # 技能执行上下文
        self.context = SkillContext()
        
        # 记忆机制
        self.failure_memories: List[FailureMemory] = []
        
        # 行为日志
        self.agent_actions: List[AgentAction] = []
        self.action_counter = 0
        
        # 决策扰动幅度
        self.perturbation_range = 0.1  # ±10%
        
        # 已执行的技能记录
        self.executed_skills: List[str] = []
        
        # 目标映射到技能偏好
        self.goal_skill_mapping = {
            AttackGoal.GET_SHELL: {
                "preferred_skills": ["rce_skill", "privilege_escalation_skill"],
                "preferred_focus": ["远程代码执行", "权限提升"],
                "success_weight_bonus": 0.1,
                "time_weight_penalty": -0.05
            },
            AttackGoal.DATA_EXFILTRATION: {
                "preferred_skills": ["sql_injection_skill", "whatweb_skill"],
                "preferred_focus": ["数据库渗透", "Web应用分析"],
                "success_weight_bonus": 0.05,
                "risk_weight_penalty": -0.1  # 数据窃取需谨慎
            },
            AttackGoal.PRIVILEGE_ESCALATION: {
                "preferred_skills": ["privilege_escalation_skill", "rce_skill"],
                "preferred_focus": ["权限提升", "系统访问"],
                "step_complexity_bonus": 0.08,  # 权限提升步骤可能复杂
                "risk_weight_bonus": 0.05  # 权限提升风险较高
            }
        }
        
        # 行为风格映射到评分权重调整
        self.style_weight_adjustments = {
            AgentStyle.STEALTH: {
                "risk_level": 0.25,      # 风险权重提高
                "time_efficiency": 0.15,  # 时间效率权重降低（隐蔽需要时间）
                "success_rate": 0.30,     # 成功率权重降低
                "step_complexity": 0.10   # 步骤复杂度权重降低
            },
            AgentStyle.AGGRESSIVE: {
                "success_rate": 0.45,     # 成功率权重大幅提高
                "time_efficiency": 0.25,  # 时间效率权重提高
                "risk_level": 0.05,       # 风险权重降低
                "tool_diversity": 0.03    # 工具多样性权重降低
            },
            AgentStyle.BALANCED: {
                # 保持默认权重
            }
        }
        
        # 记录初始化行为
        self._log_action(
            action_type="initialize",
            description=f"攻击Agent初始化 - 目标: {goal.value}, 风格: {style.value}",
            target_info="系统初始化",
            result="成功",
            confidence=1.0
        )
    
    def _log_action(self, 
                   action_type: str, 
                   description: str, 
                   target_info: str, 
                   result: str, 
                   confidence: float,
                   details: Optional[Dict[str, Any]] = None) -> None:
        """记录Agent行为"""
        self.action_counter += 1
        action = AgentAction(
            step=self.action_counter,
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            description=description,
            target_info=target_info,
            result=result,
            confidence=confidence,
            details=details
        )
        self.agent_actions.append(action)
        logger.info(f"Agent行为 [{action_type}] {description} - 结果: {result}")
    
    def _add_failure_memory(self,
                           target: str,
                           skill_name: str,
                           skill_type: str,
                           failure_type: str,
                           failure_reason: str,
                           detected_by: str,
                           avoidance_strategy: str) -> None:
        """添加失败记忆"""
        memory = FailureMemory(
            timestamp=datetime.now().isoformat(),
            target=target,
            skill_name=skill_name,
            skill_type=skill_type,
            failure_type=failure_type,
            failure_reason=failure_reason,
            detected_by=detected_by,
            avoidance_strategy=avoidance_strategy
        )
        self.failure_memories.append(memory)
        
        self._log_action(
            action_type="memory",
            description=f"记录失败记忆: {skill_name} - {failure_reason}",
            target_info=target,
            result="记忆保存",
            confidence=0.9,
            details={
                "skill_name": skill_name,
                "failure_type": failure_type,
                "avoidance_strategy": avoidance_strategy
            }
        )
    
    def _apply_goal_adjustments(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据攻击目标调整技能评分"""
        goal_config = self.goal_skill_mapping.get(self.goal, {})
        if not goal_config:
            return skills
        
        preferred_skills = goal_config.get("preferred_skills", [])
        preferred_focus = goal_config.get("preferred_focus", [])
        
        adjusted_skills = []
        for skill in skills:
            adjusted_skill = skill.copy()
            
            # 检查是否匹配目标偏好
            matches_goal = False
            
            # 检查技能名称
            skill_name = skill.get("name", "")
            if skill_name in preferred_skills:
                matches_goal = True
            
            # 检查技能描述
            skill_desc = skill.get("description", "")
            if any(focus in skill_desc for focus in preferred_focus):
                matches_goal = True
            
            # 调整成功率（如果匹配目标）
            if matches_goal:
                current_rate = adjusted_skill.get("success_rate", 0.5)
                bonus = goal_config.get("success_weight_bonus", 0)
                adjusted_skill["success_rate"] = min(current_rate * (1 + bonus), 0.95)
                
                # 标记为目标匹配技能
                adjusted_skill["goal_matched"] = True
        
        if adjusted_skills != skills:
            self._log_action(
                action_type="adjust",
                description=f"根据目标{self.goal.value}调整技能评分",
                target_info=f"偏好: {', '.join(preferred_focus)}",
                result=f"调整{len(adjusted_skills)}个技能",
                confidence=0.8
            )
        
        return adjusted_skills
    
    def _apply_style_adjustments(self) -> Dict[str, float]:
        """根据行为风格调整评分权重"""
        base_weights = self.decision_engine.scoring_weights.copy()
        style_adjustments = self.style_weight_adjustments.get(self.style, {})
        
        if not style_adjustments:
            return base_weights
        
        # 应用调整
        adjusted_weights = base_weights.copy()
        for category, adjustment in style_adjustments.items():
            if category in adjusted_weights:
                adjusted_weights[category] = adjustment
        
        # 归一化权重
        total = sum(adjusted_weights.values())
        if total > 0:
            for category in adjusted_weights:
                adjusted_weights[category] /= total
        
        self._log_action(
            action_type="style",
            description=f"应用行为风格'{self.style.value}'调整评分权重",
            target_info=f"权重调整: {style_adjustments}",
            result="权重调整完成",
            confidence=0.85
        )
        
        return adjusted_weights
    
    def _apply_decision_perturbation(self, scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用决策扰动（±10%）"""
        if not self.enable_perturbation:
            return scores
        
        perturbed_scores = []
        for score in scores:
            perturbed_score = score.copy()
            total_score = perturbed_score.get("total_score", 0)
            
            # 生成随机扰动（-10%到+10%）
            perturbation = random.uniform(-self.perturbation_range, self.perturbation_range)
            perturbed_total = total_score * (1 + perturbation)
            
            # 限制在0-10分之间
            perturbed_total = max(0, min(perturbed_total, 10.0))
            perturbed_score["total_score"] = round(perturbed_total, 2)
            
            # 记录扰动值
            perturbed_score["perturbation"] = round(perturbation * 100, 2)  # 百分比
            
            perturbed_scores.append(perturbed_score)
        
        if scores != perturbed_scores:
            self._log_action(
                action_type="perturbation",
                description="应用决策扰动防止模式化结果",
                target_info=f"扰动范围: ±{self.perturbation_range*100}%",
                result="扰动应用完成",
                confidence=0.7
            )
        
        return perturbed_scores
    
    def _avoid_previous_failures(self, skills: List[Dict[str, Any]], target: str) -> List[Dict[str, Any]]:
        """基于失败记忆避免重复失败"""
        if not self.failure_memories:
            return skills
        
        # 获取与该目标相关的失败记忆
        target_failures = [
            memory for memory in self.failure_memories 
            if memory.target == target
        ]
        
        if not target_failures:
            return skills
        
        filtered_skills = []
        for skill in skills:
            skill_name = skill.get("name", "")
            skill_type = skill.get("type", "")
            
            # 检查是否有相同技能的失败记录
            has_failure = any(
                memory.skill_name == skill_name or memory.skill_type == skill_type
                for memory in target_failures
            )
            
            if not has_failure:
                filtered_skills.append(skill)
            else:
                self._log_action(
                    action_type="avoidance",
                    description=f"避开已知失败技能: {skill_name}",
                    target_info=target,
                    result="技能过滤",
                    confidence=0.9
                )
        
        if len(filtered_skills) < len(skills):
            self._log_action(
                action_type="memory_use",
                description=f"基于{len(target_failures)}条失败记忆过滤技能",
                target_info=target,
                result=f"过滤掉{len(skills)-len(filtered_skills)}个技能",
               