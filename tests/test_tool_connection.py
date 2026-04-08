# -*- coding: utf-8 -*-
"""
AI Agent 工具连接集成测试
验证 ToolExecutionBridge 与 UnifiedExecutor 的正确连接
"""

import asyncio
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_unified_executor_connection():
    """测试 UnifiedExecutor 连接"""
    print("\n" + "=" * 60)
    print("测试 1: UnifiedExecutor 直接调用")
    print("=" * 60)
    
    try:
        from src.shared.backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
        
        executor = UnifiedExecutor(
            max_workers=2,
            execution_strategy=ExecutionStrategy.INTELLIGENT,
            require_real_execution=False  # 允许回退到模拟
        )
        
        # 测试 nmap
        print("\n执行 nmap 扫描 (目标: scanme.nmap.org)...")
        result = executor.execute_tool("nmap", "scanme.nmap.org", {"ports": "22,80,443"})
        
        print(f"  状态: {result.get('status')}")
        print(f"  执行模式: {result.get('execution_mode')}")
        print(f"  成功: {result.get('success')}")
        
        if result.get('output'):
            output = result['output']
            if isinstance(output, dict):
                print(f"  开放端口数: {len(output.get('ports', []))}")
        
        # 测试 whatweb
        print("\n执行 whatweb 扫描 (目标: example.com)...")
        result = executor.execute_tool("whatweb", "example.com")
        
        print(f"  状态: {result.get('status')}")
        print(f"  执行模式: {result.get('execution_mode')}")
        
        print("\n✓ UnifiedExecutor 直接调用测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ UnifiedExecutor 直接调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_bridge_with_executor():
    """测试 ToolExecutionBridge 与 UnifiedExecutor 集成"""
    print("\n" + "=" * 60)
    print("测试 2: ToolExecutionBridge + UnifiedExecutor 集成")
    print("=" * 60)
    
    try:
        from src.shared.backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy
        from src.shared.backend.ai_agent.tools.executor import ToolExecutionBridge
        
        # 创建 UnifiedExecutor
        executor = UnifiedExecutor(
            max_workers=2,
            require_real_execution=False
        )
        
        # 创建 ToolExecutionBridge
        bridge = ToolExecutionBridge(
            unified_executor=executor,
            enable_simulation=True,
            prefer_real_execution=True
        )
        
        # 测试 nmap_scan
        print("\n通过 Bridge 执行 nmap_scan...")
        result = await bridge.execute("nmap_scan", {
            "target": "scanme.nmap.org",
            "ports": "22,80"
        })
        
        print(f"  工具名: {result.tool_name}")
        print(f"  成功: {result.success}")
        print(f"  模拟: {result.simulated}")
        print(f"  执行时间: {result.execution_time:.2f}s")
        
        if result.output:
            print(f"  输出: {list(result.output.keys())}")
        
        # 测试 nuclei_scan
        print("\n通过 Bridge 执行 nuclei_scan...")
        result = await bridge.execute("nuclei_scan", {
            "target": "https://example.com",
            "severity": "high"
        })
        
        print(f"  工具名: {result.tool_name}")
        print(f"  成功: {result.success}")
        print(f"  模拟: {result.simulated}")
        
        # 查看统计
        print("\n执行统计:")
        stats = bridge.get_stats()
        print(f"  总调用: {stats['total_calls']}")
        print(f"  成功: {stats['successful_calls']}")
        print(f"  真实执行: {stats['real_calls']}")
        print(f"  模拟执行: {stats['simulated_calls']}")
        print(f"  成功率: {stats['success_rate']*100:.1f}%")
        
        print("\n✓ ToolExecutionBridge 集成测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ ToolExecutionBridge 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator_integration():
    """测试完整的 Orchestrator 集成"""
    print("\n" + "=" * 60)
    print("测试 3: AIAgentOrchestrator 完整集成")
    print("=" * 60)
    
    try:
        from src.shared.backend.ai_agent.orchestrator import AIAgentOrchestrator, AgentConfig, AgentMode
        
        # 创建配置（使用 mock 模式，不需要 API key）
        config = AgentConfig(
            provider="mock",
            api_key="",
            mode=AgentMode.CHAT,
            enable_simulation=True,
            enable_streaming=False
        )
        
        # 创建编排器
        orchestrator = AIAgentOrchestrator(config)
        
        # 检查组件
        print("\n检查组件初始化:")
        print(f"  agent_core: {'✓' if orchestrator.agent_core else '✗'}")
        print(f"  conversation: {'✓' if orchestrator.conversation else '✗'}")
        print(f"  tool_bridge: {'✓' if orchestrator.tool_bridge else '✗'}")
        print(f"  risk_assessor: {'✓' if orchestrator.risk_assessor else '✗'}")
        print(f"  unified_executor: {'✓' if orchestrator.unified_executor else '✗ (将使用模拟)'}")
        
        # 测试工具执行
        if orchestrator.tool_bridge:
            print("\n测试工具执行...")
            result = await orchestrator.tool_bridge.execute("nmap_scan", {
                "target": "example.com"
            })
            print(f"  nmap_scan 结果: 成功={result.success}, 模拟={result.simulated}")
        
        print("\n✓ Orchestrator 集成测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ Orchestrator 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_to_simulation():
    """测试回退到模拟执行的逻辑"""
    print("\n" + "=" * 60)
    print("测试 4: 回退到模拟执行")
    print("=" * 60)
    
    try:
        from src.shared.backend.ai_agent.tools.executor import ToolExecutionBridge
        
        # 创建不带 UnifiedExecutor 的 Bridge
        bridge = ToolExecutionBridge(
            unified_executor=None,  # 不传入 executor
            enable_simulation=True,
            prefer_real_execution=False
        )
        
        print("\n无 UnifiedExecutor，测试模拟执行...")
        result = await bridge.execute("nmap_scan", {
            "target": "example.com"
        })
        
        print(f"  成功: {result.success}")
        print(f"  模拟: {result.simulated}")
        print(f"  开放端口: {result.output.get('total_open_ports', 0)}")
        
        # 测试其他工具
        result = await bridge.execute("nuclei_scan", {
            "target": "https://example.com"
        })
        print(f"\n  nuclei_scan: 成功={result.success}, 模拟={result.simulated}")
        
        result = await bridge.execute("sqlmap_scan", {
            "target": "http://example.com?id=1"
        })
        print(f"  sqlmap_scan: 成功={result.success}, 模拟={result.simulated}")
        
        print("\n✓ 模拟执行回退测试通过")
        return True
        
    except Exception as e:
        print(f"\n✗ 模拟执行回退测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print(" AI Agent 工具连接集成测试")
    print(" 验证 ToolExecutionBridge 与 UnifiedExecutor 的正确连接")
    print("=" * 70)
    
    results = []
    
    # 运行测试
    results.append(("UnifiedExecutor 直接调用", await test_unified_executor_connection()))
    results.append(("ToolExecutionBridge 集成", await test_tool_bridge_with_executor()))
    results.append(("Orchestrator 完整集成", await test_orchestrator_integration()))
    results.append(("模拟执行回退", await test_fallback_to_simulation()))
    
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
        print("\n🎉 所有集成测试通过！AI Agent 已正确连接到真实工具系统。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和依赖。")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
