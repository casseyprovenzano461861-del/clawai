# -*- coding: utf-8 -*-
"""
攻击链生成器 - 重构版本
基于真实扫描结果生成攻击链，减少模拟数据依赖
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)


class AttackPhase(Enum):
    """攻击阶段枚举"""
    RECONNAISSANCE = "reconnaissance"      # 侦察
    FINGERPRINTING = "fingerprinting"      # 指纹识别
    VULNERABILITY_SCANNING = "vulnerability_scanning"  # 漏洞扫描
    EXPLOITATION = "exploitation"          # 漏洞利用
    POST_EXPLOITATION = "post_exploitation" # 后渗透
    DEFENSE_ANALYSIS = "defense_analysis"   # 防御分析


@dataclass
class AttackStep:
    """攻击步骤"""
    step: int
    tool: str
    phase: AttackPhase
    duration: str
    description: str
    success: bool = True
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step": self.step,
            "tool": self.tool,
            "phase": self.phase.value,
            "duration": self.duration,
            "description": self.description,
            "success": self.success,
            "details": self.details or {}
        }


@dataclass
class ScanAnalysis:
    """扫描分析结果"""
    target: str
    open_ports: List[Dict[str, Any]]
    web_technologies: List[str]
    vulnerabilities: List[Dict[str, Any]]
    waf_detected: bool = False
    waf_type: Optional[str] = None
    attack_surface_score: float = 0.0
    
    @classmethod
    def from_scan_results(cls, scan_results: Dict[str, Any]) -> 'ScanAnalysis':
        """从扫描结果创建分析对象"""
        target = scan_results.get("target", "unknown")
        
        # 提取端口信息
        open_ports = []
        if "nmap" in scan_results and "ports" in scan_results["nmap"]:
            open_ports = scan_results["nmap"]["ports"]
        
        # 提取Web技术栈
        web_technologies = []
        if "whatweb" in scan_results and "fingerprint" in scan_results["whatweb"]:
            fingerprint = scan_results["whatweb"]["fingerprint"]
            if fingerprint.get("web_server"):
                web_technologies.append(f"Web服务器: {fingerprint['web_server']}")
            if fingerprint.get("language"):
                web_technologies.extend(fingerprint["language"])
            if fingerprint.get("cms"):
                web_technologies.extend(fingerprint["cms"])
        
        # 提取漏洞信息
        vulnerabilities = []
        if "nuclei" in scan_results and "vulnerabilities" in scan_results["nuclei"]:
            vulnerabilities = scan_results["nuclei"]["vulnerabilities"]
        
        # 提取WAF信息
        waf_detected = False
        waf_type = None
        if "wafw00f" in scan_results:
            waf_detected = scan_results["wafw00f"].get("waf_detected", False)
            waf_type = scan_results["wafw00f"].get("waf_type")
        
        # 计算攻击面评分
        attack_surface_score = cls._calculate_attack_surface_score(
            open_ports, vulnerabilities, waf_detected
        )
        
        return cls(
            target=target,
            open_ports=open_ports,
            web_technologies=web_technologies,
            vulnerabilities=vulnerabilities,
            waf_detected=waf_detected,
            waf_type=waf_type,
            attack_surface_score=attack_surface_score
        )
    
    @staticmethod
    def _calculate_attack_surface_score(
        open_ports: List[Dict[str, Any]],
        vulnerabilities: List[Dict[str, Any]],
        waf_detected: bool
    ) -> float:
        """计算攻击面评分"""
        score = 0.0
        
        # 基于开放端口
        if open_ports:
            score += min(len(open_ports) * 0.3, 3.0)
        
        # 基于漏洞严重性
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low").lower()
            if severity == "critical":
                score += 2.0
            elif severity == "high":
                score += 1.0
            elif severity == "medium":
                score += 0.5
            elif severity == "low":
                score += 0.2
        
        # WAF提供保护
        if waf_detected:
            score = max(score - 1.0, 0.0)
        
        # 限制在0-10分
        return round(min(max(score, 0.0), 10.0), 2)


class AttackChainGenerator:
    """
    攻击链生成器
    基于真实扫描结果生成攻击链
    """
    
    # 工具配置
    TOOL_CONFIG = {
        "nmap": {
            "phase": AttackPhase.RECONNAISSANCE,
            "duration": "2.3s",
            "description_template": "端口扫描，发现{port_count}个开放端口"
        },
        "whatweb": {
            "phase": AttackPhase.FINGERPRINTING,
            "duration": "1.8s",
            "description_template": "技术栈识别，{technologies}"
        },
        "nuclei": {
            "phase": AttackPhase.VULNERABILITY_SCANNING,
            "duration": "4.2s",
            "description_template": "漏洞扫描，发现{vuln_count}个漏洞"
        },
        "sqlmap": {
            "phase": AttackPhase.EXPLOITATION,
            "duration": "5.5s",
            "description_template": "SQL注入检测，{result}"
        },
        "wafw00f": {
            "phase": AttackPhase.DEFENSE_ANALYSIS,
            "duration": "1.2s",
            "description_template": "WAF检测，{result}"
        }
    }
    
    # 攻击策略模板
    STRATEGY_TEMPLATES = {
        "web_attack": {
            "name": "Web应用攻击",
            "description": "针对Web应用的攻击路径",
            "phases": [
                AttackPhase.RECONNAISSANCE,
                AttackPhase.FINGERPRINTING,
                AttackPhase.VULNERABILITY_SCANNING,
                AttackPhase.EXPLOITATION,
                AttackPhase.POST_EXPLOITATION
            ],
            "tools": ["nmap", "whatweb", "nuclei", "sqlmap"]
        },
        "service_attack": {
            "name": "服务攻击",
            "description": "针对网络服务的攻击路径",
            "phases": [
                AttackPhase.RECONNAISSANCE,
                AttackPhase.VULNERABILITY_SCANNING,
                AttackPhase.EXPLOITATION,
                AttackPhase.POST_EXPLOITATION
            ],
            "tools": ["nmap", "nuclei"]
        },
        "recon_only": {
            "name": "侦察扫描",
            "description": "仅进行信息收集和侦察",
            "phases": [
                AttackPhase.RECONNAISSANCE,
                AttackPhase.FINGERPRINTING,
                AttackPhase.VULNERABILITY_SCANNING
            ],
            "tools": ["nmap", "whatweb", "nuclei"]
        }
    }
    
    def __init__(self, enable_evolution: bool = True):
        """
        初始化生成器
        
        Args:
            enable_evolution: 是否启用进化功能
        """
        self.enable_evolution = enable_evolution
    
    def generate_attack_chain(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成攻击链
        
        Args:
            scan_results: 扫描结果
            
        Returns:
            攻击链结果
        """
        try:
            # 分析扫描结果
            analysis = ScanAnalysis.from_scan_results(scan_results)
            
            # 选择攻击策略
            strategy = self._select_attack_strategy(analysis)
            
            # 生成攻击步骤
            attack_steps = self._generate_attack_steps(strategy, analysis)
            
            # 进化攻击链（如果启用）
            if self.enable_evolution:
                attack_steps = self._evolve_attack_chain(attack_steps, analysis)
            
            # 计算总时长
            total_duration = self._calculate_total_duration(attack_steps)
            
            # 生成决策信息
            decision_info = self._generate_decision_info(strategy, analysis, attack_steps)
            
            # 构建结果
            result = {
                "attack_chain": [step.to_dict() for step in attack_steps],
                "analysis": {
                    "target": analysis.target,
                    "open_ports_count": len(analysis.open_ports),
                    "vulnerabilities_count": len(analysis.vulnerabilities),
                    "web_technologies": analysis.web_technologies,
                    "waf_detected": analysis.waf_detected,
                    "waf_type": analysis.waf_type,
                    "attack_surface_score": analysis.attack_surface_score,
                    "risk_level": self._calculate_risk_level(analysis)
                },
                "decision": decision_info,
                "target_analysis": {
                    "attack_surface": analysis.attack_surface_score,
                    "open_ports": len(analysis.open_ports),
                    "vulnerabilities": len(analysis.vulnerabilities),
                    "critical_vulnerabilities": len([v for v in analysis.vulnerabilities 
                                                    if v.get("severity") == "critical"]),
                    "high_vulnerabilities": len([v for v in analysis.vulnerabilities 
                                               if v.get("severity") == "high"]),
                    "has_web": bool(analysis.web_technologies),
                    "waf_detected": analysis.waf_detected,
                    "waf_type": analysis.waf_type
                },
                "execution_summary": {
                    "total_steps": len(attack_steps),
                    "evolution_applied": self.enable_evolution,
                    "estimated_duration": total_duration,
                    "strategy_used": strategy["name"]
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"生成攻击链时出错: {str(e)}")
            return self._generate_fallback_chain(scan_results)
    
    def _select_attack_strategy(self, analysis: ScanAnalysis) -> Dict[str, Any]:
        """选择攻击策略"""
        # 根据分析结果选择策略
        if analysis.web_technologies:
            # 有Web技术栈，使用Web攻击策略
            return self.STRATEGY_TEMPLATES["web_attack"]
        elif analysis.open_ports:
            # 有开放端口，使用服务攻击策略
            return self.STRATEGY_TEMPLATES["service_attack"]
        else:
            # 默认使用侦察策略
            return self.STRATEGY_TEMPLATES["recon_only"]
    
    def _generate_attack_steps(
        self, 
        strategy: Dict[str, Any], 
        analysis: ScanAnalysis
    ) -> List[AttackStep]:
        """生成攻击步骤"""
        steps = []
        step_number = 1
        
        for tool_name in strategy["tools"]:
            if tool_name not in self.TOOL_CONFIG:
                continue
            
            tool_config = self.TOOL_CONFIG[tool_name]
            
            # 生成步骤描述
            description = self._generate_step_description(tool_name, tool_config, analysis)
            
            # 创建攻击步骤
            step = AttackStep(
                step=step_number,
                tool=tool_name,
                phase=tool_config["phase"],
                duration=tool_config["duration"],
                description=description,
                success=True,
                details=self._get_step_details(tool_name, analysis)
            )
            
            steps.append(step)
            step_number += 1
        
        return steps
    
    def _generate_step_description(
        self, 
        tool_name: str, 
        tool_config: Dict[str, Any], 
        analysis: ScanAnalysis
    ) -> str:
        """生成步骤描述"""
        template = tool_config["description_template"]
        
        if tool_name == "nmap":
            port_count = len(analysis.open_ports)
            if port_count > 0:
                port_services = ", ".join([f"{p.get('port')}({p.get('service')})" 
                                         for p in analysis.open_ports[:3]])
                if port_count > 3:
                    port_services += f" 等{port_count}个端口"
                return template.format(port_count=port_count, details=port_services)
            else:
                return "端口扫描，未发现开放端口"
        
        elif tool_name == "whatweb":
            if analysis.web_technologies:
                tech_summary = ", ".join(analysis.web_technologies[:3])
                if len(analysis.web_technologies) > 3:
                    tech_summary += f" 等{len(analysis.web_technologies)}项技术"
                return template.format(technologies=tech_summary)
            else:
                return "技术栈识别，未识别到Web技术"
        
        elif tool_name == "nuclei":
            vuln_count = len(analysis.vulnerabilities)
            if vuln_count > 0:
                critical_vulns = len([v for v in analysis.vulnerabilities 
                                    if v.get("severity") == "critical"])
                return template.format(vuln_count=vuln_count, 
                                     critical_count=critical_vulns)
            else:
                return "漏洞扫描，未发现漏洞"
        
        elif tool_name == "sqlmap":
            if analysis.waf_detected:
                return template.format(result="检测到WAF保护，尝试绕过技术")
            else:
                return template.format(result="SQL注入检测，尝试常见注入点")
        
        elif tool_name == "wafw00f":
            if analysis.waf_detected:
                return template.format(result=f"检测到WAF: {analysis.waf_type}")
            else:
                return template.format(result="未检测到WAF保护")
        
        else:
            return template.format(result="执行完成")
    
    def _get_step_details(self, tool_name: str, analysis: ScanAnalysis) -> Dict[str, Any]:
        """获取步骤详情"""
        details = {}
        
        if tool_name == "nmap":
            details["open_ports"] = analysis.open_ports
        
        elif tool_name == "whatweb":
            details["web_technologies"] = analysis.web_technologies
        
        elif tool_name == "nuclei":
            details["vulnerabilities"] = analysis.vulnerabilities
        
        elif tool_name == "wafw00f":
            details["waf_detected"] = analysis.waf_detected
            details["waf_type"] = analysis.waf_type
        
        return details
    
    def _evolve_attack_chain(
        self, 
        steps: List[AttackStep], 
        analysis: ScanAnalysis
    ) -> List[AttackStep]:
        """进化攻击链"""
        if not self.enable_evolution:
            return steps
        
        evolved_steps = []
        
        for step in steps:
            # 复制步骤
            evolved_step = AttackStep(
                step=step.step,
                tool=step.tool,
                phase=step.phase,
                duration=step.duration,
                description=step.description,
                success=step.success,
                details=step.details.copy() if step.details else {}
            )
            
            # 根据分析结果调整步骤
            if step.tool == "sqlmap" and analysis.waf_detected:
                # 如果有WAF，调整SQL注入策略
                evolved_step.description = f"{step.description}（使用WAF绕过技术）"
                evolved_step.details["waf_bypass"] = True
            
            if step.tool == "nuclei" and analysis.vulnerabilities:
                # 如果有漏洞，优先利用严重漏洞
                critical_vulns = [v for v in analysis.vulnerabilities 
                                if v.get("severity") == "critical"]
                if critical_vulns:
                    evolved_step.details["priority_vulnerabilities"] = critical_vulns
            
            evolved_steps.append(evolved_step)
        
        return evolved_steps
    
    def _calculate_total_duration(self, steps: List[AttackStep]) -> str:
        """计算总时长"""
        total_seconds = 0
        
        for step in steps:
            # 解析时长字符串，如"2.3s"
            duration_str = step.duration
            if duration_str.endswith('s'):
                try:
                    seconds = float(duration_str[:-1])
                    total_seconds += seconds
                except ValueError:
                    pass
        
        if total_seconds < 60:
            return f"{total_seconds:.1f}秒"
        else:
            minutes = total_seconds / 60
            return f"{minutes:.1f}分钟"
    
    def _generate_decision_info(
        self, 
        strategy: Dict[str, Any], 
        analysis: ScanAnalysis,
        steps: List[AttackStep]
    ) -> Dict[str, Any]:
        """生成决策信息"""
        risk_level = self._calculate_risk_level(analysis)
        confidence = self._calculate_confidence(analysis, steps)
        
        return {
            "selected_strategy": strategy["name"],
            "strategy_description": strategy["description"],
            "risk_level": risk_level,
            "confidence": confidence,
            "selection_reasons": self._generate_selection_reasons(strategy, analysis),
            "decision_factors": {
                "attack_surface": analysis.attack_surface_score,
                "vulnerability_count": len(analysis.vulnerabilities),
                "web_presence": bool(analysis.web_technologies),
                "waf_protection": analysis.waf_detected
            },
            "recommendations": self._generate_recommendations(analysis)
        }
    
    def _calculate_risk_level(self, analysis: ScanAnalysis) -> str:
        """计算风险等级"""
        score = analysis.attack_surface_score
        
        if score >= 7.0:
            return "critical"
        elif score >= 4.0:
            return "high"
        elif score >= 2.0:
            return "medium"
        else:
            return "low"
    
    def _calculate_confidence(self, analysis: ScanAnalysis, steps: List[AttackStep]) -> float:
        """计算置信度"""
        confidence = 0.6  # 基础置信度
        
        # 基于数据质量调整
        if analysis.open_ports:
            confidence += 0.1
        
        if analysis.web_technologies:
            confidence += 0.1
        
        if analysis.vulnerabilities:
            confidence += 0.15
        
        # 基于步骤数量调整
        if len(steps) >= 3:
            confidence += 0.05
        
        # 限制在0.5-0.95之间
        return round(min(max(confidence, 0.5), 0.95), 2)
    
    def _generate_selection_reasons(
        self, 
        strategy: Dict[str, Any], 
        analysis: ScanAnalysis
    ) -> List[str]:
        """生成选择理由"""
        reasons = []
        
        reasons.append(f"使用{strategy['name']}策略")
        
        if analysis.web_technologies:
            reasons.append("目标存在Web技术栈，适合Web攻击")
        
        if analysis.open_ports:
            reasons.append(f"发现{len(analysis.open_ports)}个开放端口")
        
        if analysis.vulnerabilities:
            reasons.append(f"发现{len(analysis.vulnerabilities)}个漏洞")
        
        if analysis.waf_detected:
            reasons.append(f"检测到WAF保护: {analysis.waf_type}")
        
        return reasons
    
    def _generate_recommendations(self, analysis: ScanAnalysis) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if not analysis.open_ports:
            recommendations.append("未发现开放端口，建议扩大扫描范围")
        
        if not analysis.web_technologies and analysis.open_ports:
            recommendations.append("开放端口但未识别到Web服务，建议手动验证")
        
        if analysis.waf_detected:
            recommendations.append("检测到WAF保护，建议使用WAF绕过技术")
        
        if analysis.vulnerabilities:
            critical_vulns = len([v for v in analysis.vulnerabilities 
                                if v.get("severity") == "critical"])
            if critical_vulns > 0:
                recommendations.append(f"发现{critical_vulns}个严重漏洞，建议优先利用")
        
        return recommendations
    
    def _generate_fallback_chain(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成回退攻击链"""
        # 简单的默认攻击链
        steps = [
            AttackStep(
                step=1,
                tool="nmap",
                phase=AttackPhase.RECONNAISSANCE,
                duration="2.3s",
                description="端口扫描（默认路径）",
                success=True
            ),
            AttackStep(
                step=2,
                tool="whatweb",
                phase=AttackPhase.FINGERPRINTING,
                duration="1.8s",
                description="技术栈识别（默认路径）",
                success=True
            ),
            AttackStep(
                step=3,
                tool="nuclei",
                phase=AttackPhase.VULNERABILITY_SCANNING,
                duration="4.2s",
                description="漏洞扫描（默认路径）",
                success=True
            )
        ]
        
        return {
            "attack_chain": [step.to_dict() for step in steps],
            "analysis": {
                "target": scan_results.get("target", "unknown"),
                "open_ports_count": 0,
                "vulnerabilities_count": 0,
                "web_technologies": [],
                "waf_detected": False,
                "waf_type": None,
                "attack_surface_score": 0.0,
                "risk_level": "low"
            },
            "decision": {
                "selected_strategy": "recon_only",
                "strategy_description": "侦察扫描",
                "risk_level": "low",
                "confidence": 0.6,
                "selection_reasons": ["默认回退路径"],
                "decision_factors": {
                    "attack_surface": 0.0,
                    "vulnerability_count": 0,
                    "web_presence": False,
                    "waf_protection": False
                },
                "recommendations": ["使用默认侦察路径"]
            },
            "target_analysis": {
                "attack_surface": 0.0,
                "open_ports": 0,
                "vulnerabilities": 0,
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
                "has_web": False,
                "waf_detected": False,
                "waf_type": None
            },
            "execution_summary": {
                "total_steps": 3,
                "evolution_applied": False,
                "estimated_duration": "8.3秒",
                "strategy_used": "recon_only"
            }
        }


def main():
    """测试函数"""
    import json
    
    print("=" * 80)
    print("攻击链生成器测试")
    print("=" * 80)
    
    # 创建生成器
    generator = AttackChainGenerator(enable_evolution=True)
    
    # 测试数据
    test_scan_results = {
        "target": "example.com",
        "nmap": {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"},
                {"port": 3306, "service": "mysql", "state": "open"}
            ]
        },
        "whatweb": {
            "fingerprint": {
                "web_server": "nginx",
                "language": ["PHP"],
                "cms": ["WordPress"],
                "other": ["jQuery"]
            }
        },
        "nuclei": {
            "vulnerabilities": [
                {"name": "WordPress XSS", "severity": "medium"},
                {"name": "Remote Code Execution", "severity": "critical"}
            ]
        },
        "wafw00f": {
            "waf_detected": True,
            "waf_type": "Cloudflare"
        }
    }
    
    print("\n测试数据:")
    print(json.dumps(test_scan_results, indent=2, ensure_ascii=False))
    
    print("\n生成攻击链...")
    result = generator.generate_attack_chain(test_scan_results)
    
    print("\n攻击链结果:")
    print(f"攻击步骤数: {len(result['attack_chain'])}")
    print(f"风险等级: {result['analysis']['risk_level']}")
    print(f"攻击面评分: {result['analysis']['attack_surface_score']}/10")
    print(f"置信度: {result['decision']['confidence']*100}%")
    
    print("\n攻击步骤:")
    for step in result["attack_chain"]:
        print(f"步骤 {step['step']}: [{step['tool']}] {step['description']} ({step['duration']})")
    
    print("\n决策原因:")
    for reason in result["decision"]["selection_reasons"]:
        print(f"  - {reason}")
    
    print("\n建议:")
    for recommendation in result["decision"]["recommendations"]:
        print(f"  - {recommendation}")
    
    print("\n" + "=" * 80)
    print("测试完成！")


if __name__ == "__main__":
    main()