#!/bin/bash

echo "========================================"
echo "ClawAI 前端启动脚本"
echo "========================================"
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js"
    echo "请安装Node.js 16.0或更高版本"
    echo "下载地址: https://nodejs.org/"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm"
    echo "请确保Node.js安装完整"
    exit 1
fi

# 显示版本信息
echo "✅ Node.js版本:"
node --version
echo "✅ npm版本:"
npm --version
echo ""

# 检查前端目录
if [ ! -d "frontend" ]; then
    echo "❌ 错误: 未找到frontend目录"
    echo "请确保在当前目录运行脚本"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查package.json
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 未找到package.json"
    echo "前端项目结构不完整"
    exit 1
fi

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "⚠️ 检测到未安装依赖，开始安装..."
    echo "这可能需要几分钟时间，请耐心等待..."
    echo ""
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 错误: 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
    echo ""
fi

echo "🚀 启动ClawAI前端..."
echo "访问地址: http://localhost:5173"
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动开发服务器
npm run dev