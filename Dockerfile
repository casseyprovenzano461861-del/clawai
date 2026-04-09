# ClawAI Multi-stage Production Dockerfile
# Separates build dependencies from runtime for minimal attack surface
# Version: 3.0.0 (Production Hardened)

# ============ Stage 1: Builder ============
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install build dependencies only
COPY requirements.txt .
RUN pip install --no-compile --prefix=/install -r requirements.txt

# ============ Stage 2: Runtime ============
FROM python:3.11-slim

# Metadata
LABEL maintainer="ClawAI Team"
LABEL version="3.0.0"
LABEL description="ClawAI - AI-powered Security Assessment System"

WORKDIR /app

# Minimal runtime environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/app/.local/bin:$PATH"

# Install only runtime system dependencies (no security tools in base image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user and required directories
RUN groupadd -r clawai && \
    useradd -r -g clawai -d /app -s /sbin/nologin clawai && \
    mkdir -p logs data/databases data/audit config && \
    chown -R clawai:clawai /app

USER clawai

# Runtime defaults
ENV ENVIRONMENT=production
ENV SERVER_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV DATABASE_URL=sqlite:////app/data/databases/clawai.db
ENV TOOLS_DIR=/app/tools/penetration
ENV AUDIT_STORAGE_DIR=/app/data/audit
ENV LOG_LEVEL=INFO
ENV LOG_FILE=/app/logs/clawai.log
# 生产环境默认 JSON 结构化日志
ENV LOG_JSON=true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]