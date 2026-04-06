#!/usr/bin/env python3
"""
Curl工具包装器
Windows兼容版本
"""

import subprocess
import sys
import os
from typing import Dict, Any

def execute_curl(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行curl工具
    
    Args:
        params: 执行参数
        
    Returns:
        执行结果
    """
    try:
        # 构建命令
        command = ["curl"]
        
        # 添加参数
        if "target" in params:
            command.append(params["target"])
        
        if "options" in params:
            if isinstance(params["options"], list):
                command.extend(params["options"])
            elif isinstance(params["options"], str):
                command.extend(params["options"].split())
        
        # 执行命令
        print(f"执行命令: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": ' '.join(command)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "执行超时 (5分钟)",
            "command": ' '.join(command) if 'command' in locals() else ""
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "工具未找到，请确保curl已安装并在PATH中",
            "command": ' '.join(command) if 'command' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": ' '.join(command) if 'command' in locals() else ""
        }

if __name__ == "__main__":
    # 测试代码
    test_params = {
        "target": "example.com",
        "options": ["-h"]  # 显示帮助信息
    }
    
    result = execute_curl(test_params)
    print(f"测试结果: {result}")
