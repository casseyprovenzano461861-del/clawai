# -*- coding: utf-8 -*-
"""
Neo4j图数据库数据模型定义
基于PentAGI Graphiti架构，适配ClawAI安全知识图谱需求
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class NodeModel:
    """图节点基础模型"""
    id: str
    label: str
    type: str  # 节点类型：server, vulnerability, user, tool, network, asset, threat, defense, attack, incident
    properties: Dict[str, Any] = field(default_factory=dict)
    position: Optional[Dict[str, float]] = None  # 可视化位置：{"x": 300, "y": 200}
    size: Optional[int] = None
    color: Optional[str] = None

    def to_neo4j_node(self) -> Dict[str, Any]:
        """转换为Neo4j节点属性"""
        node_props = {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            **self.properties
        }
        if self.position:
            node_props["position"] = self.position
        if self.size:
            node_props["size"] = self.size
        if self.color:
            node_props["color"] = self.color
        return node_props

    @classmethod
    def from_neo4j_node(cls, node_data: Dict[str, Any]) -> 'NodeModel':
        """从Neo4j节点数据创建模型"""
        # 提取标准属性
        id_val = node_data.get("id", str(uuid.uuid4()))
        label_val = node_data.get("label", "")
        type_val = node_data.get("type", "unknown")

        # 分离扩展属性
        position = node_data.pop("position", None) if "position" in node_data else None
        size = node_data.pop("size", None) if "size" in node_data else None
        color = node_data.pop("color", None) if "color" in node_data else None

        # 剩余属性作为properties
        properties = {k: v for k, v in node_data.items()
                     if k not in ["id", "label", "type", "position", "size", "color"]}

        return cls(
            id=id_val,
            label=label_val,
            type=type_val,
            properties=properties,
            position=position,
            size=size,
            color=color
        )


@dataclass
class EdgeModel:
    """图边（关系）基础模型"""
    id: str
    source: str  # 源节点ID
    target: str  # 目标节点ID
    label: str
    type: str  # 关系类型：has_vulnerability, has_access, can_access, exploits, protects, detects, blocks, belongs_to, uses
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: Optional[float] = None  # 关系强度 0.0-1.0
    color: Optional[str] = None
    width: Optional[int] = None

    def to_neo4j_relationship(self) -> Dict[str, Any]:
        """转换为Neo4j关系属性"""
        rel_props = {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            **self.properties
        }
        if self.strength is not None:
            rel_props["strength"] = self.strength
        if self.color:
            rel_props["color"] = self.color
        if self.width:
            rel_props["width"] = self.width
        return rel_props

    @classmethod
    def from_neo4j_relationship(cls, rel_data: Dict[str, Any]) -> 'EdgeModel':
        """从Neo4j关系数据创建模型"""
        # 提取标准属性
        id_val = rel_data.get("id", str(uuid.uuid4()))
        source_val = rel_data.get("source", "")
        target_val = rel_data.get("target", "")
        label_val = rel_data.get("label", "")
        type_val = rel_data.get("type", "unknown")

        # 分离扩展属性
        strength = rel_data.pop("strength", None) if "strength" in rel_data else None
        color = rel_data.pop("color", None) if "color" in rel_data else None
        width = rel_data.pop("width", None) if "width" in rel_data else None

        # 剩余属性作为properties
        properties = {k: v for k, v in rel_data.items()
                     if k not in ["id", "source", "target", "label", "type", "strength", "color", "width"]}

        return cls(
            id=id_val,
            source=source_val,
            target=target_val,
            label=label_val,
            type=type_val,
            properties=properties,
            strength=strength,
            color=color,
            width=width
        )


# 节点类型配置（与现有模拟数据保持一致）
NODE_TYPES = {
    "server": {
        "name": "服务器",
        "description": "网络服务器或主机设备",
        "icon": "server",
        "color": "#3b82f6"
    },
    "vulnerability": {
        "name": "漏洞",
        "description": "安全漏洞或弱点",
        "icon": "alert-triangle",
        "color": "#ef4444"
    },
    "user": {
        "name": "用户",
        "description": "系统用户或账户",
        "icon": "user",
        "color": "#10b981"
    },
    "tool": {
        "name": "工具",
        "description": "安全工具或扫描器",
        "icon": "tool",
        "color": "#8b5cf6"
    },
    "network": {
        "name": "网络",
        "description": "网络段或子网",
        "icon": "network",
        "color": "#6366f1"
    },
    "attack": {
        "name": "攻击",
        "description": "攻击路径或技术",
        "icon": "target",
        "color": "#ec4899"
    },
    "asset": {
        "name": "资产",
        "description": "重要资产或数据",
        "icon": "database",
        "color": "#14b8a6"
    },
    "threat": {
        "name": "威胁",
        "description": "威胁组织或行为者",
        "icon": "shield",
        "color": "#f97316"
    },
    "defense": {
        "name": "防御",
        "description": "防御措施或控制",
        "icon": "shield-check",
        "color": "#22c55e"
    },
    "incident": {
        "name": "事件",
        "description": "安全事件或事故",
        "icon": "incident",
        "color": "#6366f1"
    }
}

# 边类型配置（与现有模拟数据保持一致）
EDGE_TYPES = {
    "discovery": {
        "name": "发现",
        "description": "工具发现目标",
        "color": "#8b5cf6"
    },
    "has_vulnerability": {
        "name": "存在漏洞",
        "description": "目标存在安全漏洞",
        "color": "#ef4444"
    },
    "has_access": {
        "name": "访问权限",
        "description": "用户有访问目标的权限",
        "color": "#10b981"
    },
    "can_access": {
        "name": "可访问",
        "description": "通过漏洞可访问资产",
        "color": "#f59e0b"
    },
    "exploits": {
        "name": "利用",
        "description": "攻击利用漏洞",
        "color": "#ec4899"
    },
    "uses": {
        "name": "使用",
        "description": "威胁使用攻击技术",
        "color": "#f97316"
    },
    "contains": {
        "name": "包含",
        "description": "网络包含主机",
        "color": "#6366f1"
    },
    "protects": {
        "name": "保护",
        "description": "防御措施保护目标",
        "color": "#22c55e"
    },
    "detects": {
        "name": "检测",
        "description": "防御检测到漏洞",
        "color": "#3b82f6"
    },
    "blocks": {
        "name": "阻止",
        "description": "防御阻止漏洞利用",
        "color": "#14b8a6"
    },
    "belongs_to": {
        "name": "属于",
        "description": "节点属于网络",
        "color": "#8b5cf6"
    },
    "exploitable_by": {
        "name": "可被利用",
        "description": "漏洞可被工具利用",
        "color": "#f59e0b"
    },
    "executes": {
        "name": "执行攻击",
        "description": "工具执行攻击",
        "color": "#dc2626"
    },
    "affects": {
        "name": "影响资产",
        "description": "攻击影响资产",
        "color": "#0ea5e9"
    },
    "faces": {
        "name": "面临威胁",
        "description": "资产面临威胁",
        "color": "#f97316"
    },
    "mitigated_by": {
        "name": "被防护",
        "description": "威胁被防御缓解",
        "color": "#22c55e"
    },
    "manages": {
        "name": "管理",
        "description": "用户管理目标",
        "color": "#10b981"
    },
    "causes": {
        "name": "导致事件",
        "description": "攻击导致安全事件",
        "color": "#6366f1"
    },
    "assigned_to": {
        "name": "分配给",
        "description": "事件分配给用户",
        "color": "#10b981"
    },
    "deploys": {
        "name": "部署防护",
        "description": "网络部署防御",
        "color": "#22c55e"
    },
    "reports": {
        "name": "报告事件",
        "description": "用户报告事件",
        "color": "#6366f1"
    }
}

# 节点标签到Cypher标签的映射
NODE_LABELS = {
    "server": "Server",
    "vulnerability": "Vulnerability",
    "user": "User",
    "tool": "Tool",
    "network": "Network",
    "attack": "Attack",
    "asset": "Asset",
    "threat": "Threat",
    "defense": "Defense",
    "incident": "Incident"
}

# 关系类型到Cypher关系类型的映射
RELATIONSHIP_TYPES = {
    "discovery": "DISCOVERY",
    "has_vulnerability": "HAS_VULNERABILITY",
    "has_access": "HAS_ACCESS",
    "can_access": "CAN_ACCESS",
    "exploits": "EXPLOITS",
    "uses": "USES",
    "contains": "CONTAINS",
    "protects": "PROTECTS",
    "detects": "DETECTS",
    "blocks": "BLOCKS",
    "belongs_to": "BELONGS_TO",
    "exploitable_by": "EXPLOITABLE_BY",
    "executes": "EXECUTES",
    "affects": "AFFECTS",
    "faces": "FACES",
    "mitigated_by": "MITIGATED_BY",
    "manages": "MANAGES",
    "causes": "CAUSES",
    "assigned_to": "ASSIGNED_TO",
    "deploys": "DEPLOYS",
    "reports": "REPORTS"
}

def create_node_id(node_type: str, identifier: str) -> str:
    """生成标准节点ID"""
    return f"{node_type}-{identifier}"

def create_edge_id(edge_type: str, source_id: str, target_id: str) -> str:
    """生成标准边ID"""
    return f"edge-{edge_type}-{source_id}-{target_id}"

def get_node_color(node_type: str) -> str:
    """获取节点类型的默认颜色"""
    return NODE_TYPES.get(node_type, {}).get("color", "#9ca3af")

def get_edge_color(edge_type: str) -> str:
    """获取边类型的默认颜色"""
    return EDGE_TYPES.get(edge_type, {}).get("color", "#9ca3af")