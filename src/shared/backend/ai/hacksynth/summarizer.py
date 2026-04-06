"""
HackSynth Summarizer实现 - P1-2任务
基于HackSynth架构的结果总结器，用于分析和总结渗透测试结果
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FindingSeverity(str, Enum):
    """发现严重性枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """发现类别枚举"""
    VULNERABILITY = "vulnerability"
    CONFIGURATION = "configuration"
    CREDENTIAL = "credential"
    SERVICE = "service"
    NETWORK = "network"
    WEB = "web"
    DATABASE = "database"
    OTHER = "other"


class SecurityFinding(BaseModel):
    """安全发现模型"""
    id: str
    title: str
    description: str
    severity: FindingSeverity
    category: FindingCategory
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    impact: str = ""
    remediation: str = ""
    references: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def generate_id(cls, title: str, target: str) -> str:
        """生成发现ID"""
        import hashlib
        import base64
        
        # 创建唯一ID
        content = f"{title}_{target}_{datetime.now().timestamp()}"
        hash_obj = hashlib.sha256(content.encode())
        return base64.urlsafe_b64encode(hash_obj.digest()[:12]).decode()


class SummaryContext(BaseModel):
    """总结上下文模型"""
    target: str
    target_type: str = "unknown"
    phase: str = "unknown"
    command_executed: str = ""
    command_output: str = ""
    previous_summary: Optional[str] = None
    findings: List[SecurityFinding] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def output_length(self) -> int:
        """获取输出长度"""
        return len(self.command_output)


class SummaryResult(BaseModel):
    """总结结果模型"""
    summary: str
    key_findings: List[SecurityFinding]
    next_phase_recommendation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)


class HackSynthSummarizer(ABC):
    """HackSynth Summarizer抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Summarizer
        
        Args:
            config: Summarizer配置
        """
        self.config = config
        self.summary_history: List[Dict[str, Any]] = []
        self.finding_patterns = self._load_finding_patterns()
        
        logger.info(f"HackSynth Summarizer初始化完成: {self.__class__.__name__}")
    
    def _load_finding_patterns(self) -> Dict[str, Dict[str, Any]]:
        """加载发现模式"""
        return {
            "sql_injection": {
                "patterns": [
                    r"SQL injection",
                    r"SQLi",
                    r"parameter.*vulnerable.*SQL",
                    r"database.*error.*in.*response"
                ],
                "severity": FindingSeverity.HIGH,
                "category": FindingCategory.VULNERABILITY
            },
            "xss": {
                "patterns": [
                    r"XSS",
                    r"cross.*site.*scripting",
                    r"script.*injection"
                ],
                "severity": FindingSeverity.MEDIUM,
                "category": FindingCategory.VULNERABILITY
            },
            "open_port": {
                "patterns": [
                    r"(\d+)/tcp.*open",
                    r"port.*(\d+).*open"
                ],
                "severity": FindingSeverity.INFO,
                "category": FindingCategory.NETWORK
            },
            "service_version": {
                "patterns": [
                    r"(\d+\.\d+\.\d+)",
                    r"version.*(\d+\.\d+)"
                ],
                "severity": FindingSeverity.INFO,
                "category": FindingCategory.SERVICE
            },
            "vulnerable_service": {
                "patterns": [
                    r"vulnerable",
                    r"CVE-\d+-\d+",
                    r"exploit",
                    r"critical.*vulnerability"
                ],
                "severity": FindingSeverity.HIGH,
                "category": FindingCategory.VULNERABILITY
            },
            "credential_leak": {
                "patterns": [
                    r"password.*:",
                    r"username.*:",
                    r"credential",
                    r"login.*successful"
                ],
                "severity": FindingSeverity.CRITICAL,
                "category": FindingCategory.CREDENTIAL
            },
            "directory_listing": {
                "patterns": [
                    r"directory.*listing",
                    r"Index of",
                    r"Parent Directory"
                ],
                "severity": FindingSeverity.MEDIUM,
                "category": FindingCategory.CONFIGURATION
            },
            "web_technology": {
                "patterns": [
                    r"Apache.*(\d+\.\d+)",
                    r"nginx.*(\d+\.\d+)",
                    r"PHP.*(\d+\.\d+)",
                    r"WordPress.*(\d+\.\d+)"
                ],
                "severity": FindingSeverity.INFO,
                "category": FindingCategory.WEB
            }
        }
    
    @abstractmethod
    async def summarize(
        self,
        context: SummaryContext
    ) -> SummaryResult:
        """
        总结命令执行结果
        
        Args:
            context: 总结上下文
            
        Returns:
            总结结果
        """
        pass
    
    @abstractmethod
    async def extract_findings(
        self,
        command_output: str,
        target: str
    ) -> List[SecurityFinding]:
        """
        从命令输出中提取安全发现
        
        Args:
            command_output: 命令输出
            target: 目标地址
            
        Returns:
            安全发现列表
        """
        pass
    
    def analyze_command_output(
        self,
        command: str,
        output: str,
        target: str
    ) -> Dict[str, Any]:
        """
        分析命令输出
        
        Args:
            command: 执行的命令
            output: 命令输出
            target: 目标地址
            
        Returns:
            分析结果
        """
        analysis = {
            "command": command,
            "target": target,
            "output_length": len(output),
            "line_count": output.count('\n') + 1,
            "findings_count": 0,
            "severity_distribution": {},
            "tool_used": self._extract_tool_from_command(command),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # 提取发现
        findings = self._extract_findings_sync(output, target)
        analysis["findings_count"] = len(findings)
        
        # 统计严重性分布
        for finding in findings:
            severity = finding.severity.value
            analysis["severity_distribution"][severity] = analysis["severity_distribution"].get(severity, 0) + 1
        
        # 分析输出特征
        analysis["output_features"] = self._analyze_output_features(output)
        
        return analysis
    
    def _extract_findings_sync(self, output: str, target: str) -> List[SecurityFinding]:
        """同步提取发现"""
        findings = []
        
        for finding_name, pattern_info in self.finding_patterns.items():
            patterns = pattern_info["patterns"]
            severity = pattern_info["severity"]
            category = pattern_info["category"]
            
            for pattern in patterns:
                matches = re.finditer(pattern, output, re.IGNORECASE)
                for match in matches:
                    # 提取匹配内容
                    matched_text = match.group(0)
                    if len(matched_text) > 200:
                        matched_text = matched_text[:200] + "..."
                    
                    # 创建发现
                    title = self._generate_finding_title(finding_name, matched_text)
                    finding = SecurityFinding(
                        id=SecurityFinding.generate_id(title, target),
                        title=title,
                        description=f"在命令输出中发现 {finding_name} 模式",
                        severity=severity,
                        category=category,
                        evidence=matched_text,
                        confidence=0.7,  # 基础置信度
                        impact=self._get_finding_impact(finding_name, severity),
                        remediation=self._get_finding_remediation(finding_name)
                    )
                    
                    findings.append(finding)
        
        # 去重（基于证据文本）
        unique_findings = []
        seen_evidence = set()
        
        for finding in findings:
            evidence_hash = hash(finding.evidence[:100])
            if evidence_hash not in seen_evidence:
                seen_evidence.add(evidence_hash)
                unique_findings.append(finding)
        
        return unique_findings[:10]  # 限制返回数量
    
    def _generate_finding_title(self, finding_name: str, evidence: str) -> str:
        """生成发现标题"""
        title_map = {
            "sql_injection": "SQL注入漏洞",
            "xss": "跨站脚本攻击漏洞",
            "open_port": "开放端口",
            "service_version": "服务版本信息",
            "vulnerable_service": "易受攻击的服务",
            "credential_leak": "凭证泄露",
            "directory_listing": "目录列表暴露",
            "web_technology": "Web技术栈信息"
        }
        
        base_title = title_map.get(finding_name, finding_name.replace('_', ' ').title())
        
        # 从证据中提取关键信息
        if finding_name == "open_port":
            port_match = re.search(r'(\d+)', evidence)
            if port_match:
                return f"开放端口 {port_match.group(1)}"
        
        elif finding_name == "service_version":
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', evidence)
            if version_match:
                return f"服务版本 {version_match.group(1)}"
        
        return base_title
    
    def _get_finding_impact(self, finding_name: str, severity: FindingSeverity) -> str:
        """获取发现影响"""
        impact_map = {
            "sql_injection": "可能导致数据库信息泄露、数据篡改或服务器完全控制",
            "xss": "可能导致用户会话劫持、恶意脚本执行或信息泄露",
            "open_port": "暴露潜在的攻击面，可能被用于进一步攻击",
            "vulnerable_service": "可能被利用获取系统访问权限或执行恶意代码",
            "credential_leak": "可能导致未授权访问、权限提升或数据泄露",
            "directory_listing": "可能暴露敏感文件、配置信息或源代码",
            "critical": "可能导致系统完全控制、数据泄露或服务中断",
            "high": "可能导致敏感信息泄露或权限提升",
            "medium": "可能被用于进一步攻击或信息收集",
            "low": "信息泄露风险较低，但仍需关注"
        }
        
        if finding_name in impact_map:
            return impact_map[finding_name]
        
        # 基于严重性返回通用影响
        severity_impact = {
            FindingSeverity.CRITICAL: impact_map["critical"],
            FindingSeverity.HIGH: impact_map["high"],
            FindingSeverity.MEDIUM: impact_map["medium"],
            FindingSeverity.LOW: impact_map["low"],
            FindingSeverity.INFO: "信息性发现，风险较低"
        }
        
        return severity_impact.get(severity, "未知影响")
    
    def _get_finding_remediation(self, finding_name: str) -> str:
        """获取修复建议"""
        remediation_map = {
            "sql_injection": "使用参数化查询或预编译语句，实施输入验证和过滤",
            "xss": "实施输出编码，使用内容安全策略(CSP)，验证和过滤用户输入",
            "open_port": "关闭不必要的端口，配置防火墙规则，实施网络访问控制",
            "vulnerable_service": "更新到最新版本，应用安全补丁，禁用不必要的服务",
            "credential_leak": "重置泄露的凭证，实施强密码策略，启用多因素认证",
            "directory_listing": "禁用目录列表，配置适当的访问控制，移除敏感文件",
            "web_technology": "保持软件更新，应用安全配置，监控安全公告"
        }
        
        return remediation_map.get(finding_name, "实施适当的安全控制和监控")
    
    def _extract_tool_from_command(self, command: str) -> str:
        """从命令中提取工具名称"""
        command_lower = command.lower()
        
        tool_patterns = {
            "nmap": ["nmap "],
            "whatweb": ["whatweb "],
            "sqlmap": ["sqlmap "],
            "nuclei": ["nuclei "],
            "dirsearch": ["dirsearch ", "dirb ", "gobuster "],
            "nikto": ["nikto "],
            "hydra": ["hydra "],
            "metasploit": ["msfconsole", "msf "]
        }
        
        for tool, patterns in tool_patterns.items():
            for pattern in patterns:
                if pattern in command_lower:
                    return tool
        
        return "unknown"
    
    def _analyze_output_features(self, output: str) -> Dict[str, Any]:
        """分析输出特征"""
        features = {
            "has_error": False,
            "has_warning": False,
            "has_success": False,
            "has_json": False,
            "has_xml": False,
            "has_html": False,
            "keyword_counts": {}
        }
        
        output_lower = output.lower()
        
        # 检查错误和警告
        error_patterns = ["error", "failed", "exception", "cannot", "unable"]
        warning_patterns = ["warning", "caution", "notice", "deprecated"]
        success_patterns = ["success", "completed", "finished", "ok", "done"]
        
        for pattern in error_patterns:
            if pattern in output_lower:
                features["has_error"] = True
                features["keyword_counts"][pattern] = output_lower.count(pattern)
        
        for pattern in warning_patterns:
            if pattern in output_lower:
                features["has_warning"] = True
                features["keyword_counts"][pattern] = output_lower.count(pattern)
        
        for pattern in success_patterns:
            if pattern in output_lower:
                features["has_success"] = True
                features["keyword_counts"][pattern] = output_lower.count(pattern)
        
        # 检查数据格式
        if output.strip().startswith('{') or output.strip().startswith('['):
            features["has_json"] = True
        
        if "<xml" in output_lower or "<?xml" in output_lower:
            features["has_xml"] = True
        
        if "<html" in output_lower or "<!doctype" in output_lower:
            features["has_html"] = True
        
        return features
    
    def record_summary(self, context: SummaryContext, result: SummaryResult):
        """记录总结历史"""
        summary_record = {
            "timestamp": datetime.now().isoformat(),
            "target": context.target,
            "phase": context.phase,
            "command": context.command_executed[:100] if context.command_executed else "",
            "output_length": context.output_length,
            "findings_count": len(result.key_findings),
            "summary_length": len(result.summary),
            "confidence_score": result.confidence_score,
            "next_phase": result.next_phase_recommendation,
            "severity_summary": self._calculate_severity_summary(result.key_findings)
        }
        
        self.summary_history.append(summary_record)
        
        # 限制历史记录大小
        if len(self.summary_history) > 100:
            self.summary_history = self.summary_history[-100:]
    
    def _calculate_severity_summary(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """计算严重性摘要"""
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for finding in findings:
            severity = finding.severity.value
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """获取总结统计信息"""
        if not self.summary_history:
            return {"total_summaries": 0}
        
        total_summaries = len(self.summary_history)
        total_findings = sum(record.get("findings_count", 0) for record in self.summary_history)
        avg_confidence = sum(record.get("confidence_score", 0) for record in self.summary_history) / total_summaries
        
        # 统计阶段分布
        phase_distribution = {}
        for record in self.summary_history:
            phase = record.get("phase", "unknown")
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        
        return {
            "total_summaries": total_summaries,
            "total_findings": total_findings,
            "average_findings_per_summary": total_findings / total_summaries if total_summaries > 0 else 0,
            "average_confidence": avg_confidence,
            "phase_distribution": phase_distribution,
            "recent_summaries": self.summary_history[-5:] if len(self.summary_history) >= 5 else self.summary_history
        }
    
    def determine_next_phase(self, current_phase: str, findings: List[SecurityFinding]) -> str:
        """确定下一个阶段"""
        phase_sequence = [
            "reconnaissance",
            "scanning", 
            "vulnerability_assessment",
            "exploitation",
            "post_exploitation"
        ]
        
        try:
            current_index = phase_sequence.index(current_phase)
        except ValueError:
            current_index = 0
        
        # 检查是否有关键发现
        critical_findings = [f for f in findings if f.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]]
        
        if current_phase == "reconnaissance":
            # 如果有发现，进入扫描阶段
            if findings:
                return "scanning"
            else:
                return "reconnaissance"
        
        elif current_phase == "scanning":
            # 如果有漏洞发现，进入漏洞评估
            if any(f.category == FindingCategory.VULNERABILITY for f in findings):
                return "vulnerability_assessment"
            else:
                return "scanning"
        
        elif current_phase == "vulnerability_assessment":
            # 如果有高严重性漏洞，进入利用阶段
            if critical_findings:
                return "exploitation"
            else:
                return "vulnerability_assessment"
        
        elif current_phase == "exploitation":
            # 如果获得凭证或shell，进入后渗透
            if any(f.category == FindingCategory.CREDENTIAL for f in findings):
                return "post_exploitation"
            else:
                return "exploitation"
        
        elif current_phase == "post_exploitation":
            # 后渗透阶段可以持续
            return "post_exploitation"
        
        # 默认进入下一个阶段
        next_index = min(current_index + 1, len(phase_sequence) - 1)
        return phase_sequence[next_index]
    
    def get_summarizer_info(self) -> Dict[str, Any]:
        """获取Summarizer信息"""
        return {
            "summarizer_type": self.__class__.__name__,
            "finding_patterns_count": len(self.finding_patterns),
            "summary_history_count": len(self.summary_history),
            "config": self.config.get("name", "unknown")
        }

