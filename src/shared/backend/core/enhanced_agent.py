# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强的AI智能体模块
具备完整的攻击路径规划和工具决策能力
支持多模型、本地推理和缓存机制
"""

import json
import os
import sys
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 导入工具注册表
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from tools.tool_registry import ToolRegistry
except ImportError:
    # 回退到简单导入
    pass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AttackPhase(Enum):
    """攻击阶段枚举"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    GAINING_ACCESS = "gaining_access"
    MAINTAINING_ACCESS = "maintaining_access"
    COVERING_TRACKS = "covering_tracks"


@dataclass
class ToolRecommendation:
    """工具推荐"""
    tool_id: str
    name: str
    category: str
    description: str
    confidence: float  # 0.0-1.0
    priority: int  # 1-10
    phase: AttackPhase
    parameters: Dict[str, Any]


@dataclass
class AttackStep:
    """攻击步骤"""
    step_id: str
    phase: AttackPhase
    description: str
    recommended_tool: ToolRecommendation
    dependencies: List[str]  # 依赖的step_id
    expected_outcome: str
    risk: RiskLevel


@dataclass
class AttackPath:
    """攻击路径"""
    path_id: str
    name: str
    description: str
    steps: List[AttackStep]
    total_risk: RiskLevel
    success_probability: float  # 0.0-1.0
    estimated_time: int  # 分钟


class EnhancedSecurityAgent:
    """增强的安全分析智能体"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.tool_registry = ToolRegistry() if self._can_import_tool_registry() else None
        self.cache_dir = os.path.join(os.path.dirname(__file__), "ai_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化LLM客户端
        self.llm_client = self._init_llm_client()
        
        # 知识库
        self.knowledge_base = self._load_knowledge_base()
        
        logger.info(f"EnhancedSecurityAgent initialized with {len(self.knowledge_base.get('cves', []))} CVEs in knowledge base")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置"""
        default_config = {
            "llm_provider": "openai",  # openai, deepseek, local
            "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"),
            "model": "gpt-4" if os.getenv("OPENAI_API_KEY") else "deepseek-chat",
            "cache_enabled": True,
            "max_steps_per_path": 10,
            "parallel_execution": False,
            "risk_threshold": RiskLevel.MEDIUM,
            "timeout": 300  # 5分钟
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                default_config.update(custom_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        provider = self.config["llm_provider"]
        
        if provider == "local":
            # 本地模型（需要安装相应的库）
            try:
                # 尝试导入transformers
                import transformers
                from transformers import pipeline
                
                # 使用小模型以节省资源
                model_id = "microsoft/DialoGPT-small"
                return pipeline("text-generation", model=model_id)
                
            except ImportError:
                logger.warning("Transformers not installed, using rule-based fallback")
                return None
                
        elif provider == "deepseek":
            # DeepSeek API客户端
            return DeepSeekClient(self.config.get("api_key"))
            
        else:  # openai 或其他
            # 使用通用的OpenAI格式API
            return OpenAIClient(
                api_key=self.config.get("api_key"),
                model=self.config.get("model"),
                base_url=self.config.get("api_base")
            )
    
    def _load_knowledge_base(self) -> Dict:
        """加载安全知识库"""
        knowledge_base = {
            "cves": [],  # CVE漏洞信息
            "attack_patterns": [],  # 攻击模式
            "tool_capabilities": {},  # 工具能力映射
            "port_services": {},  # 端口-服务映射
            "vulnerability_patterns": []  # 漏洞模式
        }
        
        # 加载CVE数据
        cve_file = os.path.join(os.path.dirname(__file__), "knowledge", "cve_database.json")
        if os.path.exists(cve_file):
            try:
                with open(cve_file, 'r', encoding='utf-8') as f:
                    knowledge_base["cves"] = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load CVE database: {e}")
        
        # 内置的端口-服务映射
        knowledge_base["port_services"] = {
            21: {"service": "ftp", "vulnerabilities": ["anonymous_login", "weak_password"]},
            22: {"service": "ssh", "vulnerabilities": ["weak_password", "ssh_key_leak"]},
            23: {"service": "telnet", "vulnerabilities": ["clear_text", "weak_password"]},
            25: {"service": "smtp", "vulnerabilities": ["open_relay", "spoofing"]},
            53: {"service": "dns", "vulnerabilities": ["zone_transfer", "cache_poisoning"]},
            80: {"service": "http", "vulnerabilities": ["web_vulnerabilities"]},
            443: {"service": "https", "vulnerabilities": ["ssl_vulnerabilities"]},
            445: {"service": "smb", "vulnerabilities": ["eternalblue", "smb_relay"]},
            1433: {"service": "mssql", "vulnerabilities": ["weak_password", "injection"]},
            3306: {"service": "mysql", "vulnerabilities": ["weak_password", "injection"]},
            3389: {"service": "rdp", "vulnerabilities": ["bluekeep", "weak_password"]},
            5432: {"service": "postgresql", "vulnerabilities": ["weak_password", "injection"]},
            5900: {"service": "vnc", "vulnerabilities": ["weak_password", "unencrypted"]},
            6379: {"service": "redis", "vulnerabilities": ["unauthorized_access", "injection"]},
            27017: {"service": "mongodb", "vulnerabilities": ["unauthorized_access", "injection"]}
        }
        
        # 攻击模式
        knowledge_base["attack_patterns"] = [
            {
                "name": "Web应用攻击链",
                "description": "针对Web应用的完整攻击流程",
                "steps": ["端口扫描", "指纹识别", "目录爆破", "漏洞扫描", "利用尝试"]
            },
            {
                "name": "数据库渗透链",
                "description": "针对数据库系统的攻击流程",
                "steps": ["端口识别", "服务识别", "弱口令爆破", "SQL注入", "数据提取"]
            },
            {
                "name": "内网横向移动",
                "description": "在内网环境中的横向移动攻击",
                "steps": ["信息收集", "凭证窃取", "横向扫描", "服务攻击", "权限维持"]
            }
        ]
        
        # 工具能力映射
        knowledge_base["tool_capabilities"] = {
            "nmap": {"phases": [AttackPhase.RECONNAISSANCE], "capabilities": ["port_scan", "service_detection", "os_detection"]},
            "masscan": {"phases": [AttackPhase.RECONNAISSANCE], "capabilities": ["fast_port_scan"]},
            "whatweb": {"phases": [AttackPhase.RECONNAISSANCE], "capabilities": ["web_fingerprinting"]},
            "dirsearch": {"phases": [AttackPhase.SCANNING], "capabilities": ["directory_bruteforce"]},
            "nikto": {"phases": [AttackPhase.SCANNING], "capabilities": ["web_vulnerability_scan"]},
            "nuclei": {"phases": [AttackPhase.SCANNING], "capabilities": ["vulnerability_scan"]},
            "sqlmap": {"phases": [AttackPhase.GAINING_ACCESS], "capabilities": ["sql_injection"]},
            "wpscan": {"phases": [AttackPhase.SCANNING, AttackPhase.GAINING_ACCESS], "capabilities": ["wordpress_scan"]},
            "hydra": {"phases": [AttackPhase.GAINING_ACCESS], "capabilities": ["password_bruteforce"]},
            "metasploit": {"phases": [AttackPhase.GAINING_ACCESS, AttackPhase.MAINTAINING_ACCESS], "capabilities": ["exploitation", "post_exploitation"]}
        }
        
        return knowledge_base
    
    def _can_import_tool_registry(self) -> bool:
        """检查是否能导入工具注册表"""
        try:
            from tools.tool_registry import ToolRegistry
            return True
        except ImportError:
            return False
    
    def analyze_scan_results(self, scan_data: Dict) -> Dict:
        """分析扫描结果，生成风险评估和攻击建议"""
        start_time = time.time()
        
        # 提取关键信息
        target = scan_data.get("target", "unknown")
        ports = scan_data.get("ports", [])
        vulnerabilities = scan_data.get("vulnerabilities", [])
        fingerprint = scan_data.get("fingerprint", {})
        
        # 风险评估
        risk_assessment = self._assess_risk(ports, vulnerabilities, fingerprint)
        
        # 攻击路径生成
        attack_paths = self._generate_attack_paths(target, ports, vulnerabilities, fingerprint)
        
        # 工具推荐
        tool_recommendations = self._recommend_tools(ports, vulnerabilities, fingerprint)
        
        # 生成报告
        report = {
            "target": target,
            "timestamp": time.time(),
            "analysis_time": time.time() - start_time,
            "risk_assessment": risk_assessment,
            "attack_paths": attack_paths,
            "tool_recommendations": tool_recommendations,
            "summary": self._generate_summary(risk_assessment, attack_paths)
        }
        
        return report
    
    def _assess_risk(self, ports: List, vulnerabilities: List, fingerprint: Dict) -> Dict:
        """风险评估"""
        risk_score = 0
        risk_factors = []
        
        # 基于端口的风险评估
        for port_info in ports:
            port = port_info.get("port", 0)
            service = port_info.get("service", "").lower()
            
            port_risk = 0
            if port in [21, 23, 25, 110]:  # 明文协议
                port_risk += 20
                risk_factors.append(f"端口 {port} 使用明文协议")
            
            if port in [445, 3389, 22]:  # 常见攻击目标
                port_risk += 30
                risk_factors.append(f"端口 {port} 是常见攻击目标")
            
            if port in [80, 443, 8080, 8443]:  # Web服务
                port_risk += 25
                risk_factors.append(f"端口 {port} 暴露Web服务")
            
            risk_score += port_risk
        
        # 基于漏洞的风险评估
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info").lower()
            if severity == "critical":
                risk_score += 100
                risk_factors.append(f"严重漏洞: {vuln.get('name', '未知')}")
            elif severity == "high":
                risk_score += 80
                risk_factors.append(f"高危漏洞: {vuln.get('name', '未知')}")
            elif severity == "medium":
                risk_score += 50
                risk_factors.append(f"中危漏洞: {vuln.get('name', '未知')}")
            elif severity == "low":
                risk_score += 20
                risk_factors.append(f"低危漏洞: {vuln.get('name', '未知')}")
        
        # 确定风险等级
        if risk_score >= 150:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 100:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 50:
            risk_level = RiskLevel.MEDIUM
        elif risk_score >= 20:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.INFO
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "port_count": len(ports),
            "vulnerability_count": len(vulnerabilities),
            "critical_vulns": len([v for v in vulnerabilities if v.get("severity", "").lower() == "critical"]),
            "high_vulns": len([v for v in vulnerabilities if v.get("severity", "").lower() == "high"])
        }
    
    def _generate_attack_paths(self, target: str, ports: List, vulnerabilities: List, fingerprint: Dict) -> List[Dict]:
        """生成攻击路径"""
        attack_paths = []
        
        # 生成基于Web的攻击路径
        web_ports = [p for p in ports if p.get("port") in [80, 443, 8080, 8443]]
        if web_ports:
            web_path = self._create_web_attack_path(target, web_ports, vulnerabilities, fingerprint)
            if web_path:
                attack_paths.append(web_path)
        
        # 生成基于数据库的攻击路径
        db_ports = [p for p in ports if p.get("port") in [3306, 5432, 1433, 27017]]
        if db_ports:
            db_path = self._create_database_attack_path(target, db_ports)
            if db_path:
                attack_paths.append(db_path)
        
        # 生成基于服务的攻击路径
        service_path = self._create_service_attack_path(target, ports, vulnerabilities)
        if service_path:
            attack_paths.append(service_path)
        
        # 如果没有特定路径，生成通用路径
        if not attack_paths and ports:
            generic_path = self._create_generic_attack_path(target, ports)
            if generic_path:
                attack_paths.append(generic_path)
        
        return attack_paths
    
    def _create_web_attack_path(self, target: str, ports: List, vulnerabilities: List, fingerprint: Dict) -> Dict:
        """创建Web攻击路径"""
        steps = []
        
        # 步骤1: 信息收集
        steps.append({
            "step_id": "web_recon_1",
            "phase": AttackPhase.RECONNAISSANCE.value,
            "description": "Web服务指纹识别和目录发现",
            "recommended_tool": {"tool_id": "whatweb", "name": "WhatWeb", "confidence": 0.9},
            "expected_outcome": "识别Web框架、CMS、服务器版本",
            "risk": RiskLevel.LOW.value
        })
        
        # 步骤2: 目录爆破
        steps.append({
            "step_id": "web_scan_1",
            "phase": AttackPhase.SCANNING.value,
            "description": "目录和文件爆破，寻找敏感路径",
            "recommended_tool": {"tool_id": "dirsearch", "name": "Dirsearch", "confidence": 0.8},
            "dependencies": ["web_recon_1"],
            "expected_outcome": "发现管理后台、配置文件、备份文件",
            "risk": RiskLevel.MEDIUM.value
        })
        
        # 步骤3: 漏洞扫描
        steps.append({
            "step_id": "web_scan_2",
            "phase": AttackPhase.SCANNING.value,
            "description": "全面漏洞扫描",
            "recommended_tool": {"tool_id": "nikto", "name": "Nikto", "confidence": 0.7},
            "dependencies": ["web_recon_1"],
            "expected_outcome": "发现Web漏洞和配置问题",
            "risk": RiskLevel.MEDIUM.value
        })
        
        # 如果有CMS，添加CMS扫描步骤
        cms_info = fingerprint.get("cms", [])
        if any("wordpress" in cms.lower() for cms in cms_info):
            steps.append({
                "step_id": "cms_scan",
                "phase": AttackPhase.SCANNING.value,
                "description": "WordPress漏洞扫描",
                "recommended_tool": {"tool_id": "wpscan", "name": "WPScan", "confidence": 0.9},
                "expected_outcome": "发现WordPress插件和主题漏洞",
                "risk": RiskLevel.HIGH.value
            })
        
        return {
            "path_id": f"web_attack_{hashlib.md5(target.encode()).hexdigest()[:8]}",
            "name": "Web应用渗透攻击链",
            "description": "针对Web应用的完整攻击路径，包括信息收集、漏洞扫描和利用尝试",
            "steps": steps,
            "total_risk": RiskLevel.HIGH.value if vulnerabilities else RiskLevel.MEDIUM.value,
            "success_probability": 0.7 if vulnerabilities else 0.4,
            "estimated_time": 30
        }
    
    def _create_database_attack_path(self, target: str, ports: List) -> Dict:
        """创建数据库攻击路径"""
        steps = []
        
        for port_info in ports:
            port = port_info.get("port")
            service = port_info.get("service", "").lower()
            
            if port == 3306:  # MySQL
                steps.append({
                    "step_id": f"db_recon_{port}",
                    "phase": AttackPhase.RECONNAISSANCE.value,
                    "description": f"MySQL服务识别和版本检测",
                    "recommended_tool": {"tool_id": "nmap", "name": "Nmap", "confidence": 0.9},
                    "expected_outcome": "识别MySQL版本和配置信息",
                    "risk": RiskLevel.LOW.value
                })
                
                steps.append({
                    "step_id": f"db_attack_{port}",
                    "phase": AttackPhase.GAINING_ACCESS.value,
                    "description": f"MySQL弱口令爆破和SQL注入测试",
                    "recommended_tool": {"tool_id": "hydra", "name": "Hydra", "confidence": 0.6},
                    "dependencies": [f"db_recon_{port}"],
                    "expected_outcome": "获取数据库访问权限或发现SQL注入点",
                    "risk": RiskLevel.HIGH.value
                })
        
        if steps:
            return {
                "path_id": f"db_attack_{hashlib.md5(target.encode()).hexdigest()[:8]}",
                "name": "数据库渗透攻击链",
                "description": "针对数据库系统的攻击路径，包括服务识别、弱口令爆破和注入测试",
                "steps": steps,
                "total_risk": RiskLevel.HIGH.value,
                "success_probability": 0.5,
                "estimated_time": 45
            }
        
        return {}
    
    def _create_service_attack_path(self, target: str, ports: List, vulnerabilities: List) -> Dict:
        """创建服务攻击路径"""
        steps = []
        
        for port_info in ports:
            port = port_info.get("port")
            
            if port == 22:  # SSH
                steps.append({
                    "step_id": f"ssh_attack_{port}",
                    "phase": AttackPhase.GAINING_ACCESS.value,
                    "description": f"SSH弱口令爆破",
                    "recommended_tool": {"tool_id": "hydra", "name": "Hydra", "confidence": 0.5},
                    "expected_outcome": "获取SSH访问权限",
                    "risk": RiskLevel.HIGH.value
                })
            
            elif port == 3389:  # RDP
                steps.append({
                    "step_id": f"rdp_attack_{port}",
                    "phase": AttackPhase.GAINING_ACCESS.value,
                    "description": f"RDP弱口令爆破",
                    "recommended_tool": {"tool_id": "hydra", "name": "Hydra", "confidence": 0.5},
                    "expected_outcome": "获取RDP访问权限",
                    "risk": RiskLevel.HIGH.value
                })
        
        if steps:
            return {
                "path_id": f"service_attack_{hashlib.md5(target.encode()).hexdigest()[:8]}",
                "name": "服务攻击链",
                "description": "针对网络服务的攻击路径，包括SSH、RDP等服务的弱口令爆破",
                "steps": steps,
                "total_risk": RiskLevel.HIGH.value,
                "success_probability": 0.4,
                "estimated_time": 60
            }
        
        return {}
    
    def _create_generic_attack_path(self, target: str, ports: List) -> Dict:
        """创建通用攻击路径"""
        steps = [
            {
                "step_id": "generic_recon_1",
                "phase": AttackPhase.RECONNAISSANCE.value,
                "description": "全面端口扫描和服务识别",
                "recommended_tool": {"tool_id": "nmap", "name": "Nmap", "confidence": 0.9},
                "expected_outcome": "发现所有开放端口和服务",
                "risk": RiskLevel.LOW.value
            },
            {
                "step_id": "generic_scan_1",
                "phase": AttackPhase.SCANNING.value,
                "description": "漏洞扫描和配置检查",
                "recommended_tool": {"tool_id": "nuclei", "name": "Nuclei", "confidence": 0.7},
                "dependencies": ["generic_recon_1"],
                "expected_outcome": "发现系统漏洞和配置问题",
                "risk": RiskLevel.MEDIUM.value
            }
        ]
        
        return {
            "path_id": f"generic_attack_{hashlib.md5(target.encode()).hexdigest()[:8]}",
            "name": "通用渗透测试链",
            "description": "通用的渗透测试攻击路径，适用于初步评估",
            "steps": steps,
            "total_risk": RiskLevel.MEDIUM.value,
            "success_probability": 0.3,
            "estimated_time": 40
        }
    
    def _recommend_tools(self, ports: List, vulnerabilities: List, fingerprint: Dict) -> List[Dict]:
        """推荐工具"""
        recommendations = []
        
        # 基础工具推荐
        base_tools = [
            {"tool_id": "nmap", "name": "Nmap", "reason": "基础端口扫描", "priority": 1, "confidence": 0.9},
            {"tool_id": "whatweb", "name": "WhatWeb", "reason": "Web指纹识别", "priority": 2, "confidence": 0.8}
        ]
        
        # 根据端口推荐工具
        for port_info in ports:
            port = port_info.get("port")
            
            if port in [80, 443, 8080, 8443]:
                recommendations.append({
                    "tool_id": "dirsearch",
                    "name": "Dirsearch", 
                    "reason": f"Web目录爆破 (端口{port})",
                    "priority": 3,
                    "confidence": 0.7
                })
                recommendations.append({
                    "tool_id": "nikto",
                    "name": "Nikto",
                    "reason": f"Web漏洞扫描 (端口{port})",
                    "priority": 4,
                    "confidence": 0.6
                })
            
            if port == 3306:
                recommendations.append({
                    "tool_id": "sqlmap",
                    "name": "SQLMap",
                    "reason": "MySQL SQL注入测试",
                    "priority": 3,
                    "confidence": 0.5
                })
        
        # 根据指纹推荐CMS扫描器
        cms_info = fingerprint.get("cms", [])
        for cms in cms_info:
            cms_lower = cms.lower()
            if "wordpress" in cms_lower:
                recommendations.append({
                    "tool_id": "wpscan",
                    "name": "WPScan",
                    "reason": "WordPress漏洞扫描",
                    "priority": 2,
                    "confidence": 0.8
                })
            elif "joomla" in cms_lower:
                recommendations.append({
                    "tool_id": "joomscan",
                    "name": "JoomScan",
                    "reason": "Joomla漏洞扫描",
                    "priority": 2,
                    "confidence": 0.8
                })
        
        # 合并基础工具和推荐工具，去重
        all_tools = {tool["tool_id"]: tool for tool in base_tools}
        for rec in recommendations:
            if rec["tool_id"] not in all_tools:
                all_tools[rec["tool_id"]] = rec
        
        # 按优先级排序
        sorted_tools = sorted(all_tools.values(), key=lambda x: x["priority"])
        
        return sorted_tools
    
    def _generate_summary(self, risk_assessment: Dict, attack_paths: List[Dict]) -> str:
        """生成分析摘要"""
        risk_level = risk_assessment.get("risk_level", "low")
        vuln_count = risk_assessment.get("vulnerability_count", 0)
        path_count = len(attack_paths)
        
        if risk_level == "critical" or risk_level == "high":
            summary = f"目标存在高风险安全问题。发现{vuln_count}个漏洞，已生成{path_count}条攻击路径。建议立即进行安全加固。"
        elif risk_level == "medium":
            summary = f"目标存在中等风险安全问题。发现{vuln_count}个漏洞，已生成{path_count}条攻击路径。建议近期进行安全评估。"
        elif risk_level == "low":
            summary = f"目标安全性相对较好。发现{vuln_count}个漏洞，已生成{path_count}条攻击路径。建议定期安全巡检。"
        else:
            summary = f"目标安全性良好。发现{vuln_count}个漏洞，已生成{path_count}条攻击路径。建议继续保持安全配置。"
        
        return summary
    
    def query_llm(self, prompt: str, use_cache: bool = True) -> Optional[str]:
        """查询LLM，支持缓存"""
        if not self.llm_client:
            return None
        
        # 缓存键
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # 检查缓存
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                logger.info(f"Cache hit for key: {cache_key}")
                return cached.get("response")
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        
        # 调用LLM
        try:
            response = self.llm_client.generate(prompt)
            
            # 保存到缓存
            if use_cache and response:
                cache_data = {
                    "prompt": prompt,
                    "response": response,
                    "timestamp": time.time()
                }
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to write cache: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return None


class OpenAIClient:
    """OpenAI兼容客户端"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        
    def generate(self, prompt: str) -> Optional[str]:
        """生成响应"""
        if not self.api_key:
            return None
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个资深网络安全专家，擅长渗透测试和攻击路径分析。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            return None


class DeepSeekClient:
    """DeepSeek客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def generate(self, prompt: str) -> Optional[str]:
        """生成响应"""
        if not self.api_key:
            return None
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个资深网络安全专家，擅长渗透测试和攻击路径分析。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"DeepSeek request failed: {e}")
            return None


def main():
    """测试主函数"""
    test_data = {
        "target": "example.com",
        "ports": [
            {"port": 80, "service": "http", "state": "open"},
            {"port": 443, "service": "https", "state": "open"},
            {"port": 3306, "service": "mysql", "state": "open"},
            {"port": 22, "service": "ssh", "state": "open"}
        ],
        "vulnerabilities": [
            {"name": "XSS漏洞", "severity": "medium", "description": "跨站脚本漏洞"},
            {"name": "SQL注入", "severity": "high", "description": "SQL注入点"}
        ],
        "fingerprint": {
            "web_server": "nginx/1.18.0",
            "language": ["PHP 7.4"],
            "cms": ["WordPress 5.8"],
            "other": []
        }
    }
    
    agent = EnhancedSecurityAgent()
    report = agent.analyze_scan_results(test_data)
    
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()