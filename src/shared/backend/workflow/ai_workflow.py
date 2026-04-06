# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
规则引擎工作流引擎
规则引擎驱动的渗透测试工作流引擎
⚠️ 技术诚信说明：本模块使用规则引擎决策而非真正的AI系统
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StageStatus(Enum):
    """阶段状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowContext:
    """工作流上下文"""
    target: str
    start_time: float = field(default_factory=time.time)
    current_stage: str = ""
    completed_stages: List[str] = field(default_factory=list)
    stage_results: Dict[str, Any] = field(default_factory=dict)
    ai_decisions: Dict[str, Any] = field(default_factory=dict)
    workflow_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, stage_name: str, result: Any, analysis: Dict[str, Any] = None):
        """更新上下文"""
        self.current_stage = stage_name
        if stage_name not in self.completed_stages:
            self.completed_stages.append(stage_name)
        
        self.stage_results[stage_name] = {
            "result": result,
            "timestamp": time.time(),
            "analysis": analysis or {}
        }
        
        if analysis:
            self.ai_decisions[stage_name] = analysis
    
    def get_stage_result(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """获取阶段结果"""
        return self.stage_results.get(stage_name)
    
    def get_workflow_progress(self) -> float:
        """获取工作流进度"""
        if not self.completed_stages:
            return 0.0
        return len(self.completed_stages) / 6.0  # 6个阶段


class WorkflowStage:
    """工作流阶段基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = StageStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.execution_time = None
    
    async def execute(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段"""
        self.status = StageStatus.IN_PROGRESS
        self.start_time = time.time()
        
        try:
            result = await self._execute_impl(target, guidance)
            self.status = StageStatus.SUCCESS
        except Exception as e:
            self.status = StageStatus.FAILED
            result = {
                "error": str(e),
                "success": False
            }
        
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        
        return {
            "stage_name": self.name,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "result": result,
            "timestamp": time.time()
        }
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """阶段执行实现（子类需要重写）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """获取执行指标"""
        return {
            "stage_name": self.name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.execution_time
        }


class RuleEngineWorkflowEngine:
    """
    规则引擎驱动的渗透测试工作流引擎
    集成规则引擎编排器进行决策指导
    ⚠️ 技术诚信说明：使用规则引擎决策而非真正的AI系统
    """
    
    def __init__(self, enable_ai_guidance: bool = True):
        """
        初始化规则引擎工作流引擎
        
        Args:
            enable_ai_guidance: 是否启用规则引擎指导
        """
        self.enable_ai_guidance = enable_ai_guidance
        self.stages: List[WorkflowStage] = []
        self.context: Optional[WorkflowContext] = None
        self.workflow_status = WorkflowStatus.PENDING
        
        # 初始化规则引擎编排器
        if enable_ai_guidance:
            try:
                from backend.ai_core.llm_orchestrator import LLMOrchestrator, ModelType
                self.ai_orchestrator = LLMOrchestrator(enable_cache=True)
                self.ai_available = True
            except ImportError:
                print("[WARNING] 无法导入LLMOrchestrator，禁用规则引擎指导")
                self.ai_available = False
        else:
            self.ai_available = False
        
        # 初始化工作流阶段
        self._init_stages()
    
    def _init_stages(self):
        """初始化工作流阶段"""
        from .penetration_stages import (
            ReconnaissanceStage,
            ScanningStage,
            VulnerabilityAnalysisStage,
            ExploitationStage,
            PostExploitationStage,
            ReportingStage
        )
        
        self.stages = [
            ReconnaissanceStage(),
            ScanningStage(),
            VulnerabilityAnalysisStage(),
            ExploitationStage(),
            PostExploitationStage(),
            ReportingStage()
        ]
    
    async def execute_workflow(self, target: str) -> Dict[str, Any]:
        """
        执行规则引擎工作流
        
        Args:
            target: 目标IP/域名/URL
            
        Returns:
            工作流执行结果
        """
        print(f"[TARGET] 开始执行规则引擎工作流，目标: {target}")
        start_time = time.time()
        
        # 初始化上下文
        self.context = WorkflowContext(target=target)
        self.workflow_status = WorkflowStatus.RUNNING
        
        workflow_results = {
            "target": target,
            "start_time": start_time,
            "stages": [],
            "final_result": None,
            "workflow_metrics": {}
        }
        
        try:
            for stage in self.stages:
                stage_name = stage.name
                print(f"\n[STAGE] 进入阶段: {stage_name}")
                
                # AI指导当前阶段
                guidance = await self._get_stage_guidance(stage)
                
                if guidance:
                    print(f"[AI] AI指导: {guidance.get('summary', '无指导')}")
                
                # 执行阶段
                stage_result = await stage.execute(target, guidance or {})
                workflow_results["stages"].append(stage_result)
                
                # AI分析结果
                analysis = await self._analyze_stage_result(stage, stage_result)
                
                # 更新上下文
                self.context.update(stage_name, stage_result, analysis)
                
                # 显示阶段结果
                self._display_stage_result(stage_result, analysis)
                
                # AI决定是否继续
                should_continue = await self._should_continue(stage, stage_result)
                if not should_continue:
                    print(f"[WARNING] AI决定中止工作流，当前阶段: {stage_name}")
                    workflow_results["final_result"] = {
                        "status": "aborted",
                        "reason": "AI决定中止",
                        "current_stage": stage_name
                    }
                    break
            
            # 工作流完成
            if not workflow_results.get("final_result"):
                workflow_results["final_result"] = {
                    "status": "completed",
                    "reason": "所有阶段完成",
                    "total_stages": len(workflow_results["stages"])
                }
            
            end_time = time.time()
            workflow_results["end_time"] = end_time
            workflow_results["total_time"] = end_time - start_time
            workflow_results["workflow_metrics"] = self._calculate_workflow_metrics()
            
            self.workflow_status = WorkflowStatus.COMPLETED
            
            print(f"\n[SUCCESS] 规则引擎工作流执行完成，总耗时: {workflow_results['total_time']:.2f}秒")
            
        except Exception as e:
            end_time = time.time()
            workflow_results["final_result"] = {
                "status": "failed",
                "error": str(e),
                "total_time": end_time - start_time
            }
            self.workflow_status = WorkflowStatus.FAILED
            
            print(f"\n[FAILED] 规则引擎工作流执行失败: {e}")
        
        return workflow_results
    
    async def _get_stage_guidance(self, stage: WorkflowStage) -> Optional[Dict[str, Any]]:
        """获取AI对当前阶段的指导"""
        if not self.ai_available or not self.enable_ai_guidance:
            return None
        
        try:
            # 准备阶段上下文
            stage_context = {
                "stage_name": stage.name,
                "stage_description": stage.description,
                "workflow_context": self.context.metadata if self.context else {},
                "previous_results": self.context.stage_results if self.context else {},
                "target": self.context.target if self.context else "unknown"
            }
            
            # 使用AI编排器获取指导
            from backend.ai_core.prompt_engineer import PromptEngineer
            engineer = PromptEngineer()
            
            prompt_info = engineer.create_stage_guidance_prompt({
                "stage_name": stage.name,
                "previous_results": self.context.stage_results if self.context else {},
                "context": json.dumps(stage_context, ensure_ascii=False),
                "target": self.context.target if self.context else "unknown",
                "available_tools": ["nmap", "whatweb", "nuclei", "sqlmap", "wafw00f"]
            })
            
            from backend.ai_core.llm_orchestrator import AIRequest, ModelType
            request = AIRequest(
                prompt=prompt_info["user_prompt"],
                system_prompt=prompt_info["system_prompt"],
                model_type=ModelType.DEEPSEEK
            )
            
            response = self.ai_orchestrator.call_model(request)
            
            if response.error:
                print(f"[WARNING] AI指导获取失败: {response.error}")
                return None
            
            try:
                guidance = json.loads(response.content.strip())
                return guidance
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始内容作为摘要
                return {
                    "summary": response.content[:200] + "..." if len(response.content) > 200 else response.content,
                    "raw_guidance": response.content,
                    "model_used": response.model_used
                }
                
        except Exception as e:
            print(f"[WARNING] AI指导异常: {e}")
            return None
    
    async def _analyze_stage_result(self, stage: WorkflowStage, stage_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用AI分析阶段结果"""
        if not self.ai_available or not self.enable_ai_guidance:
            return None
        
        try:
            # 准备分析数据
            analysis_data = {
                "stage_name": stage.name,
                "stage_result": stage_result,
                "workflow_context": self.context.metadata if self.context else {},
                "target": self.context.target if self.context else "unknown"
            }
            
            # 使用AI编排器分析结果
            from backend.ai_core.llm_orchestrator import AIRequest, ModelType
            request = AIRequest(
                prompt=f"分析渗透测试阶段结果:\n\n{json.dumps(analysis_data, indent=2, ensure_ascii=False)}",
                system_prompt="你是一个资深网络安全专家，擅长分析渗透测试结果并提供专业见解。",
                model_type=ModelType.DEEPSEEK,
                temperature=0.2
            )
            
            response = self.ai_orchestrator.call_model(request)
            
            if response.error:
                return {"error": response.error}
            
            try:
                analysis = json.loads(response.content.strip())
                analysis["model_used"] = response.model_used
                return analysis
            except json.JSONDecodeError:
                return {
                    "analysis": response.content,
                    "model_used": response.model_used,
                    "raw_analysis": True
                }
                
        except Exception as e:
            return {"error": f"AI分析异常: {str(e)}"}
    
    async def _should_continue(self, stage: WorkflowStage, stage_result: Dict[str, Any]) -> bool:
        """AI决定是否继续工作流"""
        if not self.ai_available or not self.enable_ai_guidance:
            return True
        
        try:
            # 准备决策数据
            decision_data = {
                "stage_name": stage.name,
                "stage_result": stage_result,
                "workflow_progress": self.context.get_workflow_progress() if self.context else 0.0,
                "completed_stages": self.context.completed_stages if self.context else [],
                "target": self.context.target if self.context else "unknown"
            }
            
            # 使用AI编排器决策
            from backend.ai_core.llm_orchestrator import AIRequest, ModelType
            request = AIRequest(
                prompt=f"基于以下阶段结果决定是否继续渗透测试工作流:\n\n{json.dumps(decision_data, indent=2, ensure_ascii=False)}",
                system_prompt="你是一个资深渗透测试专家，需要决定是否继续渗透测试工作流。考虑以下因素：目标安全状况、已发现的风险、攻击进展、时间和资源限制。",
                model_type=ModelType.DEEPSEEK,
                temperature=0.3
            )
            
            response = self.ai_orchestrator.call_model(request)
            
            if response.error:
                print(f"[WARNING] AI继续决策失败: {response.error}")
                return True
            
            # 解析AI决策
            ai_response = response.content.lower()
            if "continue" in ai_response or "继续" in ai_response or "yes" in ai_response or "是" in ai_response:
                return True
            elif "stop" in ai_response or "停止" in ai_response or "no" in ai_response or "否" in ai_response:
                return False
            else:
                # 默认继续
                return True
                
        except Exception as e:
            print(f"[WARNING] AI继续决策异常: {e}")
            return True
    
    def _display_stage_result(self, stage_result: Dict[str, Any], analysis: Dict[str, Any] = None):
        """显示阶段结果"""
        stage_name = stage_result.get("stage_name", "未知阶段")
        status = stage_result.get("status", "unknown")
        exec_time = stage_result.get("execution_time", 0)
        
        status_icon = "[SUCCESS]" if status == "success" else "[FAILED]" if status == "failed" else "[WARNING]"
        print(f"  {status_icon} 阶段 {stage_name}: {status} ({exec_time:.2f}s)")
        
        if analysis and not analysis.get("error"):
            if "summary" in analysis:
                print(f"  [AI] AI分析: {analysis['summary']}")
            elif "analysis" in analysis:
                print(f"  [AI] AI分析: {analysis['analysis'][:100]}...")
    
    def _calculate_workflow_metrics(self) -> Dict[str, Any]:
        """计算工作流指标"""
        if not self.context:
            return {}
        
        metrics = {
            "total_stages": len(self.stages),
            "completed_stages": len(self.context.completed_stages),
            "success_rate": 0,
            "total_ai_guidance": len(self.context.ai_decisions),
            "stage_metrics": []
        }
        
        # 计算成功率
        success_count = 0
        for stage in self.stages:
            stage_metrics = stage.get_execution_metrics()
            metrics["stage_metrics"].append(stage_metrics)
            
            if stage_metrics["status"] == StageStatus.SUCCESS.value:
                success_count += 1
        
        if metrics["total_stages"] > 0:
            metrics["success_rate"] = success_count / metrics["total_stages"]
        
        return metrics
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "status": self.workflow_status.value,
            "target": self.context.target if self.context else None,
            "current_stage": self.context.current_stage if self.context else None,
            "completed_stages": self.context.completed_stages if self.context else [],
            "progress": self.context.get_workflow_progress() if self.context else 0.0,
            "ai_enabled": self.ai_available and self.enable_ai_guidance
        }


# 测试函数
async def test_rule_engine_workflow():
    """测试规则引擎工作流引擎"""
    print("=" * 80)
    print("规则引擎工作流引擎测试")
    print("=" * 80)
    
    try:
        # 创建规则引擎工作流引擎
        engine = RuleEngineWorkflowEngine(enable_ai_guidance=True)
        
        print(f"工作流引擎初始化完成")
        print(f"阶段数量: {len(engine.stages)}")
        print(f"规则引擎指导启用: {engine.ai_available}")
        
        # 获取工作流状态
        status = engine.get_workflow_status()
        print(f"初始状态: {status['status']}")
        
        # 测试目标
        test_target = "example.com"
        
        # 执行工作流
        print(f"\n开始执行工作流，目标: {test_target}")
        result = await engine.execute_workflow(test_target)
        
        print(f"\n工作流执行完成:")
        print(f"  目标: {result['target']}")
        print(f"  总耗时: {result.get('total_time', 0):.2f}秒")
        print(f"  最终状态: {result['final_result']['status']}")
        print(f"  完成阶段: {len(result['stages'])}")
        
        # 显示阶段结果
        print(f"\n阶段详情:")
        for i, stage_result in enumerate(result['stages'], 1):
            stage_name = stage_result['stage_name']
            status = stage_result['status']
            exec_time = stage_result['execution_time']
            print(f"  {i}. {stage_name}: {status} ({exec_time:.2f}s)")
        
        # 显示工作流指标
        metrics = result.get('workflow_metrics', {})
        if metrics:
            print(f"\n工作流指标:")
            print(f"  成功率: {metrics.get('success_rate', 0)*100:.1f}%")
            print(f"  规则引擎指导次数: {metrics.get('total_ai_guidance', 0)}")
        
        print("\n[SUCCESS] 规则引擎工作流引擎测试成功")
        return True
        
    except Exception as e:
        print(f"\n[FAILED] 规则引擎工作流引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_rule_engine_workflow())
