# -*- coding: utf-8 -*-
"""
指标收集模块
"""

import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, Summary
import time
import os


class MetricsManager:
    """指标管理类"""
    
    def __init__(self):
        self.metrics = {}
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """初始化指标"""
        # 工具执行相关指标
        self.metrics["tool_executions_total"] = Counter(
            "clawai_tool_executions_total",
            "Total number of tool executions",
            ["tool", "status"]
        )
        
        self.metrics["tool_execution_duration_seconds"] = Histogram(
            "clawai_tool_execution_duration_seconds",
            "Tool execution duration in seconds",
            ["tool"]
        )
        
        # 扫描相关指标
        self.metrics["scan_executions_total"] = Counter(
            "clawai_scan_executions_total",
            "Total number of scan executions",
            ["scenario", "status"]
        )
        
        self.metrics["scan_execution_duration_seconds"] = Histogram(
            "clawai_scan_execution_duration_seconds",
            "Scan execution duration in seconds",
            ["scenario"]
        )
        
        # 系统状态指标
        self.metrics["system_memory_usage_percent"] = Gauge(
            "clawai_system_memory_usage_percent",
            "System memory usage percentage"
        )
        
        self.metrics["system_cpu_usage_percent"] = Gauge(
            "clawai_system_cpu_usage_percent",
            "System CPU usage percentage"
        )
        
        # API请求指标
        self.metrics["api_requests_total"] = Counter(
            "clawai_api_requests_total",
            "Total number of API requests",
            ["endpoint", "method", "status"]
        )
        
        self.metrics["api_request_duration_seconds"] = Histogram(
            "clawai_api_request_duration_seconds",
            "API request duration in seconds",
            ["endpoint", "method"]
        )
        
        # 漏洞发现指标
        self.metrics["vulnerabilities_discovered_total"] = Counter(
            "clawai_vulnerabilities_discovered_total",
            "Total number of vulnerabilities discovered",
            ["severity"]
        )
        
    def get_metric(self, name):
        """获取指标"""
        return self.metrics.get(name)
    
    def record_tool_execution(self, tool, status, duration):
        """记录工具执行"""
        self.metrics["tool_executions_total"].labels(tool=tool, status=status).inc()
        self.metrics["tool_execution_duration_seconds"].labels(tool=tool).observe(duration)
    
    def record_scan_execution(self, scenario, status, duration):
        """记录扫描执行"""
        self.metrics["scan_executions_total"].labels(scenario=scenario, status=status).inc()
        self.metrics["scan_execution_duration_seconds"].labels(scenario=scenario).observe(duration)
    
    def record_api_request(self, endpoint, method, status, duration):
        """记录API请求"""
        self.metrics["api_requests_total"].labels(endpoint=endpoint, method=method, status=status).inc()
        self.metrics["api_request_duration_seconds"].labels(endpoint=endpoint, method=method).observe(duration)
    
    def record_vulnerability(self, severity):
        """记录漏洞发现"""
        self.metrics["vulnerabilities_discovered_total"].labels(severity=severity).inc()
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            import psutil
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.metrics["system_memory_usage_percent"].set(memory.percent)
            
            # CPU使用情况
            cpu = psutil.cpu_percent(interval=1)
            self.metrics["system_cpu_usage_percent"].set(cpu)
        except ImportError:
            pass
    
    def start_server(self, port=8000):
        """启动指标服务器"""
        prometheus_client.start_http_server(port)
        print(f"Metrics server started on port {port}")
