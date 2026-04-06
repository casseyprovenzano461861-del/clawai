# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
决策引擎 - 对攻击路径和Skills进行评分、排序并选择最佳
简化版本，支持Skills评分
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PathScore:
    """路径评分结果"""
    path_id: int
    name: str
    total_score: float
    category_scores: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_id": self.path_id,
            "name": self.name,
            "total_score": self.total_score,
            "category_scores": self.category_scores
        }


@dataclass
class AttackPath:
    """攻击路径数据模型"""
    path_id: int
    name: str
    strategy: str
    steps: List[Dict[str, Any]]
    target_focus: str
    difficulty: str
    estimated_time: str
    success_rate: float
    step_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
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
        self.scoring_weights = {
            "success_rate": 0.35,
            "time_efficiency": 0.20,
            "step_complexity": 0.15,
            "target_match": 0.15,
            "risk_level": 0.10,
            "tool_diversity": 0.05
        }
        
        self.difficulty_multiplier = {
            "easy": 1.0,
            "medium": 1.2,
            "hard": 1.5
        }
        
        self.risk_multiplier = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.3
        }
    
    def parse_time_estimate(self, time_str: str) -> float:
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
            return 30.0
    
    def calculate_time_efficiency_score(self, estimated_time: str, step_count: int) -> float:
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
        if not steps:
            return 5.0
        
        step_count = len(steps)
        
        tools_used = set()
        for step in steps:
            tool = step.get("tool", "")
            if tool:
                tools_used.add(tool)
        
        tool_diversity_score = min(len(tools_used) * 2.0, 6.0)
        
        if 3 <= step_count <= 6:
            step_count_score = 8.0
        elif step_count < 3:
            step_count_score = 5.0
        else:
            step_count_score = max(10.0 - (step_count - 6) * 0.5, 3.0)
        
        total_score = (tool_diversity_score + step_count_score) / 2
        
        return round(total_score, 2)
    
    def calculate_target_match_score(self, target_focus: str, scan_summary: Dict[str, Any]) -> float:
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
        base_risk = self.risk_multiplier.get(difficulty, 1.0)
        risk_adjustment = (1.0 - success_rate) * 2.0
        total_risk = base_risk + risk_adjustment
        risk_score = 10.0 - min(total_risk * 3.0, 9.0)
        
        return round(risk_score, 2)
    
    def calculate_tool_diversity_score(self, steps: List[Dict[str, Any]]) -> float:
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
        
        return PathScore(
            path_id=path.path_id,
            name=path.name,
            total_score=total_score,
            category_scores=category_scores
        )
    
    def rank_paths(self, scored_paths: List[PathScore]) -> List[PathScore]:
        return sorted(scored_paths, key=lambda x: x.total_score, reverse=True)
    
    def select_best_path(self, ranked_paths: List[PathScore], all_paths: List[AttackPath]) -> Dict[str, Any]:
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
        
        reason = f"总分最高 ({best_scored_path.total_score:.1f}/10)"
        
        confidence = best_scored_path.total_score / 10.0
        if len(ranked_paths) > 1:
            second_best = ranked_paths[1]
            score_gap = best_scored_path.total_score - second_best.total_score
            if score_gap >= 2.0:
                confidence += 0.15
            elif score_gap >= 1.0:
                confidence += 0.10
            elif score_gap >= 0.5:
                confidence += 0.05
        
        confidence = max(0.5, min(confidence, 0.95))
        
        comparison = []
        for i, other_path in enumerate(ranked_paths[1:4], start=2):
            if other_path.path_id == best_scored_path.path_id:
                continue
            
            score_gap = best_scored_path.total_score - other_path.total_score
            comparison.append({
                "path_id": other_path.path_id,
                "name": other_path.name,
                "rank": i,
                "score": other_path.total_score,
                "score_gap": round(score_gap, 2)
            })
        
        result = {
            "best_path": {
                "path_info": best_path.to_dict() if best_path else {},
                "score_info": best_scored_path.to_dict()
            },
            "reason": reason,
            "confidence": round(confidence, 2),
            "comparison": comparison,
            "ranking_summary": {
                "total_paths": len(ranked_paths),
                "score_range": f"{ranked_paths[-1].total_score:.1f}-{ranked_paths[0].total_score:.1f}"
            }
        }
        
        return result
    
    def process_paths(self, attack_paths: List[Dict[str, Any]], scan_summary: Dict[str, Any]) -> Dict[str, Any]:
        try:
            paths = []
            for path_data in attack_paths:
                path = AttackPath(
                    path_id=path_data.get("path_id", 0),
                    name=path_data.get("name", "未知路径"),
                    strategy=path_data.get("strategy", ""),
                    steps=path_data.get("steps", []),
                    target_focus=path_data.get("target_focus", ""),
                    difficulty=path_data.get("difficulty", "medium"),
                    estimated_time=path_data.get("estimated_time", "30分钟"),
                    success_rate=path_data.get("success_rate", 0.5),
                    step_count=path_data.get("step_count", len(path_data.get("steps", [])))
                )
                paths.append(path)
            
            scored_paths = []
            for path in paths:
                score = self.score_path(path, scan_summary)
                scored_paths.append(score)
            
            ranked_paths = self.rank_paths(scored_paths)
            result = self.select_best_path(ranked_paths, paths)
            
            result["all_scores"] = [score.to_dict() for score in ranked_paths]
            result["scoring_weights"] = self.scoring_weights
            result["total_paths_processed"] = len(paths)
            
            return result
            
        except Exception as e:
            logger.error(f"决策引擎处理失败: {str(e)}")
            return {
                "error": f"决策引擎处理失败: {str(e)}",
                "best_path": None,
                "reason": "处理过程中发生错误",
                "confidence": 0.0,
                "comparison": []
            }


def test_decision_engine():
    """测试决策引擎功能"""
    test_scan_summary = {
        "web_ports": ["80", "443"],
        "database_ports": ["3306"],
        "critical_vulns": [{"name": "RCE漏洞", "severity": "critical"}]
    }
    
    test_attack_paths = [
        {
            "path_id": 1,
            "name": "全面Web应用攻击",
            "strategy": "Web应用渗透测试",
            "steps": [
                {"step": 1, "tool": "nmap", "description": "端口扫描"},
                {"step": 2, "tool": "whatweb", "description": "技术栈识别"},
                {"step": 3, "tool": "nuclei", "description": "漏洞扫描"},
                {"step": 4, "tool": "sqlmap", "description": "SQL注入检测"}
            ],
            "target_focus": "Web服务",
            "difficulty": "medium",
            "estimated_time": "12分钟",
            "success_rate": 0.75,
            "step_count": 4
        },
        {
            "path_id": 2,
            "name": "快速Web安全评估",
            "strategy": "快速安全扫描",
            "steps": [
                {"step": 1, "tool": "nmap", "description": "快速端口扫描"},
                {"step": 2, "tool": "whatweb", "description": "基础技术栈识别"}
            ],
            "target_focus": "Web服务",
            "difficulty": "easy",
            "estimated_time": "6分钟",
            "success_rate": 0.85,
            "step_count": 2
        }
    ]
    
    print("=" * 80)
    print("决策引擎测试")
    print("=" * 80)
    
    engine = DecisionEngine()
    result = engine.process_paths(test_attack_paths, test_scan_summary)
    
    print("\n决策结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    
    if result.get("best_path") and result.get("reason"):
        print("✅ 测试通过：决策引擎功能完整")
        return True
    else:
        print("❌ 测试失败：决策引擎功能不完整")
        return False


if __name__ == "__main__":
    import sys
    success = test_decision_engine()
    sys.exit(0 if success else 1)