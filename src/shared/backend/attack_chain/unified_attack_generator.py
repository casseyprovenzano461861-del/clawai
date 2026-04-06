# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
统一攻击链生成器 - 重构增强版
解决代码重复、命名不一致、类型提示不足问题
使用数据模型和工具类提高代码质量
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional

from backend.core.models import (
    ToolConfig, StrategyTemplate, AttackStep, PortInfo, VulnerabilityInfo,
    ScanAnalysis, VulnerabilityAnalysis, PathEvaluation, DecisionInfo,
    TargetAnalysis, ExecutionSummary, AttackChainResult
)
from backend.core.utils import AnalysisUtils, PathBuilder, EvolutionUtils

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 常量定义 ====================

TOOL_CONFIG: Dict[str, ToolConfig] = {
    "nmap": {
        "phase": "reconnaissance",
        "duration": "2.3s",
        "description_template": "端口扫描，{detail}"
    },
    "whatweb": {
        "phase": "fingerprinting",
        "duration": "1.8s",
        "description_template": "技术栈识别，{detail}"
    },
    "nuclei": {
        "phase": "vulnerability_scanning",
        "duration": "4.2s",
        "description_template": "漏洞扫描，{detail}"
    },
    "sqlmap": {
        "phase": "exploitation",
        "duration": "5.5s",
        "description_template": "SQL注入检测，{detail}"
    },
    "wafw00f": {
        "phase": "defense_analysis",
        "duration": "1.2s",
        "description_template": "WAF检测，{detail}"
    },
    "exploit": {
        "phase": "exploitation",
        "duration": "3.5s",
        "description_template": "漏洞利用，{detail}"
    },
    "post": {
        "phase": "post_exploitation",
        "duration": "6.1s",
        "description_template": "后渗透，{detail}"
    }
}

STRATEGY_TEMPLATES: Dict[str, StrategyTemplate] = {
    "web_attack": {
        "name": "Web应用攻击",
        "description": "针对Web应用的攻击路径",
        "tools": ["nmap", "whatweb", "nuclei", "exploit", "post"],
        "priority": 1
    },
    "service_attack": {
        "name": "服务攻击",
        "description": "针对网络服务的攻击路径",
        "tools": ["nmap", "nuclei", "exploit", "post"],
        "priority": 2
    },
    "recon_only": {
        "name": "侦察扫描",
        "description": "仅进行信息收集和侦察",
        "tools": ["nmap", "whatweb", "nuclei", "post"],
        "priority": 3
    },
    "sql_injection": {
        "name": "SQL注入攻击",
        "description": "专注于SQL注入的攻击路径",
        "tools": ["nmap", "whatweb", "sqlmap", "post"],
        "priority": 2
    }
}

EVOLUTION_CONFIG: Dict[str, Any] = {
    "max_rounds": 2,
    "adjustment_rules": {
        "waf_detected": {
            "action": "replace_tool",
            "from": "sqlmap",
            "to": "xsstrike",
            "reason": "WAF检测到SQL注入，尝试XSS攻击"
        },
        "exploit_detected": {
            "action": "modify_description",
            "tool": "exploit",
            "new_description": "隐蔽式漏洞利用（避免检测）"
        },
        "critical_vuln_found": {
            "action": "prioritize_exploit",
            "priority": "high"
        }
    }
}


class UnifiedAttackGenerator:
    """
    统一攻击链生成器
    重构版本，解决代码质量问题
    """
    
    def __init__(self, enable_evolution: bool = True) -> None:
        """
        初始化统一生成器
        
        Args:
            enable_evolution: 是否启用进化功能
        """
        self.enable_evolution = enable_evolution
        self.tool_config: Dict[str, ToolConfig] = TOOL_CONFIG
        self.strategy_templates: Dict[str, StrategyTemplate] = STRATEGY_TEMPLATES
        self.evolution_config: Dict[str, Any] = EVOLUTION_CONFIG
    
    def analyze_scan_results(self, results: Dict[str, Any]) -> ScanAnalysis:
        """
        分析扫描结果，提取关键信息
        
        Args:
            results: 扫描结果字典
            
        Returns:
            分析结果对象
        """
        analysis = ScanAnalysis()
        
        try:
            # 分析nmap结果
            if "nmap" in results:
                analysis.update_from_nmap(results["nmap"])
            
            # 分析whatweb结果
            if "whatweb" in results:
                analysis.update_from_whatweb(results["whatweb"])
            
            # 分析nuclei结果
            if "nuclei" in results:
                analysis.update_from_nuclei(results["nuclei"])
            
            # 分析wafw00f结果
            if "wafw00f" in results:
                analysis.update_from_wafw00f(results["wafw00f"])
            
            # 分析sqlmap结果
            if "sqlmap" in results:
                analysis.update_from_sqlmap(results["sqlmap"])
            
            # 计算攻击面评分
            analysis.attack_surface = AnalysisUtils.calculate_attack_surface(analysis)
            
        except Exception as e:
            logger.error(f"分析扫描结果时出错: {str(e)}")
        
        return analysis
    
    def generate_attack_paths(self, analysis: ScanAnalysis) -> List[List[AttackStep]]:
        """
        基于分析结果生成攻击路径
        
        Args:
            analysis: 分析结果对象
            
        Returns:
            攻击路径列表
        """
        paths: List[List[AttackStep]] = []
        
        # 确定适用的策略
        applicable_strategies = self._identify_applicable_strategies(analysis)
        
        # 为每个适用策略生成路径
        for strategy_name in applicable_strategies:
            strategy = self.strategy_templates[strategy_name]
            path = PathBuilder.build_path_from_strategy(strategy, self.tool_config)
            
            if path:
                # 定制路径描述
                self._customize_path_descriptions(path, analysis)
                paths.append(path)
        
        # 如果没有生成路径，使用默认侦察路径
        if not paths:
            default_path = PathBuilder.build_default_path()
            paths.append(default_path)
        
        return paths
    
    def _identify_applicable_strategies(self, analysis: ScanAnalysis) -> List[str]:
        """识别适用的攻击策略"""
        strategies: List[str] = []
        
        # Web攻击策略
        if analysis.has_web:
            strategies.append("web_attack")
        
        # 服务攻击策略
        if analysis.open_ports and len(analysis.open_ports) > 0:
            strategies.append("service_attack")
        
        # SQL注入策略
        sql_injections = analysis.vulnerabilities.high
        if any("SQL" in vuln for vuln in sql_injections):
            strategies.append("sql_injection")
        
        # 总是包含侦察策略
        strategies.append("recon_only")
        
        # 去重
        return list(dict.fromkeys(strategies))
    
    def _customize_path_descriptions(self, path: List[AttackStep], analysis: ScanAnalysis) -> None:
        """根据分析结果定制路径描述"""
        for step in path:
            tool = step["tool"]
            
            if tool == "nmap":
                AnalysisUtils.customize_nmap_description(step, analysis)
            elif tool == "whatweb":
                AnalysisUtils.customize_whatweb_description(step, analysis)
            elif tool == "nuclei":
                AnalysisUtils.customize_nuclei_description(step, analysis)
            elif tool == "sqlmap":
                AnalysisUtils.customize_sqlmap_description(step, analysis)
            elif tool == "wafw00f":
                AnalysisUtils.customize_wafw00f_description(step, analysis)
            elif tool == "exploit":
                AnalysisUtils.customize_exploit_description(step, analysis)
    
    def evaluate_paths(self, paths: List[List[AttackStep]], analysis: ScanAnalysis) -> List[PathEvaluation]:
        """
        评估攻击路径，计算评分
        
        Args:
            paths: 攻击路径列表
            analysis: 分析结果对象
            
        Returns:
            包含评分的路径信息列表
        """
        evaluated_paths: List[PathEvaluation] = []
        
        for i, path in enumerate(paths):
            score = self._calculate_path_score(path, analysis)
            path_type = AnalysisUtils.identify_path_type(path)
            
            evaluated_path = PathEvaluation(
                id=i + 1,
                path=path,
                type=path_type,
                score=score,
                step_count=len(path),
                tools_used=[step["tool"] for step in path],
                estimated_duration=AnalysisUtils.estimate_total_duration(path)
            )
            
            evaluated_paths.append(evaluated_path)
        
        # 按评分排序
        evaluated_paths.sort(key=lambda x: x.score, reverse=True)
        
        return evaluated_paths
    
    def _calculate_path_score(self, path: List[AttackStep], analysis: ScanAnalysis) -> float:
        """计算路径评分"""
        score = 5.0  # 基础分
        
        # 基于工具数量
        score += len(path) * 0.3
        
        # 基于工具类型
        for step in path:
            tool = step["tool"]
            
            if tool == "exploit":
                score += 1.5
            elif tool == "sqlmap":
                score += 1.2
            elif tool == "nuclei":
                score += 0.8
            elif tool == "whatweb":
                score += 0.5
            elif tool == "nmap":
                score += 0.3
        
        # 基于分析结果调整
        vulnerabilities = analysis.vulnerabilities
        
        if vulnerabilities.critical:
            score += len(vulnerabilities.critical) * 0.8
        
        if vulnerabilities.high:
            score += len(vulnerabilities.high) * 0.5
        
        # 如果有WAF，攻击难度增加，评分降低
        if analysis.waf_detected:
            score -= 0.5
        
        # 限制在0-10分之间
        return round(min(max(score, 0.0), 10.0), 2)
    
    def evolve_paths(self, paths: List[List[AttackStep]], analysis: ScanAnalysis) -> List[List[AttackStep]]:
        """
        进化攻击路径（如果启用）
        
        Args:
            paths: 原始路径列表
            analysis: 分析结果对象
            
        Returns:
            进化后的路径列表
        """
        if not self.enable_evolution:
            return paths
        
        evolved_paths: List[List[AttackStep]] = []
        
        for path in paths:
            evolved_path = [step.copy() for step in path]
            
            # 应用进化规则
            EvolutionUtils.apply_evolution_rules(evolved_path, analysis)
            
            evolved_paths.append(evolved_path)
        
        return evolved_paths
    
    def select_best_path(self, evaluated_paths: List[PathEvaluation]) -> Dict[str, Any]:
        """
        选择最佳攻击路径
        
        Args:
            evaluated_paths: 评估后的路径列表
            
        Returns:
            最佳路径信息
        """
        if not evaluated_paths:
            return {
                "path": [],
                "score": 0,
                "type": "unknown",
                "reason": "无可用路径"
            }
        
        # 选择评分最高的路径
        best_path_info = evaluated_paths[0]
        
        return {
            "path": best_path_info.path,
            "score": best_path_info.score,
            "type": best_path_info.type,
            "step_count": best_path_info.step_count,
            "tools_used": best_path_info.tools_used,
            "estimated_duration": best_path_info.estimated_duration,
            "selection_reason": f"规则引擎评分最高 ({best_path_info.score}分)",
            "confidence": min(0.6 + (best_path_info.score / 10.0) * 0.3, 0.95)
        }
    
    def generate_attack_chain(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的攻击链
        
        Args:
            scan_results: 扫描结果
            
        Returns:
            完整的攻击链信息
        """
        try:
            # 分析扫描结果
            analysis = self.analyze_scan_results(scan_results)
            
            # 生成攻击路径
            raw_paths = self.generate_attack_paths(analysis)
            
            # 进化路径（如果启用）
            if self.enable_evolution:
                evolved_paths = self.evolve_paths(raw_paths, analysis)
            else:
                evolved_paths = raw_paths
            
            # 评估路径
            evaluated_paths = self.evaluate_paths(evolved_paths, analysis)
            
            # 选择最佳路径
            best_path = self.select_best_path(evaluated_paths)
            
            # 生成决策信息
            decision_info = DecisionInfo(
                selected_path_type=best_path["type"],
                selected_score=best_path["score"],
                confidence=best_path["confidence"],
                selection_reasons=[best_path["selection_reason"]],
                path_comparison=[
                    {
                        "path_type": path_info.type,
                        "score": path_info.score,
                        "score_difference": round(best_path["score"] - path_info.score, 2),
                        "main_reason": f"评分低{round(best_path['score'] - path_info.score, 2)}分"
                    }
                    for path_info in evaluated_paths[1:3]  # 前2个备选路径
                ],
                decision_factors={
                    "exploitability": round(best_path["score"] * 0.35, 1),
                    "impact": round(best_path["score"] * 0.25, 1),
                    "stealth": round(best_path["score"] * 0.15, 1),
                    "success_rate": round(best_path["score"] * 0.15, 1),
                    "time_efficiency": round(best_path["score"] * 0.10, 1)
                },
                rule_engine_used=True,
                rule_engine_model="rule_engine_v1.0"
            )
            
            # 生成目标分析
            target_analysis = TargetAnalysis(
                attack_surface=analysis.attack_surface,
                open_ports=len(analysis.open_ports),
                vulnerabilities=analysis.vulnerabilities.total,
                critical_vulnerabilities=len(analysis.vulnerabilities.critical),
                high_vulnerabilities=len(analysis.vulnerabilities.high),
                has_cms=analysis.has_cms,
                cms_type=analysis.cms_type,
                waf_detected=analysis.waf_detected,
                waf_type=analysis.waf_type
            )
            
            # 生成执行摘要
            execution_summary = ExecutionSummary(
                total_paths_generated=len(evaluated_paths),
                evolution_applied=self.enable_evolution,
                best_path_score=best_path["score"],
                estimated_duration=best_path["estimated_duration"]
            )
            
            # 构建最终结果
            result = AttackChainResult(
                attack_chain=best_path["path"],
                analysis=analysis,
                decision=decision_info,
                target_analysis=target_analysis,
                execution_summary=execution_summary
            )
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"生成攻击链时出错: {str(e)}")
            return self._generate_fallback_chain()
    
    def _generate_fallback_chain(self) -> Dict[str, Any]:
        """生成回退攻击链"""
        fallback_path = PathBuilder.build_default_path()
        
        return {
            "attack_chain": fallback_path,
            "analysis": {},
            "decision": {
                "selected_path_type": "reconnaissance",
                "selected_score": 5.0,
                "confidence": 0.6,
                "selection_reasons": ["规则引擎默认路径"],
                "path_comparison": [],
                "decision_factors": {
                    "exploitability": 5.0,
                    "impact": 5.0,
                    "stealth": 5.0,
                    "success_rate": 5.0,
                    "time_efficiency": 5.0
                },
                "rule_engine_used": True,
                "rule_engine_model": "rule_engine_v1.0"
            },
            "target_analysis": {
                "attack_surface": 5.0,
                "open_ports": 0,
                "vulnerabilities": 0,
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
                "has_cms": False,
                "cms_type": None,
                "waf_detected": False,
                "waf_type": None
            },
            "execution_summary": {
                "total_paths_generated": 1,
                "evolution_applied": False,
                "best_path_score": 5.0,
                "estimated_duration": "14.4秒"
            }
        }
    
    def test_generator(self) -> bool:
        """测试生成器功能"""
        try:
            # 测试数据
            test_results = {
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
                    "waf_detected": False,
                    "waf_type": None
                }
            }
            
            # 生成攻击链
            result = self.generate_attack_chain(test_results)
            
            # 验证结果
            if not result or "attack_chain" not in result:
                logger.error("测试失败：未生成攻击链")
                return False
            
            attack_chain = result["attack_chain"]
            if not isinstance(attack_chain, list) or len(attack_chain) == 0:
                logger.error("测试失败：攻击链为空")
                return False
            
            # 验证步骤格式
            for step in attack_chain:
                required_keys = ["step", "tool", "phase", "duration", "description", "success"]
                if not all(key in step for key in required_keys):
                    logger.error(f"测试失败：步骤格式不正确: {step}")
                    return False
            
            logger.info("生成器测试通过")
            return True
            
        except Exception as e:
            logger.error(f"生成器测试失败: {str(e)}")
            return False


def main():
    """主测试函数"""
    import json
    
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=" * 80)
    print("统一攻击链生成器测试")
    print("=" * 80)
    
    # 创建生成器
    generator = UnifiedAttackGenerator(enable_evolution=True)
    
    # 测试数据
    test_results = {
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
                {"name": "Remote Code Execution", "severity": "critical"},
                {"name": "SQL Injection", "severity": "high"}
            ]
        },
        "wafw00f": {
            "waf_detected": True,
            "waf_type": "Cloudflare"
        }
    }
    
    print("\n测试数据:")
    print(json.dumps(test_results, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("生成攻击链...")
    
    # 生成攻击链
    result = generator.generate_attack_chain(test_results)
    
    print("\n攻击链结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("攻击链步骤:")
    for step in result["attack_chain"]:
        print(f"步骤 {step['step']}: [{step['tool']}] {step['description']} ({step['duration']})")
    
    print(f"\n攻击评分: {result['decision']['selected_score']}")
    print(f"置信度: {result['decision']['confidence']*100}%")
    print(f"路径类型: {result['decision']['selected_path_type']}")
    print(f"攻击面评分: {result['target_analysis']['attack_surface']}/10")
    print(f"开放端口: {result['target_analysis']['open_ports']}")
    print(f"漏洞数量: {result['target_analysis']['vulnerabilities']}")
    print(f"严重漏洞: {result['target_analysis']['critical_vulnerabilities']}")
    
    print("\n" + "=" * 80)
    print("测试生成器功能...")
    if generator.test_generator():
        print("✅ 生成器测试通过")
    else:
        print("❌ 生成器测试失败")
    
    print("\n" + "=" * 80)
    print("测试完成！")


if __name__ == "__main__":
    main()
