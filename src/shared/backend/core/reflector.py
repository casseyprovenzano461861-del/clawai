# -*- coding: utf-8 -*-
"""
Reflector模块 - 审计分析器
负责审计分析执行结果，从失败中学习
"""

import json
from typing import Dict, Any, List


class Reflector:
    """反射器类"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def analyze_execution(self, node: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析执行结果"""
        analysis = {
            "node_id": node["id"],
            "node_type": node["type"],
            "status": "success" if "error" not in execution_result else "failed",
            "analysis": {},
            "recommendations": []
        }
        
        if "error" in execution_result:
            # 分析失败原因
            failure_analysis = self._analyze_failure(execution_result["error"])
            analysis["analysis"] = failure_analysis
            analysis["recommendations"] = self._generate_failure_recommendations(failure_analysis)
        else:
            # 分析成功结果
            success_analysis = self._analyze_success(execution_result, node["type"])
            analysis["analysis"] = success_analysis
            analysis["recommendations"] = self._generate_success_recommendations(success_analysis)
        
        return analysis
    
    def _analyze_failure(self, error_message: str) -> Dict[str, Any]:
        """分析失败原因"""
        # 失败模式分析
        failure_pattern = "unknown"
        severity = "low"
        
        # 基于错误信息识别失败模式
        if "nmap" in error_message and "not found" in error_message:
            failure_pattern = "tool_not_found"
            severity = "medium"
        elif "timeout" in error_message:
            failure_pattern = "timeout"
            severity = "medium"
        elif "permission" in error_message:
            failure_pattern = "permission_denied"
            severity = "high"
        elif "connection" in error_message:
            failure_pattern = "connection_error"
            severity = "medium"
        
        return {
            "error_message": error_message,
            "failure_pattern": failure_pattern,
            "severity": severity,
            "level": self._determine_failure_level(failure_pattern, severity)
        }
    
    def _analyze_success(self, result: Dict[str, Any], node_type: str) -> Dict[str, Any]:
        """分析成功结果"""
        analysis = {
            "result_summary": self._summarize_result(result, node_type),
            "key_findings": self._extract_key_findings(result, node_type),
            "confidence": self._calculate_confidence(result, node_type)
        }
        
        return analysis
    
    def _determine_failure_level(self, failure_pattern: str, severity: str) -> int:
        """确定失败级别（L1-L4）"""
        if severity == "high":
            return 4
        elif severity == "medium" and failure_pattern in ["tool_not_found", "permission_denied"]:
            return 3
        elif severity == "medium":
            return 2
        else:
            return 1
    
    def _summarize_result(self, result: Dict[str, Any], node_type: str) -> str:
        """总结执行结果"""
        if node_type == "reconnaissance":
            ports = result.get("ports", [])
            return f"发现 {len(ports)} 个开放端口"
        elif node_type == "vulnerability_scan":
            vulnerabilities = result.get("vulnerabilities", [])
            return f"发现 {len(vulnerabilities)} 个漏洞"
        elif node_type == "exploit":
            return result.get("access", "漏洞利用成功")
        elif node_type == "report":
            findings = result.get("findings", [])
            return f"生成安全报告，包含 {len(findings)} 个发现"
        else:
            return "任务执行成功"
    
    def _extract_key_findings(self, result: Dict[str, Any], node_type: str) -> List[str]:
        """提取关键发现"""
        findings = []
        
        if node_type == "reconnaissance":
            ports = result.get("ports", [])
            for port in ports[:3]:  # 只取前3个端口
                findings.append(f"端口 {port['port']}/{port['protocol']} 运行 {port['service']} 服务")
        elif node_type == "vulnerability_scan":
            vulnerabilities = result.get("vulnerabilities", [])
            high_severity = [v for v in vulnerabilities if v.get("severity") in ["high", "critical"]]
            for vuln in high_severity[:3]:  # 只取前3个高危漏洞
                findings.append(f"{vuln['severity']} 级别漏洞: {vuln['name']}")
        elif node_type == "exploit":
            findings.append(result.get("access", "获得访问权限"))
            if "data" in result:
                findings.append(result.get("data", ""))
        
        return findings
    
    def _calculate_confidence(self, result: Dict[str, Any], node_type: str) -> float:
        """计算结果置信度"""
        confidence = 0.8  # 默认置信度
        
        if node_type == "reconnaissance":
            ports = result.get("ports", [])
            if len(ports) > 0:
                confidence = 0.9
        elif node_type == "vulnerability_scan":
            vulnerabilities = result.get("vulnerabilities", [])
            if len(vulnerabilities) > 0:
                confidence = 0.85
        elif node_type == "exploit":
            if "exploit" in result and result["exploit"] == "成功":
                confidence = 0.95
        
        return confidence
    
    def _generate_failure_recommendations(self, failure_analysis: Dict[str, Any]) -> List[str]:
        """生成失败建议"""
        recommendations = []
        
        failure_pattern = failure_analysis["failure_pattern"]
        
        if failure_pattern == "tool_not_found":
            recommendations.append("安装缺失的工具")
            recommendations.append("检查工具路径配置")
        elif failure_pattern == "timeout":
            recommendations.append("增加工具执行超时时间")
            recommendations.append("检查网络连接")
        elif failure_pattern == "permission_denied":
            recommendations.append("以管理员权限运行工具")
            recommendations.append("检查目标系统权限设置")
        elif failure_pattern == "connection_error":
            recommendations.append("检查目标系统是否可达")
            recommendations.append("验证网络连接")
        else:
            recommendations.append("检查错误日志获取更多信息")
            recommendations.append("尝试使用替代工具")
        
        return recommendations
    
    def _generate_success_recommendations(self, success_analysis: Dict[str, Any]) -> List[str]:
        """生成成功建议"""
        recommendations = []
        
        key_findings = success_analysis.get("key_findings", [])
        if key_findings:
            recommendations.append("基于发现的结果调整后续测试策略")
            recommendations.append("详细记录发现的安全问题")
        
        return recommendations
    
    def generate_intelligence(self, task_graph: Dict[str, Any]) -> Dict[str, Any]:
        """生成攻击情报"""
        intelligence = {
            "attack_paths": [],
            "vulnerability_patterns": [],
            "recommended_tools": [],
            "lessons_learned": []
        }
        
        # 分析任务图，提取攻击路径
        completed_nodes = [node for node in task_graph["nodes"] if node["status"] == "completed"]
        
        # 提取漏洞模式
        vulnerabilities = []
        for node in completed_nodes:
            output = node.get("output", {})
            if "vulnerabilities" in output:
                vulnerabilities.extend(output["vulnerabilities"])
        
        # 统计漏洞类型
        vuln_types = {}
        for vuln in vulnerabilities:
            name = vuln.get("name", "unknown")
            vuln_types[name] = vuln_types.get(name, 0) + 1
        
        # 生成漏洞模式
        for vuln_name, count in vuln_types.items():
            intelligence["vulnerability_patterns"].append({
                "vulnerability": vuln_name,
                "count": count,
                "severity": self._get_vulnerability_severity(vuln_name)
            })
        
        # 生成攻击路径
        if len(completed_nodes) > 1:
            path = [node["label"] for node in completed_nodes]
            intelligence["attack_paths"].append({"path": path, "length": len(path)})
        
        # 生成推荐工具
        if vulnerabilities:
            intelligence["recommended_tools"].extend(["sqlmap", "nuclei", "metasploit"])
        
        # 生成经验教训
        intelligence["lessons_learned"].append("定期更新安全工具版本")
        intelligence["lessons_learned"].append("关注最新漏洞公告")
        intelligence["lessons_learned"].append("建立完整的安全测试流程")
        
        return intelligence
    
    def _get_vulnerability_severity(self, vuln_name: str) -> str:
        """获取漏洞严重程度"""
        high_severity_vulns = ["SQL Injection", "RCE", "Remote Code Execution", "Privilege Escalation"]
        medium_severity_vulns = ["XSS", "CSRF", "File Upload"]
        
        for vuln in high_severity_vulns:
            if vuln.lower() in vuln_name.lower():
                return "high"
        
        for vuln in medium_severity_vulns:
            if vuln.lower() in vuln_name.lower():
                return "medium"
        
        return "low"
