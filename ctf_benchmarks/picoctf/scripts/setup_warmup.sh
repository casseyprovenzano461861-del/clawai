#!/bin/bash
# PicoCTF Warm Up 挑战设置脚本
# 用于启动挑战环境的 Docker 容器

set -e  # 出错时退出

echo "正在设置 PicoCTF Warm Up 挑战环境..."

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装或不在 PATH 中"
    exit 1
fi

# 检查镜像是否存在，不存在则构建
IMAGE_NAME="clawai/picoctf-warmup:2023"
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "构建 Docker 镜像: $IMAGE_NAME"

    # 创建临时构建目录
    BUILD_DIR=$(mktemp -d)
    trap "rm -rf $BUILD_DIR" EXIT

    # 创建简单的 HTTP 服务器 Dockerfile
    cat > "$BUILD_DIR/Dockerfile" << 'EOF'
FROM nginx:alpine

# 复制挑战文件
COPY index.html /usr/share/nginx/html/

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
EOF

    # 创建包含标志的 HTML 文件
    cat > "$BUILD_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PicoCTF Warm Up</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .flag {
            background-color: #f0f8ff;
            padding: 10px;
            border-left: 4px solid #2196F3;
            margin: 20px 0;
            font-family: monospace;
            display: none;  # 标志隐藏在注释中
        }
        .instructions {
            background-color: #fffde7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Warm Up Challenge</h1>

        <div class="instructions">
            <h3>Welcome to PicoCTF!</h3>
            <p>This is a warm-up challenge to get you started.</p>
            <p><strong>Goal:</strong> Find the hidden flag.</p>
            <p><strong>Flag format:</strong> picoCTF{...}</p>
            <p><strong>Hint:</strong> The flag might be hidden in plain sight.</p>
        </div>

        <p>Look around the page to find the flag. It's somewhere here...</p>

        <div class="flag" id="flag">
            <!-- Flag: picoCTF{welcome_to_ctf} -->
        </div>

        <p>Good luck! 🍀</p>
    </div>

    <!-- Debug info: Server is running on port 80 -->
</body>
</html>
EOF

    # 构建镜像
    docker build -t "$IMAGE_NAME" "$BUILD_DIR"
    echo "镜像构建完成: $IMAGE_NAME"
else
    echo "镜像已存在: $IMAGE_NAME"
fi

# 检查容器是否已在运行
CONTAINER_NAME="picoctf-warmup-2023"
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "容器已在运行: $CONTAINER_NAME"
        echo "访问地址: http://localhost:8000/"
        exit 0
    else
        echo "启动现有容器: $CONTAINER_NAME"
        docker start "$CONTAINER_NAME"
    fi
else
    # 运行新容器
    echo "启动新容器: $CONTAINER_NAME"
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p 8000:80 \
        --restart unless-stopped \
        --memory 256m \
        --cpus 0.5 \
        "$IMAGE_NAME"
fi

# 等待容器启动
echo "等待容器启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✓ 挑战环境已就绪"
        echo "访问地址: http://localhost:8000/"
        echo "标志隐藏在 HTML 注释中: picoCTF{welcome_to_ctf}"
        exit 0
    fi
    sleep 1
done

echo "✗ 容器启动超时"
docker logs "$CONTAINER_NAME"
exit 1