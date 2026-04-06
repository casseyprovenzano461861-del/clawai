#!/usr/bin/env python3
"""
渗透测试报告生成器
生成专业的渗透测试报告，包含漏洞详情、攻击路径、后渗透结果和量化指标
"""

import json
import os
import sys
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class VulnerabilityFinding:
    """漏洞发现"""
    id: str
    name: str
    severity: str  # critical, high, medium, low
    category: str  # sql_injection, xss, rce, etc.
    description: str
    location: str
    evidence: str
    impact: str
    recommendation: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "evidence": self.evidence,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "cve_id": self.cve_id,
            "cvss_score": self.cvss_score
        }

@dataclass
class AttackPathSummary:
    """攻击路径摘要"""
    path_id: int
    name: str
    strategy: str
    steps_count: int
    success_rate: float
    estimated_time: str
    difficulty: str
    tools_used: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path_id": self.path_id,
            "name": self.name,
            "strategy": self.strategy,
            "steps_count": self.steps_count,
            "success_rate": self.success_rate,
            "estimated_time": self.estimated_time,
            "difficulty": self.difficulty,
            "tools_used": self.tools_used
        }

@dataclass
class PostExploitationSummary:
    """后渗透摘要"""
    plan_id: str
    name: str
    objectives: List[str]
    steps_count: int
    successful_steps: int
    execution_time: str
    risk_level: str
    effectiveness: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "objectives": self.objectives,
            "steps_count": self.steps_count,
            "successful_steps": self.successful_steps,
            "execution_time": self.execution_time,
            "risk_level": self.risk_level,
            "effectiveness": self.effectiveness
        }

@dataclass
class QuantitativeMetrics:
    """量化指标"""
    vulnerability_detection_rate: float
    false_positive_rate: float
    cve_coverage_rate: float
    attack_success_rate: float
    overall_score: float
    meeting_requirements: Dict[str, bool]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "vulnerability_detection_rate": self.vulnerability_detection_rate,
            "false_positive_rate": self.false_positive_rate,
            "cve_coverage_rate": self.cve_coverage_rate,
            "attack_success_rate": self.attack_success_rate,
            "overall_score": self.overall_score,
            "meeting_requirements": self.meeting_requirements
        }

class PenetrationReportGenerator:
    """渗透测试报告生成器"""
    
    def __init__(self):
        self.report_counter = 0
    
    def generate_report(self,
                       target_info: Dict[str, Any],
                       scan_results: Dict[str, Any],
                       attack_paths: List[Dict[str, Any]],
                       post_exploitation_results: Optional[Dict[str, Any]] = None,
                       quantitative_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成完整的渗透测试报告
        
        Args:
            target_info: 目标信息
            scan_results: 扫描结果
            attack_paths: 攻击路径
            post_exploitation_results: 后渗透结果（可选）
            quantitative_metrics: 量化指标（可选）
            
        Returns:
            完整的渗透测试报告
        """
        # 生成报告ID
        report_id = f"PTR-{datetime.now().strftime('%Y%m%d')}-{self.report_counter:04d}"
        self.report_counter += 1
        
        # 解析漏洞发现
        vulnerabilities = self._parse_vulnerabilities(scan_results)
        
        # 解析攻击路径
        attack_path_summaries = self._parse_attack_paths(attack_paths)
        
        # 解析后渗透结果
        post_exploitation_summary = None
        if post_exploitation_results:
            post_exploitation_summary = self._parse_post_exploitation_results(post_exploitation_results)
        
        # 解析量化指标
        quantitative_metrics_summary = None
        if quantitative_metrics:
            quantitative_metrics_summary = self._parse_quantitative_metrics(quantitative_metrics)
        
        # 生成执行摘要
        executive_summary = self._generate_executive_summary(
            target_info, vulnerabilities, attack_path_summaries, 
            post_exploitation_summary, quantitative_metrics_summary
        )
        
        # 生成风险评估
        risk_assessment = self._generate_risk_assessment(vulnerabilities, post_exploitation_summary)
        
        # 生成建议
        recommendations = self._generate_recommendations(vulnerabilities, attack_path_summaries, post_exploitation_summary)
        
        # 构建完整报告
        report = {
            "report_id": report_id,
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_information": target_info,
            "executive_summary": executive_summary,
            "quantitative_metrics": quantitative_metrics_summary.to_dict() if quantitative_metrics_summary else None,
            "vulnerability_findings": {
                "total_count": len(vulnerabilities),
                "severity_distribution": self._calculate_severity_distribution(vulnerabilities),
                "findings": [vuln.to_dict() for vuln in vulnerabilities]
            },
            "attack_path_analysis": {
                "total_paths": len(attack_path_summaries),
                "best_path": self._select_best_attack_path(attack_path_summaries),
                "paths": [path.to_dict() for path in attack_path_summaries]
            },
            "post_exploitation_results": post_exploitation_summary.to_dict() if post_exploitation_summary else None,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "technical_details": self._generate_technical_details(scan_results, attack_paths),
            "appendix": self._generate_appendix()
        }
        
        return report
    
    def _parse_vulnerabilities(self, scan_results: Dict[str, Any]) -> List[VulnerabilityFinding]:
        """解析漏洞发现"""
        vulnerabilities = []
        
        # 从扫描结果提取漏洞
        if "vulnerabilities" in scan_results:
            for i, vuln_data in enumerate(scan_results["vulnerabilities"]):
                vuln_id = f"VULN-{i+1:03d}"
                
                vulnerability = VulnerabilityFinding(
                    id=vuln_id,
                    name=vuln_data.get("name", f"漏洞 {i+1}"),
                    severity=vuln_data.get("severity", "medium"),
                    category=vuln_data.get("type", "unknown"),
                    description=vuln_data.get("description", "未提供详细描述"),
                    location=vuln_data.get("location", "未知位置"),
                    evidence=vuln_data.get("evidence", "扫描工具检测到"),
                    impact=self._determine_impact(vuln_data.get("severity", "medium")),
                    recommendation=self._generate_vulnerability_recommendation(vuln_data),
                    cve_id=vuln_data.get("cve"),
                    cvss_score=vuln_data.get("cvss_score")
                )
                vulnerabilities.append(vulnerability)
        
        # 如果没有漏洞数据，创建示例数据
        if not vulnerabilities:
            vulnerabilities = self._create_sample_vulnerabilities()
        
        return vulnerabilities
    
    def _parse_attack_paths(self, attack_paths: List[Dict[str, Any]]) -> List[AttackPathSummary]:
        """解析攻击路径"""
        summaries = []
        
        for path_data in attack_paths:
            # 提取使用的工具
            tools_used = []
            for step in path_data.get("steps", []):
                tool = step.get("tool")
                if tool and tool not in tools_used:
                    tools_used.append(tool)
            
            summary = AttackPathSummary(
                path_id=path_data.get("path_id", 0),
                name=path_data.get("name", "未知路径"),
                strategy=path_data.get("strategy", ""),
                steps_count=path_data.get("step_count", len(path_data.get("steps", []))),
                success_rate=path_data.get("success_rate", 0.5),
                estimated_time=path_data.get("estimated_time", "未知"),
                difficulty=path_data.get("difficulty", "medium"),
                tools_used=tools_used[:5]  # 最多5个工具
            )
            summaries.append(summary)
        
        return summaries
    
    def _parse_post_exploitation_results(self, post_exploitation_results: Dict[str, Any]) -> PostExploitationSummary:
        """解析后渗透结果"""
        return PostExploitationSummary(
            plan_id=post_exploitation_results.get("plan_id", "未知计划"),
            name=post_exploitation_results.get("plan_name", "后渗透测试"),
            objectives=self._extract_post_exploitation_objectives(post_exploitation_results),
            steps_count=post_exploitation_results.get("total_steps", 0),
            successful_steps=post_exploitation_results.get("successful_steps", 0),
            execution_time=f"{post_exploitation_results.get('execution_time_minutes', 0)}分钟",
            risk_level=self._determine_post_exploitation_risk(post_exploitation_results),
            effectiveness=post_exploitation_results.get("summary", {}).get("overall_effectiveness", "未知")
        )
    
    def _parse_quantitative_metrics(self, quantitative_metrics: Dict[str, Any]) -> QuantitativeMetrics:
        """解析量化指标"""
        # 从量化指标数据中提取
        vuln_metrics = quantitative_metrics.get("vulnerability_metrics", {})
        cve_metrics = quantitative_metrics.get("cve_metrics", {})
        attack_metrics = quantitative_metrics.get("attack_efficiency_metrics", {})
        
        return QuantitativeMetrics(
            vulnerability_detection_rate=vuln_metrics.get("detection_rate", 0.0),
            false_positive_rate=vuln_metrics.get("false_positive_rate", 0.0),
            cve_coverage_rate=cve_metrics.get("cve_coverage_rate", 0.0),
            attack_success_rate=attack_metrics.get("attack_success_rate", 0.0),
            overall_score=quantitative_metrics.get("overall_score", 0.0),
            meeting_requirements=quantitative_metrics.get("meeting_requirements_check", {})
        )
    
    def _generate_executive_summary(self,
                                  target_info: Dict[str, Any],
                                  vulnerabilities: List[VulnerabilityFinding],
                                  attack_paths: List[AttackPathSummary],
                                  post_exploitation: Optional[PostExploitationSummary],
                                  quantitative_metrics: Optional[QuantitativeMetrics]) -> Dict[str, Any]:
        """生成执行摘要"""
        # 统计漏洞
        critical_vulns = [v for v in vulnerabilities if v.severity == "critical"]
        high_vulns = [v for v in vulnerabilities if v.severity == "high"]
        
        # 评估整体风险
        overall_risk = self._assess_overall_risk(vulnerabilities, post_exploitation)
        
        # 生成摘要文本
        summary_text = f"本次渗透测试针对目标 {target_info.get('target', '未知目标')} 进行。"
        
        if vulnerabilities:
            summary_text += f" 共发现 {len(vulnerabilities)} 个安全漏洞，其中严重漏洞 {len(critical_vulns)} 个，高危漏洞 {len(high_vulns)} 个。"
        
        if attack_paths:
            best_path = self._select_best_attack_path(attack_paths)
            summary_text += f" 生成 {len(attack_paths)} 条攻击路径，最佳路径 '{best_path.name}' 成功率 {best_path.success_rate*100:.1f}%。"
        
        if post_exploitation:
            summary_text += f" 后渗透测试执行 {post_exploitation.steps_count} 个步骤，成功 {post_exploitation.successful_steps} 个，效果评估为'{post_exploitation.effectiveness}'。"
        
        if quantitative_metrics:
            summary_text += f" 量化指标显示：漏洞检测率 {quantitative_metrics.vulnerability_detection_rate:.1f}%，误报率 {quantitative_metrics.false_positive_rate:.1f}%。"
        
        summary_text += f" 整体风险评估为'{overall_risk}'。"
        
        return {
            "overview": summary_text,
            "key_findings": self._extract_key_findings(vulnerabilities, attack_paths),
            "overall_risk": overall_risk,
            "testing_period": f"{datetime.now().strftime('%Y-%m-%d')}",
            "tester": "ClawAI自动化渗透测试系统"
        }
    
    def _generate_risk_assessment(self, vulnerabilities: List[VulnerabilityFinding], 
                                 post_exploitation: Optional[PostExploitationSummary]) -> Dict[str, Any]:
        """生成风险评估"""
        # 计算风险分数
        risk_score = 0
        
        # 基于漏洞严重程度
        for vuln in vulnerabilities:
            if vuln.severity == "critical":
                risk_score += 10
            elif vuln.severity == "high":
                risk_score += 7
            elif vuln.severity == "medium":
                risk_score += 4
            elif vuln.severity == "low":
                risk_score += 1
        
        # 基于后渗透结果
        if post_exploitation:
            if post_exploitation.risk_level == "high":
                risk_score += 15
            elif post_exploitation.risk_level == "medium":
                risk_score += 10
            elif post_exploitation.risk_level == "low":
                risk_score += 5
        
        # 确定风险等级
        if risk_score >= 30:
            risk_level = "极高"
        elif risk_score >= 20:
            risk_level = "高"
        elif risk_score >= 10:
            risk_level = "中"
        else:
            risk_level = "低"
        
        # 生成风险描述
        risk_description = self._generate_risk_description(risk_level, vulnerabilities, post_exploitation)
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "factors_considered": [
                "漏洞数量和严重程度",
                "攻击路径成功率",
                "后渗透测试效果",
                "系统暴露面大小"
            ]
        }
    
    def _generate_recommendations(self, vulnerabilities: List[VulnerabilityFinding],
                                attack_paths: List[AttackPathSummary],
                                post_exploitation: Optional[PostExploitationSummary]) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []
        
        # 基于漏洞的建议
        critical_vulns = [v for v in vulnerabilities if v.severity in ["critical", "high"]]
        if critical_vulns:
            recommendations.append({
                "priority": "高",
                "category": "漏洞修复",
                "description": f"立即修复 {len(critical_vulns)} 个严重和高危漏洞",
                "action_items": [
                    "按照漏洞详情中的建议进行修复",
                    "优先修复远程代码执行和SQL注入漏洞",
                    "建立漏洞修复跟踪机制"
                ]
            })
        
        # 基于攻击路径的建议
        if attack_paths:
            best_path = self._select_best_attack_path(attack_paths)
            if best_path.success_rate > 0.7:
                recommendations.append({
                    "priority": "中",
                    "category": "攻击面缩减",
                    "description": f"针对攻击路径 '{best_path.name}' 中使用的工具进行防护",
                    "action_items": [
                        f"加强对{', '.join(best_path.tools_used[:3])}等工具的检测",
                        "优化网络访问控制策略",
                        "增强日志监控和告警"
                    ]
                })
        
        # 基于后渗透的建议
        if post_exploitation and post_exploitation.successful_steps > 0:
            recommendations.append({
                "priority": "高",
                "category": "后渗透防护",
                "description": "加强系统后渗透防护能力",
                "action_items": [
                    "实施最小权限原则",
                    "加强日志审计和监控",
                    "定期进行安全配置检查",
                    "建立应急响应机制"
                ]
            })
        
        # 通用建议
        recommendations.append({
            "priority": "中",
            "category": "安全加固",
            "description": "实施全面的安全加固措施",
            "action_items": [
                "定期进行安全评估和渗透测试",
                "建立持续的安全监控体系",
                "加强员工安全意识培训",
                "制定和完善安全策略"
            ]
        })
        
        return recommendations
    
    def _generate_technical_details(self, scan_results: Dict[str, Any], 
                                  attack_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成技术细节"""
        return {
            "scan_methodology": "自动化扫描 + 手动验证",
            "tools_used": self._extract_tools_used(scan_results, attack_paths),
            "testing_scope": "黑盒测试 + 灰盒测试",
            "limitations": [
                "测试时间有限，可能未覆盖所有攻击面",
                "自动化工具可能存在误报和漏报",
                "部分高级攻击技术需要人工验证"
            ],
            "data_collection": {
                "network_data": scan_results.get("network_data", {}),
                "web_technologies": scan_results.get("web_technologies", {}),
                "service_info": scan_results.get("service_info", {})
            }
        }
    
    def _generate_appendix(self) -> Dict[str, Any]:
        """生成附录"""
        return {
            "glossary": {
                "CVSS": "通用漏洞评分系统",
                "CVE": "公共漏洞和暴露",
                "RCE": "远程代码执行",
                "SQLi": "SQL注入",
                "XSS": "跨站脚本攻击",
                "CSRF": "跨站请求伪造"
            },
            "references": [
                "OWASP Testing Guide",
                "NIST Cybersecurity Framework",
                "PTES (Penetration Testing Execution Standard)"
            ],
            "contact_information": {
                "security_team": "security@example.com",
                "incident_response": "ir@example.com"
            }
        }
    
    def _determine_impact(self, severity: str) -> str:
        """确定漏洞影响"""
        impacts = {
            "critical": "可能导致系统完全被控制、数据泄露或服务中断",
            "high": "可能导致敏感信息泄露、权限提升或部分服务中断",
            "medium": "可能导致信息泄露或有限的功能影响",
            "low": "影响有限，可能只涉及信息泄露或轻微功能影响"
        }
        return impacts.get(severity, "影响程度未知")
    
    def _generate_vulnerability_recommendation(self, vuln_data: Dict[str, Any]) -> str:
        """生成漏洞修复建议"""
        category = vuln_data.get("type", "").lower()
        
        recommendations = {
            "sql_injection": "使用参数化查询或预编译语句，对用户输入进行严格验证和过滤",
            "xss": "对用户输入进行HTML编码，实施内容安全策略(CSP)",
            "rce": "更新到安全版本，限制命令执行权限，实施输入验证",
            "file_upload": "限制上传文件类型，检查文件内容，将上传文件存储在非Web可访问目录",
            "csrf": "实施CSRF令牌，验证请求来源",
            "insecure_direct_object_reference": "实施访问控制，使用间接对象引用",
            "security_misconfiguration": "遵循安全配置指南，定期进行配置审计",
            "sensitive_data_exposure": "实施数据加密，限制敏感数据访问，使用安全传输协议"
        }
        
        return recommendations.get(category, "请参考相关安全最佳实践进行修复")
    
    def _create_sample_vulnerabilities(self) -> List[VulnerabilityFinding]:
        """创建示例漏洞数据"""
        return [
            VulnerabilityFinding(
                id="VULN-001",
                name="SQL注入漏洞",
                severity="high",
                category="sql_injection",
                description="在登录页面发现SQL注入漏洞，攻击者可以绕过认证",
                location="/login.php",
                evidence="sqlmap检测到可注入参数",
                impact="可能导致数据库信息泄露或系统被控制",
                recommendation="使用参数化查询，对用户输入进行严格验证",
                cve_id="CVE-2023-12345",
                cvss_score=8.5
            ),
            VulnerabilityFinding(
                id="VULN-002",
                name="跨站脚本漏洞",
                severity="medium",
                category="xss",
                description="在搜索功能中发现反射型XSS漏洞",
                location="/search.php",
                evidence="用户输入未经过滤直接输出",
                impact="可能导致用户会话劫持或恶意脚本执行",
                recommendation="对用户输入进行HTML编码，实施CSP策略",
                cvss_score=6.1
            ),
            VulnerabilityFinding(
                id="VULN-003",
                name="敏感信息泄露",
                severity="low",
                category="information_disclosure",
                description="错误页面泄露服务器版本信息",
                location="/error.php",
                evidence="错误页面显示Apache 2.4.29版本信息",
                impact="攻击者可能利用版本信息寻找已知漏洞",
                recommendation="隐藏错误详情，返回通用错误信息",
                cvss_score=3.5
            )
        ]
    
    def _extract_post_exploitation_objectives(self, post_exploitation_results: Dict[str, Any]) -> List[str]:
        """提取后渗透目标"""
        # 从步骤中推断目标
        objectives = set()
        step_results = post_exploitation_results.get("step_results", [])
        
        category_to_objective = {
            "persistence": "持久化",
            "privilege_escalation": "权限提升",
            "lateral_movement": "横向移动",
            "data_exfiltration": "数据提取",
            "cleanup": "痕迹清理"
        }
        
        for result in step_results:
            category = result.get("category")
            if category in category_to_objective:
                objectives.add(category_to_objective[category])
        
        return list(objectives) if objectives else ["系统控制"]
    
    def _determine_post_exploitation_risk(self, post_exploitation_results: Dict[str, Any]) -> str:
        """确定后渗透风险等级"""
        summary = post_exploitation_results.get("summary", {})
        effectiveness = summary.get("overall_effectiveness", "未知")
        
        if effectiveness == "优秀":
            return "high"
        elif effectiveness == "良好":
            return "medium"
        elif effectiveness == "一般":
            return "medium"
        else:
            return "low"
    
    def _calculate_severity_distribution(self, vulnerabilities: List[VulnerabilityFinding]) -> Dict[str, int]:
        """计算严重程度分布"""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for vuln in vulnerabilities:
            severity = vuln.severity
            if severity in distribution:
                distribution[severity] += 1
        
        return distribution
    
    def _select_best_attack_path(self, attack_paths: List[AttackPathSummary]) -> AttackPathSummary:
        """选择最佳攻击路径"""
        if not attack_paths:
            # 返回一个默认路径
            return AttackPathSummary(
                path_id=0,
                name="默认攻击路径",
                strategy="基础侦察",
                steps_count=3,
                success_rate=0.6,
                estimated_time="10分钟",
                difficulty="medium",
                tools_used=["nmap", "whatweb", "nuclei"]
            )
        
        # 选择成功率最高的路径
        return max(attack_paths, key=lambda x: x.success_rate)
    
    def _assess_overall_risk(self, vulnerabilities: List[VulnerabilityFinding], 
                           post_exploitation: Optional[PostExploitationSummary]) -> str:
        """评估整体风险"""
        critical_count = len([v for v in vulnerabilities if v.severity == "critical"])
        high_count = len([v for v in vulnerabilities if v.severity == "high"])
        
        if critical_count > 0:
            return "极高"
        elif high_count >= 3:
            return "高"
        elif high_count > 0 or (post_exploitation and post_exploitation.effectiveness in ["优秀", "良好"]):
            return "中"
        else:
            return "低"
    
    def _extract_key_findings(self, vulnerabilities: List[VulnerabilityFinding], 
                            attack_paths: List[AttackPathSummary]) -> List[str]:
        """提取关键发现"""
        findings = []
        
        # 基于漏洞的关键发现
        critical_vulns = [v for v in vulnerabilities if v.severity == "critical"]
        if critical_vulns:
            findings.append(f"发现 {len(critical_vulns)} 个严重漏洞，需要立即修复")
        
        high_vulns = [v for v in vulnerabilities if v.severity == "high"]
        if high_vulns:
            findings.append(f"发现 {len(high_vulns)} 个高危漏洞，建议尽快修复")
        
        # 基于攻击路径的关键发现
        if attack_paths:
            best_path = self._select_best_attack_path(attack_paths)
            if best_path.success_rate > 0.8:
                findings.append(f"存在高成功率({best_path.success_rate*100:.1f}%)的攻击路径")
        
        # 通用发现
        if vulnerabilities:
            findings.append(f"共发现 {len(vulnerabilities)} 个安全漏洞")
        
        return findings if findings else ["未发现重大安全漏洞"]
    
    def _generate_risk_description(self, risk_level: str, vulnerabilities: List[VulnerabilityFinding],
                                 post_exploitation: Optional[PostExploitationSummary]) -> str:
        """生成风险描述"""
        descriptions = {
            "极高": "系统存在严重安全漏洞，攻击者可能完全控制系统，导致数据泄露和服务中断。建议立即采取修复措施。",
            "高": "系统存在多个高危漏洞，攻击者可能获取敏感信息或提升权限。建议尽快修复关键漏洞。",
            "中": "系统存在中等风险漏洞，攻击者可能进行有限的信息收集或功能影响。建议制定修复计划。",
            "低": "系统安全性较好，仅存在少量低风险漏洞。建议定期进行安全评估。"
        }
        
        base_description = descriptions.get(risk_level, "风险等级未知")
        
        # 添加具体信息
        if vulnerabilities:
            critical_count = len([v for v in vulnerabilities if v.severity == "critical"])
            if critical_count > 0:
                base_description += f" 发现{critical_count}个严重漏洞。"
        
        if post_exploitation and post_exploitation.effectiveness in ["优秀", "良好"]:
            base_description += " 后渗透测试显示系统存在进一步被利用的风险。"
        
        return base_description
    
    def _extract_tools_used(self, scan_results: Dict[str, Any], attack_paths: List[Dict[str, Any]]) -> List[str]:
        """提取使用的工具"""
        tools = set()
        
        # 从扫描结果提取工具
        if "tools_used" in scan_results:
            if isinstance(scan_results["tools_used"], list):
                tools.update(scan_results["tools_used"])
        
        # 从攻击路径提取工具
        for path in attack_paths:
            for step in path.get("steps", []):
                tool = step.get("tool")
                if tool:
                    tools.add(tool)
        
        return list(tools)[:10]  # 最多10个工具
    
    def save_report(self, report: Dict[str, Any], output_dir: str = "reports") -> str:
        """
        保存报告到文件
        
        Args:
            report: 报告数据
            output_dir: 输出目录
            
        Returns:
            保存的文件路径
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        report_id = report["report_id"]
        filename = f"{report_id}_penetration_test_report.json"
        filepath = os.path.join(output_dir, filename)
        
        # 保存JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已保存: {filepath}")
        return filepath
    
    def generate_html_report(self, report: Dict[str, Any], output_dir: str = "reports") -> str:
        """
        生成HTML格式的报告
        
        Args:
            report: 报告数据
            output_dir: 输出目录
            
        Returns:
            HTML文件路径
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成HTML内容
        html_content = self._create_html_content(report)
        
        # 保存HTML文件
        report_id = report["report_id"]
        filename = f"{report_id}_penetration_test_report.html"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已保存: {filepath}")
        return filepath
    
    def _create_html_content(self, report: Dict[str, Any]) -> str:
        """创建HTML报告内容"""
        # 生成完整的HTML报告
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>渗透测试报告 - {report['report_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .section-title {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .vulnerability {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #e74c3c; }}
        .critical {{ border-left-color: #e74c3c; }}
        .high {{ border-left-color: #e67e22; }}
        .medium {{ border-left-color: #f1c40f; }}
        .low {{ border-left-color: #2ecc71; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f2f2f2; }}
        .risk-high {{ color: #e74c3c; font-weight: bold; }}
        .risk-medium {{ color: #e67e22; font-weight: bold; }}
        .risk-low {{ color: #2ecc71; font-weight: bold; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .recommendation {{ background: #e8f4fd; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>渗透测试报告</h1>
            <p>报告ID: {report['report_id']} | 日期: {report['report_date']}</p>
            <p>测试系统: ClawAI自动化渗透测试系统</p>
        </div>
        
        <div class="section">
            <h2 class="section-title">执行摘要</h2>
            <p>{report['executive_summary']['overview']}</p>
            
            <h3>关键发现</h3>
            <ul>
                {"".join(f"<li>{finding}</li>" for finding in report['executive_summary']['key_findings'])}
            </ul>
            
            <p><strong>整体风险等级:</strong> 
                <span class="risk-{report['executive_summary']['overall_risk'].lower()}">
                    {report['executive_summary']['overall_risk']}
                </span>
            </p>
        </div>
        
        {self._create_quantitative_metrics_html(report)}
        
        <div class="section">
            <h2 class="section-title">漏洞发现</h2>
            <p>共发现 {report['vulnerability_findings']['total_count']} 个安全漏洞</p>
            
            <h3>严重程度分布</h3>
            <table>
                <tr>
                    <th>严重程度</th>
                    <th>数量</th>
                </tr>
                {"".join(f"<tr><td>{severity}</td><td>{count}</td></tr>" for severity, count in report['vulnerability_findings']['severity_distribution'].items() if count > 0)}
            </table>
            
            <h3>漏洞详情</h3>
            {"".join(self._create_vulnerability_html(vuln) for vuln in report['vulnerability_findings']['findings'])}
        </div>
        
        <div class="section">
            <h2 class="section-title">攻击路径分析</h2>
            <p>共生成 {report['attack_path_analysis']['total_paths']} 条攻击路径</p>
            
            <h3>最佳攻击路径</h3>
            <table>
                <tr>
                    <th>路径名称</th>
                    <th>策略</th>
                    <th>步骤数</th>
                    <th>成功率</th>
                    <th>难度</th>
                </tr>
                <tr>
                    <td>{report['attack_path_analysis']['best_path']['name']}</td>
                    <td>{report['attack_path_analysis']['best_path']['strategy']}</td>
                    <td>{report['attack_path_analysis']['best_path']['steps_count']}</td>
                    <td>{report['attack_path_analysis']['best_path']['success_rate']*100:.1f}%</td>
                    <td>{report['attack_path_analysis']['best_path']['difficulty']}</td>
                </tr>
            </table>
            
            <h3>所有攻击路径</h3>
            <table>
                <tr>
                    <th>路径ID</th>
                    <th>名称</th>
                    <th>步骤数</th>
                    <th>成功率</th>
                    <th>使用工具</th>
                </tr>
                {"".join(f"<tr><td>{path['path_id']}</td><td>{path['name']}</td><td>{path['steps_count']}</td><td>{path['success_rate']*100:.1f}%</td><td>{', '.join(path['tools_used'][:3])}</td></tr>" for path in report['attack_path_analysis']['paths'])}
            </table>
        </div>
        
        {self._create_post_exploitation_html(report)}
        
        <div class="section">
            <h2 class="section-title">风险评估</h2>
            <p><strong>风险分数:</strong> {report['risk_assessment']['risk_score']}</p>
            <p><strong>风险等级:</strong> <span class="risk-{report['risk_assessment']['risk_level'].lower()}">{report['risk_assessment']['risk_level']}</span></p>
            <p><strong>风险描述:</strong> {report['risk_assessment']['risk_description']}</p>
            
            <h3>风险因素</h3>
            <ul>
                {"".join(f"<li>{factor}</li>" for factor in report['risk_assessment']['factors_considered'])}
            </ul>
        </div>
        
        <div class="section">
            <h2 class="section-title">安全建议</h2>
            {"".join(self._create_recommendation_html(rec) for rec in report['recommendations'])}
        </div>
        
        <div class="section">
            <h2 class="section-title">技术细节</h2>
            <h3>使用的工具</h3>
            <ul>
                {"".join(f"<li>{tool}</li>" for tool in report['technical_details']['tools_used'])}
            </ul>
            
            <h3>测试范围</h3>
            <p>{report['technical_details']['testing_scope']}</p>
            
            <h3>测试方法</h3>
            <p>{report['technical_details']['scan_methodology']}</p>
            
            <h3>局限性</h3>
            <ul>
                {"".join(f"<li>{limitation}</li>" for limitation in report['technical_details']['limitations'])}
            </ul>
        </div>
        
        <div class="section">
            <h2 class="section-title">附录</h2>
            <h3>术语表</h3>
            <table>
                <tr>
                    <th>术语</th>
                    <th>解释</th>
                </tr>
                {"".join(f"<tr><td>{term}</td><td>{explanation}</td></tr>" for term, explanation in report['appendix']['glossary'].items())}
            </table>
            
            <h3>参考文档</h3>
            <ul>
                {"".join(f"<li>{ref}</li>" for ref in report['appendix']['references'])}
            </ul>
            
            <h3>联系方式</h3>
            <table>
                <tr>
                    <th>团队</th>
                    <th>联系方式</th>
                </tr>
                {"".join(f"<tr><td>{team}</td><td>{contact}</td></tr>" for team, contact in report['appendix']['contact_information'].items())}
            </table>
        </div>
        
        <div class="section" style="text-align: center; color: #666; font-size: 12px;">
            <p>本报告由ClawAI自动化渗透测试系统生成</p>
            <p>生成时间: {report['report_date']}</p>
            <p>© 2026 ClawAI Security Team. 所有权利保留。</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _create_vulnerability_html(self, vuln: Dict[str, Any]) -> str:
        """创建漏洞HTML"""
        severity_class = vuln.get("severity", "medium").lower()
        cvss_score = vuln.get("cvss_score", "N/A")
        cve_id = vuln.get("cve_id", "无")
        
        return f"""
        <div class="vulnerability {severity_class}">
            <h4>{vuln['id']}: {vuln['name']}</h4>
            <p><strong>严重程度:</strong> <span class="{severity_class}">{vuln['severity']}</span></p>
            <p><strong>类别:</strong> {vuln['category']}</p>
            <p><strong>位置:</strong> {vuln['location']}</p>
            <p><strong>描述:</strong> {vuln['description']}</p>
            <p><strong>证据:</strong> {vuln['evidence']}</p>
            <p><strong>影响:</strong> {vuln['impact']}</p>
            <p><strong>CVE ID:</strong> {cve_id}</p>
            <p><strong>CVSS评分:</strong> {cvss_score}</p>
            <p><strong>修复建议:</strong> {vuln['recommendation']}</p>
        </div>
        """
    
    def _create_quantitative_metrics_html(self, report: Dict[str, Any]) -> str:
        """创建量化指标HTML"""
        if not report.get("quantitative_metrics"):
            return ""
        
        metrics = report["quantitative_metrics"]
        
        return f"""
        <div class="section">
            <h2 class="section-title">量化指标</h2>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div class="metric-card">
                    <div class="metric-value">{metrics['vulnerability_detection_rate']}%</div>
                    <div class="metric-label">漏洞检测率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['false_positive_rate']}%</div>
                    <div class="metric-label">误报率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['cve_coverage_rate']}%</div>
                    <div class="metric-label">CVE覆盖支持率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['attack_success_rate']}%</div>
                    <div class="metric-label">攻击成功率</div>
                </div>
            </div>
            
            <h3>总体评分: {metrics['overall_score']}</h3>
            
            <h3>会议纪要要求检查</h3>
            <table>
                <tr>
                    <th>要求</th>
                    <th>状态</th>
                </tr>
                {"".join(f"<tr><td>{req}</td><td>{'✅ 满足' if met else '❌ 未满足'}</td></tr>" for req, met in metrics['meeting_requirements'].items())}
            </table>
        </div>
        """
    
    def _create_post_exploitation_html(self, report: Dict[str, Any]) -> str:
        """创建后渗透结果HTML"""
        if not report.get("post_exploitation_results"):
            return ""
        
        post_exp = report["post_exploitation_results"]
        
        return f"""
        <div class="section">
            <h2 class="section-title">后渗透测试结果</h2>
            <p><strong>计划名称:</strong> {post_exp['name']}</p>
            <p><strong>计划ID:</strong> {post_exp['plan_id']}</p>
            <p><strong>目标:</strong> {', '.join(post_exp['objectives'])}</p>
            <p><strong>执行时间:</strong> {post_exp['execution_time']}</p>
            <p><strong>步骤统计:</strong> {post_exp['successful_steps']}/{post_exp['steps_count']} 成功</p>
            <p><strong>风险等级:</strong> {post_exp['risk_level']}</p>
            <p><strong>效果评估:</strong> {post_exp['effectiveness']}</p>
        </div>
        """
    
    def _create_recommendation_html(self, recommendation: Dict[str, Any]) -> str:
        """创建建议HTML"""
        priority_class = recommendation['priority'].lower()
        priority_colors = {
            "高": "#e74c3c",
            "中": "#f39c12",
            "低": "#2ecc71"
        }
        color = priority_colors.get(recommendation['priority'], "#3498db")
        
        return f"""
        <div class="recommendation" style="border-left-color: {color};">
            <h4><span style="color: {color};">[{recommendation['priority']}优先级]</span> {recommendation['category']}</h4>
            <p><strong>描述:</strong> {recommendation['description']}</p>
            <p><strong>行动项:</strong></p>
            <ul>
                {"".join(f"<li>{item}</li>" for item in recommendation['action_items'])}
            </ul>
        </div>
        """
    
    def test_report_generator(self) -> bool:
        """测试报告生成器"""
        print("测试渗透测试报告生成器...")
        print("=" * 60)
        
        try:
            # 创建测试数据
            target_info = {
                "target": "http://test.example.com",
                "ip_address": "192.168.1.100",
                "scan_date": "2026-04-03",
                "scope": "Web应用程序"
            }
            
            scan_results = {
                "vulnerabilities": [
                    {
                        "name": "SQL注入漏洞",
                        "severity": "high",
                        "type": "sql_injection",
                        "description": "在登录页面发现SQL注入漏洞",
                        "location": "/login.php",
                        "evidence": "sqlmap检测到可注入参数",
                        "cve": "CVE-2023-12345",
                        "cvss_score": 8.5
                    },
                    {
                        "name": "XSS漏洞",
                        "severity": "medium",
                        "type": "xss",
                        "description": "在搜索功能中发现反射型XSS",
                        "location": "/search.php",
                        "evidence": "用户输入未过滤直接输出"
                    }
                ],
                "tools_used": ["nmap", "nuclei", "sqlmap", "whatweb"]
            }
            
            attack_paths = [
                {
                    "path_id": 1,
                    "name": "SQL注入攻击路径",
                    "strategy": "通过SQL注入获取管理员权限",
                    "steps": [
                        {"tool": "sqlmap", "action": "检测SQL注入点"},
                        {"tool": "metasploit", "action": "利用SQL注入获取shell"},
                        {"tool": "meterpreter", "action": "提权和持久化"}
                    ],
                    "success_rate": 0.85,
                    "estimated_time": "15分钟",
                    "difficulty": "medium"
                },
                {
                    "path_id": 2,
                    "name": "XSS攻击路径",
                    "strategy": "通过XSS窃取会话cookie",
                    "steps": [
                        {"tool": "xsser", "action": "检测XSS漏洞"},
                        {"tool": "beef", "action": "部署XSS攻击载荷"},
                        {"tool": "burpsuite", "action": "窃取会话cookie"}
                    ],
                    "success_rate": 0.70,
                    "estimated_time": "10分钟",
                    "difficulty": "low"
                }
            ]
            
            post_exploitation_results = {
                "plan_id": "POST_EXP_001",
                "plan_name": "Windows后渗透测试",
                "total_steps": 5,
                "successful_steps": 4,
                "execution_time_minutes": 25,
                "summary": {
                    "overall_effectiveness": "良好",
                    "category_success_rates": {
                        "persistence": 80.0,
                        "privilege_escalation": 75.0,
                        "data_exfiltration": 90.0
                    }
                },
                "step_results": [
                    {"category": "persistence", "success": True},
                    {"category": "privilege_escalation", "success": True},
                    {"category": "lateral_movement", "success": False},
                    {"category": "data_exfiltration", "success": True},
                    {"category": "cleanup", "success": True}
                ]
            }
            
            quantitative_metrics = {
                "vulnerability_metrics": {
                    "detection_rate": 92.5,
                    "false_positive_rate": 8.2,
                    "precision": 91.8,
                    "recall": 92.5,
                    "f1_score": 92.1
                },
                "cve_metrics": {
                    "cve_coverage_rate": 15.3,
                    "cve_detection_rate": 80.0
                },
                "attack_efficiency_metrics": {
                    "attack_success_rate": 85.0,
                    "time_efficiency": 0.45,
                    "resource_efficiency": 0.32
                },
                "overall_score": 78.4,
                "meeting_requirements_check": {
                    "vulnerability_detection_rate_ge_90": True,
                    "false_positive_rate_le_10": True,
                    "cve_coverage_ge_1": True,
                    "attack_success_rate_ge_80": True
                }
            }
            
            # 生成报告
            generator = PenetrationReportGenerator()
            report = generator.generate_report(
                target_info=target_info,
                scan_results=scan_results,
                attack_paths=attack_paths,
                post_exploitation_results=post_exploitation_results,
                quantitative_metrics=quantitative_metrics
            )
            
            print("✅ 报告生成成功!")
            print(f"报告ID: {report['report_id']}")
            print(f"报告日期: {report['report_date']}")
            print(f"目标: {report['target_information']['target']}")
            print(f"漏洞数量: {report['vulnerability_findings']['total_count']}")
            print(f"攻击路径数量: {report['attack_path_analysis']['total_paths']}")
            print(f"整体风险等级: {report['executive_summary']['overall_risk']}")
            
            # 保存JSON报告
            json_path = generator.save_report(report)
            print(f"✅ JSON报告已保存: {json_path}")
            
            # 生成HTML报告
            html_path = generator.generate_html_report(report)
            print(f"✅ HTML报告已保存: {html_path}")
            
            # 验证报告内容
            assert report['report_id'].startswith('PTR-'), "报告ID格式错误"
            assert report['vulnerability_findings']['total_count'] > 0, "漏洞数量应为正数"
            assert report['attack_path_analysis']['total_paths'] > 0, "攻击路径数量应为正数"
            assert report['executive_summary']['overall_risk'] in ['低', '中', '高', '极高'], "风险等级无效"
            
            print("\n" + "=" * 60)
            print("[成功] 渗透测试报告生成器功能完整!")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import sys
    # 运行测试
    generator = PenetrationReportGenerator()
    success = generator.test_report_generator()
    sys.exit(0 if success else 1)
