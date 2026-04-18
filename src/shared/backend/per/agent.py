# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：智能体主模块
借鉴LuaN1aoAgent的设计，实现规划-执行-反思循环
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import sys
import os

# 添加路径以便导入现有模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)

# 导入PER组件
try:
    from .planner import PERPlanner
    from .executor import PERExecutor
    from .reflector import PERReflector
    from .llm_integration import create_llm_integration, LLMIntegration
except ImportError:
    # 直接运行时的导入
    from planner import PERPlanner
    from executor import PERExecutor
    from reflector import PERReflector
    from llm_integration import create_llm_integration, LLMIntegration


class PERAgent:
    """P-E-R架构：智能体
    
    实现规划(Planning)-执行(Execution)-反思(Reflection)循环
    
    核心特性：
    1. 智能规划：使用LLM生成和优化任务规划
    2. 执行管理：支持真实和模拟执行，集成现有Skill系统
    3. 深度反思：使用LLM分析执行结果，提取洞察
    4. 动态重规划：基于反思结果调整计划
    5. 历史压缩：支持长会话的上下文管理
    6. 工具集成：兼容现有Skill系统
    """
    
    def __init__(self, 
                 llm_client=None,
                 skill_registry=None,
                 output_mode: str = "default",
                 use_llm: bool = True):
        """初始化P-E-R智能体
        
        Args:
            llm_client: LLM客户端实例（可选）
            skill_registry: 技能注册表（可选）
            output_mode: 输出模式（default/simple/debug）
            use_llm: 是否使用LLM（默认True）
        """
        self.output_mode = output_mode
        self.use_llm = use_llm and llm_client is not None
        
        # 初始化LLM集成
        self.llm_integration: Optional[LLMIntegration] = None
        if self.use_llm:
            try:
                self.llm_integration = create_llm_integration(llm_client=llm_client)
                logger.info("PER Agent LLM集成初始化成功")
            except Exception as e:
                logger.warning(f"LLM集成初始化失败: {e}，将使用回退模式")
                self.use_llm = False
        
        # 初始化PER组件
        self.planner = PERPlanner(
            llm_client=llm_client,
            output_mode=output_mode,
            use_llm=self.use_llm
        )
        
        self.executor = PERExecutor(
            skill_registry=skill_registry,
            llm_client=llm_client,
            max_retries=1,
            use_llm=self.use_llm
        )
        
        self.reflector = PERReflector(
            llm_client=llm_client,
            use_llm=self.use_llm
        )
        
        # 图谱管理器（可选）
        self.graph_manager = None
        
        # 会话状态
        self.session_id: Optional[str] = None
        self.current_goal: Optional[str] = None
        self.target_info: Optional[Dict[str, Any]] = None
        self.execution_context: Dict[str, Any] = {}
        
        # 会话历史
        self.session_history: List[Dict[str, Any]] = []
        
        # 迭代计数
        self.iteration_count: int = 0
        self.max_iterations: int = 20
        
        # 会话统计
        self.session_stats = {
            "total_iterations": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_planning": 0,
            "total_reflections": 0,
            "llm_calls": 0
        }
        
        logger.info(f"PER Agent初始化完成 (use_llm={self.use_llm})")
    
    def set_graph_manager(self, graph_manager) -> None:
        """设置图谱管理器
        
        Args:
            graph_manager: 图谱管理器实例
        """
        self.graph_manager = graph_manager
        logger.debug("图谱管理器已设置")
    
    def set_skill_registry(self, skill_registry) -> None:
        """设置技能注册表
        
        Args:
            skill_registry: 技能注册表实例
        """
        self.executor.set_skill_registry(skill_registry)
        logger.debug("技能注册表已设置")
    
    async def run(self, 
                 goal: str, 
                 target_info: Dict[str, Any],
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """运行P-E-R循环
        
        Args:
            goal: 目标描述
            target_info: 目标信息
            context: 执行上下文（可选）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self.current_goal = goal
        self.target_info = target_info
        self.execution_context = context or {}
        
        logger.info(f"开始P-E-R循环: {goal}")
        
        # 初始化会话
        self.session_id = f"per_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 设置执行器上下文
        self.executor.set_context(self.execution_context)
        
        # 阶段1: 初始规划
        logger.info("阶段1: 初始规划")
        initial_operations = await self.planner.generate_initial_plan(goal, target_info)
        
        if not initial_operations:
            logger.warning("初始规划失败，无法生成任务图")
            return {
                "success": False,
                "error": "初始规划失败",
                "session_id": self.session_id,
                "goal": goal
            }
        
        # 应用初始规划到图谱
        if self.graph_manager:
            for operation in initial_operations:
                self._apply_graph_operation(operation)
        
        # 记录规划
        self.session_stats["total_planning"] += 1
        
        # 阶段2-4: 执行-反思-重规划循环
        iteration = 0
        all_reflections = []
        
        while iteration < self.max_iterations:
            self.iteration_count = iteration
            iteration += 1
            self.session_stats["total_iterations"] += 1
            
            logger.info(f"P-E-R迭代 {iteration}/{self.max_iterations}")
            
            # 阶段2: 执行
            logger.info("阶段2: 执行")
            execution_results = await self._execute_pending_tasks()
            
            if not execution_results:
                logger.info("没有待执行的任务，检查是否完成目标")
                if self._check_goal_completion():
                    logger.info("目标已达成，结束P-E-R循环")
                    break
                else:
                    logger.warning("没有待执行任务但目标未达成，可能需要重新规划")
                    # 尝试动态重规划
                    replan_operations = await self.planner.dynamic_replan(
                        goal,
                        self._get_current_graph_state(),
                        await self.reflector.generate_intelligence_summary(all_reflections)
                    )
                    
                    if replan_operations:
                        for operation in replan_operations:
                            self._apply_graph_operation(operation)
                        continue
                    else:
                        break
            
            # 更新统计
            for result in execution_results:
                if result.success:
                    self.session_stats["successful_executions"] += 1
                else:
                    self.session_stats["failed_executions"] += 1
            
            # 阶段3: 反思（并行）
            logger.info("阶段3: 反思")

            async def _reflect_one(result):
                # 空结果/超时结果跳过 LLM 反思，直接返回轻量占位
                if not result.success and not result.output:
                    return {
                        "subtask_id": result.subtask_id,
                        "insights": [],
                        "replan_needed": False,
                        "hard_action": None,
                        "_skipped": True,
                    }
                subtask_data = self._get_subtask_data(result.subtask_id)
                return await self.reflector.analyze_execution_result(
                    result.subtask_id,
                    result.output,
                    subtask_data,
                )

            reflections = await asyncio.gather(
                *[_reflect_one(r) for r in execution_results],
                return_exceptions=False,
            )
            all_reflections.extend(reflections)

                # ✅ 处理 hard_action：reflector 硬规则触发的动作
                hard_action = reflection.get("hard_action")
                if hard_action == "trigger_validation":
                    # 发现漏洞，注入验证任务
                    validate_id = f"validate_{result.subtask_id}"
                    logger.info(f"[hard_action] 注入验证任务: {validate_id}")
                    validate_task = {
                        "id": validate_id,
                        "data": {
                            "task_type": "validation",
                            "description": f"验证 {result.subtask_id} 发现的漏洞",
                            "original_subtask_id": result.subtask_id,
                            "original_result": result.output,
                        },
                        "priority": 1,
                        "status": "pending",
                    }
                    if self.graph_manager and hasattr(self.graph_manager, "add_node"):
                        self.graph_manager.add_node(validate_id, validate_task["data"])
                    elif hasattr(self, "_pending_inject"):
                        self._pending_inject.append(validate_task)
                elif hard_action == "switch_tool":
                    logger.info(f"[hard_action] 工具失败，重规划将切换工具: {result.subtask_id}")
            
            self.session_stats["total_reflections"] += len(reflections)
            
            # 阶段4: 动态重规划
            logger.info("阶段4: 动态重规划")
            
            # 全部反思被跳过时（均为空结果），跳过 LLM 情报摘要，避免无效调用
            all_skipped = all(r.get("_skipped") for r in reflections if isinstance(r, dict))
            if all_skipped:
                intelligence_summary = {"audit_result": {"status": "in_progress"}}
                logger.debug("本轮反思全部跳过，跳过 LLM intelligence_summary 调用")
            else:
                intelligence_summary = await self.reflector.generate_intelligence_summary(reflections)
            
            # 检查是否达成目标
            if intelligence_summary.get("audit_result", {}).get("status") == "goal_achieved":
                logger.info("目标已达成，结束P-E-R循环")
                break
            
            # 执行动态重规划
            replan_operations = await self.planner.dynamic_replan(
                goal,
                self._get_current_graph_state(),
                intelligence_summary
            )
            
            if replan_operations:
                self.session_stats["total_planning"] += 1
                for operation in replan_operations:
                    self._apply_graph_operation(operation)
            
            # 检查是否需要历史压缩
            if self._needs_history_compression():
                logger.info("执行历史压缩")
                self._compress_history()
        
        # 生成最终报告
        final_report = await self._generate_final_report(all_reflections)
        
        logger.info(f"P-E-R循环结束，共执行{iteration}次迭代")
        
        return final_report
    
    async def _execute_pending_tasks(self) -> List[Any]:
        """执行待处理任务（并行加速版）

        无依赖关系的任务通过 asyncio.gather 并发执行，
        有显式依赖的任务按依赖顺序串行。

        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        pending_tasks = self._get_pending_tasks()
        if not pending_tasks:
            return []

        # 按优先级排序
        pending_tasks.sort(key=lambda x: x.get("priority", 99))

        # 将任务分为「无依赖」和「有依赖」两批
        independent, dependent = [], []
        for task in pending_tasks:
            deps = task.get("data", {}).get("dependencies", []) or task.get("dependencies", [])
            if deps:
                dependent.append(task)
            else:
                independent.append(task)

        # 并行执行无依赖任务（最多 5 个同时跑，避免资源耗尽）
        MAX_PARALLEL = 5
        results = []

        async def _run_one(task):
            task_id = task.get("id")
            task_data = task.get("data", {})
            logger.debug(f"并行执行任务: {task_id}")
            result = await self.executor.execute_subtask(task_id, task_data, self.graph_manager)
            self.session_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "execution",
                "task_id": task_id,
                "success": result.success,
            })
            return result

        # 分批并行（每批 MAX_PARALLEL 个）
        for i in range(0, len(independent), MAX_PARALLEL):
            batch = independent[i:i + MAX_PARALLEL]
            batch_results = await asyncio.gather(*[_run_one(t) for t in batch], return_exceptions=False)
            results.extend(batch_results)

        # 有依赖的任务仍串行执行（依赖已满足才能跑）
        for task in dependent:
            results.append(await _run_one(task))

        return results
    
    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待处理任务
        
        Returns:
            List[Dict[str, Any]]: 待处理任务列表
        """
        if self.graph_manager:
            # 从图谱管理器获取
            try:
                return self.graph_manager.get_pending_nodes()
            except Exception as e:
                logger.debug(f"Error getting pending tasks: {e}")
        
        # 回退：返回空列表
        return []
    
    def _get_subtask_data(self, subtask_id: str) -> Dict[str, Any]:
        """获取子任务数据
        
        Args:
            subtask_id: 子任务ID
            
        Returns:
            Dict[str, Any]: 子任务数据
        """
        if self.graph_manager:
            try:
                node = self.graph_manager.get_node(subtask_id)
                if node:
                    return node
            except Exception as e:
                logger.debug(f"Error getting subtask data for {subtask_id}: {e}")
        
        # 回退：返回默认数据
        return {
            "description": f"任务: {subtask_id}",
            "mission_briefing": "执行任务",
            "completion_criteria": "完成目标"
        }
    
    def _apply_graph_operation(self, operation: Dict[str, Any]) -> bool:
        """应用图操作
        
        Args:
            operation: 图操作指令
            
        Returns:
            bool: 是否成功
        """
        if not self.graph_manager:
            return False
        
        command = operation.get("command", "").upper()
        
        try:
            if command == "ADD_NODE":
                node_data = operation.get("node_data", {})
                node_id = node_data.get("id")
                if node_id:
                    self.graph_manager.add_node(node_id, node_data)
                    return True
            
            elif command == "UPDATE_NODE":
                node_id = operation.get("node_id")
                updates = operation.get("updates", {})
                if node_id:
                    self.graph_manager.update_node(node_id, updates)
                    return True
            
            elif command == "DEPRECATE_NODE":
                node_id = operation.get("node_id")
                if node_id:
                    self.graph_manager.update_node(node_id, {"status": "deprecated"})
                    return True
        
        except Exception as e:
            logger.warning(f"图操作失败: {command} - {e}")
        
        return False
    
    def _get_current_graph_state(self) -> Dict[str, Any]:
        """获取当前图谱状态
        
        Returns:
            Dict[str, Any]: 图谱状态
        """
        if self.graph_manager:
            try:
                return {
                    "nodes": self.graph_manager.get_all_nodes(),
                    "edges": self.graph_manager.get_all_edges() if hasattr(self.graph_manager, 'get_all_edges') else []
                }
            except Exception as e:
                logger.debug(f"Error getting graph state: {e}")
        
        return {"nodes": {}, "edges": []}
    
    def _check_goal_completion(self) -> bool:
        """检查目标是否完成
        
        Returns:
            bool: 目标是否完成
        """
        if not self.graph_manager:
            return False
        
        try:
            # 检查是否所有任务都已完成
            all_nodes = self.graph_manager.get_all_nodes()
            
            if not all_nodes:
                return False
            
            # 检查是否有未完成的任务
            for node_id, node_data in all_nodes.items():
                status = node_data.get("status", "unknown")
                if status in ["pending", "in_progress"]:
                    return False
            
            # 所有任务都已完成
            return True
        
        except Exception as e:
            logger.debug(f"Error checking goal completion: {e}")
            return False
    
    def _needs_history_compression(self) -> bool:
        """检查是否需要历史压缩
        
        Returns:
            bool: 是否需要压缩
        """
        return (
            self.planner.needs_compression() or
            self.reflector.needs_compression() or
            len(self.session_history) > 50
        )
    
    def _compress_history(self) -> None:
        """压缩历史"""
        logger.info("执行历史压缩")
        
        # 压缩规划历史
        if self.planner.needs_compression():
            self.planner.mark_compressed()
        
        # 压缩反思历史
        if self.reflector.needs_compression():
            self.reflector.mark_compressed()
        
        # 压缩会话历史
        if len(self.session_history) > 50:
            # 保留最近的记录
            self.session_history = self.session_history[-25:]
    
    async def _generate_final_report(self, all_reflections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成最终报告

        区分已验证漏洞（verified_findings）和疑似漏洞（unverified_findings），
        让报告具有"证据驱动"的专业性。
        """
        # 生成情报摘要
        intelligence_summary = await self.reflector.generate_intelligence_summary(all_reflections)

        # 从反思历史中收集验证任务结果
        verified_findings = []
        unverified_findings = []

        for reflection in all_reflections:
            exec_summary = reflection.get("execution_summary", {})
            task_type = exec_summary.get("task_type", "")
            hard_action = reflection.get("hard_action", "")

            if task_type == "validation":
                # 来自 ValidatorAgent 的结果
                vr = exec_summary.get("validation_result", {})
                if vr.get("verified"):
                    verified_findings.append({
                        "vuln_type": vr.get("vuln_type"),
                        "target": vr.get("target"),
                        "confidence": vr.get("confidence"),
                        "exploit_proof": vr.get("exploit_proof"),
                        "evidence": vr.get("evidence", []),
                        "suggested_next": vr.get("suggested_next"),
                    })
                else:
                    # 验证未通过，仍记录为疑似
                    unverified_findings.append({
                        "vuln_type": vr.get("vuln_type"),
                        "target": vr.get("target"),
                        "confidence": vr.get("confidence", 0.3),
                        "note": "二次验证未能复现，可能是误报",
                    })
            elif hard_action == "trigger_validation":
                # 等待验证的疑似漏洞
                for finding in reflection.get("key_findings", []):
                    unverified_findings.append({
                        "description": str(finding),
                        "confidence": 0.5,
                        "note": "已发现信号，验证任务已触发",
                    })

        # 从 intelligence_summary 的通用 findings 中补充未分类发现
        for f in intelligence_summary.get("findings", []):
            f_str = str(f)
            already_tracked = any(
                str(v.get("description", "") + v.get("exploit_proof", "")) == f_str
                for v in verified_findings + unverified_findings
            )
            if not already_tracked:
                unverified_findings.append({"description": f_str, "confidence": 0.4})

        # 构建报告
        report = {
            "success": True,
            "session_id": self.session_id,
            "goal": self.current_goal,
            "target_info": self.target_info,
            "iterations": self.iteration_count,
            "status": intelligence_summary.get("audit_result", {}).get("status", "unknown"),
            # 核心区分：已验证 vs 疑似
            "verified_findings": verified_findings,
            "unverified_findings": unverified_findings,
            "verified_count": len(verified_findings),
            "unverified_count": len(unverified_findings),
            # 保留原有字段
            "findings": intelligence_summary.get("findings", []),
            "patterns_summary": intelligence_summary.get("patterns_summary", {}),
            "strategic_recommendations": intelligence_summary.get("strategic_recommendations", []),
            "session_stats": self.session_stats,
            "timestamp": datetime.now().isoformat(),
            "use_llm": self.use_llm,
        }

        # 添加LLM统计
        if self.llm_integration:
            report["llm_stats"] = self.llm_integration.get_stats()

        return report
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要
        
        Returns:
            Dict[str, Any]: 会话摘要
        """
        return {
            "session_id": self.session_id,
            "goal": self.current_goal,
            "iterations": self.iteration_count,
            "session_stats": self.session_stats,
            "planner_summary": self.planner.get_planning_summary(),
            "executor_summary": self.executor.get_execution_summary(),
            "reflector_summary": self.reflector.get_reflection_summary(),
            "use_llm": self.use_llm
        }
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.session_id = None
        self.current_goal = None
        self.target_info = None
        self.execution_context = {}
        self.session_history.clear()
        self.iteration_count = 0
        
        # 重置统计
        self.session_stats = {
            "total_iterations": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_planning": 0,
            "total_reflections": 0,
            "llm_calls": 0
        }
        
        # 清空组件历史
        self.planner.clear_history()
        self.reflector.clear_history()
        self.executor.clear_history()
        
        logger.info("PER Agent已重置")


async def test_per_agent():
    """测试PER智能体"""
    import sys
    
    print("=" * 80)
    print("PER智能体测试")
    print("=" * 80)
    
    # 创建PER智能体（不使用LLM进行测试）
    agent = PERAgent(use_llm=False)
    
    # 测试目标
    goal = "对example.com进行渗透测试"
    target_info = {
        "target": "example.com",
        "type": "web_application",
        "scope": ["example.com", "www.example.com"]
    }
    
    context = {
        "scan_depth": "standard",
        "timeout": 300
    }
    
    print(f"\n目标: {goal}")
    print(f"目标信息: {target_info}")
    
    # 运行PER循环（模拟执行）
    print("\n运行P-E-R循环...")
    
    # 由于我们没有真正的图谱管理器，这里只测试组件
    print("\n测试Planner组件:")
    operations = await agent.planner.generate_initial_plan(goal, target_info)
    print(f"  生成 {len(operations)} 个图操作")
    for i, op in enumerate(operations[:3]):
        cmd = op.get("command", "UNKNOWN")
        node_id = op.get("node_data", {}).get("id", "unknown")
        print(f"    {i+1}. [{cmd}] {node_id}")
    
    print("\n测试Executor组件:")
    agent.executor.set_context(context)
    
    test_task = {
        "description": "信息收集: example.com",
        "mission_briefing": "对目标进行全面的信息收集",
        "completion_criteria": "完成端口扫描和服务识别"
    }
    
    result = await agent.executor.execute_subtask("test_task", test_task)
    print(f"  执行结果: {'成功' if result.success else '失败'}")
    print(f"  执行时间: {result.execution_time:.2f}秒")
    print(f"  工具调用数: {len(result.tool_calls)}")
    
    print("\n测试Reflector组件:")
    subtask_data = {
        "description": "信息收集: example.com",
        "mission_briefing": "对目标进行全面的信息收集",
        "completion_criteria": "完成端口扫描和服务识别"
    }
    
    reflection = await agent.reflector.analyze_execution_result(
        "test_task",
        result.output,
        subtask_data
    )
    print(f"  反思状态: {reflection['audit_result']['status']}")
    print(f"  关键发现数: {len(reflection['key_findings'])}")
    print(f"  洞察: {reflection['insight'][:50]}...")
    
    print("\n测试会话摘要:")
    summary = agent.get_session_summary()
    print(f"  总迭代数: {summary['session_stats']['total_iterations']}")
    print(f"  成功执行: {summary['session_stats']['successful_executions']}")
    print(f"  使用LLM: {summary['use_llm']}")
    
    print("\n" + "=" * 80)
    print("[PASS] PER智能体测试完成")
    
    return True


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_per_agent())
    sys.exit(0 if success else 1)
