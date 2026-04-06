"""
项目模型
借鉴PentAGI的项目管理设计
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, List, Optional

from .base import BaseModel


class ProjectStatus(PyEnum):
    """项目状态枚举"""
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 活跃
    PAUSED = "paused"        # 暂停
    COMPLETED = "completed"  # 完成
    ARCHIVED = "archived"    # 归档


class ProjectVisibility(PyEnum):
    """项目可见性枚举"""
    PRIVATE = "private"      # 私有
    TEAM = "team"           # 团队可见
    PUBLIC = "public"       # 公开


class Project(BaseModel):
    """项目模型"""
    __tablename__ = "projects"
    
    # 基本信息
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 状态信息
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    visibility = Column(Enum(ProjectVisibility), default=ProjectVisibility.PRIVATE, nullable=False)
    
    # 目标信息
    targets = Column(JSON, default=list, nullable=False)  # 目标列表
    scope = Column(JSON, default=dict, nullable=False)    # 扫描范围
    
    # 配置信息
    config = Column(JSON, default=dict, nullable=False)   # 项目配置
    tags = Column(JSON, default=list, nullable=False)     # 标签
    
    # 统计信息
    scan_count = Column(Integer, default=0, nullable=False)
    vulnerability_count = Column(Integer, default=0, nullable=False)
    last_scan_at = Column(DateTime, nullable=True)
    
    # 外键关系
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    owner = relationship("User", back_populates="projects")
    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan")
    team_members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    
    def __init__(self, name: str, owner_id: int, **kwargs):
        """初始化项目"""
        super().__init__(**kwargs)
        self.name = name
        self.owner_id = owner_id

        # 初始化JSON字段
        self.targets = []

        # 默认配置
        self.config = {
            "scan_mode": "standard",  # quick, standard, deep
            "tools": {
                "nmap": True,
                "sqlmap": True,
                "nikto": True,
                "dirsearch": True
            },
            "rate_limit": 10,  # 每秒请求数
            "timeout": 3600,   # 超时时间（秒）
            "concurrency": 3   # 并发数
        }

        # 默认范围
        self.scope = {
            "include": [],
            "exclude": [],
            "depth": 3,
            "max_pages": 1000
        }
    
    def add_target(self, target: str, target_type: str = "domain"):
        """添加目标"""
        target_info = {
            "target": target,
            "type": target_type,
            "added_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        if target_info not in self.targets:
            self.targets.append(target_info)
    
    def remove_target(self, target: str):
        """移除目标"""
        self.targets = [t for t in self.targets if t["target"] != target]
    
    def update_stats(self):
        """更新统计信息"""
        from .scan import ScanStatus
        
        # 更新扫描数量
        self.scan_count = len(self.scans)
        
        # 更新漏洞数量
        total_vulnerabilities = 0
        for scan in self.scans:
            if scan.status == ScanStatus.COMPLETED and scan.results:
                total_vulnerabilities += scan.results.get("vulnerability_count", 0)
        
        self.vulnerability_count = total_vulnerabilities
        
        # 更新最后扫描时间
        completed_scans = [s for s in self.scans if s.status == ScanStatus.COMPLETED]
        if completed_scans:
            self.last_scan_at = max(s.completed_at for s in completed_scans if s.completed_at)
    
    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 添加枚举值的字符串表示
        data["status"] = self.status.value if hasattr(self.status, 'value') else self.status
        data["visibility"] = self.visibility.value if hasattr(self.visibility, 'value') else self.visibility
        
        # 添加统计信息
        data["target_count"] = len(self.targets)
        data["member_count"] = len(self.team_members)
        
        # 如果需要详细信息
        if include_details:
            data["owner"] = self.owner.to_dict() if self.owner else None
            data["scans"] = [scan.to_dict() for scan in self.scans[:10]]  # 最近10次扫描
            data["members"] = [member.to_dict() for member in self.team_members]
        
        return data


class ProjectMember(BaseModel):
    """项目成员模型"""
    __tablename__ = "project_members"
    
    # 基本信息
    role = Column(String(50), default="member", nullable=False)  # owner, admin, member, viewer
    
    # 权限信息
    permissions = Column(JSON, default=list, nullable=False)
    
    # 外键关系
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="team_members")
    user = relationship("User")
    
    def __init__(self, project_id: int, user_id: int, role: str = "member", **kwargs):
        """初始化项目成员"""
        super().__init__(**kwargs)
        self.project_id = project_id
        self.user_id = user_id
        self.role = role
        
        # 根据角色设置权限
        self.permissions = self._get_role_permissions(role)
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """获取角色权限"""
        permissions = {
            "owner": [
                "project:read", "project:update", "project:delete",
                "scan:create", "scan:read", "scan:update", "scan:delete",
                "member:add", "member:remove", "member:update",
                "report:create", "report:read", "report:update", "report:delete"
            ],
            "admin": [
                "project:read", "project:update",
                "scan:create", "scan:read", "scan:update", "scan:delete",
                "member:add", "member:remove", "member:update",
                "report:create", "report:read", "report:update"
            ],
            "member": [
                "project:read",
                "scan:create", "scan:read", "scan:update",
                "report:create", "report:read"
            ],
            "viewer": [
                "project:read",
                "scan:read",
                "report:read"
            ]
        }
        
        return permissions.get(role, [])
    
    def has_permission(self, permission: str) -> bool:
        """检查成员权限"""
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        
        # 添加用户信息
        if self.user:
            data["user"] = self.user.to_dict()
        
        return data