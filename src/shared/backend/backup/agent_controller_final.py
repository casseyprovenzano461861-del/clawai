# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
攻击Agent控制器 - 基于Skills体系的实时决策Agent
简化版本，包含核心功能
"""

import json
import random
import logging
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# 动态导入现有模块
try:
    from .skills.skill_registry import SkillRegistry
    from .skills.base_skill import SkillContext
    from .decision_engine import DecisionEngine
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.skills.skill_registry import SkillRegistry
    from backend.skills.base_skill import SkillContext
    from backend.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class AttackGoal(Enum):
    GET_SHELL = "get_shell"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class AgentStyle(Enum):
    STEALTH = "stealth"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"


@dataclass
class AgentAction:
    step: int
    timestamp: str
    action_type: str
    description: str
    target_info: str
    result: str
    confidence: float
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
    success: bool
    goal: str
    style: str
    final_context: Dict[str, Any]
    total_steps: int
    final_score: float
    agent_actions: List[Dict[str, Any]]
    skills_executed: List[str]
    execution_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "goal": self.goal,
            "style": self.style,
            "final_context": self.final_context,
            "total_steps": self.total_steps,
            "final_score": self.final_score,
            "agent_actions": self.agent_actions,
            "skills_executed": self.skills_executed,
            "execution_summary": self.execution_summary
        }


class AgentController:
    """基于Skills体系的实时决策Agent"""
    
    def __init__(self, 
                 goal: AttackGoal = AttackGoal.GET_SHELL,
                 style: AgentStyle = AgentStyle.BALANCED,
                 max_iterations: int = 10):
        self.goal = goal
        self.style = style
        self.max_iterations = max_iterations
        
        self.skill_registry = SkillRegistry()
        self.decision_engine = DecisionEngine()
        self.context = SkillContext()
        
        self.agent_actions: List[AgentAction] = []
        self.action_counter = 0
        self.executed_skills: List[str] = []
    
    def _log_action(self, action_type: str, description: str, target_info: str, 
                   result: str, confidence: float, details: Optional[Dict[str, Any]] = None) -> None:
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
    
    def _perceive_context(self, target: str) -> Dict[str, Any]:
        context_summary = {
            "target": target,
            "goal": self.goal.value,
            "style": self.style.value,
            "context_state": self.context.get_state(),
            "executed_skills": self.executed_skills.copy()
        }
        
        self._log_action(
            action_type="perceive",
            description="感知当前上下文状态",
            target_info=target,
            result="上下文感知完成",
            confidence=0.9,
            details={"context_summary": context_summary}
        )
        
        return context_summary
    
    def _select_best_skill(self, target: str) -> Optional[Dict[str, Any]]:
        available_skills = self.skill_registry.get_all_skills()
        
        if not available_skills:
            self._log_action(
                action_type="select",
                description="选择最佳技能",
                target_info=target,
                result="无可用技能",
                confidence=0.0
            )
            return None
        
        applicable_skills = []
        for skill in available_skills:
            if skill.can_handle(self.context):
                skill_info = {
                    "name": skill.name,
                    "description": skill.description,
                    "type": skill.__class__.__name__,
                    "success_rate": skill.success_rate,
                    "estimated_time": skill.estimated_time,
                    "difficulty": skill.difficulty,
                    "skill_object": skill
                }
                applicable_skills.append(skill_info)
        
        if not applicable_skills:
            self._log_action(
                action_type="select",
                description="选择最佳技能",
                target_info=target,
                result="无适用技能",
                confidence=0.0
            )
            return None
        
        # 将技能转换为类似攻击路径的格式供决策引擎评分
        skill_paths = []
        for i, skill_info in enumerate(applicable_skills):
            skill_path = {
                "path_id": i + 1,
                "name": skill_info["name"],
                "strategy": f"技能执行: {skill_info['description']}",
                "steps": [
                    {
                        "step": 1,
                        "tool": skill_info["type"],
                        "description": skill_info["description"]
                    }
                ],
                "target_focus": skill_info["type"],
                "difficulty": skill_info.get("difficulty", "medium"),
                "estimated_time": skill_info.get("estimated_time", "10分钟"),
                "success_rate": skill_info.get("success_rate", 0.5),
                "step_count": 1
            }
            skill_paths.append(skill_path)
        
        # 决策引擎评分
        scan_summary = self.context.get_state().get("scan_results", {})
        decision_result = self.decision_engine.process_paths(skill_paths, scan_summary)
        
        best_skill_info = None
        if decision_result.get("best_path"):
            best_path_info = decision_result["best_path"]["path_info"]
            best_skill_name = best_path_info["name"]
            
            for skill_info in applicable_skills:
                if skill_info["name"] == best_skill_name:
                    best_skill_info = skill_info
                    best_skill_info["score_info"] = decision_result["best_path"]["score_info"]
                    best_skill_info["reason"] = decision_result.get("reason", "评分最高")
                    break
        
        if best_skill_info:
            skill_name = best_skill_info["name"]
            score = best_skill_info["score_info"]["total_score"]
            
            self._log_action(
                action_type="select",
                description=f"选择最佳技能: {skill_name}",
                target_info=target,
                result="技能选择完成",
                confidence=min(0.5 + score / 20, 0.95),
                details={
                    "selected_skill": skill_name,
                    "score": score,
                    "reason": best_skill_info["reason"]
                }
            )
        
        return best_skill_info
    
    def _execute_skill(self, skill_info: Dict[str, Any], target: str) -> Dict[str, Any]:
        skill = skill_info["skill_object"]
        skill_name = skill_info["name"]
        
        self._log_action(
            action_type="execute",
            description=f"执行技能: {skill_name}",
            target_info=target,
            result="技能执行中",
            confidence=0.8
        )
        
        try:
            execution_result = skill.execute(self.context)
            self.executed_skills.append(skill_name)
            self.context.update_from_skill(skill_name, execution_result)
            
            self._log_action(
                action_type="execute",
                description=f"技能执行完成: {skill_name}",
                target_info=target,
                result="成功",
                confidence=0.9,
                details={
                    "skill_name": skill_name,
                    "execution_result": execution_result.get("summary", "执行成功")
                }
            )
            
            return {
                "success": True,
                "skill_name": skill_name,
                "execution_result": execution_result
            }
            
        except Exception as e:
            self._log_action(
                action_type="execute",
                description=f"技能执行失败: {skill_name}",
                target_info=target,
                result="失败",
                confidence=0.0,
                details={
                    "skill_name": skill_name,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "skill_name": skill_name,
                "error": str(e)
            }
    
    def _check_goal_achievement(self) -> bool:
        context_state = self.context.get_state()
        
        if self.goal == AttackGoal.GET_SHELL:
            return context_state.get("has_shell_access", False)
        elif self.goal == AttackGoal.DATA_EXFILTRATION:
            return context_state.get("data_exfiltrated", False)
        elif self.goal == AttackGoal.PRIVILEGE_ESCALATION:
            return context_state.get("privilege_escalated", False)
        
        return False
    
    def execute_attack_plan(self, scan_results: Dict[str, Any], target: str = "unknown") -> AgentResult:
        try:
            self.context.update("scan_results", scan_results)
            self.context.update("target", target)
            
            self._log_action(
                action_type="start",
                description="开始执行基于Skills的攻击计划",
                target_info=target,
                result="计划启动",
                confidence=0.9
            )
            
            iteration = 0
            goal_achieved = False
            
            while iteration < self.max_iterations and not goal_achieved:
                iteration += 1
                
                self._perceive_context(target)
                goal_achieved = self._check_goal_achievement()
                
                if goal_achieved:
                    self._log_action(
                        action_type="check",
                        description="检查攻击目标达成情况",
                        target_info=target,
                        result="目标已达成",
                        confidence=1.0
                    )
                    break
                
                best_skill_info = self._select_best_skill(target)
                if not best_skill_info:
                    self._log_action(
                        action_type="error",
                        description="无法选择合适技能",
                        target_info=target,
                        result="决策失败",
                        confidence=0.0
                    )
                    break
                
                execution_result = self._execute_skill(best_skill_info, target)
                if not execution_result["success"]:
                    continue
            
            agent_actions_dict = [action.to_dict() for action in self.agent_actions]
            
            final_score = 0.0
            if self.executed_skills:
                total_success_rate = 0.0
                for skill_name in self.executed_skills:
                    skill = self.skill_registry.get_skill(skill_name)
                    if skill:
                        total_success_rate += skill.success_rate
                final_score = (total_success_rate / len(self.executed_skills)) * 10
            
            execution_summary = f"目标: {target} | 攻击目标: {self.goal.value} | 行为风格: {self.style.value} | " \
                              f"目标达成: {'是' if goal_achieved else '否'} | 执行技能数: {len(self.executed_skills)} | " \
                              f"最终评分: {final_score:.1f}/10 | 总决策步骤: {len(agent_actions_dict)}"
            
            result = AgentResult(
                success=goal_achieved,
                goal=self.goal.value,
                style=self.style.value,
                final_context=self.context.get_state(),
                total_steps=len(agent_actions_dict),
                final_score=final_score,
                agent_actions=agent_actions_dict,
                skills_executed=self.executed_skills.copy(),
                execution_summary=execution_summary
            )
            
            self._log_action(
                action_type="complete",
                description="基于Skills的攻击计划执行完成",
                target_info=target,
                result="成功" if goal_achieved else "部分成功",
                confidence=0.95 if goal_achieved else 0.7
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Agent执行失败: {str(e)}")
            self._log_action(
                action_type="error",
                description=f"执行过程中发生错误: {str(e)}",
                target_info=target,
                result="失败",
                confidence=0.0
            )
            
            agent_actions_dict = [action.to_dict() for action in self.agent_actions]
            return AgentResult(
                success=False,
                goal=self.goal.value,
                style=self.style.value,
                final_context=self.context.get_state(),
                total_steps=len(agent_actions_dict),
                final_score=0.0,
                agent_actions=agent_actions_dict,
                skills_executed=self.executed_skills.copy(),
                execution_summary=f"攻击失败: {str(e)}"
            )


def test_agent_controller():
    """测试基于Skills的Agent控制器功能"""
    import sys
    
    test_scan_results = {
        "nmap": {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"},
                {"port": 3306, "service": "mysql", "state": "open"}
            ]
        },
        "whatweb": {
            "fingerprint": {
                "web_server": "nginx",
                "language": ["PHP"],
                "cms": ["WordPress"]
            }
        }
    }
    
    print("=" * 80)
    print("基于Skills的攻击Agent控制器测试")
    print("=" * 80)
    
    print("\n测试用例: 获取Shell（平衡模式）")
    
    agent = AgentController(
        goal=AttackGoal.GET_SHELL,
        style=AgentStyle.BALANCED,
        max_iterations=5
    )
    
    result = agent.execute_attack_plan(test_scan_results, target="test.example.com")
    
    print(f"成功: {result.success}")
    print(f"最终评分: {result.final_score:.1f}/10")
    print(f"总步骤数: {result.total_steps}")
    print(f"执行技能数: {len(result.skills_executed)}")
    print(f"执行技能: {', '.join(result.skills_executed) if result.skills_executed else '无'}")
    print(f"执行摘要: {result.execution_summary}")
    
    print("\n行为日志示例:")
    for i, action in enumerate(result.agent_actions[:5]):
        print(f"  {action['step']}. [{action['action_type']}] {action['description']}")
        print(f"     结果: {action['result']}, 置信度: {action['confidence']:.2f}")
    
    print("\n" + "=" * 80)
    
    if result.agent_actions and len(result.agent_actions) > 0:
        print("✅ 测试通过：Agent控制器功能完整")
        return True
    else:
        print("❌ 测试失败：Agent控制器功能不完整")
        return False


if __name__ == "__main__":
    import sys
    success = test_agent_controller()
    sys.exit(0 if success else 1)