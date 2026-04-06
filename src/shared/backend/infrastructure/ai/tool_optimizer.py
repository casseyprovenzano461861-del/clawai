# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能工具推荐和参数优化系统
基于目标特性和攻击阶段，智能选择最佳工具并优化参数
"""

import json
import math
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolEffectiveness(Enum):
    """工具效果评级"""
    EXCELLENT = "excellent"  # 90-100% 成功率
    GOOD = "good"          # 70-89% 成功率
    FAIR = "fair"          # 50-69% 成功率
    POOR = "poor"          # 30-49% 成功率
    UNKNOWN = "unknown"    # 未知


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    description: str
    param_type: str  # int, string, bool, list
    default_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: List[str] = field(default_factory=list)
    importance: float = 0.5  # 参数重要性 0.0-1.0


@dataclass
class ToolProfile:
    """工具性能画像"""
    tool_id: str
    tool_name: str
    category: str
    effectiveness: Dict[str, float]  # 对不同场景的效果评分
    average_success_rate: float  # 平均成功率 0.0-1.0
    execution_time: Dict[str, float]  # 不同场景下的执行时间（秒）
    resource_usage: Dict[str, float]  # CPU、内存等资源占用
    reliability: float  # 可靠性评分 0.0-1.0
    stealthiness: float  # 隐蔽性评分 0.0-1.0
    parameters: List[ToolParameter] = field(default_factory=list)


@dataclass
class ToolRecommendation:
    """工具推荐结果"""
    tool_id: str
    tool_name: str
    category: str
    confidence: float  # 推荐置信度 0.0-1.0
    effectiveness_score: float  # 效果评分 0.0-1.0
    estimated_success_rate: float  # 预估成功率
    estimated_time: float  # 预估执行时间（秒）
    parameters: Dict[str, Any]  # 优化后的参数
    alternative_tools: List[str]  # 备选工具
    reasoning: str  # 推荐理由


@dataclass
class AttackContext:
    """攻击上下文"""
    target: str
    target_type: str  # web, api, service, database, network
    open_ports: List[int]
    services: List[str]
    vulnerabilities: List[Dict[str, Any]]
    fingerprint: Dict[str, Any]
    attack_phase: str  # reconnaissance, scanning, exploitation, post_exploitation
    previous_results: Dict[str, Any]  # 之前的攻击结果
    constraints: Dict[str, Any]  # 约束条件（时间、隐蔽性等）


class ToolOptimizer:
    """工具优化器"""
    
    def __init__(self, knowledge_base: Dict = None):
        self.knowledge_base = knowledge_base or self._load_default_knowledge()
        self.tool_profiles = self._load_tool_profiles()
        
        # 参数优化器配置
        self.optimization_weights = {
            "success_rate": 0.40,
            "execution_time": 0.25,
            "stealthiness": 0.20,
            "resource_usage": 0.10,
            "reliability": 0.05
        }
    
    def _load_default_knowledge(self) -> Dict:
        """加载默认知识库"""
        return {
            "tool_capabilities": {
                "nmap": {
                    "best_for": ["port_scanning", "service_detection", "os_detection"],
                    "scenarios": {
                        "network_discovery": 0.95,
                        "port_scan": 0.90,
                        "service_identification": 0.85,
                        "os_detection": 0.75
                    },
                    "parameter_sensitivity": {
                        "ports": 0.8,
                        "scan_type": 0.7,
                        "timing": 0.6,
                        "script": 0.5
                    }
                },
                "masscan": {
                    "best_for": ["fast_port_scanning", "large_network_scan"],
                    "scenarios": {
                        "fast_port_scan": 0.98,
                        "large_network": 0.92,
                        "high_speed_scan": 0.95,
                        "service_detection": 0.40
                    }
                },
                "whatweb": {
                    "best_for": ["web_fingerprinting", "technology_detection"],
                    "scenarios": {
                        "web_fingerprint": 0.90,
                        "cms_detection": 0.85,
                        "technology_stack": 0.80,
                        "version_detection": 0.75
                    }
                },
                "dirsearch": {
                    "best_for": ["directory_bruteforce", "file_discovery"],
                    "scenarios": {
                        "directory_enumeration": 0.85,
                        "sensitive_file": 0.70,
                        "backup_file": 0.65,
                        "config_file": 0.60
                    }
                },
                "nikto": {
                    "best_for": ["web_vulnerability_scan", "configuration_check"],
                    "scenarios": {
                        "web_vuln_scan": 0.80,
                        "misconfiguration": 0.75,
                        "security_headers": 0.70,
                        "file_disclosure": 0.65
                    }
                },
                "nuclei": {
                    "best_for": ["vulnerability_scanning", "cve_detection"],
                    "scenarios": {
                        "cve_detection": 0.85,
                        "vulnerability_scan": 0.80,
                        "configuration_audit": 0.75,
                        "exposure_detection": 0.70
                    }
                },
                "sqlmap": {
                    "best_for": ["sql_injection", "database_exploitation"],
                    "scenarios": {
                        "sql_injection": 0.90,
                        "database_fingerprint": 0.80,
                        "data_exfiltration": 0.75,
                        "os_shell": 0.65
                    }
                },
                "wpscan": {
                    "best_for": ["wordpress_scan", "cms_vulnerability"],
                    "scenarios": {
                        "wordpress_scan": 0.88,
                        "plugin_vuln": 0.82,
                        "theme_vuln": 0.78,
                        "user_enumeration": 0.72
                    }
                },
                "hydra": {
                    "best_for": ["password_bruteforce", "login_attacks"],
                    "scenarios": {
                        "ssh_bruteforce": 0.70,
                        "ftp_bruteforce": 0.75,
                        "http_login": 0.65,
                        "rdp_bruteforce": 0.60
                    }
                }
            },
            "service_tool_mapping": {
                "http": ["nuclei", "nikto", "dirsearch", "sqlmap", "whatweb"],
                "https": ["nuclei", "nikto", "dirsearch", "sqlmap", "whatweb"],
                "ssh": ["hydra", "medusa", "nmap"],
                "ftp": ["hydra", "medusa", "nmap"],
                "smb": ["crackmapexec", "enum4linux", "nmap"],
                "mysql": ["sqlmap", "hydra", "nmap"],
                "rdp": ["hydra", "crackmapexec", "nmap"],
                "redis": ["redis_exploit", "nmap"],
                "vnc": ["hydra", "vnc_bruteforce"]
            },
            "vulnerability_tool_mapping": {
                "sqli": ["sqlmap", "commix"],
                "xss": ["nuclei", "xsstrike"],
                "rce": ["nuclei", "metasploit"],
                "lfi": ["nuclei", "lfi_scanner"],
                "weak_password": ["hydra", "medusa", "crackmapexec"],
                "misconfiguration": ["nikto", "nuclei"],
                "cve": ["nuclei", "searchsploit"]
            },
            "parameter_optimization_rules": {
                "nmap": {
                    "ports": {
                        "web_target": "80,443,8080,8443",
                        "database_target": "3306,5432,1433,27017",
                        "full_scan": "1-65535",
                        "common_ports": "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017"
                    },
                    "timing": {
                        "stealth": "T2",
                        "balanced": "T3",
                        "aggressive": "T4",
                        "insane": "T5"
                    },
                    "scripts": {
                        "default": [],
                        "vuln_scan": ["vuln"],
                        "service_detection": ["banner"],
                        "os_detection": ["os"]
                    }
                },
                "dirsearch": {
                    "wordlists": {
                        "quick": "common.txt",
                        "standard": "directory-list-2.3-medium.txt",
                        "deep": "directory-list-2.3-big.txt"
                    },
                    "extensions": {
                        "php": "php,php3,php4,php5,phtml",
                        "asp": "asp,aspx",
                        "jsp": "jsp,jspx",
                        "generic": "php,asp,aspx,jsp,html,htm,txt"
                    }
                },
                "hydra": {
                    "username_lists": {
                        "common": "common_users.txt",
                        "extended": "userlist.txt"
                    },
                    "password_lists": {
                        "rockyou": "rockyou.txt",
                        "common": "common_passwords.txt",
                        "brute": "password.lst"
                    },
                    "rate_limits": {
                        "stealth": 2,
                        "normal": 5,
                        "aggressive": 10
                    }
                }
            }
        }
    
    def _load_tool_profiles(self) -> Dict[str, ToolProfile]:
        """加载工具性能画像"""
        profiles = {}
        
        # Nmap工具画像
        nmap_params = [
            ToolParameter(
                name="ports",
                description="扫描端口范围",
                param_type="string",
                default_value="21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017",
                importance=0.9
            ),
            ToolParameter(
                name="scan_type",
                description="扫描类型",
                param_type="string",
                default_value="-sT",
                options=["-sS", "-sT", "-sU", "-sN", "-sF", "-sX", "-sA", "-sW"],
                importance=0.8
            ),
            ToolParameter(
                name="timing",
                description="扫描速度",
                param_type="string",
                default_value="T3",
                options=["T0", "T1", "T2", "T3", "T4", "T5"],
                importance=0.7
            ),
            ToolParameter(
                name="script",
                description="NSE脚本",
                param_type="string",
                default_value="",
                importance=0.5
            )
        ]
        
        profiles["nmap"] = ToolProfile(
            tool_id="nmap",
            tool_name="Nmap",
            category="network_scan",
            effectiveness={
                "port_scanning": 0.95,
                "service_detection": 0.85,
                "os_detection": 0.75,
                "vulnerability_scan": 0.60
            },
            average_success_rate=0.88,
            execution_time={
                "quick_scan": 30,
                "standard_scan": 120,
                "comprehensive_scan": 600
            },
            resource_usage={"cpu": 0.7, "memory": 0.5},
            reliability=0.95,
            stealthiness=0.6,
            parameters=nmap_params
        )
        
        # WhatWeb工具画像
        whatweb_params = [
            ToolParameter(
                name="aggression",
                description="攻击级别",
                param_type="int",
                default_value=3,
                min_value=1,
                max_value=4,
                importance=0.8
            ),
            ToolParameter(
                name="timeout",
                description="超时时间（秒）",
                param_type="int",
                default_value=30,
                min_value=5,
                max_value=300,
                importance=0.6
            )
        ]
        
        profiles["whatweb"] = ToolProfile(
            tool_id="whatweb",
            tool_name="WhatWeb",
            category="fingerprint",
            effectiveness={
                "web_fingerprinting": 0.90,
                "cms_detection": 0.85,
                "technology_stack": 0.80,
                "version_detection": 0.75
            },
            average_success_rate=0.85,
            execution_time={
                "quick": 10,
                "standard": 30,
                "deep": 120
            },
            resource_usage={"cpu": 0.3, "memory": 0.2},
            reliability=0.90,
            stealthiness=0.8,
            parameters=whatweb_params
        )
        
        # Dirsearch工具画像
        dirsearch_params = [
            ToolParameter(
                name="wordlist",
                description="字典文件",
                param_type="string",
                default_value="common.txt",
                options=["common.txt", "directory-list-2.3-medium.txt", "directory-list-2.3-big.txt"],
                importance=0.9
            ),
            ToolParameter(
                name="extensions",
                description="扩展名",
                param_type="string",
                default_value="php,asp,aspx,jsp,html,htm,txt",
                importance=0.7
            ),
            ToolParameter(
                name="recursive",
                description="递归扫描",
                param_type="bool",
                default_value=True,
                importance=0.6
            ),
            ToolParameter(
                name="threads",
                description="线程数",
                param_type="int",
                default_value=10,
                min_value=1,
                max_value=50,
                importance=0.5
            )
        ]
        
        profiles["dirsearch"] = ToolProfile(
            tool_id="dirsearch",
            tool_name="Dirsearch",
            category="dir_brute",
            effectiveness={
                "directory_enumeration": 0.85,
                "sensitive_file": 0.70,
                "backup_file": 0.65,
                "config_file": 0.60
            },
            average_success_rate=0.72,
            execution_time={
                "quick": 60,
                "standard": 300,
                "comprehensive": 1800
            },
            resource_usage={"cpu": 0.5, "memory": 0.3},
            reliability=0.85,
            stealthiness=0.4,
            parameters=dirsearch_params
        )
        
        # SQLMap工具画像
        sqlmap_params = [
            ToolParameter(
                name="level",
                description="测试等级",
                param_type="int",
                default_value=1,
                min_value=1,
                max_value=5,
                importance=0.8
            ),
            ToolParameter(
                name="risk",
                description="风险等级",
                param_type="int",
                default_value=1,
                min_value=1,
                max_value=3,
                importance=0.7
            ),
            ToolParameter(
                name="techniques",
                description="注入技术",
                param_type="string",
                default_value="BEUSTQ",
                importance=0.6
            )
        ]
        
        profiles["sqlmap"] = ToolProfile(
            tool_id="sqlmap",
            tool_name="SQLMap",
            category="exploit",
            effectiveness={
                "sql_injection": 0.90,
                "database_fingerprint": 0.80,
                "data_exfiltration": 0.75,
                "os_shell": 0.65
            },
            average_success_rate=0.82,
            execution_time={
                "quick": 60,
                "standard": 300,
                "comprehensive": 1200
            },
            resource_usage={"cpu": 0.6, "memory": 0.4},
            reliability=0.88,
            stealthiness=0.3,
            parameters=sqlmap_params
        )
        
        return profiles
    
    def analyze_attack_context(self, context: AttackContext) -> Dict[str, Any]:
        """分析攻击上下文"""
        analysis = {
            "target_type": context.target_type,
            "open_ports_count": len(context.open_ports),
            "services_count": len(context.services),
            "vulnerabilities_count": len(context.vulnerabilities),
            "attack_phase": context.attack_phase,
            "primary_service": None,
            "attack_surface": [],
            "tool_requirements": [],
            "constraints": context.constraints
        }
        
        # 确定主要服务
        if context.services:
            # 根据端口数量和服务重要性确定主要服务
            port_service_map = {}
            for port in context.open_ports:
                service = self._map_port_to_service(port)
                if service:
                    port_service_map[port] = service
            
            # 统计服务出现次数
            service_counts = {}
            for service in port_service_map.values():
                service_counts[service] = service_counts.get(service, 0) + 1
            
            if service_counts:
                analysis["primary_service"] = max(service_counts.items(), key=lambda x: x[1])[0]
        
        # 分析攻击面
        attack_surface = []
        
        # 基于端口的攻击面
        for port in context.open_ports:
            port_analysis = self._analyze_port_attack_surface(port)
            if port_analysis:
                attack_surface.append(port_analysis)
        
        # 基于漏洞的攻击面
        for vuln in context.vulnerabilities:
            vuln_analysis = self._analyze_vulnerability_attack_surface(vuln)
            if vuln_analysis:
                attack_surface.append(vuln_analysis)
        
        # 基于指纹的攻击面
        if context.fingerprint:
            fingerprint_analysis = self._analyze_fingerprint_attack_surface(context.fingerprint)
            attack_surface.extend(fingerprint_analysis)
        
        analysis["attack_surface"] = attack_surface
        
        # 确定工具需求
        tool_requirements = []
        
        # 根据攻击阶段确定工具需求
        if context.attack_phase == "reconnaissance":
            tool_requirements.extend(["nmap", "whatweb", "subfinder"])
        elif context.attack_phase == "scanning":
            tool_requirements.extend(["dirsearch", "nikto", "nuclei"])
        elif context.attack_phase == "exploitation":
            # 基于漏洞类型确定工具
            for vuln in context.vulnerabilities:
                vuln_type = vuln.get("type", "").lower()
                if "sql" in vuln_type or "injection" in vuln_type:
                    tool_requirements.append("sqlmap")
                elif "xss" in vuln_type:
                    tool_requirements.append("xsstrike")
                elif "rce" in vuln_type or "command" in vuln_type:
                    tool_requirements.append("commix")
        
        analysis["tool_requirements"] = list(set(tool_requirements))
        
        return analysis
    
    def _map_port_to_service(self, port: int) -> Optional[str]:
        """映射端口到服务"""
        port_service_map = {
            21: "ftp",
            22: "ssh",
            23: "telnet",
            25: "smtp",
            53: "dns",
            80: "http",
            110: "pop3",
            111: "rpcbind",
            135: "msrpc",
            139: "netbios",
            143: "imap",
            443: "https",
            445: "smb",
            993: "imaps",
            995: "pop3s",
            1433: "mssql",
            1521: "oracle",
            3306: "mysql",
            3389: "rdp",
            5432: "postgresql",
            5900: "vnc",
            6379: "redis",
            8080: "http",
            8443: "https",
            27017: "mongodb"
        }
        
        return port_service_map.get(port)
    
    def _analyze_port_attack_surface(self, port: int) -> Dict[str, Any]:
        """分析端口攻击面"""
        service = self._map_port_to_service(port)
        if not service:
            return None
        
        attack_vectors = {
            "ftp": ["weak_password", "anonymous_login", "directory_traversal"],
            "ssh": ["weak_password", "ssh_key_leak", "version_vulnerability"],
            "http": ["web_vulnerabilities", "directory_traversal", "misconfiguration"],
            "https": ["ssl_vulnerabilities", "web_vulnerabilities", "misconfiguration"],
            "smb": ["eternalblue", "smb_relay", "weak_password"],
            "mysql": ["weak_password", "sql_injection", "misconfiguration"],
            "rdp": ["bluekeep", "weak_password", "credential_leak"],
            "redis": ["unauthorized_access", "rce", "data_leak"]
        }
        
        return {
            "port": port,
            "service": service,
            "attack_vectors": attack_vectors.get(service, ["unknown"]),
            "risk_level": self._assess_port_risk(port)
        }
    
    def _assess_port_risk(self, port: int) -> str:
        """评估端口风险等级"""
        high_risk_ports = [22, 23, 25, 445, 3389, 5900]
        medium_risk_ports = [21, 80, 110, 143, 443, 1433, 3306, 5432, 6379, 27017]
        
        if port in high_risk_ports:
            return "high"
        elif port in medium_risk_ports:
            return "medium"
        else:
            return "low"
    
    def _analyze_vulnerability_attack_surface(self, vulnerability: Dict[str, Any]) -> Dict[str, Any]:
        """分析漏洞攻击面"""
        vuln_name = vulnerability.get("name", "").lower()
        severity = vulnerability.get("severity", "unknown").lower()
        
        # 根据漏洞名称推断攻击向量
        attack_vectors = []
        if any(keyword in vuln_name for keyword in ["sql", "injection"]):
            attack_vectors.append("sql_injection")
        if any(keyword in vuln_name for keyword in ["xss", "cross"]):
            attack_vectors.append("xss")
        if any(keyword in vuln_name for keyword in ["rce", "remote code", "command"]):
            attack_vectors.append("rce")
        if any(keyword in vuln_name for keyword in ["lfi", "file inclusion"]):
            attack_vectors.append("lfi")
        if any(keyword in vuln_name for keyword in ["weak", "password"]):
            attack_vectors.append("weak_password")
        
        if not attack_vectors:
            attack_vectors = ["unknown"]
        
        return {
            "vulnerability": vuln_name,
            "severity": severity,
            "attack_vectors": attack_vectors,
            "estimated_impact": self._estimate_vuln_impact(severity)
        }
    
    def _estimate_vuln_impact(self, severity: str) -> str:
        """评估漏洞影响"""
        impact_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info"
        }
        
        return impact_map.get(severity, "unknown")
    
    def _analyze_fingerprint_attack_surface(self, fingerprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析指纹攻击面"""
        attack_surface = []
        
        # CMS相关的攻击面
        cms_list = fingerprint.get("cms", [])
        for cms in cms_list:
            cms_lower = cms.lower()
            if "wordpress" in cms_lower:
                attack_surface.append({
                    "type": "cms",
                    "name": "WordPress",
                    "attack_vectors": ["plugin_vulnerability", "theme_vulnerability", "weak_password"],
                    "tools": ["wpscan", "nuclei"]
                })
            elif "joomla" in cms_lower:
                attack_surface.append({
                    "type": "cms",
                    "name": "Joomla",
                    "attack_vectors": ["component_vulnerability", "template_vulnerability"],
                    "tools": ["joomscan", "nuclei"]
                })
        
        # Web服务器相关的攻击面
        web_server = fingerprint.get("web_server", "")
        if web_server:
            server_lower = web_server.lower()
            if "nginx" in server_lower:
                attack_surface.append({
                    "type": "web_server",
                    "name": "nginx",
                    "attack_vectors": ["configuration_vulnerability", "request_smuggling"],
                    "tools": ["nuclei", "custom_scripts"]
                })
            elif "apache" in server_lower:
                attack_surface.append({
                    "type": "web_server",
                    "name": "Apache",
                    "attack_vectors": ["mod_vulnerability", ".htaccess_misconfiguration"],
                    "tools": ["nikto", "nuclei"]
                })
        
        return attack_surface
    
    def recommend_tools(self, context: AttackContext, top_n: int = 5) -> List[ToolRecommendation]:
        """推荐工具"""
        # 分析攻击上下文
        context_analysis = self.analyze_attack_context(context)
        
        # 候选工具列表
        candidate_tools = self._select_candidate_tools(context_analysis)
        
        # 为每个候选工具评分
        scored_tools = []
        for tool_id in candidate_tools:
            score, reasoning = self._score_tool(tool_id, context_analysis)
            
            # 获取工具信息
            tool_info = self.tool_profiles.get(tool_id)
            if not tool_info:
                continue
            
            # 优化参数
            optimized_params = self._optimize_parameters(tool_id, context_analysis)
            
            # 预估成功率和时间
            estimated_success = self._estimate_success_rate(tool_id, context_analysis)
            estimated_time = self._estimate_execution_time(tool_id, context_analysis)
            
            # 获取备选工具
            alternatives = self._get_alternative_tools(tool_id, context_analysis)
            
            recommendation = ToolRecommendation(
                tool_id=tool_id,
                tool_name=tool_info.tool_name,
                category=tool_info.category,
                confidence=score,
                effectiveness_score=estimated_success,
                estimated_success_rate=estimated_success,
                estimated_time=estimated_time,
                parameters=optimized_params,
                alternative_tools=alternatives,
                reasoning=reasoning
            )
            
            scored_tools.append(recommendation)
        
        # 按置信度排序
        scored_tools.sort(key=lambda x: x.confidence, reverse=True)
        
        return scored_tools[:top_n]
    
    def _select_candidate_tools(self, context_analysis: Dict[str, Any]) -> List[str]:
        """选择候选工具"""
        candidate_tools = []
        
        # 基于攻击阶段
        attack_phase = context_analysis["attack_phase"]
        if attack_phase == "reconnaissance":
            candidate_tools.extend(["nmap", "masscan", "whatweb", "theharvester"])
        elif attack_phase == "scanning":
            candidate_tools.extend(["dirsearch", "nikto", "nuclei", "wpscan", "joomscan"])
        elif attack_phase == "exploitation":
            candidate_tools.extend(["sqlmap", "hydra", "metasploit", "commix", "xsstrike"])
        
        # 基于服务
        primary_service = context_analysis["primary_service"]
        if primary_service:
            service_tools = self.knowledge_base["service_tool_mapping"].get(primary_service, [])
            candidate_tools.extend(service_tools)
        
        # 基于攻击面
        for attack_surface in context_analysis["attack_surface"]:
            if "tools" in attack_surface:
                candidate_tools.extend(attack_surface["tools"])
        
        # 去重并过滤
        candidate_tools = list(set(candidate_tools))
        
        # 过滤掉不可用的工具（在实际部署中会检查工具是否存在）
        available_tools = self._get_available_tools()
        candidate_tools = [t for t in candidate_tools if t in available_tools]
        
        return candidate_tools
    
    def _get_available_tools(self) -> List[str]:
        """获取可用工具列表（简化版本，实际需要检查工具是否存在）"""
        # 这里返回所有预定义的工具，实际部署中应该检查工具是否安装在系统中
        return list(self.tool_profiles.keys())
    
    def _score_tool(self, tool_id: str, context_analysis: Dict[str, Any]) -> Tuple[float, str]:
        """为工具评分"""
        tool_info = self.tool_profiles.get(tool_id)
        if not tool_info:
            return 0.0, "未知工具"
        
        score = 0.0
        reasoning_parts = []
        
        # 1. 基于攻击阶段的评分
        attack_phase = context_analysis["attack_phase"]
        phase_scores = {
            "reconnaissance": {"nmap": 0.9, "whatweb": 0.8, "masscan": 0.7},
            "scanning": {"dirsearch": 0.9, "nikto": 0.8, "nuclei": 0.85},
            "exploitation": {"sqlmap": 0.9, "hydra": 0.7, "metasploit": 0.8}
        }
        
        phase_score = phase_scores.get(attack_phase, {}).get(tool_id, 0.5)
        score += phase_score * 0.3
        if phase_score > 0.7:
            reasoning_parts.append(f"适合{attack_phase}阶段")
        
        # 2. 基于服务的评分
        primary_service = context_analysis["primary_service"]
        if primary_service:
            service_tools = self.knowledge_base["service_tool_mapping"].get(primary_service, [])
            if tool_id in service_tools:
                score += 0.25
                reasoning_parts.append(f"针对{primary_service}服务优化")
        
        # 3. 基于攻击面的评分
        for attack_surface in context_analysis["attack_surface"]:
            if "tools" in attack_surface and tool_id in attack_surface["tools"]:
                score += 0.2
                reasoning_parts.append(f"匹配攻击面: {attack_surface.get('name', 'unknown')}")
                break
        
        # 4. 基于工具性能的评分
        performance_score = tool_info.average_success_rate * 0.25
        score += performance_score
        
        # 考虑约束条件
        constraints = context_analysis["constraints"]
        if "stealth" in constraints and constraints["stealth"]:
            stealth_factor = tool_info.stealthiness
            score *= (0.5 + 0.5 * stealth_factor)
            reasoning_parts.append(f"隐蔽性: {stealth_factor:.2f}")
        
        if "time" in constraints:
            time_limit = constraints["time"]
            avg_time = sum(tool_info.execution_time.values()) / len(tool_info.execution_time)
            if avg_time <= time_limit:
                score += 0.1
                reasoning_parts.append(f"符合时间约束")
            else:
                score *= 0.8
                reasoning_parts.append(f"时间可能超过限制")
        
        # 确保分数在0-1之间
        score = max(0.0, min(1.0, score))
        
        reasoning = "；".join(reasoning_parts) if reasoning_parts else "通用推荐"
        
        return score, reasoning
    
    def _optimize_parameters(self, tool_id: str, context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化工具参数"""
        optimization_rules = self.knowledge_base["parameter_optimization_rules"]
        tool_rules = optimization_rules.get(tool_id, {})
        
        optimized_params = {}
        
        if tool_id == "nmap":
            # 根据目标类型优化nmap参数
            target_type = context_analysis["target_type"]
            open_ports = context_analysis["open_ports_count"]
            
            # 端口参数
            ports_rules = tool_rules.get("ports", {})
            if target_type == "web":
                optimized_params["ports"] = ports_rules.get("web_target", "80,443,8080,8443")
            elif target_type == "database":
                optimized_params["ports"] = ports_rules.get("database_target", "3306,5432,1433,27017")
            elif open_ports > 10:
                optimized_params["ports"] = ports_rules.get("common_ports", "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017")
            else:
                optimized_params["ports"] = ports_rules.get("full_scan", "1-65535")
            
            # 定时参数
            constraints = context_analysis["constraints"]
            if "stealth" in constraints and constraints["stealth"]:
                optimized_params["timing"] = tool_rules.get("timing", {}).get("stealth", "T2")
            else:
                optimized_params["timing"] = tool_rules.get("timing", {}).get("balanced", "T3")
            
            # 脚本参数
            if "vulnerabilities_count" in context_analysis and context_analysis["vulnerabilities_count"] > 0:
                optimized_params["script"] = ",".join(tool_rules.get("scripts", {}).get("vuln_scan", ["vuln"]))
        
        elif tool_id == "dirsearch":
            # 根据指纹优化dirsearch参数
            fingerprint_present = any("cms" in str(aspect) for aspect in context_analysis.get("attack_surface", []))
            
            wordlists = tool_rules.get("wordlists", {})
            if fingerprint_present:
                optimized_params["wordlist"] = wordlists.get("standard", "directory-list-2.3-medium.txt")
            else:
                optimized_params["wordlist"] = wordlists.get("quick", "common.txt")
            
            # 扩展名参数
            extensions = tool_rules.get("extensions", {})
            optimized_params["extensions"] = extensions.get("generic", "php,asp,aspx,jsp,html,htm,txt")
            
            # 线程数
            optimized_params["threads"] = 10
        
        elif tool_id == "hydra":
            # 优化hydra参数
            constraints = context_analysis["constraints"]
            
            rate_limits = tool_rules.get("rate_limits", {})
            if "stealth" in constraints and constraints["stealth"]:
                optimized_params["rate_limit"] = rate_limits.get("stealth", 2)
            else:
                optimized_params["rate_limit"] = rate_limits.get("normal", 5)
            
            # 密码字典
            password_lists = tool_rules.get("password_lists", {})
            optimized_params["password_list"] = password_lists.get("common", "common_passwords.txt")
        
        # 为其他工具提供默认参数
        tool_profile = self.tool_profiles.get(tool_id)
        if tool_profile and not optimized_params:
            for param in tool_profile.parameters:
                optimized_params[param.name] = param.default_value
        
        return optimized_params
    
    def _estimate_success_rate(self, tool_id: str, context_analysis: Dict[str, Any]) -> float:
        """预估成功率"""
        tool_info = self.tool_profiles.get(tool_id)
        if not tool_info:
            return 0.5
        
        base_success = tool_info.average_success_rate
        
        # 根据上下文调整
        adjustment = 1.0
        
        # 如果工具有针对当前服务的优化，提高成功率
        primary_service = context_analysis["primary_service"]
        if primary_service:
            service_tools = self.knowledge_base["service_tool_mapping"].get(primary_service, [])
            if tool_id in service_tools:
                adjustment *= 1.1
        
        # 如果有相关漏洞，提高成功率
        if context_analysis["vulnerabilities_count"] > 0:
            adjustment *= 1.05
        
        # 考虑约束条件
        constraints = context_analysis["constraints"]
        if "stealth" in constraints and constraints["stealth"]:
            # 隐蔽性要求可能降低成功率
            stealth_factor = tool_info.stealthiness
            adjustment *= (0.7 + 0.3 * stealth_factor)
        
        estimated_success = base_success * adjustment
        return max(0.1, min(0.95, estimated_success))
    
    def _estimate_execution_time(self, tool_id: str, context_analysis: Dict[str, Any]) -> float:
        """预估执行时间"""
        tool_info = self.tool_profiles.get(tool_id)
        if not tool_info:
            return 300  # 默认5分钟
        
        # 根据目标复杂度调整时间
        complexity_factor = 1.0
        
        open_ports = context_analysis["open_ports_count"]
        if open_ports > 50:
            complexity_factor *= 1.5
        elif open_ports > 20:
            complexity_factor *= 1.2
        
        # 获取基础时间
        execution_times = tool_info.execution_time
        avg_time = sum(execution_times.values()) / len(execution_times)
        
        estimated_time = avg_time * complexity_factor
        
        # 考虑约束条件
        constraints = context_analysis["constraints"]
        if "time" in constraints:
            time_limit = constraints["time"]
            if estimated_time > time_limit:
                # 如果预估时间超过限制，可能需要调整参数
                estimated_time = min(estimated_time, time_limit * 1.5)
        
        return estimated_time
    
    def _get_alternative_tools(self, primary_tool: str, context_analysis: Dict[str, Any]) -> List[str]:
        """获取备选工具"""
        alternatives = []
        
        # 基于工具类别的备选
        primary_profile = self.tool_profiles.get(primary_tool)
        if primary_profile:
            category = primary_profile.category
            
            # 查找同类别其他工具
            for tool_id, profile in self.tool_profiles.items():
                if tool_id != primary_tool and profile.category == category:
                    alternatives.append(tool_id)
        
        # 基于功能的备选
        tool_capabilities = self.knowledge_base["tool_capabilities"]
        primary_capabilities = tool_capabilities.get(primary_tool, {}).get("best_for", [])
        
        for tool_id, capabilities in tool_capabilities.items():
            if tool_id != primary_tool:
                tool_best_for = capabilities.get("best_for", [])
                # 如果有重叠的功能
                common_capabilities = set(primary_capabilities) & set(tool_best_for)
                if common_capabilities and tool_id not in alternatives:
                    alternatives.append(tool_id)
        
        # 限制备选工具数量
        return alternatives[:3]
    
    def generate_tool_execution_plan(self, context: AttackContext) -> Dict[str, Any]:
        """生成工具执行计划"""
        # 推荐工具
        recommendations = self.recommend_tools(context, top_n=3)
        
        if not recommendations:
            return {"error": "没有找到合适的工具推荐"}
        
        # 创建执行计划
        execution_plan = {
            "target": context.target,
            "attack_phase": context.attack_phase,
            "primary_tool": {
                "tool_id": recommendations[0].tool_id,
                "tool_name": recommendations[0].tool_name,
                "parameters": recommendations[0].parameters,
                "estimated_success_rate": recommendations[0].estimated_success_rate,
                "estimated_time": recommendations[0].estimated_time,
                "confidence": recommendations[0].confidence
            },
            "alternative_tools": [],
            "execution_sequence": [],
            "fallback_strategy": {},
            "monitoring_metrics": []
        }
        
        # 添加备选工具
        for i, rec in enumerate(recommendations[1:], 1):
            execution_plan["alternative_tools"].append({
                "tool_id": rec.tool_id,
                "tool_name": rec.tool_name,
                "parameters": rec.parameters,
                "confidence": rec.confidence
            })
        
        # 生成执行序列
        execution_plan["execution_sequence"] = self._generate_execution_sequence(
            recommendations[0], context
        )
        
        # 生成回退策略
        execution_plan["fallback_strategy"] = self._generate_fallback_strategy(
            recommendations, context
        )
        
        # 监控指标
        execution_plan["monitoring_metrics"] = [
            "success_rate",
            "execution_time",
            "resource_usage",
            "stealthiness_score"
        ]
        
        return execution_plan
    
    def _generate_execution_sequence(self, primary_tool: ToolRecommendation, 
                                   context: AttackContext) -> List[Dict[str, Any]]:
        """生成执行序列"""
        sequence = []
        
        # 前置检查
        sequence.append({
            "step": 1,
            "action": "前置检查",
            "description": f"检查{primary_tool.tool_name}工具是否可用",
            "expected_outcome": "工具可用，参数配置正确",
            "timeout": 30
        })
        
        # 参数验证
        sequence.append({
            "step": 2,
            "action": "参数验证",
            "description": f"验证{primary_tool.tool_name}参数配置",
            "expected_outcome": "参数配置有效，无安全风险",
            "timeout": 10
        })
        
        # 执行工具
        sequence.append({
            "step": 3,
            "action": "工具执行",
            "description": f"执行{primary_tool.tool_name}，参数: {json.dumps(primary_tool.parameters, ensure_ascii=False)[:100]}",
            "expected_outcome": "成功执行，获取扫描/攻击结果",
            "estimated_time": primary_tool.estimated_time,
            "timeout": primary_tool.estimated_time * 1.5
        })
        
        # 结果解析
        sequence.append({
            "step": 4,
            "action": "结果解析",
            "description": "解析工具输出，提取关键信息",
            "expected_outcome": "解析成功，生成结构化报告",
            "timeout": 60
        })
        
        # 后置处理
        sequence.append({
            "step": 5,
            "action": "后置处理",
            "description": "清理临时文件，更新知识库",
            "expected_outcome": "清理完成，知识库更新",
            "timeout": 30
        })
        
        return sequence
    
    def _generate_fallback_strategy(self, recommendations: List[ToolRecommendation],
                                  context: AttackContext) -> Dict[str, Any]:
        """生成回退策略"""
        fallback = {
            "primary_failure": {
                "condition": "主工具执行失败或结果不理想",
                "actions": [
                    "检查日志和错误信息",
                    "验证参数配置",
                    "重试（最多2次）"
                ],
                "next_tool": recommendations[1].tool_name if len(recommendations) > 1 else None
            },
            "timeout": {
                "condition": "执行超时",
                "actions": [
                    "终止当前进程",
                    "清理资源",
                    "切换到更快的工具或简化参数"
                ],
                "next_tool": self._find_faster_alternative(recommendations)
            },
            "low_success": {
                "condition": "成功率低于预期",
                "actions": [
                    "分析失败原因",
                    "调整参数",
                    "尝试不同的攻击向量"
                ],
                "next_phase": self._determine_next_phase(context.attack_phase)
            }
        }
        
        return fallback
    
    def _find_faster_alternative(self, recommendations: List[ToolRecommendation]) -> Optional[str]:
        """查找更快的备选工具"""
        if len(recommendations) < 2:
            return None
        
        # 按预估时间排序
        sorted_tools = sorted(recommendations, key=lambda x: x.estimated_time)
        
        # 返回第二快的工具（最快的可能是主工具）
        for i, tool in enumerate(sorted_tools):
            if i > 0:
                return tool.tool_name
        
        return None
    
    def _determine_next_phase(self, current_phase: str) -> str:
        """确定下一个攻击阶段"""
        phase_sequence = ["reconnaissance", "scanning", "exploitation", "post_exploitation"]
        
        try:
            current_index = phase_sequence.index(current_phase)
            if current_index < len(phase_sequence) - 1:
                return phase_sequence[current_index + 1]
        except ValueError:
            pass
        
        return current_phase


def test_optimizer():
    """测试优化器"""
    context = AttackContext(
        target="example.com",
        target_type="web",
        open_ports=[80, 443, 22, 3306],
        services=["http", "https", "ssh", "mysql"],
        vulnerabilities=[
            {"name": "SQL注入漏洞", "severity": "high", "type": "sqli"},
            {"name": "XSS漏洞", "severity": "medium", "type": "xss"}
        ],
        fingerprint={
            "web_server": "nginx/1.18.0",
            "cms": ["WordPress 5.8"],
            "language": ["PHP 7.4"]
        },
        attack_phase="exploitation",
        previous_results={"port_scan": "completed", "fingerprint": "completed"},
        constraints={"time": 600, "stealth": True}
    )
    
    optimizer = ToolOptimizer()
    
    # 测试工具推荐
    recommendations = optimizer.recommend_tools(context, top_n=3)
    
    print("\n" + "="*60)
    print("工具推荐结果")
    print("="*60)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.tool_name} ({rec.tool_id})")
        print(f"   置信度: {rec.confidence:.3f}")
        print(f"   预估成功率: {rec.estimated_success_rate:.1%}")
        print(f"   预估时间: {rec.estimated_time:.0f}秒")
        print(f"   推荐理由: {rec.reasoning}")
        print(f"   优化参数: {rec.parameters}")
        print(f"   备选工具: {', '.join(rec.alternative_tools[:2])}")
    
    # 测试执行计划生成
    execution_plan = optimizer.generate_tool_execution_plan(context)
    
    print("\n" + "="*60)
    print("执行计划")
    print("="*60)
    
    print(f"\n主工具: {execution_plan['primary_tool']['tool_name']}")
    print(f"攻击阶段: {execution_plan['attack_phase']}")
    
    print("\n执行序列:")
    for step in execution_plan["execution_sequence"]:
        print(f"  {step['step']}. {step['action']}: {step['description']}")
    
    return recommendations, execution_plan


if __name__ == "__main__":
    test_optimizer()