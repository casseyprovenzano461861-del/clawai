#!/usr/bin/env python3
"""
知识图谱模块测试
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.backend.graph.models import (
    Node, Edge, NodeType, RelationshipType,
    VulnerabilityNode, HostNode, UserNode, AssetNode,
    ScanResultNode, AttackNode, DefenseNode
)
from src.shared.backend.graph.exceptions import (
    GraphRepositoryError, NodeNotFoundError, EdgeNotFoundError,
    DatabaseConnectionError
)


class TestModels:
    """测试数据模型"""

    def test_node_creation(self):
        """测试节点创建"""
        node = Node(
            id="test-1",
            label="测试节点",
            type=NodeType.HOST,
            properties={"ip": "192.168.1.1", "os": "Linux"}
        )

        assert node.id == "test-1"
        assert node.label == "测试节点"
        assert node.type == NodeType.HOST
        assert node.properties["ip"] == "192.168.1.1"
        assert node.properties["os"] == "Linux"

    def test_edge_creation(self):
        """测试边创建"""
        edge = Edge(
            id="edge-1",
            source="node-1",
            target="node-2",
            label="连接",
            type=RelationshipType.HAS_VULNERABILITY,
            properties={"discovered": "2026-04-06", "confidence": 0.9}
        )

        assert edge.id == "edge-1"
        assert edge.source == "node-1"
        assert edge.target == "node-2"
        assert edge.type == RelationshipType.HAS_VULNERABILITY
        assert edge.properties["confidence"] == 0.9

    def test_specialized_nodes(self):
        """测试专用节点类型"""
        vuln = VulnerabilityNode(
            id="cve-2024-1234",
            label="SQL注入漏洞",
            cve_id="CVE-2024-1234",
            severity="高危",
            cvss_score=8.5,
            description="SQL注入漏洞描述"
        )

        assert vuln.type == NodeType.VULNERABILITY
        assert vuln.cve_id == "CVE-2024-1234"
        assert vuln.severity == "高危"
        assert vuln.cvss_score == 8.5

        host = HostNode(
            id="host-1",
            label="Web服务器",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55",
            os="Ubuntu 22.04",
            open_ports=[80, 443, 22]
        )

        assert host.type == NodeType.HOST
        assert host.ip_address == "192.168.1.100"
        assert host.open_ports == [80, 443, 22]


class TestCypherQueries:
    """测试Cypher查询模板"""

    def test_cypher_templates(self):
        """测试Cypher查询模板导入"""
        from src.shared.backend.graph.cypher_queries import (
            CREATE_NODE, CREATE_EDGE, FIND_NODE_BY_ID,
            FIND_EDGES_BY_NODE, FIND_SHORTEST_PATH,
            FIND_ATTACK_PATHS, GET_GRAPH_STATS
        )

        assert CREATE_NODE is not None
        assert CREATE_EDGE is not None
        assert FIND_NODE_BY_ID is not None
        assert FIND_EDGES_BY_NODE is not None
        assert FIND_SHORTEST_PATH is not None
        assert FIND_ATTACK_PATHS is not None
        assert GET_GRAPH_STATS is not None

        # 检查模板包含必要的占位符
        assert "{node_id}" in FIND_NODE_BY_ID
        assert "{source}" in CREATE_EDGE or "$source" in CREATE_EDGE


@patch('src.shared.backend.graph.neo4j_client.GraphDatabase')
class TestNeo4jClient:
    """测试Neo4j客户端（使用模拟）"""

    def test_client_initialization(self, mock_graph_database):
        """测试客户端初始化"""
        from src.shared.backend.graph.neo4j_client import Neo4jClient

        mock_driver = Mock()
        mock_graph_database.driver.return_value = mock_driver

        client = Neo4jClient(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )

        mock_graph_database.driver.assert_called_once()
        assert client.driver is not None

    def test_get_session(self, mock_graph_database):
        """测试获取会话"""
        from src.shared.backend.graph.neo4j_client import Neo4jClient

        mock_driver = Mock()
        mock_session = Mock()
        mock_driver.session.return_value = mock_session
        mock_graph_database.driver.return_value = mock_driver

        client = Neo4jClient(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )

        with client.get_session() as session:
            assert session is not None
            mock_driver.session.assert_called_once()


@patch('src.shared.backend.graph.repository.Neo4jClient')
class TestKnowledgeGraphRepository:
    """测试知识图谱仓库（使用模拟）"""

    def test_repository_initialization(self, mock_client_class):
        """测试仓库初始化"""
        from src.shared.backend.graph.repository import KnowledgeGraphRepository

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = KnowledgeGraphRepository()

        mock_client_class.assert_called_once()
        assert repo.client is not None

    def test_create_node(self, mock_client_class):
        """测试创建节点"""
        from src.shared.backend.graph.repository import KnowledgeGraphRepository

        mock_client = Mock()
        mock_session = Mock()
        mock_result = Mock()

        mock_client_class.return_value = mock_client
        mock_client.get_session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = {"n": {"id": "test-1"}}

        repo = KnowledgeGraphRepository()
        node = Node(
            id="test-1",
            label="测试节点",
            type=NodeType.HOST,
            properties={"ip": "192.168.1.1"}
        )

        result = repo.create_node(node)

        assert result is not None
        mock_session.run.assert_called_once()

    def test_find_node_by_id_not_found(self, mock_client_class):
        """测试查找不存在的节点"""
        from src.shared.backend.graph.repository import KnowledgeGraphRepository

        mock_client = Mock()
        mock_session = Mock()
        mock_result = Mock()

        mock_client_class.return_value = mock_client
        mock_client.get_session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = None

        repo = KnowledgeGraphRepository()

        with pytest.raises(NodeNotFoundError):
            repo.find_node_by_id("non-existent-id")

    def test_get_graph_stats(self, mock_client_class):
        """测试获取图统计信息"""
        from src.shared.backend.graph.repository import KnowledgeGraphRepository

        mock_client = Mock()
        mock_session = Mock()
        mock_result = Mock()

        mock_client_class.return_value = mock_client
        mock_client.get_session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result

        # 模拟统计查询结果
        mock_result.single.side_effect = [
            {"node_count": 10},
            {"edge_count": 15},
            {"type": "host", "count": 5},
            {"type": "vulnerability", "count": 3},
            {"type": "user", "count": 2},
            None,  # 表示没有更多节点类型
            {"type": "has_vulnerability", "count": 8},
            {"type": "has_access", "count": 7},
            None   # 表示没有更多边类型
        ]

        repo = KnowledgeGraphRepository()
        stats = repo.get_graph_stats()

        assert stats["total_nodes"] == 10
        assert stats["total_edges"] == 15
        assert stats["node_types"]["host"] == 5
        assert stats["node_types"]["vulnerability"] == 3
        assert stats["edge_types"]["has_vulnerability"] == 8


class TestAPIEndpoints:
    """测试API端点（模拟测试）"""

    def test_api_route_import(self):
        """测试API路由导入"""
        from src.shared.backend.api.knowledge_graph_fastapi import router

        assert router is not None
        assert hasattr(router, "routes")

        # 检查关键端点是否存在
        route_paths = [route.path for route in router.routes]
        assert "/graph" in route_paths or any("/graph" in str(path) for path in route_paths)
        assert "/nodes" in route_paths or any("/nodes" in str(path) for path in route_paths)
        assert "/edges" in route_paths or any("/edges" in str(path) for path in route_paths)

    def test_dependency_injection(self):
        """测试依赖注入"""
        from src.shared.backend.api.knowledge_graph_fastapi import get_knowledge_graph_repository

        # 这个函数应该返回一个仓库实例
        # 在实际应用中，它会被FastAPI的依赖注入系统调用
        assert callable(get_knowledge_graph_repository)


class TestImporters:
    """测试数据导入器"""

    def test_importer_base_class(self):
        """测试基础导入器类"""
        from src.shared.backend.graph.importers.base_importer import BaseImporter

        # 创建模拟导入器
        class MockImporter(BaseImporter):
            def validate_data(self, data):
                return True

            def import_data(self, data):
                return {"imported": 5}

        importer = MockImporter()
        assert importer.validate_data({}) is True
        result = importer.import_data({})
        assert result["imported"] == 5

    def test_nmap_importer_structure(self):
        """测试NMAP导入器结构"""
        from src.shared.backend.graph.importers.nmap_importer import NmapImporter

        importer = NmapImporter()
        assert hasattr(importer, "validate_data")
        assert hasattr(importer, "import_data")
        assert hasattr(importer, "parse_nmap_xml")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])