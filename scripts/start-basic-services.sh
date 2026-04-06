#!/bin/bash

# ClawAI 基础服务启动脚本
# 只启动Redis和PostgreSQL，用于网络受限环境

set -e

echo "========================================"
echo "启动 ClawAI 基础服务 (网络受限模式)"
echo "========================================"
echo ""

# 检查Docker环境
echo "步骤1: 检查Docker环境..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker守护进程未运行"
    exit 1
fi
echo "✓ Docker守护进程正常运行"

# 停止现有服务
echo ""
echo "步骤2: 停止现有服务..."
docker-compose -f docker-compose.microservices.yml down --remove-orphans 2>/dev/null || true
echo "✓ 已停止现有服务"

# 尝试拉取Redis镜像（使用阿里云镜像）
echo ""
echo "步骤3: 拉取Redis镜像 (阿里云镜像)..."
echo "尝试两个可能的镜像源..."
if docker pull registry.cn-hangzhou.aliyuncs.com/aliyun-ocs/redis:7-alpine; then
    echo "✓ Redis镜像拉取成功 (aliyun-ocs)"
    # 标记为redis:7-alpine以便docker-compose使用
    docker tag registry.cn-hangzhou.aliyuncs.com/aliyun-ocs/redis:7-alpine redis:7-alpine
elif docker pull registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine; then
    echo "✓ Redis镜像拉取成功 (library)"
    # 标记为redis:7-alpine以便docker-compose使用
    docker tag registry.cn-hangzhou.aliyuncs.com/library/redis:7-alpine redis:7-alpine
else
    echo "⚠️  阿里云镜像拉取失败，尝试Docker Hub官方镜像"
    echo "注意: 可能需要VPN或代理"
    read -p "是否尝试拉取Docker Hub官方镜像? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if docker pull redis:7-alpine; then
            echo "✓ Docker Hub Redis镜像拉取成功"
        else
            echo "❌ 所有镜像源都拉取失败"
            echo "   请检查网络连接或配置镜像加速器"
        fi
    fi
fi

# 尝试拉取PostgreSQL镜像
echo ""
echo "步骤4: 拉取PostgreSQL镜像 (可能需要代理)..."
echo "提示: pgvector/pgvector:pg16 可能无法从国内直接访问"
echo "      如果拉取失败，请配置VPN或代理后重试"
echo ""

read -p "是否尝试拉取PostgreSQL镜像? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if docker pull pgvector/pgvector:pg16; then
        echo "✓ PostgreSQL镜像拉取成功"
    else
        echo "❌ PostgreSQL镜像拉取失败"
        echo "   您可以:"
        echo "   1. 使用VPN连接国际网络"
        echo "   2. 配置HTTP代理: export HTTP_PROXY=http://your-proxy:port"
        echo "   3. 手动下载镜像并导入: docker load < postgres-image.tar"
    fi
fi

# 启动基础服务
echo ""
echo "步骤5: 启动基础服务..."
echo "启动Redis和PostgreSQL..."

# 使用中国镜像配置（临时）
cat > docker-compose.basic.yml << 'EOF'
version: '3.8'
services:
  redis:
    image: registry.cn-hangzhou.aliyuncs.com/aliyun-ocs/redis:7-alpine
    container_name: clawai-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  postgres:
    image: registry.aliyuncs.com/pgvector/pgvector:pg16
    container_name: clawai-postgres
    environment:
      POSTGRES_DB: clawai
      POSTGRES_USER: clawai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-clawai123}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clawai"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
    driver: local
  postgres_data:
    driver: local
EOF

docker-compose -f docker-compose.basic.yml up -d

# 等待服务启动
echo ""
echo "步骤6: 等待服务启动..."
echo "等待20秒..."

for i in {1..20}; do
    if docker-compose -f docker-compose.basic.yml exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo "✓ Redis服务就绪"
        break
    fi
    sleep 1
done

for i in {1..20}; do
    if docker-compose -f docker-compose.basic.yml exec -T postgres pg_isready -U clawai 2>/dev/null; then
        echo "✓ PostgreSQL服务就绪"
        break
    fi
    sleep 1
done

echo ""
echo "========================================"
echo "基础服务启动完成"
echo "========================================"
echo ""
echo "✅ 服务状态:"
echo "   Redis:       localhost:6379"
echo "   PostgreSQL:  localhost:5432"
echo ""
echo "📊 验证命令:"
echo "   Redis:       docker-compose -f docker-compose.basic.yml exec redis redis-cli ping"
echo "   PostgreSQL:  docker-compose -f docker-compose.basic.yml exec postgres psql -U clawai -d clawai -c 'SELECT 1'"
echo ""
echo "🚀 启动完整微服务:"
echo "   1. 确保网络连接正常 (可能需要VPN/代理)"
echo "   2. 运行: ./start-microservices.sh"
echo ""
echo "⚙️  网络问题解决方案:"
echo "   1. 配置阿里云镜像加速器: .\configure-docker-mirror.ps1"
echo "   2. 使用代理: export HTTP_PROXY=http://your-proxy:port"
echo "   3. 使用VPN连接"
echo "   4. 手动下载镜像并导入"
echo ""