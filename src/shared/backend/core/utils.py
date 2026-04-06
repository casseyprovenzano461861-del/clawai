# -*- coding: utf-8 -*-
"""
工具类定义
用于解决代码重复问题，提供公共的工具函数
"""

import logging
from typing import List, Dict, Any, Optional
from .models import AttackStep, ToolConfig, ScanAnalysis

logger = logging.getLogger(__name__)


class AnalysisUtils:
    """分析工具类"""
    
    @staticmethod
    def create_default_analysis() -> ScanAnalysis:
        """创建默认分析对象"""
        return ScanAnalysis()
    
    @staticmethod
    def process_vulnerabilities(vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理漏洞列表"""
        result = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "total": 0
        }
        
        result["total"] = len(vulnerabilities)
        
        for vuln in vulnerabilities:
            if isinstance(vuln, dict):
                severity = vuln.get("severity", "").lower()
                name = vuln.get("name", "未知漏洞")
                
                if severity == "critical":
                    result["critical"].append(name)
                elif severity == "high":
                    result["high"].append(name)
                elif severity == "medium":
                    result["medium"].append(name)
                elif severity == "low":
                    result["low"].append(name)
        
        return result
    
    @staticmethod
    def create_attack_step(step_number: int, tool_name: str, tool_config: ToolConfig) -> AttackStep:
        """创建攻击步骤"""
        return {
            "step": step_number,
            "tool": tool_name,
            "phase": tool_config["phase"],
            "duration": tool_config["duration"],
            "description": tool_config["description_template"].format(detail="执行中..."),
            "success": True
        }
    
    @staticmethod
    def calculate_attack_surface(analysis: ScanAnalysis) -> float:
        """计算攻击面评分"""
        score = 5.0  # 基础分
        
        # 基于开放端口
        open_ports = len(analysis.open_ports)
        if open_ports > 0:
            score += min(open_ports * 0.5, 3.0)
        
        # 基于漏洞
        vulnerabilities = analysis.vulnerabilities
        
        if vulnerabilities.critical:
            score += len(vulnerabilities.critical) * 2.5
        
        if vulnerabilities.high:
            score += len(vulnerabilities.high) * 1.5
        
        if vulnerabilities.medium:
            score += len(vulnerabilities.medium) * 0.8
        
        if vulnerabilities.low:
            score += len(vulnerabilities.low) * 0.3
        
        # 基于技术栈
        if analysis.has_cms:
            score += 0.8
        
        if analysis.has_database:
            score += 1.2
        
        # WAF提供保护
        if analysis.waf_detected:
            score -= 1.0
        
        # 限制在0-10分之间
        return round(min(max(score, 0.0), 10.0), 1)
    
    @staticmethod
    def identify_path_type(path: List[AttackStep]) -> str:
        """识别路径类型"""
        tools = [step["tool"] for step in path]
        
        if "exploit" in tools:
            return "exploit_attack"
        elif "sqlmap" in tools:
            return "sql_injection"
        elif "nuclei" in tools and "exploit" not in tools:
            return "vulnerability_scan"
        elif "whatweb" in tools and "nuclei" not in tools:
            return "reconnaissance"
        else:
            return "general_attack"
    
    @staticmethod
    def estimate_total_duration(path: List[AttackStep]) -> str:
        """估计总执行时间"""
        total_seconds = 0.0
        
        for step in path:
            duration_str = step.get("duration", "0s")
            if duration_str.endswith("s"):
                try:
                    seconds = float(duration_str[:-1])
                    total_seconds += seconds
                except ValueError:
                    pass
        
        if total_seconds < 60:
            return f"{total_seconds:.1f}秒"
        else:
            minutes = total_seconds / 60
            return f"{minutes:.1f}分钟"
    
    @staticmethod
    def customize_nmap_description(step: AttackStep, analysis: ScanAnalysis) -> None:
        """定制nmap步骤描述"""
        open_ports = analysis.open_ports
        if open_ports:
            port_count = len(open_ports)
            port_desc = f"发现{port_count}个开放端口"
            if port_count <= 5:
                port_details = []
                for port_info in open_ports[:5]:
                    if isinstance(port_info, dict):
                        port = port_info.get("port", "")
                        service = port_info.get("service", "")
                        if port and service:
                            port_details.append(f"{port}({service})")
                if port_details:
                    port_desc += f": {', '.join(port_details)}"
            step["description"] = f"端口扫描，{port_desc}"
    
    @staticmethod
    def customize_whatweb_description(step: AttackStep, analysis: ScanAnalysis) -> None:
        """定制whatweb步骤描述"""
        web_tech = analysis.web_technologies
        if web_tech:
            tech_desc = "，".join(web_tech[:3])
            step["description"] = f"技术栈识别，{tech_desc}"
        else:
            step["description"] = "技术栈识别，未识别到具体技术"
    
    @staticmethod
    def customize_nuclei_description(step: AttackStep, analysis: ScanAnalysis) -> None:
        """定制nuclei步骤描述"""
        vulnerabilities = analysis.vulnerabilities
        total = vulnerabilities.total
        if total > 0:
            critical = len(vulnerabilities.critical)
            high = len(vulnerabilities.high)
            
            vuln_desc = f"发现{total}个漏洞"
            if critical > 0:
                vuln_desc += f"（{critical}个严重）"
            elif high > 0:
                vuln_desc += f"（{high}个高危）"
            
            step["description"] = f"漏洞扫描，{vuln_desc}"
        else:
            step["description"] = "漏洞扫描，未发现漏洞"
    
    @staticmethod
    def customize_sqlmap_description(step: AttackStep, analysis: ScanAnalysis) -> None:
        """定制sqlmap步骤描述"""
        sql_injections = analysis.vulnerabilities.high
        if any("SQL" in vuln for vuln in sql_injections):
            step["description"] = "SQL注入检测，发现SQL注入漏洞"
        else:
            step["description"] = "SQL注入检测，未发现SQL注入点"
    
    @staticmethod
    def customize_wafw00f_description(step: AttackStep, analysis: ScanAnalysis) -> None:
        """定制wafw00f步骤描述"""
        if analysis.waf_detected:
            waf_type = analysis.waf_type or "未知类型"
            step["description"] = f"WAF检测，检测到{waf_type}防护"
        else:
            step["description"] = "WAF检测，未检测到WAF防护"
    
    @staticmethod
    def customize_exploit_description(step: AttackStep, analysis: ScanAnalysis) -> None:
        """定制exploit步骤描述"""
        critical_vulns = analysis.vulnerabilities.critical
        if critical_vulns:
            vuln_name = critical_vulns[0] if critical_vulns else "严重漏洞"
            step["description"] = f"漏洞利用，尝试利用{vuln_name}"
        else:
            step["description"] = "漏洞利用，尝试利用发现的漏洞"


class PathBuilder:
    """路径构建工具类"""
    
    @staticmethod
    def build_default_path() -> List[AttackStep]:
        """构建默认侦察路径"""
        return [
            {
                "step": 1,
                "tool": "nmap",
                "phase": "reconnaissance",
                "duration": "2.3s",
                "description": "端口扫描，基础网络侦察",
                "success": True
            },
            {
                "step": 2,
                "tool": "whatweb",
                "phase": "fingerprinting",
                "duration": "1.8s",
                "description": "技术栈识别，分析目标技术架构",
                "success": True
            },
            {
                "step": 3,
                "tool": "nuclei",
                "phase": "vulnerability_scanning",
                "duration": "4.2s",
                "description": "漏洞扫描，检测已知安全漏洞",
                "success": True
            },
            {
                "step": 4,
                "tool": "post",
                "phase": "post_exploitation",
                "duration": "6.1s",
                "description": "后渗透，信息整理和报告生成",
                "success": True
            }
        ]
    
    @staticmethod
    def build_path_from_strategy(strategy: Dict[str, Any], tool_config: Dict[str, ToolConfig]) -> List[AttackStep]:
        """根据策略构建攻击路径"""
        path = []
        step_number = 1
        
        for tool_name in strategy.get("tools", []):
            if tool_name in tool_config:
                tool_config_item = tool_config[tool_name]
                
                # 创建步骤
                step = AnalysisUtils.create_attack_step(step_number, tool_name, tool_config_item)
                path.append(step)
                step_number += 1
        
        return path


class EvolutionUtils:
    """进化工具类"""
    
    @staticmethod
    def apply_evolution_rules(path: List[AttackStep], analysis: ScanAnalysis) -> None:
        """应用进化规则"""
        # 规则1: 如果检测到WAF，调整SQL注入攻击
        if analysis.waf_detected:
            for step in path:
                if step["tool"] == "sqlmap":
                    step["tool"] = "xsstrike"
                    step["description"] = "XSS攻击（绕过WAF检测）"
                    break
        
        # 规则2: 如果有严重漏洞，优化利用步骤
        critical_vulns = analysis.vulnerabilities.critical
        if critical_vulns:
            for step in path:
                if step["tool"] == "exploit":
                    vuln_name = critical_vulns[0] if critical_vulns else "严重漏洞"
                    step["description"] = f"优先利用{vuln_name}（严重漏洞）"
                    break
        
        # 规则3: 如果有数据库服务，确保有数据库攻击步骤
        if analysis.has_database:
            has_db_attack = any(step["tool"] in ["sqlmap", "exploit"] for step in path)
            if not has_db_attack:
                # 在合适位置插入数据库攻击
                for i, step in enumerate(path):
                    if step["tool"] == "nuclei":
                        path.insert(i + 1, {
                            "step": step["step"] + 1,
                            "tool": "sqlmap",
                            "phase": "exploitation",
                            "duration": "5.5s",
                            "description": "数据库漏洞检测",
                            "success": True
                        })
                        # 重新编号后续步骤
                        for j in range(i + 2, len(path)):
                            path[j]["step"] += 1
                        break