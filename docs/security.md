# Security

## Authentication and Authorization

### JWT Authentication

ClawAI uses JSON Web Tokens (JWT) for API authentication. Tokens are issued upon login and validated on every request to protected endpoints.

- Tokens are signed with `JWT_SECRET_KEY` (must be changed from default in production)
- Token expiration is configurable via environment variables
- The `python-jose` library handles JWT encoding/decoding with cryptographic signatures

### RBAC

Role-Based Access Control is implemented in `src/shared/backend/auth/` with five default roles:

| Role | Permissions |
|------|-------------|
| admin | Full system access, user management, destructive operations |
| operator | Execute scans and tools, view reports |
| analyst | View scan results and reports, read-only |
| viewer | View dashboards only |
| guest | Limited read access |

RBAC configuration is loaded from `config/rbac.json` at startup. The `PermissionManager` enforces role-based checks on all API endpoints.

## Secret Management

- All secrets are provided through environment variables -- never hardcoded
- The `.env` file (loaded by `python-dotenv`) holds local configuration
- `.env` is excluded from version control via `.gitignore`
- `.env.example` documents all available variables without exposing values
- Pre-commit hooks include `detect-private-key` to prevent accidental key commits

Required secrets in production:

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Signs JWT tokens |
| `SECRET_KEY` | General application secret |
| `DEEPSEEK_API_KEY` | DeepSeek LLM access |
| `OPENAI_API_KEY` | OpenAI LLM access |
| `ANTHROPIC_API_KEY` | Anthropic LLM access |

## Audit System

All sensitive operations are logged to the audit system:

- Tool executions (tool name, target, arguments, result summary)
- Authentication events (login, logout, token refresh)
- RBAC permission changes
- Configuration modifications
- Destructive operations (available to admin role only)

Audit logs are stored in `data/audit/` organized by date. The audit storage directory is configurable via `AUDIT_STORAGE_DIR`.

## Tool Execution Safety

### Execution Modes

| Mode | Behavior |
|------|----------|
| **Real** | Executes actual tool binary. Requires the tool to be installed on the host. |
| **Simulated** | Returns mock results. Safe for testing and training. |
| **Hybrid** | Attempts real execution first; falls back to simulated on failure. |

### Timeout Controls

All tool executions have configurable timeouts to prevent runaway processes. Default timeouts are set per tool category and can be overridden in `config/tools_extended.json`.

### Sandboxing

Tool execution runs in a controlled environment. The `TOOLS_DIR` environment variable isolates tool binaries to a designated directory.

## Input Validation

`src/shared/backend/input_validator.py`

The `InputValidator` class detects and blocks malicious input patterns before they reach tool execution:

| Attack Type | Detection Pattern |
|-------------|-------------------|
| SQL Injection | UNION SELECT, OR 1=1, sleep(), benchmark() |
| XSS | `<script>` tags, event handlers (onload, onerror, onclick) |
| Path Traversal | `../` and `..\` sequences |
| Command Injection | exec(), system(), popen(), eval(), pipe commands |
| Protocol Injection | file://, php://, data://, javascript: |
| Time-based Blind | sleep(), waitfor delay, pg_sleep() |

Additional validations:
- Target address length limits
- IP address and port range validation
- URL format validation
- Domain name format validation

## Responsible Use

ClawAI is designed for **authorized security testing only**. By using this software you agree to:

1. Only test systems you own or have explicit written authorization to test
2. Comply with all applicable laws and regulations
3. Not use the tool for unauthorized access, data theft, or disruption
4. Follow responsible disclosure for any vulnerabilities discovered
5. Use the simulated mode for learning and training when no authorized target is available

The system includes safeguards to promote responsible use:
- API authentication can be enforced via `API_AUTH_ENABLED=true`
- Destructive operations require admin-level RBAC permissions
- All operations are audit-logged
- Input validation prevents common injection patterns in target specifications
