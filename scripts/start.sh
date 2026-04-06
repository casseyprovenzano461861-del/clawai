#!/bin/bash


# ClawAI 项目启动脚本
# 借鉴PentAGI的启动方式

set -e

echo "========================================"
echo "ClawAI 智能安全评估系统"
echo "========================================"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    echo "请先安装Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 创建必要的目录
mkdir -p data logs reports

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置环境变量"
fi

# 启动服务
echo "启动ClawAI服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✓ 后端API服务运行正常"
else
    echo "✗ 后端API服务启动失败"
    docker-compose logs backend
    exit 1
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ 前端Web服务运行正常"
else
    echo "✗ 前端Web服务启动失败"
    docker-compose logs frontend
    exit 1
fi

# 显示服务信息
echo ""
echo "========================================"
echo "服务启动完成！"
echo "========================================"
echo "后端API: http://localhost:5000"
echo "前端界面: http://localhost:3000"
echo "数据库: localhost:5432"
echo "Redis缓存: localhost:6379"
echo "Grafana监控: http://localhost:3001"
echo "Prometheus: http://localhost:9090"
echo ""
echo "健康检查: curl http://localhost:5000/health"
echo "API文档: http://localhost:5000/api-docs"
echo ""
echo "停止服务: docker-compose down"
echo "查看日志: docker-compose logs -f"
echo "========================================"