# -*- coding: utf-8 -*-
"""
知识图谱API模块 - FastAPI版本
基于PentAGI Graphiti架构的安全实体关系可视化后端服务
使用Neo4j图数据库存储
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..graph.repository import get_repository
from ..graph.exceptions import GraphRepositoryError, NodeNotFoundError, EdgeNotFoundError
from ..graph.models import NODE_TYPES, EDGE_TYPES

# 创建FastAPI路由器
router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["知识图谱"])
logger = logging.getLogger(__name__)


# 依赖注入：获取知识图谱仓库
def get_knowledge_graph_repository():
    """获取知识图谱仓库依赖"""
    return get_repository()


@router.get("/graph", summary="获取知识图谱数据")
async def get_knowledge_graph(
    filter_type: Optional[str] = Query(None, description="过滤节点类型 (all表示所有类型)"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: Optional[int] = Query(None, description="返回节点数量限制"),
    repository=Depends(get_knowledge_graph_repository)
):
    """
    获取完整的知识图谱数据，包括节点和边
    """
    try:
        graph_data = repository.get_graph_data(filter_type, search, limit)

        # 添加元数据
        metadata = {
            "total_nodes": len(graph_data.get("nodes", [])),
            "total_edges": len(graph_data.get("edges", [])),
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "data_source": "neo4j"
        }

        return {
            "success": True,
            "data": graph_data,
            "metadata": metadata
        }
    except GraphRepositoryError as e:
        logger.error(f"获取知识图谱数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识图谱数据失败: {str(e)}")
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/stats", summary="获取图谱统计信息")
async def get_graph_stats(
    repository=Depends(get_knowledge_graph_repository)
):
    """
    获取知识图谱的统计信息
    """
    try:
        stats = repository.get_graph_stats()
        return {
            "success": True,
            "data": stats
        }
    except GraphRepositoryError as e:
        logger.error(f"获取图谱统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/node/{node_id}", summary="获取节点详情")
async def get_node_details(
    node_id: str,
    repository=Depends(get_knowledge_graph_repository)
):
    """
    根据节点ID获取节点详情
    """
    try:
        node_details = repository.get_node_details(node_id)
        return {
            "success": True,
            "data": node_details
        }
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 未找到")
    except GraphRepositoryError as e:
        logger.error(f"获取节点详情失败: {node_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取节点详情失败: {str(e)}")


@router.get("/edge/{edge_id}", summary="获取边详情")
async def get_edge_details(
    edge_id: str,
    repository=Depends(get_knowledge_graph_repository)
):
    """
    根据边ID获取边详情
    """
    try:
        # 暂时返回简单响应，后续实现具体逻辑
        # TODO: 实现从数据库获取边详情的逻辑
        raise HTTPException(status_code=501, detail="获取边详情功能暂未实现")
    except Exception as e:
        logger.error(f"获取边详情失败: {edge_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取边详情失败: {str(e)}")


@router.get("/search", summary="搜索图谱")
async def search_graph(
    query: str = Query(..., description="搜索关键词"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    limit: int = Query(10, description="返回结果数量限制"),
    repository=Depends(get_knowledge_graph_repository)
):
    """
    搜索知识图谱中的节点和边
    """
    try:
        # 搜索节点
        nodes = repository.search_nodes(query, node_type)
        if limit and len(nodes) > limit:
            nodes = nodes[:limit]

        # 暂时只返回节点搜索结果，边搜索后续实现
        results = {
            "nodes": [node.__dict__ for node in nodes],
            "edges": []  # TODO: 实现边搜索
        }

        metadata = {
            "query": query,
            "node_type_filter": node_type,
            "node_count": len(results["nodes"]),
            "edge_count": len(results["edges"]),
            "total_results": len(results["nodes"]) + len(results["edges"])
        }

        return {
            "success": True,
            "data": results,
            "metadata": metadata
        }
    except GraphRepositoryError as e:
        logger.error(f"搜索图谱失败: {query}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check(
    repository=Depends(get_knowledge_graph_repository)
):
    """
    知识图谱API健康检查
    """
    try:
        health_info = repository.health_check()
        return health_info
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "knowledge-graph-api",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/config", summary="获取配置信息")
async def get_config():
    """
    获取知识图谱配置信息
    """
    return {
        "success": True,
        "data": {
            "node_types": NODE_TYPES,
            "edge_types": EDGE_TYPES,
            "supported_operations": [
                "get_graph", "get_stats", "get_node_details",
                "get_edge_details", "search", "health_check"
            ],
            "api_version": "1.0.0",
            "data_source": "neo4j",
            "timestamp": datetime.now().isoformat()
        }
    }


@router.get("/path/shortest", summary="获取最短路径")
async def get_shortest_path(
    source: str = Query(..., description="源节点ID"),
    target: str = Query(..., description="目标节点ID"),
    max_depth: int = Query(10, description="最大路径深度", ge=1, le=50),
    relationship_types: Optional[List[str]] = Query(None, description="允许的关系类型列表"),
    repository=Depends(get_knowledge_graph_repository)
):
    """
    获取两个节点之间的最短路径
    """
    try:
        path = repository.find_shortest_path(source, target, max_depth, relationship_types)
        if not path:
            raise HTTPException(status_code=404, detail="未找到路径")

        return {
            "success": True,
            "data": path
        }
    except NodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GraphRepositoryError as e:
        logger.error(f"获取最短路径失败: {source} -> {target}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取路径失败: {str(e)}")


@router.get("/path/attack", summary="获取攻击路径")
async def get_attack_paths(
    start_type: str = Query("vulnerability", description="起始节点类型"),
    end_type: str = Query("asset", description="结束节点类型"),
    max_depth: int = Query(5, description="最大路径深度", ge=1, le=20),
    repository=Depends(get_knowledge_graph_repository)
):
    """
    查找攻击路径（从起始节点类型到结束节点类型）
    """
    try:
        paths = repository.find_attack_paths(start_type, end_type, max_depth)
        return {
            "success": True,
            "data": {
                "paths": paths,
                "count": len(paths),
                "start_type": start_type,
                "end_type": end_type,
                "max_depth": max_depth
            }
        }
    except GraphRepositoryError as e:
        logger.error(f"获取攻击路径失败: {start_type} -> {end_type}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取攻击路径失败: {str(e)}")


@router.get("/node/{node_id}/related", summary="获取相关节点")
async def get_related_nodes(
    node_id: str,
    relationship_types: Optional[List[str]] = Query(None, description="允许的关系类型列表"),
    max_depth: int = Query(2, description="最大深度", ge=1, le=5),
    repository=Depends(get_knowledge_graph_repository)
):
    """
    获取指定节点的相关节点
    """
    try:
        related_nodes = repository.get_related_nodes(node_id, relationship_types, max_depth)
        return {
            "success": True,
            "data": {
                "node_id": node_id,
                "related_nodes": related_nodes,
                "count": len(related_nodes),
                "max_depth": max_depth
            }
        }
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 未找到")
    except GraphRepositoryError as e:
        logger.error(f"获取相关节点失败: {node_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取相关节点失败: {str(e)}")


@router.post("/import/mock", summary="导入模拟数据")
async def import_mock_data(
    repository=Depends(get_knowledge_graph_repository)
):
    """
    导入模拟数据（仅用于测试和演示）
    """
    try:
        node_count, edge_count = repository.import_mock_data()
        return {
            "success": True,
            "data": {
                "imported_nodes": node_count,
                "imported_edges": edge_count,
                "message": "模拟数据导入完成"
            }
        }
    except GraphRepositoryError as e:
        logger.error(f"导入模拟数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入模拟数据失败: {str(e)}")