# -*- coding: utf-8 -*-
"""
知识图谱数据访问层
提供高级数据访问接口，封装Neo4j客户端操作
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

from .neo4j_client import get_neo4j_client
from .models import NodeModel, EdgeModel, NODE_TYPES, EDGE_TYPES, NODE_LABELS, RELATIONSHIP_TYPES
from .exceptions import GraphRepositoryError, NodeNotFoundError, EdgeNotFoundError

logger = logging.getLogger(__name__)


class KnowledgeGraphRepository:
    """知识图谱数据仓库"""

    def __init__(self):
        self.client = get_neo4j_client()

    # ========== 节点管理 ==========

    def create_node(self, node_data: Dict[str, Any]) -> NodeModel:
        """
        创建节点

        Args:
            node_data: 节点数据，包含label, type, properties等

        Returns:
            创建的节点模型
        """
        try:
            # 生成节点ID
            node_id = node_data.get("id") or f"{node_data.get('type', 'node')}-{str(uuid.uuid4())[:8]}"

            # 创建节点模型
            node = NodeModel(
                id=node_id,
                label=node_data.get("label", ""),
                type=node_data.get("type", "unknown"),
                properties=node_data.get("properties", {}),
                position=node_data.get("position"),
                size=node_data.get("size"),
                color=node_data.get("color")
            )

            # 保存到数据库
            self.client.create_node(node)
            logger.info(f"创建节点: {node_id} ({node.type})")
            return node

        except Exception as e:
            logger.error(f"创建节点失败: {e}")
            raise GraphRepositoryError(f"创建节点失败: {e}")

    def get_node(self, node_id: str) -> Optional[NodeModel]:
        """
        获取节点

        Args:
            node_id: 节点ID

        Returns:
            节点模型，如果不存在则返回None
        """
        try:
            node_data = self.client.get_node(node_id)
            if not node_data:
                return None
            return NodeModel.from_neo4j_node(node_data)
        except Exception as e:
            logger.error(f"获取节点失败: {node_id}, 错误: {e}")
            raise GraphRepositoryError(f"获取节点失败: {e}")

    def update_node(self, node_id: str, updates: Dict[str, Any]) -> Optional[NodeModel]:
        """
        更新节点

        Args:
            node_id: 节点ID
            updates: 要更新的属性

        Returns:
            更新后的节点模型
        """
        try:
            # 先获取现有节点
            node = self.get_node(node_id)
            if not node:
                raise NodeNotFoundError(f"节点不存在: {node_id}")

            # 更新属性
            for key, value in updates.items():
                if key in ["id", "type"]:
                    continue  # 不允许修改ID和类型
                elif key in ["label", "position", "size", "color"]:
                    setattr(node, key, value)
                else:
                    node.properties[key] = value

            # 保存到数据库
            self.client.update_node(node_id, node.to_neo4j_node())
            logger.info(f"更新节点: {node_id}")
            return node

        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"更新节点失败: {node_id}, 错误: {e}")
            raise GraphRepositoryError(f"更新节点失败: {e}")

    def delete_node(self, node_id: str) -> bool:
        """
        删除节点

        Args:
            node_id: 节点ID

        Returns:
            是否成功删除
        """
        try:
            deleted_count = self.client.delete_node(node_id)
            success = deleted_count > 0
            if success:
                logger.info(f"删除节点: {node_id}")
            else:
                logger.warning(f"节点不存在，无法删除: {node_id}")
            return success
        except Exception as e:
            logger.error(f"删除节点失败: {node_id}, 错误: {e}")
            raise GraphRepositoryError(f"删除节点失败: {e}")

    def get_nodes_by_type(self, node_type: str, limit: int = 100, offset: int = 0) -> List[NodeModel]:
        """
        根据类型获取节点

        Args:
            node_type: 节点类型
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            节点模型列表
        """
        try:
            nodes_data = self.client.get_nodes_by_type(node_type, limit, offset)
            return [NodeModel.from_neo4j_node(node_data) for node_data in nodes_data]
        except Exception as e:
            logger.error(f"获取节点列表失败: {node_type}, 错误: {e}")
            raise GraphRepositoryError(f"获取节点列表失败: {e}")

    def search_nodes(self, search_term: str, node_type: Optional[str] = None) -> List[NodeModel]:
        """
        搜索节点

        Args:
            search_term: 搜索关键词
            node_type: 节点类型过滤（可选）

        Returns:
            节点模型列表
        """
        try:
            nodes_data = self.client.search_nodes(search_term, node_type)
            return [NodeModel.from_neo4j_node(node_data) for node_data in nodes_data]
        except Exception as e:
            logger.error(f"搜索节点失败: {search_term}, 错误: {e}")
            raise GraphRepositoryError(f"搜索节点失败: {e}")

    # ========== 关系管理 ==========

    def create_relationship(self, edge_data: Dict[str, Any]) -> EdgeModel:
        """
        创建关系

        Args:
            edge_data: 关系数据，包含source, target, type, label, properties等

        Returns:
            创建的关系模型
        """
        try:
            # 验证源节点和目标节点是否存在
            source_node = self.get_node(edge_data.get("source", ""))
            target_node = self.get_node(edge_data.get("target", ""))

            if not source_node:
                raise NodeNotFoundError(f"源节点不存在: {edge_data.get('source')}")
            if not target_node:
                raise NodeNotFoundError(f"目标节点不存在: {edge_data.get('target')}")

            # 生成关系ID
            edge_id = edge_data.get("id") or f"edge-{str(uuid.uuid4())[:8]}"

            # 创建关系模型
            edge = EdgeModel(
                id=edge_id,
                source=edge_data["source"],
                target=edge_data["target"],
                label=edge_data.get("label", ""),
                type=edge_data.get("type", "related"),
                properties=edge_data.get("properties", {}),
                strength=edge_data.get("strength"),
                color=edge_data.get("color"),
                width=edge_data.get("width")
            )

            # 保存到数据库
            self.client.create_relationship(edge)
            logger.info(f"创建关系: {edge_id} ({edge.type})")
            return edge

        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise GraphRepositoryError(f"创建关系失败: {e}")

    def get_node_relationships(self, node_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """
        获取节点的所有关系

        Args:
            node_id: 节点ID
            direction: 关系方向 (incoming, outgoing, both)

        Returns:
            关系信息列表，每条包含关系、源节点和目标节点
        """
        try:
            # 验证节点是否存在
            node = self.get_node(node_id)
            if not node:
                raise NodeNotFoundError(f"节点不存在: {node_id}")

            return self.client.get_relationships_for_node(node_id, direction)
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取节点关系失败: {node_id}, 错误: {e}")
            raise GraphRepositoryError(f"获取节点关系失败: {e}")

    # ========== 图查询 ==========

    def get_graph_data(self, filter_type: Optional[str] = None,
                       search_term: Optional[str] = None,
                       limit: Optional[int] = None) -> Dict[str, Any]:
        """
        获取知识图谱数据（用于可视化）

        Args:
            filter_type: 过滤节点类型
            search_term: 搜索关键词
            limit: 返回节点数量限制

        Returns:
            图谱数据，包含节点和边
        """
        try:
            # 获取节点
            if search_term:
                nodes = self.search_nodes(search_term, filter_type)
            elif filter_type and filter_type != "all":
                nodes = self.get_nodes_by_type(filter_type, limit or 1000)
            else:
                # 获取所有类型的节点，但限制数量
                all_nodes = []
                for node_type in NODE_TYPES.keys():
                    type_nodes = self.get_nodes_by_type(node_type, limit or 200)
                    all_nodes.extend(type_nodes)
                    if limit and len(all_nodes) >= limit:
                        all_nodes = all_nodes[:limit]
                        break
                nodes = all_nodes

            # 获取与这些节点相关的边
            node_ids = {node.id for node in nodes}
            edges = []

            # 为每个节点获取关系
            for node_id in node_ids:
                relationships = self.get_node_relationships(node_id, "both")
                for rel_info in relationships:
                    rel = rel_info["relationship"]
                    source_id = rel_info["source_node"]["id"]
                    target_id = rel_info["target_node"]["id"]

                    # 确保源节点和目标节点都在我们的节点集合中
                    if source_id in node_ids and target_id in node_ids:
                        edge = EdgeModel.from_neo4j_relationship(rel)
                        edges.append(edge)

            # 去重边
            unique_edges = []
            seen_edge_ids = set()
            for edge in edges:
                if edge.id not in seen_edge_ids:
                    seen_edge_ids.add(edge.id)
                    unique_edges.append(edge)

            return {
                "nodes": [node.__dict__ for node in nodes],
                "edges": [edge.__dict__ for edge in unique_edges]
            }

        except Exception as e:
            logger.error(f"获取图谱数据失败: {e}")
            raise GraphRepositoryError(f"获取图谱数据失败: {e}")

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        获取图谱统计信息

        Returns:
            统计信息
        """
        try:
            stats = self.client.get_graph_stats()

            # 添加节点类型统计
            node_type_counts = {}
            for node_type in NODE_TYPES.keys():
                try:
                    nodes = self.get_nodes_by_type(node_type, limit=1)
                    if nodes:
                        # 获取总数（需要优化查询）
                        node_type_counts[node_type] = len(self.get_nodes_by_type(node_type, limit=10000))
                except Exception:
                    node_type_counts[node_type] = 0

            # 添加边类型统计
            edge_type_counts = {}
            for edge_type in EDGE_TYPES.keys():
                edge_type_counts[edge_type] = 0  # 暂时需要优化查询

            return {
                "total_nodes": stats.get("total_nodes", 0),
                "total_edges": stats.get("total_edges", 0),
                "node_types": node_type_counts,
                "edge_types": edge_type_counts,
                "node_type_config": NODE_TYPES,
                "edge_type_config": EDGE_TYPES,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            raise GraphRepositoryError(f"获取图谱统计失败: {e}")

    def get_node_details(self, node_id: str) -> Dict[str, Any]:
        """
        获取节点详细信息

        Args:
            node_id: 节点ID

        Returns:
            节点详情，包含节点信息、相关边和相关节点
        """
        try:
            node = self.get_node(node_id)
            if not node:
                raise NodeNotFoundError(f"节点不存在: {node_id}")

            # 获取相关关系
            relationships = self.get_node_relationships(node_id, "both")

            # 提取相关节点ID
            related_node_ids = set()
            for rel_info in relationships:
                source_id = rel_info["source_node"]["id"]
                target_id = rel_info["target_node"]["id"]
                if source_id != node_id:
                    related_node_ids.add(source_id)
                if target_id != node_id:
                    related_node_ids.add(target_id)

            # 获取相关节点信息（简化版）
            related_nodes = []
            for related_id in list(related_node_ids)[:20]:  # 限制数量
                related_node = self.get_node(related_id)
                if related_node:
                    related_nodes.append({
                        "id": related_node.id,
                        "label": related_node.label,
                        "type": related_node.type,
                        "color": related_node.color
                    })

            return {
                "node": node.__dict__,
                "related_edges": [rel_info["relationship"] for rel_info in relationships],
                "related_nodes": related_nodes,
                "node_type_info": NODE_TYPES.get(node.type, {}),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取节点详情失败: {node_id}, 错误: {e}")
            raise GraphRepositoryError(f"获取节点详情失败: {e}")

    # ========== 高级查询 ==========

    def find_shortest_path(self, source_id: str, target_id: str,
                           max_depth: int = 10,
                           relationship_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        查找最短路径

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_depth: 最大深度
            relationship_types: 允许的关系类型列表

        Returns:
            路径信息
        """
        try:
            # 验证节点是否存在
            source_node = self.get_node(source_id)
            target_node = self.get_node(target_id)

            if not source_node:
                raise NodeNotFoundError(f"源节点不存在: {source_id}")
            if not target_node:
                raise NodeNotFoundError(f"目标节点不存在: {target_id}")

            return self.client.get_shortest_path(source_id, target_id, max_depth, relationship_types)
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"查找最短路径失败: {source_id} -> {target_id}, 错误: {e}")
            raise GraphRepositoryError(f"查找最短路径失败: {e}")

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
        try:
            return self.client.find_attack_paths(start_node_type, end_node_type, max_depth)
        except Exception as e:
            logger.error(f"查找攻击路径失败: {e}")
            raise GraphRepositoryError(f"查找攻击路径失败: {e}")

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
            相关节点信息列表
        """
        try:
            # 验证节点是否存在
            node = self.get_node(node_id)
            if not node:
                raise NodeNotFoundError(f"节点不存在: {node_id}")

            return self.client.get_related_nodes(node_id, relationship_types, max_depth)
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取相关节点失败: {node_id}, 错误: {e}")
            raise GraphRepositoryError(f"获取相关节点失败: {e}")

    # ========== 批量操作 ==========

    def import_mock_data(self) -> Tuple[int, int]:
        """
        导入模拟数据（用于测试和初始化）

        Returns:
            (创建的节点数量, 创建的关系数量)
        """
        try:
            from .models import NodeModel, EdgeModel

            # 模拟节点数据
            mock_nodes = [
                NodeModel(
                    id="target-1",
                    label="目标服务器",
                    type="server",
                    properties={
                        "ip": "192.168.1.100",
                        "os": "Linux",
                        "ports": "22,80,443",
                        "status": "在线",
                        "risk": "中",
                        "last_seen": "2026-04-05T10:30:00Z"
                    },
                    position={"x": 300, "y": 200},
                    size=40,
                    color="#3b82f6"
                ),
                NodeModel(
                    id="vuln-1",
                    label="SQL注入漏洞",
                    type="vulnerability",
                    properties={
                        "cve": "CVE-2024-1234",
                        "severity": "高危",
                        "cvss": 8.5,
                        "exploit": "可用",
                        "patch": "未修复",
                        "discovered": "2026-04-04T14:20:00Z"
                    },
                    position={"x": 500, "y": 150},
                    size=35,
                    color="#ef4444"
                ),
                NodeModel(
                    id="user-1",
                    label="管理员账户",
                    type="user",
                    properties={
                        "username": "admin",
                        "role": "管理员",
                        "last_login": "2026-04-05T08:45:00Z",
                        "status": "活跃",
                        "department": "IT"
                    },
                    position={"x": 100, "y": 200},
                    size=35,
                    color="#10b981"
                ),
                NodeModel(
                    id="tool-1",
                    label="NMAP扫描器",
                    type="tool",
                    properties={
                        "tool": "nmap",
                        "version": "7.94",
                        "findings": 15,
                        "success": True,
                        "last_run": "2026-04-05T11:20:00Z"
                    },
                    position={"x": 100, "y": 300},
                    size=30,
                    color="#8b5cf6"
                )
            ]

            # 模拟关系数据
            mock_edges = [
                EdgeModel(
                    id="edge-1",
                    source="tool-1",
                    target="target-1",
                    label="扫描发现",
                    type="discovery",
                    properties={
                        "timestamp": "2026-04-05T11:20:00Z",
                        "method": "端口扫描",
                        "confidence": "高"
                    },
                    strength=0.9
                ),
                EdgeModel(
                    id="edge-2",
                    source="target-1",
                    target="vuln-1",
                    label="存在漏洞",
                    type="has_vulnerability",
                    properties={
                        "timestamp": "2026-04-05T11:25:00Z",
                        "scanner": "nmap",
                        "confirmed": True
                    },
                    strength=0.8
                ),
                EdgeModel(
                    id="edge-3",
                    source="user-1",
                    target="target-1",
                    label="访问权限",
                    type="has_access",
                    properties={
                        "timestamp": "2026-04-05T08:45:00Z",
                        "access_level": "管理员",
                        "method": "SSH密钥"
                    },
                    strength=0.7
                )
            ]

            # 批量导入
            node_count = self.client.bulk_create_nodes(mock_nodes)
            edge_count = self.client.bulk_create_relationships(mock_edges)

            logger.info(f"导入模拟数据完成: {node_count} 个节点, {edge_count} 个关系")
            return node_count, edge_count

        except Exception as e:
            logger.error(f"导入模拟数据失败: {e}")
            raise GraphRepositoryError(f"导入模拟数据失败: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            is_healthy = self.client.health_check()
            stats = self.get_graph_stats()

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "knowledge-graph-repository",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": {
                    "total_nodes": stats.get("total_nodes", 0),
                    "total_edges": stats.get("total_edges", 0),
                    "node_types": len(NODE_TYPES),
                    "edge_types": len(EDGE_TYPES)
                }
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "service": "knowledge-graph-repository",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }


# 全局仓库实例
_repository_instance: Optional[KnowledgeGraphRepository] = None


def get_repository() -> KnowledgeGraphRepository:
    """
    获取全局知识图谱仓库实例

    Returns:
        KnowledgeGraphRepository实例
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = KnowledgeGraphRepository()
    return _repository_instance