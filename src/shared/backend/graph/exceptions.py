# -*- coding: utf-8 -*-
"""
知识图谱异常定义
"""


class GraphRepositoryError(Exception):
    """知识图谱仓库基础异常"""
    pass


class NodeNotFoundError(GraphRepositoryError):
    """节点未找到异常"""
    def __init__(self, node_id: str):
        super().__init__(f"节点未找到: {node_id}")
        self.node_id = node_id


class EdgeNotFoundError(GraphRepositoryError):
    """边未找到异常"""
    def __init__(self, edge_id: str):
        super().__init__(f"边未找到: {edge_id}")
        self.edge_id = edge_id


class Neo4jConnectionError(GraphRepositoryError):
    """Neo4j连接异常"""
    def __init__(self, message: str = "Neo4j连接失败"):
        super().__init__(message)


class Neo4jQueryError(GraphRepositoryError):
    """Neo4j查询异常"""
    def __init__(self, query: str, error: str):
        super().__init__(f"Neo4j查询失败: {error}\n查询: {query[:200]}...")
        self.query = query
        self.error = error


class InvalidNodeTypeError(GraphRepositoryError):
    """无效节点类型异常"""
    def __init__(self, node_type: str, valid_types: list):
        super().__init__(f"无效的节点类型: {node_type}，有效类型: {valid_types}")
        self.node_type = node_type
        self.valid_types = valid_types


class InvalidEdgeTypeError(GraphRepositoryError):
    """无效边类型异常"""
    def __init__(self, edge_type: str, valid_types: list):
        super().__init__(f"无效的边类型: {edge_type}，有效类型: {valid_types}")
        self.edge_type = edge_type
        self.valid_types = valid_types


class DataValidationError(GraphRepositoryError):
    """数据验证异常"""
    def __init__(self, field: str, value: Any, message: str = ""):
        error_msg = f"数据验证失败: 字段 '{field}' 值 '{value}' 无效"
        if message:
            error_msg += f" - {message}"
        super().__init__(error_msg)
        self.field = field
        self.value = value


class BulkOperationError(GraphRepositoryError):
    """批量操作异常"""
    def __init__(self, operation: str, success_count: int, total_count: int, errors: list):
        super().__init__(
            f"批量操作 '{operation}' 部分失败: 成功 {success_count}/{total_count}，错误: {errors}"
        )
        self.operation = operation
        self.success_count = success_count
        self.total_count = total_count
        self.errors = errors