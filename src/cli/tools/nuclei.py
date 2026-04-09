#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nuclei 工具 - 基于模板的漏洞扫描"""

from src.cli.tools import ToolDefinition, ToolResult, execute_streaming


class NucleiTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="nuclei",
            description="使用 nuclei 进行基于模板的漏洞扫描。可指定模板分类和严重级别进行定向扫描。扫描为只读探测，不会利用发现的漏洞。",
            input_schema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "扫描目标 URL（如 http://example.com）",
                    },
                    "templates": {
                        "type": "string",
                        "description": "模板标签，多个用逗号分隔，如 'cves,vulns'、'cve-2023-xxx'",
                    },
                    "severity": {
                        "type": "string",
                        "description": "严重级别过滤，多个用逗号分隔，如 'critical,high'、'medium,low'",
                    },
                },
                "required": ["target"],
            },
            is_dangerous=False,
            is_readonly=True,
            timeout=300,
        )

    async def execute(self, args: dict, on_output=None) -> ToolResult:
        target = args.get("target", "").strip()
        if not target:
            return ToolResult(success=False, output="", error="目标不能为空")

        cmd = ["nuclei", "-u", target, "-silent"]

        # 模板过滤
        templates = args.get("templates", "").strip()
        if templates:
            cmd.extend(["-t", templates])

        # 严重级别过滤
        severity = args.get("severity", "").strip()
        if severity:
            cmd.extend(["-severity", severity])

        return await execute_streaming(cmd, on_output, timeout=self.timeout)


TOOL = NucleiTool()
