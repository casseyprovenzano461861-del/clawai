# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
性能基准测试脚本
用于测试ClawAI生产环境的性能指标
"""

import asyncio
import time
import statistics
import psutil
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    async def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("🚀 开始性能基准测试...")
        print("=" * 60)
        
        self.start_time = time.time()
        
        try:
            # 运行所有基准测试
            self.results = {
                "timestamp": datetime.now().isoformat(),
                "system_info": self.get_system_info(),
                "memory_test": await self.test_memory_usage(),
                "cpu_test": await self.test_cpu_performance(),
                "disk_test": await self.test_disk_performance(),
                "network_test": await self.test_network_performance(),
                "ai_response_test": await self.test_ai_response(),
                "tool_execution_test": await self.test_tool_execution(),
                "concurrent_requests_test": await self.test_concurrent_requests(),
                "database_operations_test": await self.test_database_operations(),
            }
            
            # 计算总体评分
            self.results["overall_score"] = self.calculate_overall_score()
            self.results["recommendations"] = self.generate_recommendations()
            
            self.end_time = time.time()
            self.results["execution_time"] = self.end_time - self.start_time
            
            return self.results
            
        except Exception as e:
            print(f"[失败] 基准测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        print("[搜索] 收集系统信息...")
        
        info = {
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "total_disk_gb": round(psutil.disk_usage('/').total / (1024**3), 2) if sys.platform != 'win32' else round(psutil.disk_usage('C:\\').total / (1024**3), 2),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }
        
        return info
    
    async def test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用情况"""
        print("🧠 测试内存使用...")
        
        results = []
        
        # 测试内存分配和释放
        for i in range(5):
            start_mem = psutil.Process().memory_info().rss
            
            # 分配一些内存
            test_data = [bytearray(1024 * 1024) for _ in range(10)]  # 10MB
            
            mid_mem = psutil.Process().memory_info().rss
            
            # 释放内存
            del test_data
            
            end_mem = psutil.Process().memory_info().rss
            
            results.append({
                "iteration": i + 1,
                "start_memory_mb": round(start_mem / (1024**2), 2),
                "peak_memory_mb": round(mid_mem / (1024**2), 2),
                "end_memory_mb": round(end_mem / (1024**2), 2),
                "memory_leak_mb": round((end_mem - start_mem) / (1024**2), 2),
            })
        
        avg_memory_leak = statistics.mean([r["memory_leak_mb"] for r in results])
        
        return {
            "iterations": results,
            "avg_memory_leak_mb": round(avg_memory_leak, 2),
            "score": max(0, 100 - avg_memory_leak * 10),  # 每1MB内存泄漏扣10分
            "status": "good" if avg_memory_leak < 1 else "warning" if avg_memory_leak < 5 else "poor"
        }
    
    async def test_cpu_performance(self) -> Dict[str, Any]:
        """测试CPU性能"""
        print("⚡ 测试CPU性能...")
        
        results = []
        
        # 测试计算性能
        for i in range(3):
            start_time = time.time()
            
            # 执行一些CPU密集型计算
            total = 0
            for j in range(1000000):
                total += j * j
            
            end_time = time.time()
            duration = end_time - start_time
            
            results.append({
                "iteration": i + 1,
                "duration_seconds": round(duration, 3),
                "operations_per_second": round(1000000 / duration, 0)
            })
        
        avg_duration = statistics.mean([r["duration_seconds"] for r in results])
        
        return {
            "iterations": results,
            "avg_duration_seconds": round(avg_duration, 3),
            "avg_ops_per_second": round(1000000 / avg_duration, 0),
            "score": min(100, max(0, 100 - (avg_duration - 0.1) * 100)),  # 基准0.1秒
            "status": "good" if avg_duration < 0.2 else "warning" if avg_duration < 0.5 else "poor"
        }
    
    async def test_disk_performance(self) -> Dict[str, Any]:
        """测试磁盘性能"""
        print("💾 测试磁盘性能...")
        
        results = []
        test_file = Path("benchmark_temp_file.bin")
        
        try:
            for i in range(3):
                # 写入测试
                start_write = time.time()
                
                with open(test_file, 'wb') as f:
                    # 写入10MB数据
                    f.write(b'0' * 10 * 1024 * 1024)
                
                write_time = time.time() - start_write
                write_speed = (10 * 1024 * 1024) / write_time / (1024**2)  # MB/s
                
                # 读取测试
                start_read = time.time()
                
                with open(test_file, 'rb') as f:
                    data = f.read()
                
                read_time = time.time() - start_read
                read_speed = (10 * 1024 * 1024) / read_time / (1024**2)  # MB/s
                
                results.append({
                    "iteration": i + 1,
                    "write_speed_mbps": round(write_speed, 2),
                    "read_speed_mbps": round(read_speed, 2),
                    "write_time_seconds": round(write_time, 3),
                    "read_time_seconds": round(read_time, 3),
                })
            
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
            
            avg_write_speed = statistics.mean([r["write_speed_mbps"] for r in results])
            avg_read_speed = statistics.mean([r["read_speed_mbps"] for r in results])
            
            return {
                "iterations": results,
                "avg_write_speed_mbps": round(avg_write_speed, 2),
                "avg_read_speed_mbps": round(avg_read_speed, 2),
                "score": min(100, max(0, (avg_write_speed + avg_read_speed) / 2)),  # 每1MB/s得1分，最高100分
                "status": "good" if avg_write_speed > 50 and avg_read_speed > 50 else "warning" if avg_write_speed > 20 and avg_read_speed > 20 else "poor"
            }
            
        except Exception as e:
            print(f"[警告]  磁盘测试失败: {e}")
            return {
                "error": str(e),
                "score": 0,
                "status": "failed"
            }
    
    async def test_network_performance(self) -> Dict[str, Any]:
        """测试网络性能"""
        print("🌐 测试网络性能...")
        
        import socket
        import urllib.request
        import urllib.error
        
        results = []
        
        try:
            # 测试本地连接
            start_local = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            try:
                sock.connect(('localhost', 5000))
                local_success = True
            except:
                local_success = False
            finally:
                sock.close()
            
            local_time = time.time() - start_local
            
            # 测试外部连接（Google DNS）
            start_external = time.time()
            try:
                urllib.request.urlopen('https://8.8.8.8', timeout=3)
                external_success = True
            except:
                external_success = False
            
            external_time = time.time() - start_external
            
            results.append({
                "local_connection_success": local_success,
                "local_connection_time_seconds": round(local_time, 3),
                "external_connection_success": external_success,
                "external_connection_time_seconds": round(external_time, 3),
            })
            
            score = 0
            if local_success:
                score += 30
                if local_time < 0.1:
                    score += 20
                elif local_time < 0.5:
                    score += 10
            
            if external_success:
                score += 30
                if external_time < 0.5:
                    score += 20
                elif external_time < 1.0:
                    score += 10
            
            return {
                "results": results,
                "score": score,
                "status": "good" if score >= 80 else "warning" if score >= 50 else "poor"
            }
            
        except Exception as e:
            print(f"[警告]  网络测试失败: {e}")
            return {
                "error": str(e),
                "score": 0,
                "status": "failed"
            }
    
    async def test_ai_response(self) -> Dict[str, Any]:
        """测试AI响应时间"""
        print("🤖 测试AI响应时间...")
        
        results = []
        
        try:
            # 尝试导入AI编排器
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from backend.ai_core.enhanced_llm_orchestrator import EnhancedLLMOrchestrator
            
            orchestrator = EnhancedLLMOrchestrator(mode="rule_only")  # 使用规则引擎模式进行测试
            
            test_prompts = [
                {"target": "example.com", "prompt": "分析目标的安全状况"},
                {"target": "test.local", "prompt": "规划攻击路径"},
                {"target": "demo.site", "prompt": "评估漏洞风险"},
            ]
            
            for i, test_data in enumerate(test_prompts):
                start_time = time.time()
                
                try:
                    result = orchestrator.analyze_target({
                        "target": test_data["target"],
                        "scan_time": datetime.now().isoformat(),
                        "nmap": {"ports": [{"port": 80, "service": "HTTP", "state": "open"}]}
                    })
                    
                    response_time = time.time() - start_time
                    success = "analysis" in result or "error" not in result
                    
                    results.append({
                        "iteration": i + 1,
                        "prompt": test_data["prompt"],
                        "response_time_seconds": round(response_time, 3),
                        "success": success,
                        "model_used": result.get("model_used", "unknown"),
                    })
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    results.append({
                        "iteration": i + 1,
                        "prompt": test_data["prompt"],
                        "response_time_seconds": round(response_time, 3),
                        "success": False,
                        "error": str(e),
                    })
            
            if results:
                success_rate = sum(1 for r in results if r["success"]) / len(results)
                avg_response_time = statistics.mean([r["response_time_seconds"] for r in results if r.get("success", False)]) if any(r.get("success", False) for r in results) else 0
                
                score = 0
                if success_rate > 0.8:
                    score += 50
                elif success_rate > 0.5:
                    score += 30
                
                if avg_response_time > 0:
                    if avg_response_time < 0.5:
                        score += 50
                    elif avg_response_time < 1.0:
                        score += 30
                    elif avg_response_time < 2.0:
                        score += 20
                
                return {
                    "iterations": results,
                    "success_rate": round(success_rate, 2),
                    "avg_response_time_seconds": round(avg_response_time, 3),
                    "score": min(100, score),
                    "status": "good" if score >= 80 else "warning" if score >= 50 else "poor"
                }
            else:
                return {
                    "error": "No results generated",
                    "score": 0,
                    "status": "failed"
                }
                
        except Exception as e:
            print(f"[警告]  AI响应测试失败: {e}")
            return {
                "error": str(e),
                "score": 0,
                "status": "failed"
            }
    
    async def test_tool_execution(self) -> Dict[str, Any]:
        """测试工具执行性能"""
        print("🛠️ 测试工具执行性能...")
        
        results = []
        
        try:
            # 模拟工具执行测试
            test_tools = [
                {"name": "nmap_simulation", "simulated_time": 0.5},
                {"name": "whatweb_simulation", "simulated_time": 0.3},
                {"name": "nuclei_simulation", "simulated_time": 0.8},
            ]
            
            for i, tool in enumerate(test_tools):
                start_time = time.time()
                
                # 模拟工具执行
                await asyncio.sleep(tool["simulated_time"])
                
                execution_time = time.time() - start_time
                
                results.append({
                    "iteration": i + 1,
                    "tool_name": tool["name"],
                    "execution_time_seconds": round(execution_time, 3),
                    "simulated_time_seconds": tool["simulated_time"],
                    "accuracy": round(tool["simulated_time"] / execution_time, 2) if execution_time > 0 else 0,
                })
            
            avg_execution_time = statistics.mean([r["execution_time_seconds"] for r in results])
            avg_accuracy = statistics.mean([r["accuracy"] for r in results])
            
            score = min(100, max(0, 100 - (avg_execution_time - 0.5) * 50))  # 基准0.5秒
            
            return {
                "iterations": results,
                "avg_execution_time_seconds": round(avg_execution_time, 3),
                "avg_accuracy": round(avg_accuracy, 2),
                "score": round(score, 1),
                "status": "good" if score >= 80 else "warning" if score >= 50 else "poor"
            }
            
        except Exception as e:
            print(f"[警告]  工具执行测试失败: {e}")
            return {
                "error": str(e),
                "score": 0,
                "status": "failed"
            }
    
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """测试并发请求处理能力"""
        print("⚡ 测试并发请求处理...")
        
        results = []
        
        async def mock_request(request_id: int, delay: float = 0.1):
            """模拟请求处理"""
            start_time = time.time()
            await asyncio.sleep(delay)  # 模拟处理时间
            processing_time = time.time() - start_time
            
            return {
                "request_id": request_id,
                "processing_time_seconds": round(processing_time, 3),
                "success": True
            }
        
        try:
            # 测试不同并发级别
            concurrency_levels = [1, 5, 10, 20]
            
            for level in concurrency_levels:
                start_time = time.time()
                
                # 创建并发任务
                tasks = [mock_request(i, 0.1) for i in range(level)]
                responses = await asyncio.gather(*tasks)
                
                total_time = time.time() - start_time
                
                success_count = sum(1 for r in responses if r["success"])
                avg_processing_time = statistics.mean([r["processing_time_seconds"] for r in responses])
                
                results.append({
                    "concurrency_level": level,
                    "total_time_seconds": round(total_time, 3),
                    "success_rate": round(success_count / level, 2),
                    "avg_processing_time_seconds": round(avg_processing_time, 3),
                    "requests_per_second": round(level / total_time, 1) if total_time > 0 else 0,
                })
            
            # 计算评分
            best_rps = max(r["requests_per_second"] for r in results)
            score = min(100, best_rps * 2)  # 每RPS得2分，最高100分
            
            return {
                "concurrency_tests": results,
                "max_requests_per_second": round(best_rps, 1),
                "score": round(score, 1),
                "status": "good" if score >= 80 else "warning" if score >= 50 else "poor"
            }
            
        except Exception as e:
            print(f"[警告]  并发请求测试失败: {e}")
            return {
                "error": str(e),
                "score": 0,
                "status": "failed"
            }
    
    async def test_database_operations(self) -> Dict[str, Any]:
        """测试数据库操作性能"""
        print("🗃️ 测试数据库操作性能...")
        
        results = []
        
        try:
            import sqlite3
            import tempfile
            
            # 创建临时数据库进行测试
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
                db_path = tmp.name
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 创建测试表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS benchmark_test (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 测试插入性能
            insert_times = []
            for i in range(100):
                start_time = time.time()
                cursor.execute("INSERT INTO benchmark_test (data) VALUES (?)", (f"test_data_{i}",))
                insert_times.append(time.time() - start_time)
            
            conn.commit()
            
            # 测试查询性能
            query_times = []
            for i in range(10):
                start_time = time.time()
                cursor.execute("SELECT * FROM benchmark_test WHERE data LIKE ?", (f"%test_data_{i}%",))
                cursor.fetchall()
                query_times.append(time.time() - start_time)
            
            # 测试更新性能
            update_times = []
            for i in range(10):
                start_time = time.time()
                cursor.execute("UPDATE benchmark_test SET data = ? WHERE id = ?", (f"updated_data_{i}", i+1))
                update_times.append(time.time() - start_time)
            
            conn.commit()
            conn.close()
            
            # 清理临时文件
            import os
            os.unlink(db_path)
            
            results.append({
                "avg_insert_time_ms": round(statistics.mean(insert_times) * 1000, 2),
                "avg_query_time_ms": round(statistics.mean(query_times) * 1000, 2),
                "avg_update_time_ms": round(statistics.mean(update_times) * 1000, 2),
                "inserts_per_second": round(1 / statistics.mean(insert_times), 0),
                "queries_per_second": round(1 / statistics.mean(query_times), 0),
            })
            
            # 计算评分（基于操作速度）
            avg_op_time_ms = statistics.mean([
                statistics.mean(insert_times) * 1000,
                statistics.mean(query_times) * 1000,
                statistics.mean(update_times) * 1000
            ])
            
            score = max(0, 100 - avg_op_time_ms)  # 每1ms扣1分
            
            return {
                "operations": results,
                "avg_operation_time_ms": round(avg_op_time_ms, 2),
                "score": round(score, 1),
                "status": "good" if score >= 80 else "warning" if score >= 50 else "poor"
            }
            
        except Exception as e:
            print(f"[警告]  数据库操作测试失败: {e}")
            return {
                "error": str(e),
                "score": 0,
                "status": "failed"
            }
    
    def calculate_overall_score(self) -> Dict[str, Any]:
        """计算总体评分"""
        scores = {}
        weights = {
            "memory_test": 0.1,
            "cpu_test": 0.15,
            "disk_test": 0.1,
            "network_test": 0.1,
            "ai_response_test": 0.2,
            "tool_execution_test": 0.15,
            "concurrent_requests_test": 0.1,
            "database_operations_test": 0.1,
        }
        
        total_weighted_score = 0
        total_weight = 0
        
        for test_name, weight in weights.items():
            if test_name in self.results and "score" in self.results[test_name]:
                score = self.results[test_name]["score"]
                scores[test_name] = {
                    "score": score,
                    "weight": weight,
                    "weighted_score": score * weight,
                    "status": self.results[test_name].get("status", "unknown")
                }
                total_weighted_score += score * weight
                total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        return {
            "component_scores": scores,
            "overall_score": round(overall_score, 1),
            "grade": self._get_grade(overall_score),
            "status": "good" if overall_score >= 80 else "warning" if overall_score >= 60 else "poor"
        }
    
    def _get_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "F"
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 检查各组件性能
        overall_score = self.results.get("overall_score", {}).get("overall_score", 0)
        
        if overall_score < 60:
            recommendations.append("[警告]  系统性能较差，建议全面优化")
        
        # 检查具体组件
        for test_name, test_result in self.results.items():
            if isinstance(test_result, dict) and "status" in test_result:
                status = test_result["status"]
                score = test_result.get("score", 0)
                
                if status == "poor" or score < 50:
                    if test_name == "memory_test":
                        recommendations.append("[建议] 内存使用需要优化，检查内存泄漏")
                    elif test_name == "cpu_test":
                        recommendations.append("[建议] CPU性能较低，考虑优化算法或升级硬件")
                    elif test_name == "disk_test":
                        recommendations.append("[建议] 磁盘I/O较慢，考虑使用SSD或优化文件操作")
                    elif test_name == "network_test":
                        recommendations.append("[建议] 网络连接有问题，检查网络配置")
                    elif test_name == "ai_response_test":
                        recommendations.append("[建议] AI响应时间较长，考虑使用缓存或优化模型")
                    elif test_name == "tool_execution_test":
                        recommendations.append("[建议] 工具执行效率低，优化工具调用流程")
                    elif test_name == "concurrent_requests_test":
                        recommendations.append("[建议] 并发处理能力不足，考虑增加工作线程或优化异步处理")
                    elif test_name == "database_operations_test":
                        recommendations.append("[建议] 数据库操作较慢，优化查询或考虑使用索引")
        
        # 根据总体评分添加建议
        if overall_score >= 80:
            recommendations.append("[成功] 系统性能良好，继续保持")
        elif overall_score >= 60:
            recommendations.append("[图表] 系统性能可接受，但有优化空间")
        
        # 通用建议
        recommendations.append("[统计] 定期运行性能测试监控系统状态")
        recommendations.append("🔧 根据测试结果针对性优化瓶颈组件")
        
        return recommendations
    
    def save_report(self, output_dir: str = "reports") -> str:
        """保存测试报告"""
        report_dir = Path(output_dir)
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"performance_benchmark_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return str(report_file)
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("[统计] 性能基准测试摘要")
        print("=" * 60)
        
        overall = self.results.get("overall_score", {})
        
        if "overall_score" in overall:
            print(f"🏆 总体评分: {overall['overall_score']} / 100 ({overall.get('grade', 'N/A')})")
            print(f"[图表] 总体状态: {overall.get('status', 'unknown')}")
        
        print(f"⏱️  测试耗时: {self.results.get('execution_time', 0):.2f} 秒")
        
        print("\n[列表] 组件性能:")
        for test_name, test_result in self.results.items():
            if isinstance(test_result, dict) and "score" in test_result and test_name != "overall_score":
                status = test_result.get("status", "unknown")
                score = test_result.get("score", 0)
                print(f"  {test_name}: {score}/100 ({status})")
        
        print("\n[建议] 优化建议:")
        for recommendation in self.results.get("recommendations", []):
            print(f"  • {recommendation}")


async def main():
    """主函数"""
    print("🔧 ClawAI 性能基准测试工具")
    print("=" * 60)
    
    try:
        # 创建基准测试实例
        benchmark = PerformanceBenchmark()
        
        # 运行所有测试
        results = await benchmark.run_all_benchmarks()
        
        if results:
            # 打印摘要
            benchmark.print_summary()
            
            # 保存报告
            report_file = benchmark.save_report()
            print(f"\n[文档] 详细报告已保存到: {report_file}")
            
            # 返回成功
            return 0
        else:
            print("[失败] 基准测试失败")
            return 1
            
    except Exception as e:
        print(f"[失败] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 运行异步主函数
    exit_code = asyncio.run(main())
    sys.exit(exit_code)