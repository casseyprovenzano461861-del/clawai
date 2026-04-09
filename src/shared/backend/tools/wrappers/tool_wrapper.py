#!/usr/bin/env python3
"""
统一工具包装器
提供一致的接口调用各种安全工具
使用 shell=False + 列表参数防止命令注入
"""

import subprocess
import json
import shlex
import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 危险字符检测
_DANGEROUS_CHARS = set(';|`$&')


def _validate_target(target: str) -> str:
    """验证目标参数，防止命令注入"""
    if not target or not isinstance(target, str):
        raise ValueError("目标地址不能为空")
    # 检测危险字符
    found = _DANGEROUS_CHARS.intersection(target)
    if found:
        raise ValueError(f"目标地址包含危险字符: {found}")
    return target


class ToolWrapper:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent.absolute()

    def execute_tool(self, tool_name, target, args=None):
        """执行工具并返回标准化结果"""
        try:
            _validate_target(target)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "target": target
            }

        # 工具映射表
        tool_map = {
            "nmap": self._execute_nmap,
            "nuclei": self._execute_nuclei,
            "whatweb": self._execute_whatweb,
            "sqlmap": self._execute_sqlmap,
            "dirsearch": self._execute_dirsearch,
            "wafw00f": self._execute_wafw00f,
        }

        if tool_name not in tool_map:
            return {
                "success": False,
                "error": f"未知工具: {tool_name}",
                "tool": tool_name,
                "target": target
            }

        try:
            return tool_map[tool_name](target, args or {})
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "target": target
            }

    def _execute_nmap(self, target, args):
        """执行Nmap扫描"""
        from config import config

        if os.path.exists(config.NMAP_PATH) and config.NMAP_PATH.endswith(".py"):
            cmd = ["python", config.NMAP_PATH, target]
        else:
            cmd = ["nmap", "-sV", "-sC", "-oX", "-", target]

        return self._run_command(cmd, "nmap")

    def _execute_nuclei(self, target, args):
        """执行Nuclei扫描"""
        from config import config

        if os.path.exists(config.NUCLEI_PATH) and config.NUCLEI_PATH.endswith(".py"):
            cmd = ["python", config.NUCLEI_PATH, target]
        else:
            cmd = ["nuclei", "-u", target, "-json"]

        return self._run_command(cmd, "nuclei")

    def _execute_whatweb(self, target, args):
        """执行WhatWeb指纹识别"""
        from config import config

        if os.path.exists(config.WHATWEB_PATH) and config.WHATWEB_PATH.endswith(".py"):
            cmd = ["python", config.WHATWEB_PATH, target]
        else:
            cmd = ["whatweb", target, "--color=never"]

        return self._run_command(cmd, "whatweb")

    def _execute_sqlmap(self, target, args):
        """执行SQLMap扫描"""
        sqlmap_path = str(self.project_root / "工具" / "sqlmap" / "sqlmap.py")
        cmd = ["python", sqlmap_path, "-u", target, "--batch", "--level=1", "--risk=1"]
        return self._run_command(cmd, "sqlmap")

    def _execute_dirsearch(self, target, args):
        """执行目录爆破"""
        dirsearch_path = str(self.project_root / "工具" / "dirsearch" / "dirsearch.py")
        cmd = ["python", dirsearch_path, "-u", target, "-e", "php,html,js", "-t", "10"]
        return self._run_command(cmd, "dirsearch")

    def _execute_wafw00f(self, target, args):
        """执行WAF检测"""
        wafw00f_path = str(self.project_root / "工具" / "wafw00f" / "wafw00f_wrapper.py")
        cmd = ["python", wafw00f_path, target]
        return self._run_command(cmd, "wafw00f")

    def _run_command(self, cmd: list, tool_name: str):
        """运行命令并解析结果（安全模式：列表参数 + shell=False）"""
        try:
            result = subprocess.run(
                cmd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # 尝试解析JSON输出
                try:
                    data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "tool": tool_name,
                        "data": data,
                        "raw_output": result.stdout
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "tool": tool_name,
                        "data": {"output": result.stdout},
                        "raw_output": result.stdout
                    }
            else:
                return {
                    "success": False,
                    "tool": tool_name,
                    "error": result.stderr,
                    "raw_output": result.stdout
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "tool": tool_name,
                "error": "执行超时"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "tool": tool_name,
                "error": f"命令未找到: {cmd[0]}"
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }

def main():
    """测试工具包装器"""
    if len(sys.argv) < 3:
        print("用法: python tool_wrapper.py <工具名> <目标>")
        sys.exit(1)

    tool_name = sys.argv[1]
    target = sys.argv[2]

    wrapper = ToolWrapper()
    result = wrapper.execute_tool(tool_name, target)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
