# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
WhatWebSkill - Web指纹识别技能

功能：
1. Web技术栈识别
2. CMS检测
3. 服务器信息收集
"""

import random
import time
from typing import Dict, List, Any
from .base_skill import BaseSkill


class WhatWebSkill(BaseSkill):
    """WhatWeb指纹识别技能"""
    
    def get_name(self) -> str:
        return "WhatWebSkill"
    
    def get_description(self) -> str:
        return "使用WhatWeb进行Web应用技术栈指纹识别"
    
    def get_category(self) -> str:
        return "reconnaissance"
    
    def get_difficulty(self) -> str:
        return "easy"
    
    def get_required_tools(self) -> List[str]:
        return ["whatweb"]
    
    def get_prerequisites(self) -> List[str]:
        return ["NmapScanSkill"]  # 需要先进行端口扫描
    
    def get_success_rate(self) -> float:
        """获取技能成功率"""
        return 0.90  # WhatWeb识别成功率较高
    
    def get_estimated_time(self) -> str:
        """获取预估执行时间"""
        return "2-5分钟"
    
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """
        判断是否能处理当前上下文
        
        条件：
        1. 有目标地址
        2. 目标有Web服务（80, 443, 8080, 8443等端口开放）
        3. 尚未进行Web指纹识别或需要更新
        """
        if not context:
            return False
        
        target = context.get("target", "")
        if not target:
            return False
        
        # 检查是否已有Web服务信息
        scan_results = context.get("scan_results", {})
        current_state = context.get("current_state", {})
        
        # 检查是否有Web端口开放
        has_web_ports = False
        
        # 从扫描结果检查
        if "nmap" in scan_results:
            nmap_data = scan_results["nmap"]
            if isinstance(nmap_data, dict) and "ports" in nmap_data:
                for port_info in nmap_data["ports"]:
                    if isinstance(port_info, dict):
                        service = port_info.get("service", "").lower()
                        port = port_info.get("port", 0)
                        if service in ["http", "https", "www", "web"] or port in [80, 443, 8080, 8443]:
                            has_web_ports = True
                            break
        
        # 从当前状态检查
        if "open_ports" in current_state:
            for port_info in current_state["open_ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "").lower()
                    port = port_info.get("port", 0)
                    if service in ["http", "https", "www", "web"] or port in [80, 443, 8080, 8443]:
                        has_web_ports = True
                        break
        
        if not has_web_ports:
            return False
        
        # 检查是否已有whatweb扫描结果
        if "whatweb" in scan_results:
            whatweb_data = scan_results["whatweb"]
            # 如果已有详细的指纹信息，可能不需要再次扫描
            if isinstance(whatweb_data, dict) and "fingerprint" in whatweb_data:
                fingerprint = whatweb_data["fingerprint"]
                if fingerprint and len(fingerprint) >= 2:  # 如果有2个以上指纹信息
                    # 检查是否需要更新（例如，之前扫描不完整）
                    web_techs = current_state.get("web_technologies", {})
                    if web_techs and len(web_techs) >= 3:
                        return False
        
        # 检查当前状态
        if "web_technologies" in current_state:
            web_techs = current_state["web_technologies"]
            if web_techs and len(web_techs) >= 4:  # 如果已有4个以上技术栈信息
                return False
        
        return True
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行WhatWeb指纹识别
        
        模拟执行，实际环境中应调用真实whatweb命令
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
            scan_result = self._generate_whatweb_result(target)
            
            return {
                "success": True,
                "skill_name": self.name,
                "target": target,
                "web_technologies": scan_result["technologies"],
                "fingerprint": scan_result["fingerprint"],
                "scan_time": scan_result["scan_time"],
                "details": {
                    "command_used": f"whatweb -a 3 {target}",
                    "aggression_level": "3 (中等攻击性)",
                    "plugins_used": "所有可用插件",
                    "http_headers": scan_result.get("headers", {})
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"WhatWeb扫描失败: {str(e)}",
                "skill_name": self.name,
                "target": target
            }
    
    def _simulate_scanning(self, target: str) -> None:
        """模拟扫描过程"""
        # 模拟扫描时间
        scan_time = random.uniform(1.0, 3.0)
        time.sleep(min(scan_time, 0.3))  # 实际等待时间缩短
    
    def _generate_whatweb_result(self, target: str) -> Dict[str, Any]:
        """生成模拟的WhatWeb扫描结果"""
        
        # 常见的Web技术栈组合
        tech_stacks = [
            {
                "server": ["nginx/1.18.0"],
                "language": ["PHP/7.4", "JavaScript"],
                "cms": ["WordPress/5.8"],
                "framework": ["Bootstrap/4.6", "jQuery/3.6"],
                "other": ["MySQL", "Redis", "Let's Encrypt"]
            },
            {
                "server": ["Apache/2.4.41"],
                "language": ["Java", "JSP"],
                "cms": ["Joomla/3.10"],
                "framework": ["Spring Boot", "jQuery/2.2"],
                "other": ["Tomcat/9.0", "MySQL"]
            },
            {
                "server": ["IIS/10.0"],
                "language": ["ASP.NET", "C#"],
                "cms": ["Umbraco/8.0"],
                "framework": [".NET Framework 4.8", "jQuery/1.12"],
                "other": ["SQL Server", "Windows Server 2019"]
            },
            {
                "server": ["nginx/1.20.1"],
                "language": ["Python/3.9", "JavaScript"],
                "cms": ["Django/3.2"],
                "framework": ["React/17.0", "Vue.js/3.0"],
                "other": ["PostgreSQL", "Docker", "Cloudflare"]
            }
        ]
        
        # 随机选择一个技术栈
        tech_stack = random.choice(tech_stacks)
        
        # 构建指纹信息
        fingerprint = {
            "web_server": tech_stack["server"][0] if tech_stack["server"] else "Unknown",
            "programming_languages": tech_stack["language"],
            "content_management_systems": tech_stack["cms"],
            "javascript_frameworks": [f for f in tech_stack["framework"] if "jQuery" in f or "React" in f or "Vue" in f],
            "web_frameworks": [f for f in tech_stack["framework"] if "Spring" in f or "Django" in f or ".NET" in f],
            "database_technologies": [t for t in tech_stack["other"] if "SQL" in t or "Postgre" in t or "MySQL" in t],
            "caching_technologies": [t for t in tech_stack["other"] if "Redis" in t],
            "security_technologies": [t for t in tech_stack["other"] if "Cloudflare" in t or "Let's Encrypt" in t],
            "container_technologies": [t for t in tech_stack["other"] if "Docker" in t]
        }
        
        # 清理空列表
        fingerprint = {k: v for k, v in fingerprint.items() if v}
        
        # HTTP头信息
        headers = {
            "Server": fingerprint.get("web_server", "Unknown"),
            "X-Powered-By": tech_stack["language"][0] if tech_stack["language"] else "Unknown",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Content-Security-Policy": "default-src 'self'"
        }
        
        # 根据技术栈添加特定头
        if "WordPress" in str(tech_stack["cms"]):
            headers["X-Pingback"] = f"http://{target}/xmlrpc.php"
            headers["Link"] = f'<http://{target}/wp-json/>; rel="https://api.w.org/"'
        
        return {
            "technologies": tech_stack,
            "fingerprint": fingerprint,
            "headers": headers,
            "scan_time": f"{random.uniform(0.8, 2.5):.1f} seconds"
        }
    
    def _extract_from_existing_scan(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        从现有扫描结果中提取WhatWeb信息
        """
        if "whatweb" not in scan_results:
            return {}
        
        whatweb_data = scan_results["whatweb"]
        if not isinstance(whatweb_data, dict):
            return {}
        
        result = {
            "technologies": {},
            "fingerprint": {},
            "headers": {}
        }
        
        # 提取指纹信息
        if "fingerprint" in whatweb_data:
            fingerprint = whatweb_data["fingerprint"]
            if isinstance(fingerprint, dict):
                result["fingerprint"] = fingerprint
                
                # 构建技术栈信息
                technologies = {}
                
                if fingerprint.get("web_server"):
                    technologies["server"] = [fingerprint["web_server"]]
                
                if fingerprint.get("language"):
                    technologies["language"] = fingerprint["language"][:3]
                
                if fingerprint.get("cms"):
                    technologies["cms"] = fingerprint["cms"][:3]
                
                if fingerprint.get("other"):
                    technologies["other"] = fingerprint["other"][:5]
                
                result["technologies"] = technologies
        
        # 提取HTTP头信息
        if "http_headers" in whatweb_data:
            result["headers"] = whatweb_data["http_headers"]
        
        return result
    
    def _get_web_targets(self, context: Dict[str, Any]) -> List[str]:
        """
        获取Web目标列表
        
        从上下文中的端口信息提取Web服务目标
        """
        targets = []
        base_target = context.get("target", "")
        
        if not base_target:
            return targets
        
        # 检查扫描结果中的端口
        scan_results = context.get("scan_results", {})
        current_state = context.get("current_state", {})
        
        web_ports = []
        
        # 从nmap结果提取
        if "nmap" in scan_results:
            nmap_data = scan_results["nmap"]
            if isinstance(nmap_data, dict) and "ports" in nmap_data:
                for port_info in nmap_data["ports"]:
                    if isinstance(port_info, dict):
                        service = port_info.get("service", "").lower()
                        port = port_info.get("port", 0)
                        if service in ["http", "https", "www", "web"] or port in [80, 443, 8080, 8443]:
                            web_ports.append(port)
        
        # 从当前状态提取
        if "open_ports" in current_state:
            for port_info in current_state["open_ports"]:
                if isinstance(port_info, dict):
                    service = port_info.get("service", "").lower()
                    port = port_info.get("port", 0)
                    if service in ["http", "https", "www", "web"] or port in [80, 443, 8080, 8443]:
                        if port not in web_ports:
                            web_ports.append(port)
        
        # 构建目标列表
        for port in web_ports:
            if port == 80:
                targets.append(f"http://{base_target}")
            elif port == 443:
                targets.append(f"https://{base_target}")
            else:
                targets.append(f"http://{base_target}:{port}")
                targets.append(f"https://{base_target}:{port}")
        
        # 去重
        return list(set(targets))