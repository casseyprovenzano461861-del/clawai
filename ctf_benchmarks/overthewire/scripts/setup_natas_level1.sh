#!/bin/bash
# OverTheWire Natas Level 1 设置脚本
# 设置右键点击禁用的 Web 服务器

set -e

echo "正在设置 OverTheWire Natas Level 1 挑战环境..."

# Docker 检查
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

IMAGE_NAME="clawai/overthewire-natas-level1:latest"
CONTAINER_NAME="overthewire-natas-level1"
HTTP_PORT=8081

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

# 创建认证文件 (natas1 / 上一关的标志)
RUN htpasswd -bc /etc/nginx/.htpasswd natas1 gtVrDuiDfck831PqWsLEZy5gyDz1clto

# 创建挑战页面
RUN mkdir -p /usr/share/nginx/html/natas1

# 创建包含右键点击禁用的 HTML 页面
RUN cat > /usr/share/nginx/html/natas1/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Natas Level 1</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #f0f0f0;
            max-width: 800px;
            margin: 100px auto;
            padding: 20px;
            user-select: none; /* 禁止文字选择 */
        }
        .container {
            background: #2a2a2a;
            padding: 40px;
            border-radius: 10px;
            border: 2px solid #444;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        h1 {
            color: #FF9800;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .warning {
            background: #4a2c2c;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #f44336;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
        }
        .content {
            background: #333;
            padding: 30px;
            border-radius: 8px;
        }
        .hint-box {
            background: #2c3e50;
            padding: 20px;
            border-radius: 8px;
            margin: 30px 0;
            border-left: 5px solid #3498db;
        }
        code {
            background: #1a1a1a;
            padding: 10px;
            border-radius: 5px;
            display: block;
            margin: 10px 0;
            color: #4CAF50;
            font-size: 1.1em;
        }
        .auth-info {
            background: #3d2c2c;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border-left: 5px solid #e74c3c;
            font-size: 0.9em;
        }
        .bypass-tips {
            background: #1e3a1e;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #4CAF50;
            font-size: 0.9em;
            opacity: 0.8;
        }
        .hidden-message {
            color: #333;
            font-size: 0.8em;
            margin-top: 30px;
            text-align: center;
        }
    </style>

    <script>
        // 禁用右键点击
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            alert('Right click is disabled!');
            return false;
        });

        // 禁用键盘快捷键 (Ctrl+U, F12 等)
        document.addEventListener('keydown', function(e) {
            // Ctrl+U (查看源代码)
            if (e.ctrlKey && e.keyCode === 85) {
                e.preventDefault();
                alert('View source is disabled!');
                return false;
            }
            // F12 (开发者工具)
            if (e.keyCode === 123) {
                e.preventDefault();
                alert('Developer tools are disabled!');
                return false;
            }
            // Ctrl+Shift+I (开发者工具)
            if (e.ctrlKey && e.shiftKey && e.keyCode === 73) {
                e.preventDefault();
                alert('Developer tools are disabled!');
                return false;
            }
        });

        // 禁用文字选择
        document.addEventListener('selectstart', function(e) {
            e.preventDefault();
            return false;
        });

        // 页面加载完成后的消息
        window.onload = function() {
            console.log('Natas Level 1 loaded. Right-click is disabled.');
            console.log('Try to bypass the restrictions to find the password.');
        };
    </script>
</head>
<body>
    <div class="container">
        <h1>🛡️ Natas Level 1</h1>

        <div class="warning">
            ⚠️ SECURITY RESTRICTIONS ACTIVE ⚠️<br>
            Right-click and developer tools are disabled on this page.
        </div>

        <div class="content">
            <p>Welcome to Natas Level 1. This level has some client-side restrictions.</p>
            <p><strong>Goal:</strong> Find the password for the next level despite the restrictions.</p>
            <p><strong>Hint:</strong> Client-side restrictions can often be bypassed.</p>

            <div class="hint-box">
                <h3>💡 How to bypass restrictions:</h3>
                <ul>
                    <li>Use browser menu: View → Page Source</li>
                    <li>Use keyboard shortcut that isn't blocked</li>
                    <li>Use command line tools like curl</li>
                    <li>Disable JavaScript in your browser</li>
                </ul>

                <code>curl -u natas1:gtVrDuiDfck831PqWsLEZy5gyDz1clto http://localhost:8081/natas1/</code>
            </div>

            <!-- The password for natas2 is ZluruAthQk7Q2MqmDeTiUij2ZvWy2mBi -->

            <div class="bypass-tips">
                <strong>Security Lesson:</strong> Client-side restrictions are never secure.
                Always validate on the server side. This page blocks right-click and some
                keyboard shortcuts, but there are many ways to view the source code.
            </div>

            <div class="auth-info">
                <p><strong>Authentication Info:</strong></p>
                <p>Username: natas1</p>
                <p>Password: gtVrDuiDfck831PqWsLEZy5gyDz1clto (from Natas Level 0)</p>
            </div>
        </div>

        <div class="hidden-message">
            <!-- Debug: This would normally be hidden better -->
            <!-- The actual password is in the comment above -->
        </div>
    </div>

    <script>
        // 额外的保护（可绕过）
        document.onkeypress = function(e) {
            // 阻止 Ctrl+S 等
            if (e.ctrlKey) {
                e.preventDefault();
                return false;
            }
        };
    </script>
</body>
</html>
HTML_EOF

# 创建 nginx 配置
RUN cat > /etc/nginx/conf.d/natas.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name localhost;

    location /natas1/ {
        root /usr/share/nginx/html;
        index index.html;

        # 基础认证
        auth_basic "Natas Level 1";
        auth_basic_user_file /etc/nginx/.htpasswd;

        # 禁止目录列表
        autoindex off;
    }

    # 重定向根路径
    location = / {
        return 302 /natas1/;
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
        echo "访问地址: http://localhost:$HTTP_PORT/natas1/"
        echo "认证信息:"
        echo "  用户名: natas1"
        echo "  密码: gtVrDuiDfck831PqWsLEZy5gyDz1clto (Natas Level 0 的标志)"
        echo "  标志: 在页面源代码的注释中（右键点击被禁用）"
        echo "  下一关密码: ZluruAthQk7Q2MqmDeTiUij2ZvWy2mBi"
        echo ""
        echo "测试命令（绕过限制）:"
        echo "  curl -u natas1:gtVrDuiDfck831PqWsLEZy5gyDz1clto http://localhost:$HTTP_PORT/natas1/"
        echo "  curl -s -u natas1:gtVrDuiDfck831PqWsLEZy5gyDz1clto http://localhost:$HTTP_PORT/natas1/ | grep 'The password for natas2 is'"

        # 测试认证
        echo -n "测试认证..."
        if curl -s -u natas1:gtVrDuiDfck831PqWsLEZy5gyDz1clto "http://localhost:$HTTP_PORT/natas1/" | grep -q "Natas Level 1"; then
            echo "成功"
            echo "注意: 页面有 JavaScript 限制，但 curl 可以绕过"
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