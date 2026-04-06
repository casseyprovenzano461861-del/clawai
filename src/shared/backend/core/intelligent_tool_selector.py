# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能工具选择器模块
基于攻击步骤和上下文智能选择工具和优化参数
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToolCapability:
    """工具能力描述"""
    tool_id: str
    name: str
    capabilities: List[str]  # 支持的能力列表
    efficiency_score: float  # 效率评分 0.0-1.0
    accuracy_score: float   # 准确率评分 0.0-1.0
    stealth_score: float    # 隐蔽性评分 0.0-1.0
    resource_usage: Dict[str, float]  # 资源使用情况


@dataclass
class ToolRecommendation:
    """工具推荐结果"""
    tool_id: str
    name: str
    confidence: float  # 置信度 0.0-1.0
    parameters: Dict[str, Any]
    rationale: str  # 选择理由
    expected_outcome: str
    risk_level: str  # low, medium, high
    alternatives: List[Dict[str, Any]]  # 备选工具


class IntelligentToolSelector:
    """
    智能工具选择器
    基于攻击步骤和上下文智能选择工具和优化参数
    """
    
    def __init__(self, tool_registry=None):
        self.logger = logging.getLogger(__name__)
        self.tool_registry = tool_registry
        
        # 工具能力数据库
        self.tool_capabilities = self._initialize_tool_capabilities()
        
        # 参数优化规则
        self.parameter_rules = self._initialize_parameter_rules()
        
        # 工具组合策略
        self.combination_strategies = self._initialize_combination_strategies()
        
        # 选择历史
        self.selection_history = []
    
    def _initialize_tool_capabilities(self) -> Dict[str, ToolCapability]:
        """初始化工具能力数据库"""
        capabilities = {
            # ===== 网络扫描工具 =====
            "nmap": ToolCapability(
                tool_id="nmap",
                name="Nmap",
                capabilities=["port_scan", "service_detection", "os_detection", "vulnerability_scan"],
                efficiency_score=0.8,
                accuracy_score=0.9,
                stealth_score=0.4,
                resource_usage={"cpu": 0.7, "memory": 0.5, "network": 0.8}
            ),
            "masscan": ToolCapability(
                tool_id="masscan",
                name="Masscan",
                capabilities=["fast_port_scan", "large_scale_scan"],
                efficiency_score=0.9,
                accuracy_score=0.7,
                stealth_score=0.2,
                resource_usage={"cpu": 0.8, "memory": 0.3, "network": 0.9}
            ),
            "rustscan": ToolCapability(
                tool_id="rustscan",
                name="RustScan",
                capabilities=["fast_port_scan", "simple_output"],
                efficiency_score=0.85,
                accuracy_score=0.6,
                stealth_score=0.3,
                resource_usage={"cpu": 0.6, "memory": 0.2, "network": 0.7}
            ),
            
            # ===== Web扫描工具 =====
            "whatweb": ToolCapability(
                tool_id="whatweb",
                name="WhatWeb",
                capabilities=["web_fingerprinting", "technology_detection"],
                efficiency_score=0.7,
                accuracy_score=0.85,
                stealth_score=0.6,
                resource_usage={"cpu": 0.4, "memory": 0.3, "network": 0.3}
            ),
            "nikto": ToolCapability(
                tool_id="nikto",
                name="Nikto",
                capabilities=["web_vulnerability_scan", "configuration_check"],
                efficiency_score=0.6,
                accuracy_score=0.8,
                stealth_score=0.3,
                resource_usage={"cpu": 0.5, "memory": 0.4, "network": 0.6}
            ),
            "nuclei": ToolCapability(
                tool_id="nuclei",
                name="Nuclei",
                capabilities=["template_based_scan", "vulnerability_detection"],
                efficiency_score=0.75,
                accuracy_score=0.85,
                stealth_score=0.5,
                resource_usage={"cpu": 0.6, "memory": 0.5, "network": 0.7}
            ),
            
            # ===== 目录爆破工具 =====
            "dirsearch": ToolCapability(
                tool_id="dirsearch",
                name="Dirsearch",
                capabilities=["directory_bruteforce", "file_discovery"],
                efficiency_score=0.7,
                accuracy_score=0.8,
                stealth_score=0.4,
                resource_usage={"cpu": 0.5, "memory": 0.3, "network": 0.8}
            ),
            "gobuster": ToolCapability(
                tool_id="gobuster",
                name="Gobuster",
                capabilities=["directory_bruteforce", "dns_bruteforce"],
                efficiency_score=0.8,
                accuracy_score=0.75,
                stealth_score=0.5,
                resource_usage={"cpu": 0.6, "memory": 0.2, "network": 0.7}
            ),
            "ffuf": ToolCapability(
                tool_id="ffuf",
                name="FFUF",
                capabilities=["web_fuzzing", "parameter_fuzzing"],
                efficiency_score=0.85,
                accuracy_score=0.7,
                stealth_score=0.6,
                resource_usage={"cpu": 0.7, "memory": 0.4, "network": 0.9}
            ),
            
            # ===== 漏洞利用工具 =====
            "sqlmap": ToolCapability(
                tool_id="sqlmap",
                name="SQLMap",
                capabilities=["sql_injection", "database_fingerprinting", "data_extraction"],
                efficiency_score=0.9,
                accuracy_score=0.95,
                stealth_score=0.2,
                resource_usage={"cpu": 0.8, "memory": 0.6, "network": 0.7}
            ),
            "xsstrike": ToolCapability(
                tool_id="xsstrike",
                name="XSStrike",
                capabilities=["xss_detection", "payload_generation"],
                efficiency_score=0.7,
                accuracy_score=0.8,
                stealth_score=0.4,
                resource_usage={"cpu": 0.5, "memory": 0.3, "network": 0.5}
            ),
            "commix": ToolCapability(
                tool_id="commix",
                name="Commix",
                capabilities=["command_injection", "os_command_execution"],
                efficiency_score=0.75,
                accuracy_score=0.7,
                stealth_score=0.3,
                resource_usage={"cpu": 0.6, "memory": 0.4, "network": 0.6}
            ),
            
            # ===== CMS扫描工具 =====
            "wpscan": ToolCapability(
                tool_id="wpscan",
                name="WPScan",
                capabilities=["wordpress_scan", "plugin_vulnerability"],
                efficiency_score=0.8,
                accuracy_score=0.9,
                stealth_score=0.5,
                resource_usage={"cpu": 0.7, "memory": 0.5, "network": 0.6}
            ),
            "joomscan": ToolCapability(
                tool_id="joomscan",
                name="JoomScan",
                capabilities=["joomla_scan", "extension_vulnerability"],
                efficiency_score=0.7,
                accuracy_score=0.8,
                stealth_score=0.5,
                resource_usage={"cpu": 0.6, "memory": 0.4, "network": 0.5}
            ),
            
            # ===== 密码破解工具 =====
            "hydra": ToolCapability(
                tool_id="hydra",
                name="Hydra",
                capabilities=["password_bruteforce", "protocol_support"],
                efficiency_score=0.85,
                accuracy_score=0.6,
                stealth_score=0.1,
                resource_usage={"cpu": 0.9, "memory": 0.3, "network": 0.8}
            ),
            "medusa": ToolCapability(
                tool_id="medusa",
                name="Medusa",
                capabilities=["parallel_bruteforce", "module_based"],
                efficiency_score=0.8,
                accuracy_score=0.65,
                stealth_score=0.2,
                resource_usage={"cpu": 0.8, "memory": 0.4, "network": 0.7}
            ),
            
            # ===== 后渗透工具 =====
            "metasploit": ToolCapability(
                tool_id="metasploit",
                name="Metasploit",
                capabilities=["exploitation", "post_exploitation", "payload_generation"],
                efficiency_score=0.7,
                accuracy_score=0.85,
                stealth_score=0.3,
                resource_usage={"cpu": 0.8, "memory": 0.7, "network": 0.6}
            ),
            "crackmapexec": ToolCapability(
                tool_id="crackmapexec",
                name="CrackMapExec",
                capabilities=["lateral_movement", "credential_abuse", "service_enumeration"],
                efficiency_score=0.75,
                accuracy_score=0.8,
                stealth_score=0.4,
                resource_usage={"cpu": 0.7, "memory": 0.5, "network": 0.7}
            )
        }
        
        return capabilities
    
    def _initialize_parameter_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化参数优化规则"""
        rules = {
            # ===== 通用规则 =====
            "stealth_mode": {
                "conditions": {"stealth_required": True},
                "parameters": {
                    "threads": 1,
                    "rate": "10/s",
                    "delay": "1-3s",
                    "timeout": 30,
                    "retries": 1,
                    "user_agent": "random"
                }
            },
            "performance_mode": {
                "conditions": {"performance_priority": True, "stealth_required": False},
                "parameters": {
                    "threads": 10,
                    "rate": "1000/s",
                    "delay": "0s",
                    "timeout": 10,
                    "retries": 3,
                    "user_agent": "default"
                }
            },
            "balanced_mode": {
                "conditions": {},  # 默认条件
                "parameters": {
                    "threads": 5,
                    "rate": "100/s",
                    "delay": "0.5s",
                    "timeout": 20,
                    "retries": 2,
                    "user_agent": "common"
                }
            },
            
            # ===== 针对工具类型的特定规则 =====
            "port_scanner": {
                "conditions": {"tool_category": "port_scan"},
                "parameters": {
                    "scan_type": "syn",
                    "ports": "1-1000",
                    "max_retries": 2,
                    "host_timeout": 120
                }
            },
            "web_scanner": {
                "conditions": {"tool_category": "web_scan"},
                "parameters": {
                    "depth": 3,
                    "extensions": "php,asp,aspx,jsp,html,htm",
                    "follow_redirects": True,
                    "verify_ssl": False
                }
            },
            "bruteforce": {
                "conditions": {"tool_category": "bruteforce"},
                "parameters": {
                    "username_list": "common_users.txt",
                    "password_list": "common_passwords.txt",
                    "stop_on_success": True,
                    "continue_on_failure": False
                }
            }
        }
        
        return rules
    
    def _initialize_combination_strategies(self) -> Dict[str, Dict[str, Any]]:
        """初始化工具组合策略"""
        strategies = {
            "complementary": {
                "description": "互补组合 - 覆盖不同攻击面",
                "criteria": {
                    "coverage": "high",
                    "redundancy": "low",
                    "efficiency": "medium"
                },
                "examples": [
                    ["nmap", "whatweb", "nikto"],  # 全面Web扫描
                    ["masscan", "nuclei", "sqlmap"]  # 快速漏洞扫描
                ]
            },
            "redundant": {
                "description": "冗余组合 - 提高成功率",
                "criteria": {
                    "coverage": "medium",
                    "redundancy": "high",
                    "efficiency": "low"
                },
                "examples": [
                    ["dirsearch", "gobuster", "ffuf"],  # 多个目录爆破工具
                    ["hydra", "medusa"]  # 多个密码破解工具
                ]
            },
            "progressive": {
                "description": "递进组合 - 从简单到复杂",
                "criteria": {
                    "coverage": "high",
                    "redundancy": "low",
                    "efficiency": "high"
                },
                "examples": [
                    ["nmap", "nikto", "sqlmap"],  # 递进Web测试
                    ["whatweb", "wpscan", "metasploit"]  # 递进CMS攻击
                ]
            },
            "parallel": {
                "description": "并行组合 - 提高效率",
                "criteria": {
                    "coverage": "medium",
                    "redundancy": "medium",
                    "efficiency": "high"
                },
                "examples": [
                    ["masscan", "whatweb"],  # 并行端口扫描和指纹识别
                    ["dirsearch", "nikto"]  # 并行目录爆破和漏洞扫描
                ]
            }
        }
        
        return strategies
    
    def select_tools(
        self, 
        attack_step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[ToolRecommendation]:
        """
        选择工具
        
        Args:
            attack_step: 攻击步骤描述
            context: 上下文信息
            
        Returns:
            List[ToolRecommendation]: 工具推荐列表
        """
        self.logger.info(f"为攻击步骤选择工具: {attack_step.get('description', '未知步骤')}")
        
        # 1. 获取候选工具
        candidate_tools = self._get_candidate_tools(attack_step)
        
        if not candidate_tools:
            self.logger.warning("没有找到候选工具，返回空列表")
            return []
        
        # 2. 评估工具能力
        evaluated_tools = self._evaluate_tool_capabilities(candidate_tools, attack_step, context)
        
        # 3. 优化工具组合
        tool_combinations = self._optimize_tool_combinations(evaluated_tools, context)
        
        # 4. 优化参数
        optimized_tools = self._optimize_parameters(tool_combinations, context)
        
        # 5. 记录选择历史
        self._record_selection_history(attack_step, optimized_tools, context)
        
        return optimized_tools
    
    def _get_candidate_tools(self, attack_step: Dict[str, Any]) -> List[str]:
        """获取候选工具"""
        step_type = attack_step.get("type", "")
        required_capabilities = attack_step.get("required_capabilities", [])
        
        candidate_tools = []
        
        for tool_id, capability in self.tool_capabilities.items():
            # 检查工具是否满足步骤类型要求
            if step_type and not self._matches_step_type(tool_id, step_type):
                continue
            
            # 检查工具是否满足能力要求
            if required_capabilities:
                if not all(cap in capability.capabilities for cap in required_capabilities):
                    continue
            
            candidate_tools.append(tool_id)
        
        # 如果没有特定要求，返回所有工具
        if not candidate_tools and not step_type and not required_capabilities:
            candidate_tools = list(self.tool_capabilities.keys())
        
        self.logger.debug(f"找到 {len(candidate_tools)} 个候选工具: {candidate_tools}")
        return candidate_tools
    
    def _matches_step_type(self, tool_id: str, step_type: str) -> bool:
        """检查工具是否匹配步骤类型"""
        # 步骤类型到工具类别的映射
        step_type_mapping = {
            "reconnaissance": ["port_scan", "web_fingerprinting"],
            "scanning": ["vulnerability_scan", "web_scan"],
            "exploitation": ["sql_injection", "command_injection", "exploitation"],
            "bruteforce": ["password_bruteforce"],
            "post_exploitation": ["post_exploitation", "lateral_movement"]
        }
        
        if step_type not in step_type_mapping:
            return True  # 未知步骤类型，不进行过滤
        
        tool_capability = self.tool_capabilities.get(tool_id)
        if not tool_capability:
            return False
        
        # 检查工具是否有匹配的能力
        required_capabilities = step_type_mapping[step_type]
        return any(cap in tool_capability.capabilities for cap in required_capabilities)
    
    def _evaluate_tool_capabilities(
        self, 
        candidate_tools: List[str], 
        attack_step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """评估工具能力"""
        evaluated_tools = []
        
        for tool_id in candidate_tools:
            capability = self.tool_capabilities.get(tool_id)
            if not capability:
                continue
            
            # 计算综合评分
            overall_score = self._calculate_overall_score(capability, attack_step, context)
            
            evaluated_tools.append({
                "tool_id": tool_id,
                "name": capability.name,
                "capabilities": capability.capabilities,
                "efficiency_score": capability.efficiency_score,
                "accuracy_score": capability.accuracy_score,
                "stealth_score": capability.stealth_score,
                "resource_usage": capability.resource_usage,
                "overall_score": overall_score,
                "suitability": self._assess_suitability(capability, attack_step, context)
            })
        
        # 按综合评分排序
        evaluated_tools.sort(key=lambda x: x["overall_score"], reverse=True)
        return evaluated_tools
    
    def _calculate_overall_score(
        self, 
        capability: ToolCapability, 
        attack_step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """计算综合评分"""
        # 基础权重
        weights = {
            "efficiency": 0.3,
            "accuracy": 0.4,
            "stealth": 0.3
        }
        
        # 根据上下文调整权重
        if context.get("stealth_required", False):
            weights["stealth"] = 0.5
            weights["efficiency"] = 0.2
            weights["accuracy"] = 0.3
        
        if context.get("performance_priority", False):
            weights["efficiency"] = 0.5
            weights["accuracy"] = 0.3
            weights["stealth"] = 0.2
        
        if context.get("accuracy_priority", False):
            weights["accuracy"] = 0.6
            weights["efficiency"] = 0.2
            weights["stealth"] = 0.2
        
        # 计算加权平均
        overall_score = (
            capability.efficiency_score * weights["efficiency"] +
            capability.accuracy_score * weights["accuracy"] +
            capability.stealth_score * weights["stealth"]
        )
        
        return round(overall_score, 3)
    
    def _assess_suitability(
        self, 
        capability: ToolCapability, 
        attack_step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """评估适用性"""
        score = self._calculate_overall_score(capability, attack_step, context)
        
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _optimize_tool_combinations(
        self, 
        evaluated_tools: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[List[Dict[str, Any]]]:
        """优化工具组合"""
        if not evaluated_tools:
            return []
        
        # 确定组合策略
        combination_strategy = self._select_combination_strategy(context)
        
        # 根据策略生成组合
        if combination_strategy == "complementary":
            combinations = self._generate_complementary_combinations(evaluated_tools)
        elif combination_strategy == "redundant":
            combinations = self._generate_redundant_combinations(evaluated_tools)
        elif combination_strategy == "progressive":
            combinations = self._generate_progressive_combinations(evaluated_tools)
        elif combination_strategy == "parallel":
            combinations = self._generate_parallel_combinations(evaluated_tools)
        else:
            # 默认：选择评分最高的单个工具
            combinations = [[evaluated_tools[0]]]
        
        # 限制组合数量
        max_combinations = context.get("max_combinations", 3)
        combinations = combinations[:max_combinations]
        
        self.logger.debug(f"生成 {len(combinations)} 个工具组合（策略: {combination_strategy}）")
        return combinations
    
    def _select_combination_strategy(self, context: Dict[str, Any]) -> str:
        """选择组合策略"""
        # 根据上下文选择策略
        if context.get("coverage_priority", False):
            return "complementary"
        elif context.get("success_priority", False):
            return "redundant"
        elif context.get("efficiency_priority", False):
            return "parallel"
        elif context.get("thoroughness_priority", False):
            return "progressive"
        
        # 默认策略
        return "complementary"
    
    def _generate_complementary_combinations(
        self, 
        evaluated_tools: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """生成互补组合"""
        combinations = []
        
        # 按能力分组
        tools_by_capability = {}
        for tool in evaluated_tools:
            for capability in tool["capabilities"]:
                if capability not in tools_by_capability:
                    tools_by_capability[capability] = []
                tools_by_capability[capability].append(tool)
        
        # 生成覆盖多种能力的组合
        important_capabilities = ["port_scan", "web_fingerprinting", "vulnerability_scan", "exploitation"]
        
        for cap in important_capabilities:
            if cap in tools_by_capability and tools_by_capability[cap]:
                combination = [tools_by_capability[cap][0]]  # 选择该能力的最佳工具
                
                # 添加其他能力的最佳工具
                for other_cap in important_capabilities:
                    if other_cap != cap and other_cap in tools_by_capability and tools_by_capability[other_cap]:
                        other_tool = tools_by_capability[other_cap][0]
                        if other_tool not in combination:
                            combination.append(other_tool)
                
                if len(combination) > 1:
                    combinations.append(combination)
        
        # 如果没有生成组合，返回单个最佳工具
        if not combinations:
            combinations = [[evaluated_tools[0]]]
        
        return combinations
    
    def _generate_redundant_combinations(
        self, 
        evaluated_tools: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """生成冗余组合"""
        combinations = []
        
        # 选择评分最高的工具，然后添加类似工具
        if evaluated_tools:
            primary_tool = evaluated_tools[0]
            combination = [primary_tool]
            
            # 添加具有类似能力的工具
            primary_capabilities = set(primary_tool["capabilities"])
            
            for tool in evaluated_tools[1:4]:  # 考虑前几个工具
                tool_capabilities = set(tool["capabilities"])
                similarity = len(primary_capabilities.intersection(tool_capabilities)) / len(primary_capabilities)
                
                if similarity >= 0.6:  # 相似度超过60%
                    combination.append(tool)
            
            combinations.append(combination)
        
        return combinations
    
    def _generate_progressive_combinations(
        self, 
        evaluated_tools: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """生成递进组合"""
        combinations = []
        
        # 简单到复杂的递进组合
        if len(evaluated_tools) >= 2:
            # 按复杂性排序（假设评分较低的工具更简单）
            sorted_tools = sorted(evaluated_tools, key=lambda x: x["overall_score"])
            
            # 生成2-3步的递进组合
            for i in range(min(3, len(sorted_tools) - 1)):
                combination = sorted_tools[i:i+2]
                combinations.append(combination)
        
        return combinations
    
    def _generate_parallel_combinations(
        self, 
        evaluated_tools: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """生成并行组合"""
        combinations = []
        
        # 选择资源使用不冲突的工具进行并行
        if evaluated_tools:
            combination = [evaluated_tools[0]]
            
            for tool in evaluated_tools[1:3]:  # 考虑前几个工具
                # 检查资源使用是否冲突（简单的启发式规则）
                resource_conflict = False
                for resource in ["cpu", "memory", "network"]:
                    if tool["resource_usage"].get(resource, 0) + combination[0]["resource_usage"].get(resource, 0) > 1.5:
                        resource_conflict = True
                        break
                
                if not resource_conflict:
                    combination.append(tool)
            
            combinations.append(combination)
        
        return combinations
    
    def _optimize_parameters(
        self, 
        tool_combinations: List[List[Dict[str, Any]]], 
        context: Dict[str, Any]
    ) -> List[ToolRecommendation]:
        """优化参数"""
        optimized_recommendations = []
        
        for combination in tool_combinations:
            for tool_info in combination:
                # 生成优化参数
                optimized_params = self._generate_optimized_parameters(tool_info, context)
                
                # 生成推荐理由
                rationale = self._generate_recommendation_rationale(tool_info, context)
                
                # 计算置信度
                confidence = self._calculate_recommendation_confidence(tool_info, optimized_params)
                
                # 生成备选工具
                alternatives = self._generate_alternatives(tool_info, combination)
                
                # 创建推荐对象
                recommendation = ToolRecommendation(
                    tool_id=tool_info["tool_id"],
                    name=tool_info["name"],
                    confidence=confidence,
                    parameters=optimized_params,
                    rationale=rationale,
                    expected_outcome=self._generate_expected_outcome(tool_info),
                    risk_level=self._assess_risk_level(tool_info, optimized_params),
                    alternatives=alternatives
                )
                
                optimized_recommendations.append(recommendation)
        
        return optimized_recommendations
    
    def _generate_optimized_parameters(
        self, 
        tool_info: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成优化参数"""
        # 基础参数
        base_params = {
            "tool": tool_info["tool_id"],
            "timeout": 30,
            "retries": 2,
            "verbose": False
        }
        
        # 应用参数优化规则
        for rule_name, rule in self.parameter_rules.items():
            if self._rule_matches_conditions(rule["conditions"], tool_info, context):
                base_params.update(rule["parameters"])
                break
        
        # 基于上下文进一步优化
        if context.get("stealth_required", False):
            base_params.update({
                "threads": max(1, base_params.get("threads", 5) // 2),
                "delay": "2-5s",
                "rate": "5/s"
            })
        
        if context.get("performance_priority", False):
            base_params.update({
                "threads": base_params.get("threads", 5) * 2,
                "delay": "0s",
                "rate": "500/s"
            })
        
        # 基于工具类型的特定优化
        tool_capabilities = self.tool_capabilities.get(tool_info["tool_id"])
        if tool_capabilities:
            if "port_scan" in tool_capabilities.capabilities:
                base_params.update({
                    "ports": context.get("target_ports", "1-1000"),
                    "scan_type": "syn"
                })
            elif "web_scan" in tool_capabilities.capabilities:
                base_params.update({
                    "target": context.get("target_url", ""),
                    "depth": 3
                })
            elif "bruteforce" in tool_capabilities.capabilities:
                base_params.update({
                    "username_list": "common_users.txt",
                    "password_list": "rockyou.txt"
                })
        
        return base_params
    
    def _rule_matches_conditions(
        self, 
        conditions: Dict[str, Any], 
        tool_info: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> bool:
        """检查规则条件是否匹配"""
        for key, expected_value in conditions.items():
            # 检查上下文
            if key in context:
                if context[key] != expected_value:
                    return False
            # 检查工具信息
            elif key in tool_info:
                if tool_info[key] != expected_value:
                    return False
            else:
                return False
        
        return True
    
    def _generate_recommendation_rationale(
        self, 
        tool_info: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """生成推荐理由"""
        rationale_parts = []
        
        # 基于评分
        score = tool_info.get("overall_score", 0)
        if score >= 0.8:
            rationale_parts.append("综合评分优秀")
        elif score >= 0.6:
            rationale_parts.append("综合评分良好")
        
        # 基于适用性
        suitability = tool_info.get("suitability", "fair")
        if suitability == "excellent":
            rationale_parts.append("非常适合当前场景")
        elif suitability == "good":
            rationale_parts.append("适合当前场景")
        
        # 基于上下文
        if context.get("stealth_required", False):
            stealth_score = tool_info.get("stealth_score", 0)
            if stealth_score >= 0.7:
                rationale_parts.append("隐蔽性高")
        
        if context.get("performance_priority", False):
            efficiency_score = tool_info.get("efficiency_score", 0)
            if efficiency_score >= 0.7:
                rationale_parts.append("执行效率高")
        
        # 默认理由
        if not rationale_parts:
            rationale_parts.append("根据能力和上下文评估推荐")
        
        return "；".join(rationale_parts)
    
    def _calculate_recommendation_confidence(
        self, 
        tool_info: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> float:
        """计算推荐置信度"""
        # 基础置信度基于工具评分
        base_confidence = tool_info.get("overall_score", 0.5)
        
        # 参数优化程度调整
        param_optimization_bonus = 0.0
        
        # 检查是否有针对性的参数优化
        if parameters.get("threads") != 5:  # 默认值
            param_optimization_bonus += 0.1
        
        if parameters.get("delay") != "0.5s":  # 默认值
            param_optimization_bonus += 0.1
        
        # 最终置信度
        confidence = min(base_confidence + param_optimization_bonus, 0.95)
        return round(confidence, 2)
    
    def _generate_alternatives(
        self, 
        tool_info: Dict[str, Any], 
        combination: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成备选工具"""
        alternatives = []
        
        # 当前组合中的其他工具作为备选
        for other_tool in combination:
            if other_tool["tool_id"] != tool_info["tool_id"]:
                alternatives.append({
                    "tool_id": other_tool["tool_id"],
                    "name": other_tool["name"],
                    "reason": f"同组合备选工具，{other_tool.get('suitability', '未知')}适用性"
                })
        
        # 如果没有备选，添加评分次高的工具
        if not alternatives:
            # 这里简化处理，实际应该从所有工具中选择
            pass
        
        return alternatives[:2]  # 最多返回2个备选
    
    def _generate_expected_outcome(self, tool_info: Dict[str, Any]) -> str:
        """生成预期结果"""
        tool_id = tool_info["tool_id"]
        
        outcome_map = {
            "nmap": "发现开放端口、服务和操作系统信息",
            "masscan": "快速发现开放端口",
            "whatweb": "识别Web技术栈和框架",
            "nikto": "发现Web服务器漏洞和配置问题",
            "nuclei": "基于模板发现漏洞",
            "dirsearch": "发现隐藏目录和文件",
            "sqlmap": "检测和利用SQL注入漏洞",
            "wpscan": "发现WordPress漏洞",
            "hydra": "尝试暴力破解登录凭证",
            "metasploit": "利用漏洞并建立访问"
        }
        
        return outcome_map.get(tool_id, "执行安全测试并返回结果")
    
    def _assess_risk_level(
        self, 
        tool_info: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> str:
        """评估风险等级"""
        tool_id = tool_info["tool_id"]
        
        # 高风险工具
        high_risk_tools = ["sqlmap", "hydra", "metasploit", "commix", "xsstrike"]
        
        # 中风险工具
        medium_risk_tools = ["nikto", "nuclei", "wpscan", "crackmapexec"]
        
        if tool_id in high_risk_tools:
            # 检查是否有降低风险的参数
            if parameters.get("stealth_mode", False) or parameters.get("threads", 10) <= 2:
                return "medium"
            return "high"
        
        elif tool_id in medium_risk_tools:
            return "medium"
        
        else:
            return "low"
    
    def _record_selection_history(
        self, 
        attack_step: Dict[str, Any], 
        recommendations: List[ToolRecommendation], 
        context: Dict[str, Any]
    ):
        """记录选择历史"""
        import time
        
        record = {
            "timestamp": time.time(),
            "attack_step": attack_step.get("description", "未知步骤"),
            "step_type": attack_step.get("type", "未知"),
            "context_summary": {
                "stealth_required": context.get("stealth_required", False),
                "performance_priority": context.get("performance_priority", False)
            },
            "recommendations": [
                {
                    "tool": rec.tool_id,
                    "confidence": rec.confidence,
                    "risk_level": rec.risk_level
                }
                for rec in recommendations
            ]
        }
        
        self.selection_history.append(record)
        
        # 保持历史记录大小
        if len(self.selection_history) > 100:
            self.selection_history = self.selection_history[-50:]
    
    def get_selection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取选择历史"""
        return self.selection_history[-limit:] if self.selection_history else []
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        stats = {
            "total_tools": len(self.tool_capabilities),
            "by_category": {},
            "average_scores": {
                "efficiency": 0.0,
                "accuracy": 0.0,
                "stealth": 0.0
            }
        }
        
        # 按能力分类统计
        all_capabilities = set()
        for capability in self.tool_capabilities.values():
            all_capabilities.update(capability.capabilities)
        
        for capability in all_capabilities:
            tools_with_capability = [
                tool for tool in self.tool_capabilities.values() 
                if capability in tool.capabilities
            ]
            stats["by_category"][capability] = len(tools_with_capability)
        
        # 计算平均分
        if self.tool_capabilities:
            total_efficiency = sum(tool.efficiency_score for tool in self.tool_capabilities.values())
            total_accuracy = sum(tool.accuracy_score for tool in self.tool_capabilities.values())
            total_stealth = sum(tool.stealth_score for tool in self.tool_capabilities.values())
            
            stats["average_scores"]["efficiency"] = total_efficiency / len(self.tool_capabilities)
            stats["average_scores"]["accuracy"] = total_accuracy / len(self.tool_capabilities)
            stats["average_scores"]["stealth"] = total_stealth / len(self.tool_capabilities)
        
        return stats


def main():
    """测试函数"""
    import json
    
    # 创建智能工具选择器
    selector = IntelligentToolSelector()
    
    # 测试攻击步骤
    test_attack_step = {
        "type": "scanning",
        "description": "Web漏洞扫描",
        "required_capabilities": ["web_scan", "vulnerability_scan"]
    }
    
    # 测试上下文
    test_context = {
        "stealth_required": False,
        "performance_priority": True,
        "coverage_priority": True,
        "target_url": "http://example.com",
        "max_combinations": 2
    }
    
    print("=" * 80)
    print("智能工具选择器测试")
    print("=" * 80)
    
    print(f"\n工具统计:")
    stats = selector.get_tool_statistics()
    print(f"  工具总数: {stats['total_tools']}")
    print(f"  平均效率分: {stats['average_scores']['efficiency']:.2f}")
    print(f"  平均准确率分: {stats['average_scores']['accuracy']:.2f}")
    print(f"  平均隐蔽性分: {stats['average_scores']['stealth']:.2f}")
    
    print(f"\n按能力分类:")
    for category, count in sorted(stats["by_category"].items())[:5]:  # 显示前5个
        print(f"  {category}: {count}个工具")
    
    # 选择工具
    print(f"\n工具选择:")
    recommendations = selector.select_tools(test_attack_step, test_context)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.name} ({rec.tool_id})")
        print(f"   置信度: {rec.confidence:.2f}")
        print(f"   风险等级: {rec.risk_level}")
        print(f"   推荐理由: {rec.rationale}")
        print(f"   预期结果: {rec.expected_outcome}")
        
        print(f"   优化参数:")
        for key, value in rec.parameters.items():
            print(f"      {key}: {value}")
        
        if rec.alternatives:
            print(f"   备选工具:")
            for alt in rec.alternatives:
                print(f"      - {alt['name']} ({alt['reason']})")
    
    # 显示选择历史
    history = selector.get_selection_history()
    if history:
        print(f"\n最近的选择历史 ({len(history)}条):")
        for record in history[-2:]:  # 显示最后2条
            print(f"  - {record['attack_step']}")
            for rec in record["recommendations"]:
                print(f"    * {rec['tool']} (置信度: {rec['confidence']:.2f})")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()