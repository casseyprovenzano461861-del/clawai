# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
上下文管理器模块
负责分析扫描数据和用户上下文，生成上下文分析结果
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TargetAnalysis:
    """目标分析结果"""
    target_type: str  # Web, Database, Service, Network, Internal
    sub_type: str     # 子类型，如 WordPress, MySQL, SSH等
    confidence: float # 置信度 0.0-1.0


class ContextManager:
    """
    上下文管理器
    分析扫描数据和用户上下文，生成上下文分析结果
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 技术栈识别规则
        self.tech_stack_patterns = {
            "web_servers": {
                "nginx": ["nginx", "nginx/"],
                "apache": ["apache", "httpd"],
                "iis": ["iis", "microsoft-iis"],
                "tomcat": ["tomcat", "apache-tomcat"]
            },
            "programming_languages": {
                "php": ["php", "php/"],
                "python": ["python", "django", "flask"],
                "java": ["java", "jsp", "servlet"],
                "nodejs": ["node.js", "express", "node/"],
                "ruby": ["ruby", "rails", "sinatra"],
                "asp": ["asp.net", "asp", ".net"]
            },
            "frameworks": {
                "wordpress": ["wordpress", "wp-"],
                "joomla": ["joomla"],
                "drupal": ["drupal"],
                "laravel": ["laravel"],
                "spring": ["spring", "spring-boot"],
                "react": ["react", "reactjs"],
                "vue": ["vue.js", "vuejs"],
                "angular": ["angular"]
            },
            "databases": {
                "mysql": ["mysql", "mariadb"],
                "postgresql": ["postgresql", "postgres"],
                "mongodb": ["mongodb"],
                "redis": ["redis"],
                "oracle": ["oracle"],
                "sqlserver": ["sql server", "mssql"]
            }
        }
        
        # 防御措施识别
        self.defense_patterns = {
            "waf": ["waf", "cloudflare", "akamai", "imperva", "f5", "barracuda"],
            "firewall": ["firewall", "iptables", "ufw"],
            "ids_ips": ["snort", "suricata", "security onion", "zeek"],
            "siem": ["splunk", "elasticsearch", "logrhythm", "arcsight"],
            "edr": ["crowdstrike", "carbon black", "sentinelone", "cybereason"]
        }
        
        # 端口-服务映射
        self.port_service_map = {
            # Web服务
            80: {"service": "http", "type": "web"},
            443: {"service": "https", "type": "web"},
            8080: {"service": "http-proxy", "type": "web"},
            8443: {"service": "https-alt", "type": "web"},
            
            # 数据库
            3306: {"service": "mysql", "type": "database"},
            5432: {"service": "postgresql", "type": "database"},
            1433: {"service": "mssql", "type": "database"},
            1521: {"service": "oracle", "type": "database"},
            27017: {"service": "mongodb", "type": "database"},
            6379: {"service": "redis", "type": "database"},
            
            # 文件/打印服务
            21: {"service": "ftp", "type": "service"},
            22: {"service": "ssh", "type": "service"},
            23: {"service": "telnet", "type": "service"},
            25: {"service": "smtp", "type": "service"},
            53: {"service": "dns", "type": "service"},
            110: {"service": "pop3", "type": "service"},
            143: {"service": "imap", "type": "service"},
            445: {"service": "smb", "type": "service"},
            3389: {"service": "rdp", "type": "service"},
            
            # 其他服务
            161: {"service": "snmp", "type": "service"},
            389: {"service": "ldap", "type": "service"},
            636: {"service": "ldaps", "type": "service"},
            873: {"service": "rsync", "type": "service"},
            2049: {"service": "nfs", "type": "service"},
            5900: {"service": "vnc", "type": "service"},
            5985: {"service": "winrm", "type": "service"},
            5986: {"service": "winrm-ssl", "type": "service"}
        }
    
    def analyze(self, scan_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """
        分析上下文
        
        Args:
            scan_data: 扫描结果数据
            user_context: 用户上下文
            
        Returns:
            Dict: 上下文分析结果
        """
        self.logger.info("开始上下文分析...")
        
        # 1. 目标分析
        target_analysis = self._analyze_target(scan_data)
        
        # 2. 技术栈识别
        tech_stack = self._identify_tech_stack(scan_data)
        
        # 3. 防御措施检测
        defense_measures = self._detect_defense_measures(scan_data)
        
        # 4. 环境约束分析
        environment_constraints = self._analyze_environment_constraints(
            scan_data, user_context
        )
        
        # 5. 合规要求分析
        compliance_requirements = self._analyze_compliance_requirements(user_context)
        
        # 6. 时间约束分析
        time_constraints = self._analyze_time_constraints(user_context)
        
        # 7. 风险容忍度分析
        risk_tolerance = self._analyze_risk_tolerance(user_context)
        
        result = {
            "target_type": target_analysis.target_type,
            "target_subtype": target_analysis.sub_type,
            "target_confidence": target_analysis.confidence,
            "tech_stack": tech_stack,
            "defense_measures": defense_measures,
            "environment_constraints": environment_constraints,
            "compliance_requirements": compliance_requirements,
            "time_constraints": time_constraints,
            "risk_tolerance": risk_tolerance
        }
        
        self.logger.debug(f"上下文分析完成: {result}")
        return result
    
    def _analyze_target(self, scan_data: Dict) -> TargetAnalysis:
        """分析目标类型"""
        target = scan_data.get("target", "")
        
        # 从扫描数据中提取信息
        ports = scan_data.get("ports", [])
        vulnerabilities = scan_data.get("vulnerabilities", [])
        fingerprint = scan_data.get("fingerprint", {})
        
        # 基于端口分析目标类型
        target_types = self._analyze_target_by_ports(ports)
        
        # 基于指纹分析
        fingerprint_types = self._analyze_target_by_fingerprint(fingerprint)
        
        # 基于漏洞分析
        vulnerability_types = self._analyze_target_by_vulnerabilities(vulnerabilities)
        
        # 合并分析结果
        all_evidence = {}
        
        # 收集所有证据
        for evidence_list in [target_types, fingerprint_types, vulnerability_types]:
            for target_type, confidence in evidence_list.items():
                if target_type not in all_evidence:
                    all_evidence[target_type] = []
                all_evidence[target_type].append(confidence)
        
        # 计算每个目标类型的平均置信度
        final_scores = {}
        for target_type, confidences in all_evidence.items():
            if confidences:
                final_scores[target_type] = sum(confidences) / len(confidences)
        
        # 如果没有找到证据，使用默认分析
        if not final_scores:
            return self._analyze_target_fallback(target, ports)
        
        # 选择置信度最高的目标类型
        best_target = max(final_scores.items(), key=lambda x: x[1])
        
        # 确定子类型
        sub_type = self._determine_subtype(
            best_target[0], ports, fingerprint, vulnerabilities
        )
        
        return TargetAnalysis(
            target_type=best_target[0],
            sub_type=sub_type,
            confidence=best_target[1]
        )
    
    def _analyze_target_by_ports(self, ports: List[Dict]) -> Dict[str, float]:
        """基于端口分析目标类型"""
        scores = {
            "Web": 0.0,
            "Database": 0.0,
            "Service": 0.0,
            "Network": 0.0,
            "Internal": 0.0
        }
        
        if not ports:
            return scores
        
        web_ports = [80, 443, 8080, 8443]
        db_ports = [3306, 5432, 1433, 1521, 27017, 6379]
        service_ports = [21, 22, 23, 25, 53, 110, 143, 445, 3389]
        internal_ports = [139, 445, 389, 636, 2049, 5985, 5986]
        
        for port_info in ports:
            port = port_info.get("port", 0)
            
            if port in web_ports:
                scores["Web"] += 0.3
            if port in db_ports:
                scores["Database"] += 0.4
            if port in service_ports:
                scores["Service"] += 0.2
            if port in internal_ports:
                scores["Internal"] += 0.5
        
        # 归一化
        for key in scores:
            scores[key] = min(scores[key], 1.0)
        
        return scores
    
    def _analyze_target_by_fingerprint(self, fingerprint: Dict) -> Dict[str, float]:
        """基于指纹分析目标类型"""
        scores = {
            "Web": 0.0,
            "Database": 0.0,
            "Service": 0.0
        }
        
        # 检查Web指纹
        web_server = fingerprint.get("web_server", "")
        if web_server:
            scores["Web"] += 0.7
        
        # 检查语言和框架
        languages = fingerprint.get("language", [])
        frameworks = fingerprint.get("cms", [])
        
        if languages or frameworks:
            scores["Web"] += 0.3
        
        # 检查其他指纹
        other = fingerprint.get("other", [])
        for item in other:
            if "database" in item.lower():
                scores["Database"] += 0.4
            if "service" in item.lower():
                scores["Service"] += 0.3
        
        return scores
    
    def _analyze_target_by_vulnerabilities(self, vulnerabilities: List[Dict]) -> Dict[str, float]:
        """基于漏洞分析目标类型"""
        scores = {
            "Web": 0.0,
            "Database": 0.0,
            "Service": 0.0
        }
        
        for vuln in vulnerabilities:
            name = vuln.get("name", "").lower()
            
            # Web相关漏洞
            web_keywords = ["xss", "csrf", "sql", "injection", "lfi", "rfi", "xxe"]
            if any(keyword in name for keyword in web_keywords):
                scores["Web"] += 0.2
            
            # 数据库相关漏洞
            db_keywords = ["sqli", "nosql", "mongodb", "redis", "database"]
            if any(keyword in name for keyword in db_keywords):
                scores["Database"] += 0.3
            
            # 服务相关漏洞
            service_keywords = ["rce", "command", "buffer", "overflow", "privilege"]
            if any(keyword in name for keyword in service_keywords):
                scores["Service"] += 0.25
        
        # 限制最大值
        for key in scores:
            scores[key] = min(scores[key], 1.0)
        
        return scores
    
    def _analyze_target_fallback(self, target: str, ports: List[Dict]) -> TargetAnalysis:
        """目标分析回退逻辑"""
        # 基于目标域名分析
        target_lower = target.lower()
        
        if any(keyword in target_lower for keyword in ["db", "database", "mysql", "postgres"]):
            return TargetAnalysis("Database", "unknown", 0.6)
        
        if any(keyword in target_lower for keyword in ["api", "service", "backend"]):
            return TargetAnalysis("Service", "unknown", 0.6)
        
        if any(keyword in target_lower for keyword in ["intranet", "internal", "local"]):
            return TargetAnalysis("Internal", "unknown", 0.7)
        
        # 基于端口分析
        if ports:
            for port_info in ports:
                port = port_info.get("port", 0)
                if port in [80, 443, 8080, 8443]:
                    return TargetAnalysis("Web", "unknown", 0.8)
                if port in [3306, 5432, 1433]:
                    return TargetAnalysis("Database", "unknown", 0.7)
        
        # 默认返回Web类型
        return TargetAnalysis("Web", "unknown", 0.5)
    
    def _determine_subtype(
        self, 
        target_type: str, 
        ports: List[Dict], 
        fingerprint: Dict, 
        vulnerabilities: List[Dict]
    ) -> str:
        """确定目标子类型"""
        if target_type == "Web":
            # 检查CMS/框架
            cms_list = fingerprint.get("cms", [])
            if cms_list:
                return cms_list[0]  # 返回第一个检测到的CMS
            
            # 检查Web服务器
            web_server = fingerprint.get("web_server", "")
            if web_server:
                return web_server
            
            return "Generic Web"
        
        elif target_type == "Database":
            # 检查数据库类型
            for port_info in ports:
                port = port_info.get("port", 0)
                service = port_info.get("service", "").lower()
                
                if port == 3306 or "mysql" in service:
                    return "MySQL"
                elif port == 5432 or "postgres" in service:
                    return "PostgreSQL"
                elif port == 1433 or "mssql" in service:
                    return "SQL Server"
                elif port == 27017 or "mongodb" in service:
                    return "MongoDB"
                elif port == 6379 or "redis" in service:
                    return "Redis"
            
            return "Generic Database"
        
        elif target_type == "Service":
            # 检查服务类型
            for port_info in ports:
                port = port_info.get("port", 0)
                
                if port == 22:
                    return "SSH"
                elif port == 3389:
                    return "RDP"
                elif port == 445:
                    return "SMB"
                elif port == 21:
                    return "FTP"
                elif port == 23:
                    return "Telnet"
            
            return "Generic Service"
        
        else:
            return "Unknown"
    
    def _identify_tech_stack(self, scan_data: Dict) -> List[str]:
        """识别技术栈"""
        tech_stack = []
        fingerprint = scan_data.get("fingerprint", {})
        
        # 提取所有指纹信息
        all_fingerprint_data = []
        
        # Web服务器
        web_server = fingerprint.get("web_server", "")
        if web_server:
            all_fingerprint_data.append(web_server.lower())
        
        # 编程语言
        languages = fingerprint.get("language", [])
        for lang in languages:
            all_fingerprint_data.append(lang.lower())
        
        # CMS/框架
        cms_list = fingerprint.get("cms", [])
        for cms in cms_list:
            all_fingerprint_data.append(cms.lower())
        
        # 其他指纹
        other_list = fingerprint.get("other", [])
        for item in other_list:
            all_fingerprint_data.append(item.lower())
        
        # 匹配技术栈模式
        detected_tech = set()
        
        for category, patterns in self.tech_stack_patterns.items():
            for tech_name, keywords in patterns.items():
                for keyword in keywords:
                    for fingerprint_item in all_fingerprint_data:
                        if keyword in fingerprint_item:
                            detected_tech.add(tech_name)
        
        # 从端口信息推断技术栈
        ports = scan_data.get("ports", [])
        for port_info in ports:
            port = port_info.get("port", 0)
            service = port_info.get("service", "").lower()
            
            if port == 3306 or "mysql" in service:
                detected_tech.add("mysql")
            elif port == 5432 or "postgres" in service:
                detected_tech.add("postgresql")
            elif port == 6379 or "redis" in service:
                detected_tech.add("redis")
            elif port == 27017 or "mongodb" in service:
                detected_tech.add("mongodb")
        
        return sorted(list(detected_tech))
    
    def _detect_defense_measures(self, scan_data: Dict) -> List[str]:
        """检测防御措施"""
        defenses = []
        
        # 检查WAF
        waf_info = scan_data.get("wafw00f", {})
        if waf_info.get("waf_detected", False):
            waf_type = waf_info.get("waf_type", "Unknown WAF")
            defenses.append(f"WAF: {waf_type}")
        
        # 从指纹信息中检测防御措施
        fingerprint = scan_data.get("fingerprint", {})
        other_items = fingerprint.get("other", [])
        
        for item in other_items:
            item_lower = item.lower()
            for defense_type, keywords in self.defense_patterns.items():
                for keyword in keywords:
                    if keyword in item_lower:
                        defenses.append(f"{defense_type.upper()}: {keyword}")
                        break
        
        # 从端口信息推断
        ports = scan_data.get("ports", [])
        for port_info in ports:
            port = port_info.get("port", 0)
            
            # 安全相关端口
            security_ports = {
                514: "Syslog",
                1514: "Syslog over TLS",
                20514: "Syslog over DTLS",
                6514: "Syslog over TLS",
                5140: "Syslog over TCP"
            }
            
            if port in security_ports:
                defenses.append(f"Security Monitoring: {security_ports[port]}")
        
        return defenses
    
    def _analyze_environment_constraints(self, scan_data: Dict, user_context: Dict) -> Dict[str, Any]:
        """分析环境约束"""
        constraints = {
            "network": "external",  # external/internal
            "access_level": "normal",  # normal/limited/privileged
            "bandwidth_limit": "none",  # none/low/medium/high
            "resource_constraints": "none"  # none/low/medium/high
        }
        
        # 从用户上下文获取
        user_constraints = user_context.get("constraints", {})
        constraints.update(user_constraints)
        
        # 从扫描数据推断
        target = scan_data.get("target", "")
        target_lower = target.lower()
        
        # 网络环境推断
        internal_keywords = ["intranet", "internal", "local", "192.168", "10.", "172."]
        if any(keyword in target_lower for keyword in internal_keywords):
            constraints["network"] = "internal"
        
        # 带宽限制推断（基于目标地理位置或用户设置）
        if user_context.get("bandwidth_sensitive", False):
            constraints["bandwidth_limit"] = "low"
        
        # 资源约束推断
        resource_constraints = user_context.get("resource_constraints", {})
        if resource_constraints:
            if resource_constraints.get("memory_limit", 0) < 1024:  # < 1GB
                constraints["resource_constraints"] = "low"
            elif resource_constraints.get("memory_limit", 0) < 4096:  # < 4GB
                constraints["resource_constraints"] = "medium"
        
        return constraints
    
    def _analyze_compliance_requirements(self, user_context: Dict) -> List[str]:
        """分析合规要求"""
        requirements = []
        
        # 从用户上下文获取
        user_requirements = user_context.get("compliance_requirements", [])
        requirements.extend(user_requirements)
        
        # 基于行业推断
        industry = user_context.get("industry", "")
        if industry:
            industry_lower = industry.lower()
            
            if "finance" in industry_lower or "bank" in industry_lower:
                requirements.extend(["PCI-DSS", "GLBA", "SOX"])
            elif "health" in industry_lower or "medical" in industry_lower:
                requirements.extend(["HIPAA", "HITECH"])
            elif "government" in industry_lower:
                requirements.extend(["FISMA", "NIST", "FedRAMP"])
            elif "retail" in industry_lower:
                requirements.append("PCI-DSS")
        
        return list(set(requirements))  # 去重
    
    def _analyze_time_constraints(self, user_context: Dict) -> Dict[str, Any]:
        """分析时间约束"""
        constraints = {
            "strict": False,
            "time_limit": None,  # 时间限制（分钟）
            "schedule": "anytime",  # 执行时间安排
            "urgency": "normal"  # 紧急程度
        }
        
        # 从用户上下文获取
        user_time = user_context.get("time_constraints", {})
        constraints.update(user_time)
        
        # 推断紧急程度
        urgency = user_context.get("urgency", "normal")
        constraints["urgency"] = urgency
        
        if urgency == "high":
            constraints["strict"] = True
            constraints["time_limit"] = constraints.get("time_limit", 60)  # 默认1小时
        
        return constraints
    
    def _analyze_risk_tolerance(self, user_context: Dict) -> str:
        """分析风险容忍度"""
        # 从用户上下文获取
        user_tolerance = user_context.get("risk_tolerance", "")
        
        if user_tolerance in ["low", "medium", "high"]:
            return user_tolerance
        
        # 基于行业推断
        industry = user_context.get("industry", "")
        if industry:
            industry_lower = industry.lower()
            
            if any(keyword in industry_lower for keyword in ["finance", "bank", "government"]):
                return "low"
            elif any(keyword in industry_lower for keyword in ["health", "medical"]):
                return "low"
            elif any(keyword in industry_lower for keyword in ["startup", "tech", "software"]):
                return "medium"
        
        # 基于测试类型推断
        test_type = user_context.get("test_type", "")
        if test_type == "pentest":
            return "medium"
        elif test_type == "security_assessment":
            return "low"
        elif test_type == "red_team":
            return "high"
        
        # 默认值
        return "medium"


def main():
    """测试函数"""
    import json
    
    # 创建上下文管理器
    manager = ContextManager()
    
    # 测试数据
    test_scan_data = {
        "target": "example.com",
        "ports": [
            {"port": 80, "service": "http", "state": "open"},
            {"port": 443, "service": "https", "state": "open"},
            {"port": 3306, "service": "mysql", "state": "open"}
        ],
        "vulnerabilities": [
            {"name": "SQL Injection", "severity": "high"},
            {"name": "XSS Vulnerability", "severity": "medium"}
        ],
        "fingerprint": {
            "web_server": "nginx/1.18.0",
            "language": ["PHP 7.4"],
            "cms": ["WordPress 5.8"],
            "other": ["jQuery", "Bootstrap"]
        },
        "wafw00f": {
            "waf_detected": True,
            "waf_type": "Cloudflare"
        }
    }
    
    test_user_context = {
        "target": "example.com",
        "industry": "e-commerce",
        "test_type": "pentest",
        "constraints": {
            "network": "external",
            "bandwidth_limit": "medium"
        },
        "time_constraints": {
            "strict": False,
            "time_limit": 120
        },
        "risk_tolerance": "medium"
    }
    
    # 分析上下文
    context_analysis = manager.analyze(test_scan_data, test_user_context)
    
    print("=" * 80)
    print("上下文管理器测试")
    print("=" * 80)
    
    print(f"\n目标分析:")
    print(f"  类型: {context_analysis['target_type']}")
    print(f"  子类型: {context_analysis['target_subtype']}")
    print(f"  置信度: {context_analysis['target_confidence']:.2f}")
    
    print(f"\n技术栈 ({len(context_analysis['tech_stack'])}项):")
    for tech in context_analysis['tech_stack']:
        print(f"  - {tech}")
    
    print(f"\n防御措施 ({len(context_analysis['defense_measures'])}项):")
    for defense in context_analysis['defense_measures']:
        print(f"  - {defense}")
    
    print(f"\n环境约束:")
    for key, value in context_analysis['environment_constraints'].items():
        print(f"  {key}: {value}")
    
    print(f"\n合规要求 ({len(context_analysis['compliance_requirements'])}项):")
    for req in context_analysis['compliance_requirements']:
        print(f"  - {req}")
    
    print(f"\n时间约束:")
    for key, value in context_analysis['time_constraints'].items():
        print(f"  {key}: {value}")
    
    print(f"\n风险容忍度: {context_analysis['risk_tolerance']}")
    print("=" * 80)


if __name__ == "__main__":
    main()