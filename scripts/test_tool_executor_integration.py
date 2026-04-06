#!/usr/bin/env python3
"""
测试工具执行器API集成
验证统一执行器是否能够通过工具执行器API执行工具
"""

import os
import sys
import logging
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_tool_executor_api():
    """测试工具执行器API集成"""
    print("=" * 80)
    print("测试工具执行器API集成")
    print("=" * 80)

    # 创建统一执行器实例，启用工具执行器API
    executor = UnifiedExecutor(
        max_workers=1,
        enable_retry=False,
        execution_strategy=ExecutionStrategy.SEQUENTIAL,
        enable_security=False,
        require_real_execution=True,  # 要求真实执行
        use_tool_executor_api=True    # 启用工具执行器API
    )

    print(f"统一执行器初始化完成")
    print(f"使用工具执行器API: {executor.use_tool_executor_api}")
    print(f"工具执行器URL: {executor.tool_executor_url}")

    # 测试目标（安全的测试目标）
    test_target = "http://example.com"
    test_tool = "whatweb"

    print(f"\n测试工具: {test_tool}")
    print(f"测试目标: {test_target}")

    try:
        # 执行工具
        print(f"\n开始执行工具...")
        start_time = time.time()
        result = executor.execute_tool(test_tool, test_target, {})
        execution_time = time.time() - start_time

        print(f"工具执行完成，耗时: {execution_time:.2f}秒")
        print(f"执行结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"  工具: {result.get('tool', 'unknown')}")
        print(f"  目标: {result.get('target', 'unknown')}")

        if result.get('error'):
            print(f"  错误: {result.get('error')}")

        if result.get('output'):
            output_preview = result.get('output', '')[:200]
            print(f"  输出预览: {output_preview}...")

        # 检查是否通过工具执行器API执行
        if result.get('execution_mode') == 'real' and result.get('method') == 'tool_executor_api':
            print(f"\n✅ 成功通过工具执行器API执行工具!")
            return True
        elif result.get('execution_mode') == 'real':
            print(f"\n⚠️ 工具通过真实执行完成，但未使用工具执行器API")
            return True
        elif result.get('execution_mode') == 'simulated':
            print(f"\n❌ 工具降级到模拟执行")
            return False
        else:
            print(f"\n❓ 未知执行模式: {result.get('execution_mode')}")
            return False

    except Exception as e:
        print(f"\n❌ 工具执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_tool_executor_api():
    """测试不使用工具执行器API的情况（回退到标准执行）"""
    print("\n" + "=" * 80)
    print("测试不使用工具执行器API（回退模式）")
    print("=" * 80)

    # 创建统一执行器实例，禁用工具执行器API
    executor = UnifiedExecutor(
        max_workers=1,
        enable_retry=False,
        execution_strategy=ExecutionStrategy.SEQUENTIAL,
        enable_security=False,
        require_real_execution=False,   # 允许模拟执行
        use_tool_executor_api=False     # 禁用工具执行器API
    )

    print(f"统一执行器初始化完成（工具执行器API已禁用）")

    # 测试目标
    test_target = "http://example.com"
    test_tool = "whatweb"

    print(f"\n测试工具: {test_tool}")
    print(f"测试目标: {test_target}")

    try:
        # 执行工具
        print(f"\n开始执行工具...")
        start_time = time.time()
        result = executor.execute_tool(test_tool, test_target, {})
        execution_time = time.time() - start_time

        print(f"工具执行完成，耗时: {execution_time:.2f}秒")
        print(f"执行结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  执行模式: {result.get('execution_mode', 'unknown')}")

        if result.get('execution_mode') == 'simulated':
            print(f"\n✅ 成功降级到模拟执行（预期行为）")
            return True
        else:
            print(f"\n⚠️ 未按预期降级到模拟执行")
            return False

    except Exception as e:
        print(f"\n❌ 工具执行失败: {e}")
        return False

if __name__ == "__main__":
    print("ClawAI 工具执行器API集成测试")
    print("=" * 80)

    # 测试1: 使用工具执行器API
    success_api = test_tool_executor_api()

    # 测试2: 不使用工具执行器API
    success_fallback = test_without_tool_executor_api()

    print("\n" + "=" * 80)
    print("测试总结:")
    print(f"  工具执行器API测试: {'✅ 通过' if success_api else '❌ 失败'}")
    print(f"  回退模式测试: {'✅ 通过' if success_fallback else '❌ 失败'}")
    print("=" * 80)

    if success_api and success_fallback:
        print("\n🎉 所有测试通过！工具执行器API集成工作正常。")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，需要进一步调试。")
        sys.exit(1)