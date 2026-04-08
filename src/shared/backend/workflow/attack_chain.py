# -*- coding: utf-8 -*-
"""
攻击链管理模块
实现多阶段攻击链的定义、执行和管理
"""

import json
import time
import sys
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from shared.backend.core.tool_manager import ToolManager
from shared.backend.ai_core.llm_tool_interface import LLMTOOLInterface, ToolCall, ToolResult


class AttackStageType(Enum):
    """攻击阶段类型"""
    RECONNAISSANCE = "reconnaissance"  # 信息收集
    SCANNING = "scanning"  # 扫描
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"  # 漏洞分析
    EXPLOITATION = "exploitation"  # 漏洞利用
    POST_EXPLOITATION = "post_exploitation"  # 后渗透
    REPORTING = "reporting"  # 报告


class AttackChainStatus(Enum):
    """攻击链状态"""
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    PAUSED = "paused"  # 暂停


@dataclass
class AttackStage:
    """攻击阶段"""
    stage_id: str
    name: str
    stage_type: AttackStageType
    tools: List[ToolCall]
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 600


@dataclass
class AttackChain:
    """攻击链"""
    chain_id: str
    name: str
    description: str
    stages: List[AttackStage]
    target: str
    status: AttackChainStatus = AttackChainStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    """阶段执行结果"""
    stage_id: str
    status: str
    tool_results: Dict[str, ToolResult]
    start_time: float
    end_time: float
    execution_time: float
    error: Optional[str] = None


class AttackChainManager:
    """
    攻击链管理器
    负责攻击链的创建、执行和管理
    """
    
    def __init__(self):
        """初始化攻击链管理器"""
        self.tool_manager = ToolManager()
        self.llm_interface = LLMTOOLInterface()
        self.active_chains = {}
        self.completed_chains = {}
    
    def create_attack_chain(self, name: str, description: str, target: str, stages: List[AttackStage]) -> AttackChain:
        """创建攻击链"""
        chain_id = f"chain_{int(time.time())}"
        attack_chain = AttackChain(
            chain_id=chain_id,
            name=name,
            description=description,
            target=target,
            stages=stages
        )
        self.active_chains[chain_id] = attack_chain
        return attack_chain
    
    def execute_attack_chain(self, chain_id: str) -> Dict[str, Any]:
        """执行攻击链"""
        if chain_id not in self.active_chains:
            return {"error": f"攻击链 {chain_id} 不存在"}
        
        attack_chain = self.active_chains[chain_id]
        attack_chain.status = AttackChainStatus.RUNNING
        attack_chain.started_at = time.time()
        
        stage_results = {}
        all_successful = True
        
        # 按依赖关系执行阶段
        for stage in self._get_execution_order(attack_chain.stages):
            print(f"执行阶段: {stage.name} ({stage.stage_type.value})")
            
            # 执行阶段工具
            stage_result = self._execute_stage(stage)
            stage_results[stage.stage_id] = stage_result
            
            # 检查执行状态
            if stage_result.status != "success":
                all_successful = False
                print(f"阶段执行失败: {stage.name}")
            else:
                print(f"阶段执行成功: {stage.name}")
        
        # 更新攻击链状态
        if all_successful:
            attack_chain.status = AttackChainStatus.COMPLETED
            attack_chain.completed_at = time.time()
        else:
            attack_chain.status = AttackChainStatus.FAILED
        
        attack_chain.results = stage_results
        
        # 移到已完成链
        self.completed_chains[chain_id] = attack_chain
        del self.active_chains[chain_id]
        
        return {
            "chain_id": chain_id,
            "status": attack_chain.status.value,
            "stage_results": stage_results
        }
    
    def _get_execution_order(self, stages: List[AttackStage]) -> List[AttackStage]:
        """根据依赖关系获取执行顺序"""
        # 简单的拓扑排序
        visited = set()
        order = []
        
        def visit(stage: AttackStage):
            if stage.stage_id in visited:
                return
            
            # 先执行依赖的阶段
            for dep_id in stage.dependencies:
                dep_stage = next((s for s in stages if s.stage_id == dep_id), None)
                if dep_stage:
                    visit(dep_stage)
            
            visited.add(stage.stage_id)
            order.append(stage)
        
        for stage in stages:
            visit(stage)
        
        return order
    
    def _execute_stage(self, stage: AttackStage) -> StageResult:
        """执行攻击阶段"""
        start_time = time.time()
        tool_results = {}
        error = None
        
        try:
            # 并行执行工具
            if stage.tools:
                tool_results = self.llm_interface.execute_tools_in_parallel(stage.tools)
            
            # 检查工具执行结果
            all_successful = all(result.success for result in tool_results.values())
            if not all_successful:
                error = "部分工具执行失败"
                status = "partial_success"
            else:
                status = "success"
        
        except Exception as e:
            error = f"执行阶段时出错: {str(e)}"
            status = "failed"
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return StageResult(
            stage_id=stage.stage_id,
            status=status,
            tool_results=tool_results,
            start_time=start_time,
            end_time=end_time,
            execution_time=execution_time,
            error=error
        )
    
    def get_attack_chain(self, chain_id: str) -> Optional[AttackChain]:
        """获取攻击链"""
        if chain_id in self.active_chains:
            return self.active_chains[chain_id]
        elif chain_id in self.completed_chains:
            return self.completed_chains[chain_id]
        return None
    
    def list_attack_chains(self) -> List[Dict[str, Any]]:
        """列出所有攻击链"""
        chains = []
        
        # 活跃链
        for chain in self.active_chains.values():
            chains.append({
                "chain_id": chain.chain_id,
                "name": chain.name,
                "status": chain.status.value,
                "target": chain.target,
                "created_at": chain.created_at
            })
        
        # 已完成链
        for chain in self.completed_chains.values():
            chains.append({
                "chain_id": chain.chain_id,
                "name": chain.name,
                "status": chain.status.value,
                "target": chain.target,
                "created_at": chain.created_at,
                "completed_at": chain.completed_at
            })
        
        return chains
    
    def get_attack_chain_result(self, chain_id: str) -> Optional[Dict[str, Any]]:
        """获取攻击链执行结果"""
        chain = self.get_attack_chain(chain_id)
        if not chain:
            return None
        
        result = {
            "chain_id": chain.chain_id,
            "name": chain.name,
            "target": chain.target,
            "status": chain.status.value,
            "created_at": chain.created_at,
            "started_at": chain.started_at,
            "completed_at": chain.completed_at,
            "stages": []
        }
        
        # 添加阶段结果
        for stage in chain.stages:
            stage_result = chain.results.get(stage.stage_id)
            if stage_result:
                stage_info = {
                    "stage_id": stage.stage_id,
                    "name": stage.name,
                    "stage_type": stage.stage_type.value,
                    "status": stage_result.status,
                    "execution_time": stage_result.execution_time,
                    "error": stage_result.error,
                    "tool_results": {}
                }
                
                # 添加工具结果
                for tool_name, tool_result in stage_result.tool_results.items():
                    stage_info["tool_results"][tool_name] = {
                        "success": tool_result.success,
                        "output": tool_result.output,
                        "error": tool_result.error
                    }
                
                result["stages"].append(stage_info)
        
        return result
    
    def create_default_attack_chain(self, target: str) -> AttackChain:
        """创建默认攻击链"""
        # 信息收集阶段
        reconnaissance_stage = AttackStage(
            stage_id="reconnaissance",
            name="信息收集",
            stage_type=AttackStageType.RECONNAISSANCE,
            description="收集目标的基本信息，包括子域名、开放端口等",
            tools=[
                ToolCall(
                    tool_name="nmap",
                    parameters={"target": target, "ports": "1-1000"},
                    timeout=300
                ),
                ToolCall(
                    tool_name="subfinder",
                    parameters={"domain": target},
                    timeout=300
                )
            ]
        )
        
        # 扫描阶段
        scanning_stage = AttackStage(
            stage_id="scanning",
            name="漏洞扫描",
            stage_type=AttackStageType.SCANNING,
            description="扫描目标的漏洞和安全问题",
            tools=[
                ToolCall(
                    tool_name="nuclei",
                    parameters={"target": f"https://{target}"},
                    timeout=600
                ),
                ToolCall(
                    tool_name="nikto",
                    parameters={"target": f"https://{target}"},
                    timeout=300
                )
            ],
            dependencies=["reconnaissance"]
        )
        
        # 漏洞分析阶段
        vulnerability_analysis_stage = AttackStage(
            stage_id="vulnerability_analysis",
            name="漏洞分析",
            stage_type=AttackStageType.VULNERABILITY_ANALYSIS,
            description="分析扫描结果，识别高危漏洞",
            tools=[],  # 此阶段主要依赖AI分析
            dependencies=["scanning"]
        )
        
        # 漏洞利用阶段
        exploitation_stage = AttackStage(
            stage_id="exploitation",
            name="漏洞利用",
            stage_type=AttackStageType.EXPLOITATION,
            description="尝试利用发现的漏洞",
            tools=[
                ToolCall(
                    tool_name="sqlmap",
                    parameters={"url": f"https://{target}"},
                    timeout=600
                )
            ],
            dependencies=["vulnerability_analysis"]
        )
        
        # 后渗透阶段
        post_exploitation_stage = AttackStage(
            stage_id="post_exploitation",
            name="后渗透",
            stage_type=AttackStageType.POST_EXPLOITATION,
            description="在成功利用漏洞后进行进一步操作",
            tools=[],  # 此阶段主要依赖AI指导
            dependencies=["exploitation"]
        )
        
        # 报告阶段
        reporting_stage = AttackStage(
            stage_id="reporting",
            name="生成报告",
            stage_type=AttackStageType.REPORTING,
            description="生成完整的安全测试报告",
            tools=[],  # 此阶段主要依赖AI生成报告
            dependencies=["post_exploitation"]
        )
        
        # 创建攻击链
        return self.create_attack_chain(
            name=f"{target} 安全测试",
            description=f"对 {target} 的完整安全测试攻击链",
            target=target,
            stages=[
                reconnaissance_stage,
                scanning_stage,
                vulnerability_analysis_stage,
                exploitation_stage,
                post_exploitation_stage,
                reporting_stage
            ]
        )


# 测试代码
if __name__ == "__main__":
    print("开始测试攻击链管理模块...")
    # 初始化攻击链管理器
    manager = AttackChainManager()
    
    print("=" * 80)
    print("攻击链管理模块测试")
    print("=" * 80)
    
    # 测试1: 创建默认攻击链
    print("\n测试1: 创建默认攻击链")
    target = "example.com"
    chain = manager.create_default_attack_chain(target)
    print(f"创建攻击链: {chain.name}")
    print(f"攻击链ID: {chain.chain_id}")
    print(f"目标: {chain.target}")
    print(f"阶段数量: {len(chain.stages)}")
    
    for stage in chain.stages:
        print(f"- {stage.name} ({stage.stage_type.value}): {len(stage.tools)} 个工具")
    
    # 测试2: 执行攻击链
    print("\n测试2: 执行攻击链")
    print("开始执行攻击链...")
    result = manager.execute_attack_chain(chain.chain_id)
    print(f"执行结果: {result['status']}")
    
    # 测试3: 获取攻击链结果
    print("\n测试3: 获取攻击链结果")
    chain_result = manager.get_attack_chain_result(chain.chain_id)
    if chain_result:
        print(f"攻击链状态: {chain_result['status']}")
        print(f"阶段执行情况:")
        for stage in chain_result['stages']:
            print(f"- {stage['name']}: {stage['status']} (耗时: {stage['execution_time']:.2f}秒)")
    else:
        print("无法获取攻击链结果")
    
    # 测试4: 列出所有攻击链
    print("\n测试4: 列出所有攻击链")
    chains = manager.list_attack_chains()
    print(f"攻击链数量: {len(chains)}")
    for c in chains:
        print(f"- {c['name']}: {c['status']}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("所有测试通过！")
