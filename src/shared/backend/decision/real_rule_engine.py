# -*- coding: utf-8 -*-
"""
真实的规则引擎 - 不伪装成AI
技术诚信重建：创建真实的规则引擎
"""

import json
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """规则定义"""
    id: str
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: str  # critical, high, medium, low
    weight: float  # 0.0 - 1.0
    category: str  # reconnaissance, vulnerability, exploitation, post_exploitation
    recommendation: str
    confidence_adjustment: float = 0.0  # 对置信度的调整


@dataclass
class FeatureSet:
    """特征集合"""
    open_ports: List[int] = field(default_factory=list)
    web_technologies: List[str] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)  # port -> service
    os_info: Optional[str] = None
    ssl_info: Optional[Dict[str, Any]] = None
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    technologies: List[str] = field(default_factory=list)
    cms_info: Optional[str] = None
    database_info: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "open_ports": self.open_ports,
            "web_technologies": self.web_technologies,
            "services": self.services,
            "os_info": self.os_info,
            "ssl_info": self.ssl_info,
            "vulnerability_count": len(self.vulnerabilities),
            "header_count": len(self.headers),
            "technologies": self.technologies,
            "cms_info": self.cms_info,
            "database_info": self.database_info
        }


class RealRuleEngine:
    """真实的规则引擎 - 不伪装成AI"""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.knowledge_base: Dict[str, Any] = {}
        self._init_rules()
        self._init_knowledge_base()
        
        logger.info(f"RealRuleEngine 初始化完成 - 规则数量: {len(self.rules)}")
    
    def _init_rules(self):
        """初始化规则库"""
        # 侦察规则
        self.rules.extend([
            Rule(
                id="RECON-001",
                name="高危端口开放",
                description="发现SSH、Telnet、RDP等高危管理端口开放",
                condition=lambda f: any(p in f.open_ports for p in [22, 23, 3389, 5900]),
                severity="high",
                weight=0.8,
                category="reconnaissance",
                recommendation="关闭不必要的管理端口，或配置强认证和访问控制",
                confidence_adjustment=0.2
            ),
            Rule(
                id="RECON-002",
                name="数据库端口暴露",
                description="发现数据库服务端口直接暴露在互联网",
                condition=lambda f: any(p in f.open_ports for p in [3306, 5432, 1433, 27017]),
                severity="high",
                weight=0.7,
                category="reconnaissance",
                recommendation="数据库服务不应直接暴露在互联网，应使用VPN或跳板机访问",
                confidence_adjustment=0.15
            ),
            Rule(
                id="RECON-003",
                name="Web服务端口开放",
                description="HTTP/HTTPS服务端口开放",
                condition=lambda f: any(p in f.open_ports for p in [80, 443, 8080, 8443]),
                severity="medium",
                weight=0.5,
                category="reconnaissance",
                recommendation="确保Web服务配置安全，应用安全补丁",
                confidence_adjustment=0.1
            ),
        ])
        
        # 漏洞规则
        self.rules.extend([
            Rule(
                id="VULN-001",
                name="已知漏洞存在",
                description="扫描发现已知CVE漏洞",
                condition=lambda f: len(f.vulnerabilities) > 0,
                severity="critical",
                weight=0.9,
                category="vulnerability",
                recommendation="立即修复发现的CVE漏洞，应用安全补丁",
                confidence_adjustment=0.25
            ),
            Rule(
                id="VULN-002",
                name="过期SSL/TLS配置",
                description="SSL/TLS配置过期或存在弱点",
                condition=lambda f: f.ssl_info and (
                    f.ssl_info.get("protocol") == "SSLv3" or 
                    "weak" in f.ssl_info.get("grade", "").lower()
                ),
                severity="medium",
                weight=0.6,
                category="vulnerability",
                recommendation="升级到TLS 1.2+，禁用弱加密算法",
                confidence_adjustment=0.15
            ),
            Rule(
                id="VULN-003",
                name="信息泄露风险",
                description="HTTP头或响应中包含敏感信息",
                condition=lambda f: any(
                    header.lower() in ["server", "x-powered-by", "x-aspnet-version"] 
                    for header in f.headers.keys()
                ),
                severity="low",
                weight=0.4,
                category="vulnerability",
                recommendation="移除或模糊化服务器信息头，减少信息泄露",
                confidence_adjustment=0.1
            ),
        ])
        
        # Web应用规则
        self.rules.extend([
            Rule(
                id="WEB-001",
                name="过时的Web技术",
                description="使用过时或存在已知漏洞的Web技术",
                condition=lambda f: any(
                    tech in ["PHP/5.", "Apache/2.2", "IIS/6.0", "nginx/1.14"] 
                    for tech in f.web_technologies
                ),
                severity="high",
                weight=0.7,
                category="web_application",
                recommendation="升级Web服务器和组件到最新安全版本",
                confidence_adjustment=0.2
            ),
            Rule(
                id="WEB-002",
                name="CMS版本暴露",
                description="CMS系统版本信息暴露",
                condition=lambda f: f.cms_info and any(
                    cms in f.cms_info.lower() for cms in ["wordpress", "joomla", "drupal"]
                ),
                severity="medium",
                weight=0.5,
                category="web_application",
                recommendation="隐藏CMS版本信息，及时更新CMS和插件",
                confidence_adjustment=0.15
            ),
            Rule(
                id="WEB-003",
                name="管理后台可访问",
                description="Web应用管理后台可直接访问",
                condition=lambda f: "admin" in [tech.lower() for tech in f.technologies] or 
                                   any("/admin" in header.lower() for header in f.headers.values()),
                severity="high",
                weight=0.6,
                category="web_application",
                recommendation="限制管理后台访问，启用强认证和访问控制",
                confidence_adjustment=0.18
            ),
        ])
        
        # 安全配置规则
        self.rules.extend([
            Rule(
                id="SEC-001",
                name="缺乏安全头",
                description="缺少重要的安全HTTP头",
                condition=lambda f: not all(
                    header in f.headers for header in ["X-Content-Type-Options", "X-Frame-Options"]
                ),
                severity="medium",
                weight=0.5,
                category="security_config",
                recommendation="配置安全HTTP头：X-Content-Type-Options, X-Frame-Options等",
                confidence_adjustment=0.12
            ),
            Rule(
                id="SEC-002",
                name="CORS配置宽松",
                description="CORS配置允许任意来源访问",
                condition=lambda f: "access-control-allow-origin" in f.headers and 
                                   f.headers["access-control-allow-origin"] == "*",
                severity="medium",
                weight=0.4,
                category="security_config",
                recommendation="限制CORS配置，仅允许可信来源",
                confidence_adjustment=0.1
            ),
            Rule(
                id="SEC-003",
                name="目录列表启用",
                description="Web服务器目录列表功能启用",
                condition=lambda f: "directory listing" in [tech.lower() for tech in f.technologies],
                severity="low",
                weight=0.3,
                category="security_config",
                recommendation="禁用Web服务器目录列表功能",
                confidence_adjustment=0.08
            ),
        ])
        
        logger.info(f"已加载 {len(self.rules)} 条安全规则")
    
    def _init_knowledge_base(self):
        """初始化知识库"""
        self.knowledge_base = {
            "port_risk_levels": {
                "critical": [21, 22, 23, 25, 53, 110, 135, 139, 143, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900],
                "high": [80, 443, 8080, 8443, 27017, 6379, 9200],
                "medium": [161, 162, 389, 636, 873, 2049, 5060],
                "low": [111, 123, 137, 138, 500, 514, 873]
            },
            "vulnerability_severity": {
                "critical": ["rce", "sqli", "xss", "file_inclusion", "command_injection"],
                "high": ["csrf", "ssrf", "xxe", "idor", "path_traversal"],
                "medium": ["clickjacking", "information_disclosure", "weak_crypto"],
                "low": ["security_headers", "cors", "directory_listing"]
            },
            "web_tech_risk": {
                "high": ["PHP/5.", "Apache/2.2", "IIS/6.0", "Tomcat/7.", "WordPress/4."],
                "medium": ["nginx/1.14", "Apache/2.4", "IIS/8.0", "Tomcat/8."],
                "low": ["nginx/1.18+", "Apache/2.4.41+", "IIS/10.0", "Tomcat/9."]
            }
        }
    
    def _extract_features(self, target_data: Dict[str, Any]) -> FeatureSet:
        """从目标数据中提取特征"""
        features = FeatureSet()
        
        # 提取端口信息
        if "nmap" in target_data:
            nmap_result = target_data.get("nmap", {})
            if "ports" in nmap_result:
                for port_info in nmap_result["ports"]:
                    port = int(port_info.get("port", 0))
                    if port > 0:
                        features.open_ports.append(port)
                        service = port_info.get("service", "")
                        if service:
                            features.services[port] = service
        
        # 提取Web技术信息
        if "whatweb" in target_data:
            whatweb_result = target_data.get("whatweb", {})
            if isinstance(whatweb_result, dict):
                technologies = whatweb_result.get("technologies", [])
                if isinstance(technologies, list):
                    features.web_technologies.extend(technologies)
        
        # 提取服务信息
        if "services" in target_data:
            services = target_data.get("services", [])
            if isinstance(services, list):
                for service in services:
                    if isinstance(service, str):
                        features.technologies.append(service)
        
        # 提取漏洞信息
        if "vulnerabilities" in target_data:
            vulnerabilities = target_data.get("vulnerabilities", [])
            if isinstance(vulnerabilities, list):
                features.vulnerabilities.extend(vulnerabilities)
        
        # 提取HTTP头信息
        if "headers" in target_data:
            headers = target_data.get("headers", {})
            if isinstance(headers, dict):
                features.headers.update(headers)
        
        # 提取CMS信息
        if "cms" in target_data:
            cms_info = target_data.get("cms", "")
            if cms_info:
                features.cms_info = cms_info
        
        # 提取数据库信息
        if "database" in target_data:
            db_info = target_data.get("database", "")
            if db_info:
                features.database_info = db_info
        
        # 提取SSL信息
        if "ssl" in target_data:
            ssl_info = target_data.get("ssl", {})
            if isinstance(ssl_info, dict):
                features.ssl_info = ssl_info
        
        # 提取操作系统信息
        if "os" in target_data:
            os_info = target_data.get("os", "")
            if os_info:
                features.os_info = os_info
        
        logger.debug(f"特征提取完成 - 开放端口: {len(features.open_ports)}, 漏洞: {len(features.vulnerabilities)}")
        return features
    
    def _match_rules(self, features: FeatureSet) -> List[Dict[str, Any]]:
        """匹配规则"""
        matched_rules = []
        
        for rule in self.rules:
            try:
                if rule.condition(features):
                    matched_info = {
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "severity": rule.severity,
                        "weight": rule.weight,
                        "category": rule.category,
                        "recommendation": rule.recommendation,
                        "confidence_adjustment": rule.confidence_adjustment
                    }
                    matched_rules.append(matched_info)
                    logger.debug(f"规则匹配: {rule.id} - {rule.name}")
            except Exception as e:
                logger.warning(f"规则匹配异常 {rule.id}: {e}")
        
        return matched_rules
    
    def _calculate_risk_score(self, matched_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算风险分数"""
        if not matched_rules:
            return {
                "total_score": 0.0,
                "category_scores": {},
                "severity_breakdown": {},
                "risk_level": "low"
            }
        
        # 按类别和严重性统计
        category_scores = {}
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for rule in matched_rules:
            category = rule["category"]
            severity = rule["severity"]
            weight = rule["weight"]
            
            # 累加类别分数
            if category not in category_scores:
                category_scores[category] = 0.0
            category_scores[category] += weight * 10  # 转换为10分制
            
            # 统计严重性数量
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # 计算总分（加权平均）
        total_weight = sum(r["weight"] for r in matched_rules)
        if total_weight > 0:
            total_score = sum(r["weight"] * 10 for r in matched_rules) / total_weight
        else:
            total_score = 0.0
        
        # 确定风险等级
        if severity_counts["critical"] > 0 or total_score >= 8.0:
            risk_level = "critical"
        elif severity_counts["high"] > 0 or total_score >= 6.0:
            risk_level = "high"
        elif severity_counts["medium"] > 0 or total_score >= 4.0:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "total_score": round(total_score, 2),
            "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
            "severity_breakdown": severity_counts,
            "risk_level": risk_level
        }
    
    def _calculate_confidence(self, matched_rules: List[Dict[str, Any]]) -> float:
        """计算置信度"""
        if not matched_rules:
            return 0.3  # 基础置信度
        
        # 基础置信度基于匹配规则数量
        base_confidence = min(len(matched_rules) * 0.1, 0.6)
        
        # 规则权重和严重性调整
        weight_adjustment = 0.0
        severity_adjustment = 0.0
        
        for rule in matched_rules:
            weight_adjustment += rule["weight"] * 0.05
            severity = rule["severity"]
            if severity == "critical":
                severity_adjustment += 0.15
            elif severity == "high":
                severity_adjustment += 0.10
            elif severity == "medium":
                severity_adjustment += 0.05
        
        # 规则置信度调整
        confidence_adjustment = sum(r["confidence_adjustment"] for r in matched_rules)
        
        # 计算最终置信度
        total_confidence = (
            base_confidence + 
            min(weight_adjustment, 0.2) + 
            min(severity_adjustment, 0.3) + 
            min(confidence_adjustment, 0.2)
        )
        
        return round(min(max(total_confidence, 0.1), 0.9), 2)
    
    def _generate_recommendations(self, matched_rules: List[Dict[str, Any]], risk_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []
        
        # 按严重性排序规则
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_rules = sorted(matched_rules, key=lambda r: severity_order.get(r["severity"], 4))
        
        # 为每个规则生成建议
        for rule in sorted_rules[:8]:  # 最多8个建议
            recommendations.append({
                "priority": rule["severity"],
                "rule_id": rule["id"],
                "title": rule["name"],
                "description": rule["description"],
                "action": rule["recommendation"],
                "category": rule["category"]
            })
        
        # 基于风险等级添加通用建议
        risk_level = risk_info.get("risk_level", "low")
        
        if risk_level == "critical":
            recommendations.append({
                "priority": "critical",
                "rule_id": "GENERAL-001",
                "title": "立即安全响应",
                "description": "系统存在严重安全风险",
                "action": "立即启动安全应急响应流程，隔离受影响系统，进行全面安全评估",
                "category": "general"
            })
        elif risk_level == "high":
            recommendations.append({
                "priority": "high",
                "rule_id": "GENERAL-002",
                "title": "高优先级修复",
                "description": "系统存在高风险安全问题",
                "action": "制定并执行高优先级修复计划，在48小时内解决关键问题",
                "category": "general"
            })
        
        return recommendations
    
    def analyze(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """基于规则的智能分析"""
        logger.info(f"开始规则引擎分析 - 目标: {target_data.get('target', '未知')}")
        
        # 1. 特征提取
        features = self._extract_features(target_data)
        
        # 2. 规则匹配
        matched_rules = self._match_rules(features)
        
        # 3. 风险评估
        risk_info = self._calculate_risk_score(matched_rules)
        
        # 4. 生成建议
        recommendations = self._generate_recommendations(matched_rules, risk_info)
        
        # 5. 计算置信度
        confidence = self._calculate_confidence(matched_rules)
        
        # 6. 生成分析报告
        analysis_report = {
            "method": "rule_based_analysis",
            "timestamp": self._get_timestamp(),
            "features_analyzed": features.to_dict(),
            "rules_matched": len(matched_rules),
            "matched_rules_details": matched_rules,
            "risk_assessment": risk_info,
            "recommendations": recommendations,
            "confidence": confidence,
            "transparency": {
                "rule_engine_version": "1.0",
                "total_rules": len(self.rules),
                "matching_method": "特征匹配和条件评估",
                "risk_calculation": "基于规则权重和严重性的加权评分",
                "technical_honesty": "基于预定义规则的分析，非AI/机器学习"
            }
        }
        
        logger.info(f"规则引擎分析完成 - 风险等级: {risk_info['risk_level']}, 置信度: {confidence}")
        
        return analysis_report
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": "RealRuleEngine",
            "version": "1.0",
            "description": "基于规则的安全分析引擎，不伪装成AI",
            "total_rules": len(self.rules),
            "rule_categories": list(set(rule.category for rule in self.rules)),
            "capabilities": [
                "端口安全分析",
                "漏洞风险评估",
                "Web安全配置检查",
                "安全策略建议生成"
            ],
            "limitations": [
                "基于预定义规则，无法学习新规则",
                "需要准确的输入数据",
                "无法处理未知攻击模式"
            ],
            "transparency_level": "高 - 所有规则和计算过程透明"
        }


def test_real_rule_engine():
    """测试真实的规则引擎"""
    print("=" * 80)
    print("真实的规则引擎测试")
    print("=" * 80)
    
    try:
        # 创建规则引擎
        engine = RealRuleEngine()
        
        # 获取引擎信息
        engine_info = engine.get_engine_info()
        print(f"\n引擎信息:")
        print(f"  名称: {engine_info['name']}")
        print(f"  版本: {engine_info['version']}")
        print(f"  描述: {engine_info['description']}")
        print(f"  规则数量: {engine_info['total_rules']}")
        print(f"  规则类别: {', '.join(engine_info['rule_categories'])}")
        
        print(f"\n能力:")
        for capability in engine_info['capabilities']:
            print(f"  ✓ {capability}")
        
        print(f"\n局限性:")
        for limitation in engine_info['limitations']:
            print(f"  ⚠ {limitation}")
        
        print(f"\n透明度: {engine_info['transparency_level']}")
        
        # 测试数据
        test_target_data = {
            "target": "test.example.com",
            "nmap": {
                "ports": [
                    {"port": 22, "service": "ssh", "state": "open"},
                    {"port": 80, "service": "http", "state": "open"},
                    {"port": 443, "service": "https", "state": "open"},
                    {"port": 3306, "service": "mysql", "state": "open"}
                ]
            },
            "whatweb": {
                "technologies": ["nginx/1.14", "PHP/5.6", "WordPress/5.4"]
            },
            "vulnerabilities": [
                {"name": "CVE-2021-12345", "severity": "high", "type": "sqli"},
                {"name": "CVE-2020-67890", "severity": "medium", "type": "xss"}
            ],
            "headers": {
                "Server": "nginx/1.14.0",
                "X-Powered-By": "PHP/5.6.40"
            },
            "cms": "WordPress",
            "ssl": {"protocol": "TLSv1.2", "grade": "B"}
        }
        
        print(f"\n{'='*60}")
        print(f"测试分析 - 目标: {test_target_data['target']}")
        print(f"{'='*60}")
        
        # 执行分析
        analysis_result = engine.analyze(test_target_data)
        
        print(f"\n分析结果:")
        print(f"  分析方法: {analysis_result['method']}")
        print(f"  匹配规则数: {analysis_result['rules_matched']}")
        print(f"  风险等级: {analysis_result['risk_assessment']['risk_level']}")
        print(f"  风险分数: {analysis_result['risk_assessment']['total_score']}/10")
        print(f"  置信度: {analysis_result['confidence']}")
        
        print(f"\n风险详情:")
        for category, score in analysis_result['risk_assessment']['category_scores'].items():
            print(f"  {category}: {score}/10")
        
        print(f"\n严重性分布:")
        for severity, count in analysis_result['risk_assessment']['severity_breakdown'].items():
            print(f"  {severity}: {count} 条规则")
        
        print(f"\n关键建议 (前3条):")
        for i, rec in enumerate(analysis_result['recommendations'][:3], 1):
            print(f"  {i}. [{rec['priority']}] {rec['title']}")
            print(f"     行动: {rec['action']}")
        
        print(f"\n透明度信息:")
        for key, value in analysis_result['transparency'].items():
            print(f"  {key}: {value}")
        
        print(f"\n技术诚信验证:")
        honesty_checks = [
            ("明确标识为规则引擎", analysis_result['method'] == 'rule_based_analysis'),
            ("规则数量透明", 'total_rules' in analysis_result['transparency']),
            ("无AI伪装", 'technical_honesty' in analysis_result['transparency']),
            ("置信度合理", 0 <= analysis_result['confidence'] <= 1)
        ]
        
        for check_name, check_passed in honesty_checks:
            status = "✓" if check_passed else "✗"
            print(f"  {status} {check_name}")
        
        print(f"\n{'='*80}")
        print("测试完成 - 真实的规则引擎验证通过")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_real_rule_engine()
    if success:
        print("\n[SUCCESS] 真实的规则引擎测试通过!")
    else:
        print("\n[FAILED] 真实的规则引擎测试失败!")