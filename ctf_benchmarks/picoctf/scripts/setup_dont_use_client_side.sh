#!/bin/bash
# PicoCTF Don't Use Client Side 挑战设置脚本
# 客户端密码验证挑战

set -e

echo "正在设置 PicoCTF Don't Use Client Side 挑战环境..."

# Docker 检查
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

IMAGE_NAME="clawai/picoctf-dont-use-client-side:2019"
CONTAINER_NAME="picoctf-dont-use-client-side-2019"
PORT=8002

# 检查镜像
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "构建 Docker 镜像: $IMAGE_NAME"

    BUILD_DIR=$(mktemp -d)
    trap "rm -rf $BUILD_DIR" EXIT

    # Dockerfile
    cat > "$BUILD_DIR/Dockerfile" << 'EOF'
FROM python:3.9-alpine

# 安装依赖
RUN pip install flask

# 创建应用目录
WORKDIR /app

# 复制应用文件
COPY app.py .
COPY templates/ ./templates/

# 暴露端口
EXPOSE 80

# 运行应用
CMD ["python", "app.py"]
EOF

    # 创建 templates 目录
    mkdir -p "$BUILD_DIR/templates"

    # Flask 应用
    cat > "$BUILD_DIR/app.py" << 'EOF'
from flask import Flask, request, render_template_string, make_response
import os

app = Flask(__name__)

# 正确的密码（隐藏在客户端 JavaScript 中）
CORRECT_PASSWORD = "GquH2wDujm2fXKqK"
FLAG = "picoCTF{no_clients_plz_b7cacb18}"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Don't Use Client Side</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0d1117;
            color: #c9d1d9;
            max-width: 800px;
            margin: 100px auto;
            padding: 20px;
        }
        .container {
            background: #161b22;
            padding: 40px;
            border-radius: 10px;
            border: 1px solid #30363d;
        }
        h1 {
            color: #58a6ff;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }
        .form-group {
            margin: 20px 0;
        }
        input[type="password"] {
            width: 100%;
            padding: 12px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #c9d1d9;
            font-size: 16px;
            font-family: 'Courier New', monospace;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            font-family: 'Courier New', monospace;
        }
        button:hover {
            background: #2ea043;
        }
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            font-weight: bold;
        }
        .success {
            background: #13233a;
            border: 1px solid #1f6feb;
            color: #58a6ff;
        }
        .error {
            background: #2d1919;
            border: 1px solid #f85149;
            color: #f85149;
        }
        .hint {
            margin-top: 30px;
            padding: 15px;
            background: #1c2128;
            border-left: 4px solid #d29922;
            border-radius: 0 6px 6px 0;
            font-size: 0.9em;
        }
        code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 4px;
            color: #ff7b72;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Don't Use Client Side</h1>

        <p>Can you bypass this client-side validation?</p>

        <form id="passwordForm" method="POST">
            <div class="form-group">
                <input type="password" id="password" name="password"
                       placeholder="Enter the password..." autocomplete="off">
            </div>
            <button type="submit" onclick="return verify()">Submit Password</button>
        </form>

        {% if message %}
        <div class="message {{ 'success' if success else 'error' }}">
            {{ message }}
        </div>
        {% endif %}

        <div class="hint">
            <strong>Hint:</strong> The challenge name is a hint. Don't rely on the client side.
            Check the page source and JavaScript code.
        </div>
    </div>

    <script>
        // Client-side password validation (INSECURE!)
        function verify() {
            var pass = document.getElementById("password").value;
            var passArr = pass.split("");

            // Password is split and compared in pieces
            // This is terrible security practice!
            if (passArr[0] == 'G' && passArr[1] == 'q' && passArr[2] == 'u') {
                if (pass.substring(0, 3) == 'Gqu') {
                    if (pass.substring(0, 4) == 'GquH') {
                        if (pass.substring(0, 5) == 'GquH2') {
                            if (pass.substring(0, 6) == 'GquH2w') {
                                if (pass.substring(0, 8) == 'GquH2wDu') {
                                    if (pass.substring(0, 10) == 'GquH2wDujm') {
                                        if (pass.substring(0, 12) == 'GquH2wDujm2f') {
                                            if (pass.substring(0, 14) == 'GquH2wDujm2fXK') {
                                                if (pass.substring(0, 16) == 'GquH2wDujm2fXKqK') {
                                                    return true; // Password seems correct
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            alert("Invalid password! Check the JavaScript code for clues.");
            return false;
        }

        // Debug function (exposed in console)
        window.getPasswordHint = function() {
            console.log("Password fragments: ['Gq', 'Gqu', 'GquH', 'GquH2', 'GquH2w', 'GquH2wDu', 'GquH2wDujm', 'GquH2wDujm2f', 'GquH2wDujm2fXK', 'GquH2wDujm2fXKqK']");
            console.log("Combine them to get the full password!");
        };

        // Call hint function on page load (for debugging)
        console.log("Don't Use Client Side Challenge loaded");
        console.log("Type 'getPasswordHint()' in console for help");
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    success = False

    if request.method == 'POST':
        password = request.form.get('password', '')

        if password == CORRECT_PASSWORD:
            message = f"🎉 Correct! Flag: {FLAG}"
            success = True
        else:
            message = "❌ Incorrect password. Check the JavaScript code!"

    return render_template_string(HTML_TEMPLATE, message=message, success=success)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
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
        -p "$PORT:80" \
        --restart unless-stopped \
        --memory 256m \
        --cpus 0.5 \
        "$IMAGE_NAME"
fi

# 等待就绪
echo "等待服务启动..."
for i in {1..30}; do
    if curl -s "http://localhost:$PORT/" > /dev/null 2>&1; then
        echo "✓ 挑战环境已就绪"
        echo "访问地址: http://localhost:$PORT/"
        echo "密码隐藏在 JavaScript 验证逻辑中: GquH2wDujm2fXKqK"
        echo "完整标志: picoCTF{no_clients_plz_b7cacb18}"
        exit 0
    fi
    sleep 1
done

echo "✗ 启动超时"
docker logs "$CONTAINER_NAME"
exit 1