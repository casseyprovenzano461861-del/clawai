# Architecture

## P-E-R Framework

The core of ClawAI's autonomous reasoning is the **Planner-Executor-Reflector (P-E-R)** loop, located in `src/shared/backend/per/`.

```
Goal --> Planner --> Executor --> Reflector --> (revise plan) --> Planner --> ...
                       |
                       v
                   Tool calls
                       |
                       v
                   Results / Findings
```

- **Planner** (`planner.py`) -- Decomposes a high-level penetration testing goal into a directed graph of executable subtasks. Each subtask specifies the tool to use, expected inputs, and success criteria.
- **Executor** (`executor.py`) -- Runs subtasks sequentially or in parallel, invoking tools via the unified tool interface. Handles timeouts, retries, and result collection.
- **Reflector** (`reflector.py`) -- Evaluates execution results against the plan. If a subtask fails or produces unexpected findings, the reflector revises the plan and feeds it back to the planner.
- **Agent** (`agent.py`) -- Orchestrates the full P-E-R loop, managing state transitions (idle, running, paused, completed, error) and communicating progress via the EventBus.

The P-E-R agent automatically recognizes `skill_` prefixed tool calls and delegates them to the Skills system.

## LLM Abstraction Layer

`src/shared/backend/llm/`

All LLM interactions go through the `LLMBackend` abstract base class (`base.py`), which defines two core interfaces:

- `chat(messages, **kwargs) -> ChatResponse` -- Synchronous completion
- `stream_chat(messages, **kwargs) -> AsyncIterator[StreamChunk]` -- Streaming completion

Five concrete backends:

| Backend | File | Provider |
|---------|------|----------|
| `OpenAIBackend` | `openai_backend.py` | OpenAI (GPT-4, GPT-3.5) |
| `DeepSeekBackend` | `openai_backend.py` | DeepSeek (deepseek-chat, deepseek-reasoner) |
| `AnthropicBackend` | `anthropic_backend.py` | Anthropic (Claude) |
| `OllamaBackend` | `ollama_backend.py` | Ollama (local models) |
| `MockBackend` | `mock_backend.py` | Testing / offline mode |

Backends are created via `create_backend(provider, model)` and are interchangeable -- any component that accepts an `LLMBackend` can use any provider.

## ModelRouter

`src/shared/backend/llm/router.py`

The `ModelRouter` implements two-tier routing to minimize API costs:

| Task Type | Tier | Rationale |
|-----------|------|-----------|
| `PLANNING` | smart | Complex reasoning required |
| `REFLECTION` | smart | Deep analysis needed |
| `EXECUTION` | cheap | Straightforward tool invocation |
| `TOOL_SELECT` | cheap | Low-complexity selection |
| `CHAT` | cheap | Prioritize response speed |

Configuration via environment variables:

```
ROUTER_SMART_PROVIDER=deepseek
ROUTER_SMART_MODEL=deepseek-chat
ROUTER_CHEAP_PROVIDER=deepseek
ROUTER_CHEAP_MODEL=deepseek-chat
```

Cost tracking is built in -- call `router.get_stats()` for cumulative token usage and USD cost per tier. Any call can override the default tier with `tier="smart"` or `tier="cheap"`.

## EventBus

`src/shared/backend/events.py`

A thread-safe, singleton publish/subscribe event bus that decouples the P-E-R agent from the UI layer (TUI/CLI).

Seven event types:

| Type | Direction | Purpose |
|------|-----------|---------|
| `STATE_CHANGED` | Agent -> UI | State transition (idle/running/paused/completed/error) |
| `MESSAGE` | Agent -> UI | Text output (info/success/error/warning) |
| `TOOL` | Agent -> UI | Tool invocation start/complete/error |
| `FINDING` | Agent -> UI | Vulnerability or flag discovered |
| `PROGRESS` | Agent -> UI | Progress percentage and description |
| `USER_COMMAND` | UI -> Agent | Pause/resume/stop commands |
| `USER_INPUT` | UI -> Agent | Additional natural language instructions |

Key design properties:
- Singleton -- one instance shared across the process
- Thread-safe -- all operations guarded by a lock
- Fault-tolerant -- subscriber exceptions do not affect other subscribers

## Skills System

`src/shared/backend/skills/`

The Skills system encapsulates penetration testing techniques as callable units that the P-E-R agent can invoke through OpenAI Function Calling.

**Core components:**

- `core.py` -- `Skill` dataclass, `SkillExecutor` that runs a skill against a target, and `get_openai_tools()` that generates Function Calling schemas from skill definitions
- `registry.py` -- `SkillRegistry` singleton holding all skills, with `execute()`, `search()`, and `get_openai_tools()` methods
- `extended_skills.py` -- 13 additional skills covering XXE, SSRF, SSTI, IDOR, CSRF, deserialization, NoSQL injection, flag detection, WAF detection, and privilege escalation, plus `PayloadMutator` and WAF fingerprint database

**Built-in skills (14):** sqli_basic, sqli_union, sqli_time_blind, xss_reflected, xss_stored, auth_bypass_sql, auth_bruteforce, info_backup_files, info_sensitive_paths, rce_command_injection, lfi_basic, dvwa_sqli, dvwa_xss, dvwa_bruteforce

**Extended skills (13):** xxe_testing, ssrf_testing, file_upload_testing, ssti_testing, idor_testing, csrf_testing, deserialization_testing, nosql_injection, flag_detector, waf_detect, openssh_user_enum, privesc_linux, privesc_windows

**Auxiliary:** `PayloadMutator` generates WAF bypass variants; `WAF_SIGNATURES` contains 15+ WAF fingerprints; `FLAG_PATTERNS` covers common CTF flag formats.

## Tool Integration

`src/shared/backend/tools/`

ClawAI integrates 30+ security tools across several categories:

| Category | Tools |
|----------|-------|
| Network scanning | nmap, masscan, rustscan |
| Web scanning | nuclei, nikto, sqlmap, xsstrike, commix |
| Directory enumeration | gobuster, dirsearch, ffuf, feroxbuster |
| Information gathering | amass, subfinder, theharvester, dnsrecon |
| Password cracking | hashcat, john, hydra, medusa |
| Post-exploitation | metasploit, impacket, evil-winrm, crackmapexec |

Three execution modes:

- **Real** -- Executes the actual tool binary on the host (requires tool installed)
- **Simulated** -- Returns mock results for testing and training
- **Hybrid** -- Attempts real execution, falls back to simulated on failure

All tool invocations are subject to timeout controls and audit logging.

## CLI Module

`src/cli/`

The CLI provides both a simple command interface and a rich TUI:

| Command | Description |
|---------|-------------|
| `chat` | AI conversation mode with optional target (`-t`) |
| `scan` | Quick vulnerability scan |
| `tools` | List and manage integrated tools |
| `status` | Show service status |

Key files:
- `main.py` -- Entry point using Click
- `chat_cli.py` -- Intent recognition and task execution for chat mode
- `tui/app.py` -- Textual-based TUI application
- `tui/widgets/` -- UI components (ChatInput, MessageList, StatusBar)
- `prompts/chat_system.py` -- System prompts for the chat AI
- `completer.py` -- Tab completion for commands

The TUI communicates with the P-E-R agent via the EventBus, receiving real-time updates on state changes, tool invocations, and findings.

## Frontend

`frontend/`

- **React 18** + **Vite 5** + **TailwindCSS 3** for the UI layer
- **vis-network** for interactive network topology and knowledge graph visualization
- **Three.js** for 3D attack chain visualization with rotatable node graphs
- WebSocket connections for real-time progress updates from the backend

The frontend connects to the FastAPI backend's REST API and WebSocket endpoints for bidirectional communication.
