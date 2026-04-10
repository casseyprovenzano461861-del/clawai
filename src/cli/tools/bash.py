#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bash 工具 - 执行任意 Shell 命令（危险，需确认）"""

from src.cli.tools import ToolDefinition, ToolResult, execute_shell_streaming


class BashTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="bash",
            description="执行 Shell 命令。可用于文件操作、系统命令、管道组合等。属于危险操作，需要用户确认后才能执行。支持管道(|)、重定向(> >>)、逻辑运算(&& ||)等shell特性。",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 Shell 命令",
                    },
                },
                "required": ["command"],
            },
            is_dangerous=True,
            is_readonly=False,
            timeout=120,
        )

    async def execute(self, args: dict, on_output=None) -> ToolResult:
        command = args.get("command", "").strip()
        if not command:
            return ToolResult(success=False, output="", error="命令不能为空")

        return await execute_shell_streaming(command, on_output, timeout=self.timeout)


TOOL = BashTool()
