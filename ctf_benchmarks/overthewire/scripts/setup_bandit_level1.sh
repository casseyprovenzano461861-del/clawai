#!/bin/bash
# OverTheWire Bandit Level 1 设置脚本
# 设置包含特殊文件名 "-" 的 SSH 服务器

set -e

echo "正在设置 OverTheWire Bandit Level 1 挑战环境..."

# Docker 检查
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    exit 1
fi

IMAGE_NAME="clawai/overthewire-bandit-level1:latest"
CONTAINER_NAME="overthewire-bandit-level1"
SSH_PORT=2221

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

# 创建 bandit1 用户
RUN adduser -D -s /bin/bash bandit1 \
    && echo "bandit1:CV1DtqXWVFXTvM2F0k09SHz0YwRINYA9" | chpasswd

# 设置挑战文件 - 创建名为 "-" 的文件
RUN mkdir -p /home/bandit1 \
    && echo "CV1DtqXWVFXTvM2F0k09SHz0YwRINYA1" > /home/bandit1/- \
    && chown -R bandit1:bandit1 /home/bandit1 \
    && chmod 644 /home/bandit1/-

# 修复文件权限（确保文件可读）
RUN ls -la /home/bandit1/

# 设置欢迎消息
RUN echo 'echo "Welcome to OverTheWire Bandit Level 1!"' >> /home/bandit1/.bashrc \
    && echo 'echo ""' >> /home/bandit1/.bashrc \
    && echo 'echo "The password for the next level is stored in a file called -" >> /home/bandit1/.bashrc \
    && echo 'echo "in the home directory. The file name has a dash in it."' >> /home/bandit1/.bashrc \
    && echo 'echo ""' >> /home/bandit1/.bashrc \
    && echo 'echo "Hint: How do you read a file named -?"' >> /home/bandit1/.bashrc \
    && echo 'echo "Try: cat ./-  or  cat -- -  or  cat /home/bandit1/-"' >> /home/bandit1/.bashrc \
    && echo 'cd /home/bandit1' >> /home/bandit1/.bashrc

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
        echo "  用户名: bandit1"
        echo "  密码: boJ9jbbUNNfktd78OOpsqOltutMc3MY1 (上一关的标志)"
        echo "  标志文件: /home/bandit1/- (特殊文件名)"
        echo "  标志内容: CV1DtqXWVFXTvM2F0k09SHz0YwRINYA1"
        echo ""
        echo "连接命令: ssh -p $SSH_PORT bandit1@localhost"
        echo "读取标志: ssh -p $SSH_PORT bandit1@localhost 'cat ./-'"

        # 测试连接
        echo -n "测试连接..."
        if sshpass -p boJ9jbbUNNfktd78OOpsqOltutMc3MY1 ssh -p "$SSH_PORT" \
                   -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
                   bandit1@localhost "ls -la" 2>/dev/null | grep -q -- "-"; then
            echo "成功，特殊文件存在"
        else
            echo "连接测试失败，但端口已监听"
        fi

        exit 0
    fi
    sleep 1
done

echo "✗ SSH 服务启动超时"
docker logs "$CONTAINER_NAME"
exit 1