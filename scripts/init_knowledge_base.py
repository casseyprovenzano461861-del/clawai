# -*- coding: utf-8 -*-
"""
知识库初始化脚本（增强版）
初始化 Qdrant 并导入内置安全知识
"""

import asyncio
import sys
import os
import logging
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 HuggingFace 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


async def main():
    print("=" * 60)
    print("ClawAI 知识库初始化")
    print("=" * 60)
    
    # 导入模块
    print("\n📦 导入模块...")
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    from src.shared.backend.rag.knowledge_loader import KnowledgeLoader
    
    # 连接 Qdrant
    print("\n🔌 连接 Qdrant...")
    client = QdrantClient(host="localhost", port=16333)
    print("✅ 连接成功")
    
    # 加载嵌入模型
    print("\n🤖 加载嵌入模型 (BGE-small-zh-v1.5)...")
    encoder = SentenceTransformer('BAAI/bge-small-zh-v1.5')
    vector_size = encoder.get_sentence_embedding_dimension()
    print(f"✅ 模型加载成功，向量维度: {vector_size}")
    
    # 创建集合
    collection_name = "security_knowledge"
    print(f"\n📁 创建集合: {collection_name}")
    
    # 删除旧集合
    try:
        client.delete_collection(collection_name)
        print("   已删除旧集合")
    except:
        pass
    
    # 创建新集合
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    print("✅ 集合创建成功")
    
    # 加载内置知识
    print("\n📚 加载内置知识...")
    loader = KnowledgeLoader()
    documents = loader.load_builtin_knowledge()
    print(f"✅ 加载了 {len(documents)} 条知识")
    
    # 索引文档
    print("\n🔄 开始索引文档...")
    indexed_count = 0
    points = []
    
    for i, doc in enumerate(documents):
        print(f"   处理: {doc.title}...")
        
        # 分割文本
        content = doc.content
        chunks = [content] if len(content) <= 500 else [
            content[j:j+500] for j in range(0, len(content), 450)
        ]
        
        # 生成向量
        vectors = encoder.encode(chunks, show_progress_bar=False)
        
        # 创建点
        for j, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),  # 使用 UUID
                vector=vector.tolist(),
                payload={
                    "doc_id": doc.id,
                    "title": doc.title,
                    "content": chunk,
                    "category": doc.category,
                    "tags": doc.tags,
                    "source": doc.source,
                }
            ))
    
    # 批量上传
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        indexed_count = len(points)
    
    print(f"\n✅ 索引完成: {indexed_count} 个文档块")
    
    # 获取集合统计
    info = client.get_collection(collection_name)
    print(f"\n📊 集合统计:")
    print(f"   - 点数量: {info.points_count}")
    
    # 测试搜索
    print("\n🔍 测试语义搜索...")
    test_queries = [
        "nmap 端口扫描",
        "SQL注入漏洞利用",
        "渗透测试方法"
    ]
    
    for query in test_queries:
        print(f"\n   查询: '{query}'")
        query_vector = encoder.encode(query)
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector.tolist(),
            limit=2
        )
        for r in results.points:
            print(f"   → {r.payload['title']} (score: {r.score:.3f})")
    
    print("\n" + "=" * 60)
    print("🎉 知识库初始化成功!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
