# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
规则引擎解释系统
提供决策原因解释、风险评估解释和替代方案解释
⚠️ 技术诚信说明：本模块使用规则引擎解释而非真正的AI系统
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

from .multi_model_decision import DecisionResult, ModelDecision

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """解释类型"""
    DECISION_REASON = "decision_reason"      # 决策原因解释
    RISK_ASSESSMENT = "risk_assessment"      # 风险评估解释
    ALTERNATIVE_OPTION = "alternative_option" # 替代方案解释
    CONFIDENCE_ANALYSIS = "confidence_analysis" # 置信度分析
    MODEL_BIAS = "model_bias"               # 模型偏差分析


@dataclass
class Explanation:
    """AI解释"""
    explanation_id: str
    explanation_type: ExplanationType
    target_decision: str
    explanation_content: str
    confidence_score: float  # 0.0-1.0
    supporting_evidence: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "explanation_id": self.explanation_id,
            "explanation_type": self.explanation_type.value,
            "target_decision": self.target_decision,
            "explanation_content": self.explanation_content,
            "confidence_score": round(self.confidence_score, 4),
            "supporting_evidence": self.supporting_evidence,
            "timestamp": datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }


class ExplanationTemplate:
    """解释模板"""
    
    def __init__(self):
        # 决策原因解释模板
        self.decision_reason_templates = [
            "模型选择{decision}的主要原因包括：{reasons}。该决策基于{confidence:.0%}的置信度。",
            "基于分析，{decision}被选中因为：{reasons}。各模型对此的共识度为{consensus_level}。",
            "选择{decision}的决策逻辑：{reasons}。这个选择在{models_count}个模型中有{support_count}个支持。",
        ]
        
        # 风险评估解释模板
        self.risk_assessment_templates = [
            "此决策涉及的风险评估：{risk_details}。综合风险等级为{risk_level}。",
            "风险评估结果：{risk_details}。主要风险因素包括{risk_factors}。",
            "决策{decision}的风险分析：{risk_details}。建议风险缓解措施：{mitigation}。",
        ]
        
        # 替代方案解释模板
        self.alternative_templates = [
            "替代方案分析：{alternatives}。未选择这些方案的主要原因是{reasons}。",
            "考虑过的替代方案包括：{alternatives}。这些方案的优劣对比：{comparison}。",
            "其他可行方案：{alternatives}。最终决策优于这些方案的原因：{superiority_reasons}。",
        ]
        
        # 置信度分析模板
        self.confidence_templates = [
            "置信度分析：模型间置信度分布为{confidence_distribution}。主要分歧点：{divergence_points}。",
            "模型置信度评估：平均置信度{avg_confidence:.0%}，标准差{std_confidence:.0%}。{confidence_insights}。",
            "决策置信度来源分析：{confidence_sources}。影响置信度的关键因素：{key_factors}。",
        ]
    
    def generate_decision_reason(self, decision: str, reasons: List[str], 
                                confidence: float, models_count: int, 
                                support_count: int) -> str:
        """生成决策原因解释"""
        template = self.decision_reason_templates[0]
        
        reasons_text = "；".join(reasons)
        consensus_level = "高" if support_count / models_count >= 0.7 else "中" if support_count / models_count >= 0.5 else "低"
        
        return template.format(
            decision=decision,
            reasons=reasons_text,
            confidence=confidence,
            consensus_level=consensus_level,
            models_count=models_count,
            support_count=support_count
        )
    
    def generate_risk_assessment(self, decision: str, risk_details: str, 
                                risk_level: str, risk_factors: List[str],
                                mitigation: str) -> str:
        """生成风险评估解释"""
        template = self.risk_assessment_templates[0]
        
        factors_text = "、".join(risk_factors)
        
        return template.format(
            decision=decision,
            risk_details=risk_details,
            risk_level=risk_level,
            risk_factors=factors_text,
            mitigation=mitigation
        )
    
    def generate_alternative_explanation(self, alternatives: List[str], 
                                        reasons: List[str], 
                                        comparison: Dict[str, Any]) -> str:
        """生成替代方案解释"""
        template = self.alternative_templates[0]
        
        alternatives_text = "、".join(alternatives)
        reasons_text = "；".join(reasons)
        
        return template.format(
            alternatives=alternatives_text,
            reasons=reasons_text,
            comparison=json.dumps(comparison, ensure_ascii=False, indent=2)
        )


class RuleEngineExplanationSystem:
    """
    规则引擎解释系统
    提供决策原因解释、风险评估解释和替代方案解释
    ⚠️ 技术诚信说明：使用规则引擎模板生成解释而非真正的AI系统
    """
    
    def __init__(self, template_language: str = "zh-CN"):
        """
        初始化AI解释系统
        
        Args:
            template_language: 模板语言
        """
        self.template_language = template_language
        self.explanation_templates = ExplanationTemplate()
        self.explanation_history = []
        
        # 解释生成策略
        self.explanation_strategies = {
            "simple": self._generate_simple_explanation,
            "detailed": self._generate_detailed_explanation,
            "technical": self._generate_technical_explanation
        }
    
    def explain_decision(self, decision_result: DecisionResult, 
                         strategy: str = "detailed") -> Explanation:
        """
        解释决策
        
        Args:
            decision_result: 决策结果
            strategy: 解释策略 (simple/detailed/technical)
            
        Returns:
            解释对象
        """
        explanation_id = f"exp_{int(time.time())}_{hash(str(decision_result)) % 10000:04d}"
        
        # 选择解释生成策略
        explain_func = self.explanation_strategies.get(strategy, self._generate_detailed_explanation)
        
        # 生成解释
        explanation_content, evidence = explain_func(decision_result)
        
        # 计算解释置信度
        confidence_score = self._calculate_explanation_confidence(decision_result, evidence)
        
        # 创建解释对象
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.DECISION_REASON,
            target_decision=decision_result.final_decision,
            explanation_content=explanation_content,
            confidence_score=confidence_score,
            supporting_evidence=evidence,
            metadata={
                "strategy": strategy,
                "decision_status": decision_result.status.value,
                "original_confidence": decision_result.confidence
            }
        )
        
        # 记录解释历史
        self.explanation_history.append(explanation)
        
        return explanation
    
    def explain_risk(self, decision_result: DecisionResult, 
                     risk_data: Dict[str, Any]) -> Explanation:
        """
        解释风险评估
        
        Args:
            decision_result: 决策结果
            risk_data: 风险评估数据
            
        Returns:
            风险评估解释
        """
        explanation_id = f"risk_{int(time.time())}_{hash(str(decision_result)) % 10000:04d}"
        
        # 提取风险信息
        risk_level = risk_data.get("risk_level", "medium")
        risk_factors = risk_data.get("risk_factors", [])
        mitigation = risk_data.get("mitigation", "标准安全措施")
        
        # 生成风险评估解释
        explanation_content = self.explanation_templates.generate_risk_assessment(
            decision=decision_result.final_decision,
            risk_details=risk_data.get("risk_details", "标准风险评估"),
            risk_level=risk_level,
            risk_factors=risk_factors,
            mitigation=mitigation
        )
        
        # 收集支持证据
        evidence = [
            f"风险等级: {risk_level}",
            f"风险因素数量: {len(risk_factors)}",
            f"决策置信度: {decision_result.confidence:.2f}"
        ]
        
        # 计算风险评估置信度
        confidence_score = self._calculate_risk_confidence(risk_data)
        
        # 创建解释对象
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.RISK_ASSESSMENT,
            target_decision=decision_result.final_decision,
            explanation_content=explanation_content,
            confidence_score=confidence_score,
            supporting_evidence=evidence,
            metadata={
                "risk_level": risk_level,
                "risk_factor_count": len(risk_factors),
                "mitigation_provided": bool(mitigation)
            }
        )
        
        return explanation
    
    def explain_alternatives(self, decision_result: DecisionResult, 
                             alternatives_data: Dict[str, Any]) -> Explanation:
        """
        解释替代方案
        
        Args:
            decision_result: 决策结果
            alternatives_data: 替代方案数据
            
        Returns:
            替代方案解释
        """
        explanation_id = f"alt_{int(time.time())}_{hash(str(decision_result)) % 10000:04d}"
        
        # 提取替代方案信息
        alternatives = alternatives_data.get("alternatives", [])
        rejection_reasons = alternatives_data.get("rejection_reasons", [])
        comparison = alternatives_data.get("comparison", {})
        
        # 生成替代方案解释
        explanation_content = self.explanation_templates.generate_alternative_explanation(
            alternatives=alternatives,
            reasons=rejection_reasons,
            comparison=comparison
        )
        
        # 收集支持证据
        evidence = [
            f"替代方案数量: {len(alternatives)}",
            f"主要拒绝原因: {'; '.join(rejection_reasons[:3])}" if rejection_reasons else "无明确拒绝原因"
        ]
        
        # 计算解释置信度
        confidence_score = self._calculate_alternatives_confidence(alternatives_data)
        
        # 创建解释对象
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.ALTERNATIVE_OPTION,
            target_decision=decision_result.final_decision,
            explanation_content=explanation_content,
            confidence_score=confidence_score,
            supporting_evidence=evidence,
            metadata={
                "alternative_count": len(alternatives),
                "has_comparison": bool(comparison)
            }
        )
        
        return explanation
    
    def analyze_model_biases(self, decision_result: DecisionResult) -> Explanation:
        """
        分析模型偏差
        
        Args:
            decision_result: 决策结果
            
        Returns:
            模型偏差分析解释
        """
        explanation_id = f"bias_{int(time.time())}_{hash(str(decision_result)) % 10000:04d}"
        
        # 分析模型决策模式
        model_biases = self._detect_model_biases(decision_result.model_decisions)
        
        # 生成偏差分析解释
        explanation_content = self._generate_bias_analysis(decision_result, model_biases)
        
        # 收集支持证据
        evidence = [
            f"检测到偏差数量: {len(model_biases)}",
            f"模型数量: {len(decision_result.model_decisions)}",
            f"决策一致性: {decision_result.status.value}"
        ]
        
        # 计算偏差分析置信度
        confidence_score = self._calculate_bias_confidence(model_biases)
        
        # 创建解释对象
        explanation = Explanation(
            explanation_id=explanation_id,
            explanation_type=ExplanationType.MODEL_BIAS,
            target_decision=decision_result.final_decision,
            explanation_content=explanation_content,
            confidence_score=confidence_score,
            supporting_evidence=evidence,
            metadata={
                "bias_count": len(model_biases),
                "biased_models": list(model_biases.keys())
            }
        )
        
        return explanation
    
    def _generate_simple_explanation(self, decision_result: DecisionResult) -> Tuple[str, List[str]]:
        """生成简单解释"""
        # 提取关键信息
        final_decision = decision_result.final_decision
        status = decision_result.status.value
        confidence = decision_result.confidence
        
        # 生成简单解释
        explanation = f"系统选择{final_decision}作为最终决策。"
        explanation += f" 决策状态: {status}，综合置信度: {confidence:.0%}。"
        
        # 添加简单理由
        if decision_result.model_decisions:
            top_model = decision_result.model_decisions[0]
            explanation += f" 主要基于{top_model.model_name}的建议: {top_model.reasoning[:100]}..."
        
        # 证据
        evidence = [
            f"决策状态: {status}",
            f"综合置信度: {confidence:.2f}",
            f"模型数量: {len(decision_result.model_decisions)}"
        ]
        
        return explanation, evidence
    
    def _generate_detailed_explanation(self, decision_result: DecisionResult) -> Tuple[str, List[str]]:
        """生成详细解释"""
        # 提取投票摘要
        voting_summary = decision_result.voting_summary
        
        # 分析决策分布
        decision_distribution = voting_summary.get("decision_distribution", {})
        top_decision = voting_summary.get("top_decision")
        top_count = voting_summary.get("top_count", 0)
        total_models = voting_summary.get("total_models", 0)
        
        # 计算支持率
        support_rate = top_count / total_models if total_models > 0 else 0
        
        # 提取模型理由
        model_reasons = []
        for model_decision in decision_result.model_decisions:
            if model_decision.decision == top_decision:
                model_reasons.append(f"{model_decision.model_name}: {model_decision.reasoning[:80]}...")
        
        # 生成详细解释
        explanation = f"决策分析报告:\n"
        explanation += f"1. 最终决策: {decision_result.final_decision}\n"
        explanation += f"2. 决策机制: {decision_result.resolution_strategy}\n"
        explanation += f"3. 模型投票: {top_count}/{total_models}个模型支持此决策 (支持率: {support_rate:.0%})\n"
        explanation += f"4. 决策置信度: {decision_result.confidence:.0%}\n"
        explanation += f"5. 主要支持理由:\n"
        
        for i, reason in enumerate(model_reasons[:3], 1):
            explanation += f"   {i}. {reason}\n"
        
        # 添加替代方案（如果有）
        if len(decision_distribution) > 1:
            alternatives = [d for d in decision_distribution.keys() if d != top_decision]
            explanation += f"6. 考虑过的替代方案: {', '.join(alternatives[:3])}\n"
        
        # 证据
        evidence = [
            f"支持率: {support_rate:.2f}",
            f"决策机制: {decision_result.resolution_strategy}",
            f"模型理由数量: {len(model_reasons)}",
            f"替代方案数量: {len(decision_distribution) - 1 if len(decision_distribution) > 1 else 0}"
        ]
        
        return explanation, evidence
    
    def _generate_technical_explanation(self, decision_result: DecisionResult) -> Tuple[str, List[str]]:
        """生成技术解释"""
        # 提取详细统计数据
        voting_summary = decision_result.voting_summary
        decision_distribution = voting_summary.get("decision_distribution", {})
        
        # 计算技术指标
        confidence_scores = [md.confidence for md in decision_result.model_decisions]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # 分析置信度分布
        confidence_std = self._calculate_confidence_std(confidence_scores)
        
        # 生成技术解释
        explanation = f"技术决策分析:\n"
        explanation += "=" * 50 + "\n"
        explanation += f"决策ID: {hash(str(decision_result)) % 1000000:06d}\n"
        explanation += f"时间戳: {datetime.fromtimestamp(decision_result.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n"
        explanation += f"算法: {decision_result.resolution_strategy}\n\n"
        
        explanation += "投票分布:\n"
        for decision, info in decision_distribution.items():
            count = info.get("count", 0)
            avg_conf = info.get("average_confidence", 0)
            models = info.get("models", [])
            explanation += f"  {decision}: {count}票 (平均置信度: {avg_conf:.2f}, 模型: {', '.join([m['name'] for m in models[:2]])}{'...' if len(models) > 2 else ''})\n"
        
        explanation += f"\n置信度统计:\n"
        explanation += f"  平均值: {avg_confidence:.3f}\n"
        explanation += f"  标准差: {confidence_std:.3f}\n"
        explanation += f"  范围: [{min(confidence_scores):.3f}, {max(confidence_scores):.3f}]\n"
        
        explanation += f"\n决策质量指标:\n"
        explanation += f"  状态: {decision_result.status.value}\n"
        explanation += f"  最终置信度: {decision_result.confidence:.3f}\n"
        explanation += f"  模型一致性: {self._calculate_model_consistency(decision_result.model_decisions):.2%}\n"
        
        # 证据
        evidence = [
            f"置信度平均值: {avg_confidence:.3f}",
            f"置信度标准差: {confidence_std:.3f}",
            f"模型一致性: {self._calculate_model_consistency(decision_result.model_decisions):.2%}",
            f"决策分布熵: {self._calculate_decision_entropy(decision_distribution):.3f}"
        ]
        
        return explanation, evidence
    
    def _detect_model_biases(self, model_decisions: List[ModelDecision]) -> Dict[str, List[str]]:
        """检测模型偏差"""
        biases = {}
        
        if not model_decisions:
            return biases
        
        # 按模型分组
        model_groups = {}
        for md in model_decisions:
            if md.model_name not in model_groups:
                model_groups[md.model_name] = []
            model_groups[md.model_name].append(md)
        
        # 分析每个模型的决策模式
        for model_name, decisions in model_groups.items():
            model_biases = []
            
            # 检查置信度偏差
            confidences = [d.confidence for d in decisions]
            avg_confidence = sum(confidences) / len(confidences)
            
            if avg_confidence > 0.85:
                model_biases.append("过度自信")
            elif avg_confidence < 0.4:
                model_biases.append("信心不足")
            
            # 检查决策一致性
            unique_decisions = len(set(d.decision for d in decisions))
            if unique_decisions == 1 and len(decisions) > 2:
                model_biases.append("决策固化")
            
            # 检查理由模式
            reasoning_patterns = self._analyze_reasoning_patterns(decisions)
            if reasoning_patterns.get("repetitive", False):
                model_biases.append("理由重复")
            
            if model_biases:
                biases[model_name] = model_biases
        
        return biases
    
    def _generate_bias_analysis(self, decision_result: DecisionResult, 
                                model_biases: Dict[str, List[str]]) -> str:
        """生成偏差分析"""
        if not model_biases:
            return "未检测到明显的模型偏差。所有模型表现正常。"
        
        explanation = "模型偏差检测报告:\n"
        explanation += "=" * 50 + "\n"
        
        for model_name, biases in model_biases.items():
            explanation += f"模型 {model_name}:\n"
            explanation += f"  检测到偏差: {', '.join(biases)}\n"
            
            # 获取该模型的决策
            model_decisions = [md for md in decision_result.model_decisions 
                              if md.model_name == model_name]
            
            if model_decisions:
                avg_confidence = sum(md.confidence for md in model_decisions) / len(model_decisions)
                explanation += f"  平均置信度: {avg_confidence:.2f}\n"
                explanation += f"  决策数量: {len(model_decisions)}\n"
            
            explanation += "\n"
        
        explanation += "建议:\n"
        if any("过度自信" in biases for biases in model_biases.values()):
            explanation += "  - 对过度自信的模型结果进行校准\n"
        if any("信心不足" in biases for biases in model_biases.values()):
            explanation += "  - 对信心不足的模型提供更多训练数据\n"
        if any("决策固化" in biases for biases in model_biases.values()):
            explanation += "  - 引入更多样化的决策场景\n"
        
        return explanation
    
    def _calculate_explanation_confidence(self, decision_result: DecisionResult, 
                                         evidence: List[str]) -> float:
        """计算解释置信度"""
        # 基础置信度
        base_confidence = decision_result.confidence
        
        # 证据强度加成
        evidence_bonus = min(0.2, len(evidence) * 0.05)
        
        # 模型一致性加成
        model_consistency = self._calculate_model_consistency(decision_result.model_decisions)
        consistency_bonus = model_consistency * 0.1
        
        # 计算最终置信度
        confidence = base_confidence * 0.7 + evidence_bonus + consistency_bonus
        
        return min(1.0, confidence)
    
    def _calculate_risk_confidence(self, risk_data: Dict[str, Any]) -> float:
        """计算风险评估置信度"""
        # 基于风险数据的完整性计算置信度
        completeness_score = 0.0
        
        if risk_data.get("risk_level"):
            completeness_score += 0.3
        if risk_data.get("risk_factors"):
            completeness_score += 0.3
        if risk_data.get("mitigation"):
            completeness_score += 0.2
        if risk_data.get("risk_details"):
            completeness_score += 0.2
        
        return completeness_score
    
    def _calculate_alternatives_confidence(self, alternatives_data: Dict[str, Any]) -> float:
        """计算替代方案解释置信度"""
        # 基于替代方案分析的完整性计算置信度
        completeness_score = 0.0
        
        if alternatives_data.get("alternatives"):
            completeness_score += 0.4
        if alternatives_data.get("rejection_reasons"):
            completeness_score += 0.3
        if alternatives_data.get("comparison"):
            completeness_score += 0.3
        
        return completeness_score
    
    def _calculate_bias_confidence(self, model_biases: Dict[str, List[str]]) -> float:
        """计算偏差分析置信度"""
        if not model_biases:
            return 0.8  # 没有偏差检测到，置信度中等
        
        # 基于检测到的偏差数量和类型计算置信度
        total_biases = sum(len(biases) for biases in model_biases.values())
        
        if total_biases >= 5:
            return 0.95  # 检测到多个偏差，置信度高
        elif total_biases >= 2:
            return 0.85  # 检测到一些偏差，置信度中等
        else:
            return 0.7   # 检测到少量偏差，置信度较低
    
    def _calculate_confidence_std(self, confidence_scores: List[float]) -> float:
        """计算置信度标准差"""
        if len(confidence_scores) <= 1:
            return 0.0
        
        import statistics
        try:
            return statistics.stdev(confidence_scores)
        except Exception as e:
            return 0.0
    
    def _calculate_model_consistency(self, model_decisions: List[ModelDecision]) -> float:
        """计算模型一致性"""
        if len(model_decisions) <= 1:
            return 1.0
        
        decisions = [md.decision for md in model_decisions]
        most_common = max(set(decisions), key=decisions.count)
        consistency = decisions.count(most_common) / len(decisions)
        
        return consistency
    
    def _calculate_decision_entropy(self, decision_distribution: Dict[str, Any]) -> float:
        """计算决策分布熵"""
        if not decision_distribution:
            return 0.0
        
        total_count = sum(info.get("count", 0) for info in decision_distribution.values())
        if total_count == 0:
            return 0.0
        
        import math
        entropy = 0.0
        for info in decision_distribution.values():
            count = info.get("count", 0)
            if count > 0:
                probability = count / total_count
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _analyze_reasoning_patterns(self, decisions: List[ModelDecision]) -> Dict[str, Any]:
        """分析理由模式"""
        if not decisions:
            return {}
        
        reasoning_texts = [d.reasoning.lower() for d in decisions]
        
        # 检查重复
        unique_reasonings = set(reasoning_texts)
        repetitive = len(unique_reasonings) < len(reasoning_texts) * 0.7
        
        # 检查关键词模式
        common_words = set()
        for text in reasoning_texts[:3]:
            words = text.split()[:10]
            common_words.update(words)
        
        return {
            "repetitive": repetitive,
            "common_words": list(common_words)[:5],
            "unique_count": len(unique_reasonings)
        }
    
    def get_explanation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取解释历史"""
        recent_history = self.explanation_history[-limit:] if self.explanation_history else []
        return [exp.to_dict() for exp in recent_history]
    
    def export_explanations(self, filepath: str):
        """导出解释到文件"""
        import json
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_explanations": len(self.explanation_history),
            "explanations": [exp.to_dict() for exp in self.explanation_history]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


# 测试函数
def test_explanation_system():
    """测试规则引擎解释系统"""
    print("=" * 80)
    print("规则引擎解释系统测试")
    print("=" * 80)
    
    # 创建解释系统
    explanation_system = RuleEngineExplanationSystem()
    
    # 模拟决策结果（使用multi_model_decision中的测试数据）
    from .multi_model_decision import ModelDecision, DecisionResult, DecisionStatus
    
    # 创建测试决策结果
    model_decisions = [
        ModelDecision(
            model_name="deepseek",
            decision="rce_attack",
            confidence=0.85,
            reasoning="检测到严重RCE漏洞，攻击成功率高，目标系统存在未授权访问"
        ),
        ModelDecision(
            model_name="openai",
            decision="rce_attack",
            confidence=0.78,
            reasoning="存在远程代码执行漏洞，建议优先利用，系统补丁滞后"
        ),
        ModelDecision(
            model_name="claude",
            decision="sql_injection",
            confidence=0.65,
            reasoning="SQL注入攻击更隐蔽，风险更低，适合长期潜伏"
        )
    ]
    
    # 创建决策结果对象
    decision_result = DecisionResult(
        final_decision="rce_attack",
        status=DecisionStatus.MAJORITY,
        confidence=0.72,
        voting_summary={
            "total_models": 3,
            "decision_distribution": {
                "rce_attack": {
                    "count": 2,
                    "average_confidence": 0.815,
                    "models": [
                        {"name": "deepseek", "confidence": 0.85},
                        {"name": "openai", "confidence": 0.78}
                    ]
                },
                "sql_injection": {
                    "count": 1,
                    "average_confidence": 0.65,
                    "models": [
                        {"name": "claude", "confidence": 0.65}
                    ]
                }
            },
            "top_decision": "rce_attack",
            "top_count": 2
        },
        model_decisions=model_decisions,
        resolution_strategy="majority_voting"
    )
    
    # 测试1: 生成决策解释
    print("\n1. 决策解释测试:")
    explanation1 = explanation_system.explain_decision(decision_result, strategy="simple")
    print(f"简单解释: {explanation1.explanation_content}")
    print(f"置信度: {explanation1.confidence_score:.2f}")
    
    explanation2 = explanation_system.explain_decision(decision_result, strategy="detailed")
    print(f"\n详细解释:\n{explanation2.explanation_content}")
    
    # 测试2: 风险评估解释
    print("\n2. 风险评估解释测试:")
    risk_data = {
        "risk_level": "high",
        "risk_factors": ["权限提升", "数据泄露", "系统瘫痪"],
        "mitigation": "使用沙箱环境，限制攻击范围，实时监控",
        "risk_details": "RCE攻击可能导致完全系统控制"
    }
    
    risk_explanation = explanation_system.explain_risk(decision_result, risk_data)
    print(f"风险评估:\n{risk_explanation.explanation_content}")
    
    # 测试3: 替代方案解释
    print("\n3. 替代方案解释测试:")
    alternatives_data = {
        "alternatives": ["sql_injection", "xss_attack", "dos_attack"],
        "rejection_reasons": [
            "SQL注入需要数据库交互，目标可能无数据库",
            "XSS攻击需要用户交互，不适用于当前场景",
            "DoS攻击破坏性太强，不符合渗透测试原则"
        ],
        "comparison": {
            "rce_attack": {"effectiveness": 9, "stealth": 6, "impact": 10},
            "sql_injection": {"effectiveness": 7, "stealth": 8, "impact": 7},
            "xss_attack": {"effectiveness": 5, "stealth": 7, "impact": 4}
        }
    }
    
    alt_explanation = explanation_system.explain_alternatives(decision_result, alternatives_data)
    print(f"替代方案分析:\n{alt_explanation.explanation_content}")
    
    # 测试4: 模型偏差分析
    print("\n4. 模型偏差分析测试:")
    bias_explanation = explanation_system.analyze_model_biases(decision_result)
    print(f"模型偏差分析:\n{bias_explanation.explanation_content}")
    
    # 测试5: 获取解释历史
    print("\n5. 解释历史:")
    history = explanation_system.get_explanation_history()
    for i, exp in enumerate(history, 1):
        print(f"{i}. {exp['explanation_type']}: {exp['explanation_content'][:80]}...")
    
    print("\n" + "=" * 80)
    print("AI解释系统测试完成")


if __name__ == "__main__":
    test_explanation_system()