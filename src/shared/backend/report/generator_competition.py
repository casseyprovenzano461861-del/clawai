# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""比赛级安全报告生成器（≤200行）"""

import json, sys
from datetime import datetime
import os

# 添加attack_chain目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from attack_chain.generator import AttackChainGenerator

class CompetitionReportGenerator:
    def __init__(self, use_ai=True):
        self.use_ai = use_ai
        self.attack_chain_generator = AttackChainGenerator()
    
    def _ai_summary(self, data):
        target = data.get("target", "未知目标")
        assets = len(data.get("assets", []))
        chain = data.get("attack_chain", [])
        if not self.use_ai:
            return f"对{target}的安全测试，发现{assets}个资产，执行{len(chain)}个步骤。"
        tools = {step.get("tool", "") for step in chain}
        vuln_tools = {"nuclei", "sqlmap", "wpscan", "exploit"}
        has_vulns = bool(tools & vuln_tools)
        summary = f"本次对{target}的安全评估"
        if has_vulns:
            summary += "发现了多个安全漏洞，包括"
            if "nuclei" in tools: summary += "自动化漏洞扫描结果、"
            if "sqlmap" in tools: summary += "SQL注入点、"
            if "exploit" in tools: summary += "可验证的攻击路径。"
            else: summary += "潜在的安全风险。"
        else:
            summary += f"完成了信息收集和{len(chain)}步攻击链分析，为深度测试奠定了基础。"
        return summary
    
    def _risk_level(self, data):
        results = data.get("results", {})
        if "nuclei" in results:
            for vuln in results["nuclei"].get("vulnerabilities", []):
                if isinstance(vuln, dict):
                    sev = vuln.get("severity", "").lower()
                    if sev in ["critical", "high"]: return "高"
                    if sev == "medium": return "中"
        if "sqlmap" in results and results["sqlmap"].get("injection_points"):
            return "中"
        if "wpscan" in results:
            for plugin in results["wpscan"].get("plugins", []):
                if isinstance(plugin, dict) and plugin.get("vulnerable"):
                    return "中"
        return "低"
    
    def _key_findings(self, data):
        findings = []
        for step in data.get("attack_chain", [])[:5]:
            tool, desc = step.get("tool", ""), step.get("description", "")
            if tool == "nmap" and "开放" in desc:
                findings.append(f"端口发现: {desc}")
            elif tool == "whatweb" and "识别" in desc:
                findings.append(f"技术栈识别: {desc}")
            elif tool in ["nuclei", "sqlmap", "wpscan"] and "漏洞" in desc:
                findings.append(f"安全漏洞: {desc}")
            elif tool == "exploit":
                findings.append(f"攻击验证: {desc}")
        if not findings:
            findings = ["完成基础信息收集", "执行自动化漏洞扫描", "生成攻击路径分析"]
        return findings
    
    def _vulnerabilities(self, data):
        vulns = []
        results = data.get("results", {})
        if "nuclei" in results:
            for v in results["nuclei"].get("vulnerabilities", []):
                if isinstance(v, dict):
                    vulns.append({"type": "安全漏洞", "name": v.get("name", "未知"),
                                 "severity": v.get("severity", "unknown"), "source": "nuclei"})
        if "sqlmap" in results:
            for point in results["sqlmap"].get("injection_points", []):
                if isinstance(point, dict):
                    vulns.append({"type": "SQL注入", "name": "SQL注入漏洞",
                                 "severity": "high", "source": "sqlmap"})
        if "wpscan" in results:
            for plugin in results["wpscan"].get("plugins", []):
                if isinstance(plugin, dict) and plugin.get("vulnerable"):
                    vulns.append({"type": "插件漏洞", "name": f"{plugin.get('name', '未知')}漏洞",
                                 "severity": "medium", "source": "wpscan"})
        return vulns
    
    def _recommendations(self, data):
        recs = ["及时更新系统和应用补丁", "加强访问控制和身份验证", "定期进行安全扫描和测试"]
        for vuln in self._vulnerabilities(data):
            vuln_type, severity = vuln.get("type", ""), vuln.get("severity", "")
            if "SQL注入" in vuln_type:
                recs.extend(["对用户输入进行严格过滤和验证", "使用参数化查询或预编译语句"])
            elif "安全漏洞" in vuln_type:
                if severity in ["critical", "high"]:
                    recs.append("立即修复高危漏洞，防止远程代码执行")
                else:
                    recs.append("评估中低危漏洞影响并制定修复计划")
            elif "插件漏洞" in vuln_type:
                recs.extend(["及时更新CMS插件和主题到最新版本", "移除不必要的插件，减少攻击面"])
        unique = []
        for rec in recs:
            if rec not in unique:
                unique.append(rec)
            if len(unique) >= 6:
                break
        return unique
    
    def generate(self, data):
        # 自动生成攻击链（如果数据中没有或需要重新生成）
        if "attack_chain" not in data or not data["attack_chain"]:
            # 使用攻击链生成器自动生成
            data = self.attack_chain_generator.generate_and_merge(data)
        
        return {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "CompetitionReportGenerator",
                "version": "2.0"
            },
            "summary": self._ai_summary(data),
            "risk_level": self._risk_level(data),
            "key_findings": self._key_findings(data),
            "attack_chain": data.get("attack_chain", []),
            "details": {
                "assets": data.get("assets", []),
                "vulnerabilities": self._vulnerabilities(data)
            },
            "recommendations": self._recommendations(data)
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="比赛级安全报告生成器")
    parser.add_argument("--input", help="输入JSON文件路径")
    parser.add_argument("--example", action="store_true", help="生成示例报告")
    parser.add_argument("--no-ai", action="store_true", help="不使用AI生成摘要")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--auto-chain", action="store_true", help="自动生成攻击链（覆盖输入中的攻击链）")
    args = parser.parse_args()
    generator = CompetitionReportGenerator(use_ai=not args.no_ai)
    
    if args.example:
        data = {
            "target": "example.com",
            "assets": ["http://example.com", "https://example.com"],
            "results": {
                "nmap": {"ports": [{"port": 80, "service": "http"}]},
                "nuclei": {"vulnerabilities": [{"name": "XSS Vulnerability", "severity": "medium"}]}
            },
            "attack_chain": [
                {"step": 1, "tool": "nmap", "description": "发现80端口开放"},
                {"step": 2, "tool": "nuclei", "description": "发现XSS漏洞"}
            ]
        }
    elif args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"错误: {str(e)} - generator_competition.py:150"); sys.exit(1)
    else:
        try:
            input_data = sys.stdin.read()
            data = json.loads(input_data) if input_data else {}
        except Exception as e:
            print(f"错误: 无效输入 - {str(e)}")
            print("用法: python generator_competition.py --input <file>")
            sys.exit(1)
    
    # 如果指定了自动生成攻击链，则覆盖输入中的攻击链
    if args.auto_chain:
        data = generator.attack_chain_generator.generate_and_merge(data)
    
    result = generator.generate(data)
    output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"报告已保存到: {args.output} - generator_competition.py:165")
        except Exception as e:
            print(f"保存失败: {str(e)} - generator_competition.py:167"); sys.exit(1)
    else:
        print(output)

if __name__ == "__main__":
    main()
