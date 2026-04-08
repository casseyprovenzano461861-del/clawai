# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能编排系统 - 第5天任务：智能编排与执行优化
支持任务分解、并行执行、资源管理和智能调度
"""

import os
import sys
import json
import time
import asyncio
import threading
from typing import Dict, List, Any, Optional, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import traceback
from datetime import datetime
import uuid

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.config import get_settings

# 获取配置实例
config = get_settings()


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 取消


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    TOOL_LICENSE = "tool_license"  # 工具许可证
    API_QUOTA = "api_quota"        # API配额


@dataclass
class TaskResource:
    """任务资源需求"""
    cpu_cores: int = 1
    memory_mb: int = 100
    network_bandwidth: int = 0  # 0表示无特殊要求
    required_tools: List[str] = field(default_factory=list)
    api_quota_required: int = 0


@dataclass
class ExecutionTask:
    """执行任务"""
    task_id: str
    task_type: str
    parameters: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    timeout_seconds: int = 300
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    resources: TaskResource = field(default_factory=TaskResource)
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """使ExecutionTask可比较，用于优先级队列"""
        # 按优先级比较，如果优先级相同则按任务ID比较
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.task_id < other.task_id
    
    def __eq__(self, other):
        """比较两个任务是否相等"""
        return self.task_id == other.task_id
    
    def __hash__(self):
        """使任务可哈希"""
        return hash(self.task_id)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    resource_used: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SystemResource:
    """系统资源状态"""
    total_cpu_cores: int = os.cpu_count() or 4
    available_cpu_cores: int = os.cpu_count() or 4
    total_memory_mb: int = 8192  # 8GB默认
    available_memory_mb: int = 8192
    active_tasks: int = 0
    max_concurrent_tasks: int = 10
    tool_licenses: Dict[str, int] = field(default_factory=dict)
    api_quotas: Dict[str, int] = field(default_factory=dict)
    
    def can_allocate(self, resources: TaskResource) -> bool:
        """检查是否可以分配资源"""
        if resources.cpu_cores > self.available_cpu_cores:
            return False
        
        if resources.memory_mb > self.available_memory_mb:
            return False
        
        # 检查工具许可证
        for tool in resources.required_tools:
            if tool in self.tool_licenses and self.tool_licenses[tool] <= 0:
                return False
        
        # 检查API配额
        if resources.api_quota_required > 0:
            # 简单检查，实际实现中需要更复杂的配额管理
            total_quota = sum(self.api_quotas.values())
            if resources.api_quota_required > total_quota:
                return False
        
        return True
    
    def allocate(self, resources: TaskResource):
        """分配资源"""
        self.available_cpu_cores -= resources.cpu_cores
        self.available_memory_mb -= resources.memory_mb
        self.active_tasks += 1
        
        # 分配工具许可证
        for tool in resources.required_tools:
            if tool in self.tool_licenses:
                self.tool_licenses[tool] -= 1
    
    def release(self, resources: TaskResource):
        """释放资源"""
        self.available_cpu_cores += resources.cpu_cores
        self.available_memory_mb += resources.memory_mb
        self.active_tasks -= 1
        
        # 释放工具许可证
        for tool in resources.required_tools:
            if tool in self.tool_licenses:
                self.tool_licenses[tool] += 1


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, ExecutionTask] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}
        self.resource_manager = SystemResource()
        self.lock = threading.Lock()
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while True:
            try:
                # 获取优先级最高的任务
                priority, task = self.task_queue.get(timeout=1.0)
                
                # 检查依赖是否满足
                if not self._check_dependencies(task):
                    # 依赖不满足，重新放入队列（降低优先级）
                    self.task_queue.put((priority - 1, task))
                    continue
                
                # 检查资源是否可用
                if not self.resource_manager.can_allocate(task.resources):
                    # 资源不足，稍后重试
                    self.task_queue.put((priority, task))
                    time.sleep(0.5)
                    continue
                
                # 分配资源并执行任务
                self.resource_manager.allocate(task.resources)
                self.running_tasks[task.task_id] = task
                
                # 提交任务到线程池
                future = self.executor.submit(self._execute_task, task)
                future.add_done_callback(
                    lambda f, t=task: self._task_completed_callback(f, t)
                )
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"调度器错误: {e}")
                traceback.print_exc()
    
    def _check_dependencies(self, task: ExecutionTask) -> bool:
        """检查任务依赖是否满足"""
        if not task.dependencies:
            return True
        
        with self.lock:
            for dep_id in task.dependencies:
                if dep_id not in self.task_results:
                    return False
                
                result = self.task_results[dep_id]
                if result.status != TaskStatus.COMPLETED:
                    return False
        
        return True
    
    def _execute_task(self, task: ExecutionTask) -> Any:
        """执行任务"""
        start_time = time.time()
        
        try:
            # 根据任务类型执行不同的逻辑
            if task.task_type == "scan":
                result = self._execute_scan_task(task)
            elif task.task_type == "exploit":
                result = self._execute_exploit_task(task)
            elif task.task_type == "analysis":
                result = self._execute_analysis_task(task)
            elif task.task_type == "report":
                result = self._execute_report_task(task)
            else:
                # 默认任务执行
                result = {"status": "completed", "output": task.parameters}
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                output=result,
                execution_time=execution_time,
                retry_count=0
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=execution_time,
                retry_count=0
            )
    
    def _execute_scan_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """执行扫描任务"""
        target = task.parameters.get("target", "")
        scan_type = task.parameters.get("scan_type", "basic")
        
        # 模拟扫描执行
        time.sleep(2)  # 模拟扫描耗时
        
        return {
            "target": target,
            "scan_type": scan_type,
            "results": {
                "open_ports": [80, 443, 22],
                "services": {
                    "80": "HTTP",
                    "443": "HTTPS", 
                    "22": "SSH"
                },
                "vulnerabilities": [
                    {"type": "XSS", "severity": "medium"},
                    {"type": "SQLi", "severity": "high"}
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_exploit_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """执行漏洞利用任务"""
        vulnerability = task.parameters.get("vulnerability", {})
        target = task.parameters.get("target", "")
        
        # 模拟漏洞利用执行
        time.sleep(3)  # 模拟利用耗时
        
        return {
            "target": target,
            "vulnerability": vulnerability,
            "exploit_result": "success",
            "access_gained": True,
            "evidence": "exploit_success.log",
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_analysis_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """执行分析任务"""
        scan_data = task.parameters.get("scan_data", {})
        exploit_data = task.parameters.get("exploit_data", {})
        
        # 模拟分析执行
        time.sleep(1)
        
        return {
            "risk_assessment": "high",
            "attack_paths": [
                {"path": "web_exploit", "confidence": 0.85},
                {"path": "credential_attack", "confidence": 0.65}
            ],
            "recommendations": [
                "Patch XSS vulnerability",
                "Implement WAF rules",
                "Enable 2FA authentication"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_report_task(self, task: ExecutionTask) -> Dict[str, Any]:
        """执行报告生成任务"""
        data = task.parameters.get("data", {})
        report_format = task.parameters.get("format", "json")
        
        # 模拟报告生成
        time.sleep(2)
        
        report = {
            "summary": "Penetration Test Report",
            "findings": data.get("findings", []),
            "recommendations": data.get("recommendations", []),
            "risk_score": data.get("risk_score", 0),
            "generated_at": datetime.now().isoformat(),
            "format": report_format
        }
        
        return report
    
    def _task_completed_callback(self, future, task: ExecutionTask):
        """任务完成回调"""
        try:
            result = future.result()
            
            # 释放资源
            self.resource_manager.release(task.resources)
            
            with self.lock:
                # 处理重试逻辑
                if result.status == TaskStatus.FAILED and task.retry_count < task.max_retries:
                    # 重试任务
                    task.retry_count += 1
                    self.submit_task(task)
                else:
                    # 保存结果
                    self.task_results[task.task_id] = result
                    
                    # 移除运行中的任务
                    if task.task_id in self.running_tasks:
                        del self.running_tasks[task.task_id]
                    
                    # 通知回调（如果有）
                    if task.callback_url:
                        self._notify_callback(task.callback_url, result)
                
        except Exception as e:
            print(f"任务完成回调错误: {e}")
            traceback.print_exc()
    
    def _notify_callback(self, callback_url: str, result: TaskResult):
        """通知回调URL"""
        # 这里可以实现HTTP回调通知
        # 目前仅打印日志
        print(f"回调通知: {callback_url}, 任务ID: {result.task_id}, 状态: {result.status}")
    
    def submit_task(self, task: ExecutionTask) -> str:
        """提交任务到调度器"""
        # 设置任务优先级
        priority_value = task.priority.value
        
        # 添加到任务队列
        self.task_queue.put((priority_value, task))
        
        # 记录依赖关系
        if task.dependencies:
            for dep_id in task.dependencies:
                if dep_id not in self.task_dependencies:
                    self.task_dependencies[dep_id] = set()
                self.task_dependencies[dep_id].add(task.task_id)
        
        return task.task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        with self.lock:
            return self.task_results.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """获取所有任务状态"""
        with self.lock:
            return {
                "pending_tasks": self.task_queue.qsize(),
                "running_tasks": list(self.running_tasks.keys()),
                "completed_tasks": list(self.task_results.keys()),
                "resource_usage": {
                    "cpu_available": self.resource_manager.available_cpu_cores,
                    "memory_available": self.resource_manager.available_memory_mb,
                    "active_tasks": self.resource_manager.active_tasks
                }
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.lock:
            # 目前实现较简单，实际需要更复杂的取消逻辑
            if task_id in self.running_tasks:
                # 标记为取消状态
                self.task_results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.CANCELLED,
                    error="任务被取消"
                )
                return True
        
        return False
    
    def shutdown(self):
        """关闭调度器"""
        self.executor.shutdown(wait=True)


class SmartOrchestrator:
    """
    智能编排器 - 集成任务调度和资源管理
    支持复杂的渗透测试工作流编排
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.scheduler = TaskScheduler(max_workers=max_concurrent_tasks)
        self.workflows: Dict[str, List[ExecutionTask]] = {}
        self.execution_history = []
        
        # 初始化资源管理器
        self._init_resources()
    
    def _init_resources(self):
        """初始化资源"""
        # 配置工具许可证
        self.scheduler.resource_manager.tool_licenses = {
            "nmap": 5,      # 5个nmap许可证
            "metasploit": 2, # 2个metasploit许可证
            "sqlmap": 3,     # 3个sqlmap许可证
            "burpsuite": 1   # 1个burpsuite许可证
        }
        
        # 配置API配额
        self.scheduler.resource_manager.api_quotas = {
            "openai": 1000,    # 1000次API调用
            "deepseek": 5000,  # 5000次API调用
            "virustotal": 100  # 100次API调用
        }
    
    def create_workflow(self, workflow_name: str, tasks: List[Dict[str, Any]]) -> str:
        """
        创建工作流
        
        Args:
            workflow_name: 工作流名称
            tasks: 任务定义列表
            
        Returns:
            工作流ID
        """
        workflow_id = str(uuid.uuid4())
        execution_tasks = []
        
        # 创建任务映射
        task_map = {}
        for task_def in tasks:
            task_id = task_def.get("task_id") or str(uuid.uuid4())
            
            # 创建执行任务
            execution_task = ExecutionTask(
                task_id=task_id,
                task_type=task_def.get("task_type", "generic"),
                parameters=task_def.get("parameters", {}),
                priority=TaskPriority(task_def.get("priority", 2)),
                max_retries=task_def.get("max_retries", 3),
                timeout_seconds=task_def.get("timeout_seconds", 300),
                dependencies=task_def.get("dependencies", []),
                resources=TaskResource(**task_def.get("resources", {})),
                callback_url=task_def.get("callback_url"),
                metadata=task_def.get("metadata", {})
            )
            
            task_map[task_id] = execution_task
            execution_tasks.append(execution_task)
        
        # 存储工作流
        self.workflows[workflow_id] = execution_tasks
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str) -> str:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            执行ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        execution_id = str(uuid.uuid4())
        
        # 提交所有任务
        tasks = self.workflows[workflow_id]
        for task in tasks:
            self.scheduler.submit_task(task)
        
        # 记录执行历史
        self.execution_history.append({
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "start_time": time.time(),
            "tasks": [task.task_id for task in tasks]
        })
        
        return execution_id
    
    def execute_penetration_test(self, target: str, test_type: str = "full") -> str:
        """
        执行渗透测试工作流
        
        Args:
            target: 目标地址
            test_type: 测试类型 (quick, standard, full)
            
        Returns:
            执行ID
        """
        # 根据测试类型创建工作流
        if test_type == "quick":
            tasks = self._create_quick_scan_tasks(target)
        elif test_type == "standard":
            tasks = self._create_standard_scan_tasks(target)
        else:  # full
            tasks = self._create_full_scan_tasks(target)
        
        # 创建工作流并执行
        workflow_id = self.create_workflow(f"pen_test_{target}", tasks)
        return self.execute_workflow(workflow_id)
    
    def _create_quick_scan_tasks(self, target: str) -> List[Dict[str, Any]]:
        """创建快速扫描任务"""
        return [
            {
                "task_id": f"quick_scan_{target}_1",
                "task_type": "scan",
                "parameters": {
                    "target": target,
                    "scan_type": "port_scan"
                },
                "priority": TaskPriority.HIGH.value,
                "resources": {
                    "cpu_cores": 2,
                    "memory_mb": 512,
                    "required_tools": ["nmap"]
                }
            },
            {
                "task_id": f"quick_scan_{target}_2",
                "task_type": "scan",
                "parameters": {
                    "target": target,
                    "scan_type": "vulnerability_scan"
                },
                "dependencies": [f"quick_scan_{target}_1"],
                "priority": TaskPriority.HIGH.value,
                "resources": {
                    "cpu_cores": 1,
                    "memory_mb": 256,
                    "required_tools": ["nuclei"]
                }
            }
        ]
    
    def _create_standard_scan_tasks(self, target: str) -> List[Dict[str, Any]]:
        """创建标准扫描任务"""
        return [
            {
                "task_id": f"standard_scan_{target}_1",
                "task_type": "scan",
                "parameters": {
                    "target": target,
                    "scan_type": "comprehensive_scan"
                },
                "priority": TaskPriority.HIGH.value,
                "resources": {
                    "cpu_cores": 4,
                    "memory_mb": 1024,
                    "required_tools": ["nmap", "masscan"]
                }
            },
            {
                "task_id": f"standard_scan_{target}_2",
                "task_type": "analysis",
                "parameters": {
                    "scan_data": {"placeholder": "scan_results"}
                },
                "dependencies": [f"standard_scan_{target}_1"],
                "priority": TaskPriority.MEDIUM.value,
                "resources": {
                    "cpu_cores": 2,
                    "memory_mb": 512
                }
            },
            {
                "task_id": f"standard_scan_{target}_3",
                "task_type": "report",
                "parameters": {
                    "data": {"placeholder": "analysis_results"},
                    "format": "json"
                },
                "dependencies": [f"standard_scan_{target}_2"],
                "priority": TaskPriority.LOW.value,
                "resources": {
                    "cpu_cores": 1,
                    "memory_mb": 256
                }
            }
        ]
    
    def _create_full_scan_tasks(self, target: str) -> List[Dict[str, Any]]:
        """创建完整渗透测试任务"""
        return [
            # 阶段1: 信息收集
            {
                "task_id": f"full_scan_{target}_recon",
                "task_type": "scan",
                "parameters": {
                    "target": target,
                    "scan_type": "reconnaissance"
                },
                "priority": TaskPriority.HIGH.value,
                "resources": {
                    "cpu_cores": 2,
                    "memory_mb": 512,
                    "required_tools": ["nmap", "subfinder", "amass"]
                }
            },
            
            # 阶段2: 漏洞扫描
            {
                "task_id": f"full_scan_{target}_vuln_scan",
                "task_type": "scan",
                "parameters": {
                    "target": target,
                    "scan_type": "vulnerability_assessment"
                },
                "dependencies": [f"full_scan_{target}_recon"],
                "priority": TaskPriority.HIGH.value,
                "resources": {
                    "cpu_cores": 4,
                    "memory_mb": 1024,
                    "required_tools": ["nuclei", "nikto", "wpscan"]
                }
            },
            
            # 阶段3: 漏洞利用尝试
            {
                "task_id": f"full_scan_{target}_exploit",
                "task_type": "exploit",
                "parameters": {
                    "target": target,
                    "vulnerability": {"type": "simulated"}
                },
                "dependencies": [f"full_scan_{target}_vuln_scan"],
                "priority": TaskPriority.CRITICAL.value,
                "resources": {
                    "cpu_cores": 2,
                    "memory_mb": 768,
                    "required_tools": ["metasploit", "sqlmap"]
                }
            },
            
            # 阶段4: 分析评估
            {
                "task_id": f"full_scan_{target}_analysis",
                "task_type": "analysis",
                "parameters": {
                    "scan_data": {"placeholder": "vuln_results"},
                    "exploit_data": {"placeholder": "exploit_results"}
                },
                "dependencies": [f"full_scan_{target}_exploit"],
                "priority": TaskPriority.MEDIUM.value,
                "resources": {
                    "cpu_cores": 1,
                    "memory_mb": 256
                }
            },
            
            # 阶段5: 报告生成
            {
                "task_id": f"full_scan_{target}_report",
                "task_type": "report",
                "parameters": {
                    "data": {"placeholder": "final_results"},
                    "format": "detailed"
                },
                "dependencies": [f"full_scan_{target}_analysis"],
                "priority": TaskPriority.LOW.value,
                "resources": {
                    "cpu_cores": 1,
                    "memory_mb": 256
                }
            }
        ]
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """获取执行状态"""
        # 查找执行记录
        execution_record = None
        for record in self.execution_history:
            if record["execution_id"] == execution_id:
                execution_record = record
                break
        
        if not execution_record:
            return {"error": "执行记录不存在"}
        
        # 获取所有任务状态
        task_statuses = {}
        for task_id in execution_record.get("tasks", []):
            result = self.scheduler.get_task_status(task_id)
            if result:
                task_statuses[task_id] = {
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                    "error": result.error
                }
        
        return {
            "execution_id": execution_id,
            "workflow_id": execution_record["workflow_id"],
            "start_time": execution_record["start_time"],
            "task_statuses": task_statuses,
            "overall_status": self._calculate_overall_status(task_statuses)
        }
    
    def _calculate_overall_status(self, task_statuses: Dict[str, Any]) -> str:
        """计算整体状态"""
        if not task_statuses:
            return "unknown"
        
        status_counts = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        
        for status_info in task_statuses.values():
            status = status_info.get("status", "pending")
            if status in status_counts:
                status_counts[status] += 1
        
        # 判断整体状态
        if status_counts["failed"] > 0:
            return "failed"
        elif status_counts["running"] > 0:
            return "running"
        elif status_counts["pending"] > 0:
            return "pending"
        elif status_counts["completed"] == len(task_statuses):
            return "completed"
        
        return "unknown"
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        scheduler_status = self.scheduler.get_all_tasks()
        
        return {
            "scheduler": scheduler_status,
            "active_workflows": len(self.workflows),
            "execution_history_count": len(self.execution_history),
            "resource_manager": {
                "cpu_available": self.scheduler.resource_manager.available_cpu_cores,
                "memory_available": self.scheduler.resource_manager.available_memory_mb,
                "active_tasks": self.scheduler.resource_manager.active_tasks,
                "tool_licenses": self.scheduler.resource_manager.tool_licenses,
                "api_quotas": self.scheduler.resource_manager.api_quotas
            }
        }
    
    def shutdown(self):
        """关闭编排器"""
        self.scheduler.shutdown()


# 测试函数
def test_smart_orchestrator():
    """测试智能编排器"""
    print("=" * 80)
    print("智能编排系统测试 - 第5天任务：智能编排与执行优化")
    print("=" * 80)
    
    try:
        # 创建智能编排器
        orchestrator = SmartOrchestrator(max_concurrent_tasks=5)
        
        print("\n1. 测试系统状态获取")
        system_status = orchestrator.get_system_status()
        print(f"系统状态: {json.dumps(system_status, indent=2, ensure_ascii=False)}")
        
        print("\n2. 执行快速渗透测试")
        execution_id = orchestrator.execute_penetration_test(
            target="192.168.1.100", 
            test_type="quick"
        )
        print(f"执行ID: {execution_id}")
        
        # 等待任务执行
        print("等待任务执行...")
        time.sleep(5)
        
        # 获取执行状态
        print("\n3. 获取执行状态")
        execution_status = orchestrator.get_execution_status(execution_id)
        print(f"执行状态: {json.dumps(execution_status, indent=2, ensure_ascii=False)}")
        
        print("\n4. 测试标准工作流执行")
        standard_tasks = orchestrator._create_standard_scan_tasks("example.com")
        workflow_id = orchestrator.create_workflow("standard_test", standard_tasks)
        standard_exec_id = orchestrator.execute_workflow(workflow_id)
        print(f"标准工作流执行ID: {standard_exec_id}")
        
        # 等待任务执行
        time.sleep(8)
        
        # 再次获取系统状态
        print("\n5. 最终系统状态")
        final_status = orchestrator.get_system_status()
        print(f"最终系统状态: {json.dumps(final_status, indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 80)
        print("智能编排系统测试完成")
        
        # 关闭编排器
        orchestrator.shutdown()
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_smart_orchestrator()
    if success:
        print("\n[SUCCESS] 智能编排系统测试通过!")
    else:
        print("\n[FAILED] 智能编排系统测试失败!")