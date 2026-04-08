# 智能决策引擎
# 实现基于上下文的动态决策、策略选择和反馈学习

import json
import time
from typing import Dict, List, Any, Optional

class ContextManager:
    """上下文管理器"""
    
    def analyze(self, scan_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """分析上下文信息"""
        analysis = {
            "target_type": self._identify_target_type(scan_data),
            "tech_stack": self._identify_tech_stack(scan_data),
            "defenses": self._detect_defenses(scan_data),
            "environment": self._analyze_environment(context),
            "constraints": self._identify_constraints(context)
        }
        return analysis
    
    def _identify_target_type(self, scan_data: Dict[str, Any]) -> List[str]:
        """识别目标类型"""
        target_types = []
        
        # 检查Web应用
        if scan_data.get("web_ports"):
            target_types.append("web")
        
        # 检查数据库服务
        database_ports = [3306, 5432, 1433, 1521, 6379]
        for port in scan_data.get("open_ports", []):
            if port in database_ports:
                target_types.append("database")
                break
        
        # 检查其他服务
        if scan_data.get("open_ports"):
            target_types.append("services")
        
        # 检查内网环境
        if scan_data.get("is_internal"):
            target_types.append("internal")
        
        return target_types
    
    def _identify_tech_stack(self, scan_data: Dict[str, Any]) -> Dict[str, str]:
        """识别技术栈"""
        tech_stack = {}
        
        # 从HTTP响应中识别Web技术
        for port_info in scan_data.get("port_info", []):
            if "http" in port_info.get("service", "").lower():
                headers = port_info.get("headers", {})
                if "server" in headers:
                    tech_stack["web_server"] = headers["server"]
                if "x-powered-by" in headers:
                    tech_stack["framework"] = headers["x-powered-by"]
        
        return tech_stack
    
    def _detect_defenses(self, scan_data: Dict[str, Any]) -> List[str]:
        """检测防御措施"""
        defenses = []
        
        # 检查WAF
        for port_info in scan_data.get("port_info", []):
            if "http" in port_info.get("service", "").lower():
                headers = port_info.get("headers", {})
                if any(key in headers for key in ["x-waf", "x-websecurity", "server"]):
                    defenses.append("waf")
        
        return defenses
    
    def _analyze_environment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析环境信息"""
        return {
            "network": context.get("network", "unknown"),
            "time_constraint": context.get("time_constraint", "unlimited"),
            "compliance": context.get("compliance", []),
            "resource_limit": context.get("resource_limit", {})
        }
    
    def _identify_constraints(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """识别约束条件"""
        return {
            "stealth_required": context.get("stealth_required", False),
            "avoid_disruption": context.get("avoid_disruption", True),
            "time_limit": context.get("time_limit", None),
            "resource_limit": context.get("resource_limit", {})
        }

class StrategyRepository:
    """策略库"""
    
    def __init__(self):
        self.strategies = {
            "aggressive": {
                "name": "进攻型策略",
                "description": "全面渗透测试，使用多种工具和技术",
                "suitable_for": ["web", "services", "database", "internal"],
                "risk_level": "high",
                "time_intensive": True
            },
            "defensive": {
                "name": "防御型策略",
                "description": "安全评估，避免破坏性操作",
                "suitable_for": ["web", "services", "database"],
                "risk_level": "low",
                "time_intensive": False
            },
            "stealthy": {
                "name": "隐蔽型策略",
                "description": "隐蔽渗透，避免触发告警",
                "suitable_for": ["web", "services", "internal"],
                "risk_level": "medium",
                "time_intensive": True
            },
            "fast": {
                "name": "快速型策略",
                "description": "时间受限的快速扫描",
                "suitable_for": ["web", "services"],
                "risk_level": "low",
                "time_intensive": False
            }
        }
    
    def select_strategy(self, context_analysis: Dict[str, Any]) -> str:
        """选择策略"""
        target_types = context_analysis["target_type"]
        constraints = context_analysis["constraints"]
        environment = context_analysis["environment"]
        
        # 基于约束条件选择策略
        if constraints.get("stealth_required"):
            return "stealthy"
        
        if constraints.get("time_limit") and constraints["time_limit"] < 3600:  # 小于1小时
            return "fast"
        
        if constraints.get("avoid_disruption"):
            return "defensive"
        
        # 基于目标类型选择策略
        if "internal" in target_types:
            return "stealthy"
        
        if "database" in target_types:
            return "defensive"
        
        # 默认策略
        return "aggressive"

class FeedbackLoop:
    """反馈学习机制"""
    
    def __init__(self):
        self.feedback_history = []
    
    def record_decision(self, decision: Dict[str, Any], context_analysis: Dict[str, Any]):
        """记录决策和上下文"""
        feedback = {
            "timestamp": time.time(),
            "decision": decision,
            "context": context_analysis,
            "outcome": None  # 后续会更新
        }
        self.feedback_history.append(feedback)
    
    def record_outcome(self, decision_id: str, outcome: Dict[str, Any]):
        """记录决策结果"""
        for feedback in self.feedback_history:
            if feedback["decision"].get("id") == decision_id:
                feedback["outcome"] = outcome
                break
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        if not self.feedback_history:
            return {"total_decisions": 0, "success_rate": 0.0}
        
        total = len(self.feedback_history)
        successful = sum(1 for f in self.feedback_history if f.get("outcome", {}).get("success"))
        
        return {
            "total_decisions": total,
            "success_rate": successful / total if total > 0 else 0.0
        }

class DecisionEngine:
    """决策引擎"""
    
    def __init__(self):
        self.strategy_repository = StrategyRepository()
        self.context_manager = ContextManager()
        self.feedback_loop = FeedbackLoop()
    
    def make_decision(self, scan_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """做出决策"""
        # 1. 上下文理解
        context_analysis = self.context_manager.analyze(scan_data, context)
        
        # 2. 策略选择
        strategy = self.strategy_repository.select_strategy(context_analysis)
        
        # 3. 风险评估
        risk_assessment = self._assess_risk(context_analysis)
        
        # 4. 决策生成
        decision = self._generate_decision(strategy, risk_assessment, context_analysis)
        
        # 5. 反馈收集
        self.feedback_loop.record_decision(decision, context_analysis)
        
        return decision
    
    def _assess_risk(self, context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险"""
        risk_factors = {
            "target_value": self._assess_target_value(context_analysis),
            "detection_risk": self._assess_detection_risk(context_analysis),
            "disruption_risk": self._assess_disruption_risk(context_analysis),
            "legal_risk": self._assess_legal_risk(context_analysis)
        }
        
        # 计算总体风险
        total_risk = sum(risk_factors.values()) / len(risk_factors)
        
        return {
            "risk_factors": risk_factors,
            "total_risk": total_risk,
            "risk_level": self._get_risk_level(total_risk)
        }
    
    def _assess_target_value(self, context_analysis: Dict[str, Any]) -> float:
        """评估目标价值"""
        target_types = context_analysis["target_type"]
        value = 0.0
        
        if "database" in target_types:
            value += 0.8
        if "internal" in target_types:
            value += 0.7
        if "web" in target_types:
            value += 0.5
        if "services" in target_types:
            value += 0.3
        
        return min(value, 1.0)
    
    def _assess_detection_risk(self, context_analysis: Dict[str, Any]) -> float:
        """评估被检测风险"""
        defenses = context_analysis["defenses"]
        risk = 0.0
        
        if "waf" in defenses:
            risk += 0.6
        
        return min(risk, 1.0)
    
    def _assess_disruption_risk(self, context_analysis: Dict[str, Any]) -> float:
        """评估破坏性风险"""
        constraints = context_analysis["constraints"]
        if constraints.get("avoid_disruption"):
            return 0.2
        return 0.6
    
    def _assess_legal_risk(self, context_analysis: Dict[str, Any]) -> float:
        """评估法律风险"""
        compliance = context_analysis["environment"].get("compliance", [])
        if "gdpr" in compliance or "pci_dss" in compliance:
            return 0.7
        return 0.3
    
    def _get_risk_level(self, total_risk: float) -> str:
        """获取风险等级"""
        if total_risk >= 0.7:
            return "high"
        elif total_risk >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _generate_decision(self, strategy: str, risk_assessment: Dict[str, Any], context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成决策"""
        decision = {
            "id": f"decision_{int(time.time())}",
            "strategy": strategy,
            "risk_assessment": risk_assessment,
            "context_analysis": context_analysis,
            "recommended_actions": self._generate_recommended_actions(strategy, context_analysis),
            "estimated_time": self._estimate_time(strategy, context_analysis),
            "confidence": self._calculate_confidence(strategy, risk_assessment)
        }
        
        return decision
    
    def _generate_recommended_actions(self, strategy: str, context_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成推荐动作"""
        actions = []
        target_types = context_analysis["target_type"]
        
        # 根据策略和目标类型生成推荐动作
        if strategy == "aggressive":
            if "web" in target_types:
                actions.append({"action": "web_vulnerability_scan", "tool": "nikto", "priority": "high"})
            if "services" in target_types:
                actions.append({"action": "service_enumeration", "tool": "nmap", "priority": "high"})
            if "database" in target_types:
                actions.append({"action": "database_vulnerability_scan", "tool": "sqlmap", "priority": "medium"})
        
        elif strategy == "defensive":
            if "web" in target_types:
                actions.append({"action": "passive_web_scan", "tool": "whatweb", "priority": "medium"})
            if "services" in target_types:
                actions.append({"action": "service_discovery", "tool": "nmap", "priority": "medium"})
        
        elif strategy == "stealthy":
            if "web" in target_types:
                actions.append({"action": "stealth_web_scan", "tool": "nikto", "priority": "medium"})
            if "internal" in target_types:
                actions.append({"action": "network_discovery", "tool": "nmap", "priority": "high"})
        
        elif strategy == "fast":
            if "web" in target_types:
                actions.append({"action": "quick_web_scan", "tool": "nikto", "priority": "high"})
            if "services" in target_types:
                actions.append({"action": "quick_service_scan", "tool": "nmap", "priority": "high"})
        
        return actions
    
    def _estimate_time(self, strategy: str, context_analysis: Dict[str, Any]) -> int:
        """估计执行时间（秒）"""
        base_time = {
            "aggressive": 3600,  # 1小时
            "defensive": 1800,    # 30分钟
            "stealthy": 5400,     # 1.5小时
            "fast": 600           # 10分钟
        }
        
        # 根据目标类型调整时间
        target_types = context_analysis["target_type"]
        time_multiplier = 1.0
        
        if "database" in target_types:
            time_multiplier += 0.5
        if "internal" in target_types:
            time_multiplier += 0.8
        if "services" in target_types:
            time_multiplier += 0.3
        
        return int(base_time[strategy] * time_multiplier)
    
    def _calculate_confidence(self, strategy: str, risk_assessment: Dict[str, Any]) -> float:
        """计算决策置信度"""
        # 基于策略和风险评估计算置信度
        strategy_confidence = {
            "aggressive": 0.8,
            "defensive": 0.9,
            "stealthy": 0.7,
            "fast": 0.6
        }
        
        # 风险越高，置信度越低
        risk_factor = 1.0 - risk_assessment["total_risk"] * 0.3
        
        return strategy_confidence[strategy] * risk_factor
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        return self.feedback_loop.get_feedback_stats()
