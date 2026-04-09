# -*- coding: utf-8 -*-
"""
攻击服务
处理攻击链生成和扫描的业务逻辑
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.shared.exceptions import ValidationError, ExecutionError, ToolUnavailableError
try:
    from backend.tools.unified_executor import UnifiedToolExecutor
except ImportError:
    UnifiedToolExecutor = None
try:
    from backend.attack_chain.unified_attack_generator import UnifiedAttackGenerator
except ImportError:
    UnifiedAttackGenerator = None
from backend.workflow.exploit_post_closure import run_exploit_post_closure


class AttackService:
    """
    攻击服务类
    处理所有攻击相关的业务逻辑
    """
    
    def __init__(self):
        """初始化攻击服务"""
        # 初始化工具执行器
        self.tool_executor = UnifiedToolExecutor() if UnifiedToolExecutor else None
        
        # 初始化攻击链生成器
        # 使用统一攻击链生成器，包含 exploit/post 阶段
        self.attack_generator = UnifiedAttackGenerator(enable_evolution=True) if UnifiedAttackGenerator else None
        
        # 任务存储（实际项目中应该使用数据库或缓存）
        self.tasks: Dict[str, Dict[str, Any]] = {}
        
        # 历史记录存储
        self.history: List[Dict[str, Any]] = []
    
    def execute_attack(
        self,
        target: str,
        use_real: bool = True,
        scan_options: Optional[Dict[str, Any]] = None,
        username: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        执行攻击
        
        Args:
            target: 目标地址
            use_real: 是否使用真实执行
            scan_options: 扫描选项
            username: 用户名
            
        Returns:
            攻击结果
        """
        # 生成任务ID
        task_id = str(uuid.uuid4())[:8]
        
        # 验证目标
        self._validate_target(target)
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            if use_real:
                # 真实执行模式
                result = self._execute_real_attack(target, scan_options)
                execution_mode = "real"
            else:
                # 模拟模式
                result = self._execute_mock_attack(target)
                execution_mode = "mock"
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 构建响应
            response = {
                "task_id": task_id,
                "execution_mode": execution_mode,
                "message": "攻击执行完成",
                "requested_by": username,
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "execution_time": f"{execution_time:.2f}秒",
                **result
            }
            
            # 保存任务结果
            self.tasks[task_id] = {
                "status": "completed",
                "result": response,
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "username": username
            }
            
            # 添加到历史记录
            self._add_to_history(response, username)
            
            return response
            
        except Exception as e:
            # 记录错误
            error_time = time.time() - start_time
            
            # 构建错误响应
            error_response = {
                "task_id": task_id,
                "execution_mode": "error",
                "message": f"攻击执行失败: {str(e)}",
                "requested_by": username,
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "execution_time": f"{error_time:.2f}秒",
                "error": {
                    "type": e.__class__.__name__,
                    "message": str(e)
                }
            }
            
            # 保存错误任务
            self.tasks[task_id] = {
                "status": "failed",
                "result": error_response,
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "username": username,
                "error": str(e)
            }
            
            raise ExecutionError(
                message=f"攻击执行失败: {str(e)}",
                tool_name=None,
                execution_type="attack_execution",
                details={"target": target, "username": username}
            )
    
    def _execute_real_attack(
        self,
        target: str,
        scan_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行真实攻击
        
        Args:
            target: 目标地址
            scan_options: 扫描选项
            
        Returns:
            真实攻击结果
        """
        scan_options = scan_options or {}
        
        try:
            # 执行综合扫描
            if not self.tool_executor:
                raise ExecutionError("工具执行器不可用")
            scan_result = self.tool_executor.execute_comprehensive_scan(target)
            
            # 生成攻击链
            if not self.attack_generator:
                raise ExecutionError("攻击链生成器不可用")
            attack_chain_result = self.attack_generator.generate_attack_chain(scan_result)

            # 如果真实扫描 attack_chain 为空，降级到 mock 保证 UI 有数据展示
            if not attack_chain_result.get("attack_chain"):
                mock_result = self._execute_mock_attack(target)
                mock_result["execution_mode"] = "real_fallback_mock"
                mock_result["fallback_reason"] = "真实扫描未生成攻击链，降级到模拟数据"
                return mock_result

            # exploit/post 闭环（安全验证，不发起真实 payload）
            closure = run_exploit_post_closure(
                scan_results=scan_result,
                attack_chain=attack_chain_result.get("attack_chain", []),
                target=target,
                safe_validation=True,
            )
            
            # 分析执行统计
            execution_stats = self._analyze_execution_stats(scan_result)
            
            # 构建结果
            result = {
                "scan_results": scan_result,
                "attack_chain": attack_chain_result.get("attack_chain", []),
                "analysis": attack_chain_result.get("analysis", {}),
                "decision": attack_chain_result.get("decision", {}),
                "target_analysis": attack_chain_result.get("target_analysis", {}),
                "execution_summary": attack_chain_result.get("execution_summary", {}),
                "execution_stats": execution_stats,
                "exploit_post_execution": closure.get("exploit_post_execution", []),
                "closure_summary": closure.get("closure_summary", {}),
            }
            
            return result
            
        except Exception as e:
            # 真实执行失败，回退到模拟模式
            print(f"真实执行失败，回退到模拟模式: {str(e)}")
            return self._execute_mock_attack(target)
    
    def _execute_mock_attack(self, target: str) -> Dict[str, Any]:
        """
        执行模拟攻击
        
        Args:
            target: 目标地址
            
        Returns:
            模拟攻击结果
        """
        # 生成模拟扫描结果
        mock_scan_results = {
            "target": target,
            "execution_mode": "mock",
            "nmap": {
                "ports": [
                    {"port": 80, "service": "http", "state": "open"},
                    {"port": 443, "service": "https", "state": "open"},
                    {"port": 3306, "service": "mysql", "state": "open"}
                ]
            },
            "whatweb": {
                "fingerprint": {
                    "web_server": "nginx",
                    "language": ["PHP"],
                    "cms": ["WordPress"],
                    "other": ["jQuery"]
                }
            },
            "nuclei": {
                "vulnerabilities": [
                    {"name": "WordPress XSS", "severity": "medium"},
                    {"name": "Remote Code Execution", "severity": "critical"}
                ]
            },
            "wafw00f": {
                "waf_detected": False,
                "waf_type": None
            }
        }
        
        # 生成攻击链
        if self.attack_generator:
            attack_chain_result = self.attack_generator.generate_attack_chain(mock_scan_results)
        else:
            attack_chain_result = {"attack_chain": [], "analysis": {}}

        # exploit/post 闭环（安全验证，不发起真实 payload）
        closure = run_exploit_post_closure(
            scan_results=mock_scan_results,
            attack_chain=attack_chain_result.get("attack_chain", []),
            target=target,
            safe_validation=True,
        )
        
        # 构建结果
        result = {
            "scan_results": mock_scan_results,
            "attack_chain": attack_chain_result.get("attack_chain", []),
            "analysis": attack_chain_result.get("analysis", {}),
            "decision": attack_chain_result.get("decision", {}),
            "target_analysis": attack_chain_result.get("target_analysis", {}),
            "execution_summary": attack_chain_result.get("execution_summary", {}),
            "execution_stats": {
                "real_executions": 0,
                "simulated_executions": 4,
                "errors": 0,
                "warning": "使用模拟数据，真实工具可能未安装"
            },
            "exploit_post_execution": closure.get("exploit_post_execution", []),
            "closure_summary": closure.get("closure_summary", {}),
        }
        
        return result
    
    def execute_quick_scan(self, target: str) -> Dict[str, Any]:
        """
        执行快速扫描
        
        Args:
            target: 目标地址
            
        Returns:
            快速扫描结果
        """
        # 验证目标
        self._validate_target(target)
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            def unwrap(tool_metrics: Dict[str, Any]) -> Dict[str, Any]:
                out = tool_metrics.get("output")
                return out if isinstance(out, dict) else tool_metrics

            tool_real = True

            # nmap
            if self.tool_executor and self.tool_executor.available_tools.get("nmap", False):
                nmap_metrics = self.tool_executor.execute_tool(
                    "nmap",
                    target,
                    options={"ports": "80,443,8080,8443"},
                )
                nmap_result = unwrap(nmap_metrics)
                tool_real = str(nmap_metrics.get("execution_mode", "")).lower() == "real"
            else:
                nmap_result = {
                    "ports": [
                        {"port": 80, "service": "http", "state": "open"},
                        {"port": 443, "service": "https", "state": "open"},
                    ]
                }
                tool_real = False

            # whatweb（若有 Web 端口则尝试）
            web_services = [
                p for p in nmap_result.get("ports", [])
                if isinstance(p, dict) and str(p.get("state", "")).lower() == "open" and p.get("service") in ["http", "https"]
            ]
            if web_services and self.tool_executor and self.tool_executor.available_tools.get("whatweb", False):
                whatweb_metrics = self.tool_executor.execute_tool("whatweb", target)
                whatweb_result = unwrap(whatweb_metrics)
                tool_real = tool_real and (str(whatweb_metrics.get("execution_mode", "")).lower() == "real")
                execution_mode = "real" if tool_real else "mock"
                warning = None
            else:
                whatweb_result = {"fingerprint": {}, "error": "无Web服务或工具不可用"}
                execution_mode = "mock"
                warning = "whatweb工具不可用或未发现Web服务"

            result = {
                "execution_mode": execution_mode,
                "nmap": nmap_result,
                "whatweb": whatweb_result,
                "message": "快速扫描完成",
                "target": target,
            }
            if not tool_real:
                result["warning"] = warning or "使用模拟数据"

            execution_time = time.time() - start_time
            result["execution_time"] = f"{execution_time:.2f}秒"
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "execution_mode": "error",
                "message": f"快速扫描失败: {str(e)}",
                "target": target,
                "execution_time": f"{execution_time:.2f}秒",
                "error": str(e),
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态
        """
        task = self.tasks.get(task_id)
        
        if not task:
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "任务不存在"
            }
        
        return {
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "created_at": task.get("created_at"),
            "completed_at": task.get("completed_at"),
            "username": task.get("username"),
            "has_result": "result" in task
        }
    
    def get_attack_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取攻击历史
        
        Args:
            user_id: 用户ID（可选）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            攻击历史列表
        """
        # 过滤用户历史（如果指定了user_id）
        if user_id:
            user_history = [h for h in self.history if h.get("user_id") == user_id]
        else:
            user_history = self.history
        
        # 应用分页
        start_idx = offset
        end_idx = offset + limit
        paginated_history = user_history[start_idx:end_idx]
        
        # 简化历史记录
        simplified_history = []
        for record in paginated_history:
            simplified_history.append({
                "id": record.get("id"),
                "target": record.get("target"),
                "execution_mode": record.get("execution_mode"),
                "timestamp": record.get("timestamp"),
                "execution_time": record.get("execution_time"),
                "username": record.get("username"),
                "status": record.get("status", "completed")
            })
        
        return simplified_history
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        获取可用工具列表
        
        Returns:
            工具信息字典
        """
        try:
            return self.tool_executor.get_available_tools() if self.tool_executor else {}
        except Exception as e:
            # 如果获取失败，返回空字典
            return {}
    
    def _validate_target(self, target: str) -> None:
        """
        验证目标地址
        
        Args:
            target: 目标地址
            
        Raises:
            ValidationError: 如果目标地址无效
        """
        if not target or not isinstance(target, str):
            raise ValidationError("目标地址不能为空", field="target")
        
        if len(target) > 255:
            raise ValidationError("目标地址过长", field="target")
        
        # 基本格式检查
        target_lower = target.lower()
        if any(char in target for char in [';', '|', '&', '$', '`']):
            raise ValidationError("目标地址包含危险字符", field="target")
    
    def _analyze_execution_stats(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析执行统计
        
        Args:
            scan_result: 扫描结果
            
        Returns:
            执行统计
        """
        stats = {
            "real_executions": 0,
            "simulated_executions": 0,
            "errors": 0,
            "warnings": []
        }
        
        # 分析每个工具的结果
        for tool_name, result in scan_result.items():
            if isinstance(result, dict):
                execution_mode = result.get("execution_mode", "unknown")
                
                if execution_mode == "real":
                    stats["real_executions"] += 1
                elif execution_mode == "simulated":
                    stats["simulated_executions"] += 1
                
                if "error" in result:
                    stats["errors"] += 1
                    stats["warnings"].append(f"{tool_name}: {result.get('error')}")
        
        # 计算真实执行比例
        total_executions = stats["real_executions"] + stats["simulated_executions"]
        if total_executions > 0:
            real_execution_ratio = stats["real_executions"] / total_executions
            stats["real_execution_ratio"] = f"{real_execution_ratio:.1%}"
            
            if real_execution_ratio < 0.5:
                stats["warnings"].append("真实执行比例较低，建议安装缺失的工具")
        
        return stats
    
    def _add_to_history(self, attack_result: Dict[str, Any], username: str) -> None:
        """
        添加到历史记录
        
        Args:
            attack_result: 攻击结果
            username: 用户名
        """
        analysis = attack_result.get("analysis", {})
        if not isinstance(analysis, dict) and hasattr(analysis, "to_dict") and callable(getattr(analysis, "to_dict")):
            analysis = analysis.to_dict()
        if not isinstance(analysis, dict):
            analysis = {}

        history_record = {
            "id": str(uuid.uuid4())[:8],
            "target": attack_result.get("target"),
            "execution_mode": attack_result.get("execution_mode"),
            "timestamp": attack_result.get("timestamp"),
            "execution_time": attack_result.get("execution_time"),
            "username": username,
            "status": "completed",
            "result_summary": {
                "attack_chain_steps": len(attack_result.get("attack_chain", [])),
                "vulnerabilities_found": self._count_vulnerabilities_from_analysis(analysis),
                "risk_level": analysis.get("risk_level", "unknown"),
            }
        }
        
        self.history.append(history_record)
        
        # 限制历史记录数量
        if len(self.history) > 100:
            self.history = self.history[-100:]

    @staticmethod
    def _count_vulnerabilities_from_analysis(analysis: Dict[str, Any]) -> int:
        """
        兼容不同生成器的数据结构：
        - infrastructure 版本可能返回 vulnerabilities: List[...]
        - unified 版本可能返回 vulnerabilities: int
        """
        if not isinstance(analysis, dict):
            return 0
        val = analysis.get("vulnerabilities", 0)
        if isinstance(val, list):
            return len(val)
        if isinstance(val, int):
            return val
        return 0