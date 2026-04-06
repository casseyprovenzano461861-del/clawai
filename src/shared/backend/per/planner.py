# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：规划器模块
借鉴LuaN1aoAgent的规划器设计，负责将高级目标分解为可执行的子任务图
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PlanningAttempt:
    """规划尝试记录"""
    timestamp: str
    strategy: str
    goal: str
    outcome_summary: str
    graph_operations: List[Dict[str, Any]]
    llm_prompt: Optional[str] = None
    llm_response: Optional[str] = None


class PERPlanner:
    """P-E-R架构：规划器
    
    负责：
    1. 将高级目标分解为可执行的子任务图
    2. 基于执行反馈进行动态重规划
    3. 生成图操作指令（ADD_NODE, UPDATE_NODE, DEPRECATE_NODE）
    4. 整合历史规划和反思信息
    """
    
    def __init__(self, llm_client=None, output_mode: str = "default"):
        """初始化规划器
        
        Args:
            llm_client: LLM客户端实例（可选）
            output_mode: 输出模式（default/simple/debug）
        """
        self.llm_client = llm_client
        self.output_mode = output_mode
        
        # 规划历史
        self.planning_history: List[PlanningAttempt] = []
        self.rejected_strategies: List[Dict[str, Any]] = []
        self.long_term_objectives: List[str] = []
        
        # 环境上下文
        self.environment_context: Dict[str, Any] = {}
        
        # 压缩历史
        self.compressed_history_summary: Optional[str] = None
        self.compression_count: int = 0
        
        # 需要压缩标志
        self._needs_compression: bool = False
        
        logger.info("PERPlanner初始化完成")
    
    def set_environment_context(self, context: Dict[str, Any]) -> None:
        """设置环境上下文
        
        Args:
            context: 环境上下文信息
        """
        self.environment_context = context
        logger.debug(f"设置环境上下文: {len(context)}个键")
    
    def add_long_term_objective(self, objective: str) -> None:
        """添加长期目标
        
        Args:
            objective: 长期目标描述
        """
        self.long_term_objectives.append(objective)
        logger.debug(f"添加长期目标: {objective}")
    
    def record_planning_attempt(self, 
                               strategy: str, 
                               goal: str, 
                               outcome_summary: str,
                               graph_operations: List[Dict[str, Any]],
                               llm_prompt: Optional[str] = None,
                               llm_response: Optional[str] = None) -> None:
        """记录规划尝试
        
        Args:
            strategy: 规划策略
            goal: 规划目标
            outcome_summary: 结果摘要
            graph_operations: 图操作指令
            llm_prompt: LLM提示词（可选）
            llm_response: LLM响应（可选）
        """
        attempt = PlanningAttempt(
            timestamp=datetime.now().isoformat(),
            strategy=strategy,
            goal=goal,
            outcome_summary=outcome_summary,
            graph_operations=graph_operations,
            llm_prompt=llm_prompt,
            llm_response=llm_response
        )
        
        self.planning_history.append(attempt)
        
        # 检查是否需要压缩
        if len(self.planning_history) > 20:  # 历史窗口大小
            self._needs_compression = True
        
        logger.debug(f"记录规划尝试: {strategy} -> {outcome_summary}")
    
    def record_rejected_strategy(self, 
                                strategy: str, 
                                reason: str,
                                context: Dict[str, Any]) -> None:
        """记录被拒绝的策略
        
        Args:
            strategy: 被拒绝的策略
            reason: 拒绝原因
            context: 上下文信息
        """
        rejected = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "reason": reason,
            "context": context
        }
        
        self.rejected_strategies.append(rejected)
        logger.debug(f"记录被拒绝策略: {strategy} - {reason}")
    
    def generate_initial_plan(self, 
                             goal: str, 
                             target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成初始规划
        
        Args:
            goal: 高级目标
            target_info: 目标信息
            
        Returns:
            List[Dict[str, Any]]: 图操作指令列表
        """
        logger.info(f"生成初始规划: {goal}")
        
        # 基于目标类型生成基础任务图
        if "渗透测试" in goal or "安全测试" in goal:
            return self._generate_pentest_plan(goal, target_info)
        elif "漏洞扫描" in goal or "扫描" in goal:
            return self._generate_scan_plan(goal, target_info)
        elif "信息收集" in goal or "侦察" in goal:
            return self._generate_recon_plan(goal, target_info)
        else:
            return self._generate_general_plan(goal, target_info)
    
    def _generate_pentest_plan(self, goal: str, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成渗透测试规划
        
        Args:
            goal: 目标
            target_info: 目标信息
            
        Returns:
            List[Dict[str, Any]]: 图操作指令
        """
        target = target_info.get("target", "unknown")
        
        operations = [
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"recon_{target}",
                    "description": f"信息收集: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 1,
                    "mission_briefing": f"对目标 {target} 进行全面的信息收集，包括端口扫描、服务识别、技术栈分析等",
                    "completion_criteria": "完成端口扫描和服务识别，生成详细的目标画像"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"vuln_scan_{target}",
                    "description": f"漏洞扫描: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 2,
                    "dependencies": [f"recon_{target}"],
                    "mission_briefing": f"基于信息收集结果，对目标 {target} 进行漏洞扫描",
                    "completion_criteria": "完成漏洞扫描，识别潜在的安全漏洞"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"exploit_planning_{target}",
                    "description": f"漏洞利用规划: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 3,
                    "dependencies": [f"vuln_scan_{target}"],
                    "mission_briefing": f"基于漏洞扫描结果，制定漏洞利用策略",
                    "completion_criteria": "生成详细的漏洞利用计划"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"post_exploit_{target}",
                    "description": f"后渗透活动: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 4,
                    "dependencies": [f"exploit_planning_{target}"],
                    "mission_briefing": f"在成功利用漏洞后，进行权限维持、横向移动等后渗透活动",
                    "completion_criteria": "完成后渗透活动，达成攻击目标"
                }
            }
        ]
        
        # 记录规划尝试
        self.record_planning_attempt(
            strategy="渗透测试标准流程",
            goal=goal,
            outcome_summary="生成4阶段渗透测试计划",
            graph_operations=operations
        )
        
        return operations
    
    def _generate_scan_plan(self, goal: str, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成漏洞扫描规划
        
        Args:
            goal: 目标
            target_info: 目标信息
            
        Returns:
            List[Dict[str, Any]]: 图操作指令
        """
        target = target_info.get("target", "unknown")
        
        operations = [
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"port_scan_{target}",
                    "description": f"端口扫描: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 1,
                    "mission_briefing": f"对目标 {target} 进行全面的端口扫描",
                    "completion_criteria": "识别所有开放端口和服务"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"service_scan_{target}",
                    "description": f"服务扫描: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 2,
                    "dependencies": [f"port_scan_{target}"],
                    "mission_briefing": f"基于端口扫描结果，对识别到的服务进行详细扫描",
                    "completion_criteria": "完成服务版本识别和配置分析"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"vuln_detection_{target}",
                    "description": f"漏洞检测: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 3,
                    "dependencies": [f"service_scan_{target}"],
                    "mission_briefing": f"基于服务扫描结果，进行漏洞检测",
                    "completion_criteria": "识别所有已知漏洞"
                }
            }
        ]
        
        # 记录规划尝试
        self.record_planning_attempt(
            strategy="漏洞扫描标准流程",
            goal=goal,
            outcome_summary="生成3阶段漏洞扫描计划",
            graph_operations=operations
        )
        
        return operations
    
    def _generate_recon_plan(self, goal: str, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成信息收集规划
        
        Args:
            goal: 目标
            target_info: 目标信息
            
        Returns:
            List[Dict[str, Any]]: 图操作指令
        """
        target = target_info.get("target", "unknown")
        
        operations = [
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"passive_recon_{target}",
                    "description": f"被动信息收集: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 1,
                    "mission_briefing": f"对目标 {target} 进行被动信息收集，不直接与目标交互",
                    "completion_criteria": "收集DNS记录、子域名、历史数据等"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"active_recon_{target}",
                    "description": f"主动信息收集: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 2,
                    "dependencies": [f"passive_recon_{target}"],
                    "mission_briefing": f"基于被动收集结果，进行主动信息收集",
                    "completion_criteria": "完成端口扫描、服务识别等技术栈分析"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"analysis_{target}",
                    "description": f"信息分析: {target}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 3,
                    "dependencies": [f"active_recon_{target}"],
                    "mission_briefing": f"分析收集到的信息，生成目标画像",
                    "completion_criteria": "生成详细的目标分析报告"
                }
            }
        ]
        
        # 记录规划尝试
        self.record_planning_attempt(
            strategy="信息收集标准流程",
            goal=goal,
            outcome_summary="生成3阶段信息收集计划",
            graph_operations=operations
        )
        
        return operations
    
    def _generate_general_plan(self, goal: str, target_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成通用规划
        
        Args:
            goal: 目标
            target_info: 目标信息
            
        Returns:
            List[Dict[str, Any]]: 图操作指令
        """
        target = target_info.get("target", "unknown")
        
        operations = [
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"task_analysis_{target}",
                    "description": f"任务分析: {goal}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 1,
                    "mission_briefing": f"分析任务目标: {goal}",
                    "completion_criteria": "理解任务需求，制定执行策略"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"execution_{target}",
                    "description": f"任务执行: {goal}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 2,
                    "dependencies": [f"task_analysis_{target}"],
                    "mission_briefing": f"执行任务: {goal}",
                    "completion_criteria": "完成主要任务目标"
                }
            },
            {
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"verification_{target}",
                    "description": f"结果验证: {goal}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": 3,
                    "dependencies": [f"execution_{target}"],
                    "mission_briefing": f"验证任务执行结果",
                    "completion_criteria": "确认任务目标达成"
                }
            }
        ]
        
        # 记录规划尝试
        self.record_planning_attempt(
            strategy="通用任务流程",
            goal=goal,
            outcome_summary="生成3阶段通用任务计划",
            graph_operations=operations
        )
        
        return operations
    
    def dynamic_replan(self, 
                      goal: str,
                      current_graph_state: Dict[str, Any],
                      intelligence_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """动态重规划
        
        Args:
            goal: 当前目标
            current_graph_state: 当前图谱状态
            intelligence_summary: 情报摘要（来自反思器）
            
        Returns:
            List[Dict[str, Any]]: 图操作指令
        """
        logger.info("执行动态重规划")
        
        # 分析当前状态
        completed_nodes = []
        failed_nodes = []
        pending_nodes = []
        
        for node_id, node_data in current_graph_state.get("nodes", {}).items():
            status = node_data.get("status", "unknown")
            if status == "completed":
                completed_nodes.append(node_id)
            elif status == "failed":
                failed_nodes.append(node_id)
            elif status in ["pending", "in_progress"]:
                pending_nodes.append(node_id)
        
        # 生成重规划操作
        operations = []
        
        # 1. 处理失败节点
        for failed_node in failed_nodes:
            operations.append({
                "command": "DEPRECATE_NODE",
                "node_id": failed_node,
                "reason": "任务执行失败，需要重新规划"
            })
            
            # 为失败节点创建替代任务
            operations.append({
                "command": "ADD_NODE",
                "node_data": {
                    "id": f"{failed_node}_alternative",
                    "description": f"替代任务: {failed_node}",
                    "type": "subtask",
                    "status": "pending",
                    "priority": current_graph_state["nodes"][failed_node].get("priority", 1),
                    "mission_briefing": f"替代失败任务 {failed_node}，尝试不同方法",
                    "completion_criteria": "完成原失败任务的目标"
                }
            })
        
        # 2. 基于情报摘要调整计划
        findings = intelligence_summary.get("findings", [])
        if findings:
            # 根据新发现添加任务
            for i, finding in enumerate(findings[:3]):  # 最多添加3个新任务
                operations.append({
                    "command": "ADD_NODE",
                    "node_data": {
                        "id": f"followup_{i}",
                        "description": f"跟进发现: {finding[:50]}...",
                        "type": "subtask",
                        "status": "pending",
                        "priority": 2,
                        "mission_briefing": f"跟进情报发现: {finding}",
                        "completion_criteria": "验证和处理发现的信息"
                    }
                })
        
        # 3. 检查目标达成情况
        audit_result = intelligence_summary.get("audit_result", {})
        if audit_result.get("status") == "goal_achieved":
            logger.info("目标已达成，无需进一步规划")
            return []
        
        # 记录规划尝试
        self.record_planning_attempt(
            strategy="动态重规划",
            goal=goal,
            outcome_summary=f"处理{len(failed_nodes)}个失败节点，添加{len(findings[:3])}个跟进任务",
            graph_operations=operations
        )
        
        return operations
    
    def get_planning_summary(self) -> Dict[str, Any]:
        """获取规划摘要
        
        Returns:
            Dict[str, Any]: 规划摘要信息
        """
        return {
            "total_attempts": len(self.planning_history),
            "recent_strategies": [attempt.strategy for attempt in self.planning_history[-5:]],
            "rejected_strategies_count": len(self.rejected_strategies),
            "long_term_objectives": self.long_term_objectives,
            "compression_count": self.compression_count,
            "needs_compression": self._needs_compression,
            "environment_context_keys": list(self.environment_context.keys())
        }
    
    def needs_compression(self) -> bool:
        """检查是否需要压缩
        
        Returns:
            bool: 是否需要压缩
        """
        return self._needs_compression
    
    def mark_compressed(self) -> None:
        """标记为已压缩"""
        self._needs_compression = False
    
    def clear_history(self) -> None:
        """清空规划历史"""
        self.planning_history.clear()
        self.rejected_strategies.clear()
        self.compressed_history_summary = None
        self.compression_count = 0
        self._needs_compression = False
        logger.info("规划历史已清空")


def test_planner():
    """测试规划器功能"""
    import sys
    
    print("=" * 80)
    print("PER规划器测试")
    print("=" * 80)
    
    # 创建规划器实例
    planner = PERPlanner()
    
    # 测试1: 渗透测试规划
    print("\n测试1: 渗透测试规划")
    target_info = {"target": "example.com"}
    operations = planner.generate_initial_plan("对example.com进行渗透测试", target_info)
    
    print(f"生成 {len(operations)} 个图操作:")
    for i, op in enumerate(operations):
        cmd = op.get("command", "UNKNOWN")
        node_id = op.get("node_data", {}).get("id", "unknown")
        print(f"  {i+1}. [{cmd}] {node_id}")
    
    # 测试2: 动态重规划
    print("\n测试2: 动态重规划")
    current_state = {
        "nodes": {
            "recon_example.com": {"status": "completed"},
            "vuln_scan_example.com": {"status": "failed", "priority": 2},
            "exploit_planning_example.com": {"status": "pending", "priority": 3}
        }
    }
    
    intelligence = {
        "findings": ["发现SQL注入漏洞", "发现XSS漏洞"],
        "audit_result": {"status": "in_progress"}
    }
    
    replan_ops = planner.dynamic_replan(
        "对example.com进行渗透测试",
        current_state,
        intelligence
    )
    
    print(f"动态重规划生成 {len(replan_ops)} 个操作")
    
    # 测试3: 获取规划摘要
    print("\n测试3: 规划摘要")
    summary = planner.get_planning_summary()
    print(f"总尝试次数: {summary['total_attempts']}")
    print(f"最近策略: {summary['recent_strategies']}")
    print(f"被拒策略数: {summary['rejected_strategies_count']}")
    
    print("\n" + "=" * 80)
    print("[PASS] 规划器测试完成")
    
    return True


if __name__ == "__main__":
    success = test_planner()
    sys.exit(0 if success else 1)
