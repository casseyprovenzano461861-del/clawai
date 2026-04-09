#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FileRead 工具 - 读取文件内容（直接读取，不走子进程）"""

import time

from src.cli.tools import ToolDefinition, ToolResult


class FileReadTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="file_read",
            description="读取指定文件的内容。支持按行偏移和行数限制读取大文件的部分内容。属于只读操作。",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "起始行号（从 1 开始），省略则从文件开头读取",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "读取的最大行数，省略则读取全部",
                    },
                },
                "required": ["path"],
            },
            is_dangerous=False,
            is_readonly=True,
            timeout=10,
        )

    async def execute(self, args: dict, on_output=None) -> ToolResult:
        path = args.get("path", "").strip()
        if not path:
            return ToolResult(success=False, output="", error="文件路径不能为空")

        offset = args.get("offset")
        limit = args.get("limit")

        start = time.time()

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                if offset is not None or limit is not None:
                    # 按行读取
                    lines = []
                    line_num = 0
                    start_line = (offset or 1) - 1  # 转为 0-based
                    max_lines = limit or float("inf")
                    count = 0

                    for line in f:
                        line_num += 1
                        if line_num - 1 < start_line:
                            continue
                        lines.append(f"{line_num:>6}\t{line.rstrip()}")
                        count += 1
                        if count >= max_lines:
                            break

                    output = "\n".join(lines)
                else:
                    # 全量读取，带行号
                    lines = []
                    for i, line in enumerate(f, 1):
                        lines.append(f"{i:>6}\t{line.rstrip()}")
                    output = "\n".join(lines)

            elapsed = time.time() - start

            if on_output:
                on_output(output)

            return ToolResult(success=True, output=output, duration=elapsed)

        except FileNotFoundError:
            elapsed = time.time() - start
            return ToolResult(success=False, output="", error=f"文件不存在: {path}", duration=elapsed)
        except IsADirectoryError:
            elapsed = time.time() - start
            return ToolResult(success=False, output="", error=f"路径是目录，不是文件: {path}", duration=elapsed)
        except PermissionError:
            elapsed = time.time() - start
            return ToolResult(success=False, output="", error=f"权限不足: {path}", duration=elapsed)
        except Exception as e:
            elapsed = time.time() - start
            return ToolResult(success=False, output="", error=str(e), duration=elapsed)


TOOL = FileReadTool()
