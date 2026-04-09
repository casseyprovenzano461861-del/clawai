# ClawAI

AI-powered automated penetration testing system integrating LLM agents with security tools for vulnerability discovery, exploitation, and reporting.

## Key Features

- **P-E-R Framework** -- Planner-Executor-Reflector loop decomposes high-level goals into subtask graphs, executes them, and reflects on results
- **30+ Security Tool Integrations** -- nmap, nuclei, sqlmap, metasploit, hashcat, and more with real/simulated/hybrid execution modes
- **27 Skills** -- 14 built-in + 13 extended skills (SQLi, XSS, RCE, SSRF, XXE, privilege escalation, etc.) with OpenAI Function Calling schemas
- **Multi-LLM Support** -- 5 providers (OpenAI, DeepSeek, Anthropic, Ollama, Mock) with smart/cheap tier routing and cost tracking
- **CLI with TUI** -- Interactive chat, quick scan, tool management, and status commands with a Textual-based rich terminal UI
- **3D Attack Chain Visualization** -- React frontend with Three.js and vis-network for interactive attack path exploration
- **RBAC + Audit** -- JWT authentication, 5 default roles, full audit logging of sensitive operations

## Architecture

```
ClawAI
  Backend (FastAPI)
    P-E-R Agent       -- planner.py, executor.py, reflector.py
    LLM Abstraction   -- base.py, openai/anthropic/deepseek/ollama/mock backends
    ModelRouter       -- smart/cheap tier routing with cost tracking
    EventBus          -- thread-safe singleton pub/sub (7 event types)
    Skills System     -- core.py, registry.py, extended_skills.py
    Tool Integration  -- 30+ tools, real/simulated/hybrid modes
    Auth & RBAC       -- JWT + role-based access control
    Input Validation  -- SQLi, XSS, path traversal, command injection detection
  Frontend (React + Vite)
    vis-network       -- network topology graphs
    Three.js          -- 3D attack chain visualization
  CLI (Textual TUI)
    chat / scan / tools / status commands
```

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys (DEEPSEEK_API_KEY, OPENAI_API_KEY, etc.)

# Start backend
python start.py                    # http://localhost:8000

# Start frontend
cd frontend && npm install && npm run dev  # http://localhost:3000
```

## CLI Usage

```bash
# AI chat mode (default)
python clawai.py
python clawai.py chat -t example.com

# Quick scan
python clawai.py scan 192.168.1.1

# Tool management
python clawai.py tools list

# Service status
python clawai.py status
```

## Docker

```bash
docker-compose up -d
```

This starts the ClawAI backend, Qdrant vector DB, and Redis. Add the `monitoring` profile for Prometheus + Grafana:

```bash
docker-compose --profile monitoring up -d
```

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and edit:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | -- |
| `OPENAI_API_KEY` | OpenAI API key | -- |
| `ANTHROPIC_API_KEY` | Anthropic API key | -- |
| `JWT_SECRET_KEY` | JWT signing key | **must change** |
| `SECRET_KEY` | App secret key | **must change** |
| `DATABASE_URL` | Database URL | `sqlite:///./data/databases/clawai.db` |
| `TOOLS_DIR` | Security tools directory | `./tools/penetration` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `API_AUTH_ENABLED` | Enable API authentication | `false` |

See `.env.example` for the full list.

## Testing

```bash
# Unit tests (skip slow/perf)
pytest -m "not slow and not perf"

# With coverage (fails under 30%)
make test-cov

# Integration tests only
pytest -m integration

# Lint and type check
make lint
```

## Project Structure

```
src/
  cli/                    # CLI entry point, TUI, chat logic
  shared/backend/
    ai_core/              # LLM orchestrator, decision engine, knowledge engine
    auth/                 # JWT auth, RBAC, permissions
    llm/                  # LLM backends (openai, anthropic, deepseek, ollama, mock), router
    per/                  # P-E-R framework (planner, executor, reflector)
    skills/               # Skill definitions, registry, executor
    tools/                # Tool integration system
    infrastructure/       # Database, workflow, tool infra
    events.py             # EventBus pub/sub
    input_validator.py    # Input validation and injection detection
frontend/                # React + Vite + Tailwind
tools/penetration/       # Security tool binaries/scripts
config/                  # modules.yaml, tools_extended.json
tests/                   # pytest test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.

## License

MIT
