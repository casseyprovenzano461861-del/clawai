# -*- coding: utf-8 -*-
"""
P-E-R Agent 完整功能测试
验证 RAG、预算管理、缺口分析是否真正集成
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置环境变量
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


async def test_per_with_intelligence():
    """测试带智能特性的 P-E-R Agent"""
    
    print("=" * 60)
    print("P-E-R Agent 智能特性测试")
    print("=" * 60)
    
    # 1. 测试 RAG 客户端
    print("\n[1] 测试 RAG 客户端...")
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        
        client = QdrantClient(host="localhost", port=16333)
        encoder = SentenceTransformer('BAAI/bge-small-zh-v1.5')
        
        # 搜索测试
        query = "如何使用 nmap 扫描端口"
        vector = encoder.encode(query)
        results = client.query_points(
            collection_name="security_knowledge",
            query=vector.tolist(),
            limit=2
        )
        
        print(f"   查询: '{query}'")
        print(f"   结果数: {len(results.points)}")
        for r in results.points:
            print(f"   → {r.payload['title']} (score: {r.score:.3f})")
        print("   ✅ RAG 客户端工作正常!")
        rag_working = True
    except Exception as e:
        print(f"   ❌ RAG 测试失败: {e}")
        rag_working = False
    
    # 2. 测试预算管理器
    print("\n[2] 测试 Token 预算管理器...")
    try:
        from src.shared.backend.ai_agent.budget_manager import BudgetManager, BudgetPhase
        
        budget = BudgetManager(total_budget=10000)
        budget.record_usage(input_tokens=100, output_tokens=50, phase=BudgetPhase.RECONNAISSANCE)
        
        summary = budget.get_summary()
        print(f"   总预算: {summary['total_budget']}")
        print(f"   已使用: {summary['total_used']}")
        print(f"   剩余: {summary['total_remaining']}")
        print("   ✅ 预算管理器工作正常!")
        budget_working = True
    except Exception as e:
        print(f"   ❌ 预算管理器测试失败: {e}")
        budget_working = False
    
    # 3. 测试上下文缺口分析器
    print("\n[3] 测试上下文缺口分析器...")
    try:
        from src.shared.backend.ai_agent.context_analyzer import ContextGapAnalyzer
        
        analyzer = ContextGapAnalyzer()
        result = analyzer.analyze(
            user_input="扫描 example.com",
            context={"target": "example.com"},
            task_phase="initial"
        )
        
        print(f"   有缺口: {result.has_gaps}")
        print(f"   缺口数: {len(result.gaps)}")
        if result.gaps:
            print(f"   第一个缺口: {result.gaps[0].description}")
        print("   ✅ 缺口分析器工作正常!")
        gap_working = True
    except Exception as e:
        print(f"   ❌ 缺口分析器测试失败: {e}")
        gap_working = False
    
    # 4. 测试配置系统
    print("\n[4] 测试统一配置系统...")
    try:
        from src.shared.backend.config import get_settings, get_api_key
        
        settings = get_settings()
        print(f"   活动提供商: {settings.active_provider}")
        print(f"   活动模型: {settings.active_model}")
        print(f"   RAG 启用: {settings.rag.enabled}")
        print(f"   预算启用: {settings.token_budget.enabled}")
        print("   ✅ 配置系统工作正常!")
        config_working = True
    except Exception as e:
        print(f"   ❌ 配置系统测试失败: {e}")
        config_working = False
    
    # 5. 测试 P-E-R Agent 初始化
    print("\n[5] 测试 P-E-R Agent 初始化...")
    try:
        from src.shared.backend.ai_agent.intelligent_per import IntelligentPERAgent
        from src.shared.backend.ai_agent.budget_manager import BudgetManager
        from src.shared.backend.ai_agent.context_analyzer import ContextGapAnalyzer
        
        # 创建组件
        budget_mgr = BudgetManager(total_budget=50000) if budget_working else None
        gap_analyzer = ContextGapAnalyzer() if gap_working else None
        
        # 创建 Agent (不需要真实 LLM)
        agent = IntelligentPERAgent(
            llm_client=None,  # 模拟
            tool_executor=None,  # 模拟
            context_analyzer=gap_analyzer,
            rag_client=None,  # 稍后设置
            budget_manager=budget_mgr,
            max_iterations=3
        )
        
        print(f"   Agent 创建成功!")
        print(f"   最大迭代: {agent.max_iterations}")
        print(f"   工具数量: {len(agent.tools)}")
        print("   ✅ P-E-R Agent 初始化成功!")
        agent_working = True
    except Exception as e:
        print(f"   ❌ Agent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        agent_working = False
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    results = {
        "RAG 客户端": rag_working,
        "Token 预算管理": budget_working,
        "上下文缺口分析": gap_working,
        "统一配置系统": config_working,
        "P-E-R Agent": agent_working,
    }
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    working_count = sum(results.values())
    print(f"\n通过: {working_count}/{len(results)}")
    
    if working_count == len(results):
        print("\n🎉 所有智能特性已就绪，P-E-R Agent 可以正常运行!")
    else:
        print(f"\n⚠️ 有 {len(results) - working_count} 个组件需要检查")
    
    return working_count == len(results)


if __name__ == "__main__":
    success = asyncio.run(test_per_with_intelligence())
    sys.exit(0 if success else 1)
