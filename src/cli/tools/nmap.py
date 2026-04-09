#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nmap 工具 - 网络端口扫描"""

from src.cli.tools import ToolDefinition, ToolResult, execute_streaming


class NmapTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="nmap",
            description="使用 nmap 进行网络端口扫描和服务探测。支持快速/标准/全量扫描模式。端口扫描本身是只读操作，不会对目标造成破坏。",
            input_schema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "扫描目标（IP 或域名）",
                    },
                    "ports": {
                        "type": "string",
                        "description": "端口范围，如 '1-1000'、'80,443,8080'",
                    },
                    "scan_type": {
                        "type": "string",
                        "enum": ["quick", "standard", "full"],
                        "description": "扫描类型: quick=快速扫描(-T4 -F), standard=标准扫描(-sV -sC), full=全量扫描(-sV -sC -A)",
                    },
                    "extra_args": {
                        "type": "string",
                        "description": "额外的 nmap 参数",
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

        cmd = ["nmap"]

        # 扫描类型
        scan_type = args.get("scan_type", "standard")
        if scan_type == "quick":
            cmd.extend(["-T4", "-F"])
        elif scan_type == "standard":
            cmd.extend(["-sV", "-sC"])
        elif scan_type == "full":
            cmd.extend(["-sV", "-sC", "-A"])

        # 端口范围
        ports = args.get("ports", "").strip()
        if ports:
            cmd.extend(["-p", ports])

        # 额外参数
        extra_args = args.get("extra_args", "").strip()
        if extra_args:
            import shlex
            cmd.extend(shlex.split(extra_args))

        cmd.append(target)

        return await execute_streaming(cmd, on_output, timeout=self.timeout)


TOOL = NmapTool()
