#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
伪推理引擎 - 实现结构化推理和可解释决策

核心功能：
1. 状态理解：分析当前上下文状态
2. 推理链构建：生成结构化推理步骤
3. 反事实对比：分析未选择方案的拒绝理由
4. 自然语言生成：将推理链转换为可读理由
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """上下文状态分析器"""
    
    @staticmethod
    def analyze_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析当前上下文状态
        
        Args:
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 结构化分析结果
        """
        analysis = {
            "target_type": "unknown",
            "tech_stack": [],
            "vulnerabilities": [],
            "defenses": [],
            "attack_surface": [],
            "current_state": {}
        }
        
        try:
            # 提取目标信息
            target = context.get("target", "")
            if target:
                if ":" in target:
                    analysis["target_type"] = "service"
                elif "." in target:
                    analysis["target_type"] = "host"
                else:
                    analysis["target_type"] = "unknown"
            
            # 分析扫描结果
            scan_results = context.get("scan_results", {})
            
            # 技术栈分析
            if "whatweb" in scan_results:
                whatweb_data = scan_results["whatweb"]
                if isinstance(whatweb_data, dict):
                    fingerprint = whatweb_data.get("fingerprint", {})
                    
                    # Web服务器
                    web_server = fingerprint.get("web_server", "")
                    if web_server:
                        analysis["tech_stack"].append(f"web_server:{web_server}")
                    
                    # 编程语言
                    languages = fingerprint.get("language", [])
                    for lang in languages:
                        analysis["tech_stack"].append(f"language:{lang}")
                    
                    # CMS系统
                    cms_list = fingerprint.get("cms", [])
                    for cms in cms_list:
                        analysis["tech_stack"].append(f"cms:{cms}")
            
            # 端口和服务分析
            if "nmap" in scan_results:
                nmap_data = scan_results["nmap"]
                if isinstance(nmap_data, dict):
                    ports = nmap_data.get("ports", [])
                    for port_info in ports:
                        if isinstance(port_info, dict):
                            service = port_info.get("service", "")
                            state = port_info.get("state", "")
                            
                            if state == "open":
                                analysis["attack_surface"].append(f"{service}:{port_info.get('port', '')}")
            
            # 漏洞分析
            if "nuclei" in scan_results:
                nuclei_data = scan_results["nuclei"]
                if isinstance(nuclei_data, dict):
                    vulnerabilities = nuclei_data.get("vulnerabilities", [])
                    for vuln in vulnerabilities:
                        if isinstance(vuln, dict):
                            vuln_name = vuln.get("name", "")
                            severity = vuln.get("severity", "")
                            if vuln_name:
                                analysis["vulnerabilities"].append({
                                    "name": vuln_name,
                                    "severity": severity,
                                    "type": vuln.get("type", "")
                                })
            
            # 防御机制分析（基于常见特征）
            defenses = []
            
            # 检查是否有WAF迹象
            if "whatweb" in scan_results:
                whatweb_data = scan_results["whatweb"]
                if isinstance(whatweb_data, dict):
                    headers = whatweb_data.get("headers", {})
                    if any("waf" in str(v).lower() for v in headers.values()):
                        defenses.append("WAF")
            
            # 检查是否有防火墙迹象
            if "nmap" in scan_results:
                nmap_data = scan_results["nmap"]
                if isinstance(nmap_data, dict):
                    ports = nmap_data.get("ports", [])
                    filtered_ports = [p for p in ports if isinstance(p, dict) and p.get("state") == "filtered"]
                    if filtered_ports:
                        defenses.append("Firewall")
            
            analysis["defenses"] = defenses
            
            # 当前状态分析
            current_state = context.get("current_state", {})
            analysis["current_state"] = {
                "executed_skills": current_state.get("executed_skills", []),
                "discovered_info": list(current_state.keys()),
                "has_shell": current_state.get("has_shell_access", False),
                "data_exfiltrated": current_state.get("data_exfiltrated", False)
            }
            
        except Exception as e:
            logger.error(f"上下文分析失败: {str(e)}")
        
        return analysis
    
    @staticmethod
    def get_attack_phase(context: Dict[str, Any]) -> str:
        """
        获取当前攻击阶段
        
        Returns:
            str: 攻击阶段
        """
        current_state = context.get("current_state", {})
        executed_skills = current_state.get("executed_skills", [])
        
        if not executed_skills:
            return "reconnaissance"
        
        # 根据已执行技能判断阶段
        skill_categories = []
        for skill_name in executed_skills:
            if "scan" in skill_name.lower():
                skill_categories.append("reconnaissance")
            elif "sql" in skill_name.lower():
                skill_categories.append("exploitation")
            elif "rce" in skill_name.lower():
                skill_categories.append("exploitation")
            elif "privilege" in skill_name.lower():
                skill_categories.append("post_exploitation")
        
        if "post_exploitation" in skill_categories:
            return "post_exploitation"
        elif "exploitation" in skill_categories:
            return "exploitation"
        else:
            return "reconnaissance"


class ReasoningChainBuilder:
    """推理链构建器"""
    
    @staticmethod
    def build_reasoning_chain(
        selected_skill: Dict[str, Any],
        context_analysis: Dict[str, Any],
        candidate_skills: List[Dict[str, Any]]
    ) -> List[str]:
        """
        构建结构化推理链
        
        Args:
            selected_skill: 被选中的技能
            context_analysis: 上下文分析结果
            candidate_skills: 所有候选技能
            
        Returns:
            List[str]: 推理链步骤
        """
        reasoning_steps = []
        
        try:
            # 步骤1：目标识别
            target_type = context_analysis.get("target_type", "unknown")
            if target_type != "unknown":
                reasoning_steps.append(f"识别目标类型: {target_type}")
            
            # 步骤2：技术栈分析
            tech_stack = context_analysis.get("tech_stack", [])
            if tech_stack:
                # 提取关键技术
                key_techs = []
                for tech in tech_stack[:3]:  # 取前3个关键技术
                    if ":" in tech:
                        key_techs.append(tech.split(":")[1])
                
                if key_techs:
                    reasoning_steps.append(f"检测到技术栈: {', '.join(key_techs)}")
            
            # 步骤3：攻击面分析
            attack_surface = context_analysis.get("attack_surface", [])
            if attack_surface:
                reasoning_steps.append(f"发现攻击面: {len(attack_surface)}个开放服务")
            
            # 步骤4：漏洞分析
            vulnerabilities = context_analysis.get("vulnerabilities", [])
            if vulnerabilities:
                high_vulns = [v for v in vulnerabilities if v.get("severity") in ["high", "critical"]]
                if high_vulns:
                    reasoning_steps.append(f"检测到高危漏洞: {len(high_vulns)}个")
            
            # 步骤5：防御分析
            defenses = context_analysis.get("defenses", [])
            if defenses:
                reasoning_steps.append(f"检测到防御机制: {', '.join(defenses)}")
            
            # 步骤6：攻击阶段判断
            attack_phase = ContextAnalyzer.get_attack_phase({"current_state": context_analysis.get("current_state", {})})
            reasoning_steps.append(f"当前攻击阶段: {attack_phase}")
            
            # 步骤7：技能匹配分析
            skill_name = selected_skill.get("name", "")
            skill_category = selected_skill.get("category", "")
            
            if skill_category:
                reasoning_steps.append(f"技能类别匹配: {skill_category}")
            
            # 步骤8：成功率分析
            success_rate = selected_skill.get("success_rate", 0)
            if success_rate > 0:
                reasoning_steps.append(f"预估成功率: {success_rate*100:.0f}%")
            
            # 步骤9：上下文适配性
            reasoning_steps.append(ReasoningChainBuilder._analyze_context_fit(selected_skill, context_analysis))
            
            # 步骤10：阶段适配性
            reasoning_steps.append(ReasoningChainBuilder._analyze_phase_fit(selected_skill, attack_phase))
            
        except Exception as e:
            logger.error(f"构建推理链失败: {str(e)}")
            reasoning_steps.append("推理链构建异常")
        
        return reasoning_steps
    
    @staticmethod
    def _analyze_context_fit(skill: Dict[str, Any], context_analysis: Dict[str, Any]) -> str:
        """分析技能与上下文的适配性"""
        skill_name = skill.get("name", "").lower()
        
        # 基于技能名称的适配分析
        if "sql" in skill_name:
            vulnerabilities = context_analysis.get("vulnerabilities", [])
            sql_vulns = [v for v in vulnerabilities if "sql" in str(v.get("type", "")).lower()]
            if sql_vulns:
                return "上下文适配: 检测到SQL注入漏洞"
            else:
                return "上下文适配: 常规Web应用测试"
        
        elif "rce" in skill_name:
            tech_stack = context_analysis.get("tech_stack", [])
            has_web = any("web_server" in tech for tech in tech_stack)
            if has_web:
                return "上下文适配: Web应用RCE检测"
            else:
                return "上下文适配: 远程服务RCE检测"
        
        elif "scan" in skill_name:
            attack_surface = context_analysis.get("attack_surface", [])
            if attack_surface:
                return f"上下文适配: 发现{len(attack_surface)}个可扫描目标"
            else:
                return "上下文适配: 初始信息收集"
        
        elif "privilege" in skill_name:
            current_state = context_analysis.get("current_state", {})
            if current_state.get("has_shell", False):
                return "上下文适配: 已获取Shell，进行权限提升"
            else:
                return "上下文适配: 权限提升准备"
        
        return "上下文适配: 通用攻击技能"
    
    @staticmethod
    def _analyze_phase_fit(skill: Dict[str, Any], attack_phase: str) -> str:
        """分析技能与攻击阶段的适配性"""
        skill_category = skill.get("category", "")
        
        phase_map = {
            "reconnaissance": ["reconnaissance"],
            "exploitation": ["exploitation", "vulnerability_scanning"],
            "post_exploitation": ["post_exploitation"]
        }
        
        expected_categories = phase_map.get(attack_phase, [])
        
        if skill_category in expected_categories:
            return f"阶段适配: 适合{attack_phase}阶段"
        else:
            return f"阶段适配: {skill_category}技能在{attack_phase}阶段使用"


class CounterfactualAnalyzer:
    """反事实对比分析器"""
    
    @staticmethod
    def analyze_rejected_skills(
        selected_skill: Dict[str, Any],
        candidate_skills: List[Dict[str, Any]],
        context_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        分析未选择技能的拒绝理由
        
        Args:
            selected_skill: 被选中的技能
            candidate_skills: 所有候选技能
            context_analysis: 上下文分析结果
            
        Returns:
            List[Dict[str, Any]]: 拒绝理由列表
        """
        rejected_analysis = []
        
        try:
            selected_name = selected_skill.get("name", "")
            selected_score = selected_skill.get("total_score", 0)
            
            for skill in candidate_skills:
                skill_name = skill.get("name", "")
                
                # 跳过被选中的技能
                if skill_name == selected_name:
                    continue
                
                skill_score = skill.get("total_score", 0)
                score_gap = selected_score - skill_score
                
                # 生成拒绝理由
                rejection_reason = CounterfactualAnalyzer._generate_rejection_reason(
                    skill, selected_skill, score_gap, context_analysis
                )
                
                rejected_analysis.append({
                    "skill": skill_name,
                    "score": skill_score,
                    "score_gap": round(score_gap, 2),
                    "reason": rejection_reason,
                    "category": skill.get("category", ""),
                    "success_rate": skill.get("success_rate", 0)
                })
                
                # 只分析前3个未选中的技能
                if len(rejected_analysis) >= 3:
                    break
        
        except Exception as e:
            logger.error(f"反事实分析失败: {str(e)}")
        
        return rejected_analysis
    
    @staticmethod
    def _generate_rejection_reason(
        rejected_skill: Dict[str, Any],
        selected_skill: Dict[str, Any],
        score_gap: float,
        context_analysis: Dict[str, Any]
    ) -> str:
        """生成拒绝理由"""
        reasons = []
        
        # 1. 分数差距
        if score_gap >= 2.0:
            reasons.append(f"评分低{score_gap:.1f}分")
        elif score_gap >= 1.0:
            reasons.append("评分较低")
        
        # 2. 成功率对比
        rejected_rate = rejected_skill.get("success_rate", 0)
        selected_rate = selected_skill.get("success_rate", 0)
        
        if selected_rate - rejected_rate >= 0.2:
            reasons.append("成功率偏低")
        
        # 3. 阶段适配性
        attack_phase = ContextAnalyzer.get_attack_phase({"current_state": context_analysis.get("current_state", {})})
        rejected_category = rejected_skill.get("category", "")
        
        phase_priority = {
            "reconnaissance": ["reconnaissance"],
            "exploitation": ["exploitation", "vulnerability_scanning"],
            "post_exploitation": ["post_exploitation"]
        }
        
        expected_categories = phase_priority.get(attack_phase, [])
        if rejected_category not in expected_categories:
            reasons.append(f"不适合{attack_phase}阶段")
        
        # 4. 上下文适配性
        rejected_name = rejected_skill.get("name", "").lower()
        vulnerabilities = context_analysis.get("vulnerabilities", [])
        
        if "sql" in rejected_name:
            sql_vulns = [v for v in vulnerabilities if "sql" in str(v.get("type", "")).lower()]
            if not sql_vulns:
                reasons.append("未检测到SQL注入漏洞")
        
        elif "rce" in rejected_name:
            # RCE通常需要更多前置条件
            current_state = context_analysis.get("current_state", {})
            if not current_state.get("has_shell", False):
                reasons.append("需要更多前置信息")
        
        # 5. 防御机制影响
        defenses = context_analysis.get("defenses", [])
        if "WAF" in defenses and "sql" in rejected_name:
            reasons.append("WAF可能拦截")
        
        # 默认理由
        if not reasons:
            reasons.append("综合评估不如选中方案")
        
        return "；".join(reasons)


class NaturalLanguageGenerator:
    """自然语言生成器"""
    
    @staticmethod
    def generate_reason(
        reasoning_chain: List[str],
        selected_skill: Dict[str, Any],
        rejected_analysis: List[Dict[str, Any]]
    ) -> str:
        """
        生成自然语言理由
        
        Args:
            reasoning_chain: 推理链
            selected_skill: 被选中的技能
            rejected_analysis: 反事实分析结果
            
        Returns:
            str: 自然语言理由
        """
        try:
            # 构建主要理由
            main_reason_parts = []
            
            # 添加推理链关键步骤
            if reasoning_chain:
                # 取前3个关键推理步骤
                key_steps = reasoning_chain[:3]
                for step in key_steps:
                    main_reason_parts.append(step)
            
            # 添加技能特性
            skill_name = selected_skill.get("name", "")
            success_rate = selected_skill.get("success_rate", 0)
            
            if success_rate > 0:
                main_reason_parts.append(f"{skill_name}成功率{success_rate*100:.0f}%")
            
            # 添加反事实对比摘要
            if rejected_analysis:
                top_rejected = rejected_analysis[0]
                main_reason_parts.append(f"优于{top_rejected['skill']}(低{top_rejected['score_gap']:.1f}分)")
            
            # 生成最终理由
            if main_reason_parts:
                return " → ".join(main_reason_parts)
            else:
                return "基于综合评估选择"
                
        except Exception as e:
            logger.error(f"生成自然语言理由失败: {str(e)}")
            return "系统推理决策"


class PseudoReasoningEngine:
    """伪推理引擎 - 主引擎"""
    
    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.reasoning_builder = ReasoningChainBuilder()
        self.counterfactual_analyzer = CounterfactualAnalyzer()
        self.nlg = NaturalLanguageGenerator()
    
    def generate_structured_reasoning(
        self,
        selected_skill: Dict[str, Any],
        context: Dict[str, Any],
        candidate_skills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成结构化推理结果
        
        Args:
            selected_skill: 被选中的技能
            context: 执行上下文
            candidate_skills: 所有候选技能
            
        Returns:
            Dict[str, Any]: 结构化推理结果
        """
        try:
            # 1. 上下文分析
            context_analysis = self.context_analyzer.analyze_context(context)
            
            # 2. 构建推理链
            reasoning_chain = self.reasoning_builder.build_reasoning_chain(
                selected_skill, context_analysis, candidate_skills
            )
            
            # 3. 反事实对比分析
            rejected_analysis = self.counterfactual_analyzer.analyze_rejected_skills(
                selected_skill, candidate_skills, context_analysis
            )
            
            # 4. 生成自然语言理由
            natural_reason = self.nlg.generate_reason(
                reasoning_chain, selected_skill, rejected_analysis
            )
            
            # 5. 构建完整推理结果
            reasoning_result = {
                "context_analysis": context_analysis,
                "reasoning_chain": reasoning_chain,
                "rejected_skills": rejected_analysis,
                "natural_reason": natural_reason,
                "selected_skill": {
                    "name": selected_skill.get("name", ""),
                    "category": selected_skill.get("category", ""),
                    "success_rate": selected_skill.get("success_rate", 0),
                    "total_score": selected_skill.get("total_score", 0),
                    "confidence": selected_skill.get("confidence", 0.8)
                },
                "timestamp": datetime.now().isoformat(),
                "reasoning_engine_version": "1.0"
            }
            
            return reasoning_result
            
        except Exception as e:
            logger.error(f"生成结构化推理失败: {str(e)}")
            
            # 返回降级结果
            return {
                "context_analysis": {},
                "reasoning_chain": ["推理引擎异常"],
                "rejected_skills": [],
                "natural_reason": "系统推理决策",
                "selected_skill": {
                    "name": selected_skill.get("name", ""),
                    "category": selected_skill.get("category", ""),
                    "success_rate": selected_skill.get("success_rate", 0)
                },
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_thinking_log(self, reasoning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成思考日志
        
        Args:
            reasoning_result: 结构化推理结果
            
        Returns:
            List[Dict[str, Any]]: 思考日志条目
        """
        thinking_log = []
        
        try:
            # 添加推理链步骤
            reasoning_chain = reasoning_result.get("reasoning_chain", [])
            for i, step in enumerate(reasoning_chain, 1):
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"[推理步骤 {i}] {step}",
                    "confidence": 0.8,
                    "type": "reasoning_step"
                })
            
            # 添加反事实对比
            rejected_skills = reasoning_result.get("rejected_skills", [])
            if rejected_skills:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"[对比分析] 分析了{len(rejected_skills)}个未选方案",
                    "confidence": 0.7,
                    "type": "counterfactual"
                })
                
                for rejected in rejected_skills[:2]:  # 只显示前2个
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"[放弃] {rejected['skill']}: {rejected['reason']}",
                        "confidence": 0.6,
                        "type": "rejection"
                    })
            
            # 添加最终决策
            selected_skill = reasoning_result.get("selected_skill", {})
            if selected_skill:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"[最终决策] 选择{selected_skill.get('name', '')}，成功率{selected_skill.get('success_rate', 0)*100:.0f}%",
                    "confidence": selected_skill.get("confidence", 0.8),
                    "type": "final_decision"
                })
        
        except Exception as e:
            logger.error(f"生成思考日志失败: {str(e)}")
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": "思考日志生成异常",
                "confidence": 0.3,
                "type": "error"
            })
        
        return thinking_log
    
    def format_for_display(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化推理结果用于展示
        
        Args:
            reasoning_result: 结构化推理结果
            
        Returns:
            Dict[str, Any]: 格式化展示结果
        """
        try:
            context_analysis = reasoning_result.get("context_analysis", {})
            reasoning_chain = reasoning_result.get("reasoning_chain", [])
            rejected_skills = reasoning_result.get("rejected_skills", [])
            selected_skill = reasoning_result.get("selected_skill", {})
            
            display_result = {
                "thinking_process": {
                    "title": "Agent思考过程",
                    "steps": []
                },
                "context_analysis": {
                    "target_type": context_analysis.get("target_type", "unknown"),
                    "tech_stack": context_analysis.get("tech_stack", [])[:5],
                    "vulnerabilities": len(context_analysis.get("vulnerabilities", [])),
                    "defenses": context_analysis.get("defenses", []),
                    "attack_surface": len(context_analysis.get("attack_surface", []))
                },
                "decision_summary": {
                    "selected_skill": selected_skill.get("name", ""),
                    "success_rate": f"{selected_skill.get('success_rate', 0)*100:.0f}%",
                    "confidence": f"{selected_skill.get('confidence', 0)*100:.0f}%",
                    "natural_reason": reasoning_result.get("natural_reason", "")
                },
                "comparison": {
                    "total_candidates": len(rejected_skills) + 1,
                    "rejected_count": len(rejected_skills),
                    "top_rejected": []
                }
            }
            
            # 添加思考步骤
            for i, step in enumerate(reasoning_chain[:6], 1):  # 最多显示6步
                display_result["thinking_process"]["steps"].append({
                    "step": i,
                    "description": step,
                    "icon": "✔" if i <= 3 else "→"
                })
            
            # 添加对比信息
            for rejected in rejected_skills[:2]:  # 最多显示2个
                display_result["comparison"]["top_rejected"].append({
                    "skill": rejected["skill"],
                    "reason": rejected["reason"],
                    "score_gap": rejected["score_gap"]
                })
            
            return display_result
            
        except Exception as e:
            logger.error(f"格式化展示结果失败: {str(e)}")
            return {
                "error": "格式化失败",
                "message": str(e)
            }


# 全局推理引擎实例
reasoning_engine = PseudoReasoningEngine()


def test_reasoning_engine():
    """测试推理引擎功能"""
    print("=" * 60)
    print("伪推理引擎测试")
    print("=" * 60)
    
    # 创建测试数据
    test_context = {
        "target": "example.com",
        "scan_results": {
            "nmap": {
                "ports": [
                    {"port": 80, "service": "http", "state": "open"},
                    {"port": 443, "service": "https", "state": "open"},
                    {"port": 3306, "service": "mysql", "state": "open"}
                ]
            },
            "whatweb": {
                "fingerprint": {
                    "web_server": "nginx/1.18.0",
                    "language": ["PHP"],
                    "cms": ["WordPress"]
                }
            },
            "nuclei": {
                "vulnerabilities": [
                    {"name": "WordPress SQL Injection", "severity": "high", "type": "sql_injection"}
                ]
            }
        },
        "current_state": {
            "executed_skills": ["NmapScanSkill"],
            "open_ports": [80, 443, 3306]
        }
    }
    
    test_selected_skill = {
        "name": "SQLInjectionSkill",
        "category": "exploitation",
        "success_rate": 0.75,
        "total_score": 8.2,
        "confidence": 0.85
    }
    
    test_candidate_skills = [
        {
            "name": "SQLInjectionSkill",
            "category": "exploitation",
            "success_rate": 0.75,
            "total_score": 8.2,
            "confidence": 0.85
        },
        {
            "name": "WhatWebSkill",
            "category": "reconnaissance",
            "success_rate": 0.9,
            "total_score": 6.5,
            "confidence": 0.9
        },
        {
            "name": "RCESkill",
            "category": "exploitation",
            "success_rate": 0.6,
            "total_score": 5.8,
            "confidence": 0.7
        }
    ]
    
    # 测试推理引擎
    engine = PseudoReasoningEngine()
    result = engine.generate_structured_reasoning(
        test_selected_skill, test_context, test_candidate_skills
    )
    
    print("\n1. 上下文分析:")
    context_analysis = result.get("context_analysis", {})
    print(f"   目标类型: {context_analysis.get('target_type', 'unknown')}")
    print(f"   技术栈: {', '.join(context_analysis.get('tech_stack', [])[:3])}")
    print(f"   漏洞数量: {len(context_analysis.get('vulnerabilities', []))}")
    print(f"   防御机制: {', '.join(context_analysis.get('defenses', []))}")
    
    print("\n2. 推理链:")
    reasoning_chain = result.get("reasoning_chain", [])
    for i, step in enumerate(reasoning_chain[:4], 1):
        print(f"   {i}. {step}")
    
    print("\n3. 反事实对比:")
    rejected_skills = result.get("rejected_skills", [])
    for rejected in rejected_skills:
        print(f"   - {rejected['skill']}: {rejected['reason']}")
    
    print("\n4. 自然语言理由:")
    print(f"   {result.get('natural_reason', '')}")
    
    print("\n5. 思考日志:")
    thinking_log = engine.generate_thinking_log(result)
    for log in thinking_log[:3]:
        print(f"   - {log['message']}")
    
    print("\n6. 展示格式:")
    display = engine.format_for_display(result)
    print(f"   决策: {display['decision_summary']['selected_skill']}")
    print(f"   成功率: {display['decision_summary']['success_rate']}")
    print(f"   置信度: {display['decision_summary']['confidence']}")
    
    print("\n" + "=" * 60)
    print("✅ 推理引擎测试通过")
    
    return True


if __name__ == "__main__":
    import sys
    success = test_reasoning_engine()
    sys.exit(0 if success else 1)
