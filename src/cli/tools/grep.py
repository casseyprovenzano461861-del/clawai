#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grep 工具 - 文件内容搜索（优先使用 ripgrep）"""

import shutil

from src.cli.tools import ToolDefinition, ToolResult, execute_streaming


class GrepTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="grep",
            description="在文件中搜索匹配的文本模式。优先使用 ripgrep (rg)，回退到 grep。支持正则表达式、文件类型过滤、大小写忽略等选项。属于只读操作。",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "搜索模式（支持正则表达式）",
                    },
                    "path": {
                        "type": "string",
                        "description": "搜索路径（默认当前目录）",
                    },
                    "glob": {
                        "type": "string",
                        "description": "文件类型过滤，如 '*.py'、'*.{js,ts}'",
                    },
                    "case_insensitive": {
                        "type": "boolean",
                        "description": "是否忽略大小写",
                    },
                },
                "required": ["pattern"],
            },
            is_dangerous=False,
            is_readonly=True,
            timeout=30,
        )

    async def execute(self, args: dict, on_output=None) -> ToolResult:
        pattern = args.get("pattern", "").strip()
        if not pattern:
            return ToolResult(success=False, output="", error="搜索模式不能为空")

        use_rg = shutil.which("rg") is not None

        if use_rg:
            cmd = ["rg"]
            # 默认显示行号
            cmd.append("-n")
            # 大小写忽略
            if args.get("case_insensitive"):
                cmd.append("-i")
            # glob 过滤
            glob = args.get("glob", "").strip()
            if glob:
                cmd.extend(["-g", glob])
            cmd.append("--")
            cmd.append(pattern)
            # 搜索路径
            path = args.get("path", "").strip()
            if path:
                cmd.append(path)
        else:
            cmd = ["grep", "-n", "-E"]
            if args.get("case_insensitive"):
                cmd.append("-i")
            cmd.append("--")
            cmd.append(pattern)
            # glob 过滤 (grep 用 --include)
            glob = args.get("glob", "").strip()
            if glob:
                cmd.extend(["--include", glob])
            # 搜索路径 (grep 需要 -r 和路径)
            cmd.append("-r")
            path = args.get("path", "").strip()
            cmd.append(path or ".")

        return await execute_streaming(cmd, on_output, timeout=self.timeout)


TOOL = GrepTool()
