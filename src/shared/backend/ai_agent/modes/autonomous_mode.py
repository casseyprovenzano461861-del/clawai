# -*- coding: utf-8 -*-
"""
自主模式
AI 自动执行完整的渗透测试流程
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

from ..per_adapter import PERAdapter, PERState, PERProgress
from ..conversation import ConversationManager
from ..risk_assessor import RiskLevel
from ..prompts.system_prompt import get_system_prompt

logger = logging.getLogger(__name__)


@dataclass
class AutonomousModeConfig:
    """自主模式配置"""
    max_iterations: int = 10               # 最大迭代次数
    pause_on_high_risk: bool = True         # 高风险操作暂停
    auto_continue: bool = False             # 自动继续（忽略风险）
    report_progress: bool = True            # 报告进度
    check_interval: float = 1.0             # 状态检查间隔


class AutonomousMode:
    """自主模式
    
    特点：
    - AI 自动执行完整的渗透测试流程
    - 基于 P-E-R 框架
    - 高风险操作可选暂停等待确认
    - 实时报告进度
    """
    
    def __init__(
        self,
        per_adapter: PERAdapter,
        conversation: ConversationManager,
        config: AutonomousModeConfig = None,
        confirmation_handler: Callable = None,
        progress_handler: Callable = None
    ):
        """初始化自主模式
        
        Args:
            per_adapter: P-E-R 适配器
            conversation: 对话管理器
            config: 配置
            confirmation_handler: 确认处理回调
            progress_handler: 进度处理回调
        """
        self.per_adapter = per_adapter
        self.conversation = conversation
        self.config = config or AutonomousModeConfig()
        self.confirmation_handler = confirmation_handler
        self.progress_handler = progress_handler
        
        # 设置 P-E-R 回调
        if per_adapter:
            per_adapter.set_callbacks(
                on_progress=self._on_per_progress,
                on_task_start=self._on_task_start,
                on_task_complete=self._on_task_complete,
                on_iteration_complete=self._on_iteration_complete
            )
        
        # 执行状态
        self.is_executing = False
        self.pause_requested = False
        self.current_phase = ""
        
        logger.info("自主模式初始化完成")
    
    async def start(
        self,
        target: str,
        goal: str = None,
        mode: str = "full"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """启动自主渗透测试
        
        Args:
            target: 目标地址
            goal: 测试目标描述
            mode: 测试模式 (recon/vuln_scan/full)
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        if self.is_executing:
            yield {"type": "error", "message": "已有任务在执行中"}
            return
        
        self.is_executing = True
        self.pause_requested = False
        
        # 生成目标描述
        if not goal:
            goal = self._generate_goal(target, mode)
        
        # 更新上下文
        self.conversation.set_target(target)
        self.conversation.set_phase("autonomous_start")
        
        # 记录开始
        start_time = datetime.now()
        
        yield {
            "type": "start",
            "target": target,
            "goal": goal,
            "mode": mode,
            "timestamp": start_time.isoformat()
        }
        
        # 添加系统消息
        self.conversation.add_system_message(f"开始自主渗透测试: {goal}")
        
        try:
            # 执行 P-E-R 循环
            async for event in self._execute_per_cycle(target, goal):
                yield event
                
                # 检查暂停请求
                if self.pause_requested:
                    yield {"type": "paused", "message": "用户请求暂停"}
                    break
        
        except Exception as e:
            logger.error(f"自主模式执行失败: {e}")
            yield {"type": "error", "message": str(e)}
        
        finally:
            self.is_executing = False
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            yield {
                "type": "complete",
                "duration": duration,
                "timestamp": end_time.isoformat()
            }
    
    async def _execute_per_cycle(
        self,
        target: str,
        goal: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行 P-E-R 循环"""
        if not self.per_adapter:
            yield {"type": "error", "message": "P-E-R 适配器未配置"}
            return
        
        # 启动 P-E-R
        result = await self.per_adapter.run_autonomous(goal, target)
        
        # 报告最终结果
        yield {
            "type": "result",
            "success": result.success,
            "goal_achieved": result.goal_achieved,
            "iterations": result.iterations,
            "metrics": result.metrics,
            "graph_state": result.graph_state
        }
        
        # 更新对话上下文
        self.conversation.update_context(
            phase="completed" if result.success else "failed"
        )
        
        # 添加结果摘要到历史
        summary = self._generate_summary(result)
        self.conversation.add_assistant_message(summary)
        
        yield {"type": "summary", "content": summary}
    
    def pause(self):
        """请求暂停"""
        self.pause_requested = True
        if self.per_adapter:
            self.per_adapter.pause()
    
    def resume(self):
        """恢复执行"""
        self.pause_requested = False
        if self.per_adapter:
            self.per_adapter.resume()
    
    def stop(self):
        """停止执行"""
        self.is_executing = False
        if self.per_adapter:
            self.per_adapter.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        progress = self.per_adapter.get_progress() if self.per_adapter else None
        
        return {
            "is_executing": self.is_executing,
            "is_paused": self.pause_requested,
            "current_phase": self.current_phase,
            "progress": progress.to_dict() if progress else None
        }
    
    # ==================== P-E-R 回调处理 ====================
    
    def _on_per_progress(self, progress: PERProgress):
        """P-E-R 进度回调"""
        self.current_phase = progress.state.value
        
        if self.progress_handler:
            self.progress_handler(progress)
    
    def _on_task_start(self, task_id: str, task_data: Dict[str, Any]):
        """任务开始回调"""
        logger.info(f"任务开始: {task_id}")
    
    def _on_task_complete(self, task_id: str, result: Dict[str, Any]):
        """任务完成回调"""
        logger.info(f"任务完成: {task_id}")
    
    def _on_iteration_complete(self, iteration: int, max_iterations: int):
        """迭代完成回调"""
        logger.info(f"迭代完成: {iteration}/{max_iterations}")
    
    # ==================== 辅助方法 ====================
    
    def _generate_goal(self, target: str, mode: str) -> str:
        """生成测试目标描述"""
        mode_descriptions = {
            "recon": f"对 {target} 进行信息收集和资产发现",
            "vuln_scan": f"对 {target} 进行漏洞扫描和安全评估",
            "full": f"对 {target} 进行完整的渗透测试，包括信息收集、漏洞扫描、漏洞利用等阶段"
        }
        
        return mode_descriptions.get(mode, f"对 {target} 进行安全测试")
    
    def _generate_summary(self, result) -> str:
        """生成执行摘要"""
        lines = [
            "## 渗透测试执行报告",
            "",
            f"**目标**: {result.target}",
            f"**状态**: {'成功' if result.success else '失败'}",
            f"**目标达成**: {'是' if result.goal_achieved else '否'}",
            f"**迭代次数**: {result.iterations}",
            ""
        ]
        
        if result.metrics:
            lines.append("### 指标")
            for key, value in result.metrics.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        
        graph_state = result.graph_state
        if graph_state:
            status_dist = graph_state.get("status_distribution", {})
            lines.append("### 任务状态分布")
            for status, count in status_dist.items():
                lines.append(f"- {status}: {count}")
        
        return "\n".join(lines)


# ==================== 测试 ====================

async def test_autonomous_mode():
    """测试自主模式"""
    print("=" * 60)
    print("自主模式测试")
    print("=" * 60)
    
    from ..conversation import ConversationManager
    from ..per_adapter import PERAdapter
    
    # 创建组件
    per_adapter = PERAdapter(max_iterations=3)
    conversation = ConversationManager()
    
    mode = AutonomousMode(per_adapter, conversation)
    
    # 启动测试
    print("\n启动自主渗透测试:")
    async for event in mode.start("example.com", mode="recon"):
        event_type = event.get("type")
        if event_type == "start":
            print(f"  开始: {event['target']}")
        elif event_type == "progress":
            print(f"  进度: {event.get('message', '')}")
        elif event_type == "result":
            print(f"  结果: {'成功' if event['success'] else '失败'}")
        elif event_type == "complete":
            print(f"  完成，耗时: {event['duration']:.2f}秒")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(test_autonomous_mode())
