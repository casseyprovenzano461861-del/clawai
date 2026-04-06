# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
策略库模块
存储和管理各种安全测试策略，根据上下文选择最佳策略
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum


class StrategyType(Enum):
    """策略类型枚举"""
    OFFENSIVE = "offensive"       # 进攻型 - 全面渗透测试
    DEFENSIVE = "defensive"       # 防御型 - 安全评估，避免破坏
    STEALTH = "stealth"           # 隐蔽型 - 避免触发告警
    RAPID = "rapid"               # 快速型 - 时间受限的快速扫描
    COMPREHENSIVE = "comprehensive"  # 全面型 - 深度完整测试


class Strategy:
    """策略类"""
    
    def __init__(
        self, 
        strategy_type: StrategyType,
        name: str,
        description: str,
        conditions: Dict[str, Any],
        priority: int = 1,
        weight: float = 1.0
    ):
        self.strategy_type = strategy_type
        self.name = name
        self.description = description
        self.conditions = conditions
        self.priority = priority
        self.weight = weight
        
    def matches_conditions(self, context: Dict) -> bool:
        """检查策略是否匹配上下文条件"""
        for key, expected_value in self.conditions.items():
            if key not in context:
                return False
            
            context_value = context[key]
            
            # 处理列表类型的条件
            if isinstance(expected_value, list):
                if not isinstance(context_value, list):
                    return False
                if not any(item in context_value for item in expected_value):
                    return False
            # 处理范围类型的条件
            elif isinstance(expected_value, dict) and "range" in expected_value:
                range_spec = expected_value["range"]
                if not isinstance(context_value, (int, float)):
                    return False
                if context_value < range_spec.get("min", float("-inf")):
                    return False
                if context_value > range_spec.get("max", float("inf")):
                    return False
            # 处理精确匹配
            else:
                if context_value != expected_value:
                    return False
        
        return True
    
    def calculate_score(self, context: Dict) -> float:
        """计算策略得分"""
        score = self.weight
        
        # 基于上下文调整得分
        if self.strategy_type == StrategyType.OFFENSIVE:
            # 进攻型策略在风险容忍度高时得分更高
            if context.get("risk_tolerance") == "high":
                score += 0.3
            # 在时间充裕时得分更高
            if not context.get("time_constraints", {}).get("strict", True):
                score += 0.2
        
        elif self.strategy_type == StrategyType.DEFENSIVE:
            # 防御型策略在合规要求严格时得分更高
            if len(context.get("compliance_requirements", [])) > 0:
                score += 0.3
            # 在风险容忍度低时得分更高
            if context.get("risk_tolerance") == "low":
                score += 0.2
        
        elif self.strategy_type == StrategyType.STEALTH:
            # 隐蔽型策略在有防御措施时得分更高
            if len(context.get("defense_measures", [])) > 0:
                score += 0.3
            # 在内网环境时得分更高
            if context.get("environment_constraints", {}).get("network") == "internal":
                score += 0.2
        
        elif self.strategy_type == StrategyType.RAPID:
            # 快速型策略在时间紧迫时得分更高
            if context.get("time_constraints", {}).get("strict", False):
                score += 0.4
            # 在紧急程度高时得分更高
            if context.get("time_constraints", {}).get("urgency") == "high":
                score += 0.3
        
        elif self.strategy_type == StrategyType.COMPREHENSIVE:
            # 全面型策略在技术栈复杂时得分更高
            if len(context.get("tech_stack", [])) >= 3:
                score += 0.3
            # 在目标置信度高时得分更高
            if context.get("target_confidence", 0) >= 0.8:
                score += 0.2
        
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy_type": self.strategy_type.value,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "priority": self.priority,
            "weight": self.weight
        }


class StrategyRepository:
    """
    策略库
    存储和管理安全测试策略
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.strategies = self._initialize_strategies()
        self.strategy_history = []  # 策略选择历史
        
    def _initialize_strategies(self) -> List[Strategy]:
        """初始化策略库"""
        strategies = [
            # ===== 进攻型策略 =====
            Strategy(
                strategy_type=StrategyType.OFFENSIVE,
                name="全面渗透测试",
                description="全面的渗透测试策略，覆盖所有攻击面，最大化漏洞发现",
                conditions={
                    "risk_tolerance": ["medium", "high"],
                    "target_type": ["Web", "Database", "Service"],
                    "time_constraints.strict": False
                },
                priority=1,
                weight=1.0
            ),
            Strategy(
                strategy_type=StrategyType.OFFENSIVE,
                name="重点攻击验证",
                description="针对已知漏洞和关键攻击面进行验证性测试",
                conditions={
                    "risk_tolerance": "high",
                    "vulnerabilities": {"range": {"min": 1}},  # 有漏洞时适用
                    "target_confidence": {"range": {"min": 0.7}}
                },
                priority=2,
                weight=0.9
            ),
            
            # ===== 防御型策略 =====
            Strategy(
                strategy_type=StrategyType.DEFENSIVE,
                name="安全基线评估",
                description="安全配置评估，避免破坏性操作，提供加固建议",
                conditions={
                    "risk_tolerance": "low",
                    "compliance_requirements": {"range": {"min": 1}},  # 有合规要求
                    "defense_measures": {"range": {"min": 1}}  # 有防御措施
                },
                priority=1,
                weight=1.0
            ),
            Strategy(
                strategy_type=StrategyType.DEFENSIVE,
                name="安全影响最小化测试",
                description="最小化影响的测试，确保业务连续性",
                conditions={
                    "risk_tolerance": "low",
                    "environment_constraints.resource_constraints": "low",
                    "time_constraints.strict": True
                },
                priority=2,
                weight=0.8
            ),
            
            # ===== 隐蔽型策略 =====
            Strategy(
                strategy_type=StrategyType.STEALTH,
                name="隐蔽渗透测试",
                description="避免触发安全告警的隐蔽测试策略",
                conditions={
                    "defense_measures": {"range": {"min": 1}},  # 有防御措施
                    "environment_constraints.network": "internal",  # 内网环境
                    "target_type": ["Web", "Service", "Internal"]
                },
                priority=1,
                weight=1.0
            ),
            Strategy(
                strategy_type=StrategyType.STEALTH,
                name="红队模拟攻击",
                description="模拟真实攻击者的隐蔽攻击策略",
                conditions={
                    "test_type": "red_team",
                    "defense_measures": {"range": {"min": 2}},  # 有多重防御
                    "risk_tolerance": "high"
                },
                priority=2,
                weight=0.9
            ),
            
            # ===== 快速型策略 =====
            Strategy(
                strategy_type=StrategyType.RAPID,
                name="快速风险扫描",
                description="时间受限的快速风险评估和关键漏洞扫描",
                conditions={
                    "time_constraints.strict": True,
                    "time_constraints.urgency": "high",
                    "target_type": ["Web", "Service"]
                },
                priority=1,
                weight=1.0
            ),
            Strategy(
                strategy_type=StrategyType.RAPID,
                name="应急响应测试",
                description="应急响应场景下的快速安全测试",
                conditions={
                    "time_constraints.time_limit": {"range": {"max": 60}},  # 1小时内
                    "urgency": "high",
                    "risk_tolerance": "medium"
                },
                priority=2,
                weight=0.8
            ),
            
            # ===== 全面型策略 =====
            Strategy(
                strategy_type=StrategyType.COMPREHENSIVE,
                name="深度安全审计",
                description="深度全面的安全审计，覆盖所有技术栈和攻击面",
                conditions={
                    "tech_stack": {"range": {"min": 3}},  # 复杂技术栈
                    "target_confidence": {"range": {"min": 0.8}},
                    "time_constraints.strict": False,
                    "risk_tolerance": "medium"
                },
                priority=1,
                weight=1.0
            ),
            Strategy(
                strategy_type=StrategyType.COMPREHENSIVE,
                name="年度安全评估",
                description="年度全面的安全评估，生成详细的安全报告",
                conditions={
                    "test_type": "annual_assessment",
                    "compliance_requirements": {"range": {"min": 1}},
                    "target_type": ["Web", "Database", "Service", "Network"]
                },
                priority=2,
                weight=0.9
            )
        ]
        
        return strategies
    
    def select_strategy(self, context_analysis: Dict) -> StrategyType:
        """
        选择最佳策略
        
        Args:
            context_analysis: 上下文分析结果
            
        Returns:
            StrategyType: 选择的策略类型
        """
        self.logger.info("开始策略选择...")
        
        # 找到所有匹配的策略
        matching_strategies = []
        for strategy in self.strategies:
            if strategy.matches_conditions(context_analysis):
                score = strategy.calculate_score(context_analysis)
                matching_strategies.append((strategy, score))
                self.logger.debug(f"策略匹配: {strategy.name}, 得分: {score:.2f}")
        
        if not matching_strategies:
            self.logger.warning("没有匹配的策略，使用默认进攻型策略")
            return StrategyType.OFFENSIVE
        
        # 按得分排序
        matching_strategies.sort(key=lambda x: x[1], reverse=True)
        
        # 选择得分最高的策略
        best_strategy, best_score = matching_strategies[0]
        
        # 记录策略选择历史
        self._record_strategy_selection(
            best_strategy.strategy_type, 
            best_score, 
            context_analysis,
            [s[0].name for s in matching_strategies[:3]]  # 记录前三名
        )
        
        self.logger.info(f"选择策略: {best_strategy.name} (得分: {best_score:.2f})")
        return best_strategy.strategy_type
    
    def _record_strategy_selection(
        self, 
        strategy_type: StrategyType, 
        score: float, 
        context: Dict,
        candidate_strategies: List[str]
    ):
        """记录策略选择历史"""
        import time
        
        record = {
            "timestamp": time.time(),
            "strategy": strategy_type.value,
            "score": score,
            "context_summary": {
                "target_type": context.get("target_type"),
                "tech_stack_count": len(context.get("tech_stack", [])),
                "defense_count": len(context.get("defense_measures", [])),
                "risk_tolerance": context.get("risk_tolerance")
            },
            "candidates": candidate_strategies
        }
        
        self.strategy_history.append(record)
        
        # 保持历史记录大小
        if len(self.strategy_history) > 100:
            self.strategy_history = self.strategy_history[-50:]
    
    def get_matching_strategies(self, context: Dict) -> List[Dict[str, Any]]:
        """
        获取所有匹配的策略及其得分
        
        Args:
            context: 上下文信息
            
        Returns:
            List[Dict]: 匹配的策略列表
        """
        results = []
        for strategy in self.strategies:
            if strategy.matches_conditions(context):
                score = strategy.calculate_score(context)
                results.append({
                    "name": strategy.name,
                    "type": strategy.strategy_type.value,
                    "description": strategy.description,
                    "score": score,
                    "priority": strategy.priority,
                    "weight": strategy.weight
                })
        
        # 按得分排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def add_strategy(
        self, 
        strategy_type: StrategyType,
        name: str,
        description: str,
        conditions: Dict[str, Any],
        priority: int = 1,
        weight: float = 1.0
    ):
        """添加新策略"""
        new_strategy = Strategy(
            strategy_type=strategy_type,
            name=name,
            description=description,
            conditions=conditions,
            priority=priority,
            weight=weight
        )
        
        self.strategies.append(new_strategy)
        self.logger.info(f"添加新策略: {name}")
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """移除策略"""
        for i, strategy in enumerate(self.strategies):
            if strategy.name == strategy_name:
                self.strategies.pop(i)
                self.logger.info(f"移除策略: {strategy_name}")
                return True
        
        return False
    
    def update_strategy_weight(self, strategy_name: str, weight: float) -> bool:
        """更新策略权重"""
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                old_weight = strategy.weight
                strategy.weight = weight
                self.logger.info(f"更新策略权重: {strategy_name} ({old_weight} -> {weight})")
                return True
        
        return False
    
    def get_strategy_history(self, limit: int = 10) -> List[Dict]:
        """获取策略选择历史"""
        return self.strategy_history[-limit:] if self.strategy_history else []
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        stats = {
            "total_strategies": len(self.strategies),
            "by_type": {},
            "average_selection_score": 0.0
        }
        
        # 按类型统计
        for strategy_type in StrategyType:
            type_strategies = [s for s in self.strategies if s.strategy_type == strategy_type]
            stats["by_type"][strategy_type.value] = len(type_strategies)
        
        # 计算平均选择得分
        if self.strategy_history:
            total_score = sum(record["score"] for record in self.strategy_history)
            stats["average_selection_score"] = total_score / len(self.strategy_history)
        
        return stats
    
    def export_strategies(self) -> List[Dict[str, Any]]:
        """导出所有策略"""
        return [strategy.to_dict() for strategy in self.strategies]
    
    def import_strategies(self, strategies_data: List[Dict[str, Any]]):
        """导入策略"""
        imported_count = 0
        
        for strategy_data in strategies_data:
            try:
                strategy_type = StrategyType(strategy_data["strategy_type"])
                strategy = Strategy(
                    strategy_type=strategy_type,
                    name=strategy_data["name"],
                    description=strategy_data["description"],
                    conditions=strategy_data["conditions"],
                    priority=strategy_data.get("priority", 1),
                    weight=strategy_data.get("weight", 1.0)
                )
                self.strategies.append(strategy)
                imported_count += 1
            except Exception as e:
                self.logger.error(f"导入策略失败: {e}")
        
        self.logger.info(f"成功导入 {imported_count} 个策略")


def main():
    """测试函数"""
    import json
    
    # 创建策略库
    repository = StrategyRepository()
    
    # 测试上下文
    test_context = {
        "target_type": "Web",
        "tech_stack": ["nginx", "PHP", "WordPress", "MySQL"],
        "defense_measures": ["WAF: Cloudflare"],
        "compliance_requirements": ["PCI-DSS"],
        "time_constraints": {
            "strict": False,
            "time_limit": 180,
            "urgency": "normal"
        },
        "risk_tolerance": "medium",
        "target_confidence": 0.85,
        "vulnerabilities": [
            {"name": "XSS", "severity": "medium"},
            {"name": "SQLi", "severity": "high"}
        ],
        "environment_constraints": {
            "network": "external",
            "access_level": "normal"
        }
    }
    
    print("=" * 80)
    print("策略库测试")
    print("=" * 80)
    
    print(f"\n策略总数: {repository.get_strategy_statistics()['total_strategies']}")
    
    print(f"\n按类型统计:")
    stats = repository.get_strategy_statistics()
    for strategy_type, count in stats["by_type"].items():
        print(f"  {strategy_type}: {count}个")
    
    # 获取匹配的策略
    print(f"\n匹配的策略:")
    matching_strategies = repository.get_matching_strategies(test_context)
    
    for i, strategy in enumerate(matching_strategies, 1):
        print(f"\n{i}. {strategy['name']}")
        print(f"   类型: {strategy['type']}")
        print(f"   描述: {strategy['description']}")
        print(f"   得分: {strategy['score']:.2f}")
        print(f"   优先级: {strategy['priority']}")
    
    # 选择最佳策略
    print(f"\n策略选择:")
    best_strategy_type = repository.select_strategy(test_context)
    print(f"选择的最佳策略类型: {best_strategy_type.value}")
    
    # 显示策略历史
    history = repository.get_strategy_history()
    if history:
        print(f"\n最近的策略选择历史 ({len(history)}条):")
        for record in history[-3:]:  # 显示最后3条
            print(f"  - {record['strategy']} (得分: {record['score']:.2f})")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()