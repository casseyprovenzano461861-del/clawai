# -*- coding: utf-8 -*-
"""
简化的知识库测试脚本
仅测试 Qdrant 连接，不下载嵌入模型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_qdrant_connection():
    """测试 Qdrant 连接"""
    print("=" * 60)
    print("Qdrant 连接测试")
    print("=" * 60)
    
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=16333)
        
        # 获取集合列表
        collections = client.get_collections()
        print(f"\n✅ 连接成功!")
        print(f"   现有集合: {[c.name for c in collections.collections]}")
        
        # 创建测试集合
        from qdrant_client.models import Distance, VectorParams, PointStruct
        import uuid
        
        test_collection = "test_collection"
        
        # 删除已存在的测试集合
        try:
            client.delete_collection(test_collection)
        except:
            pass
        
        # 创建新集合
        client.create_collection(
            collection_name=test_collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"\n✅ 创建测试集合: {test_collection}")
        
        # 插入测试数据
        import random
        test_vector = [random.random() for _ in range(384)]
        client.upsert(
            collection_name=test_collection,
            points=[
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=test_vector,
                    payload={"test": "hello", "category": "demo"}
                )
            ]
        )
        print("✅ 插入测试向量成功")
        
        # 搜索测试
        results = client.query_points(
            collection_name=test_collection,
            query=test_vector,
            limit=1
        )
        print(f"✅ 搜索测试成功: {len(results.points)} 条结果")
        
        # 清理
        client.delete_collection(test_collection)
        print("✅ 清理测试集合")
        
        print("\n" + "=" * 60)
        print("🎉 Qdrant 服务正常运行!")
        print("=" * 60)
        print("\n📝 注意: 嵌入模型 (BGE-small-zh) 因网络问题未能下载")
        print("   RAG 功能将在模型下载后可用")
        print("   你可以稍后手动下载: ")
        print("   pip download BAAI/bge-small-zh-v1.5 或设置代理")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_qdrant_connection()
    sys.exit(0 if success else 1)
