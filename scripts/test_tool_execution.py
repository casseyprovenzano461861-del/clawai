#!/usr/bin/env python3
"""
测试工具真实执行
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.unified_executor_final import UnifiedExecutor, ExecutionStrategy

def test_nmap():
    """测试nmap真实执行"""
    print("初始化统一执行器...")
    executor = UnifiedExecutor(
        max_workers=1,
        enable_retry=True,
        max_retries=1,
        execution_strategy=ExecutionStrategy.INTELLIGENT,
        enable_security=True,
        require_real_execution=True,
        use_tool_executor_api=True
    )

    print("执行nmap扫描localhost...")
    result = executor.execute_tool("nmap", "127.0.0.1")

    print("结果:", json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("success", False):
        print("✅ nmap执行成功")
        print("执行模式:", result.get("execution_mode", "unknown"))
        if "output" in result:
            output = result["output"]
            if "ports" in output:
                ports = output["ports"]
                open_ports = [p for p in ports if isinstance(p, dict) and p.get("state") == "open"]
                print(f"发现开放端口: {len(open_ports)}个")
    else:
        print("❌ nmap执行失败")
        print("错误:", result.get("error", "未知错误"))

    return result

if __name__ == "__main__":
    import json
    test_nmap()