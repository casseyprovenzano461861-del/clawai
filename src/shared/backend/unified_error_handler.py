# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
统一错误处理和日志记录模块
提供结构化的错误处理、日志记录和监控功能
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json


class UnifiedErrorHandler:
    """
    统一错误处理器
    提供结构化的错误处理、日志记录和监控功能
    """
    
    def __init__(self, log_level: str = "INFO", log_file: str = None):
        """
        初始化错误处理器
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件路径，如果为None则输出到控制台
        """
        self.log_level = log_level
        self.log_file = log_file
        self._setup_logging()
        
        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "module_errors": {},
            "recent_errors": []
        }
        
        # 性能监控
        self.performance_stats = {
            "total_operations": 0,
            "failed_operations": 0,
            "operation_times": {},
            "average_response_time": 0.0
        }
    
    def _setup_logging(self):
        """配置日志系统"""
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建处理器
        if self.log_file:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
        else:
            handler = logging.StreamHandler(sys.stdout)
        
        handler.setFormatter(formatter)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level.upper()))
        root_logger.addHandler(handler)
        
        # 避免重复日志
        root_logger.propagate = False
        
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, 
                    severity: str = "ERROR") -> Dict[str, Any]:
        """
        处理错误并记录
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            severity: 错误严重性 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            错误处理结果
        """
        # 更新错误统计
        self.error_stats["total_errors"] += 1
        
        # 获取错误类型
        error_type = type(error).__name__
        self.error_stats["error_types"][error_type] = self.error_stats["error_types"].get(error_type, 0) + 1
        
        # 获取模块信息
        tb = traceback.extract_tb(error.__traceback__)
        if tb:
            module_name = tb[-1].filename.split('/')[-1].split('\\')[-1]
            self.error_stats["module_errors"][module_name] = self.error_stats["module_errors"].get(module_name, 0) + 1
        
        # 构建错误信息
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "severity": severity,
            "context": context or {},
            "traceback": traceback.format_exception(type(error), error, error.__traceback__)
        }
        
        # 记录最近错误（最多保留10个）
        self.error_stats["recent_errors"].append(error_info)
        if len(self.error_stats["recent_errors"]) > 10:
            self.error_stats["recent_errors"] = self.error_stats["recent_errors"][-10:]
        
        # 记录日志
        log_message = f"{error_type}: {str(error)}"
        if context:
            log_message += f" | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if severity == "DEBUG":
            self.logger.debug(log_message, exc_info=True)
        elif severity == "INFO":
            self.logger.info(log_message, exc_info=True)
        elif severity == "WARNING":
            self.logger.warning(log_message, exc_info=True)
        elif severity == "ERROR":
            self.logger.error(log_message, exc_info=True)
        elif severity == "CRITICAL":
            self.logger.critical(log_message, exc_info=True)
        
        return error_info
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        安全执行函数，自动处理异常
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            执行结果
        """
        self.performance_stats["total_operations"] += 1
        
        try:
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            
            # 记录执行时间
            execution_time = (end_time - start_time).total_seconds()
            func_name = func.__name__
            
            if func_name not in self.performance_stats["operation_times"]:
                self.performance_stats["operation_times"][func_name] = []
            
            self.performance_stats["operation_times"][func_name].append(execution_time)
            
            # 更新平均响应时间
            total_time = sum(sum(times) for times in self.performance_stats["operation_times"].values())
            total_ops = sum(len(times) for times in self.performance_stats["operation_times"].values())
            if total_ops > 0:
                self.performance_stats["average_response_time"] = total_time / total_ops
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "error": None
            }
            
        except Exception as e:
            self.performance_stats["failed_operations"] += 1
            
            error_info = self.handle_error(
                e,
                context={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                },
                severity="ERROR"
            )
            
            return {
                "success": False,
                "result": None,
                "execution_time": 0,
                "error": error_info
            }
    
    def log_operation(self, operation: str, details: Dict[str, Any] = None, 
                     level: str = "INFO") -> None:
        """
        记录操作日志
        
        Args:
            operation: 操作名称
            details: 操作详情
            level: 日志级别
        """
        log_message = f"Operation: {operation}"
        if details:
            log_message += f" | Details: {json.dumps(details, ensure_ascii=False)}"
        
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "total_errors": self.error_stats["total_errors"],
            "error_types": dict(sorted(self.error_stats["error_types"].items(), key=lambda x: x[1], reverse=True)),
            "module_errors": dict(sorted(self.error_stats["module_errors"].items(), key=lambda x: x[1], reverse=True)),
            "recent_errors_count": len(self.error_stats["recent_errors"]),
            "error_rate": self.error_stats["total_errors"] / max(self.performance_stats["total_operations"], 1)
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = {
            "total_operations": self.performance_stats["total_operations"],
            "failed_operations": self.performance_stats["failed_operations"],
            "success_rate": 1 - (self.performance_stats["failed_operations"] / max(self.performance_stats["total_operations"], 1)),
            "average_response_time": self.performance_stats["average_response_time"]
        }
        
        # 计算各操作的平均时间
        operation_stats = {}
        for op_name, times in self.performance_stats["operation_times"].items():
            if times:
                operation_stats[op_name] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        stats["operation_stats"] = operation_stats
        return stats
    
    def clear_stats(self) -> None:
        """清除统计信息"""
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "module_errors": {},
            "recent_errors": []
        }
        
        self.performance_stats = {
            "total_operations": 0,
            "failed_operations": 0,
            "operation_times": {},
            "average_response_time": 0.0
        }
    
    def create_error_report(self) -> Dict[str, Any]:
        """创建错误报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "error_stats": self.get_error_stats(),
            "performance_stats": self.get_performance_stats(),
            "recent_errors": self.error_stats["recent_errors"][-5:],  # 最近5个错误
            "summary": {
                "total_operations": self.performance_stats["total_operations"],
                "total_errors": self.error_stats["total_errors"],
                "error_rate": self.error_stats["total_errors"] / max(self.performance_stats["total_operations"], 1),
                "success_rate": 1 - (self.performance_stats["failed_operations"] / max(self.performance_stats["total_operations"], 1))
            }
        }


# 全局错误处理器实例
_error_handler = None

def get_error_handler(log_level: str = "INFO", log_file: str = None) -> UnifiedErrorHandler:
    """
    获取全局错误处理器实例（单例模式）
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        
    Returns:
        错误处理器实例
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = UnifiedErrorHandler(log_level=log_level, log_file=log_file)
    return _error_handler

def handle_error(error: Exception, context: Dict[str, Any] = None, 
                severity: str = "ERROR") -> Dict[str, Any]:
    """
    全局错误处理函数
    
    Args:
        error: 异常对象
        context: 错误上下文
        severity: 错误严重性
        
    Returns:
        错误处理结果
    """
    handler = get_error_handler()
    return handler.handle_error(error, context, severity)

def safe_execute(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    全局安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        执行结果
    """
    handler = get_error_handler()
    return handler.safe_execute(func, *args, **kwargs)

def log_operation(operation: str, details: Dict[str, Any] = None, 
                 level: str = "INFO") -> None:
    """
    全局操作日志记录
    
    Args:
        operation: 操作名称
        details: 操作详情
        level: 日志级别
    """
    handler = get_error_handler()
    handler.log_operation(operation, details, level)

def get_stats() -> Dict[str, Any]:
    """
    获取全局统计信息
    
    Returns:
        统计信息
    """
    handler = get_error_handler()
    return {
        "error_stats": handler.get_error_stats(),
        "performance_stats": handler.get_performance_stats()
    }

def create_report() -> Dict[str, Any]:
    """
    创建全局报告
    
    Returns:
        报告数据
    """
    handler = get_error_handler()
    return handler.create_error_report()


def main():
    """测试错误处理器"""
    print("=" * 80)
    print("统一错误处理器测试")
    print("=" * 80)
    
    # 获取错误处理器
    handler = get_error_handler(log_level="DEBUG")
    
    # 测试安全执行
    print("\n1. 测试安全执行（成功案例）:")
    def successful_function(x, y):
        return x + y
    
    result = safe_execute(successful_function, 10, 20)
    print(f"结果: {result}")
    
    # 测试错误处理
    print("\n2. 测试安全执行（失败案例）:")
    def failing_function():
        raise ValueError("测试错误：函数执行失败")
    
    result = safe_execute(failing_function)
    print(f"结果: {result}")
    
    # 测试直接错误处理
    print("\n3. 测试直接错误处理:")
    try:
        raise RuntimeError("测试运行时错误")
    except Exception as e:
        error_result = handle_error(e, {"test": "context"}, "WARNING")
        print(f"错误处理结果: {json.dumps(error_result, indent=2, ensure_ascii=False)}")
    
    # 测试操作日志
    print("\n4. 测试操作日志:")
    log_operation("test_operation", {"param1": "value1", "param2": 123}, "INFO")
    
    # 获取统计信息
    print("\n5. 获取统计信息:")
    stats = get_stats()
    print(f"错误统计: {json.dumps(stats['error_stats'], indent=2, ensure_ascii=False)}")
    print(f"性能统计: {json.dumps(stats['performance_stats'], indent=2, ensure_ascii=False)}")
    
    # 创建报告
    print("\n6. 创建错误报告:")
    report = create_report()
    print(f"报告摘要: {json.dumps(report['summary'], indent=2, ensure_ascii=False)}")
    
    print("\n" + "=" * 80)
    print("测试完成！")


if __name__ == "__main__":
    main()
