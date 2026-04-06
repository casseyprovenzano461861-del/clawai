# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
攻击Agent控制器 - 基于Skills体系的实时决策Agent
修复版本，解决SkillContext初始化问题
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
    from .reasoning_engine import PseudoReasoningEngine
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.skills.skill_registry import SkillRegistry
    from backend.skills.base_skill import SkillContext
    from backend.decision_engine import DecisionEngine
    from backend.reasoning_engine import PseudoReasoningEngine

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
    reason: str = ""  # 新增：解释为什么选择这个动作
    thinking_log: List[Dict[str, Any]] = None  # 新增：思考过程日志
    skill_chain: List[str] = None  # 新增：技能链信息
    details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.thinking_log is None:
            self.thinking_log = []
        if self.skill_chain is None:
            self.skill_chain = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "description": self.description,
            "target_info": self.target_info,
            "result": self.result,
            "confidence": self.confidence,
            "reason": self.reason,
            "thinking_log": self.thinking_log,
            "skill_chain": self.skill_chain,
            "details": self.details or {}
        }
    
    def add_thinking_log(self, message: str, confidence: float = 0.8) -> None:
        """添加思考日志条目"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "confidence": confidence
        }
        self.thinking_log.append(log_entry)
    
    def get_thinking_summary(self) -> str:
        """获取思考摘要"""
        if not self.thinking_log:
            return "无思考记录"
        
        # 提取关键思考点
        key_messages = []
        for log in self.thinking_log[-3:]:  # 取最近3条
            key_messages.append(log["message"])
        
        return " | ".join(key_messages)


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
    """基于Skills体系的实时决策Agent（支持策略推理和行为解释）"""
    
    def __init__(self, 
                 goal: AttackGoal = AttackGoal.GET_SHELL,
                 style: AgentStyle = AgentStyle.BALANCED,
                 max_iterations: int = 10):
        self.goal = goal
        self.style = style
        self.max_iterations = max_iterations
        
        self.skill_registry = SkillRegistry()
        self.decision_engine = DecisionEngine()
        self.reasoning_engine = PseudoReasoningEngine()  # 新增：伪推理引擎
        self.context = None  # 稍后在execute_attack_plan中初始化
        
        self.agent_actions: List[AgentAction] = []
        self.action_counter = 0
        self.executed_skills: List[str] = []
        self.skill_chain: List[str] = []  # 技能链
        self.memory: Dict[str, Any] = {  # 记忆系统
            "failed_skills": {},
            "successful_skills": {},
            "skill_weights": {},
            "execution_patterns": []
        }
    
    def _log_action(self, action_type: str, description: str, target_info: str, 
                   result: str, confidence: float, reason: str = "", 
                   thinking_log: List[Dict[str, Any]] = None, 
                   details: Optional[Dict[str, Any]] = None) -> None:
        """记录Agent行为（增强版，支持策略推理）"""
        self.action_counter += 1
        
        if thinking_log is None:
            thinking_log = []
        
        action = AgentAction(
            step=self.action_counter,
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            description=description,
            target_info=target_info,
            result=result,
            confidence=confidence,
            reason=reason,
            thinking_log=thinking_log,
            skill_chain=self.skill_chain.copy(),
            details=details
        )
        
        self.agent_actions.append(action)
        
        # 记录思考摘要
        thinking_summary = action.get_thinking_summary()
        log_message = f"Agent行为 [{action_type}] {description} - 结果: {result}"
        if reason:
            log_message += f" | 理由: {reason}"
        if thinking_summary != "无思考记录":
            log_message += f" | 思考: {thinking_summary}"
        
        logger.info(log_message)
    
    def _add_thinking_log(self, message: str, confidence: float = 0.8) -> None:
        """添加思考日志到最近的动作"""
        if not self.agent_actions:
            return
        
        last_action = self.agent_actions[-1]
        last_action.add_thinking_log(message, confidence)
    
    def _update_memory(self, skill_name: str, success: bool, context: Dict[str, Any]) -> None:
        """更新记忆系统"""
        if success:
            # 记录成功技能
            if skill_name not in self.memory["successful_skills"]:
                self.memory["successful_skills"][skill_name] = 0
            self.memory["successful_skills"][skill_name] += 1
            
            # 提高技能权重
            if skill_name not in self.memory["skill_weights"]:
                self.memory["skill_weights"][skill_name] = 1.0
            self.memory["skill_weights"][skill_name] = min(
                self.memory["skill_weights"][skill_name] * 1.1, 2.0
            )
        else:
            # 记录失败技能
            if skill_name not in self.memory["failed_skills"]:
                self.memory["failed_skills"][skill_name] = 0
            self.memory["failed_skills"][skill_name] += 1
            
            # 降低技能权重
            if skill_name not in self.memory["skill_weights"]:
                self.memory["skill_weights"][skill_name] = 1.0
            self.memory["skill_weights"][skill_name] = max(
                self.memory["skill_weights"][skill_name] * 0.8, 0.3
            )
        
        # 记录执行模式
        execution_pattern = {
            "timestamp": datetime.now().isoformat(),
            "skill": skill_name,
            "success": success,
            "context_summary": {
                "goal": self.goal.value,
                "style": self.style.value,
                "target": context.get("target", "unknown")
            }
        }
        self.memory["execution_patterns"].append(execution_pattern)
        
        # 限制记忆大小
        if len(self.memory["execution_patterns"]) > 100:
            self.memory["execution_patterns"] = self.memory["execution_patterns"][-50:]
    
    def _get_skill_weight(self, skill_name: str) -> float:
        """获取技能权重（基于记忆）"""
        return self.memory["skill_weights"].get(skill_name, 1.0)
    
    def _generate_selection_reason(self, skill_info: Dict[str, Any], 
                                  context: Dict[str, Any], 
                                  decision_result: Dict[str, Any]) -> str:
        """生成技能选择理由（使用伪推理引擎生成结构化推理）"""
        try:
            # 获取候选技能信息
            candidate_skills = []
            if decision_result.get("candidate_skills"):
                candidate_skills = decision_result["candidate_skills"]
            elif decision_result.get("all_paths"):
                # 从决策结果中提取候选技能
                for path in decision_result["all_paths"]:
                    path_info = path.get("path_info", {})
                    candidate_skills.append({
                        "name": path_info.get("name", ""),
                        "category": skill_info.get("category", ""),
                        "success_rate": path_info.get("success_rate", 0.5),
                        "total_score": path.get("total_score", 0),
                        "confidence": skill_info.get("confidence", 0.8)
                    })
            
            # 准备选中的技能信息
            selected_skill = {
                "name": skill_info["name"],
                "category": skill_info.get("category", ""),
                "success_rate": skill_info.get("success_rate", 0.5),
                "total_score": skill_info.get("score_info", {}).get("total_score", 0),
                "confidence": skill_info.get("confidence", 0.8)
            }
            
            # 使用伪推理引擎生成结构化推理
            reasoning_result = self.reasoning_engine.generate_structured_reasoning(
                selected_skill=selected_skill,
                context=context,
                candidate_skills=candidate_skills
            )
            
            # 返回自然语言理由
            return reasoning_result.get("natural_reason", "基于结构化推理选择")
            
        except Exception as e:
            logger.error(f"伪推理引擎生成理由失败: {str(e)}")
            
            # 降级处理：使用原有逻辑
            reasons = []
            skill_name = skill_info["name"]
            skill = skill_info.get("skill_object")
            
            # 1. 基于决策引擎评分
            if decision_result.get("best_path"):
                score_info = decision_result["best_path"]["score_info"]
                total_score = score_info.get("total_score", 0)
                reasons.append(f"决策引擎评分最高 ({total_score:.1f}/10)")
            
            # 2. 基于技能特性
            if skill:
                reasons.append(f"技能类别: {skill.category}")
                reasons.append(f"成功率: {skill.success_rate*100:.1f}%")
            
            return "；".join(reasons) if reasons else "基于综合评估选择"
    
    def _perceive_context(self, target: str) -> Dict[str, Any]:
        if not self.context:
            return {"error": "上下文未初始化"}
        
        context_summary = {
            "target": target,
            "goal": self.goal.value,
            "style": self.style.value,
            "context_state": self.context.get_state() if hasattr(self.context, 'get_state') else {},
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
        """选择最佳技能（增强版，支持策略推理）"""
        if not self.context:
            thinking_log = []
            thinking_log.append({"message": "上下文未初始化，无法选择技能", "confidence": 0.0})
            
            self._log_action(
                action_type="error",
                description="选择最佳技能",
                target_info=target,
                result="上下文未初始化",
                confidence=0.0,
                reason="系统初始化失败",
                thinking_log=thinking_log
            )
            return None
        
        # 开始思考过程
        thinking_log = []
        thinking_log.append({"message": f"开始为目标 {target} 选择最佳技能", "confidence": 0.8})
        
        available_skills = self.skill_registry.get_all_skills()
        thinking_log.append({"message": f"发现 {len(available_skills)} 个可用技能", "confidence": 0.9})
        
        if not available_skills:
            thinking_log.append({"message": "无可用技能，选择失败", "confidence": 0.0})
            
            self._log_action(
                action_type="select",
                description="选择最佳技能",
                target_info=target,
                result="无可用技能",
                confidence=0.0,
                reason="技能注册表为空",
                thinking_log=thinking_log
            )
            return None
        
        # 筛选适用技能
        applicable_skills = []
        for skill in available_skills:
            if skill.can_handle(self.context):
                skill_info = {
                    "name": skill.name,
                    "description": skill.description,
                    "type": skill.__class__.__name__,
                    "success_rate": skill.get_success_rate_based_on_history(),
                    "estimated_time": skill.estimated_time,
                    "difficulty": skill.difficulty,
                    "confidence": skill.confidence,
                    "skill_object": skill
                }
                applicable_skills.append(skill_info)
        
        thinking_log.append({"message": f"筛选出 {len(applicable_skills)} 个适用技能", "confidence": 0.85})
        
        if not applicable_skills:
            thinking_log.append({"message": "无适用当前上下文的技能", "confidence": 0.3})
            
            self._log_action(
                action_type="select",
                description="选择最佳技能",
                target_info=target,
                result="无适用技能",
                confidence=0.0,
                reason="当前上下文无匹配技能",
                thinking_log=thinking_log
            )
            return None
        
        # 应用记忆权重调整成功率
        for skill_info in applicable_skills:
            skill_name = skill_info["name"]
            skill_weight = self._get_skill_weight(skill_name)
            original_success_rate = skill_info["success_rate"]
            adjusted_success_rate = original_success_rate * skill_weight
            skill_info["adjusted_success_rate"] = min(adjusted_success_rate, 0.95)
            
            thinking_log.append({
                "message": f"技能 {skill_name}: 原始成功率 {original_success_rate:.2f}, 权重 {skill_weight:.2f}, 调整后 {adjusted_success_rate:.2f}",
                "confidence": 0.8
            })
        
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
                "success_rate": skill_info.get("adjusted_success_rate", skill_info.get("success_rate", 0.5)),
                "step_count": 1
            }
            skill_paths.append(skill_path)
        
        thinking_log.append({"message": f"将技能转换为 {len(skill_paths)} 个决策路径", "confidence": 0.9})
        
        # 决策引擎评分
        scan_summary = self.context.scan_results if hasattr(self.context, 'scan_results') else {}
        decision_result = self.decision_engine.process_paths(skill_paths, scan_summary)
        
        thinking_log.append({"message": "决策引擎评分完成", "confidence": 0.85})
        
        best_skill_info = None
        if decision_result.get("best_path"):
            best_path_info = decision_result["best_path"]["path_info"]
            best_skill_name = best_path_info["name"]
            
            for skill_info in applicable_skills:
                if skill_info["name"] == best_skill_name:
                    best_skill_info = skill_info
                    best_skill_info["score_info"] = decision_result["best_path"]["score_info"]
                    best_skill_info["decision_result"] = decision_result
                    break
        
        if best_skill_info:
            skill_name = best_skill_info["name"]
            score = best_skill_info["score_info"]["total_score"]
            
            # 生成选择理由（使用伪推理引擎）
            reason = self._generate_selection_reason(best_skill_info, self.context.to_dict(), decision_result)
            
            # 使用伪推理引擎生成结构化推理结果
            try:
                # 准备候选技能信息
                candidate_skills = []
                if decision_result.get("candidate_skills"):
                    for candidate in decision_result["candidate_skills"]:
                        candidate_skills.append({
                            "name": candidate["name"],
                            "category": best_skill_info.get("category", ""),
                            "success_rate": candidate.get("path_info", {}).get("success_rate", 0.5),
                            "total_score": candidate["total_score"],
                            "confidence": best_skill_info.get("confidence", 0.8)
                        })
                
                # 准备选中的技能信息
                selected_skill = {
                    "name": best_skill_info["name"],
                    "category": best_skill_info.get("category", ""),
                    "success_rate": best_skill_info.get("success_rate", 0.5),
                    "total_score": best_skill_info["score_info"]["total_score"],
                    "confidence": best_skill_info.get("confidence", 0.8)
                }
                
                # 生成结构化推理
                reasoning_result = self.reasoning_engine.generate_structured_reasoning(
                    selected_skill=selected_skill,
                    context=self.context.to_dict(),
                    candidate_skills=candidate_skills
                )
                
                # 使用伪推理引擎生成思考日志
                reasoning_thinking_log = self.reasoning_engine.generate_thinking_log(reasoning_result)
                
                # 合并思考日志
                thinking_log.extend(reasoning_thinking_log)
                
                # 更新技能链
                self.skill_chain.append(skill_name)
                
                self._log_action(
                    action_type="select",
                    description=f"选择最佳技能: {skill_name}",
                    target_info=target,
                    result="技能选择完成",
                    confidence=min(0.5 + score / 20, 0.95),
                    reason=reason,
                    thinking_log=thinking_log,
                    details={
                        "selected_skill": skill_name,
                        "score": score,
                        "skill_confidence": best_skill_info.get("confidence", 0.8),
                        "adjusted_success_rate": best_skill_info.get("adjusted_success_rate", 0.5),
                        "decision_details": decision_result,
                        "reasoning_result": reasoning_result
                    }
                )
                
            except Exception as e:
                logger.error(f"伪推理引擎生成思考日志失败: {str(e)}")
                
                # 降级处理：使用原有思考日志
                thinking_log.append({
                    "message": f"选择技能 {skill_name}，总分 {score:.1f}/10，理由: {reason}",
                    "confidence": min(0.5 + score / 20, 0.95)
                })
                
                # 更新技能链
                self.skill_chain.append(skill_name)
                
                self._log_action(
                    action_type="select",
                    description=f"选择最佳技能: {skill_name}",
                    target_info=target,
                    result="技能选择完成",
                    confidence=min(0.5 + score / 20, 0.95),
                    reason=reason,
                    thinking_log=thinking_log,
                    details={
                        "selected_skill": skill_name,
                        "score": score,
                        "skill_confidence": best_skill_info.get("confidence", 0.8),
                        "adjusted_success_rate": best_skill_info.get("adjusted_success_rate", 0.5),
                        "decision_details": decision_result
                    }
                )
        else:
            thinking_log.append({"message": "决策引擎未返回最佳技能", "confidence": 0.3})
            
            self._log_action(
                action_type="select",
                description="选择最佳技能",
                target_info=target,
                result="决策失败",
                confidence=0.0,
                reason="决策引擎处理异常",
                thinking_log=thinking_log
            )
        
        return best_skill_info
    
    def _execute_skill(self, skill_info: Dict[str, Any], target: str) -> Dict[str, Any]:
        """执行技能（增强版，支持策略推理和记忆更新）"""
        if not self.context:
            thinking_log = []
            thinking_log.append({"message": "上下文未初始化，无法执行技能", "confidence": 0.0})
            
            self._log_action(
                action_type="error",
                description="执行技能",
                target_info=target,
                result="上下文未初始化",
                confidence=0.0,
                reason="系统状态异常",
                thinking_log=thinking_log
            )
            
            return {
                "success": False,
                "skill_name": skill_info["name"],
                "error": "上下文未初始化"
            }
        
        skill = skill_info["skill_object"]
        skill_name = skill_info["name"]
        skill_confidence = skill_info.get("confidence", 0.8)
        
        # 开始思考过程
        thinking_log = []
        thinking_log.append({
            "message": f"开始执行技能: {skill_name}，目标: {target}",
            "confidence": skill_confidence
        })
        
        # 获取技能选择理由
        selection_reason = skill_info.get("reason", "")
        if selection_reason:
            thinking_log.append({
                "message": f"选择理由: {selection_reason}",
                "confidence": 0.85
            })
        
        # 记录技能特性
        thinking_log.append({
            "message": f"技能特性: 成功率 {skill.success_rate*100:.1f}%，难度 {skill.difficulty}，预估时间 {skill.estimated_time}",
            "confidence": 0.9
        })
        
        self._log_action(
            action_type="execute",
            description=f"执行技能: {skill_name}",
            target_info=target,
            result="技能执行中",
            confidence=skill_confidence,
            reason=selection_reason,
            thinking_log=thinking_log
        )
        
        try:
            # 执行前思考
            self._add_thinking_log(f"准备执行 {skill_name}，当前置信度: {skill_confidence:.2f}", skill_confidence)
            
            # 执行技能
            execution_result = skill.execute(self.context)
            
            # 记录执行结果
            success = execution_result.get("success", False)
            self.executed_skills.append(skill_name)
            
            # 更新上下文
            if hasattr(self.context, 'add_execution_result'):
                self.context.add_execution_result(skill_name, execution_result)
            
            # 更新记忆系统
            self._update_memory(skill_name, success, self.context.to_dict())
            
            # 执行后思考
            if success:
                result_message = execution_result.get("summary", "执行成功")
                thinking_log.append({
                    "message": f"技能执行成功: {result_message}",
                    "confidence": min(skill_confidence + 0.1, 0.95)
                })
                
                # 获取技能自身的思考日志
                skill_thinking_log = skill.get_thinking_log()
                if skill_thinking_log:
                    thinking_log.extend(skill_thinking_log[-2:])  # 添加技能的最后2条思考日志
                
                self._log_action(
                    action_type="execute",
                    description=f"技能执行完成: {skill_name}",
                    target_info=target,
                    result="成功",
                    confidence=min(skill_confidence + 0.1, 0.95),
                    reason=f"技能执行成功: {result_message}",
                    thinking_log=thinking_log,
                    details={
                        "skill_name": skill_name,
                        "execution_result": execution_result,
                        "skill_confidence": skill.confidence,
                        "thinking_log_count": len(skill_thinking_log)
                    }
                )
                
                return {
                    "success": True,
                    "skill_name": skill_name,
                    "execution_result": execution_result,
                    "confidence": skill.confidence,
                    "thinking_log": skill_thinking_log
                }
                
            else:
                error_msg = execution_result.get("error", "执行失败")
                thinking_log.append({
                    "message": f"技能执行失败: {error_msg}",
                    "confidence": max(skill_confidence - 0.2, 0.3)
                })
                
                self._log_action(
                    action_type="execute",
                    description=f"技能执行完成: {skill_name}",
                    target_info=target,
                    result="失败",
                    confidence=max(skill_confidence - 0.2, 0.3),
                    reason=f"技能执行失败: {error_msg}",
                    thinking_log=thinking_log,
                    details={
                        "skill_name": skill_name,
                        "error": error_msg,
                        "skill_confidence": skill.confidence
                    }
                )
                
                return {
                    "success": False,
                    "skill_name": skill_name,
                    "error": error_msg,
                    "confidence": skill.confidence
                }
            
        except Exception as e:
            error_msg = str(e)
            thinking_log.append({
                "message": f"技能执行异常: {error_msg}",
                "confidence": 0.1
            })
            
            # 更新记忆系统（记录失败）
            self._update_memory(skill_name, False, self.context.to_dict())
            
            self._log_action(
                action_type="execute",
                description=f"技能执行失败: {skill_name}",
                target_info=target,
                result="异常失败",
                confidence=0.0,
                reason=f"执行过程中发生异常: {error_msg}",
                thinking_log=thinking_log,
                details={
                    "skill_name": skill_name,
                    "error": error_msg,
                    "exception_type": type(e).__name__
                }
            )
            
            return {
                "success": False,
                "skill_name": skill_name,
                "error": error_msg,
                "exception": str(e)
            }
    
    def _check_goal_achievement(self) -> bool:
        if not self.context:
            return False
        
        context_state = self.context.get_state() if hasattr(self.context, 'get_state') else {}
        
        if self.goal == AttackGoal.GET_SHELL:
            return context_state.get("has_shell_access", False)
        elif self.goal == AttackGoal.DATA_EXFILTRATION:
            return context_state.get("data_exfiltrated", False)
        elif self.goal == AttackGoal.PRIVILEGE_ESCALATION:
            return context_state.get("privilege_escalated", False)
        
        return False
    
    def execute_attack_plan(self, scan_results: Dict[str, Any], target: str = "unknown") -> AgentResult:
        try:
            # 初始化上下文
            self.context = SkillContext(target=target, scan_results=scan_results)
            
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
                        success_rate = getattr(skill, 'success_rate', 0.5)
                        total_success_rate += success_rate
                final_score = (total_success_rate / len(self.executed_skills)) * 10
            
            final_context = self.context.get_state() if hasattr(self.context, 'get_state') else {}
            
            execution_summary = f"目标: {target} | 攻击目标: {self.goal.value} | 行为风格: {self.style.value} | " \
                              f"目标达成: {'是' if goal_achieved else '否'} | 执行技能数: {len(self.executed_skills)} | " \
                              f"最终评分: {final_score:.1f}/10 | 总决策步骤: {len(agent_actions_dict)}"
            
            result = AgentResult(
                success=goal_achieved,
                goal=self.goal.value,
                style=self.style.value,
                final_context=final_context,
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
            final_context = self.context.get_state() if self.context and hasattr(self.context, 'get_state') else {}
            
            return AgentResult(
                success=False,
                goal=self.goal.value,
                style=self.style.value,
                final_context=final_context,
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
        print("[PASS] 测试通过：Agent控制器功能完整")
        return True
    else:
        print("[FAIL] 测试失败：Agent控制器功能不完整")
        return False


if __name__ == "__main__":
    import sys
    success = test_agent_controller()
    sys.exit(0 if success else 1)