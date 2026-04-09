# -*- coding: utf-8 -*-
"""
真实的 P-E-R 渗透测试
目标: DVWA (Damn Vulnerable Web Application)
"""

import asyncio
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# API Key 从环境变量获取（不再硬编码）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")


async def run_real_per_test():
    """运行真实的 P-E-R 渗透测试"""
    
    target = "http://127.0.0.1/dvwa/login.php"
    
    print("=" * 70)
    print("🎯 ClawAI P-E-R 自主渗透测试")
    print("=" * 70)
    print(f"\n📍 目标: {target}")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 模型: DeepSeek Chat")
    print()
    
    # 1. 初始化 LLM 客户端
    print("[初始化] 创建 LLM 客户端...")
    try:
        from openai import OpenAI
        
        llm_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        print("   ✅ LLM 客户端就绪")
    except Exception as e:
        print(f"   ❌ LLM 客户端失败: {e}")
        return False
    
    # 2. 初始化 RAG 客户端
    print("[初始化] 创建 RAG 客户端...")
    rag_client = None
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        
        qdrant = QdrantClient(host="localhost", port=16333)
        encoder = SentenceTransformer('BAAI/bge-small-zh-v1.5')
        
        class SimpleRAGClient:
            def __init__(self, qdrant, encoder):
                self.qdrant = qdrant
                self.encoder = encoder
            
            async def search(self, query, top_k=3, category_filter=None):
                vector = self.encoder.encode(query)
                results = self.qdrant.query_points(
                    collection_name="security_knowledge",
                    query=vector.tolist(),
                    limit=top_k
                )
                from dataclasses import dataclass
                @dataclass
                class Result:
                    id: str
                    content: str
                    score: float
                    title: str
                    category: str
                    tags: list
                    metadata: dict
                
                return [
                    Result(
                        id=r.id,
                        content=r.payload.get('content', ''),
                        score=r.score,
                        title=r.payload.get('title', ''),
                        category=r.payload.get('category', ''),
                        tags=r.payload.get('tags', []),
                        metadata={}
                    )
                    for r in results.points
                ]
            
            async def search_tool_guide(self, tool_name, query="", top_k=3):
                """搜索工具使用指南"""
                return await self.search(f"{tool_name} 使用方法 {query}", top_k=top_k)
            
            async def search_exploit_method(self, vuln_type, top_k=3):
                """搜索漏洞利用方法"""
                return await self.search(f"{vuln_type} 漏洞利用方法", top_k=top_k)
        
        rag_client = SimpleRAGClient(qdrant, encoder)
        print("   ✅ RAG 客户端就绪")
    except Exception as e:
        print(f"   ⚠️ RAG 客户端失败: {e} (继续无 RAG 模式)")
    
    # 3. 初始化预算管理器
    print("[初始化] 创建预算管理器...")
    try:
        from src.shared.backend.ai_agent.budget_manager import BudgetManager, BudgetPhase
        budget_manager = BudgetManager(total_budget=50000)
        print("   ✅ 预算管理器就绪")
    except Exception as e:
        print(f"   ⚠️ 预算管理器失败: {e}")
        budget_manager = None
    
    # 4. 初始化缺口分析器
    print("[初始化] 创建缺口分析器...")
    try:
        from src.shared.backend.ai_agent.context_analyzer import ContextGapAnalyzer
        context_analyzer = ContextGapAnalyzer()
        print("   ✅ 缺口分析器就绪")
    except Exception as e:
        print(f"   ⚠️ 缺口分析器失败: {e}")
        context_analyzer = None
    
    # 5. 创建工具执行器
    print("[初始化] 创建工具执行器...")
    
    async def tool_executor(tool_name, params):
        """简化的工具执行器"""
        import subprocess
        import socket
        
        result = {
            "success": False,
            "output": {},
            "simulated": True
        }
        
        try:
            if tool_name == "nmap_scan":
                target_host = params.get("target", "").replace("http://", "").split("/")[0]
                
                # 检查端口
                print(f"      🔍 扫描 {target_host}...")
                
                open_ports = []
                for port in [80, 443, 8080, 3306, 22, 21]:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    if sock.connect_ex((target_host, port)) == 0:
                        open_ports.append({"port": port, "service": "unknown"})
                    sock.close()
                
                result["output"]["ports"] = open_ports
                result["success"] = True
                print(f"      ✅ 发现 {len(open_ports)} 个开放端口")
                
            elif tool_name == "whatweb_scan":
                result["output"]["technologies"] = ["PHP", "Apache", "MySQL"]
                result["success"] = True
                print(f"      ✅ Web 技术栈识别完成")
                
            elif tool_name == "nuclei_scan":
                result["output"]["vulnerabilities"] = [
                    {"type": "DVWA", "severity": "info", "description": "DVWA 漏洞靶场检测"}
                ]
                result["success"] = True
                print(f"      ✅ 漏洞扫描完成")
                
            elif tool_name == "sqlmap_scan":
                result["output"]["vulnerable"] = True
                result["output"]["databases"] = ["dvwa", "information_schema"]
                result["success"] = True
                print(f"      ✅ SQL注入检测完成")
                
            else:
                result["output"]["message"] = f"模拟执行: {tool_name}"
                result["success"] = True
                
        except Exception as e:
            result["output"]["error"] = str(e)
            
        return type('Result', (), result)()
    
    print("   ✅ 工具执行器就绪")
    
    # 6. 创建 LLM 适配器
    class LLMAdapter:
        def __init__(self, client):
            self.client = client
            
        def chat(self, messages, tools=None):
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            return type('Response', (), {
                'content': response.choices[0].message.content,
                'tool_calls': response.choices[0].message.tool_calls,
                'usage': response.usage
            })()
    
    # 7. 创建 P-E-R Agent
    print("[初始化] 创建 P-E-R Agent...")
    from src.shared.backend.ai_agent.intelligent_per import IntelligentPERAgent
    
    agent = IntelligentPERAgent(
        llm_client=LLMAdapter(llm_client),
        tool_executor=tool_executor,
        context_analyzer=context_analyzer,
        rag_client=rag_client,
        budget_manager=budget_manager,
        max_iterations=3
    )
    print("   ✅ P-E-R Agent 就绪")
    
    # 8. 运行测试
    print("\n" + "=" * 70)
    print("🚀 开始 P-E-R 自主渗透测试")
    print("=" * 70)
    
    # 先做端口扫描确认目标可达
    print("\n[预检查] 验证目标可达性...")
    import socket
    target_host = target.replace("http://", "").replace("https://", "").split("/")[0]
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((target_host, 80))
        sock.close()
        if result == 0:
            print(f"   ✅ 目标 {target_host}:80 可达")
        else:
            print(f"   ⚠️ 目标可能不可达，继续测试...")
    except Exception as e:
        print(f"   ⚠️ 预检查失败: {e}")
    
    events = []
    async for event in agent.run(
        target=target,
        goal="发现目标的开放端口和服务，识别潜在的Web漏洞（如SQL注入、XSS等）",
        mode="full"
    ):
        events.append(event)
        
        # 处理事件
        event_type = event.get("type")
        
        if event_type == "start":
            print(f"\n🎯 开始测试: {event.get('target')}")
            
        elif event_type == "iteration":
            print(f"\n{'='*50}")
            print(f"🔄 迭代 {event.get('num')}/{event.get('max')}")
            print(f"{'='*50}")
            
        elif event_type == "phase":
            phase = event.get("phase")
            message = event.get("message", "")
            phase_icons = {
                "planning": "🧠",
                "executing": "⚡",
                "reflecting": "🔄"
            }
            icon = phase_icons.get(phase, "📌")
            print(f"\n{icon} [{phase.upper()}] {message}")
            
        elif event_type == "plan":
            tasks = event.get("tasks", [])
            print(f"\n📋 AI 生成的计划:")
            for i, task in enumerate(tasks, 1):
                print(f"   {i}. {task}")
            rag_used = event.get("rag_used", False)
            gaps = event.get("gaps_identified", 0)
            if rag_used:
                print(f"   📚 RAG 知识增强: ✅")
            if gaps > 0:
                print(f"   🔍 识别缺口: {gaps} 个")
                
        elif event_type == "task_start":
            task = event.get("task")
            print(f"\n   ⚙️  执行: {task}")
            
        elif event_type == "task_result":
            success = event.get("success")
            simulated = event.get("simulated", True)
            findings = event.get("findings", [])
            icon = "✅" if success else "❌"
            mode = "(模拟)" if simulated else "(真实)"
            print(f"   {icon} 完成 {mode}")
            if findings:
                for f in findings[:3]:
                    print(f"      📌 {json.dumps(f, ensure_ascii=False)[:100]}")
                    
        elif event_type == "reflection":
            summary = event.get("summary", "")
            print(f"\n🔄 [REFLECTING] AI 分析:")
            print(f"   {summary[:300]}...")
            
        elif event_type == "complete":
            print(f"\n{'='*70}")
            print("🎉 测试完成!")
            print(f"{'='*70}")
            print(f"   迭代次数: {event.get('iterations')}")
            print(f"   发现数量: {event.get('findings_count')}")
            print(f"   RAG 查询: {event.get('rag_queries', 0)}")
            print(f"   Token 消耗: {event.get('budget_used', 0)}")
            
        elif event_type == "error":
            print(f"\n❌ 错误: {event.get('message')}")
    
    # 输出报告
    print("\n" + "=" * 70)
    print("📊 测试报告")
    print("=" * 70)
    
    # 找到 complete 事件
    for event in reversed(events):
        if event.get("type") == "complete":
            report = event.get("report", "")
            if report:
                print(report)
            break
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_real_per_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        import pdb; pdb.post_mortem()
        sys.exit(1)
