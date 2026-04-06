"""
扫描模型
借鉴PentAGI的扫描任务设计
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, List, Optional

from .base import BaseModel


class ScanStatus(PyEnum):
    """扫描状态枚举"""
    PENDING = "pending"      # 等待中
    QUEUED = "queued"        # 已排队
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"        # 已暂停


class ScanType(PyEnum):
    """扫描类型枚举"""
    QUICK = "quick"          # 快速扫描
    STANDARD = "standard"    # 标准扫描
    DEEP = "deep"            # 深度扫描
    CUSTOM = "custom"        # 自定义扫描


class Scan(BaseModel):
    """扫描模型"""
    __tablename__ = "scans"
    
    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 状态信息
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    scan_type = Column(Enum(ScanType), default=ScanType.STANDARD, nullable=False)
    
    # 目标信息
    target = Column(String(500), nullable=False)
    target_type = Column(String(50), default="domain", nullable=False)  # domain, ip, url
    
    # 配置信息
    config = Column(JSON, default=dict, nullable=False)   # 扫描配置
    tools = Column(JSON, default=list, nullable=False)    # 使用的工具
    
    # 执行信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # 执行时长（秒）
    
    # 结果信息
    results = Column(JSON, default=dict, nullable=False)  # 扫描结果
    findings = Column(JSON, default=list, nullable=False) # 发现的问题
    logs = Column(JSON, default=list, nullable=False)     # 执行日志
    
    # 统计信息
    tool_count = Column(Integer, default=0, nullable=False)
    finding_count = Column(Integer, default=0, nullable=False)
    vulnerability_count = Column(Integer, default=0, nullable=False)
    
    # 性能信息
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    network_usage = Column(Float, nullable=True)
    
    # 外键关系
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="scans")
    creator = relationship("User", foreign_keys=[created_by])
    reports = relationship("Report", back_populates="scan", cascade="all, delete-orphan")
    
    def __init__(self, name: str, target: str, project_id: int, created_by: int, **kwargs):
        """初始化扫描"""
        super().__init__(**kwargs)
        self.name = name
        self.target = target
        self.project_id = project_id
        self.created_by = created_by
        
        # 默认配置
        self.config = {
            "timeout": 3600,
            "rate_limit": 10,
            "concurrency": 3,
            "depth": 3,
            "max_pages": 1000
        }
        
        # 默认工具
        self.tools = [
            "nmap",
            "whatweb",
            "dirsearch",
            "nikto",
            "nuclei"
        ]
        
        self.tool_count = len(self.tools)
    
    def start(self):
        """开始扫描"""
        self.status = ScanStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, results: Dict[str, Any]):
        """完成扫描"""
        self.status = ScanStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        # 计算执行时长
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
        
        # 保存结果
        self.results = results
        
        # 提取发现的问题
        self.findings = results.get("findings", [])
        self.finding_count = len(self.findings)
        
        # 计算漏洞数量
        vulnerabilities = [f for f in self.findings if f.get("type") == "vulnerability"]
        self.vulnerability_count = len(vulnerabilities)
        
        # 更新项目统计
        if self.project:
            self.project.update_stats()
    
    def fail(self, error: str):
        """标记为失败"""
        self.status = ScanStatus.FAILED
        self.completed_at = datetime.utcnow()
        
        # 保存错误信息
        self.results = {
            "error": error,
            "status": "failed"
        }
    
    def add_log(self, level: str, message: str, tool: str = None):
        """添加日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,  # info, warning, error, debug
            "message": message,
            "tool": tool
        }
        
        self.logs.append(log_entry)
    
    def update_performance(self, cpu: float, memory: float, network: float):
        """更新性能指标"""
        self.cpu_usage = cpu
        self.memory_usage = memory
        self.network_usage = network
    
    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 添加枚举值的字符串表示
        data["status"] = self.status.value if hasattr(self.status, 'value') else self.status
        data["scan_type"] = self.scan_type.value if hasattr(self.scan_type, 'value') else self.scan_type
        
        # 获取状态字符串表示
        status_str = self.status.value if hasattr(self.status, 'value') else self.status

        # 添加计算字段
        data["is_running"] = status_str == ScanStatus.RUNNING.value
        data["is_completed"] = status_str == ScanStatus.COMPLETED.value
        data["is_failed"] = status_str == ScanStatus.FAILED.value

        # 添加进度信息
        if status_str == ScanStatus.RUNNING.value and self.started_at:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
            if self.config.get("timeout"):
                data["progress"] = min(100, (elapsed / self.config["timeout"]) * 100)
        
        # 如果需要详细信息
        if include_details:
            data["project"] = self.project.to_dict() if self.project else None
            data["creator"] = self.creator.to_dict() if self.creator else None
            data["reports"] = [report.to_dict() for report in self.reports]
            
            # 添加工具执行详情
            if self.results and "tools" in self.results:
                data["tool_results"] = self.results["tools"]
        
        return data


class ScanSchedule(BaseModel):
    """扫描计划模型"""
    __tablename__ = "scan_schedules"
    
    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 调度信息
    cron_expression = Column(String(100), nullable=False)  # Cron表达式
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # 状态信息
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    
    # 配置信息
    scan_config = Column(JSON, default=dict, nullable=False)  # 扫描配置
    
    # 统计信息
    run_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    # 外键关系
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __init__(self, name: str, cron_expression: str, project_id: int, created_by: int, **kwargs):
        """初始化扫描计划"""
        super().__init__(**kwargs)
        self.name = name
        self.cron_expression = cron_expression
        self.project_id = project_id
        self.created_by = created_by
        
        # 默认扫描配置
        self.scan_config = {
            "scan_type": "standard",
            "tools": ["nmap", "whatweb", "nikto"],
            "timeout": 1800
        }
    
    def update_next_run(self):
        """更新下次运行时间"""
        from croniter import croniter
        from datetime import datetime
        
        base_time = self.last_run_at or datetime.utcnow()
        cron = croniter(self.cron_expression, base_time)
        self.next_run_at = cron.get_next(datetime)
    
    def execute(self):
        """执行扫描计划"""
        self.last_run_at = datetime.utcnow()
        self.run_count += 1
        self.update_next_run()
        
        # 这里应该触发实际的扫描任务
        # 返回扫描ID或任务ID
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 添加计算字段
        data["is_due"] = self._is_due()
        
        # 添加项目信息
        if self.project:
            data["project"] = self.project.to_dict()
        
        return data
    
    def _is_due(self) -> bool:
        """检查是否到期执行"""
        if not self.next_run_at or not self.is_active:
            return False
        return datetime.utcnow() >= self.next_run_at