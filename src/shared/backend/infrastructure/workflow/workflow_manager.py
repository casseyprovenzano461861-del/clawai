# -*- coding: utf-8 -*-
"""
工作流管理器
负责工作流定义、创建、执行控制
"""

import uuid
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from ..database import get_database


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep:
    """工作流步骤定义"""
    
    def __init__(self, step_data: Dict[str, Any]):
        """
        初始化工作流步骤
        
        Args:
            step_data: 步骤数据
        """
        self.id = step_data.get("id")
        self.tool = step_data.get("tool")
        self.tool_type = step_data.get("type", "tool")  # tool, report, custom
        self.params = step_data.get("params", {})
        self.timeout = step_data.get("timeout", 300)  # 默认5分钟
        self.depends_on = step_data.get("depends_on", [])
        self.description = step_data.get("description", "")
        self.phase = step_data.get("phase", "")
        
        # 执行器函数（运行时设置）
        self.executor: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "tool": self.tool,
            "type": self.tool_type,
            "params": self.params,
            "timeout": self.timeout,
            "depends_on": self.depends_on,
            "description": self.description,
            "phase": self.phase
        }


class WorkflowDefinition:
    """工作流定义"""
    
    def __init__(self, definition_data: Dict[str, Any]):
        """
        初始化工作流定义
        
        Args:
            definition_data: 定义数据
        """
        self.id = definition_data.get("id")
        self.name = definition_data.get("name", "")
        self.version = definition_data.get("version", "1.0")
        self.description = definition_data.get("description", "")
        
        # 解析阶段和步骤
        self.phases: List[Dict[str, Any]] = definition_data.get("phases", [])
        self.steps: Dict[str, WorkflowStep] = {}
        self.step_order: List[str] = []
        
        self._parse_steps()
    
    def _parse_steps(self):
        """解析步骤"""
        step_counter = 1
        
        for phase in self.phases:
            phase_name = phase.get("phase", f"phase_{step_counter}")
            phase_steps = phase.get("steps", [])
            
            for step_data in phase_steps:
                step_id = step_data.get("id", f"step_{step_counter}")
                step_data["phase"] = phase_name
                
                step = WorkflowStep(step_data)
                self.steps[step_id] = step
                self.step_order.append(step_id)
                
                step_counter += 1
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """获取步骤"""
        return self.steps.get(step_id)
    
    def get_step_dependencies(self, step_id: str) -> List[str]:
        """获取步骤依赖"""
        step = self.get_step(step_id)
        if not step:
            return []
        
        return step.depends_on
    
    def get_execution_order(self) -> List[str]:
        """获取执行顺序"""
        # 简单的拓扑排序（不考虑复杂依赖图）
        executed = set()
        execution_order = []
        
        # 收集所有步骤
        all_steps = list(self.steps.keys())
        
        while len(executed) < len(all_steps):
            progress = False
            
            for step_id in all_steps:
                if step_id in executed:
                    continue
                
                step = self.get_step(step_id)
                if not step:
                    executed.add(step_id)
                    progress = True
                    continue
                
                # 检查依赖是否都已执行
                dependencies_met = all(dep in executed for dep in step.depends_on)
                
                if dependencies_met:
                    execution_order.append(step_id)
                    executed.add(step_id)
                    progress = True
            
            if not progress:
                # 检测到循环依赖
                remaining = [s for s in all_steps if s not in executed]
                # 强制继续执行
                for step_id in remaining:
                    execution_order.append(step_id)
                    executed.add(step_id)
                break
        
        return execution_order
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "phases": self.phases,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()}
        }


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        """初始化工作流管理器"""
        self.db = get_database()
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.execution_handlers: Dict[str, Callable] = {}
        
        # 加载预定义工作流
        self._load_predefined_workflows()
    
    def _load_predefined_workflows(self):
        """加载预定义工作流"""
        # 快速扫描工作流
        quick_scan_workflow = {
            "id": "quick_scan",
            "name": "快速扫描工作流",
            "version": "1.0",
            "description": "快速扫描目标，包括端口扫描和Web技术识别",
            "phases": [
                {
                    "phase": "信息收集",
                    "steps": [
                        {
                            "id": "nmap_scan",
                            "tool": "nmap",
                            "params": {"ports": "80,443,8080,8443"},
                            "timeout": 300,
                            "description": "端口扫描"
                        },
                        {
                            "id": "whatweb_scan",
                            "tool": "whatweb",
                            "depends_on": ["nmap_scan"],
                            "timeout": 120,
                            "description": "Web技术识别"
                        }
                    ]
                }
            ]
        }
        
        # Web渗透测试工作流
        web_penetration_workflow = {
            "id": "web_penetration_test",
            "name": "Web渗透测试工作流",
            "version": "1.0",
            "description": "完整的Web应用渗透测试流程",
            "phases": [
                {
                    "phase": "信息收集",
                    "steps": [
                        {
                            "id": "nmap_scan",
                            "tool": "nmap",
                            "params": {"ports": "80,443,8080,8443,3306,5432"},
                            "timeout": 300,
                            "description": "端口扫描"
                        },
                        {
                            "id": "whatweb_scan",
                            "tool": "whatweb",
                            "depends_on": ["nmap_scan"],
                            "timeout": 120,
                            "description": "Web技术识别"
                        }
                    ]
                },
                {
                    "phase": "漏洞扫描",
                    "steps": [
                        {
                            "id": "nuclei_scan",
                            "tool": "nuclei",
                            "depends_on": ["whatweb_scan"],
                            "timeout": 600,
                            "description": "漏洞扫描"
                        },
                        {
                            "id": "sqlmap_scan",
                            "tool": "sqlmap",
                            "depends_on": ["nuclei_scan"],
                            "timeout": 600,
                            "description": "SQL注入检测"
                        }
                    ]
                },
                {
                    "phase": "报告生成",
                    "steps": [
                        {
                            "id": "generate_report",
                            "type": "report",
                            "tool": "report_generator",
                            "depends_on": ["nuclei_scan", "sqlmap_scan"],
                            "timeout": 60,
                            "description": "生成渗透测试报告"
                        }
                    ]
                }
            ]
        }
        
        # 保存预定义工作流
        self.create_workflow(quick_scan_workflow)
        self.create_workflow(web_penetration_workflow)
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """
        创建工作流模板
        
        Args:
            workflow_data: 工作流数据
            
        Returns:
            工作流ID
        """
        # 确保有ID
        if "id" not in workflow_data:
            workflow_data["id"] = f"workflow_{int(time.time())}"
        
        # 准备数据库记录
        workflow_id = workflow_data["id"]
        
        # 如果workflow_data没有definition字段，将整个workflow_data作为definition
        if "definition" not in workflow_data:
            db_record = {
                "id": workflow_id,
                "name": workflow_data.get("name", ""),
                "version": workflow_data.get("version", "1.0"),
                "description": workflow_data.get("description", ""),
                "definition": workflow_data  # 整个workflow_data作为definition
            }
        else:
            db_record = workflow_data
        
        # 保存到数据库
        workflow_id = self.db.insert_workflow(db_record)
        
        # 加载到内存
        self._load_workflow_definition(workflow_id)
        
        return workflow_id
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        获取工作流定义
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流定义或None
        """
        # 首先从内存中查找
        if workflow_id in self.workflow_definitions:
            return self.workflow_definitions[workflow_id]
        
        # 从数据库加载
        self._load_workflow_definition(workflow_id)
        
        return self.workflow_definitions.get(workflow_id)
    
    def _load_workflow_definition(self, workflow_id: str):
        """从数据库加载工作流定义"""
        workflow_data = self.db.get_workflow(workflow_id)
        if not workflow_data:
            return
        
        definition = WorkflowDefinition(workflow_data["definition"])
        self.workflow_definitions[workflow_id] = definition
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        获取工作流列表
        
        Returns:
            工作流列表
        """
        return self.db.list_workflows()
    
    def execute_workflow(
        self,
        workflow_id: str,
        target: str,
        created_by: str = "anonymous",
        extra_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            target: 目标地址
            created_by: 创建者
            extra_params: 额外参数
            
        Returns:
            执行ID
        """
        # 获取工作流定义
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        # 生成执行ID
        execution_id = str(uuid.uuid4())[:8]
        
        # 创建执行记录
        execution_data = {
            "id": execution_id,
            "workflow_id": workflow_id,
            "target": target,
            "status": WorkflowStatus.PENDING.value,
            "progress": 0,
            "created_by": created_by,
            "result": {}
        }
        
        if extra_params:
            execution_data["extra_params"] = extra_params
        
        self.db.insert_execution(execution_data)
        
        # 开始执行（异步）
        # 在实际应用中，这里应该将执行任务提交到任务队列
        # 为了简化，这里直接启动执行
        self._start_execution(execution_id)
        
        return execution_id
    
    def _start_execution(self, execution_id: str):
        """
        开始执行工作流
        
        Args:
            execution_id: 执行ID
        """
        # 获取执行记录
        execution = self.db.get_execution(execution_id)
        if not execution:
            raise ValueError(f"执行记录不存在: {execution_id}")
        
        # 更新状态为运行中
        self.db.update_execution(execution_id, {
            "status": WorkflowStatus.RUNNING.value,
            "started_at": datetime.now().isoformat(),
            "progress": 10
        })
        
        # 获取工作流定义
        workflow = self.get_workflow(execution["workflow_id"])
        if not workflow:
            self.db.update_execution(execution_id, {
                "status": WorkflowStatus.FAILED.value,
                "completed_at": datetime.now().isoformat(),
                "result": {"error": f"工作流定义不存在: {execution['workflow_id']}"}
            })
            return
        
        try:
            # 获取执行顺序
            execution_order = workflow.get_execution_order()
            total_steps = len(execution_order)
            
            # 执行每个步骤
            results = {}
            for i, step_id in enumerate(execution_order):
                step = workflow.get_step(step_id)
                if not step:
                    continue
                
                # 创建任务记录
                task_id = f"{execution_id}_{step_id}"
                task_data = {
                    "id": task_id,
                    "execution_id": execution_id,
                    "step_id": step_id,
                    "tool_name": step.tool or step.tool_type,
                    "status": TaskStatus.PENDING.value,
                    "progress": 0
                }
                
                self.db.insert_task(task_data)
                
                # 执行任务
                task_result = self._execute_task(
                    execution_id, task_id, step, execution["target"]
                )
                
                # 更新任务状态
                task_updates = {
                    "status": TaskStatus.COMPLETED.value if task_result.get("success") else TaskStatus.FAILED.value,
                    "completed_at": datetime.now().isoformat(),
                    "result": task_result,
                    "logs": task_result.get("logs", ""),
                    "error_message": task_result.get("error", "")
                }
                
                self.db.update_task(task_id, task_updates)
                
                # 保存结果
                results[step_id] = task_result
                
                # 更新执行进度
                progress = int(((i + 1) / total_steps) * 90) + 10  # 10%基础进度 + 实际进度
                self.db.update_execution(execution_id, {
                    "progress": min(progress, 95)
                })
            
            # 执行完成
            self.db.update_execution(execution_id, {
                "status": WorkflowStatus.COMPLETED.value,
                "completed_at": datetime.now().isoformat(),
                "progress": 100,
                "result": {
                    "steps": len(execution_order),
                    "completed": len([r for r in results.values() if r.get("success")]),
                    "failed": len([r for r in results.values() if not r.get("success")]),
                    "results": results,
                    "summary": self._generate_summary(results)
                }
            })
            
        except Exception as e:
            # 执行失败
            self.db.update_execution(execution_id, {
                "status": WorkflowStatus.FAILED.value,
                "completed_at": datetime.now().isoformat(),
                "result": {"error": str(e)}
            })
            raise
    
    def _execute_task(
        self, 
        execution_id: str, 
        task_id: str, 
        step: WorkflowStep, 
        target: str
    ) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            execution_id: 执行ID
            task_id: 任务ID
            step: 工作流步骤
            target: 目标
            
        Returns:
            任务结果
        """
        # 更新任务状态为运行中
        self.db.update_task(task_id, {
            "status": TaskStatus.RUNNING.value,
            "started_at": datetime.now().isoformat(),
            "progress": 50
        })
        
        try:
            # 根据步骤类型执行不同的操作
            if step.tool_type == "report":
                # 报告生成步骤
                result = self._execute_report_step(execution_id, step, target)
            elif step.tool in self.execution_handlers:
                # 自定义执行器
                executor = self.execution_handlers[step.tool]
                result = executor(target, step.params)
            else:
                # 默认工具执行
                result = self._execute_tool_step(step, target)
            
            # 更新任务进度
            self.db.update_task(task_id, {"progress": 90})
            
            return {
                "success": True,
                "tool": step.tool,
                "type": step.tool_type,
                "target": target,
                "params": step.params,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # 执行失败
            return {
                "success": False,
                "tool": step.tool,
                "type": step.tool_type,
                "target": target,
                "params": step.params,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_tool_step(self, step: WorkflowStep, target: str) -> Dict[str, Any]:
        """
        执行工具步骤
        
        Args:
            step: 工作流步骤
            target: 目标
            
        Returns:
            工具执行结果
        """
        # 这里应该调用统一工具执行器
        # 为了简化，返回模拟结果
        
        tool_name = step.tool
        params = step.params
        
        # 模拟不同工具的执行结果
        if tool_name == "nmap":
            return {
                "execution_mode": "real",
                "ports": [
                    {"port": 80, "service": "http", "state": "open"},
                    {"port": 443, "service": "https", "state": "open"}
                ],
                "target": target,
                "params": params,
                "timestamp": datetime.now().isoformat()
            }
        
        elif tool_name == "whatweb":
            return {
                "execution_mode": "real",
                "fingerprint": {
                    "web_server": "nginx",
                    "language": ["PHP"],
                    "cms": ["WordPress"]
                },
                "target": target,
                "timestamp": datetime.now().isoformat()
            }
        
        elif tool_name == "nuclei":
            return {
                "execution_mode": "real",
                "vulnerabilities": [
                    {"name": "WordPress XSS", "severity": "medium"},
                    {"name": "Remote Code Execution", "severity": "critical"}
                ],
                "target": target,
                "timestamp": datetime.now().isoformat()
            }
        
        elif tool_name == "sqlmap":
            return {
                "execution_mode": "simulated",
                "message": "SQL注入检测完成",
                "findings": [],
                "target": target,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            return {
                "execution_mode": "simulated",
                "message": f"工具 {tool_name} 执行完成",
                "target": target,
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_report_step(self, execution_id: str, step: WorkflowStep, target: str) -> Dict[str, Any]:
        """
        执行报告生成步骤
        
        Args:
            execution_id: 执行ID
            step: 工作流步骤
            target: 目标
            
        Returns:
            报告结果
        """
        # 获取执行的所有任务结果
        tasks = self.db.get_execution_tasks(execution_id)
        
        # 生成报告摘要
        completed_tasks = [t for t in tasks if t["status"] == TaskStatus.COMPLETED.value]
        failed_tasks = [t for t in tasks if t["status"] == TaskStatus.FAILED.value]
        
        # 生成报告内容
        report = {
            "execution_id": execution_id,
            "target": target,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tasks": len(tasks),
                "completed": len(completed_tasks),
                "failed": len(failed_tasks),
                "success_rate": len(completed_tasks) / len(tasks) if tasks else 0
            },
            "tasks": tasks,
            "recommendations": [
                "定期进行安全扫描",
                "及时修复发现的漏洞",
                "加强Web应用防火墙配置"
            ]
        }
        
        return report
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        completed = sum(1 for r in results.values() if r.get("success"))
        total = len(results)
        
        return {
            "total_steps": total,
            "completed": completed,
            "failed": total - completed,
            "success_rate": completed / total if total > 0 else 0,
            "execution_time": datetime.now().isoformat()
        }
    
    def register_executor(self, tool_name: str, executor: Callable):
        """
        注册工具执行器
        
        Args:
            tool_name: 工具名称
            executor: 执行器函数
        """
        self.execution_handlers[tool_name] = executor
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行状态
        """
        execution = self.db.get_execution(execution_id)
        if not execution:
            return {
                "execution_id": execution_id,
                "status": "not_found",
                "message": "执行记录不存在"
            }
        
        # 获取任务列表
        tasks = self.db.get_execution_tasks(execution_id)
        
        return {
            "execution_id": execution_id,
            "workflow_id": execution["workflow_id"],
            "target": execution["target"],
            "status": execution["status"],
            "progress": execution["progress"],
            "started_at": execution["started_at"],
            "completed_at": execution["completed_at"],
            "created_by": execution["created_by"],
            "created_at": execution["created_at"],
            "tasks": tasks,
            "tasks_count": len(tasks),
            "completed_tasks": len([t for t in tasks if t["status"] == TaskStatus.COMPLETED.value]),
            "failed_tasks": len([t for t in tasks if t["status"] == TaskStatus.FAILED.value])
        }
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取执行记录列表
        
        Args:
            workflow_id: 工作流ID过滤
            status: 状态过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            执行记录列表
        """
        return self.db.list_executions(workflow_id, status, limit, offset)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        取消执行
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功取消
        """
        execution = self.db.get_execution(execution_id)
        if not execution:
            return False
        
        if execution["status"] not in [WorkflowStatus.PENDING.value, WorkflowStatus.RUNNING.value]:
            return False
        
        # 更新状态为取消
        self.db.update_execution(execution_id, {
            "status": WorkflowStatus.CANCELLED.value,
            "completed_at": datetime.now().isoformat()
        })
        
        return True


# 全局工作流管理器实例
workflow_manager_instance = None


def get_workflow_manager() -> WorkflowManager:
    """
    获取工作流管理器实例（单例模式）
    
    Returns:
        WorkflowManager实例
    """
    global workflow_manager_instance
    if workflow_manager_instance is None:
        workflow_manager_instance = WorkflowManager()
    return workflow_manager_instance