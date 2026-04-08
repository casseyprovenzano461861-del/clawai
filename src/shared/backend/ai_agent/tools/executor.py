# -*- coding: utf-8 -*-
"""
工具执行桥接
连接 AI Agent 与现有工具系统
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str                              # 工具名称
    success: bool                               # 是否成功
    output: Dict[str, Any] = field(default_factory=dict)  # 输出数据
    error: Optional[str] = None                 # 错误信息
    execution_time: float = 0.0                 # 执行时间
    simulated: bool = False                     # 是否模拟执行
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "simulated": self.simulated,
            "timestamp": self.timestamp
        }


class ToolExecutionBridge:
    """工具执行桥接
    
    连接 AIAgentCore 与现有工具系统（UnifiedExecutor、ToolRegistry等）
    """
    
    def __init__(
        self,
        unified_executor=None,
        tool_registry=None,
        tool_manager=None,
        enable_simulation: bool = True,
        timeout: int = 300,
        prefer_real_execution: bool = True
    ):
        """初始化工具执行桥接
        
        Args:
            unified_executor: 统一执行器实例 (UnifiedExecutor)
            tool_registry: 工具注册表实例
            tool_manager: 工具管理器实例
            enable_simulation: 是否启用模拟执行（作为回退）
            timeout: 默认超时时间（秒）
            prefer_real_execution: 是否优先真实执行
        """
        self.unified_executor = unified_executor
        self.tool_registry = tool_registry
        self.tool_manager = tool_manager
        self.enable_simulation = enable_simulation
        self.timeout = timeout
        self.prefer_real_execution = prefer_real_execution
        
        # 线程池用于异步调用同步工具
        self._executor = ThreadPoolExecutor(max_workers=3)
        
        # 执行统计
        self.execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "simulated_calls": 0,
            "real_calls": 0,
            "total_time": 0.0
        }
        
        # AI 工具名称 -> UnifiedExecutor 工具名称映射
        self.tool_name_mapping = {
            "nmap_scan": "nmap",
            "whatweb_scan": "whatweb",
            "subfinder_scan": "subfinder",
            "dirsearch_scan": "dirsearch",
            "httpx_probe": "httpx",
            "nuclei_scan": "nuclei",
            "sqlmap_scan": "sqlmap",
            "nikto_scan": "nikto",
            "xsstrike_scan": "xsstrike",
            "wpscan": "wpscan",
            "hydra_brute": "hydra",
            "testssl_scan": "testssl",
            "masscan_scan": "masscan",
            "gobuster_scan": "gobuster",
            "ffuf_scan": "ffuf",
            "amass_scan": "amass",
        }
        
        # 渗透测试流程工具（不通过 UnifiedExecutor）
        self.workflow_tools = {
            "start_pentest": self._execute_start_pentest,
            "get_pentest_status": self._execute_get_pentest_status,
            "stop_pentest": self._execute_stop_pentest,
            "generate_report": self._execute_generate_report,
            "get_tool_status": self._execute_get_tool_status,
        }
        
        # P-E-R Agent 引用（用于自主模式）
        self._per_agent = None
        
        logger.info(f"工具执行桥接初始化完成, UnifiedExecutor: {unified_executor is not None}")
    
    def set_per_agent(self, per_agent):
        """设置 P-E-R Agent"""
        self._per_agent = per_agent
    
    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()
        self.execution_stats["total_calls"] += 1
        
        logger.info(f"执行工具: {tool_name}, 参数: {params}")
        
        try:
            # 1. 检查是否是流程工具
            if tool_name in self.workflow_tools:
                result = await self.workflow_tools[tool_name](params)
            # 2. 尝试通过 UnifiedExecutor 真实执行
            elif self.unified_executor and self.prefer_real_execution:
                result = await self._run_real_tool(tool_name, params)
            # 3. 回退到模拟执行
            elif self.enable_simulation:
                result = self._simulate_tool(tool_name, params)
            else:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error="工具不可用且模拟执行已禁用"
                )
            
            # 更新统计
            self.execution_stats["successful_calls"] += 1
            if result.simulated:
                self.execution_stats["simulated_calls"] += 1
            else:
                self.execution_stats["real_calls"] += 1
            
            logger.info(f"工具执行完成: {tool_name}, 成功: {result.success}, 模拟: {result.simulated}")
            
            return result
            
        except Exception as e:
            self.execution_stats["failed_calls"] += 1
            logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
        
        finally:
            self.execution_stats["total_time"] += time.time() - start_time
    
    async def _run_real_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """通过 UnifiedExecutor 运行真实工具"""
        import asyncio
        
        start_time = time.time()
        
        # 获取目标
        target = params.get("target") or params.get("domain") or params.get("url", "")
        if not target:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error="缺少目标参数 (target/domain/url)"
            )
        
        # 映射工具名称
        executor_tool_name = self.tool_name_mapping.get(tool_name, tool_name.replace("_scan", "").replace("_probe", ""))
        
        # 构建选项
        options = {}
        if "ports" in params:
            options["ports"] = params["ports"]
        if "scan_type" in params:
            options["scan_type"] = params["scan_type"]
        if "templates" in params:
            options["templates"] = params["templates"]
        if "severity" in params:
            options["severity"] = params["severity"]
        if "level" in params:
            options["level"] = params["level"]
        if "risk" in params:
            options["risk"] = params["risk"]
        if "extensions" in params:
            options["extensions"] = params["extensions"]
        if "service" in params:
            options["service"] = params["service"]
        if "enumerate" in params:
            options["enumerate"] = params["enumerate"]
        
        try:
            # UnifiedExecutor.execute_tool 是同步方法，需要在线程中运行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                lambda: self.unified_executor.execute_tool(executor_tool_name, target, options)
            )
            
            # 解析结果
            success = result.get("success", False) or result.get("status") in ["success", "simulated"]
            is_simulated = result.get("execution_mode") == "simulated" or result.get("status") == "simulated"
            output = result.get("output", result)
            error = result.get("error") or result.get("error_message")
            
            return ToolResult(
                tool_name=tool_name,
                success=success,
                output=output if isinstance(output, dict) else {"raw": output},
                error=error,
                execution_time=time.time() - start_time,
                simulated=is_simulated
            )
            
        except Exception as e:
            logger.error(f"UnifiedExecutor 执行失败: {e}")
            
            # 回退到模拟执行
            if self.enable_simulation:
                logger.info(f"回退到模拟执行: {tool_name}")
                return self._simulate_tool(tool_name, params)
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _simulate_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """统一的模拟执行入口"""
        target = params.get("target") or params.get("domain") or params.get("url", "")
        
        # 根据工具类型选择模拟方法
        if tool_name == "nmap_scan":
            return self._simulate_nmap(target, params.get("ports", ""), params.get("scan_type", "quick"))
        elif tool_name == "whatweb_scan":
            return self._simulate_whatweb(target)
        elif tool_name == "subfinder_scan":
            return self._simulate_subfinder(target)
        elif tool_name == "dirsearch_scan":
            return self._simulate_dirsearch(target, params.get("extensions", "php,html,js"))
        elif tool_name == "httpx_probe":
            return self._simulate_httpx(target)
        elif tool_name == "nuclei_scan":
            return self._simulate_nuclei(target, params.get("templates", ""), params.get("severity", ""))
        elif tool_name == "sqlmap_scan":
            return self._simulate_sqlmap(target, params.get("level", 1), params.get("risk", 1))
        elif tool_name == "nikto_scan":
            return self._simulate_nikto(target)
        elif tool_name == "xsstrike_scan":
            return self._simulate_xsstrike(target)
        elif tool_name == "wpscan":
            return self._simulate_wpscan(target, params.get("enumerate", "vp,vt,u"))
        elif tool_name == "hydra_brute":
            return self._simulate_hydra(target, params.get("service", "ssh"))
        elif tool_name == "testssl_scan":
            return self._simulate_testssl(target)
        else:
            # 通用模拟
            return ToolResult(
                tool_name=tool_name,
                success=True,
                output={"target": target, "message": f"{tool_name} 模拟执行完成"},
                simulated=True
            )
    
    # ==================== 渗透测试流程工具 ====================
    # 这些工具不通过 UnifiedExecutor，直接由 AI Agent 管理
    
    async def _execute_start_pentest(self, params: Dict[str, Any]) -> ToolResult:
        """启动渗透测试"""
        target = params.get("target", "")
        goal = params.get("goal", f"对 {target} 进行渗透测试")
        mode = params.get("mode", "full")
        
        if self._per_agent:
            try:
                # 启动 P-E-R 流程
                asyncio.create_task(self._run_per_agent(goal, target))
                
                return ToolResult(
                    tool_name="start_pentest",
                    success=True,
                    output={
                        "message": f"渗透测试已启动",
                        "target": target,
                        "goal": goal,
                        "mode": mode
                    }
                )
            except Exception as e:
                return ToolResult(
                    tool_name="start_pentest",
                    success=False,
                    error=str(e)
                )
        
        # 模拟模式
        if self.enable_simulation:
            return ToolResult(
                tool_name="start_pentest",
                success=True,
                output={
                    "message": "渗透测试已启动（模拟模式）",
                    "target": target,
                    "mode": mode
                },
                simulated=True
            )
        
        return ToolResult(
            tool_name="start_pentest",
            success=False,
            error="P-E-R Agent 未配置"
        )
    
    async def _run_per_agent(self, goal: str, target: str):
        """运行 P-E-R Agent"""
        if self._per_agent:
            try:
                target_info = {"target": target, "type": "web_application"}
                self._per_agent.set_goal(goal, target_info)
                await self._per_agent.run()
            except Exception as e:
                logger.error(f"P-E-R Agent 执行失败: {e}")
    
    async def _execute_get_pentest_status(self, params: Dict[str, Any]) -> ToolResult:
        """获取渗透测试状态"""
        if self._per_agent:
            state = self._per_agent.graph_manager.get_graph_state()
            return ToolResult(
                tool_name="get_pentest_status",
                success=True,
                output=state
            )
        
        return ToolResult(
            tool_name="get_pentest_status",
            success=True,
            output={"status": "idle", "message": "没有正在进行的渗透测试"},
            simulated=True
        )
    
    async def _execute_stop_pentest(self, params: Dict[str, Any]) -> ToolResult:
        """停止渗透测试"""
        if self._per_agent:
            self._per_agent.stop()
            return ToolResult(
                tool_name="stop_pentest",
                success=True,
                output={"message": "渗透测试已停止"}
            )
        
        return ToolResult(
            tool_name="stop_pentest",
            success=True,
            output={"message": "没有正在进行的渗透测试"},
            simulated=True
        )
    
    # ==================== 报告生成工具 ====================
    
    async def _execute_generate_report(self, params: Dict[str, Any]) -> ToolResult:
        """生成报告"""
        format_type = params.get("format", "html")
        include_evidence = params.get("include_evidence", True)
        
        # TODO: 集成现有报告系统
        
        return ToolResult(
            tool_name="generate_report",
            success=True,
            output={
                "message": "报告已生成",
                "format": format_type,
                "path": f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            },
            simulated=True
        )
    
    # ==================== 系统控制工具 ====================
    
    async def _execute_get_tool_status(self, params: Dict[str, Any]) -> ToolResult:
        """获取工具状态"""
        if self.tool_manager:
            status = self.tool_manager.check_tool_availability()
            return ToolResult(
                tool_name="get_tool_status",
                success=True,
                output=status
            )
        
        # 返回模拟状态
        mock_status = {
            tool: {"installed": False, "available": False}
            for tool in self.tool_mapping.keys()
        }
        
        return ToolResult(
            tool_name="get_tool_status",
            success=True,
            output=mock_status,
            simulated=True
        )
    
    # ==================== 通用执行 ====================
    
    # ==================== 模拟执行方法 ====================
    
    def _simulate_nmap(self, target: str, ports: str, scan_type: str) -> ToolResult:
        """模拟 Nmap 扫描"""
        import random
        
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 8080, 8443]
        open_count = random.randint(2, 6)
        open_ports = random.sample(common_ports, open_count)
        
        return ToolResult(
            tool_name="nmap_scan",
            success=True,
            output={
                "target": target,
                "ports": [{"port": p, "state": "open", "service": self._guess_service(p)} for p in sorted(open_ports)],
                "total_open_ports": open_count,
                "scan_type": scan_type
            },
            simulated=True
        )
    
    def _simulate_whatweb(self, target: str) -> ToolResult:
        """模拟 WhatWeb 扫描"""
        return ToolResult(
            tool_name="whatweb_scan",
            success=True,
            output={
                "target": target,
                "technologies": ["nginx", "PHP", "MySQL", "jQuery"],
                "server": "nginx/1.18.0",
                "title": "Welcome",
                "cms": None
            },
            simulated=True
        )
    
    def _simulate_subfinder(self, domain: str) -> ToolResult:
        """模拟 Subfinder 扫描"""
        return ToolResult(
            tool_name="subfinder_scan",
            success=True,
            output={
                "domain": domain,
                "subdomains": [f"www.{domain}", f"api.{domain}", f"mail.{domain}"],
                "total": 3
            },
            simulated=True
        )
    
    def _simulate_dirsearch(self, target: str, extensions: str) -> ToolResult:
        """模拟 Dirsearch 扫描"""
        return ToolResult(
            tool_name="dirsearch_scan",
            success=True,
            output={
                "target": target,
                "paths": [
                    {"path": "/admin", "status": 200, "size": 1024},
                    {"path": "/api", "status": 403, "size": 0},
                    {"path": "/backup", "status": 403, "size": 0},
                    {"path": "/config.php", "status": 200, "size": 512},
                ],
                "total": 4
            },
            simulated=True
        )
    
    def _simulate_httpx(self, targets: str) -> ToolResult:
        """模拟 HTTPX 探测"""
        return ToolResult(
            tool_name="httpx_probe",
            success=True,
            output={
                "alive": [
                    {"url": "http://example.com", "status": 200, "title": "Example"},
                ],
                "total": 1
            },
            simulated=True
        )
    
    def _simulate_nuclei(self, target: str, templates: str, severity: str) -> ToolResult:
        """模拟 Nuclei 扫描"""
        return ToolResult(
            tool_name="nuclei_scan",
            success=True,
            output={
                "target": target,
                "vulnerabilities": [
                    {"template": "CVE-2021-1234", "severity": "high", "name": "Test Vulnerability"},
                    {"template": "INFO-DISCLOSURE", "severity": "info", "name": "Information Disclosure"},
                ],
                "total": 2
            },
            simulated=True
        )
    
    def _simulate_sqlmap(self, target: str, level: int, risk: int) -> ToolResult:
        """模拟 SQLMap 扫描"""
        return ToolResult(
            tool_name="sqlmap_scan",
            success=True,
            output={
                "target": target,
                "injection_points": [
                    {"parameter": "id", "type": "integer", "payload": "1 OR 1=1"},
                ],
                "vulnerable": True,
                "database": "mysql"
            },
            simulated=True
        )
    
    def _simulate_nikto(self, target: str) -> ToolResult:
        """模拟 Nikto 扫描"""
        return ToolResult(
            tool_name="nikto_scan",
            success=True,
            output={
                "target": target,
                "findings": [
                    {"id": "000123", "msg": "Server header found", "osvdb": 0},
                ]
            },
            simulated=True
        )
    
    def _simulate_xsstrike(self, target: str) -> ToolResult:
        """模拟 XSStrike 扫描"""
        return ToolResult(
            tool_name="xsstrike_scan",
            success=True,
            output={
                "target": target,
                "vulnerabilities": [
                    {"parameter": "q", "type": "reflected", "payload": "<script>alert(1)</script>"},
                ]
            },
            simulated=True
        )
    
    def _simulate_wpscan(self, target: str, enumerate_opt: str) -> ToolResult:
        """模拟 WPScan 扫描"""
        return ToolResult(
            tool_name="wpscan",
            success=True,
            output={
                "target": target,
                "wordpress": {"version": "5.9", "detected": True},
                "plugins": [{"name": "contact-form-7", "version": "5.5"}],
                "users": [{"name": "admin", "id": 1}]
            },
            simulated=True
        )
    
    def _simulate_hydra(self, target: str, service: str) -> ToolResult:
        """模拟 Hydra 扫描"""
        return ToolResult(
            tool_name="hydra_brute",
            success=True,
            output={
                "target": target,
                "service": service,
                "results": [
                    {"user": "admin", "password": "admin123", "found": True},
                ]
            },
            simulated=True
        )
    
    def _simulate_testssl(self, target: str) -> ToolResult:
        """模拟 TestSSL 扫描"""
        return ToolResult(
            tool_name="testssl_scan",
            success=True,
            output={
                "target": target,
                "protocols": ["TLS 1.2", "TLS 1.3"],
                "ciphers": {"strong": 10, "weak": 2},
                "vulnerabilities": []
            },
            simulated=True
        )
    
    def _guess_service(self, port: int) -> str:
        """根据端口猜测服务"""
        service_map = {
            21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
            80: "http", 110: "pop3", 143: "imap", 443: "https", 445: "smb",
            993: "imaps", 995: "pop3s", 3306: "mysql", 3389: "rdp",
            5432: "postgresql", 8080: "http-proxy", 8443: "https-alt"
        }
        return service_map.get(port, "unknown")
    
    # ==================== 统计方法 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        return {
            **self.execution_stats,
            "success_rate": (
                self.execution_stats["successful_calls"] / self.execution_stats["total_calls"]
                if self.execution_stats["total_calls"] > 0 else 0
            )
        }


# ==================== 测试 ====================

async def test_tool_bridge():
    """测试工具执行桥接"""
    print("=" * 60)
    print("工具执行桥接测试")
    print("=" * 60)
    
    bridge = ToolExecutionBridge(enable_simulation=True)
    
    # 测试 Nmap
    print("\n1. Nmap 扫描:")
    result = await bridge.execute("nmap_scan", {"target": "example.com"})
    print(f"  成功: {result.success}")
    print(f"  模拟: {result.simulated}")
    print(f"  开放端口: {result.output.get('total_open_ports', 0)}")
    
    # 测试 Nuclei
    print("\n2. Nuclei 扫描:")
    result = await bridge.execute("nuclei_scan", {"target": "https://example.com"})
    print(f"  成功: {result.success}")
    print(f"  漏洞数: {len(result.output.get('vulnerabilities', []))}")
    
    # 测试统计
    print("\n3. 执行统计:")
    stats = bridge.get_stats()
    print(f"  总调用: {stats['total_calls']}")
    print(f"  成功率: {stats['success_rate']*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(test_tool_bridge())
