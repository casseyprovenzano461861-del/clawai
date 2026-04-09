#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLMap 工具 - SQL 注入检测与利用（危险，需确认）"""

from src.cli.tools import ToolDefinition, ToolResult, execute_streaming


class SQLMapTool(ToolDefinition):
    def __init__(self):
        super().__init__(
            name="sqlmap",
            description="使用 sqlmap 进行 SQL 注入自动化检测与利用。属于主动攻击工具，会对目标发起实际攻击请求，需要用户确认后才能执行。",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "目标 URL（如 http://example.com/page?id=1）",
                    },
                    "options": {
                        "type": "string",
                        "description": "额外的 sqlmap 选项字符串",
                    },
                    "risk": {
                        "type": "integer",
                        "description": "风险级别 1-3（1=安全测试，3=激进测试）",
                        "minimum": 1,
                        "maximum": 3,
                    },
                    "level": {
                        "type": "integer",
                        "description": "检测级别 1-5（1=基本，5=全面）",
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["url"],
            },
            is_dangerous=True,
            is_readonly=False,
            timeout=300,
        )

    async def execute(self, args: dict, on_output=None) -> ToolResult:
        url = args.get("url", "").strip()
        if not url:
            return ToolResult(success=False, output="", error="URL 不能为空")

        cmd = ["sqlmap", "-u", url, "--batch", "--random-agent"]

        # 风险级别
        risk = args.get("risk")
        if risk is not None:
            risk = int(risk)
            if risk < 1 or risk > 3:
                return ToolResult(success=False, output="", error="risk 必须在 1-3 之间")
            cmd.extend(["--risk", str(risk)])

        # 检测级别
        level = args.get("level")
        if level is not None:
            level = int(level)
            if level < 1 or level > 5:
                return ToolResult(success=False, output="", error="level 必须在 1-5 之间")
            cmd.extend(["--level", str(level)])

        # 额外选项
        options = args.get("options", "").strip()
        if options:
            import shlex
            cmd.extend(shlex.split(options))

        return await execute_streaming(cmd, on_output, timeout=self.timeout)


TOOL = SQLMapTool()
