# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
多规则引擎协同决策系统
支持规则引擎投票机制、置信度加权决策和分歧解决策略
⚠️ 技术诚信说明：本模块使用规则引擎而非真正的AI/机器学习系统
"""

import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class DecisionStatus(Enum):
    """决策状态"""
    CONSENSUS = "consensus"  # 一致同意
    MAJORITY = "majority"   # 多数同意
    SPLIT = "split"         # 分歧
    FAILED = "failed"       # 决策失败


class ModelConfidence(Enum):
    """模型置信度级别"""
    HIGH = "high"      # 高置信度 (0.8-1.0)
    MEDIUM = "medium"  # 中置信度 (0.6-0.8)
    LOW = "low"        # 低置信度 (0.0-0.6)


@dataclass
class ModelDecision:
    """单个模型的决策"""
    model_name: str
    decision: str
    confidence: float  # 0.0-1.0
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def confidence_level(self) -> ModelConfidence:
        """获取置信度级别"""
        if self.confidence >= 0.8:
            return ModelConfidence.HIGH
        elif self.confidence >= 0.6:
            return ModelConfidence.MEDIUM
        else:
            return ModelConfidence.LOW


@dataclass
class DecisionResult:
    """决策结果"""
    final_decision: str
    status: DecisionStatus
    confidence: float
    voting_summary: Dict[str, Any]
    model_decisions: List[ModelDecision]
    resolution_strategy: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "final_decision": self.final_decision,
            "status": self.status.value,
            "confidence": self.confidence,
            "voting_summary": self.voting_summary,
            "model_decisions": [
                {
                    "model_name": d.model_name,
                    "decision": d.decision,
                    "confidence": d.confidence,
                    "reasoning": d.reasoning[:200] + "..." if len(d.reasoning) > 200 else d.reasoning,
                    "confidence_level": d.confidence_level().value
                }
                for d in self.model_decisions
            ],
            "resolution_strategy": self.resolution_strategy,
            "timestamp": self.timestamp
        }


class MultiModelDecisionSystem:
    """
    多规则引擎协同决策系统
    支持规则引擎投票、加权决策和分歧解决
    ⚠️ 技术诚信说明：使用规则引擎决策而非真正的AI模型
    """
    
    def __init__(self, consensus_threshold: float = 0.7, majority_threshold: float = 0.5):
        """
        初始化多模型决策系统
        
        Args:
            consensus_threshold: 共识阈值 (0.0-1.0)
            majority_threshold: 多数阈值 (0.0-1.0)
        """
        self.consensus_threshold = consensus_threshold
        self.majority_threshold = majority_threshold
        self.decision_history = []
        
        # 模型权重配置（可根据历史性能动态调整）
        self.model_weights = {
            "deepseek": 1.0,
            "openai": 0.9,
            "claude": 0.8,
            "local": 0.6
        }
    
    def make_decision(self, model_decisions: List[ModelDecision]) -> DecisionResult:
        """
        基于多个模型决策进行协同决策
        
        Args:
            model_decisions: 多个模型的决策列表
            
        Returns:
            协同决策结果
        """
        if not model_decisions:
            return self._create_failed_decision("没有模型决策输入")
        
        # 检查决策一致性
        decision_counts = self._count_decisions(model_decisions)
        
        # 计算加权决策
        weighted_decision = self._calculate_weighted_decision(model_decisions)
        
        # 分析决策状态
        status, confidence, strategy = self._analyze_decision_status(
            decision_counts, weighted_decision, model_decisions
        )
        
        # 确定最终决策
        final_decision = self._determine_final_decision(
            status, decision_counts, weighted_decision
        )
        
        # 创建决策结果
        result = DecisionResult(
            final_decision=final_decision,
            status=status,
            confidence=confidence,
            voting_summary=decision_counts,
            model_decisions=model_decisions,
            resolution_strategy=strategy
        )
        
        # 记录决策历史
        self.decision_history.append(result)
        
        return result
    
    def _count_decisions(self, model_decisions: List[ModelDecision]) -> Dict[str, Any]:
        """统计各个决策的票数和置信度"""
        decision_map = {}
        
        for md in model_decisions:
            decision = md.decision
            if decision not in decision_map:
                decision_map[decision] = {
                    "count": 0,
                    "total_confidence": 0.0,
                    "models": []
                }
            
            decision_map[decision]["count"] += 1
            decision_map[decision]["total_confidence"] += md.confidence
            decision_map[decision]["models"].append({
                "name": md.model_name,
                "confidence": md.confidence
            })
        
        # 计算平均置信度
        for decision in decision_map.values():
            decision["average_confidence"] = (
                decision["total_confidence"] / decision["count"]
                if decision["count"] > 0 else 0.0
            )
        
        # 按票数排序
        sorted_decisions = sorted(
            decision_map.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        return {
            "total_models": len(model_decisions),
            "decision_distribution": {
                decision: info for decision, info in sorted_decisions
            },
            "top_decision": sorted_decisions[0][0] if sorted_decisions else None,
            "top_count": sorted_decisions[0][1]["count"] if sorted_decisions else 0
        }
    
    def _calculate_weighted_decision(self, model_decisions: List[ModelDecision]) -> Dict[str, Any]:
        """计算加权决策"""
        decision_scores = {}
        
        for md in model_decisions:
            # 获取模型权重
            weight = self.model_weights.get(md.model_name, 0.5)
            
            # 计算加权分数 (置信度 * 模型权重)
            weighted_score = md.confidence * weight
            
            if md.decision not in decision_scores:
                decision_scores[md.decision] = {
                    "weighted_score": 0.0,
                    "total_weight": 0.0,
                    "models": []
                }
            
            decision_scores[md.decision]["weighted_score"] += weighted_score
            decision_scores[md.decision]["total_weight"] += weight
            decision_scores[md.decision]["models"].append(md.model_name)
        
        # 计算归一化分数
        normalized_scores = {}
        for decision, scores in decision_scores.items():
            total_possible_weight = sum(
                self.model_weights.get(model, 0.5)
                for model in scores["models"]
            )
            
            if total_possible_weight > 0:
                normalized_score = scores["weighted_score"] / total_possible_weight
            else:
                normalized_score = 0.0
            
            normalized_scores[decision] = {
                "score": normalized_score,
                "weighted_score": scores["weighted_score"],
                "models": scores["models"]
            }
        
        # 找出最高分数的决策
        if normalized_scores:
            best_decision = max(normalized_scores.items(), key=lambda x: x[1]["score"])
            return {
                "best_decision": best_decision[0],
                "best_score": best_decision[1]["score"],
                "all_scores": normalized_scores
            }
        else:
            return {
                "best_decision": None,
                "best_score": 0.0,
                "all_scores": {}
            }
    
    def _analyze_decision_status(
        self, 
        decision_counts: Dict[str, Any],
        weighted_decision: Dict[str, Any],
        model_decisions: List[ModelDecision]
    ) -> Tuple[DecisionStatus, float, str]:
        """分析决策状态"""
        total_models = decision_counts["total_models"]
        top_count = decision_counts["top_count"]
        top_decision = decision_counts["top_decision"]
        
        # 计算共识比例
        consensus_ratio = top_count / total_models if total_models > 0 else 0.0
        
        # 检查是否达成共识
        if consensus_ratio >= self.consensus_threshold:
            # 计算共识决策的平均置信度
            consensus_confidence = self._calculate_consensus_confidence(
                top_decision, model_decisions
            )
            return DecisionStatus.CONSENSUS, consensus_confidence, "consensus_voting"
        
        # 检查是否达成多数
        elif consensus_ratio >= self.majority_threshold:
            majority_confidence = self._calculate_majority_confidence(
                top_decision, model_decisions
            )
            return DecisionStatus.MAJORITY, majority_confidence, "majority_voting"
        
        # 分歧情况
        else:
            # 使用加权决策
            best_score = weighted_decision.get("best_score", 0.0)
            best_decision = weighted_decision.get("best_decision")
            
            if best_decision and best_score > 0.5:
                # 加权决策有足够置信度
                return DecisionStatus.SPLIT, best_score, "weighted_decision"
            else:
                # 无法达成有效决策
                return DecisionStatus.FAILED, 0.0, "failed_to_resolve"
    
    def _calculate_consensus_confidence(
        self, 
        decision: str, 
        model_decisions: List[ModelDecision]
    ) -> float:
        """计算共识决策的平均置信度"""
        relevant_decisions = [
            md for md in model_decisions 
            if md.decision == decision
        ]
        
        if not relevant_decisions:
            return 0.0
        
        total_confidence = sum(md.confidence for md in relevant_decisions)
        return total_confidence / len(relevant_decisions)
    
    def _calculate_majority_confidence(
        self, 
        decision: str, 
        model_decisions: List[ModelDecision]
    ) -> float:
        """计算多数决策的加权平均置信度"""
        relevant_decisions = [
            md for md in model_decisions 
            if md.decision == decision
        ]
        
        if not relevant_decisions:
            return 0.0
        
        # 加权平均（考虑模型权重）
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for md in relevant_decisions:
            weight = self.model_weights.get(md.model_name, 0.5)
            weighted_sum += md.confidence * weight
            weight_sum += weight
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def _determine_final_decision(
        self,
        status: DecisionStatus,
        decision_counts: Dict[str, Any],
        weighted_decision: Dict[str, Any]
    ) -> str:
        """确定最终决策"""
        if status == DecisionStatus.FAILED:
            return "无法达成有效决策"
        
        if status in [DecisionStatus.CONSENSUS, DecisionStatus.MAJORITY]:
            return decision_counts["top_decision"]
        
        if status == DecisionStatus.SPLIT:
            return weighted_decision.get("best_decision", "加权决策失败")
        
        return "未知决策状态"
    
    def _create_failed_decision(self, reason: str) -> DecisionResult:
        """创建失败的决策结果"""
        return DecisionResult(
            final_decision=f"决策失败: {reason}",
            status=DecisionStatus.FAILED,
            confidence=0.0,
            voting_summary={"error": reason},
            model_decisions=[],
            resolution_strategy="failed"
        )
    
    def analyze_decision_quality(self, decision_result: DecisionResult) -> Dict[str, Any]:
        """分析决策质量"""
        # 计算决策一致性指标
        decisions = [md.decision for md in decision_result.model_decisions]
        unique_decisions = set(decisions)
        
        # 计算熵（不确定性度量）
        if len(decisions) > 0:
            from collections import Counter
            import math
            counts = Counter(decisions)
            total = len(decisions)
            entropy = -sum(
                (count/total) * math.log2(count/total)
                for count in counts.values()
            )
        else:
            entropy = 0.0
        
        # 计算平均置信度
        avg_confidence = statistics.mean(
            [md.confidence for md in decision_result.model_decisions]
        ) if decision_result.model_decisions else 0.0
        
        # 计算置信度方差
        if len(decision_result.model_decisions) > 1:
            confidence_variance = statistics.variance(
                [md.confidence for md in decision_result.model_decisions]
            )
        else:
            confidence_variance = 0.0
        
        return {
            "decision_entropy": round(entropy, 4),
            "average_confidence": round(avg_confidence, 4),
            "confidence_variance": round(confidence_variance, 4),
            "unique_decisions": len(unique_decisions),
            "total_models": len(decision_result.model_decisions),
            "decision_status": decision_result.status.value,
            "final_confidence": round(decision_result.confidence, 4)
        }
    
    def update_model_weights(self, performance_data: Dict[str, Any]):
        """
        根据模型性能动态更新模型权重
        
        Args:
            performance_data: 模型性能数据，包含每个模型的历史成功率、响应时间等
        """
        for model_name, performance in performance_data.items():
            if model_name in self.model_weights:
                # 根据成功率调整权重
                success_rate = performance.get("success_rate", 0.5)
                avg_response_time = performance.get("avg_response_time", 10.0)
                
                # 计算新权重（成功率越高、响应时间越短，权重越高）
                time_factor = max(0.1, 1.0 / (avg_response_time / 5.0))  # 基准响应时间5秒
                new_weight = success_rate * time_factor
                
                # 平滑更新
                old_weight = self.model_weights[model_name]
                self.model_weights[model_name] = 0.7 * old_weight + 0.3 * new_weight
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        recent_history = self.decision_history[-limit:] if self.decision_history else []
        return [result.to_dict() for result in recent_history]


# 测试函数
def test_multi_model_decision():
    """测试多规则引擎决策系统"""
    print("=" * 80)
    print("多规则引擎协同决策系统测试")
    print("=" * 80)
    
    # 创建决策系统
    decision_system = MultiModelDecisionSystem()
    
    # 测试用例1：共识决策
    print("\n测试用例1: 共识决策")
    consensus_decisions = [
        ModelDecision(
            model_name="deepseek",
            decision="rce_attack",
            confidence=0.85,
            reasoning="检测到严重RCE漏洞，攻击成功率高"
        ),
        ModelDecision(
            model_name="openai",
            decision="rce_attack",
            confidence=0.78,
            reasoning="存在远程代码执行漏洞，建议优先利用"
        ),
        ModelDecision(
            model_name="claude",
            decision="rce_attack",
            confidence=0.82,
            reasoning="RCE漏洞严重性高，攻击路径明确"
        )
    ]
    
    result1 = decision_system.make_decision(consensus_decisions)
    print(f"最终决策: {result1.final_decision}")
    print(f"决策状态: {result1.status.value}")
    print(f"置信度: {result1.confidence:.2f}")
    print(f"解决策略: {result1.resolution_strategy}")
    
    # 分析决策质量
    quality1 = decision_system.analyze_decision_quality(result1)
    print(f"决策质量: {quality1}")
    
    # 测试用例2：分歧决策
    print("\n测试用例2: 分歧决策")
    split_decisions = [
        ModelDecision(
            model_name="deepseek",
            decision="rce_attack",
            confidence=0.88,
            reasoning="严重RCE漏洞，攻击成功率高"
        ),
        ModelDecision(
            model_name="openai",
            decision="sql_injection",
            confidence=0.72,
            reasoning="存在SQL注入漏洞，隐蔽性更好"
        ),
        ModelDecision(
            model_name="claude",
            decision="rce_attack",
            confidence=0.65,
            reasoning="RCE漏洞但存在一定风险"
        ),
        ModelDecision(
            model_name="local",
            decision="sql_injection",
            confidence=0.55,
            reasoning="SQL注入技术成熟，风险可控"
        )
    ]
    
    result2 = decision_system.make_decision(split_decisions)
    print(f"最终决策: {result2.final_decision}")
    print(f"决策状态: {result2.status.value}")
    print(f"置信度: {result2.confidence:.2f}")
    print(f"解决策略: {result2.resolution_strategy}")
    
    # 测试用例3：加权决策（模型权重不同）
    print("\n测试用例3: 加权决策")
    
    # 调整模型权重
    decision_system.model_weights = {
        "deepseek": 1.0,   # 高权重
        "openai": 0.7,     # 中等权重
        "claude": 0.5,     # 低权重
        "local": 0.3       # 最低权重
    }
    
    weighted_decisions = [
        ModelDecision(
            model_name="deepseek",
            decision="web_shell",
            confidence=0.75,
            reasoning="WebShell上传可行，隐蔽性高"
        ),
        ModelDecision(
            model_name="openai",
            decision="credential_stuffing",
            confidence=0.82,
            reasoning="弱密码攻击，成功率较高"
        ),
        ModelDecision(
            model_name="claude",
            decision="web_shell",
            confidence=0.68,
            reasoning="文件上传漏洞可利用"
        )
    ]
    
    result3 = decision_system.make_decision(weighted_decisions)
    print(f"最终决策: {result3.final_decision}")
    print(f"决策状态: {result3.status.value}")
    print(f"置信度: {result3.confidence:.2f}")
    print(f"解决策略: {result3.resolution_strategy}")
    
    # 获取决策历史
    print("\n决策历史:")
    history = decision_system.get_decision_history()
    for i, record in enumerate(history, 1):
        print(f"{i}. {record['final_decision']} ({record['status']}, 置信度: {record['confidence']:.2f})")
    
    print("\n" + "=" * 80)
    print("测试完成")


if __name__ == "__main__":
    test_multi_model_decision()