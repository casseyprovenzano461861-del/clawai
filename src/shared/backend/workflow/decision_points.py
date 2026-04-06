# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI决策点系统
包含渗透测试工作流中的关键AI决策点
"""

import json
import time
from typing import Dict, Any, List, Optional
from enum import Enum


class DecisionType(Enum):
    """决策类型枚举"""
    TARGET_ANALYSIS = "target_analysis"
    TOOL_SELECTION = "tool_selection"
    ATTACK_PATH = "attack_path"
    RISK_ASSESSMENT = "risk_assessment"
    STAGE_GUIDANCE = "stage_guidance"
    CONTINUATION_DECISION = "continuation_decision"


class DecisionConfidence(Enum):
    """决策置信度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DecisionOutcome(Enum):
    """决策结果"""
    PROCEED = "proceed"
    ADJUST = "adjust"
    PAUSE = "pause"
    STOP = "stop"
    ESCALATE = "escalate"


class DecisionPoint:
    """决策点基类"""
    
    def __init__(self, decision_type: DecisionType, description: str):
        self.decision_type = decision_type
        self.description = description
        self.timestamp = time.time()
        self.input_data = {}
        self.output_data = {}
        self.confidence = DecisionConfidence.MEDIUM
        self.outcome = DecisionOutcome.PROCEED
        self.reasoning = ""
        self.alternatives = []
        self.recommendations = []
    
    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """做出决策（子类需要重写）"""
        self.input_data = context
        raise NotImplementedError("子类必须实现此方法")
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """获取决策摘要"""
        return {
            "decision_type": self.decision_type.value,
            "description": self.description,
            "timestamp": self.timestamp,
            "confidence": self.confidence.value,
            "outcome": self.outcome.value,
            "reasoning": self.reasoning,
            "recommendations": self.recommendations,
            "alternatives": self.alternatives
        }


class TargetAnalysisDecision(DecisionPoint):
    """目标分析决策点"""
    
    def __init__(self):
        super().__init__(
            decision_type=DecisionType.TARGET_ANALYSIS,
            description="分析渗透测试目标，确定最佳攻击入口和策略"
        )
    
    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析目标并做出决策"""
        target = context.get("target", "")
        reconnaissance_data = context.get("reconnaissance_data", {})
        
        print(f"[TARGET] 目标分析决策点 - 分析目标: {target}")
        
        # 分析目标类型
        target_type = self._analyze_target_type(target)
        
        # 分析攻击面
        attack_surface = self._analyze_attack_surface(reconnaissance_data)
        
        # 确定攻击入口点
        entry_points = self._identify_entry_points(target_type, attack_surface)
        
        # 评估目标难度
        difficulty_assessment = self._assess_difficulty(target_type, attack_surface)
        
        # 生成攻击策略
        attack_strategy = self._generate_attack_strategy(target_type, entry_points, difficulty_assessment)
        
        # 设置决策结果
        self.confidence = self._calculate_confidence(attack_surface)
        self.outcome = DecisionOutcome.PROCEED if entry_points else DecisionOutcome.STOP
        self.reasoning = self._generate_reasoning(target_type, attack_surface, entry_points)
        self.recommendations = self._generate_recommendations(attack_strategy)
        self.alternatives = self._generate_alternatives(target_type, attack_surface)
        
        # 构建输出数据
        self.output_data = {
            "target_analysis": {
                "target": target,
                "target_type": target_type,
                "attack_surface": attack_surface,
                "entry_points": entry_points,
                "difficulty_assessment": difficulty_assessment,
                "attack_strategy": attack_strategy,
                "analysis_timestamp": time.time()
            },
            "decision_summary": self.get_decision_summary()
        }
        
        return self.output_data
    
    def _analyze_target_type(self, target: str) -> Dict[str, Any]:
        """分析目标类型"""
        target_types = {
            "web_application": {
                "indicators": [".com", ".org", ".net", "http://", "https://"],
                "description": "Web应用程序",
                "attack_vectors": ["SQL注入", "XSS", "CSRF", "文件上传"]
            },
            "network_host": {
                "indicators": ["192.168.", "10.", "172.16."],
                "description": "网络主机",
                "attack_vectors": ["端口扫描", "服务利用", "漏洞扫描"]
            },
            "api_endpoint": {
                "indicators": ["/api/", "/v1/", "/graphql", "/rest"],
                "description": "API端点",
                "attack_vectors": ["参数篡改", "认证绕过", "数据泄露"]
            },
            "mobile_app": {
                "indicators": ["app.", "mobile.", "android", "ios"],
                "description": "移动应用程序",
                "attack_vectors": ["逆向工程", "API滥用", "本地存储"]
            }
        }
        
        detected_types = []
        for type_name, type_info in target_types.items():
            for indicator in type_info["indicators"]:
                if indicator in target.lower():
                    detected_types.append({
                        "type": type_name,
                        "description": type_info["description"],
                        "confidence": "high" if indicator in [".com", "http://", "https://"] else "medium"
                    })
                    break
        
        if not detected_types:
            detected_types.append({
                "type": "unknown",
                "description": "未知目标类型",
                "confidence": "low"
            })
        
        return {
            "primary_type": detected_types[0] if detected_types else {"type": "unknown", "description": "未知"},
            "all_types": detected_types,
            "analysis_method": "基于URL/目标字符串的模式匹配"
        }
    
    def _analyze_attack_surface(self, reconnaissance_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析攻击面"""
        attack_surface = {
            "network_exposure": {
                "open_ports": [],
                "services": [],
                "protocols": []
            },
            "web_application": {
                "technologies": [],
                "endpoints": [],
                "authentication_methods": []
            },
            "vulnerability_indicators": {
                "known_vulnerabilities": [],
                "security_misconfigurations": [],
                "information_leakage": []
            },
            "defense_mechanisms": {
                "waf_detected": False,
                "ids_ips_present": False,
                "firewall_rules": []
            }
        }
        
        # 从侦察数据中提取信息
        if reconnaissance_data:
            # 提取端口信息
            if "port_scan" in reconnaissance_data:
                port_scan = reconnaissance_data["port_scan"]
                attack_surface["network_exposure"]["open_ports"] = port_scan.get("open_ports", [])
                attack_surface["network_exposure"]["services"] = [
                    f"{p.get('port', '')}/{p.get('service', '')}" 
                    for p in port_scan.get("open_ports", [])
                ]
            
            # 提取技术栈信息
            if "web_app_identification" in reconnaissance_data:
                web_app = reconnaissance_data["web_app_identification"]
                attack_surface["web_application"]["technologies"] = web_app.get("technologies", [])
            
            # 提取子域名信息
            if "subdomain_discovery" in reconnaissance_data:
                subdomains = reconnaissance_data["subdomain_discovery"]
                attack_surface["web_application"]["endpoints"] = [
                    sd.get("subdomain", "") for sd in subdomains.get("subdomains", [])
                ]
        
        # 计算攻击面评分
        attack_surface_score = self._calculate_attack_surface_score(attack_surface)
        attack_surface["score"] = attack_surface_score
        attack_surface["rating"] = "low" if attack_surface_score < 3 else "medium" if attack_surface_score < 7 else "high"
        
        return attack_surface
    
    def _identify_entry_points(self, target_type: Dict[str, Any], attack_surface: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别攻击入口点"""
        entry_points = []
        
        primary_type = target_type.get("primary_type", {}).get("type", "unknown")
        
        if primary_type == "web_application":
            # Web应用入口点
            entry_points.extend([
                {
                    "type": "authentication",
                    "description": "认证系统",
                    "target": "登录页面",
                    "attack_vectors": ["暴力破解", "SQL注入", "会话劫持"],
                    "confidence": "medium"
                },
                {
                    "type": "input_validation",
                    "description": "用户输入点",
                    "target": "表单和参数",
                    "attack_vectors": ["XSS", "命令注入", "文件包含"],
                    "confidence": "high"
                },
                {
                    "type": "file_upload",
                    "description": "文件上传功能",
                    "target": "上传端点",
                    "attack_vectors": ["恶意文件上传", "MIME类型绕过"],
                    "confidence": "medium"
                }
            ])
        
        elif primary_type == "network_host":
            # 网络主机入口点
            open_ports = attack_surface.get("network_exposure", {}).get("open_ports", [])
            for port_info in open_ports[:5]:  # 最多5个端口
                entry_points.append({
                    "type": "network_service",
                    "description": f"端口 {port_info.get('port', '')} 服务",
                    "target": f"{port_info.get('service', '未知服务')}",
                    "attack_vectors": self._get_service_attack_vectors(port_info.get('service', '')),
                    "confidence": "high" if port_info.get('state') == 'open' else "low"
                })
        
        # 添加通用入口点
        entry_points.append({
            "type": "social_engineering",
            "description": "社会工程学",
            "target": "人员目标",
            "attack_vectors": ["钓鱼攻击", "凭证窃取", "物理访问"],
            "confidence": "medium"
        })
        
        return entry_points
    
    def _assess_difficulty(self, target_type: Dict[str, Any], attack_surface: Dict[str, Any]) -> Dict[str, Any]:
        """评估目标难度"""
        difficulty_score = 0
        factors = []
        
        # 目标类型难度
        primary_type = target_type.get("primary_type", {}).get("type", "unknown")
        type_difficulty = {
            "web_application": 5,
            "network_host": 6,
            "api_endpoint": 7,
            "mobile_app": 8,
            "unknown": 10
        }
        difficulty_score += type_difficulty.get(primary_type, 10)
        factors.append(f"目标类型({primary_type}): {type_difficulty.get(primary_type, 10)}分")
        
        # 攻击面评分影响
        attack_surface_score = attack_surface.get("score", 0)
        if attack_surface_score > 7:
            difficulty_score -= 3  # 攻击面大，难度降低
            factors.append(f"攻击面大: -3分")
        elif attack_surface_score < 3:
            difficulty_score += 3  # 攻击面小，难度增加
            factors.append(f"攻击面小: +3分")
        
        # 防御机制影响
        defense_mechanisms = attack_surface.get("defense_mechanisms", {})
        if defense_mechanisms.get("waf_detected"):
            difficulty_score += 2
            factors.append("WAF检测: +2分")
        if defense_mechanisms.get("ids_ips_present"):
            difficulty_score += 2
            factors.append("IDS/IPS检测: +2分")
        
        # 确定难度等级
        if difficulty_score <= 5:
            difficulty_level = "容易"
        elif difficulty_score <= 8:
            difficulty_level = "中等"
        elif difficulty_score <= 12:
            difficulty_level = "困难"
        else:
            difficulty_level = "极难"
        
        return {
            "score": difficulty_score,
            "level": difficulty_level,
            "factors": factors,
            "assessment_method": "基于目标类型、攻击面和防御机制的加权评分"
        }
    
    def _generate_attack_strategy(self, target_type: Dict[str, Any], entry_points: List[Dict[str, Any]], 
                                 difficulty_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """生成攻击策略"""
        primary_type = target_type.get("primary_type", {}).get("type", "unknown")
        difficulty_level = difficulty_assessment.get("level", "中等")
        
        strategies = {
            "web_application": {
                "easy": {
                    "approach": "直接攻击",
                    "focus": "自动化漏洞扫描和利用",
                    "tools": ["sqlmap", "nuclei", "nikto"],
                    "time_estimate": "1-2小时"
                },
                "medium": {
                    "approach": "组合攻击",
                    "focus": "手动测试结合自动化工具",
                    "tools": ["Burp Suite", "OWASP ZAP", "custom scripts"],
                    "time_estimate": "4-8小时"
                },
                "hard": {
                    "approach": "深度渗透",
                    "focus": "高级技术和绕过防御",
                    "tools": ["高级漏洞利用", "自定义载荷", "社会工程学"],
                    "time_estimate": "1-3天"
                }
            },
            "network_host": {
                "easy": {
                    "approach": "标准网络攻击",
                    "focus": "已知漏洞利用",
                    "tools": ["metasploit", "nmap scripts", "exploit-db"],
                    "time_estimate": "2-4小时"
                },
                "medium": {
                    "approach": "针对性攻击",
                    "focus": "服务特定漏洞",
                    "tools": ["漏洞扫描器", "服务枚举工具", "凭证攻击"],
                    "time_estimate": "6-12小时"
                },
                "hard": {
                    "approach": "高级网络渗透",
                    "focus": "零日漏洞和横向移动",
                    "tools": ["高级C2框架", "自定义漏洞利用", "网络流量分析"],
                    "time_estimate": "2-5天"
                }
            }
        }
        
        # 获取策略
        type_strategies = strategies.get(primary_type, strategies["web_application"])
        strategy = type_strategies.get(difficulty_level.lower(), type_strategies["medium"])
        
        # 根据入口点调整策略
        if entry_points:
            primary_entry_point = entry_points[0]
            strategy["primary_entry_point"] = primary_entry_point
        
        return strategy
    
    def _calculate_confidence(self, attack_surface: Dict[str, Any]) -> DecisionConfidence:
        """计算决策置信度"""
        attack_surface_score = attack_surface.get("score", 0)
        
        if attack_surface_score >= 8:
            return DecisionConfidence.VERY_HIGH
        elif attack_surface_score >= 5:
            return DecisionConfidence.HIGH
        elif attack_surface_score >= 3:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW
    
    def _generate_reasoning(self, target_type: Dict[str, Any], attack_surface: Dict[str, Any], 
                           entry_points: List[Dict[str, Any]]) -> str:
        """生成决策推理"""
        primary_type = target_type.get("primary_type", {}).get("description", "未知目标")
        attack_surface_rating = attack_surface.get("rating", "未知")
        entry_point_count = len(entry_points)
        
        reasoning = f"目标分析完成。识别为{primary_type}，攻击面评级为{attack_surface_rating}。"
        reasoning += f"发现了{entry_point_count}个潜在攻击入口点。"
        
        if entry_point_count > 0:
            primary_entry = entry_points[0]
            reasoning += f"主要入口点: {primary_entry['description']}，攻击向量: {', '.join(primary_entry['attack_vectors'][:2])}。"
        
        return reasoning
    
    def _generate_recommendations(self, attack_strategy: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = [
            f"采用{attack_strategy.get('approach', '标准')}攻击方法",
            f"重点攻击: {attack_strategy.get('focus', '漏洞利用')}",
            f"预计时间: {attack_strategy.get('time_estimate', '未知')}",
            "记录所有测试步骤和结果",
            "遵守授权范围和法律法规"
        ]
        
        if "tools" in attack_strategy:
            recommendations.append(f"推荐工具: {', '.join(attack_strategy['tools'][:3])}")
        
        return recommendations
    
    def _generate_alternatives(self, target_type: Dict[str, Any], attack_surface: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成替代方案"""
        alternatives = []
        
        primary_type = target_type.get("primary_type", {}).get("type", "unknown")
        
        if primary_type == "web_application":
            alternatives.append({
                "description": "API接口测试",
                "rationale": "现代Web应用通常有API接口，可能包含不同的漏洞",
                "approach": "专注于API端点的测试",
                "tools": ["Postman", "Burp Suite", "自定义API测试脚本"]
            })
        
        alternatives.append({
            "description": "社会工程学攻击",
            "rationale": "人为因素往往是安全链中最薄弱的环节",
            "approach": "针对人员的攻击测试",
            "tools": ["钓鱼工具包", "物理安全测试", "电话社会工程学"]
        })
        
        alternatives.append({
            "description": "供应链攻击",
            "rationale": "通过第三方组件或供应商进行攻击",
            "approach": "分析目标依赖的第三方服务",
            "tools": ["依赖分析工具", "供应链映射", "第三方漏洞数据库"]
        })
        
        return alternatives
    
    def _calculate_attack_surface_score(self, attack_surface: Dict[str, Any]) -> int:
        """计算攻击面评分"""
        score = 0
        
        # 网络暴露
        network_exposure = attack_surface.get("network_exposure", {})
        open_ports = len(network_exposure.get("open_ports", []))
        score += min(open_ports, 5)  # 最多5分
        
        # Web应用技术栈
        web_app = attack_surface.get("web_application", {})
        technologies = len(web_app.get("technologies", []))
        score += min(technologies, 3)  # 最多3分
        
        # 端点数量
        endpoints = len(web_app.get("endpoints", []))
        score += min(endpoints, 3)  # 最多3分
        
        # 漏洞指示器
        vuln_indicators = attack_surface.get("vulnerability_indicators", {})
        known_vulns = len(vuln_indicators.get("known_vulnerabilities", []))
        score += min(known_vulns, 4)  # 最多4分
        
        # 防御机制（反向评分）
        defense = attack_surface.get("defense_mechanisms", {})
        if defense.get("waf_detected"):
            score -= 2
        if defense.get("ids_ips_present"):
            score -= 2
        
        return max(0, min(score, 10))  # 确保分数在0-10之间
    
    def _get_service_attack_vectors(self, service: str) -> List[str]:
        """获取服务攻击向量"""
        service_vectors = {
            "http": ["Web攻击", "目录遍历", "文件包含"],
            "https": ["SSL/TLS攻击", "证书窃取", "中间人攻击"],
            "ssh": ["暴力破解", "密钥攻击", "版本漏洞"],
            "ftp": ["匿名访问", "明文传输", "缓冲区溢出"],
            "smtp": ["邮件欺骗", "开放中继", "用户枚举"],
            "rdp": ["暴力破解", "BlueKeep漏洞", "凭证窃取"],
            "mysql": ["SQL注入", "默认凭据", "权限提升"],
            "telnet": ["明文凭据", "会话劫持", "命令注入"]
        }
        
        service_lower = service.lower()
        for key, vectors in service_vectors.items():
            if key in service_lower:
                return vectors
        
        return ["通用网络攻击", "协议漏洞利用", "服务特定攻击"]


class ToolSelectionDecision(DecisionPoint):
    """工具选择决策点"""
    
    def __init__(self):
        super().__init__(
            decision_type=DecisionType.TOOL_SELECTION,
            description="根据当前阶段和目标选择合适的渗透测试工具"
        )
        self.available_tools = self._load_tool_inventory()
    
    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """选择工具并做出决策"""
        current_stage = context.get("current_stage", "")
        target_type = context.get("target_type", "")
        previous_results = context.get("previous_results", {})
        
        print(f"[TOOL] 工具选择决策点 - 当前阶段: {current_stage}, 目标类型: {target_type}")
        
        # 选择适合当前阶段的工具
        stage_tools = self._select_stage_tools(current_stage, target_type)
        
        # 根据历史结果调整工具选择
        adjusted_tools = self._adjust_tools_based_on_history(stage_tools, previous_results)
        
        # 评估工具有效性
        effectiveness_assessment = self._assess_tool_effectiveness(adjusted_tools, target_type)
        
        # 生成工具使用策略
        usage_strategy = self._generate_usage_strategy(adjusted_tools, current_stage)
        
        # 设置决策结果
        self.confidence = self._calculate_tool_confidence(adjusted_tools, effectiveness_assessment)
        self.outcome = DecisionOutcome.PROCEED if adjusted_tools else DecisionOutcome.ADJUST
        self.reasoning = self._generate_tool_reasoning(current_stage, adjusted_tools, effectiveness_assessment)
        self.recommendations = self._generate_tool_recommendations(usage_strategy)
        self.alternatives = self._generate_tool_alternatives(stage_tools, adjusted_tools)
        
        # 构建输出数据
        self.output_data = {
            "tool_selection": {
                "current_stage": current_stage,
                "target_type": target_type,
                "selected_tools": adjusted_tools,
                "effectiveness_assessment": effectiveness_assessment,
                "usage_strategy": usage_strategy,
                "selection_timestamp": time.time()
            },
            "decision_summary": self.get_decision_summary()
        }
        
        return self.output_data
    
    def _load_tool_inventory(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载工具清单"""
        return {
            "reconnaissance": [
                {"name": "nmap", "type": "port_scanner", "effectiveness": 9, "stealth": 6, "complexity": 5},
                {"name": "whatweb", "type": "web_tech_scanner", "effectiveness": 8, "stealth": 7, "complexity": 4},
                {"name": "sublist3r", "type": "subdomain_scanner", "effectiveness": 7, "stealth": 5, "complexity": 6},
                {"name": "theHarvester", "type": "info_gatherer", "effectiveness": 6, "stealth": 8, "complexity": 5},
                {"name": "dnsrecon", "type": "dns_scanner", "effectiveness": 7, "stealth": 6, "complexity": 6}
            ],
            "scanning": [
                {"name": "nuclei", "type": "vulnerability_scanner", "effectiveness": 9, "stealth": 4, "complexity": 6},
                {"name": "nikto", "type": "web_vuln_scanner", "effectiveness": 8, "stealth": 3, "complexity": 5},
                {"name": "wpscan", "type": "wordpress_scanner", "effectiveness": 9, "stealth": 5, "complexity": 5},
                {"name": "wafw00f", "type": "waf_detector", "effectiveness": 8, "stealth": 7, "complexity": 4},
                {"name": "skipfish", "type": "web_app_scanner", "effectiveness": 7, "stealth": 2, "complexity": 7}
            ],
            "vulnerability_analysis": [
                {"name": "sqlmap", "type": "sql_injection", "effectiveness": 9, "stealth": 3, "complexity": 7},
                {"name": "commix", "type": "command_injection", "effectiveness": 8, "stealth": 4, "complexity": 6},
                {"name": "xsstrike", "type": "xss_scanner", "effectiveness": 8, "stealth": 5, "complexity": 6},
                {"name": "ssrfmap", "type": "ssrf_scanner", "effectiveness": 7, "stealth": 6, "complexity": 7}
            ],
            "exploitation": [
                {"name": "metasploit", "type": "exploitation_framework", "effectiveness": 9, "stealth": 2, "complexity": 8},
                {"name": "sqlmap", "type": "sql_injection", "effectiveness": 9, "stealth": 3, "complexity": 7},
                {"name": "beef", "type": "xss_framework", "effectiveness": 8, "stealth": 5, "complexity": 7},
                {"name": "responder", "type": "llmnr_poisoning", "effectiveness": 7, "stealth": 4, "complexity": 6}
            ],
            "post_exploitation": [
                {"name": "mimikatz", "type": "credential_dumper", "effectiveness": 9, "stealth": 1, "complexity": 7},
                {"name": "powersploit", "type": "powershell_framework", "effectiveness": 8, "stealth": 3, "complexity": 8},
                {"name": "bloodhound", "type": "ad_analyzer", "effectiveness": 9, "stealth": 6, "complexity": 7},
                {"name": "cobaltstrike", "type": "c2_framework", "effectiveness": 10, "stealth": 8, "complexity": 9}
            ],
            "reporting": [
                {"name": "dradis", "type": "reporting_framework", "effectiveness": 8, "stealth": 10, "complexity": 5},
                {"name": "serpico", "type": "report_generator", "effectiveness": 7, "stealth": 10, "complexity": 6},
                {"name": "自定义脚本", "type": "automation", "effectiveness": 9, "stealth": 10, "complexity": 7}
            ]
        }
    
    def _select_stage_tools(self, current_stage: str, target_type: str) -> List[Dict[str, Any]]:
        """选择适合当前阶段的工具"""
        stage_tools = self.available_tools.get(current_stage, [])
        
        # 根据目标类型过滤工具
        filtered_tools = []
        for tool in stage_tools:
            # 检查工具是否适合目标类型
            if self._is_tool_suitable_for_target(tool, target_type):
                filtered_tools.append(tool)
        
        # 如果过滤后没有工具，返回原始工具
        if not filtered_tools:
            return stage_tools[:3]  # 返回前3个工具
        
        # 根据有效性排序并返回前3个
        filtered_tools.sort(key=lambda x: x.get("effectiveness", 0), reverse=True)
        return filtered_tools[:3]
    
    def _adjust_tools_based_on_history(self, stage_tools: List[Dict[str, Any]], 
                                      previous_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据历史结果调整工具选择"""
        if not previous_results:
            return stage_tools
        
        adjusted_tools = []
        
        for tool in stage_tools:
            tool_name = tool.get("name", "")
            
            # 检查该工具在历史中的表现
            tool_history = self._get_tool_history(tool_name, previous_results)
            
            if tool_history.get("success_rate", 0) >= 0.5:
                # 成功率高的工具，增加权重
                adjusted_tool = tool.copy()
                adjusted_tool["adjusted_effectiveness"] = tool.get("effectiveness", 0) * 1.2
                adjusted_tools.append(adjusted_tool)
            elif tool_history.get("failure_reasons"):
                # 有失败历史的工具，降低权重但可能仍保留
                adjusted_tool = tool.copy()
                adjusted_tool["adjusted_effectiveness"] = tool.get("effectiveness", 0) * 0.8
                adjusted_tool["notes"] = f"历史失败原因: {', '.join(tool_history['failure_reasons'][:2])}"
                adjusted_tools.append(adjusted_tool)
            else:
                # 无历史记录的工具，保持原样
                adjusted_tools.append(tool)
        
        # 根据调整后的有效性重新排序
        adjusted_tools.sort(key=lambda x: x.get("adjusted_effectiveness", x.get("effectiveness", 0)), reverse=True)
        return adjusted_tools[:3]
    
    def _assess_tool_effectiveness(self, selected_tools: List[Dict[str, Any]], target_type: str) -> Dict[str, Any]:
        """评估工具有效性"""
        effectiveness_scores = []
        stealth_scores = []
        complexity_scores = []
        
        for tool in selected_tools:
            effectiveness_scores.append(tool.get("adjusted_effectiveness", tool.get("effectiveness", 0)))
            stealth_scores.append(tool.get("stealth", 5))
            complexity_scores.append(tool.get("complexity", 5))
        
        avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
        avg_stealth = sum(stealth_scores) / len(stealth_scores) if stealth_scores else 0
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        # 评估整体有效性
        if avg_effectiveness >= 8:
            overall_rating = "优秀"
        elif avg_effectiveness >= 6:
            overall_rating = "良好"
        elif avg_effectiveness >= 4:
            overall_rating = "一般"
        else:
            overall_rating = "较差"
        
        return {
            "average_effectiveness": avg_effectiveness,
            "average_stealth": avg_stealth,
            "average_complexity": avg_complexity,
            "overall_rating": overall_rating,
            "tool_count": len(selected_tools),
            "assessment_method": "基于工具历史数据和目标类型的加权评估"
        }
    
    def _generate_usage_strategy(self, selected_tools: List[Dict[str, Any]], current_stage: str) -> Dict[str, Any]:
        """生成工具使用策略"""
        strategy = {
            "execution_order": [],
            "parallel_execution": False,
            "resource_allocation": {},
            "fallback_plan": []
        }
        
        # 确定执行顺序（根据复杂度和有效性）
        sorted_tools = sorted(selected_tools, 
                            key=lambda x: (x.get("complexity", 0), -x.get("adjusted_effectiveness", x.get("effectiveness", 0))))
        
        for i, tool in enumerate(sorted_tools):
            strategy["execution_order"].append({
                "step": i + 1,
                "tool": tool["name"],
                "type": tool["type"],
                "purpose": self._get_tool_purpose(tool["name"], current_stage),
                "estimated_time": f"{self._estimate_tool_time(tool)}分钟"
            })
        
        # 确定是否并行执行
        if len(selected_tools) > 1 and current_stage in ["reconnaissance", "scanning"]:
            strategy["parallel_execution"] = True
            strategy["parallel_groups"] = self._create_parallel_groups(selected_tools)
        
        # 资源分配
        strategy["resource_allocation"] = {
            "network_bandwidth": "中等" if len(selected_tools) <= 2 else "高",
            "computational_power": "中等" if avg_complexity <= 6 else "高",
            "memory_usage": "中等",
            "recommended_parallel_tasks": min(len(selected_tools), 3)
        }
        
        # 备用计划
        strategy["fallback_plan"] = [
            "如果主要工具失败，尝试替代工具",
            "调整工具参数和配置",
            "手动测试作为最后手段",
            "切换到不同攻击向量"
        ]
        
        return strategy
    
    def _calculate_tool_confidence(self, selected_tools: List[Dict[str, Any]], 
                                  effectiveness_assessment: Dict[str, Any]) -> DecisionConfidence:
        """计算工具选择置信度"""
        avg_effectiveness = effectiveness_assessment.get("average_effectiveness", 0)
        overall_rating = effectiveness_assessment.get("overall_rating", "")
        
        if avg_effectiveness >= 8 and overall_rating == "优秀":
            return DecisionConfidence.VERY_HIGH
        elif avg_effectiveness >= 6 and overall_rating in ["优秀", "良好"]:
            return DecisionConfidence.HIGH
        elif avg_effectiveness >= 4:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW
    
    def _generate_tool_reasoning(self, current_stage: str, selected_tools: List[Dict[str, Any]], 
                                effectiveness_assessment: Dict[str, Any]) -> str:
        """生成工具选择推理"""
        tool_names = [tool["name"] for tool in selected_tools]
        overall_rating = effectiveness_assessment.get("overall_rating", "")
        avg_effectiveness = effectiveness_assessment.get("average_effectiveness", 0)
        
        reasoning = f"为{current_stage}阶段选择了{len(selected_tools)}个工具: {', '.join(tool_names)}。"
        reasoning += f"工具组合整体评级为{overall_rating}(平均有效性: {avg_effectiveness:.1f}/10)。"
        
        if selected_tools:
            primary_tool = selected_tools[0]
            reasoning += f"主要工具{primary_tool['name']}适用于{primary_tool['type']}任务。"
        
        return reasoning
    
    def _generate_tool_recommendations(self, usage_strategy: Dict[str, Any]) -> List[str]:
        """生成工具使用建议"""
        recommendations = [
            "按照建议的执行顺序使用工具",
            "监控工具执行结果并及时调整策略",
            "记录工具输出和发现的问题"
        ]
        
        if usage_strategy.get("parallel_execution"):
            recommendations.append("利用并行执行提高效率")
        
        recommendations.append(f"资源分配: {usage_strategy.get('resource_allocation', {}).get('recommended_parallel_tasks', 1)}个并行任务")
        
        return recommendations
    
    def _generate_tool_alternatives(self, stage_tools: List[Dict[str, Any]], 
                                   selected_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成工具替代方案"""
        alternatives = []
        selected_names = [tool["name"] for tool in selected_tools]
        
        # 寻找未选中的替代工具
        for tool in stage_tools:
            if tool["name"] not in selected_names:
                alternatives.append({
                    "tool": tool["name"],
                    "type": tool["type"],
                    "effectiveness": tool["effectiveness"],
                    "use_case": f"作为{selected_tools[0]['name'] if selected_tools else '主要工具'}的替代",
                    "rationale": "在某些场景下可能更有效"
                })
        
        # 添加通用替代方案
        alternatives.append({
            "tool": "手动测试",
            "type": "通用",
            "effectiveness": 7,
            "use_case": "自动化工具失败时",
            "rationale": "人类智能可以识别自动化工具可能错过的问题"
        })
        
        alternatives.append({
            "tool": "自定义脚本",
            "type": "针对性",
            "effectiveness": 8,
            "use_case": "特定目标环境",
            "rationale": "针对特定环境定制的脚本通常更有效"
        })
        
        return alternatives[:3]  # 返回前3个替代方案
    
    def _is_tool_suitable_for_target(self, tool: Dict[str, Any], target_type: str) -> bool:
        """检查工具是否适合目标类型"""
        tool_name = tool.get("name", "").lower()
        
        # 工具与目标类型的映射
        target_tool_mapping = {
            "web_application": ["nmap", "whatweb", "nikto", "sqlmap", "nuclei", "xsstrike"],
            "network_host": ["nmap", "metasploit", "responder"],
            "api_endpoint": ["postman", "burp", "自定义脚本"],
            "mobile_app": ["apktool", "jadx", "frida"]
        }
        
        for target, tools in target_tool_mapping.items():
            if target in target_type.lower():
                return any(t in tool_name for t in tools)
        
        return True  # 如果不确定，默认返回True
    
    def _get_tool_history(self, tool_name: str, previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """获取工具历史表现"""
        history = {
            "success_rate": 0,
            "usage_count": 0,
            "failure_reasons": []
        }
        
        # 在实际实现中，这里会查询历史数据库
        # 这里模拟一些历史数据
        if "previous_stages" in previous_results:
            for stage in previous_results["previous_stages"]:
                if "tools_used" in stage:
                    if tool_name in stage["tools_used"]:
                        history["usage_count"] += 1
                        if stage.get("success", False):
                            history["success_rate"] += 1
        
        if history["usage_count"] > 0:
            history["success_rate"] /= history["usage_count"]
        
        # 模拟一些失败原因
        if tool_name == "sqlmap" and history["usage_count"] > 0:
            history["failure_reasons"] = ["WAF阻止", "目标已修复"]
        elif tool_name == "nmap" and history["usage_count"] > 0:
            history["failure_reasons"] = ["防火墙过滤", "网络限制"]
        
        return history
    
    def _get_tool_purpose(self, tool_name: str, current_stage: str) -> str:
        """获取工具用途"""
        purpose_map = {
            "nmap": "端口扫描和服务发现",
            "sqlmap": "SQL注入漏洞检测和利用",
            "metasploit": "漏洞利用和后期控制",
            "nikto": "Web服务器漏洞扫描",
            "whatweb": "Web技术栈识别",
            "nuclei": "快速漏洞扫描和验证",
            "mimikatz": "Windows凭据提取",
            "bloodhound": "Active Directory关系分析"
        }
        
        return purpose_map.get(tool_name, f"{current_stage}阶段通用工具")
    
    def _estimate_tool_time(self, tool: Dict[str, Any]) -> int:
        """估算工具执行时间"""
        complexity = tool.get("complexity", 5)
        effectiveness = tool.get("effectiveness", 5)
        
        # 复杂度越高，时间越长；有效性越高，时间可能越短（因为更高效）
        base_time = complexity * 2
        effectiveness_adjustment = (10 - effectiveness) * 0.5
        
        estimated_time = base_time + effectiveness_adjustment
        return int(estimated_time)
    
    def _create_parallel_groups(self, tools: List[Dict[str, Any]]) -> List[List[str]]:
        """创建并行执行组"""
        if len(tools) <= 2:
            return [[tool["name"] for tool in tools]]
        
        # 根据资源需求分组（简单的启发式方法）
        high_resource_tools = [t for t in tools if t.get("complexity", 0) >= 7]
        medium_resource_tools = [t for t in tools if 4 <= t.get("complexity", 0) < 7]
        low_resource_tools = [t for t in tools if t.get("complexity", 0) < 4]
        
        groups = []
        
        # 高资源工具单独执行
        for tool in high_resource_tools:
            groups.append([tool["name"]])
        
        # 中低资源工具可以并行
        if medium_resource_tools or low_resource_tools:
            parallel_group = [t["name"] for t in medium_resource_tools + low_resource_tools]
            if parallel_group:
                groups.append(parallel_group[:3])  # 最多3个并行
        
        return groups


class AttackPathDecision(DecisionPoint):
    """攻击路径决策点"""
    
    def __init__(self):
        super().__init__(
            decision_type=DecisionType.ATTACK_PATH,
            description="规划从初始访问到目标达成的攻击路径"
        )
    
    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """规划攻击路径并做出决策"""
        entry_points = context.get("entry_points", [])
        target_objectives = context.get("target_objectives", ["获取系统控制权"])
        constraints = context.get("constraints", {})
        
        print(f"[PATH] 攻击路径决策点 - 入口点: {len(entry_points)}个, 目标: {target_objectives}")
        
        # 生成攻击路径选项
        attack_paths = self._generate_attack_paths(entry_points, target_objectives, constraints)
        
        # 评估路径风险
        risk_assessments = self._assess_path_risks(attack_paths)
        
        # 选择最佳路径
        best_path = self._select_best_path(attack_paths, risk_assessments)
        
        # 生成详细执行计划
        execution_plan = self._generate_execution_plan(best_path, constraints)
        
        # 设置决策结果
        self.confidence = self._calculate_path_confidence(best_path, risk_assessments)
        self.outcome = DecisionOutcome.PROCEED if best_path else DecisionOutcome.ADJUST
        self.reasoning = self._generate_path_reasoning(best_path, risk_assessments)
        self.recommendations = self._generate_path_recommendations(execution_plan)
        self.alternatives = self._generate_path_alternatives(attack_paths, best_path)
        
        # 构建输出数据
        self.output_data = {
            "attack_path": {
                "available_paths": attack_paths,
                "risk_assessments": risk_assessments,
                "selected_path": best_path,
                "execution_plan": execution_plan,
                "selection_timestamp": time.time()
            },
            "decision_summary": self.get_decision_summary()
        }
        
        return self.output_data
    
    def _generate_attack_paths(self, entry_points: List[Dict[str, Any]], 
                              target_objectives: List[str], constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成攻击路径选项"""
        attack_paths = []
        
        # 为每个入口点生成路径
        for i, entry_point in enumerate(entry_points[:3]):  # 最多考虑3个入口点
            entry_type = entry_point.get("type", "")
            entry_description = entry_point.get("description", "")
            
            # 生成基于入口点的路径
            if entry_type == "authentication":
                path = self._generate_auth_based_path(entry_point, target_objectives)
            elif entry_type == "input_validation":
                path = self._generate_input_based_path(entry_point, target_objectives)
            elif entry_type == "network_service":
                path = self._generate_network_based_path(entry_point, target_objectives)
            else:
                path = self._generate_generic_path(entry_point, target_objectives)
            
            path["id"] = f"PATH-{i+1:03d}"
            path["entry_point"] = entry_description
            attack_paths.append(path)
        
        # 添加组合路径
        if len(entry_points) >= 2:
            combined_path = self._generate_combined_path(entry_points[:2], target_objectives)
            combined_path["id"] = "PATH-COMBINED"
            combined_path["entry_point"] = "组合入口点"
            attack_paths.append(combined_path)
        
        return attack_paths
    
    def _assess_path_risks(self, attack_paths: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """评估路径风险"""
        risk_assessments = {}
        
        for path in attack_paths:
            path_id = path.get("id", "")
            
            # 计算风险分数
            risk_score = 0
            risk_factors = []
            
            # 基于步骤数量
            step_count = len(path.get("steps", []))
            risk_score += min(step_count, 5)  # 最多5分
            risk_factors.append(f"步骤数量({step_count}): +{min(step_count, 5)}分")
            
            # 基于技术复杂度
            complexity = path.get("technical_complexity", 5)
            risk_score += complexity
            risk_factors.append(f"技术复杂度({complexity}/10): +{complexity}分")
            
            # 基于检测风险
            detection_risk = path.get("detection_risk", 5)
            risk_score += detection_risk
            risk_factors.append(f"检测风险({detection_risk}/10): +{detection_risk}分")
            
            # 基于时间要求
            time_requirement = path.get("estimated_time_hours", 4)
            if time_requirement > 8:
                risk_score += 3
                risk_factors.append(f"长时间要求({time_requirement}小时): +3分")
            elif time_requirement > 4:
                risk_score += 1
                risk_factors.append(f"中等时间要求({time_requirement}小时): +1分")
            
            # 确定风险等级
            if risk_score <= 10:
                risk_level = "低"
            elif risk_score <= 20:
                risk_level = "中"
            elif risk_score <= 30:
                risk_level = "高"
            else:
                risk_level = "极高"
            
            risk_assessments[path_id] = {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "success_probability": max(0, min(100, 100 - risk_score * 2)),
                "assessment_method": "基于步骤复杂度、检测风险和时间要求的加权评分"
            }
        
        return risk_assessments
    
    def _select_best_path(self, attack_paths: List[Dict[str, Any]], 
                         risk_assessments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳攻击路径"""
        if not attack_paths:
            return {}
        
        # 计算每个路径的得分
        path_scores = []
        
        for path in attack_paths:
            path_id = path.get("id", "")
            risk_assessment = risk_assessments.get(path_id, {})
            
            # 得分计算：成功概率 - 风险分数/10 + 效果分数
            success_probability = risk_assessment.get("success_probability", 50)
            effectiveness = path.get("expected_effectiveness", 5)
            
            score = success_probability + effectiveness * 5 - risk_assessment.get("risk_score", 0) / 10
            
            path_scores.append({
                "path": path,
                "score": score,
                "success_probability": success_probability,
                "risk_level": risk_assessment.get("risk_level", "中")
            })
        
        # 选择最高得分的路径
        path_scores.sort(key=lambda x: x["score"], reverse=True)
        best_path_info = path_scores[0]
        best_path = best_path_info["path"]
        
        # 添加选择理由
        best_path["selection_reason"] = (
            f"得分最高({best_path_info['score']:.1f})，成功概率{best_path_info['success_probability']}%，"
            f"风险等级{best_path_info['risk_level']}"
        )
        
        return best_path
    
    def _generate_execution_plan(self, selected_path: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细执行计划"""
        if not selected_path:
            return {}
        
        steps = selected_path.get("steps", [])
        
        execution_plan = {
            "overview": selected_path.get("description", ""),
            "total_steps": len(steps),
            "estimated_total_time": selected_path.get("estimated_time_hours", 4),
            "resource_requirements": selected_path.get("resource_requirements", {}),
            "detailed_steps": [],
            "contingency_plans": [],
            "success_criteria": selected_path.get("success_criteria", [])
        }
        
        # 详细步骤
        for i, step in enumerate(steps, 1):
            detailed_step = {
                "step_number": i,
                "action": step.get("action", ""),
                "description": step.get("description", ""),
                "tools_needed": step.get("tools", []),
                "estimated_time": step.get("estimated_time", "30分钟"),
                "success_indicators": step.get("success_indicators", ["操作完成"]),
                "failure_handling": step.get("failure_handling", "重试或转到备用方案")
            }
            execution_plan["detailed_steps"].append(detailed_step)
        
        # 应急计划
        execution_plan["contingency_plans"] = [
            "如果主要路径失败，切换到备用路径",
            "如果检测到防御响应，暂停并评估",
            "如果时间超出预期，调整攻击策略",
            "如果资源不足，优先执行关键步骤"
        ]
        
        # 添加约束考虑
        if constraints:
            execution_plan["constraints_considered"] = constraints
        
        return execution_plan
    
    def _calculate_path_confidence(self, best_path: Dict[str, Any], 
                                  risk_assessments: Dict[str, Dict[str, Any]]) -> DecisionConfidence:
        """计算路径选择置信度"""
        if not best_path:
            return DecisionConfidence.LOW
        
        path_id = best_path.get("id", "")
        risk_assessment = risk_assessments.get(path_id, {})
        
        success_probability = risk_assessment.get("success_probability", 50)
        risk_level = risk_assessment.get("risk_level", "中")
        
        if success_probability >= 80 and risk_level == "低":
            return DecisionConfidence.VERY_HIGH
        elif success_probability >= 60 and risk_level in ["低", "中"]:
            return DecisionConfidence.HIGH
        elif success_probability >= 40:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW
    
    def _generate_path_reasoning(self, best_path: Dict[str, Any], 
                                risk_assessments: Dict[str, Dict[str, Any]]) -> str:
        """生成路径选择推理"""
        if not best_path:
            return "未找到合适的攻击路径，建议调整目标或方法"
        
        path_id = best_path.get("id", "")
        risk_assessment = risk_assessments.get(path_id, {})
        
        reasoning = f"选择了攻击路径{path_id}: {best_path.get('description', '')}。"
        reasoning += f"成功概率: {risk_assessment.get('success_probability', 0)}%，"
        reasoning += f"风险等级: {risk_assessment.get('risk_level', '未知')}。"
        
        if "entry_point" in best_path:
            reasoning += f"使用入口点: {best_path['entry_point']}。"
        
        reasoning += f"预计时间: {best_path.get('estimated_time_hours', 0)}小时。"
        
        return reasoning
    
    def _generate_path_recommendations(self, execution_plan: Dict[str, Any]) -> List[str]:
        """生成路径执行建议"""
        recommendations = [
            "严格按照执行计划操作",
            "记录每个步骤的结果",
            "监控目标系统响应"
        ]
        
        if execution_plan.get("detailed_steps"):
            recommendations.append(f"总共{len(execution_plan['detailed_steps'])}个步骤，按顺序执行")
        
        if execution_plan.get("contingency_plans"):
            recommendations.append("熟悉应急计划并随时准备执行")
        
        recommendations.append(f"预计总时间: {execution_plan.get('estimated_total_time', 0)}小时")
        
        return recommendations
    
    def _generate_path_alternatives(self, attack_paths: List[Dict[str, Any]], 
                                   best_path: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成路径替代方案"""
        alternatives = []
        best_path_id = best_path.get("id", "") if best_path else ""
        
        for path in attack_paths:
            if path.get("id") != best_path_id:
                alternatives.append({
                    "path_id": path.get("id", ""),
                    "description": path.get("description", ""),
                    "entry_point": path.get("entry_point", ""),
                    "steps_count": len(path.get("steps", [])),
                    "use_case": "主要路径失败时的备用方案",
                    "rationale": "不同的攻击方法可能有更好的效果"
                })
        
        # 添加通用替代方案
        alternatives.append({
            "path_id": "MANUAL",
            "description": "手动攻击路径",
            "entry_point": "专家判断",
            "steps_count": "可变",
            "use_case": "自动化路径不适用时",
            "rationale": "人类专家可以根据实时情况调整策略"
        })
        
        return alternatives[:3]  # 返回前3个替代方案
    
    def _generate_auth_based_path(self, entry_point: Dict[str, Any], 
                                 target_objectives: List[str]) -> Dict[str, Any]:
        """生成基于认证的攻击路径"""
        return {
            "description": "通过认证系统突破的攻击路径",
            "steps": [
                {
                    "action": "密码暴力破解",
                    "description": "尝试常见密码组合",
                    "tools": ["hydra", "medusa", "patator"],
                    "estimated_time": "1小时",
                    "success_indicators": ["成功登录", "部分成功响应"]
                },
                {
                    "action": "会话劫持",
                    "description": "窃取有效会话令牌",
                    "tools": ["burp suite", "zap", "自定义脚本"],
                    "estimated_time": "2小时",
                    "success_indicators": ["获取有效会话", "成功访问受限资源"]
                },
                {
                    "action": "权限提升",
                    "description": "从普通用户提升到管理员",
                    "tools": ["漏洞利用", "配置错误利用", "社会工程学"],
                    "estimated_time": "3小时",
                    "success_indicators": ["获取管理员权限", "访问管理面板"]
                }
            ],
            "technical_complexity": 7,
            "detection_risk": 6,
            "estimated_time_hours": 6,
            "resource_requirements": {
                "computational_power": "高",
                "network_bandwidth": "中",
                "stealth_requirements": "中"
            },
            "success_criteria": [
                "获得有效凭据",
                "访问目标系统",
                "完成权限提升",
                "达成目标目标"
            ],
            "expected_effectiveness": 8
        }
    
    def _generate_input_based_path(self, entry_point: Dict[str, Any], 
                                  target_objectives: List[str]) -> Dict[str, Any]:
        """生成基于输入验证的攻击路径"""
        return {
            "description": "通过输入验证漏洞的攻击路径",
            "steps": [
                {
                    "action": "SQL注入利用",
                    "description": "利用SQL注入漏洞获取数据",
                    "tools": ["sqlmap", "自定义载荷", "手动测试"],
                    "estimated_time": "2小时",
                    "success_indicators": ["数据库访问", "数据提取"]
                },
                {
                    "action": "XSS攻击",
                    "description": "利用跨站脚本漏洞",
                    "tools": ["beef", "xsser", "手动测试"],
                    "estimated_time": "1.5小时",
                    "success_indicators": ["脚本执行", "会话窃取"]
                },
                {
                    "action": "文件包含攻击",
                    "description": "利用文件包含漏洞",
                    "tools": ["自定义脚本", "手动测试"],
                    "estimated_time": "2小时",
                    "success_indicators": ["文件读取", "代码执行"]
                }
            ],
            "technical_complexity": 8,
            "detection_risk": 5,
            "estimated_time_hours": 5.5,
            "resource_requirements": {
                "computational_power": "中",
                "network_bandwidth": "中",
                "stealth_requirements": "高"
            },
            "success_criteria": [
                "验证漏洞存在",
                "成功利用漏洞",
                "获取系统访问",
                "达成目标目标"
            ],
            "expected_effectiveness": 9
        }
    
    def _generate_network_based_path(self, entry_point: Dict[str, Any], 
                                    target_objectives: List[str]) -> Dict[str, Any]:
        """生成基于网络服务的攻击路径"""
        return {
            "description": "通过网络服务漏洞的攻击路径",
            "steps": [
                {
                    "action": "服务漏洞扫描",
                    "description": "扫描目标服务已知漏洞",
                    "tools": ["nmap", "nessus", "openvas"],
                    "estimated_time": "1小时",
                    "success_indicators": ["发现漏洞", "服务信息收集"]
                },
                {
                    "action": "漏洞利用",
                    "description": "利用发现的服务漏洞",
                    "tools": ["metasploit", "exploit-db", "自定义利用"],
                    "estimated_time": "2小时",
                    "success_indicators": ["漏洞利用成功", "获取访问权限"]
                },
                {
                    "action": "后渗透活动",
                    "description": "在目标系统上建立持久访问",
                    "tools": ["meterpreter", "powershell", "自定义脚本"],
                    "estimated_time": "2小时",
                    "success_indicators": ["持久化建立", "权限提升"]
                }
            ],
            "technical_complexity": 6,
            "detection_risk": 7,
            "estimated_time_hours": 5,
            "resource_requirements": {
                "computational_power": "高",
                "network_bandwidth": "高",
                "stealth_requirements": "低"
            },
            "success_criteria": [
                "发现可利用漏洞",
                "成功利用漏洞",
                "建立持久访问",
                "达成目标目标"
            ],
            "expected_effectiveness": 7
        }
    
    def _generate_generic_path(self, entry_point: Dict[str, Any], 
                              target_objectives: List[str]) -> Dict[str, Any]:
        """生成通用攻击路径"""
        return {
            "description": "通用渗透测试攻击路径",
            "steps": [
                {
                    "action": "信息收集",
                    "description": "全面收集目标信息",
                    "tools": ["多种侦察工具"],
                    "estimated_time": "1小时",
                    "success_indicators": ["信息收集完成", "攻击面识别"]
                },
                {
                    "action": "漏洞识别",
                    "description": "识别所有潜在漏洞",
                    "tools": ["多种扫描工具"],
                    "estimated_time": "2小时",
                    "success_indicators": ["漏洞列表生成", "优先级排序"]
                },
                {
                    "action": "漏洞利用",
                    "description": "尝试利用发现的漏洞",
                    "tools": ["多种利用工具"],
                    "estimated_time": "3小时",
                    "success_indicators": ["漏洞利用成功", "访问获取"]
                },
                {
                    "action": "目标达成",
                    "description": "完成渗透测试目标",
                    "tools": ["后渗透工具"],
                    "estimated_time": "2小时",
                    "success_indicators": ["目标完成", "证据收集"]
                }
            ],
            "technical_complexity": 5,
            "detection_risk": 5,
            "estimated_time_hours": 8,
            "resource_requirements": {
                "computational_power": "中",
                "network_bandwidth": "中",
                "stealth_requirements": "中"
            },
            "success_criteria": [
                "完成所有测试阶段",
                "验证安全状态",
                "达成测试目标"
            ],
            "expected_effectiveness": 6
        }
    
    def _generate_combined_path(self, entry_points: List[Dict[str, Any]], 
                               target_objectives: List[str]) -> Dict[str, Any]:
        """生成组合攻击路径"""
        return {
            "description": "多入口点组合攻击路径",
            "steps": [
                {
                    "action": "并行侦察",
                    "description": "同时从多个入口点进行侦察",
                    "tools": ["多种侦察工具"],
                    "estimated_time": "1.5小时",
                    "success_indicators": ["多维度信息收集", "攻击面扩展"]
                },
                {
                    "action": "弱点分析",
                    "description": "分析所有入口点的弱点",
                    "tools": ["分析工具", "手动评估"],
                    "estimated_time": "1小时",
                    "success_indicators": ["弱点优先级排序", "攻击策略制定"]
                },
                {
                    "action": "协调攻击",
                    "description": "协调多个攻击向量",
                    "tools": ["协调框架", "自定义脚本"],
                    "estimated_time": "3小时",
                    "success_indicators": ["攻击协调成功", "防御分散"]
                },
                {
                    "action": "目标达成",
                    "description": "通过最佳路径达成目标",
                    "tools": ["多种工具组合"],
                    "estimated_time": "2.5小时",
                    "success_indicators": ["目标完成", "最小化检测"]
                }
            ],
            "technical_complexity": 9,
            "detection_risk": 4,
            "estimated_time_hours": 8,
            "resource_requirements": {
                "computational_power": "高",
                "network_bandwidth": "高",
                "stealth_requirements": "高"
            },
            "success_criteria": [
                "多向量攻击成功",
                "防御系统绕过",
                "高效目标达成"
            ],
            "expected_effectiveness": 9
        }


class RiskAssessmentDecision(DecisionPoint):
    """风险评估决策点"""
    
    def __init__(self):
        super().__init__(
            decision_type=DecisionType.RISK_ASSESSMENT,
            description="评估渗透测试活动的风险和影响，做出继续/停止决策"
        )
    
    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险并做出决策"""
        current_progress = context.get("current_progress", {})
        findings = context.get("findings", [])
        business_context = context.get("business_context", {})
        
        print(f"[WARNING] 风险评估决策点 - 进度: {current_progress.get('stage', '未知')}, 发现: {len(findings)}个")
        
        # 评估技术风险
        technical_risk = self._assess_technical_risk(findings, current_progress)
        
        # 评估业务风险
        business_risk = self._assess_business_risk(technical_risk, business_context)
        
        # 评估操作风险
        operational_risk = self._assess_operational_risk(current_progress, findings)
        
        # 计算总体风险
        overall_risk = self._calculate_overall_risk(technical_risk, business_risk, operational_risk)
        
        # 做出继续/停止决策
        continuation_decision = self._make_continuation_decision(overall_risk, current_progress, findings)
        
        # 设置决策结果
        self.confidence = self._calculate_risk_confidence(technical_risk, business_risk, operational_risk)
        self.outcome = continuation_decision["recommended_action"]
        self.reasoning = continuation_decision["reasoning"]
        self.recommendations = continuation_decision["recommendations"]
        self.alternatives = self._generate_risk_alternatives(continuation_decision, overall_risk)
        
        # 构建输出数据
        self.output_data = {
            "risk_assessment": {
                "technical_risk": technical_risk,
                "business_risk": business_risk,
                "operational_risk": operational_risk,
                "overall_risk": overall_risk,
                "continuation_decision": continuation_decision,
                "assessment_timestamp": time.time()
            },
            "decision_summary": self.get_decision_summary()
        }
        
        return self.output_data
    
    def _assess_technical_risk(self, findings: List[Dict[str, Any]], 
                              current_progress: Dict[str, Any]) -> Dict[str, Any]:
        """评估技术风险"""
        risk_score = 0
        risk_factors = []
        
        # 基于漏洞严重性
        high_severity_count = sum(1 for f in findings if f.get("severity") == "high")
        medium_severity_count = sum(1 for f in findings if f.get("severity") == "medium")
        low_severity_count = sum(1 for f in findings if f.get("severity") == "low")
        
        risk_score += high_severity_count * 10
        risk_score += medium_severity_count * 5
        risk_score += low_severity_count * 1
        
        if high_severity_count > 0:
            risk_factors.append(f"高风险漏洞({high_severity_count}个): +{high_severity_count * 10}分")
        if medium_severity_count > 0:
            risk_factors.append(f"中风险漏洞({medium_severity_count}个): +{medium_severity_count * 5}分")
        if low_severity_count > 0:
            risk_factors.append(f"低风险漏洞({low_severity_count}个): +{low_severity_count}分")
        
        # 基于攻击进展
        current_stage = current_progress.get("stage", "")
        stage_risk = {
            "reconnaissance": 1,
            "scanning": 3,
            "vulnerability_analysis": 5,
            "exploitation": 8,
            "post_exploitation": 10,
            "reporting": 1
        }.get(current_stage, 5)
        
        risk_score += stage_risk
        risk_factors.append(f"当前阶段({current_stage}): +{stage_risk}分")
        
        # 基于已获取的访问级别
        access_level = current_progress.get("access_level", "none")
        access_risk = {
            "none": 0,
            "low": 3,
            "medium": 6,
            "high": 9,
            "admin": 12,
            "system": 15
        }.get(access_level, 0)
        
        if access_risk > 0:
            risk_score += access_risk
            risk_factors.append(f"当前访问级别({access_level}): +{access_risk}分")
        
        # 确定技术风险等级
        if risk_score <= 10:
            risk_level = "低"
        elif risk_score <= 25:
            risk_level = "中"
        elif risk_score <= 40:
            risk_level = "高"
        else:
            risk_level = "极高"
        
        return {
            "score": risk_score,
            "level": risk_level,
            "factors": risk_factors,
            "vulnerability_counts": {
                "high": high_severity_count,
                "medium": medium_severity_count,
                "low": low_severity_count
            },
            "current_stage": current_stage,
            "access_level": access_level
        }
    
    def _assess_business_risk(self, technical_risk: Dict[str, Any], 
                             business_context: Dict[str, Any]) -> Dict[str, Any]:
        """评估业务风险"""
        business_impact_score = 0
        impact_factors = []
        
        # 业务关键性
        business_criticality = business_context.get("criticality", "medium")
        criticality_score = {
            "low": 1,
            "medium": 3,
            "high": 6,
            "critical": 10
        }.get(business_criticality, 3)
        
        business_impact_score += criticality_score
        impact_factors.append(f"业务关键性({business_criticality}): +{criticality_score}分")
        
        # 数据敏感性
        data_sensitivity = business_context.get("data_sensitivity", "medium")
        sensitivity_score = {
            "public": 1,
            "internal": 3,
            "confidential": 6,
            "secret": 10
        }.get(data_sensitivity, 3)
        
        business_impact_score += sensitivity_score
        impact_factors.append(f"数据敏感性({data_sensitivity}): +{sensitivity_score}分")
        
        # 合规要求
        compliance_requirements = business_context.get("compliance_requirements", [])
        compliance_score = len(compliance_requirements) * 2
        
        if compliance_score > 0:
            business_impact_score += compliance_score
            impact_factors.append(f"合规要求({len(compliance_requirements)}个): +{compliance_score}分")
        
        # 声誉影响
        reputation_impact = business_context.get("reputation_impact", "medium")
        reputation_score = {
            "low": 1,
            "medium": 3,
            "high": 6,
            "severe": 10
        }.get(reputation_impact, 3)
        
        business_impact_score += reputation_score
        impact_factors.append(f"声誉影响({reputation_impact}): +{reputation_score}分")
        
        # 结合技术风险
        technical_score = technical_risk.get("score", 0)
        combined_score = (technical_score * 0.6) + (business_impact_score * 0.4)
        
        # 确定业务风险等级
        if combined_score <= 15:
            business_risk_level = "低"
        elif combined_score <= 30:
            business_risk_level = "中"
        elif combined_score <= 45:
            business_risk_level = "高"
        else:
            business_risk_level = "极高"
        
        return {
            "score": combined_score,
            "level": business_risk_level,
            "impact_factors": impact_factors,
            "technical_contribution": technical_score * 0.6,
            "business_contribution": business_impact_score * 0.4,
            "business_context": {
                "criticality": business_criticality,
                "data_sensitivity": data_sensitivity,
                "compliance_count": len(compliance_requirements),
                "reputation_impact": reputation_impact
            }
        }
    
    def _assess_operational_risk(self, current_progress: Dict[str, Any], 
                                findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估操作风险"""
        operational_score = 0
        operational_factors = []
        
        # 检测风险
        detection_indicators = current_progress.get("detection_indicators", [])
        detection_score = len(detection_indicators) * 3
        
        if detection_score > 0:
            operational_score += detection_score
            operational_factors.append(f"检测指示器({len(detection_indicators)}个): +{detection_score}分")
        
        # 操作复杂性
        current_stage = current_progress.get("stage", "")
        complexity_score = {
            "reconnaissance": 1,
            "scanning": 3,
            "vulnerability_analysis": 5,
            "exploitation": 8,
            "post_exploitation": 10,
            "reporting": 1
        }.get(current_stage, 5)
        
        operational_score += complexity_score
        operational_factors.append(f"操作复杂性({current_stage}阶段): +{complexity_score}分")
        
        # 资源消耗
        resource_usage = current_progress.get("resource_usage", {"level": "medium"})
        resource_score = {
            "low": 1,
            "medium": 3,
            "high": 6,
            "extreme": 10
        }.get(resource_usage.get("level", "medium"), 3)
        
        operational_score += resource_score
        operational_factors.append(f"资源消耗({resource_usage.get('level', 'medium')}): +{resource_score}分")
        
        # 时间压力
        time_elapsed = current_progress.get("time_elapsed_hours", 0)
        time_pressure = min(10, time_elapsed / 2)  # 每2小时增加1分，最多10分
        
        if time_pressure > 0:
            operational_score += time_pressure
            operational_factors.append(f"时间压力({time_elapsed}小时): +{time_pressure:.1f}分")
        
        # 确定操作风险等级
        if operational_score <= 10:
            operational_level = "低"
        elif operational_score <= 20:
            operational_level = "中"
        elif operational_score <= 30:
            operational_level = "高"
        else:
            operational_level = "极高"
        
        return {
            "score": operational_score,
            "level": operational_level,
            "factors": operational_factors,
            "detection_indicators": detection_indicators,
            "current_complexity": current_stage,
            "resource_usage": resource_usage,
            "time_elapsed_hours": time_elapsed
        }
    
    def _calculate_overall_risk(self, technical_risk: Dict[str, Any], 
                               business_risk: Dict[str, Any], 
                               operational_risk: Dict[str, Any]) -> Dict[str, Any]:
        """计算总体风险"""
        technical_score = technical_risk.get("score", 0)
        business_score = business_risk.get("score", 0)
        operational_score = operational_risk.get("score", 0)
        
        # 加权计算总体风险
        overall_score = (technical_score * 0.4) + (business_score * 0.4) + (operational_score * 0.2)
        
        # 确定总体风险等级
        if overall_score <= 15:
            overall_level = "低"
            color = "green"
        elif overall_score <= 30:
            overall_level = "中"
            color = "yellow"
        elif overall_score <= 45:
            overall_level = "高"
            color = "orange"
        else:
            overall_level = "极高"
            color = "red"
        
        return {
            "score": overall_score,
            "level": overall_level,
            "color": color,
            "component_scores": {
                "technical": technical_score,
                "business": business_score,
                "operational": operational_score
            },
            "component_levels": {
                "technical": technical_risk.get("level", "低"),
                "business": business_risk.get("level", "低"),
                "operational": operational_risk.get("level", "低")
            },
            "calculation_method": "技术风险40% + 业务风险40% + 操作风险20%"
        }
    
    def _make_continuation_decision(self, overall_risk: Dict[str, Any], 
                                   current_progress: Dict[str, Any], 
                                   findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """做出继续/停止决策"""
        overall_level = overall_risk.get("level", "低")
        current_stage = current_progress.get("stage", "")
        high_severity_count = sum(1 for f in findings if f.get("severity") == "high")
        
        # 基于风险等级的决策
        if overall_level == "极高":
            recommended_action = DecisionOutcome.STOP
            reasoning = "总体风险极高，必须立即停止测试以避免严重事故"
        elif overall_level == "高":
            if high_severity_count >= 3:
                recommended_action = DecisionOutcome.STOP
                reasoning = "发现多个高风险漏洞，继续测试可能导致不可控后果"
            else:
                recommended_action = DecisionOutcome.PAUSE
                reasoning = "风险较高，建议暂停测试进行风险评估"
        elif overall_level == "中":
            if current_stage in ["exploitation", "post_exploitation"]:
                recommended_action = DecisionOutcome.ADJUST
                reasoning = "中等风险但在关键阶段，建议调整策略继续"
            else:
                recommended_action = DecisionOutcome.PROCEED
                reasoning = "风险可控，可以继续测试"
        else:  # 低风险
            recommended_action = DecisionOutcome.PROCEED
            reasoning = "风险较低，安全继续测试"
        
        # 生成建议
        recommendations = self._generate_risk_recommendations(recommended_action, overall_level, current_stage)
        
        return {
            "recommended_action": recommended_action,
            "reasoning": reasoning,
            "recommendations": recommendations,
            "decision_factors": {
                "overall_risk_level": overall_level,
                "current_stage": current_stage,
                "high_severity_count": high_severity_count
            }
        }
    
    def _calculate_risk_confidence(self, technical_risk: Dict[str, Any], 
                                  business_risk: Dict[str, Any], 
                                  operational_risk: Dict[str, Any]) -> DecisionConfidence:
        """计算风险评估置信度"""
        # 基于数据完整性的置信度
        data_points = 0
        
        if technical_risk.get("vulnerability_counts"):
            data_points += 1
        if business_risk.get("business_context"):
            data_points += 1
        if operational_risk.get("detection_indicators") is not None:
            data_points += 1
        
        if data_points >= 3:
            return DecisionConfidence.VERY_HIGH
        elif data_points >= 2:
            return DecisionConfidence.HIGH
        elif data_points >= 1:
            return DecisionConfidence.MEDIUM
        else:
            return DecisionConfidence.LOW
    
    def _generate_risk_recommendations(self, recommended_action: DecisionOutcome, 
                                      risk_level: str, current_stage: str) -> List[str]:
        """生成风险管理建议"""
        recommendations = []
        
        if recommended_action == DecisionOutcome.STOP:
            recommendations.extend([
                "立即停止所有测试活动",
                "记录当前状态和发现",
                "通知相关干系人",
                "进行事后分析",
                "制定修复计划"
            ])
        elif recommended_action == DecisionOutcome.PAUSE:
            recommendations.extend([
                "暂停当前测试活动",
                "评估风险缓解选项",
                "获取额外授权",
                "调整测试策略",
                "资源重新分配"
            ])
        elif recommended_action == DecisionOutcome.ADJUST:
            recommendations.extend([
                "调整测试策略和方法",
                "增加监控和日志记录",
                "设置更严格的停止条件",
                "定期风险评估检查",
                "准备应急计划"
            ])
        else:  # PROCEED
            recommendations.extend([
                "继续当前测试计划",
                "保持风险监控",
                "定期报告进展",
                "记录所有发现",
                "遵守授权范围"
            ])
        
        # 添加通用建议
        recommendations.append(f"当前风险等级: {risk_level}")
        recommendations.append(f"当前测试阶段: {current_stage}")
        
        return recommendations
    
    def _generate_risk_alternatives(self, continuation_decision: Dict[str, Any], 
                                   overall_risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成风险应对替代方案"""
        alternatives = []
        recommended_action = continuation_decision.get("recommended_action", DecisionOutcome.PROCEED)
        risk_level = overall_risk.get("level", "低")
        
        # 基于风险等级的替代方案
        if risk_level in ["高", "极高"] and recommended_action != DecisionOutcome.STOP:
            alternatives.append({
                "action": "立即停止",
                "description": "完全停止测试活动",
                "rationale": "预防性停止以避免潜在事故",
                "applicability": "风险极高或超出授权范围时"
            })
        
        if recommended_action != DecisionOutcome.ADJUST:
            alternatives.append({
                "action": "策略调整",
                "description": "调整测试方法和目标",
                "rationale": "降低风险同时继续获取价值",
                "applicability": "风险较高但仍有测试价值时"
            })
        
        if recommended_action != DecisionOutcome.PAUSE:
            alternatives.append({
                "action": "暂停评估",
                "description": "暂时停止进行深入评估",
                "rationale": "获取更多信息再做决策",
                "applicability": "不确定风险影响时"
            })
        
        # 添加通用替代方案
        alternatives.append({
            "action": "范围缩减",
            "description": "缩小测试范围",
            "rationale": "专注于关键区域降低整体风险",
            "applicability": "资源有限或时间紧迫时"
        })
        
        return alternatives


# AI决策点系统主类
class AIDecisionSystem:
    """
    AI决策点系统
    管理渗透测试工作流中的关键决策点
    """
    
    def __init__(self, enable_ai_guidance: bool = True):
        self.enable_ai_guidance = enable_ai_guidance
        self.decision_points = {
            DecisionType.TARGET_ANALYSIS: TargetAnalysisDecision(),
            DecisionType.TOOL_SELECTION: ToolSelectionDecision(),
            DecisionType.ATTACK_PATH: AttackPathDecision(),
            DecisionType.RISK_ASSESSMENT: RiskAssessmentDecision()
        }
        self.decision_history = []
    
    def make_decision(self, decision_type: DecisionType, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定类型的决策"""
        if decision_type not in self.decision_points:
            return {
                "error": f"未知决策类型: {decision_type}",
                "available_types": [dt.value for dt in self.decision_points.keys()]
            }
        
        print(f"[AI] AI决策系统 - 执行{decision_type.value}决策")
        
        # 获取决策点实例
        decision_point = self.decision_points[decision_type]
        
        # 执行决策
        start_time = time.time()
        decision_result = decision_point.make_decision(context)
        decision_time = time.time() - start_time
        
        # 记录决策历史
        decision_record = {
            "decision_type": decision_type.value,
            "timestamp": time.time(),
            "decision_time": decision_time,
            "context_summary": self._summarize_context(context),
            "decision_result": decision_result.get("decision_summary", {}),
            "confidence": decision_point.confidence.value,
            "outcome": decision_point.outcome.value
        }
        self.decision_history.append(decision_record)
        
        # 添加性能指标
        decision_result["performance_metrics"] = {
            "decision_time_seconds": decision_time,
            "decision_history_count": len(self.decision_history),
            "average_decision_time": self._calculate_average_decision_time()
        }
        
        return decision_result
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history[-limit:] if limit > 0 else self.decision_history
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计"""
        if not self.decision_history:
            return {"total_decisions": 0}
        
        stats = {
            "total_decisions": len(self.decision_history),
            "by_type": {},
            "by_outcome": {},
            "by_confidence": {},
            "time_statistics": {
                "average_decision_time": self._calculate_average_decision_time(),
                "total_decision_time": sum(d["decision_time"] for d in self.decision_history),
                "recent_decisions": len(self.decision_history[-5:]) if len(self.decision_history) >= 5 else len(self.decision_history)
            }
        }
        
        # 按类型统计
        for decision in self.decision_history:
            decision_type = decision["decision_type"]
            stats["by_type"][decision_type] = stats["by_type"].get(decision_type, 0) + 1
            
            outcome = decision["outcome"]
            stats["by_outcome"][outcome] = stats["by_outcome"].get(outcome, 0) + 1
            
            confidence = decision["confidence"]
            stats["by_confidence"][confidence] = stats["by_confidence"].get(confidence, 0) + 1
        
        return stats
    
    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """总结决策上下文"""
        summary = {}
        
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                summary[key] = value
            elif isinstance(value, list):
                summary[key] = f"列表({len(value)}项)"
            elif isinstance(value, dict):
                summary[key] = f"字典({len(value)}键)"
            else:
                summary[key] = str(type(value))
        
        return summary
    
    def _calculate_average_decision_time(self) -> float:
        """计算平均决策时间"""
        if not self.decision_history:
            return 0.0
        
        total_time = sum(d["decision_time"] for d in self.decision_history)
        return total_time / len(self.decision_history)


# 导出类
__all__ = [
    "DecisionType",
    "DecisionConfidence",
    "DecisionOutcome",
    "DecisionPoint",
    "TargetAnalysisDecision",
    "ToolSelectionDecision",
    "AttackPathDecision",
    "RiskAssessmentDecision",
    "AIDecisionSystem"
]