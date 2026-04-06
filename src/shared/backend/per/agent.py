# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：整合Agent控制器
借鉴LuaN1aoAgent的P-E-R架构，整合规划器、执行器、反思器
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os

# 添加路径以便导入现有模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.per.planner import PERPlanner
from backend.per.executor import PERExecutor
from backend.per.reflector import PERReflector

logger = logging.getLogger(__name__)


class GraphManager:
    """简单的图谱管理器（简化版）
    
    负责管理任务图谱状态，支持基本的图操作
    """
    
    def __init__(self):
        """初始化图谱管理器"""
        self.graph = {}  # 简化：使用字典存储节点
        self.node_counter = 0
        
        # 节点状态定义
        self.VALID_STATUSES = {'pending', 'in_progress', 'completed', 'failed', 'deprecated'}
        
        logger.info("GraphManager初始化完成")
    
    def add_node(self, node_id: str, node_data: Dict[str, Any]) -> bool:
        """添加节点
        
        Args:
            node_id: 节点ID
            node_data: 节点数据
            
        Returns:
            bool: 是否添加成功
        """
        if node_id in self.graph:
            logger.warning(f"节点已存在: {node_id}")
            return False
        
        # 确保有状态字段
        if 'status' not in node_data:
            node_data['status'] = 'pending'
        
        # 验证状态
        if node_data['status'] not in self.VALID_STATUSES:
            logger.warning(f"无效状态: {node_data['status']}，修正为pending")
            node_data['status'] = 'pending'
        
        self.graph[node_id] = node_data
        self.node_counter += 1
        
        logger.debug(f"添加节点: {node_id}")
        return True
    
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> bool:
        """更新节点
        
        Args:
            node_id: 节点ID
            updates: 更新数据
            
        Returns:
            bool: 是否更新成功
        """
        if node_id not in self.graph:
            logger.warning(f"节点不存在: {node_id}")
            return False
        
        # 验证状态更新
        if 'status' in updates:
            new_status = updates['status']
            current_status = self.graph[node_id].get('status', 'pending')
            
            # 状态保护：已完成节点不能改为其他状态
            if current_status == 'completed' and new_status != 'completed':
                logger.warning(f"尝试修改已完成节点状态: {node_id} ({current_status} -> {new_status})")
                # 移除状态更新
                updates = {k: v for k, v in updates.items() if k != 'status'}
            
            # 验证新状态
            elif new_status not in self.VALID_STATUSES:
                logger.warning(f"无效状态: {new_status}，跳过状态更新")
                updates = {k: v for k, v in updates.items() if k != 'status'}
        
        # 应用更新
        self.graph[node_id].update(updates)
        
        logger.debug(f"更新节点: {node_id} - {list(updates.keys())}")
        return True
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[Dict[str, Any]]: 节点数据，不存在则返回None
        """
        return self.graph.get(node_id)
    
    def get_pending_nodes(self) -> List[str]:
        """获取待处理节点
        
        Returns:
            List[str]: 待处理节点ID列表
        """
        pending_nodes = []
        for node_id, node_data in self.graph.items():
            status = node_data.get('status', 'pending')
            if status in ['pending', 'ready']:
                pending_nodes.append(node_id)
        
        return pending_nodes
    
    def get_graph_state(self) -> Dict[str, Any]:
        """获取图谱状态
        
        Returns:
            Dict[str, Any]: 图谱状态
        """
        # 统计状态分布
        status_counts = {}
        for node_data in self.graph.values():
            status = node_data.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_nodes": len(self.graph),
            "status_distribution": status_counts,
            "nodes": self.graph
        }
    
    def clear(self) -> None:
        """清空图谱"""
        self.graph.clear()
        self.node_counter = 0
        logger.info("图谱已清空")


class PERAgent:
    """P-E-R架构：整合Agent
    
    整合规划器、执行器、反思器，实现完整的P-E-R工作流
    """
    
    def __init__(self, 
                 skill_registry=None,
                 llm_client=None,
                 max_iterations: int = 10):
        """初始化P-E-R Agent
        
        Args:
            skill_registry: 技能注册表（可选）
            llm_client: LLM客户端（可选）
            max_iterations: 最大迭代次数
        """
        # 核心组件
        self.planner = PERPlanner(llm_client=llm_client)
        self.executor = PERExecutor(skill_registry=skill_registry)
        self.reflector = PERReflector(llm_client=llm_client)
        self.graph_manager = GraphManager()
        
        # 配置参数
        self.max_iterations = max_iterations
        self.current_iteration = 0
        
        # 执行状态
        self.goal = ""
        self.target_info = {}
        self.is_running = False
        self.goal_achieved = False
        
        # 执行历史
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info("PERAgent初始化完成")
    
    def set_goal(self, goal: str, target_info: Dict[str, Any]) -> None:
        """设置目标
        
        Args:
            goal: 高级目标
            target_info: 目标信息
        """
        self.goal = goal
        self.target_info = target_info
        
        # 设置执行器上下文
        self.executor.set_context({
            "goal": goal,
            "target": target_info.get("target", "unknown"),
            "target_info": target_info
        })
        
        # 设置规划器环境上下文
        self.planner.set_environment_context({
            "goal": goal,
            "target_info": target_info
        })
        
        logger.info(f"设置目标: {goal}")
    
    async def run(self) -> Dict[str, Any]:
        """运行P-E-R工作流
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        if not self.goal:
            raise ValueError("未设置目标")
        
        self.is_running = True
        self.goal_achieved = False
        self.current_iteration = 0
        
        logger.info(f"开始执行P-E-R工作流: {self.goal}")
        
        try:
            # 阶段1: 初始规划
            logger.info("阶段1: 初始规划")
            initial_plan = self.planner.generate_initial_plan(self.goal, self.target_info)
            
            # 应用初始规划到图谱
            for operation in initial_plan:
                self._apply_graph_operation(operation)
            
            # P-E-R循环
            while (self.current_iteration < self.max_iterations and 
                   not self.goal_achieved and 
                   self.is_running):
                
                self.current_iteration += 1
                logger.info(f"P-E-R循环迭代 {self.current_iteration}/{self.max_iterations}")
                
                # 阶段2: 执行阶段
                execution_results = await self._execute_phase()
                
                # 阶段3: 反思阶段
                intelligence_summary = await self._reflect_phase(execution_results)
                
                # 阶段4: 重规划阶段
                await self._replan_phase(intelligence_summary)
                
                # 检查目标是否达成
                self.goal_achieved = self._check_goal_achievement(intelligence_summary)
            
            # 构建最终结果
            result = self._build_final_result()
            
            logger.info(f"P-E-R工作流完成: {'目标达成' if self.goal_achieved else '未达成目标'}")
            
            return result
            
        except Exception as e:
            logger.error(f"P-E-R工作流执行异常: {str(e)}")
            self.is_running = False
            
            return {
                "success": False,
                "error": str(e),
                "goal": self.goal,
                "iterations": self.current_iteration,
                "goal_achieved": False,
                "final_state": self.graph_manager.get_graph_state()
            }
    
    def _apply_graph_operation(self, operation: Dict[str, Any]) -> None:
        """应用图操作
        
        Args:
            operation: 图操作指令
        """
        command = operation.get("command")
        
        if command == "ADD_NODE":
            node_data = operation.get("node_data", {})
            node_id = node_data.get("id")
            if node_id:
                self.graph_manager.add_node(node_id, node_data)
        
        elif command == "UPDATE_NODE":
            node_id = operation.get("node_id")
            updates = operation.get("updates", {})
            if node_id:
                self.graph_manager.update_node(node_id, updates)
        
        elif command == "DEPRECATE_NODE":
            node_id = operation.get("node_id")
            if node_id:
                self.graph_manager.update_node(node_id, {"status": "deprecated"})
    
    async def _execute_phase(self) -> List[Dict[str, Any]]:
        """执行阶段
        
        Returns:
            List[Dict[str, Any]]: 执行结果列表
        """
        logger.info("执行阶段: 执行待处理任务")
        
        execution_results = []
        
        # 获取待处理节点
        pending_nodes = self.graph_manager.get_pending_nodes()
        
        if not pending_nodes:
            logger.info("没有待处理任务")
            return execution_results
        
        # 执行每个待处理任务
        for node_id in pending_nodes[:3]:  # 每次最多执行3个任务
            node_data = self.graph_manager.get_node(node_id)
            if not node_data:
                continue
            
            # 更新状态为执行中
            self.graph_manager.update_node(node_id, {"status": "in_progress"})
            
            # 执行任务
            logger.info(f"执行任务: {node_id}")
            execution_result = await self.executor.execute_subtask(
                node_id, 
                node_data,
                self.graph_manager
            )
            
            # 记录执行结果
            execution_results.append({
                "subtask_id": node_id,
                "execution_result": execution_result.to_dict(),
                "subtask_data": node_data
            })
            
            # 添加到执行历史
            self.execution_history.append({
                "iteration": self.current_iteration,
                "subtask_id": node_id,
                "timestamp": datetime.now().isoformat(),
                "result": execution_result.to_dict()
            })
        
        return execution_results
    
    async def _reflect_phase(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """反思阶段
        
        Args:
            execution_results: 执行结果列表
            
        Returns:
            Dict[str, Any]: 情报摘要
        """
        logger.info("反思阶段: 分析执行结果")
        
        reflections = []
        
        # 分析每个执行结果
        for exec_data in execution_results:
            subtask_id = exec_data["subtask_id"]
            execution_result = exec_data["execution_result"]
            subtask_data = exec_data["subtask_data"]
            
            # 分析执行结果
            reflection = self.reflector.analyze_execution_result(
                subtask_id,
                execution_result,
                subtask_data
            )
            
            reflections.append(reflection)
        
        # 生成情报摘要
        intelligence_summary = self.reflector.generate_intelligence_summary(reflections)
        
        logger.info(f"反思完成: 分析{len(reflections)}个任务，生成情报摘要")
        
        return intelligence_summary
    
    async def _replan_phase(self, intelligence_summary: Dict[str, Any]) -> None:
        """重规划阶段
        
        Args:
            intelligence_summary: 情报摘要
        """
        logger.info("重规划阶段: 基于反思结果调整计划")
        
        # 获取当前图谱状态
        current_state = self.graph_manager.get_graph_state()
        
        # 动态重规划
        replan_operations = self.planner.dynamic_replan(
            self.goal,
            current_state,
            intelligence_summary
        )
        
        # 应用重规划操作
        if replan_operations:
            logger.info(f"应用{len(replan_operations)}个重规划操作")
            for operation in replan_operations:
                self._apply_graph_operation(operation)
        else:
            logger.info("无需重规划")
    
    def _check_goal_achievement(self, intelligence_summary: Dict[str, Any]) -> bool:
        """检查目标达成情况
        
        Args:
            intelligence_summary: 情报摘要
            
        Returns:
            bool: 目标是否达成
        """
        audit_result = intelligence_summary.get("audit_result", {})
        status = audit_result.get("status", "")
        
        if status == "goal_achieved":
            logger.info("目标已达成")
            return True
        
        # 检查图谱中是否有已完成的关键任务
        graph_state = self.graph_manager.get_graph_state()
        completed_count = graph_state["status_distribution"].get("completed", 0)
        total_count = graph_state["total_nodes"]
        
        # 简单启发式：如果大部分任务已完成，则认为目标达成
        if total_count > 0 and completed_count / total_count > 0.8:
            logger.info(f"大部分任务已完成 ({completed_count}/{total_count})，认为目标达成")
            return True
        
        return False
    
    def _build_final_result(self) -> Dict[str, Any]:
        """构建最终结果
        
        Returns:
            Dict[str, Any]: 最终结果
        """
        # 获取组件摘要
        planning_summary = self.planner.get_planning_summary()
        execution_summary = self.executor.get_execution_summary()
        reflection_summary = self.reflector.get_reflection_summary()
        graph_state = self.graph_manager.get_graph_state()
        
        # 计算总体指标
        total_tasks = execution_summary.get("total_tasks", 0)
        successful_tasks = execution_summary.get("successful_tasks", 0)
        success_rate = execution_summary.get("success_rate", 0)
        
        return {
            "success": self.goal_achieved,
            "goal": self.goal,
            "target_info": self.target_info,
            "iterations": self.current_iteration,
            "goal_achieved": self.goal_achieved,
            "metrics": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "success_rate": success_rate,
                "total_iterations": self.current_iteration,
                "planning_attempts": planning_summary.get("total_attempts", 0),
                "reflection_count": reflection_summary.get("total_reflections", 0)
            },
            "planning_summary": planning_summary,
            "execution_summary": execution_summary,
            "reflection_summary": reflection_summary,
            "graph_state": graph_state,
            "execution_history": self.execution_history[-10:],  # 最近10条记录
            "timestamp": datetime.now().isoformat()
        }
    
    def stop(self) -> None:
        """停止执行"""
        self.is_running = False
        logger.info("P-E-R Agent已停止")
    
    def reset(self) -> None:
        """重置Agent状态"""
        self.planner.clear_history()
        self.executor.clear_history()
        self.reflector.clear_history()
        self.graph_manager.clear()
        
        self.execution_history.clear()
        self.current_iteration = 0
        self.goal_achieved = False
        self.is_running = False
        
        logger.info("P-E-R Agent已重置")


async def test_per_agent():
    """测试P-E-R Agent功能"""
    import sys
    
    print("=" * 80)
    print("P-E-R Agent整合测试")
    print("=" * 80)
    
    # 创建P-E-R Agent实例
    agent = PERAgent(max_iterations=3)
    
    # 设置目标
    target_info = {
        "target": "test.example.com",
        "type": "web_application",
        "description": "测试Web应用"
    }
    
    agent.set_goal("对test.example.com进行渗透测试", target_info)
    
    # 运行Agent
    print("\n运行P-E-R Agent...")
    result = await agent.run()
    
    # 显示结果
    print(f"\n执行结果:")
    print(f"  成功: {result['success']}")
    print(f"  目标达成: {result['goal_achieved']}")
    print(f"  迭代次数: {result['iterations']}")
    
    print(f"\n指标:")
    metrics = result['metrics']
    print(f"  总任务数: {metrics['total_tasks']}")
    print(f"  成功任务数: {metrics['successful_tasks']}")
    print(f"  成功率: {metrics['success_rate']*100:.1f}%")
    
    print(f"\n规划摘要:")
    planning = result['planning_summary']
    print(f"  规划尝试次数: {planning['total_attempts']}")
    
    print(f"\n执行摘要:")
    execution = result['execution_summary']
    print(f"  总执行时间: {execution['total_execution_time']:.2f}秒")
    print(f"  总工具调用数: {execution['total_tool_calls']}")
    
    print(f"\n反思摘要:")
    reflection = result['reflection_summary']
    print(f"  总反思次数: {reflection['total_reflections']}")
    print(f"  失败模式数: {reflection['failure_patterns_count']}")
    print(f"  成功模式数: {reflection['success_patterns_count']}")
    
    print(f"\n图谱状态:")
    graph_state = result['graph_state']
    print(f"  总节点数: {graph_state['total_nodes']}")
    print(f"  状态分布: {graph_state['status_distribution']}")
    
    print(f"\n执行历史 (最近{len(result['execution_history'])}条):")
    for i, history in enumerate(result['execution_history']):
        result_data = history['result']
        # 安全地获取状态
        status = result_data.get('status', 'unknown')
        success = result_data.get('success', False)
        print(f"  {i+1}. {history['subtask_id']}: {status} (成功: {success})")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    
    # 验证关键功能
    success = True
    issues = []
    
    # 验证规划器
    if planning['total_attempts'] == 0:
        success = False
        issues.append("规划器未生成任何规划")
    
    # 验证执行器
    if execution['total_tool_calls'] == 0:
        success = False
        issues.append("执行器未调用任何工具")
    
    # 验证反思器
    if reflection['total_reflections'] == 0:
        success = False
        issues.append("反思器未进行任何反思")
    
    # 验证图谱
    if graph_state['total_nodes'] == 0:
        success = False
        issues.append("图谱管理器未创建任何节点")
    
    # 输出验证结果
    if success:
        print("✅ 所有核心组件功能正常!")
    else:
        print("❌ 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
    
    return success

