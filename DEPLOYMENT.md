# ClawAI 部署指南 (模块化单体架构)

## 📋 概述

本文档提供 ClawAI 模块化单体应用的部署指南。经过 P0 阶段架构简化，ClawAI 已从复杂的微服务架构重构为模块化单体应用，部署和运维更加简单。

### 版本信息

- **版本**: 2.0.0 (模块化单体架构)
- **架构**: 模块化单体 (Single Monolith with Modular Design)
- **部署方式**: Docker / 直接运行
- **最低要求**: Python 3.11+, 4GB RAM, 10GB 磁盘空间

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ClawAI

# 创建Python虚拟环境 (推荐)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置应用

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置必要的环境变量
# 至少修改以下安全密钥:
# JWT_SECRET_KEY, SECRET_KEY
# 以及AI API密钥（如果需要AI功能）
```

### 3. 初始化配置

```bash
# 创建必要的目录
mkdir -p data/databases data/audit logs config tools/penetration

# 检查模块配置文件
ls config/modules.yaml

# 如果不存在，会自动生成默认配置
```

### 4. 启动应用

```bash
# 开发模式 (热重载)
python run.py --reload

# 生产模式
python run.py --host 0.0.0.0 --port 8000
```

应用启动后访问:
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 工具列表: http://localhost:8000/tools

## 🐳 Docker 部署

### 1. 使用 Docker Compose (推荐)

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，配置必要的环境变量

# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f clawai
```

### 2. 直接使用 Docker

```bash
# 构建镜像
docker build -t clawai:2.0.0 .

# 运行容器
docker run -d \
  --name clawai \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config:ro \
  --env-file .env \
  clawai:2.0.0
```

### 3. Docker Compose 环境变量

创建 `.env` 文件，包含以下关键配置:

```bash
# 基础配置
ENVIRONMENT=production
LOG_LEVEL=INFO

# 安全配置 (必须修改!)
JWT_SECRET_KEY=your-secure-jwt-secret-key
SECRET_KEY=your-secure-app-secret-key

# AI配置 (可选)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...

# 数据库配置
DATABASE_URL=sqlite:////app/data/databases/clawai.db

# 工具配置
TOOLS_DIR=/app/tools/penetration
```

## 🔧 配置详解

### 1. 模块配置 (`config/modules.yaml`)

控制应用加载哪些模块及其配置:

```yaml
modules:
  ai_engine:
    enabled: true
    config:
      llm_provider: "openai"
      default_model: "gpt-4"
      
  data_service:
    enabled: true
    config:
      database_url: "sqlite:///./data/databases/clawai.db"
      
  tool_executor:
    enabled: true
    config:
      tools_dir: "./tools/penetration"
      
routing:
  prefixes:
    ai_engine: "/api/v1/ai"
    data_service: "/api/v1/data"
    tool_executor: "/api/v1/tools"
```

### 2. RBAC 配置 (`config/rbac.json`)

基于角色的访问控制配置，应用启动时自动创建默认配置。

### 3. 环境变量

关键环境变量说明:

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENVIRONMENT` | 运行环境 | `development` |
| `SERVER_HOST` | 服务器地址 | `0.0.0.0` |
| `BACKEND_PORT` | 服务器端口 | `8000` |
| `DATABASE_URL` | 数据库URL | `sqlite:///./data/databases/clawai.db` |
| `TOOLS_DIR` | 安全工具目录 | `./tools/penetration` |
| `JWT_SECRET_KEY` | JWT密钥 | 必须修改 |
| `SECRET_KEY` | 应用密钥 | 必须修改 |
| `MODULES_CONFIG_PATH` | 模块配置文件路径 | `./config/modules.yaml` |
| `RBAC_CONFIG_PATH` | RBAC配置文件路径 | `./config/rbac.json` |
| `AUDIT_STORAGE_DIR` | 审计日志目录 | `./data/audit` |

## 📊 应用架构

### 模块化设计

ClawAI 2.0.0 采用模块化单体架构:

```
ClawAI 应用 (FastAPI)
├── 核心模块
│   ├── 认证和授权 (RBAC)
│   ├── 配置管理
│   ├── 错误处理和日志
│   └── 审计系统
├── 功能模块
│   ├── AI引擎模块 (/api/v1/ai/*)
│   ├── 数据服务模块 (/api/v1/data/*)
│   └── 工具执行模块 (/api/v1/tools/*)
└── 公共组件
    ├── 数据库管理
    ├── 安全沙箱
    └── 监控指标
```

### API 端点

- **核心API**:
  - `GET /` - 应用信息
  - `GET /health` - 健康检查
  - `GET /tools` - 工具列表
  - `POST /attack` - 执行攻击
  - `POST /tools/execute` - 执行工具

- **AI引擎模块** (`/api/v1/ai/*`):
  - `GET /configs` - AI配置列表
  - `POST /analyze` - 分析目标
  - `POST /generate-plan` - 生成攻击计划
  - `GET /skills` - 技能列表

- **数据服务模块** (`/api/v1/data/*`):
  - `POST /users/register` - 用户注册
  - `POST /users/login` - 用户登录
  - `POST /projects` - 创建项目
  - `GET /projects/{id}` - 获取项目

- **工具执行模块** (`/api/v1/tools/*`):
  - `GET /available` - 可用工具列表
  - `POST /execute` - 执行工具
  - `GET /tasks/{id}` - 任务状态

## 🔒 安全配置

### 1. 生产环境安全清单

- [ ] 修改所有默认密钥 (`JWT_SECRET_KEY`, `SECRET_KEY`)
- [ ] 配置合适的日志级别 (`LOG_LEVEL=INFO` 或 `WARNING`)
- [ ] 限制跨域来源 (`ALLOWED_ORIGINS`)
- [ ] 启用审计日志 (`ENABLE_AUDIT_LOGGING=true`)
- [ ] 配置RBAC权限
- [ ] 使用HTTPS (反向代理)

### 2. 网络安全

```nginx
# Nginx 反向代理配置示例
server {
    listen 443 ssl;
    server_name clawai.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📈 监控和维护

### 1. 健康检查

```bash
# 应用健康检查
curl http://localhost:8000/health

# 模块健康检查
curl http://localhost:8000/api/v1/ai/health
curl http://localhost:8000/api/v1/data/health
curl http://localhost:8000/api/v1/tools/health
```

### 2. 日志管理

日志文件位置:
- 应用日志: `logs/clawai.log`
- 审计日志: `data/audit/` (按日期组织)
- Docker日志: `docker-compose logs -f clawai`

### 3. 性能监控

内置监控端点:
- `GET /metrics` - Prometheus指标
- 使用 `prometheus-client` 收集应用指标

## 🔄 升级指南

### 从旧版本升级

1. **备份数据**:
   ```bash
   # 备份数据库
   cp data/databases/clawai.db data/databases/clawai.db.backup
   
   # 备份配置
   cp -r config config.backup
   cp .env .env.backup
   ```

2. **更新代码**:
   ```bash
   git pull origin main
   ```

3. **更新依赖**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **迁移配置**:
   - 更新 `.env` 文件中的环境变量
   - 检查 `config/modules.yaml` 配置
   - 运行配置验证

5. **重启应用**:
   ```bash
   docker-compose down && docker-compose up -d
   # 或
   pkill -f "python run.py" && python run.py
   ```

## 🐛 故障排除

### 常见问题

1. **应用启动失败**
   ```
   问题: 端口被占用
   解决: 修改 BACKEND_PORT 或停止占用端口的进程
   
   问题: 数据库连接失败
   解决: 检查 DATABASE_URL 配置，确保数据库目录可写
   ```

2. **模块未加载**
   ```
   问题: 模块路由不存在
   解决: 检查 config/modules.yaml，确保模块 enabled: true
   
   问题: 导入错误
   解决: 检查 Python 路径和依赖安装
   ```

3. **工具执行失败**
   ```
   问题: 工具未找到
   解决: 检查 TOOLS_DIR 配置，确保工具目录存在
   
   问题: 权限不足
   解决: Docker 容器需要适当的权限或卷挂载
   ```

### 获取帮助

- 查看应用日志: `logs/clawai.log`
- 检查 Docker 日志: `docker-compose logs -f`
- 访问 API 文档: `http://localhost:8000/docs`
- 查看健康状态: `http://localhost:8000/health`

## 🧠 知识图谱集成

ClawAI 集成了基于 Neo4j 的知识图谱系统，用于可视化展示网络资产、漏洞、攻击路径和防御措施之间的关系。

### Neo4j 图数据库部署

知识图谱使用 Neo4j 图数据库存储数据。有两种部署方式：

#### 选项1: 使用 Docker Compose（推荐）

项目已包含 Neo4j 服务配置在 `docker-compose.yml` 中：

```bash
# 启动 Neo4j 服务
docker-compose up -d neo4j

# 检查服务状态
docker-compose ps neo4j

# 查看 Neo4j 日志
docker-compose logs -f neo4j
```

Neo4j 服务配置：
- 端口: 7474 (HTTP), 7687 (Bolt)
- 数据卷: `./data/neo4j` (持久化存储)
- 默认凭据: neo4j/password (首次登录后需要修改)
- Web 界面: http://localhost:7474

#### 选项2: 使用现有 Neo4j 实例

如果已有 Neo4j 实例，更新配置文件 `config/config.py`：

```python
# Neo4j 配置
NEO4J_URI = "bolt://localhost:7687"  # 修改为你的 Neo4j 地址
NEO4J_USERNAME = "neo4j"             # 修改为你的用户名
NEO4J_PASSWORD = "your_password"     # 修改为你的密码
NEO4J_DATABASE = "neo4j"             # 数据库名称
```

### 初始化知识图谱

首次使用时，需要初始化数据库和导入示例数据：

```bash
# 方法1: 通过 API 导入模拟数据
curl -X POST "http://localhost:8000/api/v1/knowledge-graph/import/mock"

# 方法2: 使用初始化脚本
python scripts/init_neo4j.py
```

### 知识图谱 API

主要 API 端点：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/knowledge-graph/graph` | GET | 获取完整的图谱数据 |
| `/api/v1/knowledge-graph/nodes` | GET | 获取所有节点 |
| `/api/v1/knowledge-graph/edges` | GET | 获取所有边 |
| `/api/v1/knowledge-graph/stats` | GET | 获取统计信息 |
| `/api/v1/knowledge-graph/attack-paths` | GET | 查找攻击路径 |
| `/api/v1/knowledge-graph/node/{id}/related` | GET | 获取相关节点 |
| `/api/v1/knowledge-graph/import/mock` | POST | 导入模拟数据 |
| `/api/v1/knowledge-graph/import/nmap` | POST | 导入 NMAP 扫描结果 |

### 前端知识图谱可视化

前端使用 React + vis-network 进行可视化：

```bash
# 安装前端依赖（包括 vis-network）
cd frontend
npm install

# 启动前端开发服务器
npm run dev
```

访问知识图谱界面：`http://localhost:5173` (或前端配置的地址)

### 数据导入

#### 导入 NMAP 扫描结果

可以将 NMAP XML 扫描结果导入知识图谱：

```python
import requests

# 上传 NMAP XML 文件
with open('scan.xml', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/v1/knowledge-graph/import/nmap',
        files=files
    )
```

#### 自定义数据导入

创建自定义导入器，继承 `BaseImporter` 类：

```python
from src.shared.backend.graph.importers.base_importer import BaseImporter

class CustomImporter(BaseImporter):
    def validate_data(self, data):
        # 验证数据格式
        return True
    
    def import_data(self, data):
        # 导入数据到 Neo4j
        # 返回导入统计信息
        return {"imported_nodes": 10, "imported_edges": 15}
```

### 故障排除

#### Neo4j 连接问题

1. **连接被拒绝**：
   - 确保 Neo4j 服务正在运行：`docker-compose ps neo4j`
   - 检查防火墙设置，确保端口 7474 和 7687 开放
   - 验证凭据是否正确

2. **认证失败**：
   - 首次登录 Neo4j Web 界面 (http://localhost:7474)，修改默认密码
   - 更新 `config/config.py` 中的密码配置

3. **数据库无数据**：
   - 运行初始化脚本：`python scripts/init_neo4j.py`
   - 通过 API 导入模拟数据

#### 前端可视化问题

1. **vis-network 未加载**：
   - 确保已安装依赖：`npm install vis-network vis-data`
   - 检查浏览器控制台是否有错误

2. **数据不显示**：
   - 检查后端 API 是否返回数据
   - 查看网络请求状态
   - 确保 Neo4j 中有数据

### 性能优化

1. **Neo4j 性能优化**：
   - 创建索引加速查询
   - 定期清理旧数据
   - 调整 Neo4j 内存配置

2. **前端性能优化**：
   - 限制显示的节点数量（默认 500 个）
   - 使用分层加载
   - 启用物理引擎稳定化

## 📝 变更日志

### 2.0.0 (2026-04-06) - 模块化单体架构

**重大变更**:
- ✅ 从微服务重构为模块化单体应用
- ✅ 统一的配置管理系统
- ✅ 完整的审计日志系统
- ✅ 基于角色的访问控制 (RBAC)
- ✅ 简化的 Docker 部署
- ✅ 类型安全的 API (Pydantic)

**向后兼容**:
- 核心 API (`/`, `/health`, `/tools`, `/attack`) 保持兼容
- 环境变量支持旧格式
- 配置文件自动迁移

---

**文档版本**: 2.0.0  
**最后更新**: 2026-04-06  
**维护团队**: ClawAI Development Team