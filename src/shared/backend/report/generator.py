# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
专业安全报告生成器（规则引擎决策系统版本）
生成可直接展示的安全报告，包含规则引擎攻击路径决策解释
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any
# 导入统一攻击链生成器
from backend.attack_chain.unified_attack_generator import UnifiedAttackGenerator


class SecurityReportGenerator:
    """专业安全报告生成器（规则引擎决策系统版本）"""
    
    def __init__(self, use_ai: bool = True):
        """
        初始化报告生成器
        
        Args:
            use_ai: 是否使用AI生成摘要（模拟）- 保留参数用于兼容性
        """
        self.use_ai = use_ai
        self.attack_chain_generator = UnifiedAttackGenerator(enable_evolution=True)
    
    def _generate_summary_with_ai(self, data: Dict) -> str:
        """
        使用规则引擎生成执行摘要
        
        Args:
            data: 输入数据
            
        Returns:
            执行摘要
        """
        if not self.use_ai:
            return self._generate_summary_fallback(data)
        
        target = data.get("target", "未知目标")
        assets = data.get("assets", [])
        attack_chain = data.get("attack_chain", [])
        
        # 模拟规则引擎生成摘要
        if attack_chain:
            steps = len(attack_chain)
            tools_used = [step.get("tool", "") for step in attack_chain]
            unique_tools = set(tools_used)
            
            # 添加规则引擎痕迹标识
            summary = "【规则引擎自动推演攻击路径生成】"
            summary += f"本次对{target}的安全测试共执行{steps}个攻击步骤，"
            summary += f"使用了{len(unique_tools)}种不同的安全工具。"
            
            # 根据攻击链内容补充
            if "exploit" in tools_used:
                summary += "系统基于多源扫描结果和规则引擎推导出最优攻击路径，"
                summary += "成功发现并验证了可利用的安全漏洞，"
                summary += "表明目标系统存在实际安全风险。"
            elif "nuclei" in tools_used or "sqlmap" in tools_used:
                summary += "规则引擎发现了多个潜在安全漏洞，"
                summary += "并自动推演了可能的攻击路径，"
                summary += "建议进行深入验证和修复。"
            else:
                summary += "规则引擎完成了初步的信息收集和资产发现，"
                summary += "为后续深入测试奠定了基础。"
            
            return summary
        
        # 如果没有攻击链，仍然添加规则引擎痕迹
        fallback_summary = self._generate_summary_fallback(data)
        return f"【规则引擎生成报告】{fallback_summary}"
    
    def _generate_summary_fallback(self, data: Dict) -> str:
        """回退规则生成摘要"""
        target = data.get("target", "未知目标")
        assets_count = len(data.get("assets", []))
        chain_length = len(data.get("attack_chain", []))
        
        summary = f"本次安全测试针对{target}进行，"
        summary += f"共发现{assets_count}个资产，"
        summary += f"执行了{chain_length}个攻击步骤。"
        
        return summary
    
    def _generate_attack_story(self, data: Dict) -> str:
        """
        生成攻击路径故事（Kill Chain Story）
        
        Args:
            data: 输入数据
            
        Returns:
            完整的攻击叙事
        """
        chain = data.get("attack_chain", [])
        
        if not chain:
            return "本次测试未发现完整的攻击路径"
        
        story = []
        
        for i, step in enumerate(chain):
            desc = step.get("description", "")
            
            if i == 0:
                story.append(f"攻击者首先{desc}")
            else:
                story.append(f"随后{desc}")
        
        if story:
            story.append("最终实现对目标系统的控制")
        
        return "，".join(story) + "。"
    
    def _calculate_risk_score(self, data: Dict) -> int:
        """
        计算风险评分（可解释风险模型）
        
        评分规则：
        - critical漏洞: +5分
        - high漏洞: +3分  
        - medium漏洞: +2分
        - low漏洞: +1分
        - SQL注入: +4分
        - CMS漏洞: +2分
        
        Returns:
            风险评分
        """
        score = 0
        results = data.get("results", {})
        
        # nuclei漏洞评分
        if "nuclei" in results:
            vulnerabilities = results["nuclei"].get("vulnerabilities", [])
            for vuln in vulnerabilities:
                if isinstance(vuln, dict):
                    sev = vuln.get("severity", "").lower()
                    if sev == "critical":
                        score += 5
                    elif sev == "high":
                        score += 3
                    elif sev == "medium":
                        score += 2
                    elif sev == "low":
                        score += 1
        
        # SQL注入评分
        if "sqlmap" in results:
            injection_points = results["sqlmap"].get("injection_points", [])
            if injection_points:
                score += 4
        
        # CMS漏洞评分
        if "wpscan" in results:
            plugins = results["wpscan"].get("plugins", [])
            for plugin in plugins:
                if isinstance(plugin, dict) and plugin.get("vulnerable"):
                    score += 2
        
        return score
    
    def _calculate_risk_level(self, data: Dict) -> str:
        """
        计算风险等级（基于可解释风险模型）
        
        规则：
        - 评分 >= 8 → 高
        - 评分 >= 4 → 中  
        - 否则 → 低
        """
        score = self._calculate_risk_score(data)
        
        if score >= 8:
            return "高"
        elif score >= 4:
            return "中"
        else:
            return "低"
    
    def _generate_impact(self, data: Dict) -> str:
        """
        生成影响分析
        
        Args:
            data: 输入数据
            
        Returns:
            影响分析描述
        """
        results = data.get("results", {})
        
        # 检查SQL注入
        if "sqlmap" in results:
            injection_points = results["sqlmap"].get("injection_points", [])
            if injection_points:
                return "攻击者可获取数据库中的用户凭证，进一步接管账户"
        
        # 检查高危漏洞
        if "nuclei" in results:
            vulnerabilities = results["nuclei"].get("vulnerabilities", [])
            for vuln in vulnerabilities:
                if isinstance(vuln, dict):
                    severity = vuln.get("severity", "").lower()
                    if severity == "critical":
                        return "攻击者可能远程执行代码，完全控制服务器"
                    elif severity == "high":
                        return "攻击者可能获取敏感信息或执行部分恶意操作"
        
        # 检查CMS漏洞
        if "wpscan" in results:
            plugins = results["wpscan"].get("plugins", [])
            for plugin in plugins:
                if isinstance(plugin, dict) and plugin.get("vulnerable"):
                    return "攻击者可能通过插件漏洞获取网站控制权"
        
        return "当前漏洞可能被用于信息泄露或进一步攻击"
    
    def _extract_key_findings(self, data: Dict) -> List[str]:
        """
        从攻击链提取关键发现
        
        Args:
            data: 输入数据
            
        Returns:
            关键发现列表
        """
        attack_chain = data.get("attack_chain", [])
        findings = []
        
        for step in attack_chain:
            tool = step.get("tool", "")
            description = step.get("description", "")
            
            # 根据工具类型提取关键发现
            if tool == "nmap":
                if "开放" in description:
                    findings.append(f"发现开放端口：{description}")
            elif tool == "whatweb":
                if "识别为" in description:
                    findings.append(f"技术栈识别：{description}")
            elif tool == "nuclei":
                if "漏洞" in description:
                    findings.append(f"安全漏洞：{description}")
            elif tool == "sqlmap":
                if "SQL注入" in description:
                    findings.append(f"数据库漏洞：{description}")
            elif tool == "wpscan":
                if "插件漏洞" in description or "WordPress" in description:
                    findings.append(f"CMS漏洞：{description}")
            elif tool == "exploit":
                findings.append(f"攻击验证：{description}")
            
            # 限制最多5个关键发现
            if len(findings) >= 5:
                break
        
        # 如果没有提取到关键发现，使用通用描述
        if not findings:
            findings = [
                "完成了基本的信息收集和资产发现",
                "进行了初步的安全漏洞扫描",
                "生成了完整的攻击路径分析"
            ]
        
        return findings
    
    def _extract_vulnerabilities(self, data: Dict) -> List[Dict]:
        """提取漏洞详细信息"""
        vulnerabilities = []
        results = data.get("results", {})
        
        # 从nuclei提取漏洞
        if "nuclei" in results:
            nuclei_vulns = results["nuclei"].get("vulnerabilities", [])
            for vuln in nuclei_vulns:
                if isinstance(vuln, dict):
                    vulnerabilities.append({
                        "type": "安全漏洞",
                        "name": vuln.get("name", "未知漏洞"),
                        "severity": vuln.get("severity", "unknown"),
                        "source": "nuclei"
                    })
        
        # 从sqlmap提取SQL注入点
        if "sqlmap" in results:
            injection_points = results["sqlmap"].get("injection_points", [])
            for point in injection_points:
                if isinstance(point, dict):
                    vulnerabilities.append({
                        "type": "SQL注入",
                        "name": "SQL注入漏洞",
                        "severity": "high",
                        "source": "sqlmap",
                        "details": point
                    })
        
        # 从wpscan提取插件漏洞
        if "wpscan" in results:
            plugins = results["wpscan"].get("plugins", [])
            for plugin in plugins:
                if isinstance(plugin, dict) and plugin.get("vulnerable"):
                    vulnerabilities.append({
                        "type": "插件漏洞",
                        "name": f"{plugin.get('name', '未知插件')}漏洞",
                        "severity": "medium",
                        "source": "wpscan"
                    })
        
        return vulnerabilities
    
    def _generate_recommendations(self, data: Dict) -> List[str]:
        """
        根据漏洞类型生成修复建议（定制化建议）
        
        Args:
            data: 输入数据
            
        Returns:
            修复建议列表
        """
        recommendations = []
        vulnerabilities = self._extract_vulnerabilities(data)
        results = data.get("results", {})
        
        # 通用建议
        recommendations.append("及时更新系统和应用补丁")
        recommendations.append("加强访问控制和身份验证机制")
        recommendations.append("定期进行安全扫描和渗透测试")
        
        # 针对特定漏洞的定制建议
        for vuln in vulnerabilities:
            vuln_type = vuln.get("type", "")
            severity = vuln.get("severity", "")
            name = vuln.get("name", "")
            
            if "SQL注入" in vuln_type:
                # 检查是否有具体的注入点信息
                if "sqlmap" in results:
                    injection_points = results["sqlmap"].get("injection_points", [])
                    if injection_points:
                        for point in injection_points:
                            if isinstance(point, dict):
                                url = point.get("url", "")
                                param = point.get("parameter", "")
                                if url and param:
                                    recommendations.append(f"对 {url} 的参数 {param} 使用参数化查询")
                                else:
                                    recommendations.append("对所有用户输入进行严格的过滤和验证")
                    else:
                        recommendations.append("使用参数化查询或预编译语句防止SQL注入")
            
            elif "安全漏洞" in vuln_type:
                if "critical" in severity or "high" in severity:
                    recommendations.append(f"立即修复高危漏洞 {name}，防止远程代码执行")
                else:
                    recommendations.append(f"评估漏洞 {name} 的实际影响并制定修复计划")
            
            elif "插件漏洞" in vuln_type:
                recommendations.append(f"立即更新插件 {name} 到最新版本")
                recommendations.append("移除不必要的插件，减少攻击面")
        
        # 检查攻击链中的具体路径
        attack_chain = data.get("attack_chain", [])
        for step in attack_chain:
            tool = step.get("tool", "")
            description = step.get("description", "")
            
            if tool == "nuclei" and "漏洞" in description:
                # 提取漏洞名称
                if "WordPress" in description:
                    recommendations.append("更新WordPress核心到最新版本")
                elif "PHP" in description:
                    recommendations.append("更新PHP版本并禁用危险函数")
            
            elif tool == "wpscan" and "插件" in description:
                recommendations.append("定期审查和更新所有WordPress插件")
        
        # 去重并限制数量
        unique_recs = []
        for rec in recommendations:
            if rec not in unique_recs:
                unique_recs.append(rec)
            if len(unique_recs) >= 8:  # 最多8条建议
                break
        
        return unique_recs
    
    def generate(self, data: Dict) -> Dict:
        """
        生成专业安全报告（规则引擎决策系统版本）
        
        Args:
            data: 输入数据，包含target、assets、results
            
        Returns:
            结构化报告（包含规则引擎决策信息）
        """
        # 验证必要字段
        if not data.get("target"):
            data["target"] = "未知目标"
        
        # 使用统一攻击链生成器生成攻击链和决策信息
        attack_chain_result = self.attack_chain_generator.generate_attack_chain(data.get("results", {}))
        
        # 提取生成的攻击链
        generated_attack_chain = attack_chain_result.get("attack_chain", [])
        
        # 如果原始数据中没有攻击链，使用生成的攻击链
        if not data.get("attack_chain") and generated_attack_chain:
            data["attack_chain"] = generated_attack_chain
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(data)
        
        # 生成报告各部分
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "SecurityReportGenerator",
                "version": "5.0",
                "ai_generated": False,
                "description": "规则引擎攻击推演生成",
                "rule_engine_decision_system": True,
                "decision_trace_enabled": True
            },
            "summary": self._generate_summary_with_ai(data),
            "risk_level": self._calculate_risk_level(data),
            "risk_score": risk_score,
            "attack_story": self._generate_attack_story(data),
            "impact": self._generate_impact(data),
            "key_findings": self._extract_key_findings(data),
            "attack_chain": data.get("attack_chain", []),
            "rule_engine_decision": {
                "decision": attack_chain_result.get("decision", {}),
                "target_analysis": attack_chain_result.get("target_analysis", {}),
                "execution_summary": attack_chain_result.get("execution_summary", {}),
                "analysis": attack_chain_result.get("analysis", {})
            },
            "details": {
                "assets": data.get("assets", []),
                "vulnerabilities": self._extract_vulnerabilities(data)
            },
            "recommendations": self._generate_recommendations(data)
        }
        
        return report
    
    def generate_from_example(self) -> Dict:
        """生成示例报告"""
        example_data = {
            "target": "example.com",
            "assets": [
                "http://example.com",
                "https://example.com",
                "http://example.com:8080"
            ],
            "results": {
                "nmap": {
                    "ports": [
                        {"port": 80, "service": "http", "state": "open"},
                        {"port": 443, "service": "https", "state": "open"},
                        {"port": 22, "service": "ssh", "state": "open"}
                    ]
                },
                "whatweb": {
                    "fingerprint": {
                        "web_server": "nginx",
                        "language": ["PHP"],
                        "cms": ["WordPress"]
                    }
                },
                "nuclei": {
                    "vulnerabilities": [
                        {"name": "WordPress Core XSS", "severity": "medium"},
                        {"name": "PHP Info Disclosure", "severity": "low"}
                    ]
                },
                "wpscan": {
                    "plugins": [
                        {"name": "contact-form-7", "version": "5.5", "vulnerable": True},
                        {"name": "akismet", "version": "4.1", "vulnerable": False}
                    ]
                }
            },
            "attack_chain": [
                {"step": 1, "tool": "nmap", "description": "发现80, 443, 22端口开放"},
                {"step": 2, "tool": "whatweb", "description": "识别为WordPress系统"},
                {"step": 3, "tool": "wpscan", "description": "发现contact-form-7插件漏洞"},
                {"step": 4, "tool": "nuclei", "description": "发现WordPress XSS漏洞"},
                {"step": 5, "tool": "exploit", "description": "验证XSS漏洞可利用性"}
            ]
        }
        
        return self.generate(example_data)


def main():
    """命令行入口点"""
    import argparse
    import json
    import sys
    
    parser = argparse.ArgumentParser(description="专业安全报告生成器")
    parser.add_argument("--input", type=str, help="输入JSON文件路径")
    parser.add_argument("--output", type=str, help="输出JSON文件路径（可选）")
    parser.add_argument("--example", action="store_true", help="生成示例报告")
    
    args = parser.parse_args()
    
    generator = SecurityReportGenerator(use_ai=False)
    
    if args.example:
        # 生成示例报告
        report = generator.generate_from_example()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    
    if args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            report = generator.generate(data)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                print(f"报告已保存到: {args.output}")
            else:
                print(json.dumps(report, indent=2, ensure_ascii=False))
                
        except FileNotFoundError:
            print(f"错误: 文件不存在 - {args.input}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"错误: 无效的JSON格式 - {args.input}")
            sys.exit(1)
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
    else:
        # 从标准输入读取
        try:
            data = json.load(sys.stdin)
            report = generator.generate(data)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("错误: 无效的JSON格式")
            sys.exit(1)
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)


