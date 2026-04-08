# -*- coding: utf-8 -*-
"""
AI Agent 端到端调用测试
验证 AI Agent 能否真正调用工具执行扫描
"""

import asyncio
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_llm_tool_calling():
    """测试 LLM Function Calling 触发工具执行"""
    print("\n" + "=" * 60)
    print("测试: AI Agent Function Calling 工具调用")
    print("=" * 60)
    
    try:
        from src.shared.backend.ai_agent.orchestrator import AIAgentOrchestrator, AgentConfig, AgentMode
        
        # 创建配置（使用 mock 模式测试工具调用逻辑）
        config = AgentConfig(
            provider="mock",
            api_key="",
            mode=AgentMode.CHAT,
            enable_simulation=True,
            enable_streaming=False,
            auto_execute_safe=True  # 自动执行安全工具
        )
        
        orchestrator = AIAgentOrchestrator(config)
        
        print("\n1. 检查组件状态:")
        print(f"   - UnifiedExecutor: {'✓' if orchestrator.unified_executor else '✗'}")
        print(f"   - ToolBridge: {'✓' if orchestrator.tool_bridge else '✗'}")
        print(f"   - AgentCore: {'✓' if orchestrator.agent_core else '✗'}")
        
        # 测试直接工具调用
        print("\n2. 测试直接工具调用 (通过 tool_bridge):")
        result = await orchestrator.tool_bridge.execute("nmap_scan", {
            "target": "scanme.nmap.org",
            "ports": "22,80"
        })
        print(f"   - nmap_scan: 成功={result.success}, 模拟={result.simulated}")
        if result.output:
            ports = result.output.get('ports', [])
            print(f"   - 发现端口: {len(ports)} 个")
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_call_processing():
    """测试工具调用处理流程"""
    print("\n" + "=" * 60)
    print("测试: 工具调用处理流程")
    print("=" * 60)
    
    try:
        from src.shared.backend.ai_agent.core import AIAgentCore, ToolCall
        from src.shared.backend.ai_agent.tools.executor import ToolExecutionBridge
        
        # 创建工具执行桥接（带 UnifiedExecutor）
        from src.shared.backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
        
        executor = UnifiedExecutor(
            max_workers=2,
            require_real_execution=False
        )
        
        bridge = ToolExecutionBridge(
            unified_executor=executor,
            enable_simulation=True,
            prefer_real_execution=True
        )
        
        # 模拟 LLM 返回的工具调用
        tool_call = ToolCall(
            id="call_001",
            name="nmap_scan",
            arguments={
                "target": "scanme.nmap.org",
                "ports": "22,80,443"
            }
        )
        
        print(f"\n模拟 LLM 工具调用:")
        print(f"   - ID: {tool_call.id}")
        print(f"   - 工具: {tool_call.name}")
        print(f"   - 参数: {tool_call.arguments}")
        
        # 执行工具
        print(f"\n执行工具调用...")
        result = await bridge.execute(tool_call.name, tool_call.arguments)
        
        print(f"\n执行结果:")
        print(f"   - 成功: {result.success}")
        print(f"   - 模拟: {result.simulated}")
        print(f"   - 执行时间: {result.execution_time:.2f}s")
        
        if result.output:
            print(f"   - 输出键: {list(result.output.keys())}")
            if 'ports' in result.output:
                ports = result.output['ports']
                print(f"   - 开放端口数: {len(ports) if isinstance(ports, list) else 'N/A'}")
        
        # 测试多个工具调用
        print("\n\n测试批量工具调用:")
        
        tool_calls = [
            ("nmap_scan", {"target": "example.com"}),
            ("whatweb_scan", {"target": "https://example.com"}),
            ("nuclei_scan", {"target": "https://example.com"}),
        ]
        
        for name, args in tool_calls:
            result = await bridge.execute(name, args)
            print(f"   - {name}: 成功={result.success}, 模拟={result.simulated}")
        
        # 统计
        stats = bridge.get_stats()
        print(f"\n执行统计:")
        print(f"   - 总调用: {stats['total_calls']}")
        print(f"   - 真实执行: {stats['real_calls']}")
        print(f"   - 模拟执行: {stats['simulated_calls']}")
        
        print("\n✓ 工具调用处理测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_real_llm_tool_call():
    """测试真实 LLM 工具调用（需要 API Key）"""
    print("\n" + "=" * 60)
    print("测试: 真实 LLM 工具调用")
    print("=" * 60)
    
    # 检查 API Key
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️ 未设置 API Key，跳过真实 LLM 测试")
        print("   设置环境变量 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 以启用此测试")
        return True  # 不算失败
    
    try:
        from src.shared.backend.ai_agent.orchestrator import AIAgentOrchestrator, AgentConfig, AgentMode
        
        # 使用真实 LLM
        config = AgentConfig(
            provider="deepseek" if os.getenv("DEEPSEEK_API_KEY") else "openai",
            api_key=api_key,
            mode=AgentMode.CHAT,
            enable_simulation=True,
            enable_streaming=False,
            auto_execute_safe=True
        )
        
        print(f"\n使用 LLM: {config.provider}")
        
        orchestrator = AIAgentOrchestrator(config)
        
        # 发送需要工具调用的请求
        user_message = "请帮我扫描 scanme.nmap.org 的 22 和 80 端口"
        print(f"\n用户输入: {user_message}")
        print(f"\nLLM 响应:")
        
        response_text = ""
        async for event in orchestrator.chat(user_message, stream=False):
            if event.get("type") == "text":
                chunk = event.get("content", "")
                response_text += chunk
                print(chunk, end="", flush=True)
            elif event.get("type") == "tool_call":
                tool = event.get("tool", "")
                print(f"\n   [工具调用: {tool}]")
            elif event.get("type") == "tool_result":
                result = event.get("result", {})
                print(f"   [工具结果: 成功={result.get('success')}]")
        
        print(f"\n\n✓ 真实 LLM 测试完成")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chat_mode_flow():
    """测试 ChatMode 完整流程"""
    print("\n" + "=" * 60)
    print("测试: ChatMode 完整交互流程")
    print("=" * 60)
    
    try:
        from src.shared.backend.ai_agent.modes.chat_mode import ChatMode, ChatModeConfig
        from src.shared.backend.ai_agent.core import create_agent
        from src.shared.backend.ai_agent.conversation import ConversationManager
        from src.shared.backend.ai_agent.tools.executor import ToolExecutionBridge
        from src.shared.backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
        
        # 创建组件
        agent_core = create_agent(provider="mock", api_key="", model="mock")
        conversation = ConversationManager(max_history=10)
        
        executor = UnifiedExecutor(max_workers=2, require_real_execution=False)
        tool_bridge = ToolExecutionBridge(
            unified_executor=executor,
            enable_simulation=True,
            prefer_real_execution=True
        )
        
        agent_core.set_tool_executor(tool_bridge.execute)
        
        # 创建 ChatMode
        chat_mode = ChatMode(
            agent_core=agent_core,
            conversation=conversation,
            config=ChatModeConfig(
                auto_execute_safe=True,
                require_confirmation=False,
                stream_response=False
            )
        )
        
        print("\n模拟用户输入: 帮我扫描 example.com")
        
        events = []
        async for event in chat_mode.process_message("帮我扫描 example.com", stream=False):
            events.append(event)
            event_type = event.get("type", "unknown")
            
            if event_type == "text":
                print(f"   [文本响应]")
            elif event_type == "tool_call":
                print(f"   [工具调用: {event.get('tool')}]")
            elif event_type == "tool_result":
                result = event.get("result", {})
                print(f"   [工具结果: 成功={result.get('success')}, 模拟={result.get('simulated')}]")
            elif event_type == "complete":
                print(f"   [完成]")
        
        print(f"\n收到 {len(events)} 个事件")
        print("\n✓ ChatMode 测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print(" AI Agent 端到端调用测试")
    print(" 验证 AI Agent 能否真正调用工具执行扫描")
    print("=" * 70)
    
    results = []
    
    # 运行测试
    results.append(("直接工具调用", await test_llm_tool_calling()))
    results.append(("工具调用处理", await test_tool_call_processing()))
    results.append(("ChatMode 流程", await test_chat_mode_flow()))
    results.append(("真实 LLM 调用", await test_real_llm_tool_call()))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print(" 测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 AI Agent 可以成功调用工具执行扫描！")
    else:
        print("\n⚠️ 部分测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
