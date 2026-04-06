# -*- coding: utf-8 -*-
"""
Neo4j图数据库客户端
提供Neo4j数据库连接和基础操作
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from neo4j import GraphDatabase, Driver, Session, Result, basic_auth
from neo4j.exceptions import Neo4jError, ServiceUnavailable, AuthError

from .models import NodeModel, EdgeModel, NODE_LABELS, RELATIONSHIP_TYPES
from .cypher_queries import QUERIES

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j客户端类"""

    def __init__(self, uri: Optional[str] = None, auth: Optional[str] = None):
        """
        初始化Neo4j客户端

        Args:
            uri: Neo4j连接URI，默认为环境变量NEO4J_URI或bolt://localhost:7687
            auth: 认证信息，格式为"username/password"，默认为环境变量NEO4J_AUTH或neo4j/password
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.auth_str = auth or os.getenv("NEO4J_AUTH", "neo4j/password")

        # 解析认证信息
        if "/" in self.auth_str:
            username, password = self.auth_str.split("/", 1)
            self.auth = basic_auth(username, password)
        else:
            logger.warning(f"无效的NEO4J_AUTH格式: {self.auth_str}，使用默认认证")
            self.auth = basic_auth("neo4j", "password")

        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"成功连接到Neo4j: {self.uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"无法连接到Neo4j: {e}")
            self.driver = None
            raise ConnectionError(f"Neo4j连接失败: {e}")

    def close(self) -> None:
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")

    def execute_query(self, query: str, parameters: Optional[Dict] = None, **kwargs) -> Result:
        """
        执行Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数
            **kwargs: 额外参数

        Returns:
            Neo4j Result对象
        """
        if not self.driver:
            self._connect()

        try:
            with self.driver.session(**kwargs) as session:
                return session.run(query, parameters or {})
        except Neo4jError as e:
            logger.error(f"Neo4j查询执行失败: {e}, 查询: {query[:200]}...")
            raise

    # ========== 节点操作 ==========

    def create_node(self, node: NodeModel) -> Dict[str, Any]:
        """
        创建节点

        Args:
            node: 节点模型

        Returns:
            创建的节点数据
        """
        query = QUERIES.create_node(node.type, node.properties)
        params = {"id": node.id, **node.properties}

        result = self.execute_query(query, params)
        record = result.single()

        if record:
            neo4j_node = record["n"]
            return dict(neo4j_node.items())
        else:
            raise ValueError(f"创建节点失败: {node.id}")

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取节点

        Args:
            node_id: 节点ID

        Returns:
            节点数据，如果不存在则返回None
        """
        query = QUERIES.get_node_by_id(node_id)
        result = self.execute_query(query, {"node_id": node_id})
        record = result.single()

        if record:
            neo4j_node = record["n"]
            return dict(neo4j_node.items())
        return None

    def update_node(self, node_id: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新节点属性

        Args:
            node_id: 节点ID
            properties: 要更新的属性

        Returns:
            更新后的节点数据
        """
        query = QUERIES.update_node(node_id, properties)
        params = {"node_id": node_id, **properties}

        result = self.execute_query(query, params)
        record = result.single()

        if record:
            neo4j_node = record["n"]
            return dict(neo4j_node.items())
        return None

    def delete_node(self, node_id: str) -> int:
        """
        删除节点

        Args:
            node_id: 节点ID

        Returns:
            删除的节点数量
        """
        query = QUERIES.delete_node(node_id)
        result = self.execute_query(query, {"node_id": node_id})
        record = result.single()

        return record["deleted_count"] if record else 0

    def get_nodes_by_type(self, node_type: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        根据类型获取节点

        Args:
            node_type: 节点类型
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            节点列表
        """
        query = QUERIES.get_nodes_by_type(node_type, limit, offset)
        result = self.execute_query(query, {"limit": limit, "offset": offset})

        nodes = []
        for record in result:
            neo4j_node = record["n"]
            nodes.append(dict(neo4j_node.items()))
        return nodes

    def search_nodes(self, search_term: str, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索节点

        Args:
            search_term: 搜索关键词
            node_type: 节点类型过滤（可选）

        Returns:
            节点列表
        """
        query = QUERIES.search_nodes(search_term, node_type)
        result = self.execute_query(query, {"search_term": search_term})

        nodes = []
        for record in result:
            neo4j_node = record["n"]
            nodes.append(dict(neo4j_node.items()))
        return nodes

    # ========== 关系操作 ==========

    def create_relationship(self, edge: EdgeModel) -> Dict[str, Any]:
        """
        创建关系

        Args:
            edge: 边模型

        Returns:
            创建的关系数据
        """
        query = QUERIES.create_relationship(edge.source, edge.target, edge.type, edge.properties)
        params = {
            "source_id": edge.source,
            "target_id": edge.target,
            "rel_id": edge.id,
            **edge.properties
        }

        result = self.execute_query(query, params)
        record = result.single()

        if record:
            neo4j_rel = record["r"]
            return dict(neo4j_rel.items())
        else:
            raise ValueError(f"创建关系失败: {edge.id}")

    def get_relationships_for_node(self, node_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """
        获取节点的所有关系

        Args:
            node_id: 节点ID
            direction: 关系方向 (incoming, outgoing, both)

        Returns:
            关系列表，每条关系包含关系本身、源节点和目标节点
        """
        query = QUERIES.get_relationships_for_node(node_id, direction)
        result = self.execute_query(query, {"node_id": node_id})

        relationships = []
        for record in result:
            rel_data = {
                "relationship": dict(record["r"].items()),
                "source_node": dict(record["a"].items()),
                "target_node": dict(record["b"].items())
            }
            relationships.append(rel_data)
        return relationships

    # ========== 图查询操作 ==========

    def get_shortest_path(self, source_id: str, target_id: str,
                          max_depth: int = 10,
                          relationship_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        获取最短路径

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_depth: 最大深度
            relationship_types: 允许的关系类型列表

        Returns:
            路径信息，如果不存在路径则返回None
        """
        query = QUERIES.get_shortest_path(source_id, target_id, max_depth, relationship_types)
        result = self.execute_query(query, {
            "source_id": source_id,
            "target_id": target_id
        })
        record = result.single()

        if record and record["path"]:
            path = record["path"]
            return {
                "path_length": record["path_length"],
                "nodes": [dict(node.items()) for node in path.nodes],
                "relationships": [dict(rel.items()) for rel in path.relationships]
            }
        return None

    def get_all_paths(self, source_id: str, target_id: str,
                      max_depth: int = 5, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取所有路径

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_depth: 最大深度
            limit: 返回数量限制

        Returns:
            路径列表
        """
        query = QUERIES.get_all_paths(source_id, target_id, max_depth, limit)
        result = self.execute_query(query, {
            "source_id": source_id,
            "target_id": target_id,
            "limit": limit
        })

        paths = []
        for record in result:
            if record["path"]:
                path = record["path"]
                paths.append({
                    "path_length": record["path_length"],
                    "nodes": [dict(node.items()) for node in path.nodes],
                    "relationships": [dict(rel.items()) for rel in path.relationships]
                })
        return paths

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        获取图统计信息

        Returns:
            统计信息字典
        """
        query = QUERIES.get_graph_stats()
        result = self.execute_query(query)
        record = result.single()

        if record:
            return {
                "total_nodes": record["total_nodes"],
                "total_edges": record["total_edges"],
                "node_labels": record["node_labels"],
                "relationship_types": record["relationship_types"]
            }
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "node_labels": [],
            "relationship_types": []
        }

    def get_node_degrees(self) -> List[Dict[str, Any]]:
        """
        获取节点度中心性

        Returns:
            节点度信息列表
        """
        query = QUERIES.get_node_degrees()
        result = self.execute_query(query)

        degrees = []
        for record in result:
            degrees.append({
                "node_id": record["node_id"],
                "node_label": record["node_label"],
                "node_type": record["node_type"],
                "out_degree": record["out_degree"],
                "in_degree": record["in_degree"],
                "total_degree": record["total_degree"]
            })
        return degrees

    def find_attack_paths(self, start_node_type: str = "vulnerability",
                          end_node_type: str = "asset", max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        查找攻击路径

        Args:
            start_node_type: 起始节点类型
            end_node_type: 结束节点类型
            max_depth: 最大深度

        Returns:
            攻击路径列表
        """
        query = QUERIES.find_attack_paths(start_node_type, end_node_type, max_depth)
        result = self.execute_query(query)

        paths = []
        for record in result:
            if record["path"]:
                path = record["path"]
                paths.append({
                    "path_length": record["path_length"],
                    "node_labels": record["node_labels"],
                    "relationship_types": record["relationship_types"],
                    "nodes": [dict(node.items()) for node in path.nodes],
                    "relationships": [dict(rel.items()) for rel in path.relationships]
                })
        return paths

    def get_related_nodes(self, node_id: str,
                          relationship_types: Optional[List[str]] = None,
                          max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        获取相关节点

        Args:
            node_id: 节点ID
            relationship_types: 允许的关系类型列表
            max_depth: 最大深度

        Returns:
            相关节点列表
        """
        query = QUERIES.get_related_nodes(node_id, relationship_types, max_depth)
        result = self.execute_query(query, {"node_id": node_id})

        related_nodes = []
        for record in result:
            related_nodes.append({
                "node": dict(record["related"].items()),
                "distance": record["distance"],
                "relationship_path": record["relationship_path"]
            })
        return related_nodes

    # ========== 批量操作 ==========

    def bulk_create_nodes(self, nodes: List[NodeModel]) -> int:
        """
        批量创建节点

        Args:
            nodes: 节点模型列表

        Returns:
            创建的节点数量
        """
        nodes_data = []
        for node in nodes:
            node_data = {
                "id": node.id,
                "type": node.type,
                "label": node.label,
                "properties": node.properties
            }
            if node.position:
                node_data["properties"]["position"] = node.position
            if node.size:
                node_data["properties"]["size"] = node.size
            if node.color:
                node_data["properties"]["color"] = node.color
            nodes_data.append(node_data)

        query = QUERIES.bulk_create_nodes(nodes_data)
        result = self.execute_query(query, {"nodes_data": nodes_data})
        record = result.single()

        return record["created_count"] if record else 0

    def bulk_create_relationships(self, edges: List[EdgeModel]) -> int:
        """
        批量创建关系

        Args:
            edges: 边模型列表

        Returns:
            创建的关系数量
        """
        relationships_data = []
        for edge in edges:
            rel_data = {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "type": edge.type,
                "label": edge.label,
                "properties": edge.properties
            }
            if edge.strength is not None:
                rel_data["properties"]["strength"] = edge.strength
            if edge.color:
                rel_data["properties"]["color"] = edge.color
            if edge.width:
                rel_data["properties"]["width"] = edge.width
            relationships_data.append(rel_data)

        query = QUERIES.bulk_create_relationships(relationships_data)
        result = self.execute_query(query, {"relationships_data": relationships_data})
        record = result.single()

        return record["created_count"] if record else 0

    # ========== 数据库管理 ==========

    def clear_database(self) -> None:
        """清空数据库（仅用于测试）"""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        logger.warning("数据库已清空")

    def create_constraints(self) -> None:
        """创建数据库约束（确保数据完整性）"""
        constraints = [
            "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Node) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR ()-[r:RELATED_TO]-() REQUIRE r.id IS UNIQUE"
        ]

        for constraint in constraints:
            try:
                self.execute_query(constraint)
                logger.info(f"创建约束: {constraint}")
            except Neo4jError as e:
                logger.warning(f"创建约束失败（可能已存在）: {e}")

    def health_check(self) -> bool:
        """健康检查"""
        try:
            self.execute_query("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {e}")
            return False


# 全局客户端实例
_client_instance: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """
    获取全局Neo4j客户端实例

    Returns:
        Neo4jClient实例
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = Neo4jClient()
    return _client_instance


def close_neo4j_client() -> None:
    """关闭全局Neo4j客户端"""
    global _client_instance
    if _client_instance:
        _client_instance.close()
        _client_instance = None