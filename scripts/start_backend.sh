#!/bin/bash

echo "========================================"
echo "ClawAI 后端启动脚本"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ 错误: 未找到Python"
        echo "请安装Python 3.8或更高版本"
        echo "下载地址: https://python.org/"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 显示版本信息
echo "✅ Python版本:"
$PYTHON_CMD --version
echo ""

# 检查后端目录
if [ ! -d "backend" ]; then
    echo "❌ 错误: 未找到backend目录"
    echo "请确保在当前目录运行脚本"
    exit 1
fi

# 进入后端目录
cd backend

# 检查app.py
if [ ! -f "app.py" ]; then
    echo "❌ 错误: 未找到app.py"
    echo "后端项目结构不完整"
    exit 1
fi

# 检查requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "⚠️ 警告: 未找到requirements.txt"
    echo "将尝试直接启动应用..."
else
    echo "📦 检查Python依赖..."
    echo ""
    
    # 检查pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        echo "⚠️ 警告: 未找到pip，跳过依赖检查"
    else
        if command -v pip3 &> /dev/null; then
            PIP_CMD="pip3"
        else
            PIP_CMD="pip"
        fi
        
        echo "✅ pip版本:"
        $PIP_CMD --version
        echo ""
        
        # 检查Flask
        $PYTHON_CMD -c "import flask" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "⚠️ 检测到缺少依赖，开始安装..."
            echo "这可能需要几分钟时间，请耐心等待..."
            echo ""
            $PIP_CMD install -r requirements.txt
            if [ $? -ne 0 ]; then
                echo "❌ 错误: 依赖安装失败"
                echo "请手动运行: $PIP_CMD install -r requirements.txt"
                exit 1
            fi
            echo "✅ 依赖安装完成"
            echo ""
        else
            echo "✅ 依赖已安装"
            echo ""
        fi
    fi
fi

echo "🚀 启动ClawAI后端..."
echo "API地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动Flask应用
$PYTHON_CMD app.py