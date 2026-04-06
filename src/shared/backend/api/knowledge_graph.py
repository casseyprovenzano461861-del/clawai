# -*- coding: utf-8 -*-
"""
知识图谱API模块
基于PentAGI Graphiti架构的安全实体关系可视化后端服务
"""

from flask import Blueprint, jsonify, request
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime

# 创建蓝图
knowledge_graph_bp = Blueprint('knowledge_graph', __name__, url_prefix='/api/v1/knowledge-graph')

# 模拟知识图谱数据
MOCK_KNOWLEDGE_GRAPH_DATA = {
    "nodes": [
        {
            "id": "target-1",
            "label": "目标服务器",
            "type": "server",
            "properties": {
                "ip": "192.168.1.100",
                "os": "Linux",
                "ports": "22,80,443",
                "status": "在线",
                "risk": "中",
                "last_seen": "2026-04-05T10:30:00Z"
            },
            "position": {"x": 300, "y": 200},
            "size": 40,
            "color": "#3b82f6"
        },
        {
            "id": "vuln-1",
            "label": "SQL注入漏洞",
            "type": "vulnerability",
            "properties": {
                "cve": "CVE-2024-1234",
                "severity": "高危",
                "cvss": 8.5,
                "exploit": "可用",
                "patch": "未修复",
                "discovered": "2026-04-04T14:20:00Z"
            },
            "position": {"x": 500, "y": 150},
            "size": 35,
            "color": "#ef4444"
        },
        {
            "id": "vuln-2",
            "label": "XSS漏洞",
            "type": "vulnerability",
            "properties": {
                "cve": "CVE-2024-5678",
                "severity": "中危",
                "cvss": 6.2,
                "exploit": "可用",
                "patch": "已修复",
                "discovered": "2026-04-03T09:15:00Z"
            },
            "position": {"x": 500, "y": 250},
            "size": 30,
            "color": "#f59e0b"
        },
        {
            "id": "user-1",
            "label": "管理员账户",
            "type": "user",
            "properties": {
                "username": "admin",
                "role": "管理员",
                "last_login": "2026-04-05T08:45:00Z",
                "status": "活跃",
                "department": "IT"
            },
            "position": {"x": 100, "y": 200},
            "size": 35,
            "color": "#10b981"
        },
        {
            "id": "tool-1",
            "label": "NMAP扫描器",
            "type": "tool",
            "properties": {
                "tool": "nmap",
                "version": "7.94",
                "findings": 15,
                "success": True,
                "last_run": "2026-04-05T11:20:00Z"
            },
            "position": {"x": 100, "y": 300},
            "size": 30,
            "color": "#8b5cf6"
        },
        {
            "id": "network-1",
            "label": "内部网络",
            "type": "network",
            "properties": {
                "subnet": "192.168.1.0/24",
                "devices": 24,
                "services": 8,
                "security": "中等",
                "gateway": "192.168.1.1"
            },
            "position": {"x": 300, "y": 400},
            "size": 45,
            "color": "#6366f1"
        },
        {
            "id": "attack-1",
            "label": "攻击路径",
            "type": "attack",
            "properties": {
                "steps": 3,
                "complexity": "中等",
                "success_rate": "75%",
                "impact": "数据泄露",
                "techniques": ["T1190", "T1133", "T1005"]
            },
            "position": {"x": 500, "y": 350},
            "size": 35,
            "color": "#ec4899"
        },
        {
            "id": "asset-1",
            "label": "数据库服务器",
            "type": "asset",
            "properties": {
                "type": "MySQL",
                "version": "8.0",
                "data": "敏感",
                "backup": "有",
                "criticality": "高"
            },
            "position": {"x": 700, "y": 200},
            "size": 40,
            "color": "#14b8a6"
        },
        {
            "id": "threat-1",
            "label": "APT组织",
            "type": "threat",
            "properties": {
                "name": "APT29",
                "country": "未知",
                "targets": "政府,企业",
                "techniques": 12,
                "last_activity": "2026-04-02T16:40:00Z"
            },
            "position": {"x": 700, "y": 350},
            "size": 38,
            "color": "#f97316"
        },
        {
            "id": "defense-1",
            "label": "WAF防护",
            "type": "defense",
            "properties": {
                "vendor": "Cloudflare",
                "rules": 245,
                "blocked": 1245,
                "effectiveness": "高",
                "last_updated": "2026-04-05T09:10:00Z"
            },
            "position": {"x": 300, "y": 100},
            "size": 32,
            "color": "#22c55e"
        }
    ],
    "edges": [
        {
            "id": "edge-1",
            "source": "tool-1",
            "target": "target-1",
            "label": "扫描发现",
            "type": "discovery",
            "strength": 0.9,
            "properties": {
                "timestamp": "2026-04-05T11:20:00Z",
                "method": "端口扫描",
                "confidence": "高"
            }
        },
        {
            "id": "edge-2",
            "source": "target-1",
            "target": "vuln-1",
            "label": "存在漏洞",
            "type": "has_vulnerability",
            "strength": 0.8,
            "properties": {
                "timestamp": "2026-04-05T11:25:00Z",
                "scanner": "nmap",
                "confirmed": True
            }
        },
        {
            "id": "edge-3",
            "source": "target-1",
            "target": "vuln-2",
            "label": "存在漏洞",
            "type": "has_vulnerability",
            "strength": 0.6,
            "properties": {
                "timestamp": "2026-04-05T11:25:00Z",
                "scanner": "nmap",
                "confirmed": True
            }
        },
        {
            "id": "edge-4",
            "source": "user-1",
            "target": "target-1",
            "label": "访问权限",
            "type": "has_access",
            "strength": 0.7,
            "properties": {
                "timestamp": "2026-04-05T08:45:00Z",
                "access_level": "管理员",
                "method": "SSH密钥"
            }
        },
        {
            "id": "edge-5",
            "source": "vuln-1",
            "target": "asset-1",
            "label": "可访问",
            "type": "can_access",
            "strength": 0.9,
            "properties": {
                "timestamp": "2026-04-05T11:30:00Z",
                "exploit": "SQL注入",
                "risk": "高"
            }
        },
        {
            "id": "edge-6",
            "source": "vuln-2",
            "target": "asset-1",
            "label": "可访问",
            "type": "can_access",
            "strength": 0.5,
            "properties": {
                "timestamp": "2026-04-05T11:30:00Z",
                "exploit": "XSS",
                "risk": "中"
            }
        },
        {
            "id": "edge-7",
            "source": "attack-1",
            "target": "vuln-1",
            "label": "利用漏洞",
            "type": "exploits",
            "strength": 0.8,
            "properties": {
                "timestamp": "2026-04-05T14:00:00Z",
                "technique": "T1190",
                "success_probability": "高"
            }
        },
        {
            "id": "edge-8",
            "source": "attack-1",
            "target": "vuln-2",
            "label": "利用漏洞",
            "type": "exploits",
            "strength": 0.4,
            "properties": {
                "timestamp": "2026-04-05T14:00:00Z",
                "technique": "T1133",
                "success_probability": "中"
            }
        },
        {
            "id": "edge-9",
            "source": "threat-1",
            "target": "attack-1",
            "label": "使用攻击",
            "type": "uses",
            "strength": 0.7,
            "properties": {
                "timestamp": "2026-04-05T13:45:00Z",
                "attribution": "APT29",
                "motivation": "数据窃取"
            }
        },
        {
            "id": "edge-10",
            "source": "network-1",
            "target": "target-1",
            "label": "包含主机",
            "type": "contains",
            "strength": 1.0,
            "properties": {
                "timestamp": "2026-04-01T00:00:00Z",
                "relationship": "网络包含",
                "permanent": True
            }
        },
        {
            "id": "edge-11",
            "source": "defense-1",
            "target": "target-1",
            "label": "保护",
            "type": "protects",
            "strength": 0.8,
            "properties": {
                "timestamp": "2026-04-05T09:10:00Z",
                "protection_type": "WAF规则",
                "effectiveness": "高"
            }
        },
        {
            "id": "edge-12",
            "source": "defense-1",
            "target": "vuln-1",
            "label": "检测",
            "type": "detects",
            "strength": 0.6,
            "properties": {
                "timestamp": "2026-04-05T09:10:00Z",
                "detection_type": "签名检测",
                "accuracy": "中"
            }
        },
        {
            "id": "edge-13",
            "source": "defense-1",
            "target": "vuln-2",
            "label": "阻止",
            "type": "blocks",
            "strength": 0.9,
            "properties": {
                "timestamp": "2026-04-05T09:10:00Z",
                "block_type": "规则阻止",
                "effectiveness": "高"
            }
        }
    ]
}

# 节点类型配置
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
    }
}

# 边类型配置
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
    }
}

@knowledge_graph_bp.route('/graph', methods=['GET'])
def get_knowledge_graph():
    """
    获取知识图谱数据
    
    GET /api/v1/knowledge-graph/graph
    
    Query Parameters:
        - filter_type: 过滤节点类型 (可选)
        - search: 搜索关键词 (可选)
        - limit: 返回节点数量限制 (可选，默认全部)
    
    Returns:
        完整的知识图谱数据，包含节点和边
    """
    filter_type = request.args.get('filter_type')
    search_term = request.args.get('search', '').lower()
    limit = request.args.get('limit', type=int)
    
    # 复制数据以避免修改原始数据
    response_data = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "total_nodes": 0,
            "total_edges": 0,
            "node_types": {},
            "edge_types": {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # 过滤节点
    filtered_nodes = []
    for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]:
        # 类型过滤
        if filter_type and filter_type != "all" and node["type"] != filter_type:
            continue
        
        # 搜索过滤
        if search_term:
            search_match = (
                search_term in node["label"].lower() or
                search_term in node["type"].lower() or
                any(search_term in str(value).lower() for value in node.get("properties", {}).values())
            )
            if not search_match:
                continue
        
        filtered_nodes.append(node)
    
    # 应用数量限制
    if limit and limit > 0:
        filtered_nodes = filtered_nodes[:limit]
    
    # 过滤边（只保留与过滤后节点相关的边）
    filtered_edges = []
    filtered_node_ids = {node["id"] for node in filtered_nodes}
    
    for edge in MOCK_KNOWLEDGE_GRAPH_DATA["edges"]:
        if edge["source"] in filtered_node_ids and edge["target"] in filtered_node_ids:
            filtered_edges.append(edge)
    
    # 统计信息
    node_type_counts = {}
    edge_type_counts = {}
    
    for node in filtered_nodes:
        node_type = node["type"]
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
    
    for edge in filtered_edges:
        edge_type = edge["type"]
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
    
    # 构建响应
    response_data["nodes"] = filtered_nodes
    response_data["edges"] = filtered_edges
    response_data["metadata"]["total_nodes"] = len(filtered_nodes)
    response_data["metadata"]["total_edges"] = len(filtered_edges)
    response_data["metadata"]["node_types"] = node_type_counts
    response_data["metadata"]["edge_types"] = edge_type_counts
    response_data["metadata"]["node_type_config"] = NODE_TYPES
    response_data["metadata"]["edge_type_config"] = EDGE_TYPES
    
    return jsonify(response_data)

@knowledge_graph_bp.route('/stats', methods=['GET'])
def get_graph_stats():
    """
    获取知识图谱统计信息
    
    GET /api/v1/knowledge-graph/stats
    
    Returns:
        知识图谱的统计信息
    """
    # 计算统计信息
    total_nodes = len(MOCK_KNOWLEDGE_GRAPH_DATA["nodes"])
    total_edges = len(MOCK_KNOWLEDGE_GRAPH_DATA["edges"])
    
    # 节点类型统计
    node_type_counts = {}
    for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]:
        node_type = node["type"]
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
    
    # 边类型统计
    edge_type_counts = {}
    for edge in MOCK_KNOWLEDGE_GRAPH_DATA["edges"]:
        edge_type = edge["type"]
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
    
    # 风险统计
    high_risk_vulns = sum(
        1 for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"] 
        if node["type"] == "vulnerability" and node["properties"].get("severity") == "高危"
    )
    
    medium_risk_vulns = sum(
        1 for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"] 
        if node["type"] == "vulnerability" and node["properties"].get("severity") == "中危"
    )
    
    # 防御节点统计
    defense_nodes = sum(
        1 for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"] 
        if node["type"] == "defense"
    )
    
    # 资产节点统计
    asset_nodes = sum(
        1 for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"] 
        if node["type"] == "asset"
    )
    
    return jsonify({
        "stats": {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "high_risk_vulnerabilities": high_risk_vulns,
            "medium_risk_vulnerabilities": medium_risk_vulns,
            "defense_nodes": defense_nodes,
            "asset_nodes": asset_nodes,
            "node_types": node_type_counts,
            "edge_types": edge_type_counts
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "architecture": "PentAGI Graphiti-based"
    })

@knowledge_graph_bp.route('/node/<node_id>', methods=['GET'])
def get_node_details(node_id):
    """
    获取节点详细信息
    
    GET /api/v1/knowledge-graph/node/<node_id>
    
    Parameters:
        - node_id: 节点ID
    
    Returns:
        节点的详细信息
    """
    # 查找节点
    node = None
    for n in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]:
        if n["id"] == node_id:
            node = n
            break
    
    if not node:
        return jsonify({
            "error": "Node not found",
            "message": f"Node with ID {node_id} does not exist"
        }), 404
    
    # 查找相关边
    related_edges = []
    for edge in MOCK_KNOWLEDGE_GRAPH_DATA["edges"]:
        if edge["source"] == node_id or edge["target"] == node_id:
            related_edges.append(edge)
    
    # 查找相关节点
    related_node_ids = set()
    for edge in related_edges:
        if edge["source"] != node_id:
            related_node_ids.add(edge["source"])
        if edge["target"] != node_id:
            related_node_ids.add(edge["target"])
    
    related_nodes = []
    for n in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]:
        if n["id"] in related_node_ids:
            related_nodes.append({
                "id": n["id"],
                "label": n["label"],
                "type": n["type"],
                "color": n["color"]
            })
    
    return jsonify({
        "node": node,
        "related_edges": related_edges,
        "related_nodes": related_nodes,
        "node_type_info": NODE_TYPES.get(node["type"], {}),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@knowledge_graph_bp.route('/edge/<edge_id>', methods=['GET'])
def get_edge_details(edge_id):
    """
    获取边详细信息
    
    GET /api/v1/knowledge-graph/edge/<edge_id>
    
    Parameters:
        - edge_id: 边ID
    
    Returns:
        边的详细信息
    """
    # 查找边
    edge = None
    for e in MOCK_KNOWLEDGE_GRAPH_DATA["edges"]:
        if e["id"] == edge_id:
            edge = e
            break
    
    if not edge:
        return jsonify({
            "error": "Edge not found",
            "message": f"Edge with ID {edge_id} does not exist"
        }), 404
    
    # 查找源节点和目标节点
    source_node = None
    target_node = None
    
    for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]:
        if node["id"] == edge["source"]:
            source_node = {
                "id": node["id"],
                "label": node["label"],
                "type": node["type"],
                "color": node["color"],
                "properties": node["properties"]
            }
        if node["id"] == edge["target"]:
            target_node = {
                "id": node["id"],
                "label": node["label"],
                "type": node["type"],
                "color": node["color"],
                "properties": node["properties"]
            }
    
    return jsonify({
        "edge": edge,
        "source_node": source_node,
        "target_node": target_node,
        "edge_type_info": EDGE_TYPES.get(edge["type"], {}),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@knowledge_graph_bp.route('/search', methods=['GET'])
def search_graph():
    """
    搜索知识图谱
    
    GET /api/v1/knowledge-graph/search
    
    Query Parameters:
        - q: 搜索关键词
        - type: 搜索类型 (node, edge, all) 默认: all
    
    Returns:
        搜索结果
    """
    query = request.args.get('q', '').lower()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return jsonify({
            "error": "Missing query parameter",
            "message": "Query parameter 'q' is required"
        }), 400
    
    results = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "query": query,
            "search_type": search_type,
            "total_results": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # 搜索节点
    if search_type in ['node', 'all']:
        for node in MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]:
            # 检查标签
            if query in node["label"].lower():
                results["nodes"].append(node)
                continue
            
            # 检查类型
            if query in node["type"].lower():
                results["nodes"].append(node)
                continue
            
            # 检查属性
            for key, value in node.get("properties", {}).items():
                if query in str(value).lower():
                    results["nodes"].append(node)
                    break
    
    # 搜索边
    if search_type in ['edge', 'all']:
        for edge in MOCK_KNOWLEDGE_GRAPH_DATA["edges"]:
            # 检查标签
            if query in edge["label"].lower():
                results["edges"].append(edge)
                continue
            
            # 检查类型
            if query in edge["type"].lower():
                results["edges"].append(edge)
                continue
            
            # 检查属性
            for key, value in edge.get("properties", {}).items():
                if query in str(value).lower():
                    results["edges"].append(edge)
                    break
    
    results["metadata"]["total_results"] = len(results["nodes"]) + len(results["edges"])
    
    return jsonify(results)

@knowledge_graph_bp.route('/health', methods=['GET'])
def health_check():
    """
    知识图谱服务健康检查
    
    GET /api/v1/knowledge-graph/health
    
    Returns:
        服务健康状态
    """
    return jsonify({
        "status": "healthy",
        "service": "knowledge-graph-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "total_nodes": len(MOCK_KNOWLEDGE_GRAPH_DATA["nodes"]),
            "total_edges": len(MOCK_KNOWLEDGE_GRAPH_DATA["edges"]),
            "node_types": len(NODE_TYPES),
            "edge_types": len(EDGE_TYPES)
        }
    })

# 导出蓝图
__all__ = ['knowledge_graph_bp']
