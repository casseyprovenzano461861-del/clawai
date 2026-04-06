# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
决策引擎 - 对攻击路径和Skills进行评分、排序并选择最佳
优化版本：支持Skills评分，解决代码冗余问题
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import math

logger = logging.getLogger(__name__)


@dataclass
class PathScore:
    """路径评分结果"""
    path_id: int
    name: str
    total_score: float
    category_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path_id": self.path_id,
            "name": self.name,
            "total_score": self.total_score,
            "category_scores": self.category_scores,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvement_suggestions": self.improvement_suggestions
        }


@dataclass
class AttackPath:
    """攻击路径数据模型"""
    path_id: int
    name: str
    strategy: str
    steps: List[Dict[str, Any]]
    target_focus: str
    difficulty: str  # easy, medium, hard
    estimated_time: str
    success_rate: float
    step_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path_id": self.path_id,
            "name": self.name,
            "strategy": self.strategy,
            "steps": self.steps,
            "target_focus": self.target_focus,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "success_rate": self.success_rate,
            "step_count": self.step_count
        }


class DecisionEngine:
    """决策引擎 - 负责路径和Skills评分、排序和最佳选择"""
    
    def __init__(self):
        # 评分权重配置
        self.scoring_weights = {
            "success_rate": 0.35,      # 成功率权重
            "time_efficiency": 0.20,   # 时间效率权重
            "step_complexity": 0.15,   # 步骤复杂度权重
            "target_match": 0.15,      # 目标匹配度权重
            "risk_level": 0.10,        # 风险等级权重
            "tool_diversity": 0.05     # 工具多样性权重
        }
        
        # 难度系数映射
        self.difficulty_multiplier = {
            "easy": 1.0,
            "medium": 1.2,
            "hard": 1.5
        }
        
        # 风险系数（难度越高，风险系数越高）
        self.risk_multiplier = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.3
        }
        
        # Skills类型映射到目标焦点
        self.skill_type_to_focus = {
            "NmapScanSkill": "全面侦察",
            "WhatWebSkill": "Web技术栈识别",
            "SQLInjectionSkill": "数据库渗透",
            "RCESkill": "远程代码执行",
            "PrivilegeEscalationSkill": "权限提升"
        }
    
    def parse_time_estimate(self, time_str: str) -> float:
        """解析时间估计字符串为分钟数"""
        try:
            time_str = time_str.lower().replace(" ", "")
            
            if "小时" in time_str and "分钟" in time_str:
                parts = time_str.split("小时")
                hours = int(parts[0])
                minutes = int(parts[1].replace("分钟", ""))
                return hours * 60 + minutes
            elif "小时" in time_str:
                hours = int(time_str.replace("小时", ""))
                return hours * 60
            elif "分钟" in time_str:
                minutes = int(time_str.replace("分钟", ""))
                return minutes
            else:
                return 30.0
        except (ValueError, AttributeError):
            logger.warning(f"无法解析时间字符串: {time_str}")
            return 30.0
    
    def calculate_time_efficiency_score(self, estimated_time: str, step_count: int) -> float:
        """计算时间效率得分"""
        total_minutes = self.parse_time_estimate(estimated_time)
        
        if total_minutes <= 0:
            return 5.0
        
        steps_per_minute = step_count / total_minutes
        
        if steps_per_minute >= 0.8:
            return 9.0
        elif steps_per_minute >= 0.5:
            return 7.5
        elif steps_per_minute >= 0.3:
            return 6.0
        elif steps_per_minute >= 0.1:
            return 4.0
        else:
            return 2.0
    
    def calculate_step_complexity_score(self, steps: List[Dict[str, Any]]) -> float:
        """计算步骤复杂度得分"""
        if not steps:
            return 5.0
        
        step_count = len(steps)
        
        tools_used = set()
        tool_categories = {
            "reconnaissance": ["nmap", "whatweb", "gobuster"],
            "vulnerability": ["nuclei", "nikto"],
            "exploitation": ["sqlmap", "metasploit", "hydra"],
            "post_exploitation": ["post", "linpeas", "winpeas", "mimikatz"]
        }
        
        categories_covered = set()
        
        for step in steps:
            tool = step.get("tool", "")
            tools_used.add(tool)
            
            for category, category_tools in tool_categories.items():
                if any(tool.startswith(cat_tool) or cat_tool in tool.lower() for cat_tool in category_tools):
                    categories_covered.add(category)
        
        tool_diversity_score = min(len(tools_used) * 2.0, 6.0)
        category_coverage_score = len(categories_covered) * 1.0
        
        if 3 <= step_count <= 6:
            step_count_score = 8.0
        elif step_count < 3:
            step_count_score = 5.0
        else:
            step_count_score = max(10.0 - (step_count - 6) * 0.5, 3.0)
        
        total_score = (tool_diversity_score + category_coverage_score + step_count_score) / 3
        
        return round(total_score, 2)
    
    def calculate_target_match_score(self, target_focus: str, scan_summary: Dict[str, Any]) -> float:
        """计算目标匹配度得分"""
        focus_map = {
            "Web服务": 8.0,
            "数据库服务": 7.0,
            "特定漏洞利用": 9.0,
            "Web应用数据库": 7.5,
            "全面侦察": 6.0,
            "综合目标": 5.0,
            "Web技术栈识别": 7.0,
            "数据库渗透": 8.0,
            "远程代码执行": 9.0,
            "权限提升": 8.5
        }
        
        base_score = focus_map.get(target_focus, 6.0)
        
        if "web_ports" in scan_summary and scan_summary["web_ports"]:
            if target_focus in ["Web服务", "Web应用数据库", "Web技术栈识别"]:
                base_score += 1.0
        
        if "database_ports" in scan_summary and scan_summary["database_ports"]:
            if target_focus in ["数据库服务", "Web应用数据库", "数据库渗透"]:
                base_score += 1.0
        
        if "critical_vulns" in scan_summary and scan_summary["critical_vulns"]:
            if target_focus in ["特定漏洞利用", "远程代码执行", "权限提升"]:
                base_score += 1.5
        
        return round(min(max(base_score, 0.0), 10.0), 2)
    
    def calculate_risk_score(self, difficulty: str, success_rate: float) -> float:
        """计算风险得分（风险越低得分越高）"""
        base_risk = self.risk_multiplier.get(difficulty, 1.0)
        risk_adjustment = (1.0 - success_rate) * 2.0
        total_risk = base_risk + risk_adjustment
        risk_score = 10.0 - min(total_risk * 3.0, 9.0)
        
        return round(risk_score, 2)
    
    def calculate_tool_diversity_score(self, steps: List[Dict[str, Any]]) -> float:
        """计算工具多样性得分"""
        if not steps:
            return 5.0
        
        tools_used = set()
        for step in steps:
            tool = step.get("tool", "")
            if tool:
                tools_used.add(tool)
        
        unique_tools = len(tools_used)
        
        if unique_tools >= 5:
            return 9.0
        elif unique_tools == 4:
            return 8.0
        elif unique_tools == 3:
            return 7.0
        elif unique_tools == 2:
            return 5.0
        elif unique_tools == 1:
            return 3.0
        else:
            return 1.0
    
    def score_path(self, path: AttackPath, scan_summary: Dict[str, Any]) -> PathScore:
        """对单个攻击路径进行评分"""
        success_rate_score = path.success_rate * 10.0
        
        time_efficiency_score = self.calculate_time_efficiency_score(
            path.estimated_time, path.step_count
        )
        
        step_complexity_score = self.calculate_step_complexity_score(path.steps)
        
        target_match_score = self.calculate_target_match_score(
            path.target_focus, scan_summary
        )
        
        risk_score = self.calculate_risk_score(path.difficulty, path.success_rate)
        
        tool_diversity_score = self.calculate_tool_diversity_score(path.steps)
        
        category_scores = {
            "success_rate": success_rate_score,
            "time_efficiency": time_efficiency_score,
            "step_complexity": step_complexity_score,
            "target_match": target_match_score,
            "risk_level": risk_score,
            "tool_diversity": tool_diversity_score
        }
        
        total_score = 0.0
        for category, score in category_scores.items():
            weight = self.scoring_weights[category]
            total_score += score * weight
        
        difficulty_mult = self.difficulty_multiplier.get(path.difficulty, 1.0)
        total_score *= difficulty_mult
        
        total_score = round(min(max(total_score, 0.0), 10.0), 2)
        
        strengths, weaknesses = self._analyze_strengths_weaknesses(category_scores)
        
        improvement_suggestions = self._generate_improvement_suggestions(
            category_scores, path
        )
        
        return PathScore(
            path_id=path.path_id,
            name=path.name,
            total_score=total_score,
            category_scores=category_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=improvement_suggestions
        )
    
    def _analyze_strengths_weaknesses(self, category_scores: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """分析强项和弱项"""
        strengths = []
        weaknesses = []
        
        thresholds = {
            "success_rate": 7.0,
            "time_efficiency": 6.0,
            "step_complexity": 6.0,
            "target_match": 6.0,
            "risk_level": 6.0,
            "tool_diversity": 5.0
        }
        
        descriptions = {
            "success_rate": "成功率",
            "time_efficiency": "时间效率",
            "step_complexity": "步骤复杂度",
            "target_match": "目标匹配度",
            "risk_level": "风险控制",
            "tool_diversity": "工具多样性"
        }
        
        for category, score in category_scores.items():
            threshold = thresholds[category]
            description = descriptions[category]
            
            if score >= threshold + 1.5:
                strengths.append(f"{description}优秀 ({score:.1f}/10)")
            elif score >= threshold:
                strengths.append(f"{description}良好 ({score:.1f}/10)")
            elif score >= threshold - 1.0:
                pass
            else:
                weaknesses.append(f"{description}需改进 ({score:.1f}/10)")
        
        return strengths[:3], weaknesses[:3]
    
    def _generate_improvement_suggestions(self, category_scores: Dict[str, float], path: AttackPath) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if category_scores["success_rate"] < 6.0:
            suggestions.append("考虑增加成功率更高的工具或步骤")
        
        if category_scores["time_efficiency"] < 5.0:
            suggestions.append("优化步骤顺序，减少等待时间")
        
        if category_scores["step_complexity"] < 5.0:
            if path.step_count > 8:
                suggestions.append("步骤过多，建议合并相关步骤")
            elif path.step_count < 3:
                suggestions.append("步骤过少，可能遗漏关键环节")
        
        if category_scores["target_match"] < 5.0:
            suggestions.append("重新评估目标焦点，优化攻击策略")
        
        if category_scores["risk_level"] < 5.0:
            suggestions.append("增加隐蔽性步骤，降低被检测风险")
        
        if category_scores["tool_diversity"] < 4.0:
            suggestions.append("增加不同类别的工具，提高攻击维度")
        
        return suggestions[:3]
    
    def rank_paths(self, scored_paths: List[PathScore]) -> List[PathScore]:
        """对评分后的路径进行排序"""
        sorted_paths = sorted(scored_paths, key=lambda x: x.total_score, reverse=True)
        
        for i, path in enumerate(sorted_paths):
            path.rank = i + 1
        
        return sorted_paths
    
    def select_best_path(self, ranked_paths: List[PathScore], all_paths: List[AttackPath]) -> Dict[str, Any]:
        """选择最佳路径并生成详细理由"""
        if not ranked_paths:
            return {
                "best_path": None,
                "reason": "无可用路径",
                "confidence": 0.0,
                "comparison": []
            }
        
        best_scored_path = ranked_paths[0]
        
        best_path = None
        for path in all_paths:
            if path.path_id == best_scored_path.path_id:
                best_path = path
                break
        
        if not best_path:
            best_path = all_paths[0] if all_paths else None
        
        reason = self._generate_selection_reason(best_scored_path, ranked_paths)
        confidence = self._calculate_confidence(best_scored_path, ranked_paths)
        comparison = self._generate_comparison(best_scored_path, ranked_paths)
        
        result = {
            "best_path": {
                "path_info": best_path.to_dict() if best_path else {},
                "score_info": best_scored_path.to_dict()
            },
            "reason": reason,
            "confidence": confidence,
            "comparison": comparison,
            "ranking_summary": {
                "total_paths": len(ranked_paths),
                "score_range": f"{ranked_paths[-1].total_score:.1f}-{ranked_paths[0].total_score:.1f}",
                "score_gap": f"{ranked_paths[0].total_score - ranked_paths[1].total_score:.1f}" if len(ranked_paths) > 1 else "0.0"
            }
        }
        
        return result
    
    def _generate_selection_reason(self, best_path: PathScore, ranked_paths: List[PathScore]) -> str:
        """生成选择理由"""
        reasons = []
        
        reasons.append(f"总分最高 ({best_path.total_score:.1f}/10)")
        
        if best_path.strengths:
            top_strength = best_path.strengths[0]
            reasons.append(f"强项突出: {top_strength}")
        
        if len(ranked_paths) > 1:
            second_best = ranked_paths[1]
            score_gap = best_path.total_score - second_best.total_score
            if score_gap >= 1.0:
                reasons.append(f"显著领先第二名 {score_gap:.1f} 分")
            elif score_gap >= 0.5:
                reasons.append(f"略微领先第二名 {score_gap:.1f} 分")
        
        if "风险控制" in " ".join(best_path.strengths):
            reasons.append("风险控制优秀，攻击稳定性高")
        
        return "；".join(reasons)
    
    def _calculate_confidence(self, best_path: PathScore, ranked_paths: List[PathScore]) -> float:
        """计算置信度"""
        base_confidence = best_path.total_score /