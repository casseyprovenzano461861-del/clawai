# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Agent模块 - 智能分析版本
使用DeepSeek API进行安全分析，具备攻击路径推演能力
"""

import json
import os
import sys
import requests


class SecurityAgent:
    """安全分析Agent类"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def call_llm(self, prompt):
        """调用DeepSeek API"""
        if not self.api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个资深网络安全专家，擅长攻击路径分析和威胁建模"},
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception:
            return None
    
    def _build_prompt(self, target, ports, vulnerabilities):
        """构建LLM提示词（包含攻击路径分析）"""
        ports_str = "无开放端口"
        if ports:
            ports_list = [f"{p.get('port', '')}/{p.get('service', '未知')}" for p in ports]
            ports_str = "、".join(ports_list)
        
        vulns_str = "无已知漏洞"
        if vulnerabilities:
            vulns_list = []
            for v in vulnerabilities:
                name = v.get('name', '未知漏洞')
                severity = v.get('severity', 'unknown')
                vulns_list.append(f"{name}({severity})")
            vulns_str = "、".join(vulns_list)
        
        return f"""请分析以下安全扫描结果：

目标：{target}
开放端口：{ports_str}
漏洞：{vulns_str}

请以资深网络安全专家的身份，进行攻击路径推演和威胁分析，输出JSON格式的分析结果：
{{
  "summary": "简要总结安全状况",
  "risk_level": "low/medium/high",
  "attack_path": "攻击者可能如何利用这些端口和漏洞进行攻击，包括攻击路径、利用方式和潜在危害",
  "advice": "具体的修复建议和安全措施"
}}

攻击路径分析要求：
1. 即使没有漏洞，也要分析端口暴露的攻击面
2. 考虑攻击者如何利用开放端口进行初始访问
3. 分析可能的横向移动路径
4. 评估权限提升的可能性
5. 考虑数据泄露和持久化威胁

请确保输出是有效的JSON格式，不要包含其他内容。"""
    
    def _rule_based_analyze(self, target, ports, vulnerabilities):
        """规则基础分析（fallback）"""
        port_count = len(ports)
        vuln_count = len(vulnerabilities)
        
        risk_level = "low"
        for vuln in vulnerabilities:
            severity = vuln.get('severity', '').lower()
            if severity in ['critical', 'high']:
                risk_level = "high"
                break
            elif severity == 'medium' and risk_level != 'high':
                risk_level = "medium"
        
        if vuln_count == 0 and port_count == 0:
            summary = f"目标 {target} 未发现开放端口和漏洞，安全性良好。"
        elif vuln_count == 0:
            summary = f"目标 {target} 发现 {port_count} 个开放端口，但未检测到已知漏洞。"
        else:
            summary = f"目标 {target} 发现 {port_count} 个开放端口和 {vuln_count} 个漏洞，风险等级为 {risk_level}。"
        
        # 攻击路径分析
        attack_path = "未发现明显的攻击路径。"
        if ports:
            port_analysis = []
            for port in ports:
                port_num = port.get('port', 0)
                service = port.get('service', '').lower()
                
                if port_num == 22 or 'ssh' in service:
                    port_analysis.append("SSH端口可能遭受暴力破解或密钥泄露攻击")
                elif port_num == 3389 or 'rdp' in service:
                    port_analysis.append("RDP端口可能被用于远程桌面攻击和横向移动")
                elif port_num == 445 or 'smb' in service:
                    port_analysis.append("SMB端口可能被用于横向渗透和权限提升")
                elif port_num in [80, 443, 8080, 8443] or 'http' in service:
                    port_analysis.append("Web服务端口可能遭受注入攻击、跨站脚本或目录遍历")
                elif port_num == 21 or 'ftp' in service:
                    port_analysis.append("FTP端口可能存在弱口令或匿名访问风险")
                elif port_num == 3306 or 'mysql' in service:
                    port_analysis.append("数据库端口可能遭受SQL注入或未授权访问")
            
            if port_analysis:
                attack_path = "攻击者可能通过以下路径进行攻击：" + "；".join(port_analysis[:3])
        
        if risk_level == "low":
            advice = "系统配置相对安全，但仍建议定期更新补丁，加固安全基线，防范零日漏洞攻击。"
        elif risk_level == "medium":
            advice = "系统存在中等风险漏洞，建议实施深度防御策略，加强日志监控和入侵检测。"
        else:  # high
            high_vulns = [v for v in vulnerabilities if v.get('severity', '').lower() in ['critical', 'high']]
            if high_vulns:
                vuln_names = "、".join([v.get('name', '未知漏洞') for v in high_vulns[:2]])
                advice = f"发现高危漏洞: {vuln_names}。这些漏洞可能导致远程代码执行或权限提升，建议立即修复并隔离受影响系统。"
            else:
                advice = "系统暴露大量攻击面，存在严重安全风险。建议立即进行应急响应，实施网络隔离，并启动安全事件调查流程。"
        
        return {
            "summary": summary,
            "risk_level": risk_level,
            "attack_path": attack_path,
            "advice": advice
        }
    
    def analyze(self, scan_result):
        """分析扫描结果"""
        target = scan_result.get('target', 'unknown')
        recon = scan_result.get('recon', {})
        scan = scan_result.get('scan', {})
        
        ports = recon.get('ports', []) if recon else []
        vulnerabilities = scan.get('vulnerabilities', []) if scan else []
        
        # 尝试使用LLM分析
        if self.api_key:
            prompt = self._build_prompt(target, ports, vulnerabilities)
            llm_response = self.call_llm(prompt)
            
            if llm_response:
                try:
                    result = json.loads(llm_response.strip())
                    if all(key in result for key in ["summary", "risk_level", "attack_path", "advice"]):
                        return result
                except json.JSONDecodeError:
                    pass
        
        # 回退到规则基础分析
        return self._rule_based_analyze(target, ports, vulnerabilities)


def main():
    if len(sys.argv) != 2:
        print("用法: python  <scan_result_json> - agent.py:179")
        print("示例: python  '{\"target\":\"example.com\",\"recon\":{\"ports\":[]},\"scan\":{\"vulnerabilities\":[]}}' - agent.py:180")
        sys.exit(1)
    
    try:
        scan_result = json.loads(sys.argv[1])
        agent = SecurityAgent()
        report = agent.analyze(scan_result)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("错误: 输入不是有效的JSON格式 - agent.py:189")
        sys.exit(1)
    except Exception as e:
        print(f"分析失败: {str(e)} - agent.py:192")
        sys.exit(1)


if __name__ == "__main__":
    main()
