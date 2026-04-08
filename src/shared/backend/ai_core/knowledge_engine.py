# -*- coding: utf-8 -*-
"""
知识增强引擎
为智能体提供漏洞知识库、Payload军火库和攻击手册
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Vulnerability:
    """漏洞信息"""
    cve_id: str
    name: str
    description: str
    severity: str
    cvss_score: float
    affected_systems: List[str]
    remediation: str
    references: List[str]


@dataclass
class Payload:
    """Payload信息"""
    id: str
    name: str
    description: str
    vulnerability_type: str
    payload: str
    usage: str
    references: List[str]


@dataclass
class AttackPlaybook:
    """攻击手册"""
    id: str
    name: str
    description: str
    scenario: str
    steps: List[str]
    tools: List[str]
    references: List[str]


class KnowledgeEngine:
    """知识增强引擎"""
    
    def __init__(self):
        """初始化知识增强引擎"""
        self.knowledge_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        self.vulnerability_db = self.load_vulnerability_db()
        self.payload_db = self.load_payload_db()
        self.attack_playbooks = self.load_attack_playbooks()
    
    def load_vulnerability_db(self) -> Dict[str, Vulnerability]:
        """加载漏洞数据库"""
        vuln_db = {}
        
        # 加载内置漏洞数据
        builtin_vulns = self._get_builtin_vulnerabilities()
        for vuln in builtin_vulns:
            vuln_db[vuln.cve_id] = vuln
        
        # 加载自定义漏洞数据
        custom_vuln_file = os.path.join(self.knowledge_dir, "custom_vulnerabilities.json")
        if os.path.exists(custom_vuln_file):
            try:
                with open(custom_vuln_file, 'r', encoding='utf-8') as f:
                    custom_vulns = json.load(f)
                    for vuln_data in custom_vulns:
                        vuln = Vulnerability(**vuln_data)
                        vuln_db[vuln.cve_id] = vuln
            except Exception as e:
                print(f"加载自定义漏洞数据失败: {e}")
        
        return vuln_db
    
    def load_payload_db(self) -> Dict[str, Payload]:
        """加载Payload数据库"""
        payload_db = {}
        
        # 加载内置Payload数据
        builtin_payloads = self._get_builtin_payloads()
        for payload in builtin_payloads:
            payload_db[payload.id] = payload
        
        # 加载自定义Payload数据
        custom_payload_file = os.path.join(self.knowledge_dir, "custom_payloads.json")
        if os.path.exists(custom_payload_file):
            try:
                with open(custom_payload_file, 'r', encoding='utf-8') as f:
                    custom_payloads = json.load(f)
                    for payload_data in custom_payloads:
                        payload = Payload(**payload_data)
                        payload_db[payload.id] = payload
            except Exception as e:
                print(f"加载自定义Payload数据失败: {e}")
        
        return payload_db
    
    def load_attack_playbooks(self) -> Dict[str, AttackPlaybook]:
        """加载攻击手册"""
        playbook_db = {}
        
        # 加载内置攻击手册
        builtin_playbooks = self._get_builtin_attack_playbooks()
        for playbook in builtin_playbooks:
            playbook_db[playbook.id] = playbook
        
        # 加载自定义攻击手册
        custom_playbook_file = os.path.join(self.knowledge_dir, "custom_playbooks.json")
        if os.path.exists(custom_playbook_file):
            try:
                with open(custom_playbook_file, 'r', encoding='utf-8') as f:
                    custom_playbooks = json.load(f)
                    for playbook_data in custom_playbooks:
                        playbook = AttackPlaybook(**playbook_data)
                        playbook_db[playbook.id] = playbook
            except Exception as e:
                print(f"加载自定义攻击手册失败: {e}")
        
        return playbook_db
    
    def _get_builtin_vulnerabilities(self) -> List[Vulnerability]:
        """获取内置漏洞数据"""
        return [
            Vulnerability(
                cve_id="CVE-2023-1234",
                name="SQL注入漏洞",
                description="Web应用程序中的SQL注入漏洞，攻击者可以通过注入恶意SQL语句获取数据库信息",
                severity="high",
                cvss_score=8.5,
                affected_systems=["Web应用", "数据库"],
                remediation="使用参数化查询，避免直接拼接SQL语句",
                references=["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-1234"]
            ),
            Vulnerability(
                cve_id="CVE-2023-5678",
                name="跨站脚本漏洞",
                description="Web应用程序中的XSS漏洞，攻击者可以注入恶意脚本",
                severity="medium",
                cvss_score=6.1,
                affected_systems=["Web应用"],
                remediation="对用户输入进行适当的转义和过滤",
                references=["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-5678"]
            ),
            Vulnerability(
                cve_id="CVE-2023-9012",
                name="命令注入漏洞",
                description="Web应用程序中的命令注入漏洞，攻击者可以执行系统命令",
                severity="critical",
                cvss_score=9.8,
                affected_systems=["Web应用", "服务器"],
                remediation="对用户输入进行严格的验证和过滤，避免直接执行系统命令",
                references=["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-9012"]
            )
        ]
    
    def _get_builtin_payloads(self) -> List[Payload]:
        """获取内置Payload数据"""
        return [
            Payload(
                id="payload-001",
                name="SQL注入Payload",
                description="用于测试SQL注入漏洞的Payload",
                vulnerability_type="sql_injection",
                payload="' OR 1=1 --",
                usage="在输入框中输入该Payload，观察是否返回所有记录",
                references=["https://owasp.org/www-community/attacks/SQL_Injection"]
            ),
            Payload(
                id="payload-002",
                name="XSS Payload",
                description="用于测试XSS漏洞的Payload",
                vulnerability_type="xss",
                payload="<script>alert('XSS')</script>",
                usage="在输入框中输入该Payload，观察是否弹出alert框",
                references=["https://owasp.org/www-community/attacks/xss/"]
            ),
            Payload(
                id="payload-003",
                name="命令注入Payload",
                description="用于测试命令注入漏洞的Payload",
                vulnerability_type="command_injection",
                payload="; ls -la",
                usage="在输入框中输入该Payload，观察是否执行ls命令",
                references=["https://owasp.org/www-community/attacks/Command_Injection"]
            )
        ]
    
    def _get_builtin_attack_playbooks(self) -> List[AttackPlaybook]:
        """获取内置攻击手册"""
        return [
            AttackPlaybook(
                id="playbook-001",
                name="Web应用渗透测试",
                description="针对Web应用的完整渗透测试流程",
                scenario="Web应用安全测试",
                steps=[
                    "信息收集：使用nmap、subfinder等工具收集目标信息",
                    "漏洞扫描：使用nuclei、nikto等工具扫描漏洞",
                    "漏洞验证：对发现的漏洞进行验证",
                    "漏洞利用：尝试利用验证成功的漏洞",
                    "后渗透：在成功利用漏洞后进行进一步操作",
                    "报告生成：生成详细的安全测试报告"
                ],
                tools=["nmap", "subfinder", "nuclei", "nikto", "sqlmap"],
                references=["https://owasp.org/www-project-web-security-testing-guide/"]
            ),
            AttackPlaybook(
                id="playbook-002",
                name="网络渗透测试",
                description="针对网络的完整渗透测试流程",
                scenario="网络安全测试",
                steps=[
                    "网络扫描：使用nmap扫描网络拓扑",
                    "服务识别：识别网络中的服务和版本",
                    "漏洞扫描：扫描网络中的漏洞",
                    "漏洞利用：尝试利用发现的漏洞",
                    "权限提升：获取更高的系统权限",
                    "持久化：建立持久访问通道",
                    "报告生成：生成详细的安全测试报告"
                ],
                tools=["nmap", "masscan", "metasploit", "hydra"],
                references=["https://owasp.org/www-project-network-security-testing-guide/"]
            )
        ]
    
    def search_vulnerabilities(self, target_info: Dict[str, Any]) -> List[Vulnerability]:
        """根据目标信息搜索相关漏洞"""
        # 提取目标信息
        target = target_info.get("target", "")
        technology_stack = target_info.get("technology_stack", [])
        open_ports = target_info.get("open_ports", [])
        
        # 搜索相关漏洞
        relevant_vulns = []
        for vuln in self.vulnerability_db.values():
            # 检查是否与目标技术栈相关
            for system in vuln.affected_systems:
                if any(tech.lower() in system.lower() for tech in technology_stack):
                    relevant_vulns.append(vuln)
                    break
        
        return relevant_vulns
    
    def get_payload(self, vulnerability_id: str) -> Optional[Payload]:
        """获取漏洞对应的payload"""
        # 简单实现：根据漏洞类型查找对应的payload
        vuln = self.vulnerability_db.get(vulnerability_id)
        if not vuln:
            return None
        
        # 根据漏洞描述推断漏洞类型
        vuln_desc = vuln.description.lower()
        if "sql" in vuln_desc:
            vuln_type = "sql_injection"
        elif "xss" in vuln_desc:
            vuln_type = "xss"
        elif "command" in vuln_desc:
            vuln_type = "command_injection"
        else:
            vuln_type = "general"
        
        # 查找对应类型的payload
        for payload in self.payload_db.values():
            if payload.vulnerability_type == vuln_type:
                return payload
        
        return None
    
    def get_attack_playbook(self, scenario: str) -> Optional[AttackPlaybook]:
        """获取特定场景的攻击手册"""
        for playbook in self.attack_playbooks.values():
            if scenario.lower() in playbook.scenario.lower():
                return playbook
        
        return None
    
    def add_vulnerability(self, vulnerability: Vulnerability):
        """添加新漏洞"""
        self.vulnerability_db[vulnerability.cve_id] = vulnerability
        self._save_custom_vulnerabilities()
    
    def add_payload(self, payload: Payload):
        """添加新payload"""
        self.payload_db[payload.id] = payload
        self._save_custom_payloads()
    
    def add_attack_playbook(self, playbook: AttackPlaybook):
        """添加新攻击手册"""
        self.attack_playbooks[playbook.id] = playbook
        self._save_custom_playbooks()
    
    def _save_custom_vulnerabilities(self):
        """保存自定义漏洞"""
        custom_vulns = []
        for vuln in self.vulnerability_db.values():
            # 只保存自定义漏洞（非内置）
            if not vuln.cve_id.startswith("CVE-2023-"):
                custom_vulns.append({
                    "cve_id": vuln.cve_id,
                    "name": vuln.name,
                    "description": vuln.description,
                    "severity": vuln.severity,
                    "cvss_score": vuln.cvss_score,
                    "affected_systems": vuln.affected_systems,
                    "remediation": vuln.remediation,
                    "references": vuln.references
                })
        
        custom_vuln_file = os.path.join(self.knowledge_dir, "custom_vulnerabilities.json")
        with open(custom_vuln_file, 'w', encoding='utf-8') as f:
            json.dump(custom_vulns, f, ensure_ascii=False, indent=2)
    
    def _save_custom_payloads(self):
        """保存自定义payload"""
        custom_payloads = []
        for payload in self.payload_db.values():
            # 只保存自定义payload（非内置）
            if not payload.id.startswith("payload-00"):
                custom_payloads.append({
                    "id": payload.id,
                    "name": payload.name,
                    "description": payload.description,
                    "vulnerability_type": payload.vulnerability_type,
                    "payload": payload.payload,
                    "usage": payload.usage,
                    "references": payload.references
                })
        
        custom_payload_file = os.path.join(self.knowledge_dir, "custom_payloads.json")
        with open(custom_payload_file, 'w', encoding='utf-8') as f:
            json.dump(custom_payloads, f, ensure_ascii=False, indent=2)
    
    def _save_custom_playbooks(self):
        """保存自定义攻击手册"""
        custom_playbooks = []
        for playbook in self.attack_playbooks.values():
            # 只保存自定义攻击手册（非内置）
            if not playbook.id.startswith("playbook-00"):
                custom_playbooks.append({
                    "id": playbook.id,
                    "name": playbook.name,
                    "description": playbook.description,
                    "scenario": playbook.scenario,
                    "steps": playbook.steps,
                    "tools": playbook.tools,
                    "references": playbook.references
                })
        
        custom_playbook_file = os.path.join(self.knowledge_dir, "custom_playbooks.json")
        with open(custom_playbook_file, 'w', encoding='utf-8') as f:
            json.dump(custom_playbooks, f, ensure_ascii=False, indent=2)
    
    def get_vulnerability_by_cve(self, cve_id: str) -> Optional[Vulnerability]:
        """根据CVE ID获取漏洞信息"""
        return self.vulnerability_db.get(cve_id)
    
    def get_all_vulnerabilities(self) -> List[Vulnerability]:
        """获取所有漏洞"""
        return list(self.vulnerability_db.values())
    
    def get_all_payloads(self) -> List[Payload]:
        """获取所有payload"""
        return list(self.payload_db.values())
    
    def get_all_attack_playbooks(self) -> List[AttackPlaybook]:
        """获取所有攻击手册"""
        return list(self.attack_playbooks.values())


# 测试代码
if __name__ == "__main__":
    # 初始化知识增强引擎
    knowledge_engine = KnowledgeEngine()
    
    print("=" * 80)
    print("知识增强引擎测试")
    print("=" * 80)
    
    # 测试1: 获取所有漏洞
    print("\n测试1: 获取所有漏洞")
    vulnerabilities = knowledge_engine.get_all_vulnerabilities()
    print(f"漏洞数量: {len(vulnerabilities)}")
    for vuln in vulnerabilities:
        print(f"- {vuln.cve_id}: {vuln.name} ({vuln.severity})")
    
    # 测试2: 获取所有payload
    print("\n测试2: 获取所有payload")
    payloads = knowledge_engine.get_all_payloads()
    print(f"Payload数量: {len(payloads)}")
    for payload in payloads:
        print(f"- {payload.id}: {payload.name} ({payload.vulnerability_type})")
    
    # 测试3: 获取所有攻击手册
    print("\n测试3: 获取所有攻击手册")
    playbooks = knowledge_engine.get_all_attack_playbooks()
    print(f"攻击手册数量: {len(playbooks)}")
    for playbook in playbooks:
        print(f"- {playbook.id}: {playbook.name} ({playbook.scenario})")
    
    # 测试4: 搜索相关漏洞
    print("\n测试4: 搜索相关漏洞")
    target_info = {
        "target": "example.com",
        "technology_stack": ["Web应用", "SQL"],
        "open_ports": [80, 443]
    }
    relevant_vulns = knowledge_engine.search_vulnerabilities(target_info)
    print(f"相关漏洞数量: {len(relevant_vulns)}")
    for vuln in relevant_vulns:
        print(f"- {vuln.cve_id}: {vuln.name}")
    
    # 测试5: 获取漏洞对应的payload
    print("\n测试5: 获取漏洞对应的payload")
    payload = knowledge_engine.get_payload("CVE-2023-1234")
    if payload:
        print(f"找到payload: {payload.name}")
        print(f"Payload内容: {payload.payload}")
    else:
        print("未找到对应的payload")
    
    # 测试6: 获取攻击手册
    print("\n测试6: 获取攻击手册")
    playbook = knowledge_engine.get_attack_playbook("Web应用")
    if playbook:
        print(f"找到攻击手册: {playbook.name}")
        print("步骤:")
        for i, step in enumerate(playbook.steps, 1):
            print(f"{i}. {step}")
    else:
        print("未找到对应的攻击手册")
    
    print("\n" + "=" * 80)
    print("测试完成")
