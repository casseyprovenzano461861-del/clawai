# ClawAI 快速启动指南

## 1. 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.10 | `start.py` 会检查版本 |
| Node.js | LTS 版本 | 前端构建所需 |
| pip | 最新 | Python 包管理 |
| npm | 随 Node.js 安装 | 前端包管理 |

## 2. 安装步骤

### 2.1 克隆项目

```bash
git clone <repo-url>
cd ClawAI
```

### 2.2 配置环境变量

复制 `.env.example` 为 `.env`，并填写必要的配置：

```bash
cp .env.example .env
```

**必须配置的项** — 至少设置一个 LLM API Key，否则 AI 功能无法使用：

```ini
# 选择一个 LLM 提供商
LLM_PROVIDER=deepseek    # 可选: openai | anthropic | deepseek

# 对应的 API Key（至少填一个）
DEEPSEEK_API_KEY=sk-xxx
# OPENAI_API_KEY=sk-xxx
# ANTHROPIC_API_KEY=sk-xxx
```

**其他常用配置**（一般默认即可）：

```ini
ENVIRONMENT=development
DATABASE_URL=sqlite:///./data/databases/clawai.db
SERVER_HOST=0.0.0.0
BACKEND_PORT=8000
JWT_SECRET_KEY=clawai-jwt-secret-key-development   # 生产环境务必修改
TOOLS_DIR=./tools/penetration
```

### 2.3 安装后端依赖

推荐使用虚拟环境：

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

> **注意**：`sentence-transformers` 和 `qdrant-client` 依赖 PyTorch，体积较大。如果不需要 RAG/向量检索功能，可以跳过安装这两个包。

### 2.4 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

## 3. 启动项目

### 方式一：一键启动（推荐）

```bash
python start.py
```

这会同时启动后端和前端。

其他选项：

```bash
python start.py --backend          # 仅启动后端
python start.py --frontend         # 仅启动前端
python start.py --mode dev         # 开发模式（后端热重载）
python start.py --backend-port 8888  # 指定后端端口
```

### 方式二：分别启动

**后端：**

```bash
# 方式 A：通过 run.py
python run.py --host 0.0.0.0 --port 8000 --reload

# 方式 B：直接使用 uvicorn
python -m uvicorn src.shared.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端：**

```bash
cd frontend
npm run dev
```

### 方式三：CLI 模式（无需 Web UI）

```bash
python clawai.py                      # AI 对话模式
python clawai.py chat -t example.com  # 指定目标的对话
python clawai.py scan 192.168.1.1     # 快速扫描
python clawai.py tools list           # 查看可用工具
```

## 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | React Web UI |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 服务状态 |

## 5. 可选服务

以下服务非必须，但启用后可解锁更多功能：

### 5.1 Redis（缓存/消息队列）

```bash
docker-compose up -d redis
```

### 5.2 Qdrant（RAG 向量检索）

```bash
docker-compose up -d qdrant
```

### 5.3 完整 Docker 部署

```bash
# 启动所有辅助服务（Qdrant + Redis）
docker-compose up -d

# 含监控栈（Prometheus + Grafana）
docker-compose --profile monitoring up -d

# 完整应用容器化部署
cd docker
docker-compose up -d
```

## 6. 已知问题

### 端口不一致

Vite 开发服务器默认代理到 `localhost:8888`，但后端默认启动在 `8000` 端口。解决方案（二选一）：

1. 启动时指定端口：`python start.py --backend-port 8888`
2. 修改 `frontend/vite.config.js` 中的 proxy target 为 `http://localhost:8000`

## 7. 配置文件说明

| 文件 | 用途 |
|------|------|
| `.env` | 主配置文件（API Key、端口、数据库等） |
| `config/modules.yaml` | 模块启用与参数配置 |
| `config/rbac.json` | 角色权限控制（admin/analyst/user/guest/auditor） |
| `config/tool_paths.yaml` | 安全工具路径映射 |
| `config/tools_extended.json` | 扩展工具配置 |

## 8. 故障排除

| 问题 | 解决方案 |
|------|---------|
| 启动失败 / 端口占用 | 修改 `BACKEND_PORT` 或停止占用端口的进程 |
| 数据库连接失败 | 检查 `DATABASE_URL`，确保 `data/databases/` 目录可写 |
| 工具执行失败 | 检查 `TOOLS_DIR` 配置，确保工具已安装且有执行权限 |
| 前端 API 调用 404 | 检查 Vite proxy 端口是否与后端一致（见第 6 节） |
| AI 功能无响应 | 确认 `.env` 中已配置有效的 LLM API Key |

**日志位置**：
- 应用日志：`logs/clawai.log`
- 审计日志：`data/audit/`
- API 文档：http://localhost:8000/docs

---

**文档版本**: 2.1.0
**最后更新**: 2026-04-08
