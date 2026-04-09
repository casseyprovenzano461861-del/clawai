# -*- coding: utf-8 -*-
"""
数据导入器基类
定义扫描结果到知识图谱的转换接口
"""

import abc
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models import NodeModel, EdgeModel
from ..repository import KnowledgeGraphRepository

logger = logging.getLogger(__name__)


class BaseImporter(abc.ABC):
    """数据导入器基类"""

    def __init__(self, repository: Optional[KnowledgeGraphRepository] = None):
        """
        初始化导入器

        Args:
            repository: 知识图谱仓库实例，如果为None则创建新实例
        """
        self.repository = repository or KnowledgeGraphRepository()

    @abc.abstractmethod
    def can_import(self, data: Any) -> bool:
        """
        检查是否可以导入该数据

        Args:
            data: 要检查的数据

        Returns:
            是否可以导入
        """
        pass

    @abc.abstractmethod
    def import_data(self, data: Any, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        导入数据到知识图谱

        Args:
            data: 要导入的数据
            scan_id: 扫描任务ID（可选）

        Returns:
            导入结果统计
        """
        pass

    def create_node(self, node_data: Dict[str, Any]) -> NodeModel:
        """
        创建节点

        Args:
            node_data: 节点数据

        Returns:
            创建的节点模型
        """
        try:
            return self.repository.create_node(node_data)
        except Exception as e:
            logger.error(f"创建节点失败: {node_data.get('id', 'unknown')}, 错误: {e}")
            raise

    def create_relationship(self, edge_data: Dict[str, Any]) -> EdgeModel:
        """
        创建关系

        Args:
            edge_data: 关系数据

        Returns:
            创建的关系模型
        """
        try:
            return self.repository.create_relationship(edge_data)
        except Exception as e:
            logger.error(f"创建关系失败: {edge_data.get('id', 'unknown')}, 错误: {e}")
            raise

    def _generate_node_id(self, node_type: str, identifier: str, scan_id: Optional[str] = None) -> str:
        """
        生成节点ID

        Args:
            node_type: 节点类型
            identifier: 标识符
            scan_id: 扫描ID（可选）

        Returns:
            节点ID
        """
        if scan_id:
            return f"{node_type}-{scan_id}-{identifier}"
        return f"{node_type}-{identifier}"

    def _generate_edge_id(self, edge_type: str, source_id: str, target_id: str) -> str:
        """
        生成边ID

        Args:
            edge_type: 边类型
            source_id: 源节点ID
            target_id: 目标节点ID

        Returns:
            边ID
        """
        return f"edge-{edge_type}-{source_id}-{target_id}"

    def _timestamp_to_iso(self, timestamp: Any) -> str:
        """
        转换时间戳为ISO格式

        Args:
            timestamp: 时间戳（可以是datetime对象、字符串、整数等）

        Returns:
            ISO格式时间字符串
        """
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()
        elif isinstance(timestamp, str):
            # 尝试解析字符串
            try:
                # 简单处理，如果已经是ISO格式或类似格式
                if 'T' in timestamp:
                    return timestamp
                else:
                    # 添加默认时间
                    return f"{timestamp}T00:00:00Z"
            except Exception as e:
                return datetime.now().isoformat()
        else:
            return datetime.now().isoformat()