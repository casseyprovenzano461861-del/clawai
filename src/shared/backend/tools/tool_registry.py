# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
工具注册表
管理所有集成的安全工具，满足比赛要求的 ≥30 个工具
"""

from typing import Dict, List, Any, Optional
import importlib
import os

class ToolRegistry:
    """安全工具注册表"""
    
    # 所有支持的工具列表（30+个）
    TOOLS = {
        # ===== 网络扫描类（3个）=====
        "nmap": {
            "name": "Nmap",
            "category": "network_scan",
            "description": "端口扫描与服务识别",
            "module": "nmap",
            "class": "NmapTool"
        },
        "masscan": {
            "name": "Masscan",
            "category": "network_scan",
            "description": "高速端口扫描器",
            "module": "masscan",
            "class": "MasscanTool"
        },
        "rustscan": {
            "name": "RustScan",
            "category": "network_scan",
            "description": "Rust编写的快速端口扫描器",
            "module": "rustscan",
            "class": "RustScanTool"
        },
        
        # ===== Web扫描类（4个）=====
        "nuclei": {
            "name": "Nuclei",
            "category": "vuln_scan",
            "description": "基于模板的漏洞扫描器",
            "module": "nuclei",
            "class": "NucleiTool"
        },
        "nikto": {
            "name": "Nikto",
            "category": "web_scan",
            "description": "Web服务器漏洞扫描器",
            "module": "nikto",
            "class": "NiktoTool"
        },
        "whatweb": {
            "name": "WhatWeb",
            "category": "fingerprint",
            "description": "Web指纹识别工具",
            "module": "whatweb",
            "class": "WhatWebTool"
        },
        "httpx": {
            "name": "HTTPX",
            "category": "http_probe",
            "description": "HTTP探测与存活检测",
            "module": "httpx",
            "class": "HTTPXTool"
        },
        
        # ===== 目录爆破类（4个）=====
        "dirsearch": {
            "name": "Dirsearch",
            "category": "dir_brute",
            "description": "目录和文件爆破工具",
            "module": "dirsearch",
            "class": "DirsearchTool"
        },
        "gobuster": {
            "name": "Gobuster",
            "category": "dir_brute",
            "description": "Go编写的目录爆破工具",
            "module": "gobuster",
            "class": "GobusterTool"
        },
        "ffuf": {
            "name": "FFUF",
            "category": "dir_brute",
            "description": "快速Web模糊测试工具",
            "module": "ffuf",
            "class": "FFUFTool"
        },
        "feroxbuster": {
            "name": "Feroxbuster",
            "category": "dir_brute",
            "description": "Rust编写的递归目录爆破",
            "module": "feroxbuster",
            "class": "FeroxbusterTool"
        },
        
        # ===== 漏洞利用类（4个）=====
        "sqlmap": {
            "name": "SQLMap",
            "category": "exploit",
            "description": "SQL注入自动化利用工具",
            "module": "sqlmap",
            "class": "SQLMapTool"
        },
        "xsstrike": {
            "name": "XSStrike",
            "category": "exploit",
            "description": "XSS漏洞检测与利用",
            "module": "xsstrike",
            "class": "XSStrikeTool"
        },
        "commix": {
            "name": "Commix",
            "category": "exploit",
            "description": "命令注入利用工具",
            "module": "commix",
            "class": "CommixTool"
        },
        "tplmap": {
            "name": "Tplmap",
            "category": "exploit",
            "description": "模板注入利用工具",
            "module": "tplmap",
            "class": "TplmapTool"
        },
        
        # ===== CMS扫描类（4个）=====
        "wpscan": {
            "name": "WPScan",
            "category": "cms_scan",
            "description": "WordPress漏洞扫描器",
            "module": "wpscan",
            "class": "WPScanTool"
        },
        "joomscan": {
            "name": "JoomScan",
            "category": "cms_scan",
            "description": "Joomla漏洞扫描器",
            "module": "joomscan",
            "class": "JoomScanTool"
        },
        "droopescan": {
            "name": "Droopescan",
            "category": "cms_scan",
            "description": "Drupal/WordPress/Joomla扫描器",
            "module": "droopescan",
            "class": "DroopescanTool"
        },
        "cmsmap": {
            "name": "CMSMap",
            "category": "cms_scan",
            "description": "CMS漏洞扫描器",
            "module": "cmsmap",
            "class": "CMSMapTool"
        },
        
        # ===== 子域枚举类（3个）=====
        "subfinder": {
            "name": "Subfinder",
            "category": "subdomain",
            "description": "被动子域名枚举工具",
            "module": "subfinder",
            "class": "SubfinderTool"
        },
        "amass": {
            "name": "Amass",
            "category": "subdomain",
            "description": "深度子域名枚举",
            "module": "amass",
            "class": "AmassTool"
        },
        "sublist3r": {
            "name": "Sublist3r",
            "category": "subdomain",
            "description": "子域名枚举工具",
            "module": "sublist3r",
            "class": "Sublist3rTool"
        },
        
        # ===== 密码破解类（4个）=====
        "hydra": {
            "name": "Hydra",
            "category": "brute_force",
            "description": "网络登录暴力破解",
            "module": "hydra",
            "class": "HydraTool"
        },
        "medusa": {
            "name": "Medusa",
            "category": "brute_force",
            "description": "并行登录暴力破解",
            "module": "medusa",
            "class": "MedusaTool"
        },
        "john": {
            "name": "John the Ripper",
            "category": "password_crack",
            "description": "密码破解工具",
            "module": "john",
            "class": "JohnTool"
        },
        "hashcat": {
            "name": "Hashcat",
            "category": "password_crack",
            "description": "GPU加速密码破解",
            "module": "hashcat",
            "class": "HashcatTool"
        },
        
        # ===== 后渗透类（4个）=====
        "metasploit": {
            "name": "Metasploit",
            "category": "post_exploit",
            "description": "渗透测试框架",
            "module": "metasploit",
            "class": "MetasploitTool"
        },
        "impacket_tool": {
            "name": "Impacket",
            "category": "post_exploit",
            "description": "网络协议工具包",
            "module": "impacket_tool",
            "class": "ImpacketTool"
        },
        "crackmapexec": {
            "name": "CrackMapExec",
            "category": "post_exploit",
            "description": "内网渗透利器",
            "module": "crackmapexec",
            "class": "CrackMapExecTool"
        },
        "evil_winrm": {
            "name": "Evil-WinRM",
            "category": "post_exploit",
            "description": "Windows远程管理利用",
            "module": "evil_winrm",
            "class": "EvilWinRMTool"
        },
        
        # ===== 信息收集类（3个）=====
        "theharvester": {
            "name": "TheHarvester",
            "category": "osint",
            "description": "邮箱和子域名收集",
            "module": "theharvester",
            "class": "TheHarvesterTool"
        },
        "dnsrecon": {
            "name": "DNSRecon",
            "category": "dns",
            "description": "DNS信息收集",
            "module": "dnsrecon",
            "class": "DNSReconTool"
        },
        "whois_tool": {
            "name": "Whois",
            "category": "osint",
            "description": "域名注册信息查询",
            "module": "whois_tool",
            "class": "WhoisTool"
        },
        
        # ===== 其他工具（4个）=====
        "searchsploit": {
            "name": "SearchSploit",
            "category": "exploit_db",
            "description": "Exploit-DB本地搜索",
            "module": "searchsploit",
            "class": "SearchSploitTool"
        },
        "sslscan": {
            "name": "SSLScan",
            "category": "ssl",
            "description": "SSL/TLS配置检测",
            "module": "sslscan",
            "class": "SSLScanTool"
        },
        "testssl": {
            "name": "TestSSL",
            "category": "ssl",
            "description": "SSL/TLS漏洞检测",
            "module": "testssl",
            "class": "TestSSLTool"
        },
        "wafw00f": {
            "name": "Wafw00f",
            "category": "waf",
            "description": "WAF指纹识别",
            "module": "wafw00f",
            "class": "Wafw00fTool"
        },
    }
    
    def __init__(self):
        self.loaded_tools = {}
    
    def get_tool_count(self) -> int:
        """获取工具总数"""
        return len(self.TOOLS)
    
    def get_tools_by_category(self, category: str) -> List[Dict]:
        """按类别获取工具"""
        return [
            {"id": k, **v} 
            for k, v in self.TOOLS.items() 
            if v["category"] == category
        ]
    
    def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        return list(set(t["category"] for t in self.TOOLS.values()))
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict]:
        """获取工具信息"""
        return self.TOOLS.get(tool_id)
    
    def load_tool(self, tool_id: str):
        """动态加载工具"""
        if tool_id in self.loaded_tools:
            return self.loaded_tools[tool_id]
        
        tool_info = self.TOOLS.get(tool_id)
        if not tool_info:
            raise ValueError(f"未知工具: {tool_id}")
        
        try:
            module = importlib.import_module(f"tools.{tool_info['module']}")
            tool_class = getattr(module, tool_info["class"])
            tool_instance = tool_class()
            self.loaded_tools[tool_id] = tool_instance
            return tool_instance
        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"加载工具 {tool_id} 失败: {e}")
    
    def list_all_tools(self) -> List[Dict]:
        """列出所有工具"""
        result = []
        for tool_id, info in self.TOOLS.items():
            result.append({
                "id": tool_id,
                "name": info["name"],
                "category": info["category"],
                "description": info["description"]
            })
        return result
    
    def print_tool_summary(self):
        """打印工具摘要"""
        print(f"\n{'='*60}")
        print(f"ClawAI 安全工具集成 - 共 {self.get_tool_count()} 个工具")
        print(f"{'='*60}")
        
        categories = {}
        for tool_id, info in self.TOOLS.items():
            cat = info["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(info["name"])
        
        for cat, tools in sorted(categories.items()):
            print(f"\n[{cat}] ({len(tools)}个)")
            for tool in tools:
                print(f"  - {tool}")


def main():
    registry = ToolRegistry()
    registry.print_tool_summary()
    print(f"\n✅ 工具总数: {registry.get_tool_count()} (满足比赛要求 ≥30)")


if __name__ == "__main__":
    main()