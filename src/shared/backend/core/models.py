# -*- coding: utf-8 -*-
"""
数据模型定义
用于解决代码重复问题，提供统一的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TypedDict


# ==================== 类型别名定义 ====================

class ToolConfig(TypedDict):
    """工具配置类型"""
    phase: str
    duration: str
    description_template: str


class StrategyTemplate(TypedDict):
    """策略模板类型"""
    name: str
    description: str
    tools: List[str]
    priority: int


class AttackStep(TypedDict):
    """攻击步骤类型"""
    step: int
    tool: str
    phase: str
    duration: str
    description: str
    success: bool


class PortInfo(TypedDict):
    """端口信息类型"""
    port: int
    service: str
    state: str


class VulnerabilityInfo(TypedDict):
    """漏洞信息类型"""
    name: str
    severity: str


# ==================== 数据模型类 ====================

@dataclass
class AttackPath:
    """攻击路径数据模型（统一版本）"""
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackPath':
        """从字典创建AttackPath实例"""
        return cls(
            path_id=data.get("path_id", 0),
            name=data.get("name", ""),
            strategy=data.get("strategy", ""),
            steps=data.get("steps", []),
            target_focus=data.get("target_focus", ""),
            difficulty=data.get("difficulty", "medium"),
            estimated_time=data.get("estimated_time", "30分钟"),
            success_rate=data.get("success_rate", 0.5),
            step_count=data.get("step_count", len(data.get("steps", [])))
        )


@dataclass
class VulnerabilityAnalysis:
    """漏洞分析数据模型"""
    critical: List[str] = field(default_factory=list)
    high: List[str] = field(default_factory=list)
    medium: List[str] = field(default_factory=list)
    low: List[str] = field(default_factory=list)
    total: int = 0
    
    def add_vulnerability(self, name: str, severity: str) -> None:
        """添加漏洞到相应严重级别列表"""
        severity_lower = severity.lower()
        
        if severity_lower == "critical":
            self.critical.append(name)
        elif severity_lower == "high":
            self.high.append(name)
        elif severity_lower == "medium":
            self.medium.append(name)
        elif severity_lower == "low":
            self.low.append(name)
        
        self.total += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取漏洞摘要"""
        return {
            "critical": self.critical,
            "high": self.high,
            "medium": self.medium,
            "low": self.low,
            "total": self.total
        }


@dataclass
class ScanAnalysis:
    """扫描分析数据模型"""
    open_ports: List[PortInfo] = field(default_factory=list)
    web_technologies: List[str] = field(default_factory=list)
    vulnerabilities: VulnerabilityAnalysis = field(default_factory=VulnerabilityAnalysis)
    has_web: bool = False
    has_database: bool = False
    has_cms: bool = False
    cms_type: Optional[str] = None
    waf_detected: bool = False
    waf_type: Optional[str] = None
    attack_surface: float = 5.0
    
    def update_from_nmap(self, nmap_result: Dict[str, Any]) -> None:
        """从nmap结果更新分析"""
        if "ports" in nmap_result:
            ports = nmap_result["ports"]
            self.open_ports = ports
            
            # 检查Web端口
            web_ports = {80, 443, 8080, 8443}
            for port_info in ports:
                if isinstance(port_info, dict):
                    port = port_info.get("port")
                    if port in web_ports:
                        self.has_web = True
                    
                    # 检查数据库端口
                    db_ports = {3306, 5432, 27017, 1433}
                    if port in db_ports:
                        self.has_database = True
    
    def update_from_whatweb(self, whatweb_result: Dict[str, Any]) -> None:
        """从whatweb结果更新分析"""
        if "fingerprint" in whatweb_result:
            fingerprint = whatweb_result["fingerprint"]
            
            # 提取技术栈
            if fingerprint.get("web_server"):
                self.web_technologies.append(f"服务器: {fingerprint['web_server']}")
            
            if fingerprint.get("language"):
                langs = fingerprint["language"][:2]
                self.web_technologies.append(f"语言: {', '.join(langs)}")
            
            if fingerprint.get("cms"):
                self.has_cms = True
                self.cms_type = fingerprint["cms"][0] if fingerprint["cms"] else None
                self.web_technologies.append(f"CMS: {self.cms_type}")
    
    def update_from_nuclei(self, nuclei_result: Dict[str, Any]) -> None:
        """从nuclei结果更新分析"""
        if "vulnerabilities" in nuclei_result:
            vulnerabilities = nuclei_result["vulnerabilities"]
            
            for vuln in vulnerabilities:
                if isinstance(vuln, dict):
                    severity = vuln.get("severity", "").lower()
                    name = vuln.get("name", "未知漏洞")
                    self.vulnerabilities.add_vulnerability(name, severity)
    
    def update_from_wafw00f(self, waf_result: Dict[str, Any]) -> None:
        """从wafw00f结果更新分析"""
        self.waf_detected = waf_result.get("waf_detected", False)
        self.waf_type = waf_result.get("waf_type")
    
    def update_from_sqlmap(self, sqlmap_result: Dict[str, Any]) -> None:
        """从sqlmap结果更新分析"""
        if "injections" in sqlmap_result and sqlmap_result["injections"]:
            # 标记有SQL注入漏洞
            self.vulnerabilities.add_vulnerability("SQL注入漏洞", "high")


@dataclass
class PathEvaluation:
    """路径评估数据模型"""
    id: int
    path: List[AttackStep]
    type: str
    score: float
    step_count: int
    tools_used: List[str]
    estimated_duration: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "path": self.path,
            "type": self.type,
            "score": self.score,
            "step_count": self.step_count,
            "tools_used": self.tools_used,
            "estimated_duration": self.estimated_duration
        }


@dataclass
class DecisionInfo:
    """决策信息数据模型"""
    selected_path_type: str
    selected_score: float
    confidence: float
    selection_reasons: List[str]
    path_comparison: List[Dict[str, Any]]
    decision_factors: Dict[str, float]
    rule_engine_used: bool
    rule_engine_model: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "selected_path_type": self.selected_path_type,
            "selected_score": self.selected_score,
            "confidence": self.confidence,
            "selection_reasons": self.selection_reasons,
            "path_comparison": self.path_comparison,
            "decision_factors": self.decision_factors,
            "rule_engine_used": self.rule_engine_used,
            "rule_engine_model": self.rule_engine_model
        }


@dataclass
class TargetAnalysis:
    """目标分析数据模型"""
    attack_surface: float
    open_ports: int
    vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    has_cms: bool
    cms_type: Optional[str]
    waf_detected: bool
    waf_type: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "attack_surface": self.attack_surface,
            "open_ports": self.open_ports,
            "vulnerabilities": self.vulnerabilities,
            "critical_vulnerabilities": self.critical_vulnerabilities,
            "high_vulnerabilities": self.high_vulnerabilities,
            "has_cms": self.has_cms,
            "cms_type": self.cms_type,
            "waf_detected": self.waf_detected,
            "waf_type": self.waf_type
        }


@dataclass
class ExecutionSummary:
    """执行摘要数据模型"""
    total_paths_generated: int
    evolution_applied: bool
    best_path_score: float
    estimated_duration: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "total_paths_generated": self.total_paths_generated,
            "evolution_applied": self.evolution_applied,
            "best_path_score": self.best_path_score,
            "estimated_duration": self.estimated_duration
        }


@dataclass
class AttackChainResult:
    """攻击链结果数据模型"""
    attack_chain: List[AttackStep]
    analysis: ScanAnalysis
    decision: DecisionInfo
    target_analysis: TargetAnalysis
    execution_summary: ExecutionSummary
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "attack_chain": self.attack_chain,
            "analysis": self.analysis.to_dict() if hasattr(self.analysis, 'to_dict') else self.analysis,
            "decision": self.decision.to_dict(),
            "target_analysis": self.target_analysis.to_dict(),
            "execution_summary": self.execution_summary.to_dict()
        }