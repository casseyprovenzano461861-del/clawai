#!/bin/bash

# ClawAI 微服务架构启动脚本
# 一键启动所有微服务并进行健康检查

set -e  # 遇到错误时退出

echo "========================================"
echo "启动 ClawAI 微服务架构"
echo "========================================"
echo ""

# 1. 检查Docker守护进程
echo "步骤1: 检查Docker环境..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker守护进程未运行"
    echo ""
    echo "解决方案:"
    echo "  Windows: 请启动Docker Desktop应用程序，等待系统托盘显示 'Docker Desktop is running'"
    echo "  Linux/Mac: 请运行: sudo systemctl start docker"
    echo ""
    echo "等待10秒后重试..."
    sleep 10
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker守护进程仍然未运行，请手动启动Docker"
        exit 1
    fi
fi
echo "✓ Docker守护进程正常运行"

# 2. 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: docker-compose 未安装"
    exit 1
fi
echo "✓ docker-compose 可用"

# 3. 停止现有服务（避免冲突）
echo ""
echo "步骤2: 停止现有服务..."
if [ -f "docker-compose.microservices.yml" ]; then
    docker-compose -f docker-compose.microservices.yml down --remove-orphans || true
    echo "✓ 已停止现有微服务"
else
    echo "⚠  docker-compose.microservices.yml 文件不存在"
fi

# 4. 构建并启动服务
echo ""
echo "步骤3: 构建并启动微服务..."
echo "这可能需要几分钟时间，请耐心等待..."

# 首先启动基础依赖（Redis和PostgreSQL）
echo "启动基础依赖服务 (Redis + PostgreSQL)..."
docker-compose -f docker-compose.microservices.yml up -d redis postgres

# 等待数据库就绪
echo "等待数据库服务就绪..."
for i in {1..30}; do
    if docker-compose -f docker-compose.microservices.yml exec -T postgres pg_isready -U clawai > /dev/null 2>&1; then
        echo "✓ PostgreSQL数据库就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL数据库启动超时"
        docker-compose -f docker-compose.microservices.yml logs postgres
        exit 1
    fi
    sleep 2
done

# 等待Redis就绪
echo "等待Redis服务就绪..."
for i in {1..30}; do
    if docker-compose -f docker-compose.microservices.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Redis启动超时"
        docker-compose -f docker-compose.microservices.yml logs redis
        exit 1
    fi
    sleep 2
done

# 构建并启动所有服务
echo "构建并启动所有微服务..."
docker-compose -f docker-compose.microservices.yml build --no-cache
docker-compose -f docker-compose.microservices.yml up -d

# 5. 等待服务启动
echo ""
echo "步骤4: 等待服务启动..."
echo "等待30秒让所有服务完全启动..."
sleep 30

# 6. 验证服务健康状态
echo ""
echo "步骤5: 验证服务健康状态..."
echo ""

SERVICES=(
    "API网关:8080"
    "AI引擎:8081" 
    "工具执行:8082"
    "数据服务:8083"
)

ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    name=$(echo "$service" | cut -d: -f1)
    port=$(echo "$service" | cut -d: -f2)
    
    echo -n "检查 $name (http://localhost:$port/health)... "
    
    if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ 健康"
    else
        echo "❌ 不健康"
        ALL_HEALTHY=false
    fi
done

echo ""
if [ "$ALL_HEALTHY" = true ]; then
    echo "✅ 所有微服务启动成功！"
else
    echo "⚠  部分服务可能未完全启动，请检查日志:"
    echo "    docker-compose -f docker-compose.microservices.yml logs"
fi

# 7. 显示服务信息
echo ""
echo "========================================"
echo "ClawAI 微服务架构启动完成"
echo "========================================"
echo ""
echo "📡 服务端点:"
echo "  • API网关文档:    http://localhost:8080/docs"
echo "  • AI引擎文档:     http://localhost:8081/docs"
echo "  • 工具执行文档:   http://localhost:8082/docs"
echo "  • 数据服务文档:   http://localhost:8083/docs"
echo ""
echo "📊 监控系统:"
echo "  • Grafana监控面板: http://localhost:3001"
echo "  • Prometheus指标:  http://localhost:9090"
echo ""
echo "🛠️  管理命令:"
echo "  • 查看日志: docker-compose -f docker-compose.microservices.yml logs -f"
echo "  • 停止服务: docker-compose -f docker-compose.microservices.yml down"
echo "  • 重启服务: docker-compose -f docker-compose.microservices.yml restart"
echo ""
echo "🔧 快速测试命令:"
echo "  • 健康检查: curl http://localhost:8080/health | python -m json.tool"
echo "  • 工具列表: curl http://localhost:8080/api/v1/tools/available"
echo "  • 测试nmap: curl -X POST http://localhost:8080/api/v1/tools/execute \\"
echo "      -H \"Content-Type: application/json\" \\"
echo "      -d '{\"tool\": \"nmap\", \"target\": \"scanme.nmap.org\", \"parameters\": {\"ports\": \"80,443\"}}'"
echo ""
echo "========================================"
