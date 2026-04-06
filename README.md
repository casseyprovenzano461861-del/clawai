# ClawAI - 智能安全评估系统

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

ClawAI是一个基于AI的智能安全评估系统，集成了渗透测试工具、AI分析和知识图谱技术，为安全团队提供自动化的漏洞发现、风险评估和修复建议。

## 🚀 核心功能

- **智能渗透测试**：AI驱动的漏洞扫描和攻击模拟
- **工具集成**：集成Nmap、Nikto等主流安全工具
- **知识图谱**：基于Neo4j构建的攻击路径分析
- **实时监控**：WebSocket实时推送扫描结果
- **自动化报告**：自动生成详细的安全评估报告
- **模块化架构**：支持插件化扩展和安全工具集成
- **多租户支持**：基于RBAC的角色权限管理

## 📋 系统架构

```
ClawAI (模块化单体架构)
├── 前端 (Vite + TailwindCSS)
├── API网关 (FastAPI)
├── AI引擎 (LLM集成)
├── 数据服务 (SQLite/PostgreSQL + Neo4j)
├── 工具执行器 (安全工具封装)
└── 监控服务 (Prometheus + 审计日志)
```

## 🛠️ 快速开始

### 环境要求

- Python 3.11+
- Docker 24.0+ (可选，推荐)
- Node.js 18+ (前端开发)
- Neo4j 5.26+ (知识图谱)

### 本地开发部署

1. **克隆项目**
   ```bash
   git clone https://github.com/your-org/claw-ai.git
   cd claw-ai
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate     # Windows
   ```

3. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置必要的配置
   ```

5. **初始化数据库**
   ```bash
   python scripts/init_database.py
   ```

6. **启动后端服务**
   ```bash
   python run.py
   ```

7. **启动前端开发服务器** (另一个终端)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

8. **访问应用**
   - 前端界面: http://localhost:5173
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

### Docker部署

使用Docker Compose快速启动完整环境：

```bash
# 复制环境变量模板
cp .env.example .env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 默认端口映射
- **应用**: http://localhost:8000
- **Neo4j浏览器**: http://localhost:7474 (用户名: neo4j, 密码: password)
- **前端界面**: http://localhost:5173

## 🔧 配置说明

### 主要配置文件

- `.env` - 主环境变量配置文件
- `config/modules.yaml` - 模块配置
- `config/rbac.json` - 角色权限配置
- `docker-compose.yml` - Docker服务配置

### 关键环境变量

```bash
# 数据库配置
DATABASE_URL=sqlite:///data/databases/clawai.db
# 或 PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/clawai

# Neo4j图数据库
NEO4J_AUTH=neo4j/password
NEO4J_URL=bolt://localhost:7687

# JWT认证
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI配置 (可选)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# 工具配置
TOOLS_DIR=/app/tools/penetration
```

## 📖 API文档

启动服务后访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 主要API端点

- `GET /health` - 健康检查
- `GET /tools` - 可用工具列表
- `POST /scans` - 创建安全扫描
- `GET /scans/{scan_id}` - 获取扫描结果
- `GET /knowledge/nodes` - 知识图谱节点查询
- `POST /auth/login` - 用户登录
- `GET /users/me` - 获取当前用户信息

## 🧪 测试

### 运行测试套件

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行所有测试
pytest

# 运行特定测试模块
pytest tests/unit/
pytest tests/integration/

# 运行带覆盖率
pytest --cov=src tests/

# 运行前端测试
cd frontend
npm test
```

### 测试覆盖率报告

```bash
pytest --cov=src --cov-report=html tests/
# 打开 htmlcov/index.html 查看覆盖率报告
```

## 🗂️ 项目结构

```
claw-ai/
├── src/                    # Python源代码
│   ├── ai_engine/         # AI引擎模块
│   ├── api_gateway/       # API网关
│   ├── data_service/      # 数据服务
│   ├── modules/           # 功能模块
│   ├── monitoring/        # 监控服务
│   └── shared/            # 共享代码
├── frontend/              # 前端应用
│   ├── src/              # Vue/React组件
│   ├── public/           # 静态资源
│   └── package.json      # 前端依赖
├── tools/                # 安全工具封装
├── config/               # 配置文件
├── data/                 # 数据存储
│   ├── databases/       # 数据库文件
│   ├── audit/           # 审计日志
│   └── reports/         # 生成报告
├── tests/               # 测试代码
├── scripts/             # 实用脚本
├── docker/              # Docker构建文件
├── docs/                # 项目文档
└── external_tools/      # 外部工具集成
```

## 🔐 安全特性

- **RBAC权限控制**：基于角色的访问控制
- **JWT认证**：安全的用户认证机制
- **审计日志**：所有操作记录可追溯
- **输入验证**：全面的请求参数验证
- **CORS配置**：安全的跨域资源共享
- **速率限制**：防止API滥用
- **安全头部**：HTTP安全头部配置

## 📈 监控与日志

### 日志级别配置
```yaml
LOG_LEVEL: INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT: json # 或 text
LOG_FILE: /app/logs/clawai.log
```

### 健康检查端点
```bash
curl http://localhost:8000/health
```

### Prometheus指标
```
http://localhost:8000/metrics
```

## 🤝 贡献指南

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 开发规范
- 遵循PEP 8 Python代码规范
- 为新增功能添加测试用例
- 更新相关文档
- 确保所有测试通过

## 📄 许可证

本项目基于MIT许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与联系

- **问题反馈**: [GitHub Issues](https://github.com/your-org/claw-ai/issues)
- **文档**: [项目文档](docs/)
- **邮件**: support@claw-ai.com

## 🙏 致谢

感谢以下开源项目的贡献：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Neo4j](https://neo4j.com/) - 图数据库
- [Vite](https://vitejs.dev/) - 前端构建工具
- [TailwindCSS](https://tailwindcss.com/) - CSS框架

---

**ClawAI** - 让安全评估更智能、更高效！ 🔒🤖