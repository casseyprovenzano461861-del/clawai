#!/bin/bash
# OverTheWire Bandit Level 0 设置脚本
# 设置 SSH 服务器和挑战环境

set -e

echo "正在设置 OverTheWire Bandit Level 0 挑战环境..."

# Docker 检查
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

IMAGE_NAME="clawai/overthewire-bandit-level0:latest"
CONTAINER_NAME="overthewire-bandit-level0"
SSH_PORT=2220

# 检查镜像
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "构建 Docker 镜像: $IMAGE_NAME"

    BUILD_DIR=$(mktemp -d)
    trap "rm -rf $BUILD_DIR" EXIT

    # Dockerfile
    cat > "$BUILD_DIR/Dockerfile" << 'EOF'
FROM alpine:latest

# 安装 SSH 服务器和必要工具
RUN apk add --no-cache \
    openssh \
    openssh-server-pam \
    openssh-server \
    openssh-client \
    bash \
    shadow \
    && rm -rf /var/cache/apk/*

# 配置 SSH
RUN mkdir -p /var/run/sshd \
    && ssh-keygen -A \
    && echo "PermitRootLogin no" >> /etc/ssh/sshd_config \
    && echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config \
    && echo "PermitEmptyPasswords no" >> /etc/ssh/sshd_config \
    && echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config

# 创建 bandit0 用户
RUN adduser -D -s /bin/bash bandit0 \
    && echo "bandit0:bandit0" | chpasswd

# 设置挑战文件
RUN mkdir -p /home/bandit0 \
    && echo "boJ9jbbUNNfktd78OOpsqOltutMc3MY1" > /home/bandit0/readme \
    && chown -R bandit0:bandit0 /home/bandit0 \
    && chmod 644 /home/bandit0/readme

# 设置欢迎消息
RUN echo 'echo "Welcome to OverTheWire Bandit Level 0!"' >> /home/bandit0/.bashrc \
    && echo 'echo "The password for this level is stored in a file called readme."' >> /home/bandit0/.bashrc \
    && echo 'echo "Good luck!"' >> /home/bandit0/.bashrc \
    && echo 'cd /home/bandit0' >> /home/bandit0/.bashrc

# 暴露 SSH 端口
EXPOSE 22

# 启动 SSH 服务
CMD ["/usr/sbin/sshd", "-D", "-e"]
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
        -p "$SSH_PORT:22" \
        --restart unless-stopped \
        --memory 256m \
        --cpus 0.5 \
        "$IMAGE_NAME"
fi

# 等待 SSH 服务启动
echo "等待 SSH 服务启动..."
for i in {1..30}; do
    if nc -z localhost "$SSH_PORT" 2>/dev/null; then
        echo "✓ SSH 服务已就绪"
        echo "SSH 连接信息:"
        echo "  主机: localhost"
        echo "  端口: $SSH_PORT"
        echo "  用户名: bandit0"
        echo "  密码: bandit0"
        echo "  标志文件: /home/bandit0/readme"
        echo "  标志内容: boJ9jbbUNNfktd78OOpsqOltutMc3MY1"
        echo ""
        echo "连接命令: ssh -p $SSH_PORT bandit0@localhost"
        echo "测试命令: ssh -p $SSH_PORT bandit0@localhost 'cat readme'"

        # 测试连接
        echo -n "测试连接..."
        if sshpass -p bandit0 ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no \
                   -o ConnectTimeout=5 bandit0@localhost "echo connected" 2>/dev/null | grep -q "connected"; then
            echo "成功"
        else
            echo "失败（但端口已监听）"
        fi

        exit 0
    fi
    sleep 1
done

echo "✗ SSH 服务启动超时"
docker logs "$CONTAINER_NAME"
exit 1