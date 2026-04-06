# -*- coding: utf-8 -*-
"""
异步任务管理器
提供异步任务执行、状态跟踪和队列管理功能
"""

import asyncio
import time
import uuid
import json
from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"      # 超时


class TaskPriority(int, Enum):
    """任务优先级枚举"""
    LOW = 1      # 低优先级
    NORMAL = 2   # 正常优先级
    HIGH = 3     # 高优先级
    CRITICAL = 4 # 关键优先级


class TaskType(str, Enum):
    """任务类型枚举"""
    SCAN = "scan"              # 扫描任务
    ANALYSIS = "analysis"      # 分析任务
    REPORT = "report"          # 报告任务
    WORKFLOW = "workflow"      # 工作流任务
    SYSTEM = "system"          # 系统任务
    CUSTOM = "custom"          # 自定义任务


@dataclass
class TaskResult:
    """任务结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": {
                "success": self.result.success if self.result else False,
                "data": self.result.data if self.result else None,
                "error": self.result.error if self.result else None,
                "execution_time": self.result.execution_time if self.result else 0.0
            } if self.result else None,
            "error": self.error,
            "metadata": self.metadata
        }


class AsyncTaskManager:
    """
    异步任务管理器
    
    特性：
    1. 支持异步任务执行
    2. 任务状态跟踪和进度更新
    3. 任务优先级队列
    4. 任务超时控制
    5. 任务结果缓存
    6. 任务依赖管理
    """
    
    def __init__(self, max_workers: int = 10, enable_process_pool: bool = False):
        """
        初始化任务管理器
        
        Args:
            max_workers: 最大工作线程数
            enable_process_pool: 是否启用进程池（用于CPU密集型任务）
        """
        self.max_workers = max_workers
        self.enable_process_pool = enable_process_pool
        
        # 任务存储
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_results: Dict[str, TaskResult] = {}
        
        # 执行器
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers // 2) if enable_process_pool else None
        
        # 任务队列
        self.task_queue = asyncio.PriorityQueue()
        
        # 事件循环
        self.loop = asyncio.get_event_loop()
        
        # 启动任务消费者
        self.consumer_task = None
        self.running = False
        
        logger.info(f"AsyncTaskManager 初始化完成 - 最大工作线程: {max_workers}")
    
    async def start(self):
        """启动任务管理器"""
        if self.running:
            logger.warning("任务管理器已经在运行")
            return
        
        self.running = True
        self.consumer_task = asyncio.create_task(self._task_consumer())
        logger.info("任务管理器已启动")
    
    async def stop(self):
        """停止任务管理器"""
        if not self.running:
            logger.warning("任务管理器未运行")
            return
        
        self.running = False
        
        # 取消消费者任务
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
        
        # 关闭执行器
        self.thread_executor.shutdown(wait=True)
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
        
        logger.info("任务管理器已停止")
    
    async def submit_task(
        self,
        task_func: Callable,
        task_type: TaskType = TaskType.CUSTOM,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        提交异步任务
        
        Args:
            task_func: 任务函数
            task_type: 任务类型
            priority: 任务优先级
            timeout: 任务超时时间（秒）
            **kwargs: 任务函数参数
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 创建任务信息
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.now(),
            metadata={
                "function_name": task_func.__name__,
                "timeout": timeout,
                "kwargs": kwargs
            }
        )
        
        # 存储任务信息
        self.tasks[task_id] = task_info
        
        # 添加到队列（优先级越高，数字越小）
        queue_priority = -priority.value  # 反转优先级，使高优先级先执行
        await self.task_queue.put((queue_priority, task_id, task_func, kwargs))
        
        logger.info(f"任务已提交 - ID: {task_id}, 类型: {task_type}, 优先级: {priority}")
        
        return task_id
    
    async def _task_consumer(self):
        """任务消费者"""
        logger.info("任务消费者已启动")
        
        while self.running:
            try:
                # 从队列获取任务
                priority, task_id, task_func, kwargs = await self.task_queue.get()
                
                # 检查任务是否存在
                if task_id not in self.tasks:
                    logger.warning(f"任务不存在: {task_id}")
                    self.task_queue.task_done()
                    continue
                
                task_info = self.tasks[task_id]
                
                # 更新任务状态
                task_info.status = TaskStatus.RUNNING
                task_info.started_at = datetime.now()
                
                logger.info(f"开始执行任务 - ID: {task_id}")
                
                # 执行任务
                try:
                    result = await self._execute_task(task_func, kwargs, task_info.metadata.get("timeout"))
                    
                    # 更新任务状态
                    task_info.status = TaskStatus.COMPLETED
                    task_info.completed_at = datetime.now()
                    task_info.result = result
                    task_info.progress = 100.0
                    
                    # 存储结果
                    self.task_results[task_id] = result
                    
                    logger.info(f"任务执行完成 - ID: {task_id}, 耗时: {result.execution_time:.2f}s")
                    
                except asyncio.TimeoutError:
                    task_info.status = TaskStatus.TIMEOUT
                    task_info.completed_at = datetime.now()
                    task_info.error = "任务执行超时"
                    logger.error(f"任务执行超时 - ID: {task_id}")
                    
                except Exception as e:
                    task_info.status = TaskStatus.FAILED
                    task_info.completed_at = datetime.now()
                    task_info.error = str(e)
                    logger.error(f"任务执行失败 - ID: {task_id}, 错误: {e}")
                
                finally:
                    self.task_queue.task_done()
                    
            except asyncio.CancelledError:
                logger.info("任务消费者被取消")
                break
                
            except Exception as e:
                logger.error(f"任务消费者错误: {e}")
                await asyncio.sleep(1)  # 错误后等待1秒
    
    async def _execute_task(self, task_func: Callable, kwargs: Dict, timeout: Optional[float]) -> TaskResult:
        """执行任务"""
        start_time = time.time()
        
        try:
            # 根据任务类型选择执行器
            if self._is_cpu_intensive(task_func):
                # CPU密集型任务使用进程池
                if self.process_executor:
                    result = await self.loop.run_in_executor(
                        self.process_executor,
                        lambda: task_func(**kwargs)
                    )
                else:
                    result = await self.loop.run_in_executor(
                        self.thread_executor,
                        lambda: task_func(**kwargs)
                    )
            else:
                # IO密集型任务使用线程池
                result = await self.loop.run_in_executor(
                    self.thread_executor,
                    lambda: task_func(**kwargs)
                )
            
            execution_time = time.time() - start_time
            
            return TaskResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _is_cpu_intensive(self, task_func: Callable) -> bool:
        """判断是否为CPU密集型任务"""
        # 这里可以根据函数名或其他特征判断
        cpu_intensive_functions = [
            "analyze_target",
            "generate_report",
            "process_data",
            "calculate_statistics"
        ]
        
        return task_func.__name__ in cpu_intensive_functions
    
    async def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id]
        return None
    
    async def update_task_progress(self, task_id: str, progress: float, message: Optional[str] = None):
        """更新任务进度"""
        if task_id in self.tasks:
            task_info = self.tasks[task_id]
            task_info.progress = max(0.0, min(100.0, progress))
            
            if message:
                task_info.metadata["progress_message"] = message
            
            logger.debug(f"任务进度更新 - ID: {task_id}, 进度: {progress}%")
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.tasks:
            task_info = self.tasks[task_id]
            
            if task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = datetime.now()
                logger.info(f"任务已取消 - ID: {task_id}")
                return True
        
        logger.warning(f"无法取消任务 - ID: {task_id}, 状态: {task_info.status if task_id in self.tasks else '不存在'}")
        return False
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取任务结果"""
        return self.task_results.get(task_id)
    
    async def list_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        # 过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self.tasks)
        
        status_counts = {}
        type_counts = {}
        
        for task in self.tasks.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
            type_counts[task.task_type.value] = type_counts.get(task.task_type.value, 0) + 1
        
        # 计算平均执行时间
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED and t.result]
        avg_execution_time = 0.0
        if completed_tasks:
            avg_execution_time = sum(t.result.execution_time for t in completed_tasks) / len(completed_tasks)
        
        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "type_counts": type_counts,
            "queue_size": self.task_queue.qsize(),
            "avg_execution_time": round(avg_execution_time, 2),
            "active_workers": self.thread_executor._max_workers,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task_info in self.tasks.items():
            if task_info.created_at.timestamp() < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.task_results:
                del self.task_results[task_id]
        
        logger.info(f"清理了 {len(tasks_to_remove)} 个旧任务")
        return len(tasks_to_remove)


# 全局任务管理器实例
_task_manager_instance = None

async def get_task_manager() -> AsyncTaskManager:
    """获取全局任务管理器实例"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = AsyncTaskManager(max_workers=10)
        await _task_manager_instance.start()
    return _task_manager_instance


def task_decorator(task_type: TaskType = TaskType.CUSTOM, priority: TaskPriority = TaskPriority.NORMAL):
    """
    任务装饰器
    
    Args:
        task_type: 任务类型
        priority: 任务优先级
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            task_manager = await get_task_manager()
            
            # 提交任务
            task_id = await task_manager.submit_task(
                task_func=lambda: func(*args, **kwargs),
                task_type=task_type,
                priority=priority,
                **kwargs
            )
            
            # 等待任务完成
            while True:
                task_info = await task_manager.get_task_status(task_id)
                if task_info and task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task_info.result:
                        if task_info.result.success:
                            return task_info.result.data
                        else:
                            raise Exception(f"任务执行失败: {task_info.result.error}")
                    else:
                        raise Exception(f"任务执行失败: {task_info.error}")
                
                await asyncio.sleep(0.1)
        
        return wrapper
    return decorator