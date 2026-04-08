# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) 模块

提供知识存储和语义搜索功能，用于增强 P-E-R Agent 的智能决策。
"""

from .qdrant_client import (
    QdrantRAGClient,
    KnowledgeDocument,
    SearchResult,
    get_rag_client
)

from .knowledge_loader import (
    KnowledgeLoader,
    KnowledgeSource,
    get_knowledge_loader,
    initialize_knowledge_base
)

__all__ = [
    # RAG 客户端
    "QdrantRAGClient",
    "KnowledgeDocument",
    "SearchResult",
    "get_rag_client",

    # 知识加载
    "KnowledgeLoader",
    "KnowledgeSource",
    "get_knowledge_loader",
    "initialize_knowledge_base",
]
