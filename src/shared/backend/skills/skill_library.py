from __future__ import annotations

from typing import Any, Dict, List


class SkillLibrary:
    """渗透技巧技能库 - 封装各类渗透技巧供AI调用"""
    
    def __init__(self):
        self.skills = self._initialize_skills()
    
    def _initialize_skills(self) -> Dict[str, Dict[str, Any]]:
        """初始化技能库 - 扩展至30个技能"""
        return {
            # ========== 侦察类技能 (5个) ==========
            "recon.subdomain_enum": {
                "name": "子域名枚举",
                "description": "使用Subfinder/Amass进行子域名发现和枚举",
                "category": "reconnaissance",
                "difficulty": "medium",
                "tools": ["subfinder", "amass", "sublist3r"],
                "prerequisites": [],
                "output": "子域名列表、DNS记录、关联资产",
                "success_rate": 0.85
            },
            "recon.port_scan": {
                "name": "端口扫描",
                "description": "使用NMAP进行全面的端口扫描和服务识别",
                "category": "reconnaissance",
                "difficulty": "easy",
                "tools": ["nmap", "masscan"],
                "prerequisites": ["recon.subdomain_enum"],
                "output": "开放端口、服务版本、操作系统信息",
                "success_rate": 0.95
            },
            "recon.web_fingerprint": {
                "name": "Web指纹识别",
                "description": "使用WhatWeb/Wappalyzer识别Web应用技术栈",
                "category": "reconnaissance",
                "difficulty": "easy",
                "tools": ["whatweb", "wappalyzer"],
                "prerequisites": ["recon.port_scan"],
                "output": "Web框架、CMS版本、服务器信息、技术栈详情",
                "success_rate": 0.90
            },
            "recon.dir_bruteforce": {
                "name": "目录爆破",
                "description": "使用Dirsearch/Dirb进行目录和文件发现",
                "category": "reconnaissance",
                "difficulty": "medium",
                "tools": ["dirsearch", "dirb", "gobuster"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "隐藏目录、敏感文件、备份文件、配置文件",
                "success_rate": 0.75
            },
            "recon.cms_identification": {
                "name": "CMS识别",
                "description": "识别和验证CMS类型及版本",
                "category": "reconnaissance",
                "difficulty": "easy",
                "tools": ["whatweb", "wpscan", "droopescan"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "CMS类型、版本号、插件/主题信息、已知漏洞",
                "success_rate": 0.92
            },
            
            # ========== 漏洞利用类技能 (15个) ==========
            # SQL注入变体 (5种)
            "exploit.sql_union": {
                "name": "Union-based SQL注入",
                "description": "使用UNION查询进行SQL注入攻击",
                "category": "exploitation",
                "difficulty": "medium",
                "tools": ["sqlmap", "手动测试"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "数据库信息、表结构、数据提取",
                "success_rate": 0.85
            },
            "exploit.sql_boolean": {
                "name": "Boolean-based SQL注入",
                "description": "基于布尔盲注的SQL注入攻击",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["sqlmap", "手动测试"],
                "prerequisites": ["exploit.sql_union"],
                "output": "数据库信息、条件判断结果、数据推断",
                "success_rate": 0.70
            },
            "exploit.sql_time": {
                "name": "Time-based SQL注入",
                "description": "基于时间延迟的SQL注入攻击",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["sqlmap", "手动测试"],
                "prerequisites": ["exploit.sql_boolean"],
                "output": "数据库信息、时间延迟验证、数据提取",
                "success_rate": 0.65
            },
            "exploit.sql_error": {
                "name": "Error-based SQL注入",
                "description": "基于错误信息的SQL注入攻击",
                "category": "exploitation",
                "difficulty": "medium",
                "tools": ["sqlmap", "手动测试"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "数据库错误信息、版本信息、结构信息",
                "success_rate": 0.80
            },
            "exploit.sql_outofband": {
                "name": "Out-of-band SQL注入",
                "description": "带外数据提取的SQL注入攻击",
                "category": "exploitation",
                "difficulty": "expert",
                "tools": ["sqlmap", "自定义脚本"],
                "prerequisites": ["exploit.sql_time"],
                "output": "DNS/HTTP带外数据、数据库信息",
                "success_rate": 0.60
            },
            
            # XSS类型 (3种)
            "exploit.xss_reflected": {
                "name": "反射型XSS利用",
                "description": "利用反射型XSS漏洞执行恶意脚本",
                "category": "exploitation",
                "difficulty": "medium",
                "tools": ["xsstrike", "beef", "手动测试"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "XSS验证、payload执行、会话窃取",
                "success_rate": 0.75
            },
            "exploit.xss_stored": {
                "name": "存储型XSS利用",
                "description": "利用存储型XSS漏洞进行持久化攻击",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["xsstrike", "beef", "手动测试"],
                "prerequisites": ["exploit.xss_reflected"],
                "output": "持久化payload、用户感染、数据窃取",
                "success_rate": 0.70
            },
            "exploit.xss_dom": {
                "name": "DOM-based XSS利用",
                "description": "利用DOM型XSS漏洞进行客户端攻击",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["xsstrike", "手动测试"],
                "prerequisites": ["exploit.xss_reflected"],
                "output": "DOM操作验证、客户端攻击、会话劫持",
                "success_rate": 0.65
            },
            
            # RCE方式 (3种)
            "exploit.rce_command": {
                "name": "命令注入RCE",
                "description": "通过命令注入实现远程代码执行",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["手动测试", "自定义payload"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "命令执行验证、shell获取、权限确认",
                "success_rate": 0.70
            },
            "exploit.rce_deserialization": {
                "name": "反序列化RCE",
                "description": "通过反序列化漏洞实现远程代码执行",
                "category": "exploitation",
                "difficulty": "expert",
                "tools": ["ysoserial", "手动测试"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "反序列化验证、代码执行、漏洞利用",
                "success_rate": 0.60
            },
            "exploit.rce_file_upload": {
                "name": "文件上传RCE",
                "description": "通过文件上传漏洞实现远程代码执行",
                "category": "exploitation",
                "difficulty": "medium",
                "tools": ["手动测试", "webshell"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "文件上传验证、webshell部署、代码执行",
                "success_rate": 0.75
            },
            
            # 其他漏洞利用 (4种)
            "exploit.file_inclusion": {
                "name": "文件包含漏洞利用",
                "description": "利用本地/远程文件包含漏洞",
                "category": "exploitation",
                "difficulty": "medium",
                "tools": ["手动测试", "自定义payload"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "文件包含验证、敏感文件读取、代码执行",
                "success_rate": 0.72
            },
            "exploit.file_upload": {
                "name": "文件上传漏洞利用",
                "description": "利用文件上传功能漏洞",
                "category": "exploitation",
                "difficulty": "medium",
                "tools": ["手动测试", "webshell"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "文件上传绕过、恶意文件上传、控制获取",
                "success_rate": 0.68
            },
            "exploit.command_injection": {
                "name": "命令注入漏洞利用",
                "description": "利用系统命令注入漏洞",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["手动测试", "自定义payload"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "命令注入验证、系统命令执行、权限提升",
                "success_rate": 0.65
            },
            "exploit.ssrf": {
                "name": "SSRF漏洞利用",
                "description": "利用服务器端请求伪造漏洞",
                "category": "exploitation",
                "difficulty": "hard",
                "tools": ["手动测试", "自定义payload"],
                "prerequisites": ["recon.web_fingerprint"],
                "output": "SSRF验证、内网探测、端口扫描、服务访问",
                "success_rate": 0.70
            },
            
            # ========== 后渗透类技能 (10个) ==========
            "post.privilege_escalation": {
                "name": "权限提升",
                "description": "Windows/Linux系统权限提升方法",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["metasploit", "linpeas", "winpeas", "linux-exploit-suggester"],
                "prerequisites": ["exploit.rce_command"],
                "output": "提权方法、漏洞利用、系统控制、root/admin权限",
                "success_rate": 0.60
            },
            "post.lateral_movement": {
                "name": "横向移动",
                "description": "内网横向移动和主机间跳转",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["crackmapexec", "impacket", "psexec", "wmiexec"],
                "prerequisites": ["post.privilege_escalation"],
                "output": "内网主机发现、凭证传递、服务访问、域控攻击",
                "success_rate": 0.55
            },
            "post.credential_theft": {
                "name": "凭证窃取",
                "description": "窃取系统凭证和会话令牌",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["mimikatz", "hashcat", "john", "responder"],
                "prerequisites": ["post.lateral_movement"],
                "output": "密码哈希、明文密码、会话令牌、Kerberos票据",
                "success_rate": 0.65
            },
            "post.persistence_control": {
                "name": "持久化控制",
                "description": "建立持久化后门和控制机制",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["metasploit", "empire", "cobaltstrike"],
                "prerequisites": ["post.credential_theft"],
                "output": "后门部署、计划任务、服务安装、注册表修改",
                "success_rate": 0.70
            },
            "post.data_exfiltration": {
                "name": "数据窃取",
                "description": "窃取敏感数据和文件",
                "category": "post_exploitation",
                "difficulty": "hard",
                "tools": ["rsync", "scp", "ftp", "webdav"],
                "prerequisites": ["post.persistence_control"],
                "output": "敏感文件、数据库备份、配置文件、用户数据",
                "success_rate": 0.75
            },
            "post.cover_tracks": {
                "name": "痕迹清理",
                "description": "清理攻击痕迹和日志",
                "category": "post_exploitation",
                "difficulty": "hard",
                "tools": ["meterpreter", "自定义脚本"],
                "prerequisites": ["post.data_exfiltration"],
                "output": "日志清理、文件删除、时间戳修改、审计绕过",
                "success_rate": 0.80
            },
            "post.network_recon": {
                "name": "内网侦察",
                "description": "内网网络拓扑和资产发现",
                "category": "post_exploitation",
                "difficulty": "medium",
                "tools": ["nmap", "bloodhound", "ldapsearch"],
                "prerequisites": ["post.lateral_movement"],
                "output": "内网拓扑图、域结构、共享资源、用户权限",
                "success_rate": 0.85
            },
            "post.defense_evasion": {
                "name": "防御规避",
                "description": "绕过安全防御和检测机制",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["cobaltstrike", "empire", "自定义模块"],
                "prerequisites": ["post.cover_tracks"],
                "output": "AV绕过、EDR规避、网络检测绕过、行为隐藏",
                "success_rate": 0.60
            },
            "post.command_control": {
                "name": "命令与控制",
                "description": "建立C2通道和远程控制",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["cobaltstrike", "metasploit", "empire"],
                "prerequisites": ["post.persistence_control"],
                "output": "C2服务器、反向连接、加密通信、远程控制",
                "success_rate": 0.75
            },
            "post.forensic_analysis": {
                "name": "取证分析",
                "description": "系统取证和痕迹分析",
                "category": "post_exploitation",
                "difficulty": "expert",
                "tools": ["volatility", "autopsy", "ftkimager"],
                "prerequisites": ["post.data_exfiltration"],
                "output": "内存分析、磁盘镜像、时间线分析、证据收集",
                "success_rate": 0.70
            },
            "post.report_generation": {
                "name": "报告生成",
                "description": "生成渗透测试报告",
                "category": "post_exploitation",
                "difficulty": "medium",
                "tools": ["自定义模板", "markdown", "latex"],
                "prerequisites": ["post.cover_tracks"],
                "output": "技术报告、风险分析、修复建议、演示材料",
                "success_rate": 0.90
            }
        }
    
    def get_skill(self, skill_id: str) -> Dict[str, Any]:
        """获取指定技能"""
        return self.skills.get(skill_id, {})
    
    def get_skills_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别获取技能"""
        return [skill for skill_id, skill in self.skills.items() 
                if skill.get("category") == category]
    
    def get_recommended_skills(self, scan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据扫描结果推荐技能
        
        说明：
        - 这里根据扫描结果自动推荐相关的渗透技巧
        - 符合会议纪要要求的"将各类渗透技巧封装成技能，供AI调用"
        """
        recommended = []
        
        # 基础侦察技能
        if scan_result.get("nmap"):
            recommended.append(self.get_skill("recon.nmap"))
        
        if scan_result.get("whatweb"):
            recommended.append(self.get_skill("recon.whatweb"))
        
        # 漏洞扫描技能
        nuclei = scan_result.get("nuclei")
        if nuclei and isinstance(nuclei, dict) and nuclei.get("vulnerabilities"):
            recommended.append(self.get_skill("scan.nuclei"))
            
            # 如果发现特定漏洞，推荐对应的渗透技巧
            vulns = nuclei.get("vulnerabilities", [])
            for vuln in vulns:
                if isinstance(vuln, dict):
                    vuln_name = vuln.get("name", "").lower()
                    if "log4j" in vuln_name or "log4shell" in vuln_name:
                        recommended.append(self.get_skill("exploit.cve_2021_44228"))
                    elif "struts" in vuln_name:
                        recommended.append(self.get_skill("exploit.cve_2017_5638"))
        
        # SQL注入相关
        if scan_result.get("sqlmap"):
            recommended.append(self.get_skill("scan.sqlmap"))
            recommended.append(self.get_skill("exploit.ethical_bypass"))
        
        # XSS相关
        if scan_result.get("xsstrike"):
            recommended.append(self.get_skill("scan.xss"))
        
        # WAF检测
        if scan_result.get("wafw00f"):
            recommended.append(self.get_skill("exploit.waf_bypass"))
        
        # 风险评估
        metrics_summary = scan_result.get("metrics_summary") or {}
        vulnerability_counts = metrics_summary.get("vulnerability_counts") or {}
        total_vulns = int(vulnerability_counts.get("total") or 0)
        if total_vulns > 0:
            recommended.append(self.get_skill("analyze.risk_assessment"))
            recommended.append(self.get_skill("analyze.attack_chain"))
        
        # 去重
        seen = set()
        unique_recommended = []
        for skill in recommended:
            if skill and skill.get("name"):
                skill_name = skill["name"]
                if skill_name not in seen:
                    seen.add(skill_name)
                    unique_recommended.append(skill)
        
        return unique_recommended
    
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """获取所有技能"""
        return list(self.skills.values())
    
    def get_skill_count(self) -> int:
        """获取技能总数"""
        return len(self.skills)
    
    def get_skill_statistics(self) -> Dict[str, Any]:
        """获取技能统计信息"""
        stats = {
            "total_skills": len(self.skills),
            "by_category": {},
            "by_difficulty": {}
        }
        
        for skill in self.skills.values():
            category = skill.get("category", "unknown")
            difficulty = skill.get("difficulty", "unknown")
            
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["by_difficulty"][difficulty] = stats["by_difficulty"].get(difficulty, 0) + 1
        
        return stats


# 向后兼容的函数
def recommend_skills(scan_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从 scan_result 推导"可编排的技能建议"（兼容旧版本）
    """
    library = SkillLibrary()
    return library.get_recommended_skills(scan_result)

