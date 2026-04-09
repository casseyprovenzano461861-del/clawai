# Contributing to ClawAI

## Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/ClawAI/ClawAI.git
cd ClawAI

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

- Line length: 120
- Target Python: 3.8+
- No bare `except:` clauses
- Selected rule sets: E, F, W, S (flake8-bandit), B (bugbear), A, PIE, Q, T20

```bash
# Check
ruff check .

# Auto-fix
ruff check --fix .
ruff format .
```

We also run `mypy` for type checking:

```bash
mypy src
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add SSRF testing skill
fix: correct tool timeout handling in executor
chore: update dependencies
docs: add deployment guide
refactor: extract input validation into standalone module
test: add unit tests for ModelRouter
```

## PR Process

1. Create a feature branch from `main`: `git checkout -b feature/your-feature`
2. Make your changes with clear, focused commits
3. Ensure lint and tests pass:
   ```bash
   make lint
   make test
   ```
4. Coverage must not drop below 30% (enforced by `make test-cov`)
5. Open a pull request with a description of the change and motivation

## Testing

We use pytest with the following markers:

| Marker | Purpose |
|--------|---------|
| `unit` | Unit tests (no external dependencies) |
| `integration` | Integration tests (require external services) |
| `slow` | Long-running tests |
| `perf` | Performance benchmarks |

```bash
# Default: unit tests only
pytest -m "not slow and not perf"

# Everything
pytest

# Integration tests
pytest -m integration

# With coverage
pytest --cov=src --cov-report=term-missing
```

## Pre-commit Hooks

The project includes pre-commit hooks for:

- **ruff** -- lint and format
- **bandit** -- security issue detection
- **detect-private-key** -- prevent accidental key commits

## Security

- Never commit `.env` files, API keys, or credentials
- Use environment variables for all secrets (see `.env.example`)
- Report security vulnerabilities privately rather than in public issues
- All security tool usage must be within authorized testing contexts only
