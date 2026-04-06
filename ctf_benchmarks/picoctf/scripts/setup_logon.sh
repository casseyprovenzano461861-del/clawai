#!/bin/bash
# PicoCTF Logon 挑战设置脚本
# 会话管理和认证绕过挑战

set -e

echo "正在设置 PicoCTF Logon 挑战环境..."

# Docker 检查
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

IMAGE_NAME="clawai/picoctf-logon:2019"
CONTAINER_NAME="picoctf-logon-2019"
PORT=8003

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

# 暴露端口
EXPOSE 80

# 运行应用
CMD ["python", "app.py"]
EOF

    # Flask 应用
    cat > "$BUILD_DIR/app.py" << 'EOF'
from flask import Flask, request, make_response, render_template_string
import os

app = Flask(__name__)

# 实际的管理员凭证（不在前端显示）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "super_secret_admin_password_123"
FLAG = "picoCTF{th3_c0nsp1r4cy_l1v3s_0d98e4b9}"

# 登录页面 HTML
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Company Portal Login</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 400px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #45a049;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #ffcdd2;
        }
        .info {
            background: #e3f2fd;
            color: #1565c0;
            padding: 12px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 14px;
            text-align: center;
            border: 1px solid #bbdefb;
        }
        .cookie-warning {
            background: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 13px;
            border: 1px solid #ffeaa7;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔒 Company Portal Login</h1>

        {% if error %}
        <div class="error">
            {{ error }}
        </div>
        {% endif %}

        <form method="POST" action="/logon">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username"
                       placeholder="Enter username" required>
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password"
                       placeholder="Enter password" required>
            </div>

            <button type="submit">Login</button>
        </form>

        <div class="info">
            <p>Welcome to the company portal. Please login with your credentials.</p>
            <p>Try common defaults like admin/admin</p>
        </div>

        <div class="cookie-warning">
            <strong>Note:</strong> This portal uses cookies for session management.
            Check your browser's developer tools for cookie details.
        </div>
    </div>
</body>
</html>
'''

# 标志页面 HTML
FLAG_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - Flag</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #00ff00;
            margin: 0;
            padding: 40px;
            text-align: center;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            background: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
            border: 2px solid #00ff00;
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.3);
        }
        h1 {
            color: #00ff00;
            font-size: 36px;
            margin-bottom: 30px;
            text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
        }
        .flag {
            background: #002200;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #00ff00;
            font-size: 24px;
            font-weight: bold;
            margin: 30px 0;
            letter-spacing: 2px;
            text-shadow: 0 0 10px rgba(0, 255, 0, 0.7);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 10px rgba(0, 255, 0, 0.3); }
            50% { box-shadow: 0 0 30px rgba(0, 255, 0, 0.7); }
            100% { box-shadow: 0 0 10px rgba(0, 255, 0, 0.3); }
        }
        .message {
            color: #66ff66;
            margin-bottom: 30px;
            font-size: 18px;
        }
        .access-granted {
            color: #00ff00;
            font-size: 48px;
            margin-bottom: 20px;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .cookie-info {
            background: #003300;
            padding: 15px;
            border-radius: 8px;
            margin-top: 30px;
            font-size: 14px;
            text-align: left;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="access-granted">⚡ ACCESS GRANTED ⚡</div>
        <h1>Administrator Panel</h1>

        <div class="message">
            Welcome, Administrator! You have successfully bypassed the login system.
        </div>

        <div class="flag">
            {{ flag }}
        </div>

        <div class="cookie-info">
            <strong>Cookie Analysis:</strong><br>
            • The system sets a cookie named "admin" on login attempts<br>
            • Default value is "False" for regular users<br>
            • Changing it to "True" grants administrative access<br>
            • This demonstrates insecure session management
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def redirect_to_login():
    return '''
    <html>
        <head><meta http-equiv="refresh" content="0; url=/logon"></head>
        <body>Redirecting to login...</body>
    </html>
    '''

@app.route('/logon', methods=['GET', 'POST'])
def logon():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # 创建响应
        resp = make_response(render_template_string(LOGIN_PAGE,
            error="Invalid credentials! But we set a cookie for you..."))

        # 总是设置 admin cookie，但值为 False（除非是真正的管理员）
        admin_value = "True" if (username == ADMIN_USERNAME and password == ADMIN_PASSWORD) else "False"
        resp.set_cookie('admin', admin_value, httponly=False)

        return resp

    return render_template_string(LOGIN_PAGE)

@app.route('/flag')
def flag():
    # 检查 admin cookie
    admin_cookie = request.cookies.get('admin', 'False')

    if admin_cookie == "True":
        return render_template_string(FLAG_PAGE, flag=FLAG)
    else:
        return '''
        <html>
            <head><title>Access Denied</title></head>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1 style="color: #c00;">⛔ Access Denied</h1>
                <p>You do not have administrator privileges.</p>
                <p>Current admin cookie value: <strong>''' + admin_cookie + '''</strong></p>
                <p>Try modifying your cookies to gain access.</p>
                <p><a href="/logon">Return to login</a></p>
            </body>
        </html>
        ''', 403

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
    if curl -s "http://localhost:$PORT/logon" > /dev/null 2>&1; then
        echo "✓ 挑战环境已就绪"
        echo "访问地址: http://localhost:$PORT/logon"
        echo "尝试使用任何凭证登录，检查设置的 cookie"
        echo "修改 admin cookie 从 'False' 到 'True' 访问 /flag"
        echo "完整标志: picoCTF{th3_c0nsp1r4cy_l1v3s_0d98e4b9}"
        exit 0
    fi
    sleep 1
done

echo "✗ 启动超时"
docker logs "$CONTAINER_NAME"
exit 1