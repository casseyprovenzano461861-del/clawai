# -*- coding: utf-8 -*-
"""
Neo4j Cypher查询模板
用于知识图谱的各种查询操作
"""

from typing import Dict, List, Any, Optional, Union
from .models import NODE_LABELS, RELATIONSHIP_TYPES


class CypherQueries:
    """Cypher查询模板集合"""

    @staticmethod
    def create_node(node_type: str, properties: Dict[str, Any]) -> str:
        """创建节点查询"""
        label = NODE_LABELS.get(node_type, "Node")
        props_str = ", ".join([f"n.{key} = ${key}" for key in properties.keys()])

        return f"""
        CREATE (n:{label} {{ id: $id }})
        SET {props_str}
        RETURN n
        """

    @staticmethod
    def update_node(node_id: str, properties: Dict[str, Any]) -> str:
        """更新节点查询"""
        props_str = ", ".join([f"n.{key} = ${key}" for key in properties.keys()])

        return f"""
        MATCH (n {{ id: $node_id }})
        SET {props_str}
        RETURN n
        """

    @staticmethod
    def delete_node(node_id: str) -> str:
        """删除节点查询（同时删除相关关系）"""
        return """
        MATCH (n { id: $node_id })
        DETACH DELETE n
        RETURN COUNT(n) AS deleted_count
        """

    @staticmethod
    def get_node_by_id(node_id: str) -> str:
        """根据ID获取节点"""
        return """
        MATCH (n { id: $node_id })
        RETURN n
        """

    @staticmethod
    def get_nodes_by_type(node_type: str, limit: int = 100, offset: int = 0) -> str:
        """根据类型获取节点"""
        label = NODE_LABELS.get(node_type, "Node")

        return f"""
        MATCH (n:{label})
        RETURN n
        ORDER BY n.id
        SKIP $offset
        LIMIT $limit
        """

    @staticmethod
    def search_nodes(search_term: str, node_type: Optional[str] = None) -> str:
        """搜索节点（按标签或属性）"""
        type_filter = f":{NODE_LABELS[node_type]}" if node_type and node_type in NODE_LABELS else ""

        return f"""
        MATCH (n{type_filter})
        WHERE
            n.label CONTAINS $search_term OR
            n.id CONTAINS $search_term OR
            ANY(key IN keys(n) WHERE
                key <> 'id' AND
                key <> 'label' AND
                key <> 'type' AND
                toString(n[key]) CONTAINS $search_term
            )
        RETURN n
        ORDER BY n.label
        LIMIT 50
        """

    @staticmethod
    def create_relationship(
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Dict[str, Any]
    ) -> str:
        """创建关系查询"""
        relationship_type = RELATIONSHIP_TYPES.get(rel_type, "RELATED_TO")
        props_str = ", ".join([f"r.{key} = ${key}" for key in properties.keys()])

        return f"""
        MATCH (a {{ id: $source_id }})
        MATCH (b {{ id: $target_id }})
        CREATE (a)-[r:{relationship_type} {{ id: $rel_id }}]->(b)
        SET {props_str}
        RETURN r, a, b
        """

    @staticmethod
    def get_relationships_for_node(node_id: str, direction: str = "both") -> str:
        """获取节点的所有关系"""
        if direction == "incoming":
            match_clause = "MATCH (b)-[r]->(a { id: $node_id })"
        elif direction == "outgoing":
            match_clause = "MATCH (a { id: $node_id })-[r]->(b)"
        else:  # both
            match_clause = "MATCH (a { id: $node_id })-[r]-(b)"

        return f"""
        {match_clause}
        RETURN r, a, b
        ORDER BY type(r), r.id
        """

    @staticmethod
    def get_shortest_path(
        source_id: str,
        target_id: str,
        max_depth: int = 10,
        relationship_types: Optional[List[str]] = None
    ) -> str:
        """获取最短路径"""
        rel_filter = ""
        if relationship_types:
            rel_types_str = "|".join([RELATIONSHIP_TYPES.get(rt, rt) for rt in relationship_types])
            rel_filter = f":{rel_types_str}*1..{max_depth}"

        return f"""
        MATCH (a {{ id: $source_id }})
        MATCH (b {{ id: $target_id }})
        MATCH path = shortestPath((a)-[{rel_filter}]->(b))
        RETURN path, length(path) AS path_length
        """

    @staticmethod
    def get_all_paths(
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        limit: int = 50
    ) -> str:
        """获取所有路径"""
        return f"""
        MATCH (a {{ id: $source_id }})
        MATCH (b {{ id: $target_id }})
        MATCH path = (a)-[*1..{max_depth}]->(b)
        RETURN path, length(path) AS path_length
        ORDER BY path_length
        LIMIT $limit
        """

    @staticmethod
    def get_graph_stats() -> str:
        """获取图统计信息"""
        return """
        // 节点总数
        MATCH (n)
        WITH COUNT(n) AS total_nodes

        // 关系总数
        MATCH ()-[r]->()
        WITH total_nodes, COUNT(r) AS total_edges

        // 按类型统计节点
        MATCH (n)
        WITH total_nodes, total_edges,
             COLLECT(DISTINCT labels(n)[0]) AS node_labels

        // 按类型统计关系
        MATCH ()-[r]->()
        WITH total_nodes, total_edges, node_labels,
             COLLECT(DISTINCT type(r)) AS relationship_types

        RETURN total_nodes, total_edges, node_labels, relationship_types
        """

    @staticmethod
    def get_node_degrees() -> str:
        """获取节点度中心性（入度、出度、总度）"""
        return """
        MATCH (n)
        OPTIONAL MATCH (n)-[out]->()
        OPTIONAL MATCH ()-[in]->(n)
        RETURN n.id AS node_id, n.label AS node_label, labels(n)[0] AS node_type,
               COUNT(DISTINCT out) AS out_degree,
               COUNT(DISTINCT in) AS in_degree,
               COUNT(DISTINCT out) + COUNT(DISTINCT in) AS total_degree
        ORDER BY total_degree DESC
        LIMIT 50
        """

    @staticmethod
    def find_attack_paths(
        start_node_type: str = "vulnerability",
        end_node_type: str = "asset",
        max_depth: int = 5
    ) -> str:
        """查找攻击路径（从漏洞到资产）"""
        start_label = NODE_LABELS.get(start_node_type, "Vulnerability")
        end_label = NODE_LABELS.get(end_node_type, "Asset")

        return f"""
        // 查找从漏洞到资产的攻击路径
        MATCH (start:{start_label})
        MATCH (end:{end_label})
        MATCH path = (start)-[*1..{max_depth}]->(end)
        WHERE ALL(r IN relationships(path) WHERE type(r) IN [
            'EXPLOITS', 'CAN_ACCESS', 'EXECUTES', 'AFFECTS', 'USES'
        ])
        RETURN path, length(path) AS path_length,
               [n IN nodes(path) | n.label] AS node_labels,
               [r IN relationships(path) | type(r)] AS relationship_types
        ORDER BY path_length
        LIMIT 20
        """

    @staticmethod
    def get_related_nodes(
        node_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> str:
        """获取相关节点（指定深度内）"""
        rel_filter = ""
        if relationship_types:
            rel_types_str = "|".join([RELATIONSHIP_TYPES.get(rt, rt) for rt in relationship_types])
            rel_filter = f":{rel_types_str}*1..{max_depth}"

        return f"""
        MATCH (start {{ id: $node_id }})
        MATCH (related)
        WHERE related <> start
        MATCH path = shortestPath((start)-[{rel_filter}]-(related))
        RETURN DISTINCT related,
               length(path) AS distance,
               [r IN relationships(path) | type(r)] AS relationship_path
        ORDER BY distance
        LIMIT 100
        """

    @staticmethod
    def get_subgraph(node_ids: List[str], depth: int = 1) -> str:
        """获取子图（指定节点及其邻居）"""
        return f"""
        MATCH (n)
        WHERE n.id IN $node_ids
        WITH COLLECT(n) AS start_nodes
        UNWIND start_nodes AS start
        MATCH (start)-[*0..{depth}]-(connected)
        WITH COLLECT(DISTINCT connected) AS all_nodes
        UNWIND all_nodes AS node
        OPTIONAL MATCH (node)-[r]-(neighbor)
        WHERE neighbor IN all_nodes
        RETURN COLLECT(DISTINCT node) AS nodes,
               COLLECT(DISTINCT r) AS relationships
        """

    @staticmethod
    def bulk_create_nodes(nodes_data: List[Dict[str, Any]]) -> str:
        """批量创建节点"""
        return """
        UNWIND $nodes_data AS node_data
        CREATE (n:Node { id: node_data.id })
        SET n += node_data.properties
        SET n.type = node_data.type
        SET n.label = node_data.label
        RETURN COUNT(n) AS created_count
        """

    @staticmethod
    def bulk_create_relationships(relationships_data: List[Dict[str, Any]]) -> str:
        """批量创建关系"""
        return """
        UNWIND $relationships_data AS rel_data
        MATCH (a { id: rel_data.source })
        MATCH (b { id: rel_data.target })
        CREATE (a)-[r:RELATED_TO { id: rel_data.id }]->(b)
        SET r += rel_data.properties
        SET r.type = rel_data.type
        SET r.label = rel_data.label
        RETURN COUNT(r) AS created_count
        """


# 常用查询快捷方式
QUERIES = CypherQueries()