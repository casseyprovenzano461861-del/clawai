# -*- coding: utf-8 -*-
"""
性能优化模块
实现并行执行、资源管理、缓存机制和超时控制
"""

import concurrent.futures
import time
import hashlib
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class Task:
    """任务信息"""
    id: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    success: bool
    result: Any = None
    error: str = ""
    execution_time: float = 0.0


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, max_workers: int = 10, cache_enabled: bool = True, cache_ttl: int = 3600):
        """初始化性能优化器"""
        self.max_workers = max_workers
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.cache_lock = threading.RLock()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    def execute_tasks(self, tasks: List[Task]) -> Dict[str, TaskResult]:
        """并行执行任务"""
        results = {}
        futures = {}
        
        # 检查缓存
        for task in tasks:
            cache_key = self._generate_cache_key(task)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                # 使用缓存结果
                results[task.id] = cached_result
            else:
                # 提交任务到线程池
                future = self.executor.submit(self._execute_task, task)
                futures[future] = (task, cache_key)
        
        # 收集结果
        for future in concurrent.futures.as_completed(futures):
            task, cache_key = futures[future]
            
            try:
                result = future.result()
                # 保存到缓存
                if self.cache_enabled:
                    self._save_to_cache(cache_key, result)
                results[task.id] = result
            except Exception as e:
                results[task.id] = TaskResult(
                    task_id=task.id,
                    success=False,
                    error=str(e)
                )
        
        return results
    
    def _execute_task(self, task: Task) -> TaskResult:
        """执行单个任务"""
        start_time = time.time()
        
        try:
            # 执行任务
            result = task.function(*task.args, **task.kwargs)
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            
            return TaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _generate_cache_key(self, task: Task) -> str:
        """生成缓存键"""
        # 基于任务函数名、参数和关键字参数生成缓存键
        key_data = {
            "function": task.function.__name__ if hasattr(task.function, "__name__") else str(task.function),
            "args": task.args,
            "kwargs": task.kwargs
        }
        
        # 序列化并生成哈希值
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[TaskResult]:
        """从缓存获取结果"""
        if not self.cache_enabled:
            return None
        
        with self.cache_lock:
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                timestamp = cached_data["timestamp"]
                result = cached_data["result"]
                
                # 检查缓存是否过期
                if time.time() - timestamp < self.cache_ttl:
                    return result
                else:
                    # 移除过期缓存
                    del self.cache[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, result: TaskResult):
        """保存结果到缓存"""
        if not self.cache_enabled:
            return
        
        with self.cache_lock:
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": result
            }
    
    def clear_cache(self):
        """清除缓存"""
        with self.cache_lock:
            self.cache.clear()
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        with self.cache_lock:
            return len(self.cache)
    
    def shutdown(self, wait: bool = True):
        """关闭线程池"""
        self.executor.shutdown(wait=wait)
    
    def execute_with_timeout(self, function: Callable, args: tuple = (), kwargs: dict = {}, timeout: float = 30.0) -> Any:
        """带超时的执行"""
        def wrapper():
            return function(*args, **kwargs)
        
        future = self.executor.submit(wrapper)
        
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"任务执行超时（{timeout}秒）")
    
    def execute_batch(self, functions: List[Callable], args_list: List[tuple] = None, kwargs_list: List[dict] = None, timeout: float = 30.0) -> List[Any]:
        """批量执行函数"""
        if args_list is None:
            args_list = [() for _ in functions]
        
        if kwargs_list is None:
            kwargs_list = [{} for _ in functions]
        
        # 创建任务列表
        tasks = []
        for i, (func, args, kwargs) in enumerate(zip(functions, args_list, kwargs_list)):
            task = Task(
                id=f"task_{i}",
                function=func,
                args=args,
                kwargs=kwargs,
                timeout=timeout
            )
            tasks.append(task)
        
        # 执行任务
        results = self.execute_tasks(tasks)
        
        # 提取结果
        return [results[task.id].result for task in tasks if results[task.id].success]


# 测试代码
if __name__ == "__main__":
    # 初始化性能优化器
    optimizer = PerformanceOptimizer(max_workers=5, cache_enabled=True)
    
    print("=" * 80)
    print("性能优化器测试")
    print("=" * 80)
    
    # 测试1: 基本并行执行
    print("\n测试1: 基本并行执行")
    
    def test_function(name, delay):
        print(f"开始执行 {name}")
        time.sleep(delay)
        print(f"完成执行 {name}")
        return f"{name} 执行结果"
    
    tasks = [
        Task(id="task1", function=test_function, args=("任务1", 2)),
        Task(id="task2", function=test_function, args=("任务2", 1)),
        Task(id="task3", function=test_function, args=("任务3", 3)),
        Task(id="task4", function=test_function, args=("任务4", 1.5)),
        Task(id="task5", function=test_function, args=("任务5", 2.5))
    ]
    
    start_time = time.time()
    results = optimizer.execute_tasks(tasks)
    end_time = time.time()
    
    print(f"\n并行执行耗时: {end_time - start_time:.2f} 秒")
    for task_id, result in results.items():
        print(f"{task_id}: {'成功' if result.success else '失败'} - {result.result or result.error}")
    
    # 测试2: 缓存机制
    print("\n测试2: 缓存机制")
    
    def expensive_function(x):
        print(f"执行昂贵函数，参数: {x}")
        time.sleep(1)
        return x * x
    
    # 第一次执行（应该执行）
    print("\n第一次执行:")
    task1 = Task(id="cache_test1", function=expensive_function, args=(5,))
    result1 = optimizer.execute_tasks([task1])
    print(f"结果: {result1['cache_test1'].result}")
    print(f"缓存大小: {optimizer.get_cache_size()}")
    
    # 第二次执行（应该使用缓存）
    print("\n第二次执行:")
    task2 = Task(id="cache_test2", function=expensive_function, args=(5,))
    result2 = optimizer.execute_tasks([task2])
    print(f"结果: {result2['cache_test2'].result}")
    print(f"缓存大小: {optimizer.get_cache_size()}")
    
    # 测试3: 带超时的执行
    print("\n测试3: 带超时的执行")
    
    def long_running_function():
        time.sleep(5)
        return "执行完成"
    
    try:
        result = optimizer.execute_with_timeout(long_running_function, timeout=2)
        print(f"结果: {result}")
    except TimeoutError as e:
        print(f"超时错误: {e}")
    
    # 测试4: 批量执行
    print("\n测试4: 批量执行")
    
    functions = [
        lambda x: x + 1,
        lambda x: x * 2,
        lambda x: x ** 2
    ]
    args_list = [(1,), (2,), (3,)]
    
    results = optimizer.execute_batch(functions, args_list)
    print(f"批量执行结果: {results}")
    
    # 清理
    optimizer.shutdown()
    
    print("\n" + "=" * 80)
    print("测试完成")
