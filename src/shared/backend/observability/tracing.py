# -*- coding: utf-8 -*-
"""
分布式追踪模块
"""

import opentelemetry
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TracingManager:
    """追踪管理类"""
    
    def __init__(self, service_name="clawai"):
        self.service_name = service_name
        self.tracer_provider = None
        self._initialize_tracing()
    
    def _initialize_tracing(self):
        """初始化追踪"""
        # 设置服务资源
        resource = Resource(
            attributes={
                SERVICE_NAME: self.service_name
            }
        )
        
        # 创建追踪提供者
        self.tracer_provider = TracerProvider(resource=resource)
        
        # 创建Jaeger导出器
        jaeger_exporter = JaegerExporter(
            service_name=self.service_name,
            agent_host_name="localhost",
            agent_port=6831,
        )
        
        # 创建批处理处理器
        span_processor = BatchSpanProcessor(jaeger_exporter)
        
        # 添加处理器到追踪提供者
        self.tracer_provider.add_span_processor(span_processor)
        
        # 设置全局追踪提供者
        trace.set_tracer_provider(self.tracer_provider)
    
    def get_tracer(self, name):
        """获取追踪器"""
        return trace.get_tracer(name)
    
    def start_span(self, name, parent_span=None):
        """开始一个新的span"""
        tracer = self.get_tracer(self.service_name)
        if parent_span:
            return tracer.start_as_current_span(name, context=parent_span.get_span_context())
        else:
            return tracer.start_as_current_span(name)
    
    def shutdown(self):
        """关闭追踪"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
