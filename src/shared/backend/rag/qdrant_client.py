# -*- coding: utf-8 -*-
"""
Qdrant RAG 客户端
提供向量存储和语义搜索功能
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# 延迟导入，避免启动时依赖问题
_qdrant_client = None
_sentence_transformer = None


def _get_qdrant_client():
    """延迟获取 Qdrant 客户端"""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient
        except ImportError:
            logger.warning("qdrant-client 未安装，RAG 功能将不可用")
            _qdrant_client = None
    return _qdrant_client


def _get_sentence_transformer():
    """延迟获取 SentenceTransformer"""
    global _sentence_transformer
    if _sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformer = SentenceTransformer
        except ImportError:
            logger.warning("sentence-transformers 未安装，RAG 功能将不可用")
            _sentence_transformer = None
    return _sentence_transformer


@dataclass
class KnowledgeDocument:
    """知识文档"""
    id: str
    title: str
    content: str
    category: str  # "tool_guide", "exploit_method", "cve", "technique"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    content: str
    score: float
    category: str
    title: str
    tags: List[str]
    metadata: Dict[str, Any]


class QdrantRAGClient:
    """
    Qdrant RAG 客户端

    提供知识存储和语义搜索功能，用于增强 P-E-R Agent 的智能决策
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        embedding_model: str = "BAAI/bge-small-zh-v1.5",
        collection_name: str = "security_knowledge",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        初始化 RAG 客户端

        Args:
            host: Qdrant 主机
            port: Qdrant 端口
            embedding_model: 嵌入模型名称
            collection_name: 集合名称
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠
        """
        self.host = host
        self.port = port
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 延迟初始化
        self._client = None
        self._encoder = None
        self._initialized = False

        logger.info(f"QdrantRAGClient 配置完成: {host}:{port}, model={embedding_model}")

    def _ensure_initialized(self) -> bool:
        """确保客户端已初始化"""
        if self._initialized:
            return True

        # 初始化 Qdrant 客户端
        QdrantClient = _get_qdrant_client()
        if QdrantClient is None:
            logger.error("Qdrant 客户端不可用")
            return False

        try:
            self._client = QdrantClient(host=self.host, port=self.port)
            logger.debug(f"Qdrant 客户端已连接: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"连接 Qdrant 失败: {e}")
            return False

        # 初始化嵌入模型
        SentenceTransformer = _get_sentence_transformer()
        if SentenceTransformer is None:
            logger.error("SentenceTransformer 不可用")
            return False

        try:
            self._encoder = SentenceTransformer(self.embedding_model_name)
            logger.debug(f"嵌入模型已加载: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}")
            return False

        self._initialized = True
        return True

    async def initialize_collection(self, recreate: bool = False) -> bool:
        """
        初始化集合

        Args:
            recreate: 是否重建集合

        Returns:
            是否成功
        """
        if not self._ensure_initialized():
            return False

        try:
            from qdrant_client.models import Distance, VectorParams

            # 检查集合是否存在
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name in collection_names:
                if recreate:
                    self._client.delete_collection(self.collection_name)
                    logger.info(f"已删除集合: {self.collection_name}")
                else:
                    logger.info(f"集合已存在: {self.collection_name}")
                    return True

            # 创建集合
            vector_size = self._encoder.get_sentence_embedding_dimension()
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )

            logger.info(f"已创建集合: {self.collection_name}, 向量维度: {vector_size}")
            return True

        except Exception as e:
            logger.error(f"初始化集合失败: {e}")
            return False

    def _chunk_text(self, text: str) -> List[str]:
        """
        分割文本为块

        Args:
            text: 原始文本

        Returns:
            文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # 尝试在句子边界分割
            if end < len(text):
                # 查找最近的句子边界
                for sep in ['。', '！', '？', '.', '!', '?', '\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break

            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]

    async def index_documents(
        self,
        documents: List[KnowledgeDocument],
        batch_size: int = 100
    ) -> int:
        """
        索引文档

        Args:
            documents: 文档列表
            batch_size: 批量大小

        Returns:
            成功索引的数量
        """
        if not self._ensure_initialized():
            return 0

        try:
            from qdrant_client.models import PointStruct

            # 确保集合存在
            await self.initialize_collection()

            indexed_count = 0
            points = []

            for doc in documents:
                # 分割文档
                chunks = self._chunk_text(doc.content)

                # 生成嵌入向量
                vectors = self._encoder.encode(chunks, show_progress_bar=False)

                for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    point_id = f"{doc.id}_{i}"
                    points.append(PointStruct(
                        id=point_id,
                        vector=vector.tolist(),
                        payload={
                            "doc_id": doc.id,
                            "title": doc.title,
                            "content": chunk,
                            "category": doc.category,
                            "tags": doc.tags,
                            "source": doc.source,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "metadata": doc.metadata
                        }
                    ))

                    # 批量上传
                    if len(points) >= batch_size:
                        self._client.upsert(
                            collection_name=self.collection_name,
                            points=points
                        )
                        indexed_count += len(points)
                        points = []

            # 上传剩余的点
            if points:
                self._client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                indexed_count += len(points)

            logger.info(f"已索引 {indexed_count} 个文档块")
            return indexed_count

        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            return 0

    async def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回数量
            category_filter: 类别过滤
            score_threshold: 分数阈值

        Returns:
            搜索结果列表
        """
        if not self._ensure_initialized():
            return []

        try:
            # 生成查询向量
            query_vector = self._encoder.encode(query, show_progress_bar=False)

            # 构建过滤条件
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            query_filter = None
            if category_filter:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=category_filter)
                        )
                    ]
                )

            # 搜索
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=query_filter,
                score_threshold=score_threshold
            )

            # 转换结果
            search_results = []
            for hit in results:
                payload = hit.payload
                search_results.append(SearchResult(
                    id=hit.id,
                    content=payload.get("content", ""),
                    score=hit.score,
                    category=payload.get("category", ""),
                    title=payload.get("title", ""),
                    tags=payload.get("tags", []),
                    metadata=payload.get("metadata", {})
                ))

            return search_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def search_tool_guide(
        self,
        tool_name: str,
        query: str = "",
        top_k: int = 3
    ) -> List[SearchResult]:
        """
        搜索工具使用指南

        Args:
            tool_name: 工具名称
            query: 额外查询词
            top_k: 返回数量

        Returns:
            搜索结果
        """
        full_query = f"{tool_name} 使用方法 {query}".strip()
        return await self.search(
            query=full_query,
            top_k=top_k,
            category_filter="tool_guide"
        )

    async def search_exploit_method(
        self,
        vuln_type: str,
        top_k: int = 3
    ) -> List[SearchResult]:
        """
        搜索漏洞利用方法

        Args:
            vuln_type: 漏洞类型
            top_k: 返回数量

        Returns:
            搜索结果
        """
        return await self.search(
            query=f"{vuln_type} 漏洞利用方法",
            top_k=top_k,
            category_filter="exploit_method"
        )

    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否成功
        """
        if not self._ensure_initialized():
            return False

        try:
            # 获取所有相关点
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            points = self._client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )
                    ]
                ),
                limit=1000
            )[0]

            if points:
                point_ids = [p.id for p in points]
                self._client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                logger.info(f"已删除文档: {doc_id}, 共 {len(point_ids)} 个块")

            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息

        Returns:
            统计信息字典
        """
        if not self._ensure_initialized():
            return {}

        try:
            info = self._client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
                "indexed_vectors_count": info.indexed_vectors_count,
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


# 全局实例
_rag_client: Optional[QdrantRAGClient] = None


def get_rag_client() -> Optional[QdrantRAGClient]:
    """获取全局 RAG 客户端实例"""
    global _rag_client
    if _rag_client is None:
        try:
            from ..config import get_settings
            settings = get_settings()
            _rag_client = QdrantRAGClient(
                host=settings.rag.qdrant_host,
                port=settings.rag.qdrant_port,
                embedding_model=settings.rag.embedding_model,
                collection_name=settings.rag.collection_name,
                chunk_size=settings.rag.chunk_size,
                chunk_overlap=settings.rag.chunk_overlap
            )
        except Exception as e:
            logger.error(f"初始化 RAG 客户端失败: {e}")
    return _rag_client
