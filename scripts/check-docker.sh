#!/bin/bash

echo "========================================"
echo "Docker Desktop 诊断工具 (Bash版本)"
echo "========================================"
echo ""

# 检查Docker CLI
echo "1. 检查Docker CLI..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo "   ✓ Docker CLI已安装: $docker_version"
else
    echo "   ❌ Docker CLI未安装"
    echo "   请安装Docker Desktop: https://docs.docker.com/desktop/"
    exit 1
fi

# 检查Docker Compose
echo ""
echo "2. 检查Docker Compose..."
if command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose --version)
    echo "   ✓ Docker Compose已安装: $compose_version"
else
    echo "   ❌ Docker Compose未安装"
    echo "   Docker Desktop通常包含docker-compose，请检查安装"
fi

# 测试Docker守护进程连接
echo ""
echo "3. 测试Docker守护进程连接..."
if docker info > /dev/null 2>&1; then
    echo "   ✓ Docker守护进程连接正常"
    
    # 显示Docker信息摘要
    echo ""
    echo "   Docker系统信息:"
    docker info --format '{{json .}}' | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'    容器: {data.get(\"Containers\", 0)} 运行中 / {data.get(\"Containers\", 0)} 总计')
print(f'    镜像: {data.get(\"Images\", 0)}')
print(f'    OS: {data.get(\"OperatingSystem\", \"N/A\")}')
"
else
    echo "   ❌ Docker守护进程连接失败"
    echo ""
    echo "   错误信息:"
    docker info 2>&1 | sed 's/^/     /'
    echo ""
    echo "   ⚠️  Docker Desktop可能未运行"
    echo ""
    echo "   解决方案:"
    echo "   1. 启动Docker Desktop应用程序"
    echo "   2. 等待系统托盘显示 'Docker Desktop is running'"
    echo "   3. 可能需要30-60秒完全启动"
    echo ""
    echo "   在Windows上:"
    echo "   • 点击开始菜单，搜索 'Docker Desktop'"
    echo "   • 或查找任务栏的Docker鲸鱼图标"
    echo ""
    echo "   如果已启动但仍有问题:"
    echo "   • 右键点击系统托盘图标 → Restart"
    echo "   • 重启计算机"
    exit 1
fi

# 检查是否有正在运行的容器
echo ""
echo "4. 检查运行中的容器..."
running_containers=$(docker ps -q | wc -l)
if [ "$running_containers" -gt 0 ]; then
    echo "   ✓ 有 $running_containers 个容器正在运行"
else
    echo "   ℹ️  没有运行中的容器 (正常状态)"
fi

echo ""
echo "========================================"
echo "诊断完成"
echo "========================================"
echo ""
echo "如果所有检查通过，可以运行:"
echo "  ./start-microservices.sh"
echo ""
echo "如需查看详细Docker信息:"
echo "  docker info"
echo "  docker system df"
