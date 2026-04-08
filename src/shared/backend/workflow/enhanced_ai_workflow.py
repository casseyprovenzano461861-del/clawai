# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
增强AI工作流引擎
基于真实大模型的安全测试工作流引擎
"""

import asyncio
import time
import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from ai_engine.llm_agent.pentest_agent import ClawAIPentestAgent
from ai_engine.llm_agent.config_manager import LLMConfigManager
from shared.backend.ai_core.enhanced_decision_engine import EnhancedDecisionEngine


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


class ReconnaissanceStage(WorkflowStage):
    """侦察阶段"""
    
    def __init__(self):
        super().__init__("reconnaissance", "信息收集和目标侦察")
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行侦察阶段"""
        # 这里实现实际的侦察逻辑
        # 例如使用nmap进行端口扫描
        return {
            "target": target,
            "status": "completed",
            "discovery": {
                "open_ports": [80, 443, 22],
                "services": {
                    "80": "http",
                    "443": "https",
                    "22": "ssh"
                }
            }
        }


class ScanningStage(WorkflowStage):
    """扫描阶段"""
    
    def __init__(self):
        super().__init__("scanning", "漏洞扫描和安全评估")
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行扫描阶段"""
        # 这里实现实际的扫描逻辑
        # 例如使用nuclei进行漏洞扫描
        return {
            "target": target,
            "status": "completed",
            "vulnerabilities": [
                {
                    "name": "XSS",
                    "severity": "medium",
                    "description": "跨站脚本漏洞"
                },
                {
                    "name": "SQLi",
                    "severity": "high",
                    "description": "SQL注入漏洞"
                }
            ]
        }


class VulnerabilityAnalysisStage(WorkflowStage):
    """漏洞分析阶段"""
    
    def __init__(self):
        super().__init__("vulnerability_analysis", "漏洞分析和风险评估")
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行漏洞分析阶段"""
        # 这里实现实际的漏洞分析逻辑
        return {
            "target": target,
            "status": "completed",
            "risk_assessment": {
                "high_risk": 1,
                "medium_risk": 2,
                "low_risk": 3,
                "total_risk_score": 75
            }
        }


class ExploitationStage(WorkflowStage):
    """漏洞利用阶段"""
    
    def __init__(self):
        super().__init__("exploitation", "漏洞利用和权限提升")
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行漏洞利用阶段"""
        # 这里实现实际的漏洞利用逻辑
        return {
            "target": target,
            "status": "completed",
            "exploits": [
                {
                    "vulnerability": "SQLi",
                    "status": "success",
                    "access_gained": "database"
                }
            ]
        }


class PostExploitationStage(WorkflowStage):
    """后渗透阶段"""
    
    def __init__(self):
        super().__init__("post_exploitation", "后渗透和横向移动")
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行后渗透阶段"""
        # 这里实现实际的后渗透逻辑
        return {
            "target": target,
            "status": "completed",
            "post_exploitation": {
                "data_exfiltrated": True,
                "lateral_movement": False,
                "persistence": True
            }
        }


class ReportingStage(WorkflowStage):
    """报告阶段"""
    
    def __init__(self):
        super().__init__("reporting", "安全报告生成")
    
    async def _execute_impl(self, target: str, guidance: Dict[str, Any]) -> Dict[str, Any]:
        """执行报告阶段"""
        # 这里实现实际的报告生成逻辑
        return {
            "target": target,
            "status": "completed",
            "report": {
                "generated": True,
                "vulnerabilities_count": 3,
                "risk_score": 75
            }
        }


class EnhancedAIWorkflowEngine:
    """
    增强AI工作流引擎
    基于真实大模型的安全测试工作流引擎
    """
    
    def __init__(self, enable_ai_guidance: bool = True):
        """
        初始化增强AI工作流引擎
        
        Args:
            enable_ai_guidance: 是否启用AI指导
        """
        self.enable_ai_guidance = enable_ai_guidance
        self.stages: List[WorkflowStage] = []
        self.context: Optional[WorkflowContext] = None
        self.workflow_status = WorkflowStatus.PENDING
        
        # 初始化LLM代理
        self.llm_config_manager = LLMConfigManager()
        self.llm_agent = None
        self._initialize_llm_agent()
        
        # 初始化增强决策引擎
        self.decision_engine = None
        self._initialize_decision_engine()
        
        # 初始化工作流阶段
        self._init_stages()
    
    def _initialize_llm_agent(self):
        """初始化LLM代理"""
        try:
            config = self.llm_config_manager.load_config("hacksynth_enhanced")
            self.llm_agent = ClawAIPentestAgent(
                config=config,
                tool_executor_url="http://localhost:8082",
                skill_registry=None
            )
            print(f"[INFO] LLM代理初始化成功: {self.llm_agent.model_id}")
        except Exception as e:
            print(f"[WARNING] LLM代理初始化失败: {e}")
            self.llm_agent = None
    
    def _initialize_decision_engine(self):
        """初始化增强决策引擎"""
        try:
            # 创建简单的上下文管理器和策略库
            class SimpleContextManager:
                def analyze(self, scan_data, user_context):
                    from shared.backend.ai_core.enhanced_decision_engine import ContextAnalysis
                    return ContextAnalysis(
                        target_type="Web",
                        tech_stack=["nginx", "PHP", "WordPress"],
                        defense_measures=["WAF"],
                        environment_constraints={"network": "external"},
                        compliance_requirements=[],
                        time_constraints={"strict": False},
                        risk_tolerance="medium"
                    )
            
            class SimpleStrategyRepository:
                from shared.backend.ai_core.enhanced_decision_engine import StrategyType
                def select_strategy(self, context_analysis):
                    return StrategyType.OFFENSIVE
            
            context_manager = SimpleContextManager()
            strategy_repo = SimpleStrategyRepository()
            self.decision_engine = EnhancedDecisionEngine(context_manager, strategy_repo)
            print("[INFO] 增强决策引擎初始化成功")
        except Exception as e:
            print(f"[WARNING] 增强决策引擎初始化失败: {e}")
            self.decision_engine = None
    
    def _init_stages(self):
        """初始化工作流阶段"""
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
        执行增强AI工作流
        
        Args:
            target: 目标IP/域名/URL
            
        Returns:
            工作流执行结果
        """
        print(f"[TARGET] 开始执行增强AI工作流，目标: {target}")
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
            
            print(f"\n[SUCCESS] 增强AI工作流执行完成，总耗时: {workflow_results['total_time']:.2f}秒")
            
        except Exception as e:
            end_time = time.time()
            workflow_results["final_result"] = {
                "status": "failed",
                "error": str(e),
                "total_time": end_time - start_time
            }
            self.workflow_status = WorkflowStatus.FAILED
            
            print(f"\n[FAILED] 增强AI工作流执行失败: {e}")
        
        return workflow_results
    
    async def _get_stage_guidance(self, stage: WorkflowStage) -> Optional[Dict[str, Any]]:
        """获取AI对当前阶段的指导"""
        if not self.llm_agent or not self.enable_ai_guidance:
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
            
            # 使用LLM生成指导
            analysis_prompt = f"""作为安全渗透测试专家，为以下阶段提供专业指导：

阶段信息：
- 阶段名称: {stage.name}
- 阶段描述: {stage.description}
- 目标: {self.context.target if self.context else "unknown"}
- 之前的结果: {json.dumps(self.context.stage_results, ensure_ascii=False) if self.context else "无"}

请提供：
1. 该阶段的关键目标和重点
2. 推荐使用的工具和技术
3. 可能的风险和注意事项
4. 预期的输出和结果
5. 与下一阶段的衔接建议

分析结果应该专业、详细，基于实际的安全测试经验。"""
            
            # 调用LLM生成分析
            messages = [
                {"role": "system", "content": "你是一个专业的安全渗透测试专家，具有丰富的安全测试经验和专业知识。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            llm_output, input_tokens, output_tokens = self.llm_agent.generate_text(messages)
            
            # 解析LLM输出
            guidance = {
                "summary": llm_output[:200] + "..." if len(llm_output) > 200 else llm_output,
                "raw_guidance": llm_output,
                "token_usage": {
                    "input": input_tokens,
                    "output": output_tokens
                }
            }
            
            return guidance
            
        except Exception as e:
            print(f"[WARNING] AI指导异常: {e}")
            return None
    
    async def _analyze_stage_result(self, stage: WorkflowStage, stage_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用AI分析阶段结果"""
        if not self.llm_agent or not self.enable_ai_guidance:
            return None
        
        try:
            # 准备分析数据
            analysis_data = {
                "stage_name": stage.name,
                "stage_result": stage_result,
                "workflow_context": self.context.metadata if self.context else {},
                "target": self.context.target if self.context else "unknown"
            }
            
            # 使用LLM分析结果
            analysis_prompt = f"""作为安全渗透测试专家，分析以下阶段结果：

{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

请提供：
1. 阶段执行的评估
2. 发现的关键问题和漏洞
3. 风险评估
4. 对下一阶段的建议
5. 整体安全态势分析

分析结果应该专业、详细，基于实际的安全测试经验。"""
            
            # 调用LLM生成分析
            messages = [
                {"role": "system", "content": "你是一个专业的安全渗透测试专家，具有丰富的安全测试经验和专业知识。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            llm_output, input_tokens, output_tokens = self.llm_agent.generate_text(messages)
            
            # 解析LLM输出
            analysis = {
                "analysis": llm_output,
                "token_usage": {
                    "input": input_tokens,
                    "output": output_tokens
                }
            }
            
            return analysis
            
        except Exception as e:
            print(f"[WARNING] AI分析异常: {e}")
            return None
    
    async def _should_continue(self, stage: WorkflowStage, stage_result: Dict[str, Any]) -> bool:
        """AI决定是否继续工作流"""
        if not self.llm_agent or not self.enable_ai_guidance:
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
            
            # 使用LLM进行决策
            decision_prompt = f"""作为安全渗透测试专家，基于以下阶段结果决定是否继续工作流：

{json.dumps(decision_data, indent=2, ensure_ascii=False)}

请考虑以下因素：
1. 目标安全状况
2. 已发现的风险
3. 攻击进展
4. 时间和资源限制
5. 测试目标的达成情况

请明确回答是否继续，并提供简要理由。"""
            
            # 调用LLM生成决策
            messages = [
                {"role": "system", "content": "你是一个专业的安全渗透测试专家，需要决定是否继续渗透测试工作流。"},
                {"role": "user", "content": decision_prompt}
            ]
            
            llm_output, _, _ = self.llm_agent.generate_text(messages)
            
            # 解析AI决策
            ai_response = llm_output.lower()
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
            "ai_enabled": self.llm_agent is not None and self.enable_ai_guidance
        }


# 测试函数
async def test_enhanced_ai_workflow():
    """测试增强AI工作流引擎"""
    print("=" * 80)
    print("增强AI工作流引擎测试")
    print("=" * 80)
    
    try:
        # 创建增强AI工作流引擎
        engine = EnhancedAIWorkflowEngine(enable_ai_guidance=True)
        
        print(f"工作流引擎初始化完成")
        print(f"阶段数量: {len(engine.stages)}")
        print(f"AI指导启用: {engine.llm_agent is not None}")
        
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
            print(f"  AI指导次数: {metrics.get('total_ai_guidance', 0)}")
        
        print("\n[SUCCESS] 增强AI工作流引擎测试成功")
        return True
        
    except Exception as e:
        print(f"\n[FAILED] 增强AI工作流引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_enhanced_ai_workflow())
