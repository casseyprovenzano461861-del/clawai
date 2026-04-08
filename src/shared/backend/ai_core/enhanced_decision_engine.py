# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强决策引擎模块
基于大模型的分析与决策机制
"""

import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from ai_engine.llm_agent.pentest_agent import ClawAIPentestAgent
from ai_engine.llm_agent.config_manager import LLMConfigManager


class DecisionType(Enum):
    """决策类型枚举"""
    ATTACK_PLAN = "attack_plan"           # 攻击计划
    TOOL_SELECTION = "tool_selection"     # 工具选择
    PARAMETER_OPTIMIZATION = "parameter_optimization"  # 参数优化
    RISK_MANAGEMENT = "risk_management"   # 风险管理
    EXECUTION_CONTROL = "execution_control"  # 执行控制


class StrategyType(Enum):
    """策略类型枚举"""
    OFFENSIVE = "offensive"       # 进攻型 - 全面渗透测试
    DEFENSIVE = "defensive"       # 防御型 - 安全评估，避免破坏
    STEALTH = "stealth"           # 隐蔽型 - 避免触发告警
    RAPID = "rapid"               # 快速型 - 时间受限的快速扫描
    COMPREHENSIVE = "comprehensive"  # 全面型 - 深度完整测试


@dataclass
class ContextAnalysis:
    """上下文分析结果"""
    target_type: str  # Web, Database, Service, Network, Internal
    tech_stack: List[str]
    defense_measures: List[str]
    environment_constraints: Dict[str, Any]
    compliance_requirements: List[str]
    time_constraints: Dict[str, Any]
    risk_tolerance: str  # low, medium, high


@dataclass
class Decision:
    """决策结果"""
    decision_id: str
    decision_type: DecisionType
    strategy: StrategyType
    rationale: str  # 决策理由
    confidence: float  # 置信度 0.0-1.0
    parameters: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    expected_outcome: str


class EnhancedDecisionEngine:
    """
    增强决策引擎
    基于大模型的分析与决策机制
    """
    
    def __init__(self, context_manager, strategy_repository):
        self.context_manager = context_manager
        self.strategy_repository = strategy_repository
        self.logger = logging.getLogger(__name__)
        self.decision_history = []  # 决策历史记录
        
        # 初始化LLM代理
        self.llm_config_manager = LLMConfigManager()
        self.llm_agent = None
        self._initialize_llm_agent()
    
    def _initialize_llm_agent(self):
        """初始化LLM代理"""
        try:
            config = self.llm_config_manager.load_config("hacksynth_enhanced")
            self.llm_agent = ClawAIPentestAgent(
                config=config,
                tool_executor_url="http://localhost:8082",
                skill_registry=None
            )
            self.logger.info(f"LLM代理初始化成功: {self.llm_agent.model_id}")
        except Exception as e:
            self.logger.error(f"LLM代理初始化失败: {e}")
            self.llm_agent = None
    
    def _get_context_attr(self, context, attr_name, default=None):
        """从上下文对象或字典中获取属性"""
        if hasattr(context, attr_name):
            return getattr(context, attr_name)
        elif isinstance(context, dict):
            return context.get(attr_name, default)
        else:
            return default
    
    def _normalize_strategy(self, strategy):
        """标准化策略类型，处理字符串和枚举"""
        if isinstance(strategy, StrategyType):
            return strategy
        elif isinstance(strategy, str):
            # 尝试将字符串转换为枚举
            try:
                return StrategyType(strategy)
            except ValueError:
                # 如果字符串格式不匹配，尝试匹配
                strategy_lower = strategy.lower()
                for strategy_type in StrategyType:
                    if strategy_type.value.lower() == strategy_lower:
                        return strategy_type
                # 默认返回OFFENSIVE
                self.logger.warning(f"未知策略类型: {strategy}, 使用默认进攻型策略")
                return StrategyType.OFFENSIVE
        else:
            self.logger.warning(f"无法识别的策略类型: {type(strategy)}, 使用默认进攻型策略")
            return StrategyType.OFFENSIVE
        
    def make_decision(self, scan_data: Dict, user_context: Dict) -> Decision:
        """
        做出决策
        
        Args:
            scan_data: 扫描结果数据
            user_context: 用户上下文（目标、约束、偏好等）
            
        Returns:
            Decision: 决策结果
        """
        self.logger.info("开始决策流程...")
        
        # 1. 上下文理解
        context_analysis = self.context_manager.analyze(scan_data, user_context)
        self.logger.debug(f"上下文分析完成: {context_analysis}")
        
        # 2. 策略选择
        strategy = self.strategy_repository.select_strategy(context_analysis)
        self.logger.info(f"选择策略: {strategy}")
        
        # 3. 风险评估
        risk_assessment = self._assess_risk(context_analysis, scan_data)
        self.logger.debug(f"风险评估: {risk_assessment}")
        
        # 4. 使用LLM增强分析
        enhanced_analysis = self._enhance_analysis_with_llm(
            context_analysis, 
            risk_assessment, 
            scan_data, 
            user_context
        )
        
        # 5. 决策生成
        decision = self._generate_decision(
            strategy, 
            context_analysis, 
            risk_assessment, 
            user_context, 
            enhanced_analysis
        )
        
        # 6. 记录决策历史
        self._record_decision(decision, context_analysis)
        
        self.logger.info(f"决策完成: {decision.decision_id}")
        return decision
    
    def _assess_risk(self, context: Dict, scan_data: Dict) -> Dict[str, Any]:
        """风险评估"""
        risk_score = 0
        risk_factors = []
        
        # 基于目标类型
        target_risk = {
            "Web": 30,
            "Database": 50,
            "Service": 40,
            "Network": 25,
            "Internal": 70
        }
        
        # 处理字典或ContextAnalysis对象
        if hasattr(context, 'target_type'):
            target_type = context.target_type
            defense_measures = context.defense_measures
            time_constraints = context.time_constraints
            risk_tolerance = context.risk_tolerance
            tech_stack = context.tech_stack
        else:
            target_type = context.get('target_type', 'Web')
            defense_measures = context.get('defense_measures', [])
            time_constraints = context.get('time_constraints', {})
            risk_tolerance = context.get('risk_tolerance', 'medium')
            tech_stack = context.get('tech_stack', [])
        
        risk_score += target_risk.get(target_type, 20)
        risk_factors.append(f"目标类型: {target_type}")
        
        # 基于防御措施
        if defense_measures:
            risk_score += len(defense_measures) * 10
            risk_factors.append(f"防御措施: {len(defense_measures)}项")
        
        # 基于时间约束
        if time_constraints.get("strict", False):
            risk_score += 20
            risk_factors.append("严格时间约束")
        
        # 基于扫描数据中的漏洞
        vulnerabilities = scan_data.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low").lower()
            if severity == "critical":
                risk_score += 40
            elif severity == "high":
                risk_score += 25
            elif severity == "medium":
                risk_score += 15
            elif severity == "low":
                risk_score += 5
        
        # 确定风险等级
        if risk_score >= 100:
            risk_level = "high"
        elif risk_score >= 60:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _enhance_analysis_with_llm(
        self, 
        context_analysis: ContextAnalysis, 
        risk_assessment: Dict, 
        scan_data: Dict, 
        user_context: Dict
    ) -> Dict[str, Any]:
        """使用LLM增强分析"""
        if not self.llm_agent:
            self.logger.warning("LLM代理不可用，跳过增强分析")
            return {"enhanced": False}
        
        try:
            # 构建LLM分析提示
            target = user_context.get("target", "unknown")
            
            # 构建上下文信息
            context_info = {
                "target": target,
                "target_type": context_analysis.target_type,
                "tech_stack": context_analysis.tech_stack,
                "defense_measures": context_analysis.defense_measures,
                "risk_level": risk_assessment["risk_level"],
                "risk_factors": risk_assessment["risk_factors"],
                "scan_results": scan_data
            }
            
            # 使用LLM进行分析
            analysis_prompt = f"""作为安全专家，分析以下渗透测试上下文信息，提供专业的安全分析和建议：

上下文信息：
{json.dumps(context_info, indent=2, ensure_ascii=False)}

请提供：
1. 目标系统的安全态势评估
2. 潜在的攻击面分析
3. 推荐的测试策略和工具
4. 可能的漏洞和风险点
5. 测试执行的优先级建议

分析结果应该专业、详细，基于实际的安全测试经验。"""
            
            # 调用LLM生成分析
            messages = [
                {"role": "system", "content": "你是一个专业的安全渗透测试专家，具有丰富的安全测试经验和专业知识。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            llm_output, input_tokens, output_tokens = self.llm_agent.generate_text(messages)
            
            # 解析LLM输出
            enhanced_analysis = {
                "enhanced": True,
                "llm_analysis": llm_output,
                "token_usage": {
                    "input": input_tokens,
                    "output": output_tokens
                },
                "timestamp": time.time()
            }
            
            self.logger.info("LLM增强分析完成")
            return enhanced_analysis
            
        except Exception as e:
            self.logger.error(f"LLM分析失败: {e}")
            return {"enhanced": False, "error": str(e)}
    
    def _generate_decision(
        self, 
        strategy: StrategyType, 
        context: ContextAnalysis,
        risk_assessment: Dict,
        user_context: Dict,
        enhanced_analysis: Dict
    ) -> Decision:
        """生成决策"""
        
        # 生成决策ID
        target_type = self._get_context_attr(context, 'target_type', 'Web')
        decision_id = hashlib.md5(
            f"{strategy.value}_{target_type}_{time.time()}".encode()
        ).hexdigest()[:12]
        
        # 根据策略类型生成决策
        if strategy == StrategyType.OFFENSIVE:
            decision_type = DecisionType.ATTACK_PLAN
            rationale = "采用进攻型策略进行全面渗透测试"
            parameters = {
                "intensity": "high",
                "coverage": "comprehensive",
                "stealth_level": "low",
                "time_allocation": "flexible"
            }
            expected_outcome = "全面发现和验证安全漏洞"
            
        elif strategy == StrategyType.DEFENSIVE:
            decision_type = DecisionType.RISK_MANAGEMENT
            rationale = "采用防御型策略进行安全评估，避免破坏性操作"
            parameters = {
                "intensity": "medium",
                "coverage": "focused",
                "stealth_level": "medium",
                "time_allocation": "moderate"
            }
            expected_outcome = "安全风险评估和加固建议"
            
        elif strategy == StrategyType.STEALTH:
            decision_type = DecisionType.EXECUTION_CONTROL
            rationale = "采用隐蔽型策略避免触发告警"
            parameters = {
                "intensity": "low",
                "coverage": "targeted",
                "stealth_level": "high",
                "time_allocation": "extended"
            }
            expected_outcome = "隐蔽的安全测试和漏洞发现"
            
        elif strategy == StrategyType.RAPID:
            decision_type = DecisionType.ATTACK_PLAN
            rationale = "采用快速型策略进行时间受限的扫描"
            parameters = {
                "intensity": "medium",
                "coverage": "key_areas",
                "stealth_level": "low",
                "time_allocation": "limited"
            }
            expected_outcome = "快速发现高风险漏洞"
            
        else:  # COMPREHENSIVE
            decision_type = DecisionType.ATTACK_PLAN
            rationale = "采用全面型策略进行深度安全测试"
            parameters = {
                "intensity": "very_high",
                "coverage": "exhaustive",
                "stealth_level": "medium",
                "time_allocation": "extended"
            }
            expected_outcome = "深度安全分析和全面漏洞报告"
        
        # 基于风险评估调整参数
        if risk_assessment["risk_level"] == "high":
            parameters["intensity"] = "very_high"
            parameters["monitoring"] = "enhanced"
            rationale += "（高风险环境，增强监控）"
        
        # 基于用户上下文调整
        if user_context.get("preferences", {}).get("minimal_impact", False):
            parameters["intensity"] = "low"
            rationale += "（用户要求最小影响）"
        
        # 基于LLM增强分析调整
        if enhanced_analysis.get("enhanced", False):
            llm_analysis = enhanced_analysis.get("llm_analysis", "")
            # 解析LLM分析中的建议
            if "优先级" in llm_analysis:
                parameters["priority"] = "llm_recommended"
                rationale += "（基于LLM分析调整）"
        
        # 生成备选方案
        alternatives = self._generate_alternatives(strategy, context, risk_assessment)
        
        # 计算置信度
        confidence = self._calculate_confidence(context, risk_assessment, enhanced_analysis)
        
        return Decision(
            decision_id=decision_id,
            decision_type=decision_type,
            strategy=strategy,
            rationale=rationale,
            confidence=confidence,
            parameters=parameters,
            alternatives=alternatives,
            expected_outcome=expected_outcome
        )
    
    def _generate_alternatives(
        self, 
        strategy: StrategyType, 
        context: ContextAnalysis,
        risk_assessment: Dict
    ) -> List[Dict[str, Any]]:
        """生成备选方案"""
        alternatives = []
        
        # 标准化策略类型
        normalized_strategy = self._normalize_strategy(strategy)
        
        # 生成2-3个备选策略
        all_strategies = list(StrategyType)
        current_index = all_strategies.index(normalized_strategy)
        
        # 相邻策略作为备选
        for offset in [1, -1]:
            alt_index = (current_index + offset) % len(all_strategies)
            alt_strategy = all_strategies[alt_index]
            
            alternative = {
                "strategy": alt_strategy.value,
                "reason": f"备用策略：{alt_strategy.value}",
                "confidence_adjustment": -0.2,
                "conditions": [
                    "主策略执行失败",
                    "发现意外防御措施",
                    "时间约束变化"
                ]
            }
            alternatives.append(alternative)
        
        # 根据风险评估添加专门备选
        if risk_assessment["risk_level"] == "high":
            alternatives.append({
                "strategy": StrategyType.DEFENSIVE.value,
                "reason": "高风险环境下的安全备选",
                "confidence_adjustment": -0.1,
                "conditions": ["风险过高", "合规要求严格"]
            })
        
        return alternatives
    
    def _calculate_confidence(
        self, 
        context, 
        risk_assessment: Dict,
        enhanced_analysis: Dict
    ) -> float:
        """计算置信度"""
        confidence = 0.7  # 基础置信度
        
        # 处理字典或ContextAnalysis对象
        if hasattr(context, 'tech_stack'):
            tech_stack = context.tech_stack
            defense_measures = context.defense_measures
            time_constraints = context.time_constraints
        else:
            tech_stack = context.get('tech_stack', [])
            defense_measures = context.get('defense_measures', [])
            time_constraints = context.get('time_constraints', {})
        
        # 基于上下文信息质量
        if len(tech_stack) > 0:
            confidence += 0.1
        
        if len(defense_measures) > 0:
            confidence += 0.05
        
        # 基于风险等级
        if risk_assessment["risk_level"] == "low":
            confidence += 0.1
        elif risk_assessment["risk_level"] == "high":
            confidence -= 0.05
        
        # 基于时间约束
        if not time_constraints.get("strict", False):
            confidence += 0.05
        
        # 基于LLM增强分析
        if enhanced_analysis.get("enhanced", False):
            confidence += 0.1
        
        # 限制在合理范围
        return max(0.3, min(0.95, confidence))
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """获取风险建议"""
        recommendations = {
            "high": "高风险环境，建议增强监控、分阶段执行、准备应急方案",
            "medium": "中等风险，建议标准监控、按计划执行、记录执行过程",
            "low": "低风险，建议基本监控、灵活执行、关注关键发现"
        }
        return recommendations.get(risk_level, "未知风险等级")
    
    def _record_decision(self, decision: Decision, context):
        """记录决策历史"""
        # 处理字典或ContextAnalysis对象
        if hasattr(context, 'target_type'):
            target_type = context.target_type
            tech_stack = context.tech_stack
            risk_level = context.risk_tolerance
        else:
            target_type = context.get('target_type', 'Web')
            tech_stack = context.get('tech_stack', [])
            risk_level = context.get('risk_tolerance', 'medium')
        
        decision_record = {
            "decision_id": decision.decision_id,
            "timestamp": time.time(),
            "strategy": decision.strategy.value,
            "context": {
                "target_type": target_type,
                "tech_stack": tech_stack,
                "risk_level": risk_level
            },
            "confidence": decision.confidence,
            "rationale": decision.rationale
        }
        
        self.decision_history.append(decision_record)
        
        # 保持历史记录大小
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-50:]
    
    def get_decision_history(self, limit: int = 10) -> List[Dict]:
        """获取决策历史"""
        return self.decision_history[-limit:] if self.decision_history else []
    
    def learn_from_feedback(self, decision_id: str, feedback: Dict):
        """
        从反馈中学习
        
        Args:
            decision_id: 决策ID
            feedback: 反馈信息，包含成功与否、效果评估等
        """
        success = feedback.get("success", True)
        effectiveness = feedback.get("effectiveness", 0.5)
        
        # 找到对应的决策记录
        for record in self.decision_history:
            if record["decision_id"] == decision_id:
                record["feedback"] = feedback
                record["learned"] = True
                
                # 根据反馈调整策略选择逻辑
                self._adjust_strategy_preferences(record, success, effectiveness)
                break
    
    def _adjust_strategy_preferences(self, record: Dict, success: bool, effectiveness: float):
        """调整策略偏好"""
        # 这里可以集成机器学习算法来调整策略选择
        # 目前先记录反馈供未来使用
        self.logger.info(f"学习反馈: 决策{record['decision_id']}, "
                        f"成功: {success}, 效果: {effectiveness}")


def main():
    """测试函数"""
    import json
    
    # 创建简单的上下文管理器和策略库（实际使用时需要完整实现）
    class SimpleContextManager:
        def analyze(self, scan_data, user_context):
            return ContextAnalysis(
                target_type="Web",
                tech_stack=["nginx", "PHP", "WordPress"],
                defense_measures=["WAF"],
                environment_constraints={"network": "external"},
                compliance_requirements=[],
                time_constraints={"strict": False},
                risk_tolerance="medium"
            )
    
    class SimpleStrategyRepository:
        def select_strategy(self, context_analysis):
            return StrategyType.OFFENSIVE
    
    # 创建决策引擎
    context_manager = SimpleContextManager()
    strategy_repo = SimpleStrategyRepository()
    engine = EnhancedDecisionEngine(context_manager, strategy_repo)
    
    # 测试数据
    test_scan_data = {
        "target": "example.com",
        "vulnerabilities": [
            {"name": "XSS", "severity": "medium"},
            {"name": "SQLi", "severity": "high"}
        ]
    }
    
    test_user_context = {
        "target": "example.com",
        "preferences": {
            "minimal_impact": False,
            "thoroughness": "high"
        }
    }
    
    # 做出决策
    decision = engine.make_decision(test_scan_data, test_user_context)
    
    print("=" * 80)
    print("增强决策引擎测试")
    print("=" * 80)
    
    print(f"\n决策ID: {decision.decision_id}")
    print(f"策略类型: {decision.strategy.value}")
    print(f"决策类型: {decision.decision_type.value}")
    print(f"置信度: {decision.confidence:.2f}")
    print(f"决策理由: {decision.rationale}")
    print(f"预期结果: {decision.expected_outcome}")
    
    print(f"\n参数配置:")
    for key, value in decision.parameters.items():
        print(f"  {key}: {value}")
    
    print(f"\n备选方案 ({len(decision.alternatives)}个):")
    for alt in decision.alternatives:
        print(f"  - {alt['strategy']}: {alt['reason']}")
    
    print(f"\n决策历史 ({len(engine.decision_history)}条记录)")
    print("=" * 80)


if __name__ == "__main__":
    import time
    main()
