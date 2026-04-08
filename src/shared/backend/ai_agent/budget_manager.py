# -*- coding: utf-8 -*-
"""
Token Budget 管理器
Token 预算分配、追踪和预警
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class BudgetPhase(Enum):
    """预算阶段"""
    RECONNAISSANCE = "reconnaissance"    # 信息收集
    VULN_SCAN = "vuln_scan"             # 漏洞扫描
    EXPLOITATION = "exploitation"        # 漏洞利用
    POST_EXPLOIT = "post_exploit"        # 后渗透
    REPORTING = "reporting"              # 报告生成


@dataclass
class TokenUsage:
    """Token 使用记录"""
    phase: BudgetPhase
    input_tokens: int
    output_tokens: int
    total_tokens: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_calls: int = 0
    model: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls,
            "model": self.model
        }


@dataclass
class BudgetAllocation:
    """预算分配"""
    phase: BudgetPhase
    allocated: int          # 分配的预算
    used: int = 0           # 已使用的预算
    reserved: int = 0       # 预留的预算
    
    @property
    def remaining(self) -> int:
        """剩余预算"""
        return self.allocated - self.used - self.reserved
    
    @property
    def utilization_rate(self) -> float:
        """利用率"""
        if self.allocated == 0:
            return 0.0
        return self.used / self.allocated
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "allocated": self.allocated,
            "used": self.used,
            "reserved": self.reserved,
            "remaining": self.remaining,
            "utilization_rate": round(self.utilization_rate, 3)
        }


class BudgetManager:
    """预算管理器
    
    功能：
    1. Token 预算分配
    2. 使用追踪
    3. 预警机制
    4. 动态调整
    """
    
    # 默认预算分配比例
    DEFAULT_BUDGET_SPLITS = {
        BudgetPhase.RECONNAISSANCE: 0.20,   # 20%
        BudgetPhase.VULN_SCAN: 0.35,       # 35%
        BudgetPhase.EXPLOITATION: 0.25,    # 25%
        BudgetPhase.POST_EXPLOIT: 0.10,    # 10%
        BudgetPhase.REPORTING: 0.10,       # 10%
    }
    
    # 预警阈值
    WARNING_THRESHOLD = 0.75    # 75% 时警告
    CRITICAL_THRESHOLD = 0.90   # 90% 时严重警告
    
    def __init__(
        self,
        total_budget: int = 100000,
        budget_splits: Dict[BudgetPhase, float] = None
    ):
        """初始化预算管理器
        
        Args:
            total_budget: 总预算（Token 数）
            budget_splits: 各阶段预算比例
        """
        self.total_budget = total_budget
        self.budget_splits = budget_splits or self.DEFAULT_BUDGET_SPLITS
        
        # 确保比例总和为 1
        total_split = sum(self.budget_splits.values())
        if abs(total_split - 1.0) > 0.01:
            logger.warning(f"预算比例总和 {total_split} 不等于 1，将自动调整")
            # 自动归一化
            self.budget_splits = {
                k: v / total_split for k, v in self.budget_splits.items()
            }
        
        # 初始化各阶段预算分配
        self.allocations: Dict[BudgetPhase, BudgetAllocation] = {}
        for phase, ratio in self.budget_splits.items():
            self.allocations[phase] = BudgetAllocation(
                phase=phase,
                allocated=int(total_budget * ratio)
            )
        
        # 使用记录
        self.usage_history: List[TokenUsage] = []
        
        # 当前阶段
        self.current_phase = BudgetPhase.RECONNAISSANCE
        
        # 回调
        self._on_warning = None
        self._on_exceeded = None
        
        logger.info(f"预算管理器初始化完成，总预算: {total_budget}")
    
    def set_callbacks(
        self,
        on_warning: callable = None,
        on_exceeded: callable = None
    ):
        """设置回调函数
        
        Args:
            on_warning: 预警回调
            on_exceeded: 超限回调
        """
        self._on_warning = on_warning
        self._on_exceeded = on_exceeded
    
    def record_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        phase: BudgetPhase = None,
        tool_calls: int = 0,
        model: str = ""
    ) -> bool:
        """记录 Token 使用
        
        Args:
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数
            phase: 阶段（可选，默认使用当前阶段）
            tool_calls: 工具调用次数
            model: 模型名称
            
        Returns:
            bool: 是否成功记录
        """
        phase = phase or self.current_phase
        total = input_tokens + output_tokens
        
        # 检查预算
        allocation = self.allocations.get(phase)
        if not allocation:
            logger.warning(f"未知的预算阶段: {phase}")
            return False
        
        if allocation.remaining < total:
            logger.warning(f"阶段 {phase.value} 预算不足: 剩余 {allocation.remaining}, 需要 {total}")
            
            if self._on_exceeded:
                self._on_exceeded(phase, allocation, total)
            
            return False
        
        # 记录使用
        allocation.used += total
        
        # 创建使用记录
        usage = TokenUsage(
            phase=phase,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            tool_calls=tool_calls,
            model=model
        )
        self.usage_history.append(usage)
        
        # 检查是否需要预警
        self._check_warning(phase, allocation)
        
        logger.debug(f"记录使用: {phase.value} - {total} tokens")
        return True
    
    def reserve_budget(self, phase: BudgetPhase, amount: int) -> bool:
        """预留预算
        
        Args:
            phase: 阶段
            amount: 预留数量
            
        Returns:
            bool: 是否成功
        """
        allocation = self.allocations.get(phase)
        if not allocation:
            return False
        
        if allocation.remaining < amount:
            return False
        
        allocation.reserved += amount
        logger.debug(f"预留预算: {phase.value} - {amount}")
        return True
    
    def release_reservation(self, phase: BudgetPhase, amount: int = None):
        """释放预留预算
        
        Args:
            phase: 阶段
            amount: 释放数量（None 表示全部释放）
        """
        allocation = self.allocations.get(phase)
        if not allocation:
            return
        
        if amount is None:
            amount = allocation.reserved
        
        allocation.reserved = max(0, allocation.reserved - amount)
        logger.debug(f"释放预留: {phase.value} - {amount}")
    
    def set_phase(self, phase: BudgetPhase):
        """设置当前阶段"""
        self.current_phase = phase
        logger.info(f"切换到阶段: {phase.value}")
    
    def get_phase_budget(self, phase: BudgetPhase) -> BudgetAllocation:
        """获取阶段预算"""
        return self.allocations.get(phase)
    
    def get_remaining_budget(self, phase: BudgetPhase = None) -> int:
        """获取剩余预算
        
        Args:
            phase: 阶段（None 表示总剩余）
            
        Returns:
            int: 剩余 Token 数
        """
        if phase:
            allocation = self.allocations.get(phase)
            return allocation.remaining if allocation else 0
        
        return sum(a.remaining for a in self.allocations.values())
    
    def get_total_used(self) -> int:
        """获取总使用量"""
        return sum(a.used for a in self.allocations.values())
    
    def get_utilization_rate(self) -> float:
        """获取总利用率"""
        if self.total_budget == 0:
            return 0.0
        return self.get_total_used() / self.total_budget
    
    def _check_warning(self, phase: BudgetPhase, allocation: BudgetAllocation):
        """检查是否需要预警"""
        rate = allocation.utilization_rate
        
        if rate >= self.CRITICAL_THRESHOLD:
            logger.warning(f"⚠️ 阶段 {phase.value} 预算严重不足: {rate*100:.1f}% 已使用")
            if self._on_warning:
                self._on_warning(phase, allocation, "critical")
        
        elif rate >= self.WARNING_THRESHOLD:
            logger.info(f"⚡ 阶段 {phase.value} 预算警告: {rate*100:.1f}% 已使用")
            if self._on_warning:
                self._on_warning(phase, allocation, "warning")
    
    def can_afford(self, estimated_tokens: int, phase: BudgetPhase = None) -> bool:
        """检查是否能负担
        
        Args:
            estimated_tokens: 预估 Token 数
            phase: 阶段（可选）
            
        Returns:
            bool: 是否能负担
        """
        remaining = self.get_remaining_budget(phase)
        return remaining >= estimated_tokens
    
    def adjust_budget(
        self,
        phase: BudgetPhase,
        adjustment: int
    ) -> bool:
        """调整阶段预算
        
        Args:
            phase: 阶段
            adjustment: 调整量（正数增加，负数减少）
            
        Returns:
            bool: 是否成功
        """
        allocation = self.allocations.get(phase)
        if not allocation:
            return False
        
        new_allocated = allocation.allocated + adjustment
        
        # 确保不会少于已使用的量
        if new_allocated < allocation.used:
            logger.warning(f"无法将预算调整到 {new_allocated}，已使用 {allocation.used}")
            return False
        
        allocation.allocated = new_allocated
        logger.info(f"调整预算: {phase.value} -> {new_allocated}")
        return True
    
    def reallocate_unused(self, from_phase: BudgetPhase, to_phase: BudgetPhase):
        """重新分配未使用的预算
        
        Args:
            from_phase: 源阶段
            to_phase: 目标阶段
        """
        from_alloc = self.allocations.get(from_phase)
        to_alloc = self.allocations.get(to_phase)
        
        if not from_alloc or not to_alloc:
            return
        
        unused = from_alloc.remaining
        if unused > 0:
            from_alloc.allocated = from_alloc.used
            to_alloc.allocated += unused
            logger.info(f"重新分配预算: {from_phase.value} -> {to_phase.value}: {unused}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取预算摘要"""
        return {
            "total_budget": self.total_budget,
            "total_used": self.get_total_used(),
            "total_remaining": self.get_remaining_budget(),
            "utilization_rate": round(self.get_utilization_rate(), 3),
            "current_phase": self.current_phase.value,
            "allocations": {
                phase.value: alloc.to_dict()
                for phase, alloc in self.allocations.items()
            },
            "usage_count": len(self.usage_history)
        }
    
    def get_detailed_usage(self) -> List[Dict[str, Any]]:
        """获取详细使用记录"""
        return [usage.to_dict() for usage in self.usage_history]
    
    def reset(self):
        """重置预算"""
        for allocation in self.allocations.values():
            allocation.used = 0
            allocation.reserved = 0
        
        self.usage_history.clear()
        self.current_phase = BudgetPhase.RECONNAISSANCE
        
        logger.info("预算已重置")


# ==================== 便捷函数 ====================

def create_budget_manager(
    total_budget: int = 100000,
    **kwargs
) -> BudgetManager:
    """创建预算管理器
    
    Args:
        total_budget: 总预算
        **kwargs: 其他参数
        
    Returns:
        BudgetManager: 管理器实例
    """
    return BudgetManager(total_budget=total_budget)


# ==================== 测试 ====================

def test_budget_manager():
    """测试预算管理器"""
    print("=" * 60)
    print("Budget Manager 测试")
    print("=" * 60)
    
    manager = create_budget_manager(total_budget=100000)
    
    # 测试预算分配
    print("\n1. 预算分配:")
    summary = manager.get_summary()
    for phase, alloc in summary["allocations"].items():
        print(f"  {phase}: {alloc['allocated']} tokens ({alloc['allocated']/1000:.1f}k)")
    
    # 测试使用记录
    print("\n2. 使用记录:")
    manager.set_phase(BudgetPhase.RECONNAISSANCE)
    manager.record_usage(1000, 500, tool_calls=2, model="deepseek-chat")
    manager.record_usage(800, 400)
    
    print(f"  已使用: {manager.get_total_used()}")
    print(f"  利用率: {manager.get_utilization_rate()*100:.1f}%")
    
    # 测试预算检查
    print("\n3. 预算检查:")
    print(f"  能负担 50k: {manager.can_afford(50000)}")
    print(f"  能负担 10k: {manager.can_afford(10000)}")
    
    # 测试摘要
    print("\n4. 预算摘要:")
    summary = manager.get_summary()
    print(f"  总预算: {summary['total_budget']}")
    print(f"  已使用: {summary['total_used']}")
    print(f"  剩余: {summary['total_remaining']}")
    print(f"  利用率: {summary['utilization_rate']*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_budget_manager()
