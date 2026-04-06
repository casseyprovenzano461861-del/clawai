#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j数据库初始化脚本
创建知识图谱所需的约束、索引和初始数据
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.shared.backend.graph.neo4j_client import Neo4jClient
from src.shared.backend.graph.repository import get_repository
from src.shared.backend.graph.models import NODE_TYPES, EDGE_TYPES, NODE_LABELS, RELATIONSHIP_TYPES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_constraints_and_indexes(client: Neo4jClient):
    """创建数据库约束和索引"""
    logger.info("创建数据库约束和索引...")

    # 节点ID唯一约束
    constraints = [
        # 通用节点约束
        "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Node) REQUIRE n.id IS UNIQUE",

        # 特定类型节点的约束
        "CREATE CONSTRAINT server_id_unique IF NOT EXISTS FOR (n:Server) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT vulnerability_id_unique IF NOT EXISTS FOR (n:Vulnerability) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (n:User) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT tool_id_unique IF NOT EXISTS FOR (n:Tool) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT network_id_unique IF NOT EXISTS FOR (n:Network) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT asset_id_unique IF NOT EXISTS FOR (n:Asset) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT threat_id_unique IF NOT EXISTS FOR (n:Threat) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT defense_id_unique IF NOT EXISTS FOR (n:Defense) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT attack_id_unique IF NOT EXISTS FOR (n:Attack) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT incident_id_unique IF NOT EXISTS FOR (n:Incident) REQUIRE n.id IS UNIQUE",

        # 关系ID唯一约束
        "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR ()-[r:RELATED_TO]-() REQUIRE r.id IS UNIQUE"
    ]

    # 创建索引以提高查询性能
    indexes = [
        # 节点类型索引
        "CREATE INDEX node_type_index IF NOT EXISTS FOR (n:Node) ON (n.type)",
        "CREATE INDEX node_label_index IF NOT EXISTS FOR (n:Node) ON (n.label)",

        # 特定属性索引
        "CREATE INDEX vulnerability_cve_index IF NOT EXISTS FOR (n:Vulnerability) ON (n.cve)",
        "CREATE INDEX server_ip_index IF NOT EXISTS FOR (n:Server) ON (n.ip)",
        "CREATE INDEX user_username_index IF NOT EXISTS FOR (n:User) ON (n.username)",

        # 关系类型索引
        "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.type)",
        "CREATE INDEX relationship_label_index IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.label)"
    ]

    for constraint in constraints:
        try:
            client.execute_query(constraint)
            logger.info(f"创建约束: {constraint.split('IF NOT EXISTS')[0].strip()}")
        except Exception as e:
            logger.warning(f"创建约束失败（可能已存在）: {e}")

    for index in indexes:
        try:
            client.execute_query(index)
            logger.info(f"创建索引: {index.split('IF NOT EXISTS')[0].strip()}")
        except Exception as e:
            logger.warning(f"创建索引失败（可能已存在）: {e}")

    logger.info("数据库约束和索引创建完成")


def create_initial_data(client: Neo4jClient):
    """创建初始数据（示例）"""
    logger.info("创建初始示例数据...")

    # 示例节点数据
    example_nodes = [
        {
            "id": "server-demo-1",
            "label": "示例服务器",
            "type": "server",
            "properties": {
                "ip": "192.168.1.100",
                "os": "Linux",
                "ports": "22,80,443",
                "status": "在线",
                "risk": "低",
                "last_seen": "2026-04-06T10:00:00Z"
            },
            "position": {"x": 300, "y": 200},
            "size": 40,
            "color": "#3b82f6"
        },
        {
            "id": "vuln-demo-1",
            "label": "示例SQL注入漏洞",
            "type": "vulnerability",
            "properties": {
                "cve": "CVE-2024-0001",
                "severity": "高危",
                "cvss": 8.5,
                "exploit": "可用",
                "patch": "未修复",
                "discovered": "2026-04-05T14:20:00Z"
            },
            "position": {"x": 500, "y": 150},
            "size": 35,
            "color": "#ef4444"
        },
        {
            "id": "user-demo-1",
            "label": "管理员账户",
            "type": "user",
            "properties": {
                "username": "admin",
                "role": "管理员",
                "last_login": "2026-04-06T09:15:00Z",
                "status": "活跃",
                "department": "IT"
            },
            "position": {"x": 100, "y": 200},
            "size": 35,
            "color": "#10b981"
        },
        {
            "id": "tool-demo-1",
            "label": "NMAP扫描器",
            "type": "tool",
            "properties": {
                "tool": "nmap",
                "version": "7.94",
                "findings": 15,
                "success": True,
                "last_run": "2026-04-06T11:20:00Z"
            },
            "position": {"x": 100, "y": 300},
            "size": 30,
            "color": "#8b5cf6"
        }
    ]

    # 示例关系数据
    example_edges = [
        {
            "id": "edge-demo-1",
            "source": "tool-demo-1",
            "target": "server-demo-1",
            "label": "扫描发现",
            "type": "discovery",
            "properties": {
                "timestamp": "2026-04-06T11:20:00Z",
                "method": "端口扫描",
                "confidence": "高"
            },
            "strength": 0.9,
            "color": "#8b5cf6"
        },
        {
            "id": "edge-demo-2",
            "source": "server-demo-1",
            "target": "vuln-demo-1",
            "label": "存在漏洞",
            "type": "has_vulnerability",
            "properties": {
                "timestamp": "2026-04-06T11:25:00Z",
                "scanner": "nmap",
                "confirmed": True
            },
            "strength": 0.8,
            "color": "#ef4444"
        },
        {
            "id": "edge-demo-3",
            "source": "user-demo-1",
            "target": "server-demo-1",
            "label": "访问权限",
            "type": "has_access",
            "properties": {
                "timestamp": "2026-04-06T09:15:00Z",
                "access_level": "管理员",
                "method": "SSH密钥"
            },
            "strength": 0.7,
            "color": "#10b981"
        }
    ]

    # 导入节点
    from src.shared.backend.graph.models import NodeModel, EdgeModel

    nodes_to_create = []
    for node_data in example_nodes:
        node = NodeModel(
            id=node_data["id"],
            label=node_data["label"],
            type=node_data["type"],
            properties=node_data["properties"],
            position=node_data.get("position"),
            size=node_data.get("size"),
            color=node_data.get("color")
        )
        nodes_to_create.append(node)

    edges_to_create = []
    for edge_data in example_edges:
        edge = EdgeModel(
            id=edge_data["id"],
            source=edge_data["source"],
            target=edge_data["target"],
            label=edge_data["label"],
            type=edge_data["type"],
            properties=edge_data["properties"],
            strength=edge_data.get("strength"),
            color=edge_data.get("color"),
            width=edge_data.get("width")
        )
        edges_to_create.append(edge)

    # 批量创建
    if nodes_to_create:
        node_count = client.bulk_create_nodes(nodes_to_create)
        logger.info(f"创建了 {node_count} 个示例节点")

    if edges_to_create:
        edge_count = client.bulk_create_relationships(edges_to_create)
        logger.info(f"创建了 {edge_count} 个示例关系")

    logger.info("初始示例数据创建完成")


def health_check(client: Neo4jClient):
    """健康检查"""
    logger.info("执行数据库健康检查...")

    try:
        # 测试连接
        result = client.execute_query("RETURN 1 AS test")
        test_value = result.single()["test"]

        if test_value == 1:
            logger.info("✓ Neo4j连接正常")
        else:
            logger.error("✗ Neo4j连接测试失败")
            return False

        # 检查约束和索引
        constraints_result = client.execute_query("SHOW CONSTRAINTS")
        constraints = list(constraints_result)
        logger.info(f"✓ 数据库约束数量: {len(constraints)}")

        indexes_result = client.execute_query("SHOW INDEXES")
        indexes = list(indexes_result)
        logger.info(f"✓ 数据库索引数量: {len(indexes)}")

        # 检查数据
        nodes_result = client.execute_query("MATCH (n) RETURN COUNT(n) AS node_count")
        node_count = nodes_result.single()["node_count"]
        logger.info(f"✓ 数据库节点总数: {node_count}")

        edges_result = client.execute_query("MATCH ()-[r]->() RETURN COUNT(r) AS edge_count")
        edge_count = edges_result.single()["edge_count"]
        logger.info(f"✓ 数据库关系总数: {edge_count}")

        return True

    except Exception as e:
        logger.error(f"✗ 健康检查失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("ClawAI Neo4j数据库初始化脚本")
    logger.info("=" * 60)

    # 检查环境变量
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_auth = os.getenv("NEO4J_AUTH", "neo4j/password")

    logger.info(f"Neo4j URI: {neo4j_uri}")
    logger.info(f"Neo4j Auth: {neo4j_auth.split('/')[0]}/******")

    try:
        # 创建客户端
        client = Neo4jClient(uri=neo4j_uri, auth=neo4j_auth)

        # 执行初始化步骤
        create_constraints_and_indexes(client)

        # 检查是否有现有数据
        result = client.execute_query("MATCH (n) RETURN COUNT(n) AS count")
        count = result.single()["count"]

        if count == 0:
            logger.info("数据库为空，创建初始示例数据")
            create_initial_data(client)
        else:
            logger.info(f"数据库已有 {count} 个节点，跳过初始数据创建")

        # 健康检查
        if health_check(client):
            logger.info("✓ 数据库初始化完成")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("✗ 数据库初始化失败")
            logger.info("=" * 60)
            return 1

    except Exception as e:
        logger.error(f"✗ 初始化过程中出现错误: {e}")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())