#!/usr/bin/env python3
"""Test: _chat_with_tools interactive tool call flow (approve/reject/execute)

Validates the end-to-end flow:
  LLM stream -> tool_calls -> permission check -> execute -> tool_result -> LLM final reply

Uses mock LLM client and mock tool definitions -- no real API calls needed.
"""

import asyncio
import json
import sys
import os
import pytest

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from dataclasses import dataclass


# -- Helpers: mock LLM stream chunks --

def _make_text_chunk(content: str):
    """Simulate an OpenAI streaming chunk with text content."""
    delta = MagicMock()
    delta.content = content
    delta.tool_calls = None
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def _make_tool_call_chunks(tool_name: str, tool_args: dict, call_id: str = "call_123"):
    """Simulate OpenAI streaming chunks that build up a tool_call."""
    args_json = json.dumps(tool_args)

    # Chunk 1: id + function name
    tc1 = MagicMock()
    tc1.index = 0
    tc1.id = call_id
    tc1.function = MagicMock()
    tc1.function.name = tool_name
    tc1.function.arguments = None
    delta1 = MagicMock()
    delta1.content = None
    delta1.tool_calls = [tc1]
    choice1 = MagicMock()
    choice1.delta = delta1
    chunk1 = MagicMock()
    chunk1.choices = [choice1]

    # Chunk 2: arguments
    tc2 = MagicMock()
    tc2.index = 0
    tc2.id = None
    tc2.function = MagicMock()
    tc2.function.name = None
    tc2.function.arguments = args_json
    delta2 = MagicMock()
    delta2.content = None
    delta2.tool_calls = [tc2]
    choice2 = MagicMock()
    choice2.delta = delta2
    chunk2 = MagicMock()
    chunk2.choices = [choice2]

    # Chunk 3: empty finish
    delta3 = MagicMock()
    delta3.content = None
    delta3.tool_calls = None
    choice3 = MagicMock()
    choice3.delta = delta3
    chunk3 = MagicMock()
    chunk3.choices = [choice3]

    return [chunk1, chunk2, chunk3]


# -- Fixtures --

def _make_chat_cli():
    """Create a ClawAIChatCLI with mock agent (OpenAI-type)."""
    from src.cli.chat_cli import ClawAIChatCLI

    config = {
        "llm": {"provider": "openai", "model_id": "gpt-4"},
        "agent": {"execution_mode": "mock"},
    }

    with patch("src.cli.chat_cli.AGENT_AVAILABLE", True), \
         patch("src.cli.chat_cli.ClawAIPentestAgent") as MockAgent:
        mock_agent = MagicMock()
        mock_agent.llm_client = {"type": "openai", "client": MagicMock()}
        mock_agent.model_id = "gpt-4"
        mock_agent.temperature = 0.7
        mock_agent.max_new_tokens = 1024
        mock_agent.provider = "openai"
        mock_agent.execution_mode = "local"

        MockAgent.return_value = mock_agent

        cli = ClawAIChatCLI(config)
        cli.agent = mock_agent

    return cli


def _make_tool_def(name="nmap", is_dangerous=False, is_readonly=True, output="scan done"):
    """Create a mock ToolDefinition."""
    from src.cli.tools import ToolDefinition, ToolResult

    class MockTool(ToolDefinition):
        def __init__(self):
            super().__init__(
                name=name,
                description=f"Mock {name} tool",
                input_schema={"type": "object", "properties": {"target": {"type": "string"}}, "required": ["target"]},
                is_dangerous=is_dangerous,
                is_readonly=is_readonly,
                timeout=30,
            )
            self._output = output

        async def execute(self, args, on_output=None):
            if on_output:
                on_output(self._output)
            return ToolResult(success=True, output=self._output, duration=0.1)

    return MockTool()


def _setup_registry(registry, tool):
    """Setup mock registry with a tool."""
    registry.get_openai_schemas.return_value = [tool.get_openai_schema()]
    registry.lookup.return_value = tool
    return registry


# -- Tests --

@pytest.mark.asyncio
async def test_tool_call_safe_tool_auto_executes():
    """Safe tool (not dangerous) should execute without user confirmation."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]
    nmap_tool = _make_tool_def("nmap", is_dangerous=False, is_readonly=True)

    tool_chunks = _make_tool_call_chunks("nmap", {"target": "127.0.0.1"})
    final_chunks = [_make_text_chunk("Scan complete. Found 3 open ports.")]

    mock_client.chat.completions.create.side_effect = [tool_chunks, final_chunks]

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn:
        mock_registry_fn.return_value = _setup_registry(MagicMock(), nmap_tool)

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    assert "Scan complete" in result
    assert any(m.get("role") == "tool" for m in messages)


@pytest.mark.asyncio
async def test_tool_call_dangerous_rejected():
    """Dangerous tool should be rejected when user types 'n'."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]
    bash_tool = _make_tool_def("bash", is_dangerous=True, is_readonly=False)

    tool_chunks = _make_tool_call_chunks("bash", {"command": "rm -rf /"})
    final_chunks = [_make_text_chunk("Understood, I won't run that.")]

    mock_client.chat.completions.create.side_effect = [tool_chunks, final_chunks]

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn, \
         patch("rich.prompt.Prompt.ask", return_value="n"):
        mock_registry_fn.return_value = _setup_registry(MagicMock(), bash_tool)

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert "拒绝" in tool_msgs[0]["content"]


@pytest.mark.asyncio
async def test_tool_call_dangerous_approved():
    """Dangerous tool should execute when user types 'y'."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]
    bash_tool = _make_tool_def("bash", is_dangerous=True, is_readonly=False, output="hello world")

    tool_chunks = _make_tool_call_chunks("bash", {"command": "echo hello"})
    final_chunks = [_make_text_chunk("Command executed successfully.")]

    mock_client.chat.completions.create.side_effect = [tool_chunks, final_chunks]

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn, \
         patch("rich.prompt.Prompt.ask", return_value="y"):
        mock_registry_fn.return_value = _setup_registry(MagicMock(), bash_tool)

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert "hello world" in tool_msgs[0]["content"]


@pytest.mark.asyncio
async def test_tool_call_unknown_tool():
    """Unknown tool should report error back to LLM, not crash."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]

    tool_chunks = _make_tool_call_chunks("nonexistent_tool", {"target": "x"})
    final_chunks = [_make_text_chunk("That tool doesn't exist.")]

    mock_client.chat.completions.create.side_effect = [tool_chunks, final_chunks]

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn:
        registry = MagicMock()
        registry.get_openai_schemas.return_value = []
        registry.lookup.return_value = None
        mock_registry_fn.return_value = registry

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert "未知工具" in tool_msgs[0]["content"]


@pytest.mark.asyncio
async def test_tool_call_edit_bash_command():
    """'e' choice on bash tool should let user edit the command."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]
    bash_tool = _make_tool_def("bash", is_dangerous=True, is_readonly=False, output="edited output")

    tool_chunks = _make_tool_call_chunks("bash", {"command": "rm -rf /"})
    final_chunks = [_make_text_chunk("Done.")]

    mock_client.chat.completions.create.side_effect = [tool_chunks, final_chunks]

    ask_responses = iter(["e", "ls -la"])
    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn, \
         patch("rich.prompt.Prompt.ask", side_effect=lambda *a, **kw: next(ask_responses)):
        mock_registry_fn.return_value = _setup_registry(MagicMock(), bash_tool)

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert "edited output" in tool_msgs[0]["content"]


@pytest.mark.asyncio
async def test_no_tool_call_just_text():
    """When LLM responds with text only (no tool calls), return the text."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]

    text_chunks = [
        _make_text_chunk("Hello! "),
        _make_text_chunk("How can I help?"),
    ]

    mock_client.chat.completions.create.return_value = text_chunks

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn:
        registry = MagicMock()
        registry.get_openai_schemas.return_value = []
        mock_registry_fn.return_value = registry

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    assert "Hello!" in result
    assert "How can I help?" in result


@pytest.mark.asyncio
async def test_max_tool_rounds_limit():
    """Should stop after max_tool_rounds and return a message."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]

    bash_tool = _make_tool_def("bash", is_dangerous=False, is_readonly=True, output="ok")
    tool_chunks = _make_tool_call_chunks("bash", {"command": "echo hi"})

    mock_client.chat.completions.create.side_effect = [tool_chunks] * 6

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn:
        mock_registry_fn.return_value = _setup_registry(MagicMock(), bash_tool)

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    assert "上限" in result or "limit" in result.lower() or "轮次" in result


@pytest.mark.asyncio
async def test_tool_result_truncation():
    """Tool results should be truncated to 4000 chars to avoid token overflow."""
    cli = _make_chat_cli()
    mock_client = cli.agent.llm_client["client"]

    long_output = "A" * 10000
    tool = _make_tool_def("nmap", is_dangerous=False, is_readonly=True, output=long_output)

    tool_chunks = _make_tool_call_chunks("nmap", {"target": "127.0.0.1"})
    final_chunks = [_make_text_chunk("Done.")]

    mock_client.chat.completions.create.side_effect = [tool_chunks, final_chunks]

    with patch("src.cli.tools.get_tool_registry") as mock_registry_fn:
        mock_registry_fn.return_value = _setup_registry(MagicMock(), tool)

        messages = [{"role": "system", "content": "test"}]
        result = await cli._chat_with_tools(messages)

    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert len(tool_msgs[0]["content"]) <= 4000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
