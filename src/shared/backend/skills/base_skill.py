# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
BaseSkill抽象类 - 技能体系的基础类（第二阶段升级版）

要求：
1. 定义所有Skill的通用接口
2. 提供can_handle和execute方法
3. 支持技能注册和发现机制
4. 支持策略推理和行为解释能力
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """技能抽象基类（支持策略推理和行为解释）"""
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.category = self.get_category()
        self.difficulty = self.get_difficulty()
        self.required_tools = self.get_required_tools()
        self.prerequisites = self.get_prerequisites()
        self.success_rate = self.get_success_rate()
        self.estimated_time = self.get_estimated_time()
        self.confidence = 0.8  # 默认置信度
        self.thinking_log = []  # 思考日志
        self.execution_history = []  # 执行历史
        
    @abstractmethod
    def get_name(self) -> str:
        """获取技能名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取技能描述"""
        pass
    
    @abstractmethod
    def get_category(self) -> str:
        """获取技能类别"""
        pass
    
    @abstractmethod
    def get_difficulty(self) -> str:
        """获取技能难度"""
        pass
    
    @abstractmethod
    def get_required_tools(self) -> List[str]:
        """获取所需工具列表"""
        pass
    
    @abstractmethod
    def get_prerequisites(self) -> List[str]:
        """获取前置技能列表"""
        pass
    
    @abstractmethod
    def get_success_rate(self) -> float:
        """获取技能成功率"""
        pass
    
    @abstractmethod
    def get_estimated_time(self) -> str:
        """获取预估执行时间"""
        pass
    
    @abstractmethod
    def can_handle(self, context: Dict[str, Any]) -> bool:
        """
        判断技能是否能处理当前上下文
        
        Args:
            context: 包含目标信息、扫描结果、当前状态等的上下文
            
        Returns:
            bool: 是否能处理
        """
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    def get_reason(self, context: Dict[str, Any]) -> str:
        """
        获取选择该技能的理由（策略推理）
        
        Args:
            context: 执行上下文
            
        Returns:
            str: 选择理由
        """
        # 默认实现，子类可以覆盖
        reasons = []
        
        # 基于技能类别
        if self.category == "reconnaissance":
            reasons.append("信息收集是攻击的基础步骤")
        elif self.category == "vulnerability_scanning":
            reasons.append("漏洞检测是发现攻击入口的关键")
        elif self.category == "exploitation":
            reasons.append("漏洞利用是实现攻击目标的核心")
        elif self.category == "post_exploitation":
            reasons.append("后渗透是巩固攻击成果的重要环节")
        
        # 基于上下文信息
        target = context.get("target", "")
        if target:
            reasons.append(f"目标: {target}")
        
        scan_results = context.get("scan_results", {})
        if scan_results:
            reasons.append("已有扫描结果，可进行针对性攻击")
        
        # 基于技能成功率
        reasons.append(f"成功率: {self.success_rate*100:.1f}%")
        
        return "；".join(reasons)
    
    def add_thinking_log(self, message: str, confidence: float = 0.8) -> None:
        """
        添加思考日志条目
        
        Args:
            message: 思考内容
            confidence: 置信度 (0.0-1.0)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "confidence": confidence,
            "skill": self.name
        }
        self.thinking_log.append(log_entry)
        logger.debug(f"[思考日志] {self.name}: {message} (置信度: {confidence:.2f})")
    
    def get_thinking_log(self) -> List[Dict[str, Any]]:
        """获取思考日志"""
        return self.thinking_log.copy()
    
    def clear_thinking_log(self) -> None:
        """清空思考日志"""
        self.thinking_log.clear()
    
    def update_confidence(self, success: bool, context: Dict[str, Any]) -> None:
        """
        更新技能置信度
        
        Args:
            success: 执行是否成功
            context: 执行上下文
        """
        if success:
            # 成功执行，提高置信度
            self.confidence = min(self.confidence + 0.05, 0.95)
            self.add_thinking_log(f"技能执行成功，置信度提升至 {self.confidence:.2f}", self.confidence)
        else:
            # 执行失败，降低置信度
            self.confidence = max(self.confidence - 0.1, 0.3)
            self.add_thinking_log(f"技能执行失败，置信度降低至 {self.confidence:.2f}", self.confidence)
    
    def get_skill_info(self) -> Dict[str, Any]:
        """获取技能信息（包含推理信息）"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "difficulty": self.difficulty,
            "required_tools": self.required_tools,
            "prerequisites": self.prerequisites,
            "success_rate": self.success_rate,
            "estimated_time": self.estimated_time,
            "confidence": self.confidence,
            "thinking_log_count": len(self.thinking_log)
        }
    
    def validate_context(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证上下文是否有效
        
        Args:
            context: 执行上下文
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not context:
            return False, "上下文为空"
        
        if "target" not in context:
            return False, "缺少目标信息"
        
        return True, ""
    
    def log_execution_start(self, context: Dict[str, Any]) -> None:
        """记录执行开始"""
        target = context.get("target", "unknown")
        self.add_thinking_log(f"开始执行技能，目标: {target}", self.confidence)
        logger.info(f"开始执行技能: {self.name} | 目标: {target} | 置信度: {self.confidence:.2f}")
    
    def log_execution_end(self, result: Dict[str, Any]) -> None:
        """记录执行结束"""
        success = result.get("success", False)
        status = "成功" if success else "失败"
        
        # 记录执行历史
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "skill": self.name,
            "success": success,
            "result": result,
            "confidence": self.confidence
        }
        self.execution_history.append(execution_record)
        
        # 更新置信度
        self.update_confidence(success, result.get("context", {}))
        
        self.add_thinking_log(f"技能执行完成，状态: {status}，当前置信度: {self.confidence:.2f}", self.confidence)
        logger.info(f"技能执行完成: {self.name} | 状态: {status} | 置信度: {self.confidence:.2f}")
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history.copy()
    
    def get_success_rate_based_on_history(self) -> float:
        """基于历史记录计算实际成功率"""
        if not self.execution_history:
            return self.success_rate
        
        successful_executions = sum(1 for record in self.execution_history if record.get("success", False))
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return self.success_rate
        
        actual_success_rate = successful_executions / total_executions
        # 结合默认成功率和实际成功率
        return (self.success_rate * 0.3 + actual_success_rate * 0.7)


class SkillContext:
    """技能执行上下文"""
    
    def __init__(self, target: str, scan_results: Dict[str, Any], 
                 current_state: Dict[str, Any] = None):
        """
        初始化技能上下文
        
        Args:
            target: 目标地址
            scan_results: 扫描结果
            current_state: 当前状态（已执行技能、获取的信息等）
        """
        self.target = target
        self.scan_results = scan_results or {}
        self.current_state = current_state or {}
        self.execution_history = []
        
    def add_execution_result(self, skill_name: str, result: Dict[str, Any]) -> None:
        """添加执行结果到历史"""
        self.execution_history.append({
            "skill": skill_name,
            "result": result,
            "timestamp": self._get_timestamp()
        })
        
        # 更新当前状态
        if result.get("success", False):
            self._update_state_from_result(skill_name, result)
    
    def _update_state_from_result(self, skill_name: str, result: Dict[str, Any]) -> None:
        """根据执行结果更新状态"""
        # 根据技能类型更新状态
        if skill_name == "NmapScanSkill":
            if "open_ports" in result:
                self.current_state["open_ports"] = result["open_ports"]
            if "services" in result:
                self.current_state["services"] = result["services"]
                
        elif skill_name == "WhatWebSkill":
            if "web_technologies" in result:
                self.current_state["web_technologies"] = result["web_technologies"]
                
        elif skill_name == "SQLInjectionSkill":
            if "sql_injections" in result:
                self.current_state["sql_injections"] = result["sql_injections"]
                
        elif skill_name == "RCESkill":
            if "rce_vulnerabilities" in result:
                self.current_state["rce_vulnerabilities"] = result["rce_vulnerabilities"]
                
        elif skill_name == "PrivilegeEscalationSkill":
            if "privilege_escalation" in result:
                self.current_state["privilege_escalation"] = result["privilege_escalation"]
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target": self.target,
            "scan_results": self.scan_results,
            "current_state": self.current_state,
            "execution_history": self.execution_history
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文值"""
        if key == "target":
            return self.target
        elif key == "scan_results":
            return self.scan_results
        elif key == "current_state":
            return self.current_state
        elif key == "execution_history":
            return self.execution_history
        else:
            # 尝试从current_state中获取
            return self.current_state.get(key, default)
    
    def get_available_targets(self) -> List[str]:
        """获取可用目标列表"""
        targets = [self.target]
        
        # 从当前状态中提取其他目标
        if "open_ports" in self.current_state:
            for port_info in self.current_state["open_ports"]:
                if isinstance(port_info, dict) and "service" in port_info:
                    service_target = f"{self.target}:{port_info.get('port', '')}"
                    targets.append(service_target)
        
        return targets
    
    def get_discovered_vulnerabilities(self) -> List[Dict[str, Any]]:
        """获取已发现的漏洞"""
        vulnerabilities = []
        
        # 从扫描结果中提取
        if "nuclei" in self.scan_results:
            nuclei_data = self.scan_results["nuclei"]
            if isinstance(nuclei_data, dict) and "vulnerabilities" in nuclei_data:
                vulnerabilities.extend(nuclei_data["vulnerabilities"])
        
        # 从当前状态中提取
        if "sql_injections" in self.current_state:
            for sql_injection in self.current_state["sql_injections"]:
                vulnerabilities.append({
                    "name": f"SQL注入: {sql_injection.get('parameter', '未知参数')}",
                    "severity": "high",
                    "type": "sql_injection",
                    "details": sql_injection
                })
        
        if "rce_vulnerabilities" in self.current_state:
            for rce_vuln in self.current_state["rce_vulnerabilities"]:
                vulnerabilities.append({
                    "name": f"远程代码执行: {rce_vuln.get('vulnerability', '未知漏洞')}",
                    "severity": "critical",
                    "type": "rce",
                    "details": rce_vuln
                })
        
        return vulnerabilities