# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
ClawAI API性能分析和优化工具
识别性能瓶颈，提供优化建议，实施缓存策略
"""

import time
import requests
import json
import sys
import os
import statistics
from typing import Dict, List, Any, Tuple
import concurrent.futures
import threading
from dataclasses import dataclass
from datetime import datetime
import sqlite3
from pathlib import Path

@dataclass
class APIPerformanceMetrics:
    """API性能指标"""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    success: bool
    timestamp: float
    payload_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "response_time": self.response_time,
            "status_code": self.status_code,
            "success": self.success,
            "timestamp": self.timestamp,
            "payload_size": self.payload_size
        }

class APIPerformanceAnalyzer:
    """API性能分析器"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.metrics: List[APIPerformanceMetrics] = []
        self.lock = threading.Lock()
        
        # 初始化数据库
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "api_performance.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化性能数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建性能指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                response_time REAL NOT NULL,
                status_code INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                payload_size INTEGER DEFAULT 0
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_endpoint ON api_performance(endpoint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON api_performance(timestamp)')
        
        conn.commit()
        conn.close()
    
    def save_metrics(self, metrics: APIPerformanceMetrics):
        """保存性能指标到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_performance (endpoint, method, response_time, status_code, success, payload_size)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            metrics.endpoint,
            metrics.method,
            metrics.response_time,
            metrics.status_code,
            metrics.success,
            metrics.payload_size
        ))
        
        conn.commit()
        conn.close()
        
        with self.lock:
            self.metrics.append(metrics)
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict = None, 
                     headers: Dict = None) -> APIPerformanceMetrics:
        """测试单个API端点"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.request(method, url, json=data, headers=headers, timeout=30)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 计算响应大小
            payload_size = len(response.content) if response.content else 0
            
            metrics = APIPerformanceMetrics(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=response.status_code,
                success=200 <= response.status_code < 300,
                timestamp=time.time(),
                payload_size=payload_size
            )
            
            self.save_metrics(metrics)
            return metrics
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            metrics = APIPerformanceMetrics(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=0,
                success=False,
                timestamp=time.time(),
                payload_size=0
            )
            
            self.save_metrics(metrics)
            return metrics
    
    def test_endpoints_concurrently(self, endpoints: List[Tuple[str, str, Dict]], 
                                   max_workers: int = 5) -> List[APIPerformanceMetrics]:
        """并发测试多个API端点"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_endpoint = {}
            
            for endpoint_info in endpoints:
                if len(endpoint_info) == 2:
                    endpoint, method = endpoint_info
                    data = None
                else:
                    endpoint, method, data = endpoint_info
                
                future = executor.submit(self.test_endpoint, endpoint, method, data)
                future_to_endpoint[future] = (endpoint, method)
            
            for future in concurrent.futures.as_completed(future_to_endpoint):
                endpoint, method = future_to_endpoint[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"测试 {endpoint} 失败: {e}")
        
        return results
    
    def analyze_endpoint_performance(self, endpoint: str, hours: int = 24) -> Dict[str, Any]:
        """分析单个端点的性能数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查询最近N小时的数据
        cursor.execute('''
            SELECT response_time, status_code, success, payload_size, timestamp
            FROM api_performance
            WHERE endpoint = ? 
            AND timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
        ''', (endpoint, f'-{hours} hours'))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                "endpoint": endpoint,
                "total_requests": 0,
                "error": "无历史数据"
            }
        
        response_times = [row[0] for row in rows]
        status_codes = [row[1] for row in rows]
        successes = [row[2] for row in rows]
        payload_sizes = [row[3] for row in rows]
        
        total_requests = len(rows)
        successful_requests = sum(successes)
        error_requests = total_requests - successful_requests
        
        analysis = {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_requests": error_requests,
            "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
            "response_time": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times) if response_times else 0,
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0
            },
            "payload_size": {
                "min": min(payload_sizes) if payload_sizes else 0,
                "max": max(payload_sizes) if payload_sizes else 0,
                "avg": statistics.mean(payload_sizes) if payload_sizes else 0,
                "total": sum(payload_sizes) if payload_sizes else 0
            },
            "status_code_distribution": {},
            "recommendations": []
        }
        
        # 状态码分布
        from collections import Counter
        status_counter = Counter(status_codes)
        analysis["status_code_distribution"] = dict(status_counter)
        
        # 生成优化建议
        avg_response_time = analysis["response_time"]["avg"]
        success_rate = analysis["success_rate"]
        
        if avg_response_time > 5.0:
            analysis["recommendations"].append({
                "type": "performance",
                "priority": "high",
                "message": f"响应时间过长 ({avg_response_time:.2f}s)，建议添加缓存或优化处理逻辑",
                "suggestions": [
                    "实现结果缓存机制",
                    "将长耗时操作改为异步任务",
                    "优化数据库查询",
                    "添加请求限流"
                ]
            })
        elif avg_response_time > 2.0:
            analysis["recommendations"].append({
                "type": "performance",
                "priority": "medium",
                "message": f"响应时间较慢 ({avg_response_time:.2f}s)，建议优化",
                "suggestions": [
                    "添加基础缓存",
                    "优化资源加载",
                    "减少不必要的计算"
                ]
            })
        
        if success_rate < 90.0:
            analysis["recommendations"].append({
                "type": "reliability",
                "priority": "high",
                "message": f"成功率较低 ({success_rate:.1f}%)，需要检查错误原因",
                "suggestions": [
                    "检查依赖服务状态",
                    "优化错误处理和重试机制",
                    "添加健康检查和熔断器"
                ]
            })
        
        # 检查响应时间波动
        if analysis["response_time"]["std_dev"] > avg_response_time * 0.5:
            analysis["recommendations"].append({
                "type": "consistency",
                "priority": "medium",
                "message": "响应时间波动较大，可能存在资源竞争或不稳定依赖",
                "suggestions": [
                    "添加资源池管理",
                    "优化并发控制",
                    "监控外部服务响应时间"
                ]
            })
        
        return analysis
    
    def analyze_all_endpoints(self, hours: int = 24) -> Dict[str, Any]:
        """分析所有端点的性能"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有唯一的端点
        cursor.execute('''
            SELECT DISTINCT endpoint 
            FROM api_performance
            WHERE timestamp >= datetime('now', ?)
        ''', (f'-{hours} hours',))
        
        endpoints = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        overall_analysis = {
            "timestamp": datetime.now().isoformat(),
            "analysis_period_hours": hours,
            "total_endpoints": len(endpoints),
            "endpoints": {},
            "overall_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "avg_response_time": 0,
                "slow_endpoints": [],
                "error_endpoints": []
            },
            "recommendations": []
        }
        
        endpoint_analyses = []
        total_response_time = 0
        endpoint_count = 0
        
        for endpoint in endpoints:
            analysis = self.analyze_endpoint_performance(endpoint, hours)
            endpoint_analyses.append(analysis)
            
            overall_analysis["endpoints"][endpoint] = analysis
            
            # 更新总体指标
            overall_analysis["overall_metrics"]["total_requests"] += analysis["total_requests"]
            overall_analysis["overall_metrics"]["successful_requests"] += analysis["successful_requests"]
            
            if analysis["total_requests"] > 0:
                total_response_time += analysis["response_time"]["avg"] * analysis["total_requests"]
                endpoint_count += 1
            
            # 识别慢速端点
            if analysis["response_time"]["avg"] > 2.0:
                overall_analysis["overall_metrics"]["slow_endpoints"].append({
                    "endpoint": endpoint,
                    "avg_response_time": analysis["response_time"]["avg"],
                    "request_count": analysis["total_requests"]
                })
            
            # 识别错误率高的端点
            if analysis["success_rate"] < 90.0 and analysis["total_requests"] >= 10:
                overall_analysis["overall_metrics"]["error_endpoints"].append({
                    "endpoint": endpoint,
                    "success_rate": analysis["success_rate"],
                    "error_count": analysis["error_requests"]
                })
        
        # 计算平均响应时间
        if overall_analysis["overall_metrics"]["total_requests"] > 0:
            overall_analysis["overall_metrics"]["avg_response_time"] = (
                total_response_time / overall_analysis["overall_metrics"]["total_requests"]
            )
        
        # 生成总体建议
        avg_response_time = overall_analysis["overall_metrics"]["avg_response_time"]
        total_requests = overall_analysis["overall_metrics"]["total_requests"]
        
        if avg_response_time > 3.0:
            overall_analysis["recommendations"].append({
                "type": "overall_performance",
                "priority": "high",
                "message": f"系统平均响应时间过长 ({avg_response_time:.2f}s)，需要整体优化",
                "suggestions": [
                    "实施全局缓存策略",
                    "优化数据库架构和查询",
                    "添加CDN或反向代理缓存",
                    "实施API网关进行限流和缓存"
                ]
            })
        
        slow_endpoints = overall_analysis["overall_metrics"]["slow_endpoints"]
        if slow_endpoints:
            # 按响应时间排序
            slow_endpoints.sort(key=lambda x: x["avg_response_time"], reverse=True)
            
            overall_analysis["recommendations"].append({
                "type": "slow_endpoints",
                "priority": "high",
                "message": f"发现 {len(slow_endpoints)} 个慢速端点",
                "endpoints": slow_endpoints[:5],  # 显示最慢的5个
                "suggestions": [
                    "优先优化最慢的端点",
                    "为慢速端点添加专用缓存",
                    "考虑异步处理或任务队列"
                ]
            })
        
        error_endpoints = overall_analysis["overall_metrics"]["error_endpoints"]
        if error_endpoints:
            overall_analysis["recommendations"].append({
                "type": "error_endpoints",
                "priority": "high",
                "message": f"发现 {len(error_endpoints)} 个高错误率端点",
                "endpoints": error_endpoints,
                "suggestions": [
                    "检查错误日志，修复根本原因",
                    "添加重试机制和熔断器",
                    "实施优雅降级策略"
                ]
            })
        
        if total_requests > 1000:
            overall_analysis["recommendations"].append({
                "type": "scalability",
                "priority": "medium",
                "message": f"请求量较大 ({total_requests})，需要考虑扩展性",
                "suggestions": [
                    "实施负载均衡",
                    "添加数据库读写分离",
                    "考虑微服务架构拆分",
                    "实施消息队列异步处理"
                ]
            })
        
        return overall_analysis
    
    def run_comprehensive_test(self, test_scenarios: Dict[str, List] = None) -> Dict[str, Any]:
        """运行全面的API性能测试"""
        if test_scenarios is None:
            test_scenarios = {
                "basic": [
                    ("/health", "GET"),
                    ("/health/detailed", "GET"),
                    ("/api-docs", "GET"),
                    ("/health/security", "GET")
                ],
                "simulated_attack": [
                    ("/attack", "POST", {"target": "example.com", "use_real": False})
                ]
            }
        
        print("=" * 80)
        print("ClawAI API 全面性能测试")
        print("=" * 80)
        
        all_results = []
        
        for scenario_name, endpoints in test_scenarios.items():
            print(f"\n[统计] 测试场景: {scenario_name}")
            print("-" * 40)
            
            results = self.test_endpoints_concurrently(endpoints, max_workers=3)
            
            for result in results:
                status_icon = "[成功]" if result.success else "[失败]"
                print(f"  {status_icon} {result.endpoint}: {result.response_time:.3f}s (状态码: {result.status_code})")
                all_results.append(result)
            
            # 等待一会儿避免过载
            time.sleep(1)
        
        # 分析结果
        print("\n" + "=" * 80)
        print("性能分析报告")
        print("=" * 80)
        
        analysis = self.analyze_all_endpoints(hours=1)  # 分析最近1小时的数据
        
        # 显示摘要
        overall = analysis["overall_metrics"]
        print(f"\n[图表] 总体指标:")
        print(f"  总请求数: {overall['total_requests']}")
        print(f"  平均响应时间: {overall['avg_response_time']:.3f}s")
        
        if overall["slow_endpoints"]:
            print(f"\n[慢速] 慢速端点 (>{analysis.get('slow_threshold', 2.0)}s):")
            for endpoint in overall["slow_endpoints"][:3]:  # 显示最慢的3个
                print(f"  [警告]  {endpoint['endpoint']}: {endpoint['avg_response_time']:.3f}s ({endpoint['request_count']}次请求)")
        
        if overall["error_endpoints"]:
            print(f"\n[失败] 高错误率端点 (<90%成功率):")
            for endpoint in overall["error_endpoints"]:
                print(f"  [警告]  {endpoint['endpoint']}: {endpoint['success_rate']:.1f}%成功率 ({endpoint['error_count']}次错误)")
        
        # 显示建议
        if analysis["recommendations"]:
            print(f"\n[建议] 优化建议:")
            for i, rec in enumerate(analysis["recommendations"], 1):
                priority_icon = "[高危]" if rec["priority"] == "high" else "[中危]" if rec["priority"] == "medium" else "[低危]"
                print(f"  {priority_icon} {rec['type']}: {rec['message']}")
                
                if "suggestions" in rec:
                    for suggestion in rec["suggestions"][:3]:  # 显示前3个建议
                        print(f"    • {suggestion}")
        
        # 保存详细报告
        report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(report_dir, f"api_performance_report_{timestamp}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n[报告] 详细报告已保存: {report_file}")
        
        return analysis

class ResultCache:
    """简单的内存缓存实现"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = default_ttl  # 默认5分钟
        self.lock = threading.Lock()
    
    def get(self, key: str):
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() < entry["expires_at"]:
                    return entry["value"]
                else:
                    # 过期，删除
                    del self.cache[key]
            return None
    
    def set(self, key: str, value, ttl: int = None):
        """设置缓存值"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            # 如果缓存已满，删除最旧的条目
            if len(self.cache) >= self.max_size:
                # 简单的LRU策略：删除第一个条目
                if self.cache:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
            
            self.cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
    
    def delete(self, key: str):
        """删除缓存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
    
    def stats(self):
        """获取缓存统计信息"""
        with self.lock:
            total_size = len(self.cache)
            now = time.time()
            expired_count = sum(1 for entry in self.cache.values() if now >= entry["expires_at"])
            
            return {
                "total_entries": total_size,
                "expired_entries": expired_count,
                "max_size": self.max_size,
                "hit_ratio": "N/A"  # 需要记录命中率
            }

def create_api_cache_middleware():
    """创建API缓存中间件工厂函数"""
    cache = ResultCache(max_size=200, default_ttl=60)  # 默认1分钟TTL
    
    def cache_middleware(endpoint_func):
        """缓存装饰器"""
        def wrapper(*args, **kwargs):
            # 生成缓存键
            import hashlib
            import json
            
            # 基于函数名和参数生成缓存键
            cache_key_data = {
                "func": endpoint_func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            cache_key = hashlib.md5(
                json.dumps(cache_key_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                # 标记为缓存命中
                if isinstance(cached_result, dict):
                    cached_result["_cache"] = {
                        "hit": True,
                        "cached_at": cache.cache[cache_key]["created_at"]
                    }
                return cached_result
            
            # 执行原始函数
            result = endpoint_func(*args, **kwargs)
            
            # 缓存结果（只缓存成功响应）
            if isinstance(result, tuple) and len(result) == 2:
                response, status_code = result
                if 200 <= status_code < 300:
                    cache.set(cache_key, result, ttl=300)  # 5分钟TTL
            elif isinstance(result, dict):
                cache.set(cache_key, result, ttl=300)
            
            # 标记为缓存未命中
            if isinstance(result, dict):
                result["_cache"] = {"hit": False}
            
            return result
        
        return wrapper
    
    return cache_middleware, cache

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClawAI API性能分析工具")
    parser.add_argument("--base-url", default="http://localhost:5000", help="API基础URL")
    parser.add_argument("--analyze", action="store_true", help="分析历史性能数据")
    parser.add_argument("--test", action="store_true", help="运行性能测试")
    parser.add_argument("--hours", type=int, default=24, help="分析数据的时间范围（小时）")
    parser.add_argument("--endpoint", help="分析特定端点")
    
    args = parser.parse_args()
    
    analyzer = APIPerformanceAnalyzer(base_url=args.base_url)
    
    if args.analyze:
        if args.endpoint:
            analysis = analyzer.analyze_endpoint_performance(args.endpoint, args.hours)
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            analysis = analyzer.analyze_all_endpoints(args.hours)
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    elif args.test:
        analyzer.run_comprehensive_test()
    
    else:
        # 默认运行测试和分析
        print("运行API性能测试和分析...")
        analyzer.run_comprehensive_test()
        
        # 显示历史分析
        print("\n" + "=" * 80)
        print("历史性能分析（最近24小时）")
        print("=" * 80)
        
        analysis = analyzer.analyze_all_endpoints(hours=24)
        overall = analysis["overall_metrics"]
        
        print(f"\n[统计] 总体性能:")
        print(f"  平均响应时间: {overall['avg_response_time']:.3f}s")
        print(f"  总请求数: {overall['total_requests']}")
        
        if overall["slow_endpoints"]:
            print(f"\n[慢速] 需要优化的慢速端点:")
            for endpoint in overall["slow_endpoints"][:5]:
                print(f"  • {endpoint['endpoint']}: {endpoint['avg_response_time']:.3f}s")
        
        print(f"\n[建议] 关键建议:")
        for rec in analysis["recommendations"][:3]:
            print(f"  • {rec['message']}")

if __name__ == "__main__":
    main()