#!/bin/bash
# OverTheWire Natas Level 0 设置脚本
# 设置 HTTP 基础认证 Web 服务器

set -e

echo "正在设置 OverTheWire Natas Level 0 挑战环境..."

# Docker 检查
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

IMAGE_NAME="clawai/overthewire-natas-level0:latest"
CONTAINER_NAME="overthewire-natas-level0"
HTTP_PORT=8080

# 检查镜像
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "构建 Docker 镜像: $IMAGE_NAME"

    BUILD_DIR=$(mktemp -d)
    trap "rm -rf $BUILD_DIR" EXIT

    # Dockerfile
    cat > "$BUILD_DIR/Dockerfile" << 'EOF'
FROM nginx:alpine

# 安装 htpasswd 工具
RUN apk add --no-cache apache2-utils

# 创建认证文件
RUN htpasswd -bc /etc/nginx/.htpasswd natas0 natas0

# 创建挑战页面
RUN mkdir -p /usr/share/nginx/html/natas0

# 创建包含标志的 HTML 页面
RUN cat > /usr/share/nginx/html/natas0/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Natas Level 0</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #f0f0f0;
            max-width: 800px;
            margin: 100px auto;
            padding: 20px;
        }
        .container {
            background: #2a2a2a;
            padding: 40px;
            border-radius: 10px;
            border: 2px solid #444;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        h1 {
            color: #4CAF50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .content {
            background: #333;
            padding: 30px;
            border-radius: 8px;
            border-left: 5px solid #4CAF50;
        }
        .flag-hint {
            background: #1e3a1e;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
            border: 1px solid #4CAF50;
        }
        code {
            background: #1a1a1a;
            padding: 10px;
            border-radius: 5px;
            display: block;
            margin: 10px 0;
            color: #ff9800;
            font-size: 1.1em;
        }
        .hidden-flag {
            opacity: 0.1;
            transition: opacity 0.3s;
            font-size: 0.9em;
        }
        .hidden-flag:hover {
            opacity: 1;
        }
        .instructions {
            background: #2c3e50;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 5px solid #3498db;
        }
        .auth-info {
            background: #3d2c2c;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border-left: 5px solid #e74c3c;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🕵️ Natas Level 0</h1>

        <div class="instructions">
            <h3>Welcome to Natas!</h3>
            <p>Natas teaches the basics of web security.</p>
            <p><strong>Goal:</strong> Find the password for the next level.</p>
            <p><strong>Hint:</strong> Check the page source.</p>
        </div>

        <div class="content">
            <p>Congratulations! You've reached Natas Level 0.</p>
            <p>This level is very basic. The password for the next level is hidden on this page.</p>

            <div class="flag-hint">
                <p><strong>Look carefully:</strong> The password might be in the HTML source code.</p>
                <p>Use your browser's "View Source" feature or a command line tool like curl.</p>
                <code>curl -u natas0:natas0 http://localhost:8080/natas0/</code>
            </div>

            <!-- The password for natas1 is gtVrDuiDfck831PqWsLEZy5gyDz1clto -->

            <div class="auth-info">
                <p><strong>Authentication Info:</strong></p>
                <p>Username: natas0</p>
                <p>Password: natas0</p>
                <p>This page uses HTTP Basic Authentication.</p>
            </div>
        </div>

        <div class="hidden-flag">
            <!-- Debug: Flag would normally be hidden better -->
            <!-- Actual flag location: in the comment above -->
        </div>
    </div>
</body>
</html>
HTML_EOF

# 创建 nginx 配置
RUN cat > /etc/nginx/conf.d/natas.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name localhost;

    location /natas0/ {
        root /usr/share/nginx/html;
        index index.html;

        # 基础认证
        auth_basic "Natas Level 0";
        auth_basic_user_file /etc/nginx/.htpasswd;

        # 禁止目录列表
        autoindex off;
    }

    # 重定向根路径
    location = / {
        return 302 /natas0/;
    }

    # 默认拒绝其他访问
    location / {
        deny all;
        return 403;
    }
}
NGINX_EOF

# 测试配置
RUN nginx -t

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

    docker build -t "$IMAGE_NAME" "$BUILD_DIR"
    echo "镜像构建完成"
fi

# 启动容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "容器已在运行: $CONTAINER_NAME"
    else
        echo "启动现有容器"
        docker start "$CONTAINER_NAME"
    fi
else
    echo "启动新容器"
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$HTTP_PORT:80" \
        --restart unless-stopped \
        --memory 256m \
        --cpus 0.5 \
        "$IMAGE_NAME"
fi

# 等待服务启动
echo "等待 HTTP 服务启动..."
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$HTTP_PORT/" | grep -q "401\|200\|302"; then
        echo "✓ HTTP 服务已就绪"
        echo "访问地址: http://localhost:$HTTP_PORT/natas0/"
        echo "认证信息:"
        echo "  用户名: natas0"
        echo "  密码: natas0"
        echo "  标志: 在页面源代码的注释中"
        echo "  下一关密码: gtVrDuiDfck831PqWsLEZy5gyDz1clto"
        echo ""
        echo "测试命令:"
        echo "  curl -u natas0:natas0 http://localhost:$HTTP_PORT/natas0/"
        echo "  curl -s -u natas0:natas0 http://localhost:$HTTP_PORT/natas0/ | grep 'The password for natas1 is'"

        # 测试认证
        echo -n "测试认证..."
        if curl -s -u natas0:natas0 "http://localhost:$HTTP_PORT/natas0/" | grep -q "Natas Level 0"; then
            echo "成功"
        else
            echo "失败（但服务已启动）"
        fi

        exit 0
    fi
    sleep 1
done

echo "✗ HTTP 服务启动超时"
docker logs "$CONTAINER_NAME"
exit 1