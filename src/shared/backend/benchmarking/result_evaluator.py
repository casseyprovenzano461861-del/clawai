# -*- coding: utf-8 -*-
"""
结果评估器模块
用于评估测试结果和检测标志
"""

import re
from typing import List, Dict, Any


class ResultEvaluator:
    """结果评估器类"""
    
    def __init__(self):
        self.flag_patterns = [
            r'flag\{[^}]+\}',
            r'HTB\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[a-f0-9]{32}',  # MD5 hash
            r'[a-f0-9]{40}',  # SHA1 hash
            r'[a-f0-9]{64}'   # SHA256 hash
        ]
    
    def extract_flags(self, output: str) -> List[str]:
        """从输出中提取标志"""
        flags = []
        for pattern in self.flag_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            flags.extend(matches)
        return list(set(flags))  # 去重
    
    def evaluate_result(self, challenge: Dict[str, Any], output: str) -> Dict[str, Any]:
        """评估测试结果"""
        expected_flags = challenge.get("expected_flags", [])
        extracted_flags = self.extract_flags(output)
        
        # 计算成功率
        found_flags = [flag for flag in expected_flags if flag in extracted_flags]
        success_rate = len(found_flags) / len(expected_flags) if expected_flags else 0
        
        # 分析漏洞发现
        vulnerabilities = self._analyze_vulnerabilities(output)
        
        # 评估结果
        result = {
            "challenge": challenge.get("name"),
            "success_rate": success_rate,
            "found_flags": found_flags,
            "total_flags": len(expected_flags),
            "extracted_flags": extracted_flags,
            "vulnerabilities": vulnerabilities,
            "status": "success" if success_rate == 1.0 else "partial" if success_rate > 0 else "failed"
        }
        
        return result
    
    def _analyze_vulnerabilities(self, output: str) -> List[Dict[str, Any]]:
        """分析漏洞发现"""
        vulnerabilities = []
        
        # 常见漏洞模式
        vuln_patterns = {
            "SQL Injection": r'sql.*injection|sql.*vulnerability',
            "XSS": r'xss|cross.*site.*scripting',
            "Command Injection": r'command.*injection|os.*command',
            "Authentication Bypass": r'authentication.*bypass|auth.*bypass',
            "Directory Traversal": r'directory.*traversal|path.*traversal',
            "File Upload": r'file.*upload|unrestricted.*upload',
            "CSRF": r'csrf|cross.*site.*request.*forgery',
            "SSRF": r'ssrf|server.*side.*request.*forgery',
            "Insecure Direct Object Reference": r'insecure.*direct.*object|idor',
            "Missing Access Control": r'missing.*access.*control|broken.*access.*control'
        }
        
        for vuln_name, pattern in vuln_patterns.items():
            if re.search(pattern, output, re.IGNORECASE):
                vulnerabilities.append({
                    "name": vuln_name,
                    "confidence": "high"
                })
        
        return vulnerabilities
    
    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成评估报告"""
        total_challenges = len(results)
        successful_challenges = sum(1 for result in results if result["status"] == "success")
        partial_challenges = sum(1 for result in results if result["status"] == "partial")
        failed_challenges = sum(1 for result in results if result["status"] == "failed")
        
        total_flags = sum(result["total_flags"] for result in results)
        found_flags = sum(len(result["found_flags"]) for result in results)
        
        overall_success_rate = found_flags / total_flags if total_flags > 0 else 0
        
        # 分析漏洞发现
        all_vulnerabilities = []
        for result in results:
            all_vulnerabilities.extend(result["vulnerabilities"])
        
        # 统计漏洞类型
        vuln_counts = {}
        for vuln in all_vulnerabilities:
            vuln_name = vuln["name"]
            vuln_counts[vuln_name] = vuln_counts.get(vuln_name, 0) + 1
        
        report = {
            "summary": {
                "total_challenges": total_challenges,
                "successful_challenges": successful_challenges,
                "partial_challenges": partial_challenges,
                "failed_challenges": failed_challenges,
                "total_flags": total_flags,
                "found_flags": found_flags,
                "overall_success_rate": overall_success_rate
            },
            "detailed_results": results,
            "vulnerability_summary": vuln_counts,
            "recommendations": self._generate_recommendations(results)
        }
        
        return report
    
    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 分析失败的挑战
        failed_challenges = [result for result in results if result["status"] == "failed"]
        if failed_challenges:
            recommendations.append(f"需要改进对 {len(failed_challenges)} 个挑战的处理能力")
        
        # 分析部分成功的挑战
        partial_challenges = [result for result in results if result["status"] == "partial"]
        if partial_challenges:
            recommendations.append(f"需要提高对 {len(partial_challenges)} 个挑战的成功率")
        
        # 分析漏洞发现
        all_vulnerabilities = []
        for result in results:
            all_vulnerabilities.extend(result["vulnerabilities"])
        
        if len(all_vulnerabilities) < len(results) * 2:  # 每个挑战至少发现2个漏洞
            recommendations.append("需要提高漏洞发现能力")
        
        return recommendations
