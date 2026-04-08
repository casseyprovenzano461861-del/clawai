#!/bin/bash

echo "=========================="
echo "ClawAI 一键启动脚本"
echo "=========================="

# 检查Python是否安装
echo "检查Python安装情况..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python。请先安装Python 3.8或更高版本。"
    exit 1
fi
echo "Python已安装"

# 检查后端依赖
echo "检查后端依赖..."
if [ ! -f "backend/requirements.txt" ]; then
    echo "错误: 未找到backend/requirements.txt文件。"
    exit 1
fi

# 安装后端依赖
if [ ! -d "backend/venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv backend/venv
fi

echo "激活虚拟环境..."
source backend/venv/bin/activate

echo "安装后端依赖..."
pip install -r backend/requirements.txt

# 检查前端依赖
echo "检查前端依赖..."
if [ ! -f "frontend/package.json" ]; then
    echo "错误: 未找到frontend/package.json文件。"
    exit 1
fi

# 安装前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 启动后端服务
echo "启动后端服务..."
(source backend/venv/bin/activate && python backend/main.py) &

# 等待后端服务启动
echo "等待后端服务启动..."
sleep 5

# 启动前端开发服务器
echo "启动前端开发服务器..."
(cd frontend && npm run dev) &

# 等待前端服务启动
echo "等待前端服务启动..."
sleep 5

# 打开浏览器
echo "打开浏览器..."
if command -v open &> /dev/null; then
    open http://localhost:5173
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost:5173
else
    echo "请手动打开浏览器访问: http://localhost:5173"
fi

echo "=========================="
echo "ClawAI 启动完成！"
echo "后端服务运行在: http://localhost:5000"
echo "前端服务运行在: http://localhost:5173"
echo "=========================="
echo "按Ctrl+C退出..."

# 等待用户输入
read -r
