#!/usr/bin/env python3
"""
简单工具包装器
"""

import subprocess
import sys
from pathlib import Path

def execute_tool(tool_name, target="example.com"):
    """执行工具"""
    project_root = Path(__file__).parent.parent.parent.parent
    mock_tools_dir = project_root / "backend" / "tools" / "mock"
    
    mock_file = mock_tools_dir / f"{tool_name.lower()}_mock.py"
    
    if mock_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(mock_file), target],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "tool": tool_name,
                    "output": result.stdout,
                    "type": "mock"
                }
            else:
                return {
                    "success": False,
                    "tool": tool_name,
                    "error": result.stderr,
                    "type": "mock"
                }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "type": "mock"
            }
    else:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"工具未找到: {tool_name}",
            "type": "real"
        }

if __name__ == "__main__":
    # 测试
    tools = ["nmap", "nuclei", "sqlmap"]
    for tool in tools:
        print(f"\n测试 {tool}:")
        result = execute_tool(tool)
        if result["success"]:
            print(f"  [OK] 执行成功")
        else:
            print(f"  [FAIL] 执行失败: {result.get('error', '未知错误')}")
