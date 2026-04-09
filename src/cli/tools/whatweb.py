#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WhatWeb 工具 - Web 指纹识别"""

from src.cli.tools import ToolDefinition, ToolResult, execute_streaming


class WhatwebTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="whatweb",
            description="使用 whatweb 识别目标网站的技术栈指纹，包括 Web 服务器、CMS、框架、JavaScript 库等。属于只读探测操作。",
            input_schema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "目标 URL 或域名（如 http://example.com）",
                    },
                },
                "required": ["target"],
            },
            is_dangerous=False,
            is_readonly=True,
            timeout=60,
        )

    async def execute(self, args: dict, on_output=None) -> ToolResult:
        target = args.get("target", "").strip()
        if not target:
            return ToolResult(success=False, output="", error="目标不能为空")

        cmd = ["whatweb", target]

        return await execute_streaming(cmd, on_output, timeout=self.timeout)


TOOL = WhatwebTool()
