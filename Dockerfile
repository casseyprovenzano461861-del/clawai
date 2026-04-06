# ClawAI 模块化单体应用 Dockerfile
# 简化的Docker配置，用于生产环境部署
# 生成时间: 2026-04-06
# 版本: 2.0.0 (模块化单体架构)

# 使用Python 3.11轻量级镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
# 包括一些基本的安全工具和系统工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    # 基础网络工具
    iputils-ping \
    netcat-openbsd \
    dnsutils \
    # 安全工具（基础版本，生产环境建议使用专用容器）
    nmap \
    nikto \
    whatweb \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
# 复制依赖文件
COPY requirements.txt .
COPY requirements-dev.txt .

# 安装生产依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录结构
RUN mkdir -p \
    logs \
    data/databases \
    data/audit \
    config \
    tools/penetration

# 设置环境变量默认值
ENV ENVIRONMENT=production
ENV SERVER_HOST=0.0.0.0
ENV BACKEND_PORT=8000
ENV DATABASE_URL=sqlite:////app/data/databases/clawai.db
ENV TOOLS_DIR=/app/tools/penetration
ENV AUDIT_STORAGE_DIR=/app/data/audit
ENV LOG_LEVEL=INFO
ENV LOG_FILE=/app/logs/clawai.log
ENV RBAC_CONFIG_PATH=/app/config/rbac.json
ENV MODULES_CONFIG_PATH=/app/config/modules.yaml

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
# 使用run.py启动模块化单体应用
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]

# 构建标签
LABEL maintainer="ClawAI Team"
LABEL version="2.0.0"
LABEL description="ClawAI - 智能安全评估系统 (模块化单体架构)"