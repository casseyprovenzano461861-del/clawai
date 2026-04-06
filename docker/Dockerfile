# ClawAI Dockerfile
# 构建基于Python的ClawAI后端服务

# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装安全工具（可选）
# 注意：生产环境可能需要单独安装nmap、whatweb等工具
# 这里只安装Python依赖，工具可以通过卷挂载或单独容器提供

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs results

# 设置环境变量默认值
ENV BACKEND_PORT=5000
ENV SERVER_HOST=0.0.0.0
ENV DEBUG=false
ENV API_AUTH_ENABLED=true
ENV DATABASE_TYPE=sqlite
ENV DATABASE_URL=sqlite:////app/clawai.db
ENV LOG_LEVEL=INFO
ENV LOG_FILE=/app/logs/clawai.log

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["python", "backend/api_server.py"]