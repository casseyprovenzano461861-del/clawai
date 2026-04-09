# Deployment

## Docker Deployment (Recommended)

### Prerequisites

- Docker 20.10+
- Docker Compose v2+

### Steps

```bash
# Clone the repository
git clone https://github.com/ClawAI/ClawAI.git
cd ClawAI

# Configure environment
cp .env.example .env
# Edit .env -- at minimum set JWT_SECRET_KEY, SECRET_KEY, and your LLM API keys

# Start services
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

This starts:
- **ClawAI backend** on port 8000 (from Dockerfile)
- **Qdrant** vector database on ports 16333 (REST) and 16334 (gRPC)
- **Redis** on port 16379

### With Monitoring

```bash
docker-compose --profile monitoring up -d
```

Adds:
- **Prometheus** on port 9090
- **Grafana** on port 3000 (default admin password from `GRAFANA_ADMIN_PASSWORD` env var)

### Without Docker

```bash
# Install dependencies
pip install -e .

# Configure
cp .env.example .env

# Start backend
python run.py --host 0.0.0.0 --port 8000

# Or with auto-reload for development
python run.py --reload
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Runtime environment (`development` / `production`) | `development` |
| `SERVER_HOST` | Backend bind address | `0.0.0.0` |
| `BACKEND_PORT` | Backend port | `8000` |
| `DATABASE_URL` | Database connection string | `sqlite:///./data/databases/clawai.db` |
| `TOOLS_DIR` | Security tools directory | `./tools/penetration` |
| `JWT_SECRET_KEY` | JWT token signing key | **must change** |
| `SECRET_KEY` | Application secret key | **must change** |
| `API_AUTH_ENABLED` | Enable JWT authentication on API | `false` |
| `MODULES_CONFIG_PATH` | Module configuration file | `./config/modules.yaml` |
| `RBAC_CONFIG_PATH` | RBAC configuration file | `./config/rbac.json` |
| `AUDIT_STORAGE_DIR` | Audit log directory | `./data/audit` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FILE` | Log file path | `./logs/clawai.log` |
| `DEBUG` | Enable debug mode | `false` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | -- |
| `OPENAI_API_KEY` | OpenAI API key | -- |
| `ANTHROPIC_API_KEY` | Anthropic API key | -- |
| `ROUTER_SMART_PROVIDER` | Smart tier LLM provider | `deepseek` |
| `ROUTER_SMART_MODEL` | Smart tier model name | `deepseek-chat` |
| `ROUTER_CHEAP_PROVIDER` | Cheap tier LLM provider | `deepseek` |
| `ROUTER_CHEAP_MODEL` | Cheap tier model name | `deepseek-chat` |

## Production Checklist

Before deploying to production, verify the following:

- [ ] `JWT_SECRET_KEY` set to a strong, unique value (not the default)
- [ ] `SECRET_KEY` set to a strong, unique value (not the default)
- [ ] `API_AUTH_ENABLED=true` to enforce authentication
- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=INFO` or `WARNING` (not `DEBUG`)
- [ ] `ALLOWED_ORIGINS` configured to restrict CORS origins
- [ ] `ENABLE_AUDIT_LOGGING=true`
- [ ] HTTPS configured via reverse proxy (Nginx, Caddy, etc.)
- [ ] Firewall rules restrict access to backend port
- [ ] Database directory has appropriate permissions
- [ ] Regular backup strategy for `data/` directory

### Nginx Reverse Proxy Example

```nginx
server {
    listen 443 ssl;
    server_name clawai.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring

### Prometheus + Grafana (Optional)

Available via the `monitoring` Docker Compose profile:

```bash
docker-compose --profile monitoring up -d
```

- Prometheus scrapes `/metrics` on the backend
- Grafana dashboards can be configured in `config/grafana/provisioning/`
- Default Grafana credentials: admin / value of `GRAFANA_ADMIN_PASSWORD`

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Module health
curl http://localhost:8000/api/v1/ai/health
curl http://localhost:8000/api/v1/data/health
curl http://localhost:8000/api/v1/tools/health

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Logging

| Log Type | Location |
|----------|----------|
| Application | `logs/clawai.log` |
| Audit | `data/audit/` (organized by date) |
| Docker | `docker-compose logs -f` |

## Scaling Considerations

- **Database**: The default SQLite is suitable for single-instance deployments. For multi-instance setups, switch to PostgreSQL by changing `DATABASE_URL` and installing the `postgres` extra (`pip install -e ".[postgres]"`)
- **Redis**: Used for caching and message queuing. The Docker Compose configuration includes Redis; point `REDIS_URL` to your Redis instance for distributed setups
- **Qdrant**: Vector database for ML features. Runs as a separate service in Docker Compose
- **Stateless backend**: The FastAPI application is stateless and can be horizontally scaled behind a load balancer, provided `DATABASE_URL` and `REDIS_URL` point to shared instances
- **Tool execution**: For high-throughput scanning, consider dedicating worker nodes with the security tools installed and routing tool execution to those nodes
