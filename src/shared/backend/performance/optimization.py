# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
性能优化模块 - 第四阶段：性能优化
集成异步处理、连接池、缓存策略和性能监控
"""

import asyncio
import os
import sys
import json
import time
import logging
import functools
import threading
from typing import Dict, List, Any, Optional, Callable, Union, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import redis
import aioredis
import aiomysql
import aiohttp
from contextlib import asynccontextmanager

# 导入现有缓存系统
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.core.llm_cache import IntelligentLLMCache
from config import config

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    request_id: str
    endpoint: str
    start_time: float
    end_time: float
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hits: int = 0
    cache_misses: int = 0
    database_queries: int = 0
    external_api_calls: int = 0
    success: bool = True
    error_message: Optional[str] = None


class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self):
        self.redis_pool = None
        self.mysql_pool = None
        self.http_session = None
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        self.lock = threading.Lock()
    
    async def init_redis_pool(self, redis_url: str = None):
        """初始化Redis连接池"""
        if not redis_url:
            redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}"
        
        try:
            self.redis_pool = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Redis连接池初始化成功: {redis_url}")
        except Exception as e:
            logger.error(f"Redis连接池初始化失败: {e}")
            self.redis_pool = None
    
    async def init_mysql_pool(self, mysql_config: Dict = None):
        """初始化MySQL连接池"""
        if not mysql_config:
            mysql_config = {
                "host": config.DB_HOST,
                "port": config.DB_PORT,
                "user": config.DB_USER,
                "password": config.DB_PASSWORD,
                "db": config.DB_NAME,
                "minsize": 1,
                "maxsize": 10
            }
        
        try:
            self.mysql_pool = await aiomysql.create_pool(**mysql_config)
            logger.info("MySQL连接池初始化成功")
        except Exception as e:
            logger.error(f"MySQL连接池初始化失败: {e}")
            self.mysql_pool = None
    
    async def init_http_session(self):
        """初始化HTTP会话连接池"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            logger.info("HTTP会话连接池初始化成功")
        except Exception as e:
            logger.error(f"HTTP会话连接池初始化失败: {e}")
            self.http_session = None
    
    async def get_redis(self):
        """获取Redis连接"""
        if not self.redis_pool:
            await self.init_redis_pool()
        return self.redis_pool
    
    async def get_mysql(self):
        """获取MySQL连接"""
        if not self.mysql_pool:
            await self.init_mysql_pool()
        return self.mysql_pool
    
    async def get_http_session(self):
        """获取HTTP会话"""
        if not self.http_session:
            await self.init_http_session()
        return self.http_session
    
    async def close_all(self):
        """关闭所有连接池"""
        if self.redis_pool:
            await self.redis_pool.close()
        if self.mysql_pool:
            self.mysql_pool.close()
            await self.mysql_pool.wait_closed()
        if self.http_session:
            await self.http_session.close()
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("所有连接池已关闭")


class AsyncExecutor:
    """异步执行器"""
    
    def __init__(self, connection_pool: ConnectionPoolManager = None):
        self.connection_pool = connection_pool or ConnectionPoolManager()
        self.cache_system = IntelligentLLMCache(backend="sqlite")
        self.metrics_store = []
        self.max_metrics = 1000
    
    async def execute_tool_async(self, tool_name: str, target: str, options: Dict = None) -> Dict[str, Any]:
        """异步执行工具"""
        if options is None:
            options = {}
        
        cache_key = f"tool:{tool_name}:{target}:{hash(str(options))}"
        
        # 检查缓存
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"工具 {tool_name} 缓存命中")
            return cached_result
        
        # 执行工具
        start_time = time.time()
        try:
            # 这里应该调用真实的工具执行逻辑
            result = await self._execute_tool_real_async(tool_name, target, options)
            result["execution_time"] = time.time() - start_time
            result["cache_key"] = cache_key
            
            # 缓存结果
            await self._cache_result(cache_key, result, ttl=300)  # 5分钟TTL
            
            return result
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {e}")
            return {
                "tool": tool_name,
                "target": target,
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    async def execute_scan_async(self, target: str, tools: List[str] = None) -> Dict[str, Any]:
        """异步执行扫描任务"""
        if tools is None:
            tools = ["nmap", "whatweb", "nuclei", "httpx"]
        
        start_time = time.time()
        logger.info(f"开始异步扫描: {target}")
        
        # 并发执行所有工具
        tasks = []
        for tool_name in tools:
            task = self.execute_tool_async(tool_name, target)
            tasks.append(task)
        
        # 等待所有任务完成
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        results = {}
        for tool_name, result in zip(tools, results_list):
            if isinstance(result, Exception):
                results[tool_name] = {
                    "tool": tool_name,
                    "success": False,
                    "error": str(result)
                }
            else:
                results[tool_name] = result
        
        total_time = time.time() - start_time
        
        # 分析结果
        analysis = self._analyze_scan_results(results)
        
        return {
            "target": target,
            "execution_time": total_time,
            "results": results,
            "analysis": analysis,
            "performance": {
                "total_tools": len(tools),
                "successful_tools": sum(1 for r in results.values() if r.get("success", False)),
                "failed_tools": sum(1 for r in results.values() if not r.get("success", True)),
                "average_tool_time": total_time / len(tools) if tools else 0
            }
        }
    
    async def _execute_tool_real_async(self, tool_name: str, target: str, options: Dict) -> Dict[str, Any]:
        """异步执行真实工具（模拟实现）"""
        # 这里应该集成现有的统一工具执行器
        # 暂时使用模拟实现
        
        await asyncio.sleep(0.5)  # 模拟工具执行时间
        
        # 根据工具类型返回不同的结果
        if tool_name == "nmap":
            return {
                "tool": tool_name,
                "target": target,
                "success": True,
                "ports": [
                    {"port": 80, "service": "http", "state": "open"},
                    {"port": 443, "service": "https", "state": "open"},
                    {"port": 22, "service": "ssh", "state": "closed"}
                ]
            }
        elif tool_name == "whatweb":
            return {
                "tool": tool_name,
                "target": target,
                "success": True,
                "fingerprint": {
                    "web_server": "nginx/1.18.0",
                    "technologies": ["PHP", "jQuery", "Bootstrap"]
                }
            }
        elif tool_name == "nuclei":
            return {
                "tool": tool_name,
                "target": target,
                "success": True,
                "vulnerabilities": [
                    {"name": "CVE-2021-1234", "severity": "high"},
                    {"name": "CVE-2021-5678", "severity": "medium"}
                ]
            }
        else:
            return {
                "tool": tool_name,
                "target": target,
                "success": True,
                "result": "工具执行成功"
            }
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取结果"""
        try:
            redis = await self.connection_pool.get_redis()
            if redis:
                cached_data = await redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis缓存获取失败: {e}")
        
        # 回退到LLM缓存系统
        return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any], ttl: int = 300):
        """缓存结果"""
        try:
            redis = await self.connection_pool.get_redis()
            if redis:
                await redis.setex(cache_key, ttl, json.dumps(result))
        except Exception as e:
            logger.warning(f"Redis缓存设置失败: {e}")
    
    def _analyze_scan_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """分析扫描结果"""
        total_tools = len(results)
        successful_tools = sum(1 for r in results.values() if r.get("success", False))
        
        # 提取漏洞信息
        vulnerabilities = []
        for tool_result in results.values():
            if tool_result.get("success") and "vulnerabilities" in tool_result:
                vulnerabilities.extend(tool_result["vulnerabilities"])
        
        # 风险等级评估
        risk_level = "low"
        if vulnerabilities:
            high_vulns = sum(1 for v in vulnerabilities if v.get("severity") == "high")
            if high_vulns > 0:
                risk_level = "critical" if high_vulns > 2 else "high"
            elif any(v.get("severity") == "medium" for v in vulnerabilities):
                risk_level = "medium"
        
        return {
            "total_tools": total_tools,
            "successful_tools": successful_tools,
            "success_rate": successful_tools / total_tools * 100 if total_tools > 0 else 0,
            "vulnerabilities_found": len(vulnerabilities),
            "risk_level": risk_level,
            "recommendations": self._generate_recommendations(results, vulnerabilities)
        }
    
    def _generate_recommendations(self, results: Dict, vulnerabilities: List) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 基于扫描结果生成建议
        if "nmap" in results and results["nmap"].get("success"):
            ports = results["nmap"].get("ports", [])
            open_ports = [p for p in ports if p.get("state") == "open"]
            if len(open_ports) > 10:
                recommendations.append("开放端口过多，建议关闭不必要的服务")
        
        if vulnerabilities:
            high_vulns = [v for v in vulnerabilities if v.get("severity") == "high"]
            if high_vulns:
                recommendations.append(f"发现 {len(high_vulns)} 个高危漏洞，建议立即修复")
        
        if not recommendations:
            recommendations.append("未发现明显安全问题，建议定期安全扫描")
        
        return recommendations
    
    async def track_performance(self, metrics: PerformanceMetrics):
        """跟踪性能指标"""
        with threading.Lock():
            self.metrics_store.append(metrics)
            if len(self.metrics_store) > self.max_metrics:
                self.metrics_store = self.metrics_store[-self.max_metrics:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.metrics_store:
            return {"message": "暂无性能数据"}
        
        recent_metrics = self.metrics_store[-100:]  # 最近100条
        
        # 计算统计信息
        execution_times = [m.execution_time for m in recent_metrics]
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics) * 100
        
        # 按端点分组
        endpoints = {}
        for metric in recent_metrics:
            if metric.endpoint not in endpoints:
                endpoints[metric.endpoint] = []
            endpoints[metric.endpoint].append(metric)
        
        endpoint_stats = {}
        for endpoint, metrics_list in endpoints.items():
            times = [m.execution_time for m in metrics_list]
            endpoint_stats[endpoint] = {
                "call_count": len(metrics_list),
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "success_rate": sum(1 for m in metrics_list if m.success) / len(metrics_list) * 100
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_requests": len(self.metrics_store),
            "recent_requests": len(recent_metrics),
            "overall_success_rate": success_rate,
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "p95_execution_time": sorted(execution_times)[int(len(execution_times) * 0.95)],
            "p99_execution_time": sorted(execution_times)[int(len(execution_times) * 0.99)],
            "endpoint_stats": endpoint_stats,
            "cache_stats": self._get_cache_stats()
        }
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            return self.cache_system.get_cache_stats()
        except:
            return {"error": "缓存系统不可用"}


def performance_monitor(func: Callable):
    """性能监控装饰器"""
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            request_id = f"{func.__name__}_{int(time.time() * 1000)}"
            start_time = time.time()
            
            try:
                # 获取资源使用情况
                import psutil
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                start_cpu = process.cpu_percent()
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 计算指标
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024
                end_cpu = process.cpu_percent()
                
                metrics = PerformanceMetrics(
                    request_id=request_id,
                    endpoint=func.__name__,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    memory_usage_mb=(start_memory + end_memory) / 2,
                    cpu_usage_percent=(start_cpu + end_cpu) / 2
                )
                
                # 存储指标（异步）
                if hasattr(args[0], 'async_executor'):
                    asyncio.create_task(args[0].async_executor.track_performance(metrics))
                
                return result
            except Exception as e:
                # 错误情况下的指标
                end_time = time.time()
                metrics = PerformanceMetrics(
                    request_id=request_id,
                    endpoint=func.__name__,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(e)
                )
                raise e
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            request_id = f"{func.__name__}_{int(time.time() * 1000)}"
            start_time = time.time()
            
            try:
                # 获取资源使用情况
                import psutil
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                start_cpu = process.cpu_percent()
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 计算指标
                end_time = time.time()
                end_memory = process.memory_info().rss / 1024 / 1024
                end_cpu = process.cpu_percent()
                
                metrics = PerformanceMetrics(
                    request_id=request_id,
                    endpoint=func.__name__,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    memory_usage_mb=(start_memory + end_memory) / 2,
                    cpu_usage_percent=(start_cpu + end_cpu) / 2
                )
                
                # 存储指标（异步）
                if len(args) > 0 and hasattr(args[0], 'async_executor'):
                    asyncio.create_task(args[0].async_executor.track_performance(metrics))
                
                return result
            except Exception as e:
                # 错误情况下的指标
                end_time = time.time()
                metrics = PerformanceMetrics(
                    request_id=request_id,
                    endpoint=func.__name__,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=end_time - start_time,
                    memory_usage_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(e)
                )
                raise e
        return sync_wrapper


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, connection_pool: ConnectionPoolManager):
        self.pool = connection_pool
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询并优化"""
        start_time = time.time()
        
        try:
            mysql_pool = await self.pool.get_mysql()
            if not mysql_pool:
                return []
            
            async with mysql_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params or ())
                    result = await cur.fetchall()
                    
                    # 记录查询性能
                    query_time = time.time() - start_time
                    if query_time > 1.0:  # 超过1秒的查询记录警告
                        logger.warning(f"慢查询: {query[:100]}... 耗时: {query_time:.2f}s")
                    
                    return result
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return []
    
    async def batch_insert(self, table: str, data: List[Dict]) -> bool:
        """批量插入优化"""
        if not data:
            return False
        
        # 分批插入，每批100条
        batch_size = 100
        success = True
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            if not await self._insert_batch(table, batch):
                success = False
        
        return success
    
    async def _insert_batch(self, table: str, batch: List[Dict]) -> bool:
        """执行批量插入"""
        if not batch:
            return True
        
        columns = list(batch[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)
        
        values = []
        for item in batch:
            values.append(tuple(item[col] for col in columns))
        
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        
        try:
            mysql_pool = await self.pool.get_mysql()
            if not mysql_pool:
                return False
            
            async with mysql_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.executemany(query, values)
                    await conn.commit()
                    return True
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return False


async def main():
    """测试函数"""
    print("=" * 80)
    print("性能优化模块测试")
    print("=" * 80)
    
    # 创建异步执行器
    async_executor = AsyncExecutor()
    
    # 测试异步扫描
    print("\n1. 测试异步扫描:")
    result = await async_executor.execute_scan_async("example.com")
    print(f"   目标: {result['target']}")
    print(f"   执行时间: {result['execution_time']:.2f}s")
    print(f"   成功工具: {result['performance']['successful_tools']}/{result['performance']['total_tools']}")
    print(f"   风险等级: {result['analysis']['risk_level']}")
    
    # 测试性能监控
    print("\n2. 测试性能监控:")
    
    @performance_monitor
    async def test_function():
        await asyncio.sleep(0.1)
        return "test_result"
    
    result = await test_function()
    print(f"   函数执行结果: {result}")
    
    # 测试性能报告
    print("\n3. 测试性能报告:")
    report = async_executor.get_performance_report()
    print(f"   总请求数: {report.get('total_requests', 0)}")
    print(f"   平均执行时间: {report.get('avg_execution_time', 0):.2f}s")
    
    print("\n" + "=" * 80)
    
    # 清理
    await async_executor.connection_pool.close_all()


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())