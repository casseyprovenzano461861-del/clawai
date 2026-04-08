# -*- coding: utf-8 -*-
"""
真正的 P-E-R 自主模式演示
AI 自己规划、执行、反思整个渗透测试流程
"""

import asyncio
import sys
import os
import json

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 默认 API Key
DEFAULT_API_KEY = "sk-a4503ae9180f4c0cae86d2aaa62621e9"


async def demo_intelligent_per():
    """演示智能 P-E-R 自主模式"""
    print("\n" + "=" * 70)
    print(" 智能 P-E-R 自主模式演示")
    print(" AI 自己规划 → 执行 → 反思整个渗透测试流程")
    print("=" * 70)
    
    from src.shared.backend.ai_agent.core import AIAgentCore, LLMConfig, LLMProvider
    from src.shared.backend.ai_agent.intelligent_per import IntelligentPERAgent, PERPhase
    from src.shared.backend.ai_agent.context_analyzer import ContextGapAnalyzer
    from src.shared.backend.ai_agent.rag_client import RAGClient
    from src.shared.backend.ai_agent.budget_manager import BudgetManager
    from src.shared.backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
    
    # 检查 API Key
    env_key = os.getenv("DEEPSEEK_API_KEY")
    api_key = env_key if (env_key and env_key.startswith("sk-") and len(env_key) > 20) else DEFAULT_API_KEY
    
    print(f"\n✓ 使用 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 1. 创建 LLM 客户端
    print("\n[1/4] 初始化 AI 核心...")
    llm_config = LLMConfig(
        provider=LLMProvider.DEEPSEEK,
        model="deepseek-chat",
        api_key=api_key,
        temperature=0.3,  # 降低温度以获得更稳定的规划
        max_tokens=4096
    )
    
    llm_client = AIAgentCore(llm_config)
    
    # 2. 创建工具执行器
    print("[2/4] 初始化工具执行器...")
    executor = UnifiedExecutor(
        max_workers=3,
        execution_strategy=ExecutionStrategy.INTELLIGENT,
        require_real_execution=False
    )
    
    async def tool_executor(tool_name: str, params: dict):
        """工具执行器包装"""
        result = executor.execute_tool(
            tool_name.replace("_scan", "").replace("_probe", ""),
            params.get("target", params.get("domain", params.get("url", ""))),
            params
        )
        
        class ToolResult:
            def __init__(self, data):
                self.success = data.get("success", data.get("status") == "success")
                self.output = data.get("output", data)
                self.simulated = data.get("execution_mode") == "simulated"
        
        return ToolResult(result)
    
    # 3. 创建智能组件
    print("[3/4] 初始化智能组件...")
    context_analyzer = ContextGapAnalyzer()
    rag_client = RAGClient()
    budget_manager = BudgetManager(total_budget=50000)
    
    # 4. 创建智能 P-E-R Agent
    print("[4/4] 创建 P-E-R Agent...")
    per_agent = IntelligentPERAgent(
        llm_client=llm_client,
        tool_executor=tool_executor,
        context_analyzer=context_analyzer,
        rag_client=rag_client,
        budget_manager=budget_manager,
        max_iterations=3
    )
    
    # 目标
    target = "scanme.nmap.org"
    goal = f"对 {target} 进行安全评估，发现开放的端口和服务"
    
    print(f"\n{'=' * 70}")
    print(f" 目标: {target}")
    print(f" 任务: {goal}")
    print(f"{'=' * 70}")
    
    # 运行 P-E-R 循环
    print("\n🚀 开始执行...\n")
    
    findings = []
    
    async for event in per_agent.run(target, goal, mode="recon"):
        event_type = event.get("type")
        
        if event_type == "iteration":
            print(f"\n{'─' * 50}")
            print(f"📊 迭代 {event['num']}/{event['max']}")
            print(f"{'─' * 50}")
        
        elif event_type == "phase":
            phase = event.get("phase")
            message = event.get("message", "")
            print(f"\n🔄 [{phase.upper()}] {message}")
        
        elif event_type == "plan":
            tasks = event.get("tasks", [])
            print(f"\n📋 AI 生成的计划:")
            for i, task in enumerate(tasks, 1):
                print(f"   {i}. {task}")
        
        elif event_type == "task_start":
            task = event.get("task")
            print(f"\n   ⚙️  执行: {task}")
        
        elif event_type == "task_result":
            task = event.get("task")
            success = event.get("success")
            simulated = event.get("simulated")
            task_findings = event.get("findings", [])
            
            status = "✅" if success else "❌"
            mode = "(模拟)" if simulated else "(真实)"
            print(f"   {status} 完成 {mode}")
            
            if task_findings:
                print(f"   📌 发现:")
                for f in task_findings[:3]:
                    if isinstance(f, dict):
                        f_type = f.get("type", f.get("template", "unknown"))
                        print(f"      - {f_type}: {json.dumps(f, ensure_ascii=False)[:80]}")
                findings.extend(task_findings)
        
        elif event_type == "reflection":
            summary = event.get("summary", "")
            print(f"\n💭 AI 反思:")
            print(f"   {summary[:300]}...")
        
        elif event_type == "complete":
            print(f"\n{'=' * 70}")
            print(f" 🎉 执行完成!")
            print(f"{'=' * 70}")
            print(f"   迭代次数: {event.get('iterations', 0)}")
            print(f"   发现数量: {event.get('findings_count', 0)}")
            
            report = event.get("report", "")
            if report:
                print(f"\n📄 报告预览:")
                print("-" * 50)
                print(report[:1000])
                if len(report) > 1000:
                    print("\n... (报告已截断)")
        
        elif event_type == "error":
            print(f"\n❌ 错误: {event.get('message')}")
    
    print("\n" + "=" * 70)
    print(" 演示完成!")
    print("=" * 70)


async def interactive_per():
    """交互式 P-E-R 模式"""
    print("\n" + "=" * 70)
    print(" 智能 P-E-R 自主模式")
    print(" 输入目标进行自动化渗透测试")
    print("=" * 70)
    
    from src.shared.backend.ai_agent.core import AIAgentCore, LLMConfig, LLMProvider
    from src.shared.backend.ai_agent.intelligent_per import IntelligentPERAgent
    from src.shared.backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
    
    # 检查 API Key
    env_key = os.getenv("DEEPSEEK_API_KEY")
    api_key = env_key if (env_key and env_key.startswith("sk-") and len(env_key) > 20) else DEFAULT_API_KEY
    
    print(f"\n✓ 使用 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 初始化组件
    llm_config = LLMConfig(
        provider=LLMProvider.DEEPSEEK,
        model="deepseek-chat",
        api_key=api_key,
        temperature=0.3,
        max_tokens=4096
    )
    
    llm_client = AIAgentCore(llm_config)
    executor = UnifiedExecutor(max_workers=2, require_real_execution=False)
    
    async def tool_executor(tool_name: str, params: dict):
        result = executor.execute_tool(
            tool_name.replace("_scan", "").replace("_probe", ""),
            params.get("target", params.get("domain", "")),
            params
        )
        class ToolResult:
            def __init__(self, data):
                self.success = data.get("success", data.get("status") == "success")
                self.output = data.get("output", data)
                self.simulated = data.get("execution_mode") == "simulated"
        return ToolResult(result)
    
    per_agent = IntelligentPERAgent(
        llm_client=llm_client,
        tool_executor=tool_executor,
        max_iterations=2
    )
    
    print("\n初始化完成。输入 'quit' 退出\n")
    
    while True:
        try:
            target = input("🎯 目标地址: ").strip()
            
            if target.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见!")
                break
            
            if not target:
                continue
            
            print(f"\n🚀 开始对 {target} 进行自动化渗透测试...\n")
            
            async for event in per_agent.run(target):
                event_type = event.get("type")
                
                if event_type == "iteration":
                    print(f"\n📊 迭代 {event['num']}/{event['max']}")
                
                elif event_type == "phase":
                    print(f"\n🔄 [{event.get('phase', '').upper()}] {event.get('message', '')}")
                
                elif event_type == "plan":
                    print(f"📋 计划: {', '.join(event.get('tasks', []))}")
                
                elif event_type == "task_start":
                    print(f"   ⚙️  执行: {event.get('task')}")
                
                elif event_type == "task_result":
                    status = "✅" if event.get("success") else "❌"
                    mode = "(模拟)" if event.get("simulated") else "(真实)"
                    print(f"   {status} 完成 {mode}")
                    
                    for f in event.get("findings", [])[:2]:
                        print(f"      📌 {json.dumps(f, ensure_ascii=False)[:60]}")
                
                elif event_type == "reflection":
                    print(f"\n💭 {event.get('summary', '')[:200]}")
                
                elif event_type == "complete":
                    print(f"\n🎉 完成! 迭代: {event.get('iterations')}, 发现: {event.get('findings_count')}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_per())
    else:
        asyncio.run(demo_intelligent_per())
