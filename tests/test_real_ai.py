# -*- coding: utf-8 -*-
"""
真实 LLM 工具调用演示
让 AI 自动决策并调用工具执行扫描
"""

import asyncio
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# API Key 从环境变量获取（不再硬编码）
DEFAULT_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")


async def demo_real_ai_tool_call():
    """演示真实 AI 工具调用"""
    print("\n" + "=" * 70)
    print(" AI Agent 真实工具调用演示")
    print("=" * 70)
    
    from src.shared.backend.ai_agent.orchestrator import AIAgentOrchestrator, AgentConfig, AgentMode
    
    # 检查 API Key（必须通过环境变量设置）
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key or not api_key.startswith("sk-") or len(api_key) <= 20:
        print("\n⚠️  未设置有效的 DEEPSEEK_API_KEY 环境变量，跳过测试")
        return False
    
    print(f"\n✓ 使用 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 创建配置
    config = AgentConfig(
        provider="deepseek",
        api_key=api_key,
        mode=AgentMode.CHAT,
        enable_simulation=True,
        enable_streaming=True,
        auto_execute_safe=True,  # 自动执行安全工具
        require_confirmation=False  # 不需要确认（演示用）
    )
    
    print("\n初始化 AI Agent...")
    orchestrator = AIAgentOrchestrator(config)
    
    print(f"  - LLM: {config.provider}")
    print(f"  - UnifiedExecutor: {'✓' if orchestrator.unified_executor else '✗'}")
    print(f"  - 自动执行安全工具: {config.auto_execute_safe}")
    
    # 模拟对话
    print("\n" + "-" * 70)
    print(" 对话开始")
    print("-" * 70)
    
    conversations = [
        "你好，我想对 scanme.nmap.org 进行端口扫描，只扫描 22 和 80 端口",
    ]
    
    for user_input in conversations:
        print(f"\n👤 用户: {user_input}")
        print(f"\n🤖 AI: ", end="", flush=True)
        
        response_text = ""
        tool_calls = []
        
        async for event in orchestrator.chat(user_input, stream=True):
            event_type = event.get("type", "")
            
            if event_type in ["text", "content"]:
                chunk = event.get("content", "")
                response_text += chunk
                print(chunk, end="", flush=True)
                
            elif event_type == "tool_call" or event_type == "tool_call_start":
                tool_name = event.get("tool", event.get("tool_name", "unknown"))
                tool_args = event.get("arguments", {})
                tool_calls.append((tool_name, tool_args))
                print(f"\n\n🔧 [调用工具: {tool_name}]")
                if tool_args:
                    print(f"   参数: {tool_args}")
                print(f"\n🤖 AI: ", end="", flush=True)
                
            elif event_type == "tool_result" or event_type == "tool_call_result":
                result = event.get("result", {})
                success = result.get("success", False)
                simulated = result.get("simulated", True)
                mode = "模拟" if simulated else "真实"
                status = "✓ 成功" if success else "✗ 失败"
                print(f"\n   结果: {status} ({mode}执行)")
                
                # 显示扫描结果
                output = result.get("output", {})
                if isinstance(output, dict):
                    if "ports" in output:
                        ports = output["ports"]
                        if isinstance(ports, list):
                            print(f"   发现端口: {len(ports)} 个开放")
                            for p in ports[:5]:  # 最多显示5个
                                if isinstance(p, dict):
                                    print(f"      - 端口 {p.get('port')}: {p.get('state')} ({p.get('service', 'unknown')})")
                    if "vulnerabilities" in output:
                        vulns = output["vulnerabilities"]
                        if isinstance(vulns, list) and len(vulns) > 0:
                            print(f"   发现漏洞: {len(vulns)} 个")
                
                print(f"\n🤖 AI: ", end="", flush=True)
                
            elif event_type == "error":
                error = event.get("error", "未知错误")
                print(f"\n\n❌ 错误: {error}")
                
            elif event_type == "complete":
                if response_text:
                    print()  # 换行
        
        print()  # 响应结束换行
    
    print("\n" + "-" * 70)
    print(" 对话结束")
    print("-" * 70)
    
    # 显示统计
    if orchestrator.tool_bridge:
        stats = orchestrator.tool_bridge.get_stats()
        print(f"\n执行统计:")
        print(f"  - 总调用: {stats['total_calls']}")
        print(f"  - 真实执行: {stats['real_calls']}")
        print(f"  - 模拟执行: {stats['simulated_calls']}")
        print(f"  - 成功率: {stats['success_rate']*100:.1f}%")
    
    return True


async def interactive_demo():
    """交互式演示"""
    print("\n" + "=" * 70)
    print(" AI Agent 交互式演示")
    print(" 输入 'quit' 退出")
    print("=" * 70)
    
    from src.shared.backend.ai_agent.orchestrator import AIAgentOrchestrator, AgentConfig, AgentMode
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key or not api_key.startswith("sk-") or len(api_key) <= 20:
        print("\n⚠️  未设置有效的 DEEPSEEK_API_KEY 环境变量，跳过测试")
        return
    
    print(f"\n✓ 使用 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    config = AgentConfig(
        provider="deepseek",
        api_key=api_key,
        mode=AgentMode.CHAT,
        enable_simulation=True,
        enable_streaming=True,
        auto_execute_safe=True
    )
    
    orchestrator = AIAgentOrchestrator(config)
    
    print("\n初始化完成，开始对话...\n")
    
    while True:
        try:
            user_input = input("👤 你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见!")
                break
            
            if not user_input:
                continue
            
            print(f"\n🤖 AI: ", end="", flush=True)
            
            async for event in orchestrator.chat(user_input, stream=True):
                event_type = event.get("type", "")
                
                if event_type in ["text", "content"]:
                    print(event.get("content", ""), end="", flush=True)
                elif event_type == "tool_call_start":
                    tool_name = event.get("tool_name", "unknown")
                    print(f"\n\n🔧 [调用工具: {tool_name}]", end="", flush=True)
                elif event_type == "tool_call_result":
                    result = event.get("result", {})
                    mode = "模拟" if result.get("simulated") else "真实"
                    status = "✓" if result.get("success") else "✗"
                    output = result.get("output", {})
                    
                    # 显示扫描结果
                    if isinstance(output, dict) and "ports" in output:
                        ports = output.get("ports", [])
                        print(f"\n   {status} {mode}执行 - 发现 {len(ports)} 个开放端口", end="", flush=True)
                        for p in ports[:3]:
                            if isinstance(p, dict):
                                print(f"\n      - {p.get('port')}/{p.get('state')} ({p.get('service', '')})", end="", flush=True)
                    else:
                        print(f"\n   {status} {mode}执行", end="", flush=True)
                    
                    print(f"\n🤖 AI: ", end="", flush=True)
                elif event_type == "error":
                    print(f"\n❌ 错误: {event.get('error')}", end="", flush=True)
                    
            print()  # 换行
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_demo())
    else:
        success = asyncio.run(demo_real_ai_tool_call())
        if success:
            print("\n" + "=" * 70)
            print(" 演示完成!")
            print(" 运行 'python tests/test_real_ai.py --interactive' 进入交互模式")
            print("=" * 70)
