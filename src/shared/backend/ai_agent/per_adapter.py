# -*- coding: utf-8 -*-
"""
P-E-R 框架适配器
连接 AI Agent 与自动化渗透测试框架
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PERState(Enum):
    """P-E-R 执行状态"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class PERExecutionResult:
    """P-E-R 执行结果"""
    success: bool
    goal: str
    target: str
    iterations: int
    goal_achieved: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    planning_summary: Dict[str, Any] = field(default_factory=dict)
    execution_summary: Dict[str, Any] = field(default_factory=dict)
    reflection_summary: Dict[str, Any] = field(default_factory=dict)
    graph_state: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "goal": self.goal,
            "target": self.target,
            "iterations": self.iterations,
            "goal_achieved": self.goal_achieved,
            "metrics": self.metrics,
            "planning_summary": self.planning_summary,
            "execution_summary": self.execution_summary,
            "reflection_summary": self.reflection_summary,
            "graph_state": self.graph_state,
            "timestamp": self.timestamp
        }


@dataclass
class PERProgress:
    """P-E-R 执行进度"""
    state: PERState
    current_iteration: int
    max_iterations: int
    current_task: str
    completed_tasks: int
    total_tasks: int
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state": self.state.value,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "progress_percent": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
            "message": self.message
        }


class PERAdapter:
    """P-E-R 框架适配器
    
    连接 AI Agent 与 P-E-R 自动化渗透测试框架，
    提供自主模式的渗透测试能力。
    """
    
    def __init__(
        self,
        per_agent=None,
        max_iterations: int = 10,
        auto_start: bool = False
    ):
        """初始化 P-E-R 适配器
        
        Args:
            per_agent: PERAgent 实例
            max_iterations: 最大迭代次数
            auto_start: 是否自动开始执行
        """
        self.per_agent = per_agent
        self.max_iterations = max_iterations
        self.auto_start = auto_start
        
        # 执行状态
        self.state = PERState.IDLE
        self.current_goal = ""
        self.current_target = ""
        self.progress: Optional[PERProgress] = None
        self.result: Optional[PERExecutionResult] = None
        
        # 回调函数
        self._on_progress: Optional[Callable] = None
        self._on_task_start: Optional[Callable] = None
        self._on_task_complete: Optional[Callable] = None
        self._on_iteration_complete: Optional[Callable] = None
        
        # 执行任务
        self._execution_task: Optional[asyncio.Task] = None
        
        logger.info(f"PERAdapter 初始化完成，最大迭代次数: {max_iterations}")
    
    # ==================== 回调设置 ====================
    
    def set_callbacks(
        self,
        on_progress: Callable = None,
        on_task_start: Callable = None,
        on_task_complete: Callable = None,
        on_iteration_complete: Callable = None
    ):
        """设置回调函数
        
        Args:
            on_progress: 进度更新回调
            on_task_start: 任务开始回调
            on_task_complete: 任务完成回调
            on_iteration_complete: 迭代完成回调
        """
        self._on_progress = on_progress
        self._on_task_start = on_task_start
        self._on_task_complete = on_task_complete
        self._on_iteration_complete = on_iteration_complete
    
    # ==================== 核心方法 ====================
    
    async def run_autonomous(
        self,
        goal: str,
        target: str,
        target_info: Dict[str, Any] = None
    ) -> PERExecutionResult:
        """执行自主渗透测试模式
        
        Args:
            goal: 测试目标描述
            target: 目标地址
            target_info: 目标额外信息
            
        Returns:
            PERExecutionResult: 执行结果
        """
        if not self.per_agent:
            logger.error("PERAgent 未配置")
            return PERExecutionResult(
                success=False,
                goal=goal,
                target=target,
                iterations=0,
                goal_achieved=False,
                metrics={"error": "PERAgent 未配置"}
            )
        
        # 初始化状态
        self.current_goal = goal
        self.current_target = target
        self.state = PERState.PLANNING
        self.result = None
        
        # 初始化进度
        self._update_progress(
            PERState.PLANNING,
            0,
            "正在规划渗透测试任务..."
        )
        
        try:
            # 设置目标
            target_info = target_info or {
                "target": target,
                "type": self._infer_target_type(target)
            }
            
            self.per_agent.set_goal(goal, target_info)
            
            # 运行 P-E-R 循环
            result = await self._run_per_cycle()
            
            self.result = result
            self.state = PERState.COMPLETED if result.success else PERState.FAILED
            
            return result
            
        except Exception as e:
            logger.error(f"P-E-R 执行失败: {e}")
            self.state = PERState.FAILED
            
            return PERExecutionResult(
                success=False,
                goal=goal,
                target=target,
                iterations=0,
                goal_achieved=False,
                metrics={"error": str(e)}
            )
    
    async def _run_per_cycle(self) -> PERExecutionResult:
        """运行 P-E-R 循环"""
        iteration = 0
        
        while iteration < self.max_iterations and self.state != PERState.STOPPED:
            iteration += 1
            
            # 更新状态
            self._update_progress(
                PERState.EXECUTING,
                iteration,
                f"执行迭代 {iteration}/{self.max_iterations}"
            )
            
            if self._on_iteration_complete:
                self._on_iteration_complete(iteration, self.max_iterations)
            
            # 执行一轮 P-E-R
            try:
                result = await self.per_agent.run()
                
                if result.get("goal_achieved"):
                    return self._build_result(result, iteration)
                
                # 重置 Agent 以继续下一轮
                self.per_agent.is_running = True
                
            except Exception as e:
                logger.error(f"迭代 {iteration} 执行失败: {e}")
        
        # 达到最大迭代次数，返回结果
        final_state = self.per_agent.graph_manager.get_graph_state()
        return self._build_result({"success": False, "final_state": final_state}, iteration)
    
    def _build_result(self, raw_result: Dict[str, Any], iterations: int) -> PERExecutionResult:
        """构建执行结果"""
        return PERExecutionResult(
            success=raw_result.get("success", False),
            goal=self.current_goal,
            target=self.current_target,
            iterations=iterations,
            goal_achieved=raw_result.get("goal_achieved", False),
            metrics=raw_result.get("metrics", {}),
            planning_summary=raw_result.get("planning_summary", {}),
            execution_summary=raw_result.get("execution_summary", {}),
            reflection_summary=raw_result.get("reflection_summary", {}),
            graph_state=raw_result.get("graph_state", raw_result.get("final_state", {})),
            execution_history=raw_result.get("execution_history", [])
        )
    
    # ==================== 控制方法 ====================
    
    def start(self):
        """开始执行"""
        if self.state == PERState.IDLE:
            self.state = PERState.PLANNING
            logger.info("P-E-R 执行已启动")
    
    def pause(self):
        """暂停执行"""
        if self.per_agent:
            self.per_agent.stop()
            self.state = PERState.STOPPED
            logger.info("P-E-R 执行已暂停")
    
    def resume(self):
        """恢复执行"""
        if self.state == PERState.STOPPED and self.per_agent:
            self.per_agent.is_running = True
            self.state = PERState.EXECUTING
            logger.info("P-E-R 执行已恢复")
    
    def stop(self):
        """停止执行"""
        if self.per_agent:
            self.per_agent.stop()
        
        self.state = PERState.STOPPED
        logger.info("P-E-R 执行已停止")
    
    def reset(self):
        """重置状态"""
        if self.per_agent:
            self.per_agent.reset()
        
        self.state = PERState.IDLE
        self.current_goal = ""
        self.current_target = ""
        self.progress = None
        self.result = None
        
        logger.info("P-E-R 适配器已重置")
    
    # ==================== 状态查询 ====================
    
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前执行状态"""
        if self.per_agent:
            return self.per_agent.graph_manager.get_graph_state()
        return {}
    
    def get_progress(self) -> Optional[PERProgress]:
        """获取执行进度"""
        return self.progress
    
    def get_result(self) -> Optional[PERExecutionResult]:
        """获取执行结果"""
        return self.result
    
    def is_running(self) -> bool:
        """是否正在执行"""
        return self.state in [PERState.PLANNING, PERState.EXECUTING, PERState.REFLECTING]
    
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.state in [PERState.COMPLETED, PERState.FAILED, PERState.STOPPED]
    
    # ==================== 辅助方法 ====================
    
    def _update_progress(
        self,
        state: PERState,
        iteration: int,
        message: str,
        current_task: str = ""
    ):
        """更新进度"""
        graph_state = self.get_current_state()
        
        completed_tasks = graph_state.get("status_distribution", {}).get("completed", 0)
        total_tasks = graph_state.get("total_nodes", 0)
        
        self.progress = PERProgress(
            state=state,
            current_iteration=iteration,
            max_iterations=self.max_iterations,
            current_task=current_task,
            completed_tasks=completed_tasks,
            total_tasks=total_tasks,
            message=message
        )
        
        if self._on_progress:
            self._on_progress(self.progress)
    
    def _infer_target_type(self, target: str) -> str:
        """推断目标类型"""
        target = target.lower()
        
        if target.startswith("http://") or target.startswith("https://"):
            return "web_application"
        elif ":" in target:
            return "network_service"
        elif target.replace(".", "").isdigit():
            return "ip_address"
        else:
            return "domain"
    
    def _get_status_summary(self) -> str:
        """获取状态摘要"""
        state_names = {
            PERState.IDLE: "空闲",
            PERState.PLANNING: "规划中",
            PERState.EXECUTING: "执行中",
            PERState.REFLECTING: "反思中",
            PERState.REPLANNING: "重规划中",
            PERState.COMPLETED: "已完成",
            PERState.FAILED: "失败",
            PERState.STOPPED: "已停止"
        }
        
        return f"""
P-E-R 执行状态:
- 状态: {state_names.get(self.state, self.state.value)}
- 目标: {self.current_target or '未设置'}
- 目标: {self.current_goal or '未设置'}
- 迭代: {self.progress.current_iteration if self.progress else 0}/{self.max_iterations}
"""


# ==================== 工厂函数 ====================

def create_per_adapter(
    skill_registry=None,
    llm_client=None,
    max_iterations: int = 10
) -> PERAdapter:
    """创建 P-E-R 适配器
    
    Args:
        skill_registry: 技能注册表
        llm_client: LLM 客户端
        max_iterations: 最大迭代次数
        
    Returns:
        PERAdapter: 适配器实例
    """
    try:
        # 尝试导入 PERAgent
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from backend.per.agent import PERAgent
        
        per_agent = PERAgent(
            skill_registry=skill_registry,
            llm_client=llm_client,
            max_iterations=max_iterations
        )
        
        return PERAdapter(per_agent=per_agent, max_iterations=max_iterations)
        
    except ImportError as e:
        logger.warning(f"无法导入 PERAgent: {e}")
        return PERAdapter(max_iterations=max_iterations)


# ==================== 测试 ====================

async def test_per_adapter():
    """测试 P-E-R 适配器"""
    print("=" * 60)
    print("P-E-R 适配器测试")
    print("=" * 60)
    
    # 创建适配器（无 PERAgent）
    adapter = PERAdapter(max_iterations=3)
    
    # 测试状态
    print("\n1. 初始状态:")
    print(f"  状态: {adapter.state.value}")
    print(f"  是否运行中: {adapter.is_running()}")
    
    # 设置回调
    def on_progress(progress):
        print(f"  [进度] {progress.state.value}: {progress.message}")
    
    adapter.set_callbacks(on_progress=on_progress)
    
    # 模拟执行（无 PERAgent）
    print("\n2. 模拟执行:")
    result = await adapter.run_autonomous("测试目标", "example.com")
    print(f"  结果: {'成功' if result.success else '失败'}")
    print(f"  原因: {result.metrics.get('error', '未知')}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(test_per_adapter())
