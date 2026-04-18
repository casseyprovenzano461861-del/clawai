# ClawAI — 项目全貌说明

> 这份文档用于向外部 AI（如 GPT）介绍项目，帮助快速理解整个系统的结构、现状与瓶颈。

---

## 一、项目定位

ClawAI 是一个**基于大语言模型（LLM）的自动化渗透测试系统**。目标是：

- 用 AI 代替人工做信息收集 → 漏洞发现 → 漏洞利用 → 报告生成的完整闭环
- 支持真实安全工具（nmap、sqlmap、nuclei 等 30+）与 AI 规划器协同工作
- 既可以在 CTF 靶场使用，也面向企业红队渗透

---

## 二、技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 主语言 |
| FastAPI | 0.104.1 | REST API 服务 |
| SQLAlchemy | 2.0.23 | ORM，SQLite/PostgreSQL |
| OpenAI SDK | latest | LLM 调用（GPT/DeepSeek/Claude） |
| Pydantic | v2 | 数据验证 |
| Redis | - | 缓存/消息队列 |
| Neo4j | - | 攻击链图存储 |
| Textual | - | 终端 TUI 界面 |
| Rich | - | 终端美化输出 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2.0 | UI 框架 |
| Vite | 5.0.10 | 构建工具 |
| TailwindCSS | 3.4.0 | 样式 |
| Three.js | - | 3D 攻击链可视化 |
| vis-network | - | 网络拓扑图 |

### 基础设施
- Docker + docker-compose（开发/生产双套配置）
- Nginx（反向代理、TLS、速率限制）
- GitHub Actions CI/CD（3个工作流）
- Prometheus + Grafana（监控）

---

## 三、目录结构

```
ClawAI/
├── clawai.py                    # 主 CLI 入口（委托给 src/cli/main.py）
├── start.py                     # 统一启动脚本（后端+前端）
├── requirements.txt             # 78 个生产依赖
├── requirements-dev.txt         # 测试依赖（pytest, mypy, bandit 等）
├── pyproject.toml               # 项目配置（pytest、coverage 配置）
├── .env                         # 环境变量（API Keys、数据库配置）
├── .env.development             # 开发环境配置（可提交）
├── .env.production.example      # 生产环境模板
│
├── src/
│   ├── cli/                     # CLI 模块
│   │   ├── main.py              # CLI 命令路由（chat/scan/tools/session/status）
│   │   ├── chat_cli.py          # 对话核心逻辑（意图识别、任务调度）
│   │   ├── session_store.py     # 会话持久化
│   │   ├── tui/
│   │   │   ├── app.py           # Textual TUI 主界面
│   │   │   └── widgets/         # UI 组件（ChatInput, MessageList, StatusBar）
│   │   └── prompts/
│   │       └── chat_system.py   # 对话系统提示词
│   │
│   └── shared/backend/          # 后端核心
│       ├── main.py              # FastAPI 应用入口（路由、中间件注册）
│       │
│       ├── per/                 # ⭐ P-E-R 核心框架（165 KB）
│       │   ├── agent.py         # 智能体主类（PERAgent）
│       │   ├── planner.py       # 规划器（任务分解、子任务图）
│       │   ├── executor.py      # 执行器（工具调用、结果收集）
│       │   ├── reflector.py     # 反思器（结果评估、改进建议）
│       │   └── llm_integration.py # LLM 调用适配层
│       │
│       ├── skills/              # 技能系统（27 个技能）
│       │   ├── core.py          # Skill 类定义、SkillExecutor、OpenAI Function Schema 生成
│       │   ├── registry.py      # SkillRegistry（14 个内置技能）
│       │   ├── extended_skills.py # 扩展技能（13 个，整合自开源项目）
│       │   ├── base_skill.py    # 技能基类
│       │   ├── nmap_skill.py    # Nmap 专用技能
│       │   ├── sql_injection_skill.py
│       │   ├── rce_skill.py
│       │   └── privilege_escalation_skill.py
│       │
│       ├── tools/               # 30+ 安全工具封装
│       │   ├── base_tool.py     # 工具基类（BaseTool, ToolExecutionMode）
│       │   ├── unified_executor_final.py  # 统一执行器（真实/模拟自动切换）
│       │   ├── nmap.py / masscan.py / rustscan.py
│       │   ├── nuclei.py / nikto.py / whatweb.py
│       │   ├── sqlmap.py / xsstrike.py / commix.py
│       │   ├── gobuster.py / ffuf.py / dirsearch.py
│       │   ├── amass.py / subfinder.py / theharvester.py
│       │   ├── hydra.py / hashcat.py / john.py / medusa.py
│       │   ├── metasploit （通过 XMLRPC）
│       │   ├── impacket_tool.py / evil_winrm.py / crackmapexec.py
│       │   └── tool_health_check.py  # 工具可用性检测
│       │
│       ├── ai_core/             # AI 核心模块（20+ 文件）
│       │   ├── llm_orchestrator.py      # LLM 编排（多模型路由）
│       │   ├── multi_model_decision.py  # 多模型决策（成本/能力路由）
│       │   ├── knowledge_engine.py      # 知识引擎
│       │   ├── learning_system.py       # 学习系统（经验积累）
│       │   ├── smart_orchestrator.py    # 智能编排器
│       │   ├── cache_system.py          # 结果缓存
│       │   ├── explanation_system.py    # 决策解释
│       │   └── offline_mode.py          # 离线模式（无 API Key）
│       │
│       ├── llm/                 # LLM 后端抽象层
│       │   ├── base.py          # LLMBackend 抽象基类
│       │   ├── openai_backend.py
│       │   ├── anthropic_backend.py
│       │   ├── ollama_backend.py
│       │   ├── mock_backend.py  # Mock 后端（无 API Key 时）
│       │   └── router.py        # 多后端路由（按能力/成本选择）
│       │
│       ├── workflow/            # 渗透流程
│       │   ├── ai_workflow.py
│       │   ├── penetration_stages.py   # 渗透阶段定义
│       │   ├── attack_chain.py         # 攻击链编排
│       │   ├── decision_points.py      # 决策节点（1700+ 行）
│       │   └── intelligent_path_planner.py
│       │
│       ├── auth/                # 认证与权限
│       │   ├── rbac.py          # RBAC 权限系统
│       │   ├── fastapi_permissions.py
│       │   └── authentication.py
│       │
│       ├── security/            # 安全模块
│       │   ├── input_validation.py  # 输入验证（SQL注入/XSS/命令注入检测）
│       │   ├── rate_limit.py        # API 速率限制（滑动窗口）
│       │   └── sanitize.py
│       │
│       ├── audit/               # 审计日志
│       ├── log/                 # 日志管理（JSON结构化、request_id 追踪）
│       ├── monitoring/          # Prometheus 监控指标
│       ├── schemas/             # Pydantic 数据模型
│       ├── models/              # SQLAlchemy ORM 模型
│       ├── api/v1/              # REST API 路由
│       │   ├── pentest.py / tools.py / auth_fastapi.py
│       │   ├── reports_fastapi.py / rbac.py / plugins.py / skills.py
│       │   └── monitor.py
│       └── core/
│           ├── tool_manager.py  # 工具管理器（1000+ 行）
│           └── events.py        # EventBus 事件系统
│
├── frontend/
│   ├── src/
│   │   ├── components/          # 20+ React 组件
│   │   │   ├── ModernDashboard.jsx
│   │   │   ├── AttackChain3D.jsx       # Three.js 3D 可视化
│   │   │   ├── KnowledgeGraph.jsx      # 知识图谱（vis-network）
│   │   │   ├── ReportGenerator.jsx
│   │   │   ├── ScanHistory.jsx
│   │   │   ├── SkillLibrary.jsx
│   │   │   └── ToolManager.jsx
│   │   └── pages/               # 5 个页面
│
├── tests/
│   ├── unit/                    # 134 个单元测试（全部通过）
│   ├── root_tests/              # 28 个集成测试
│   └── conftest.py              # pytest fixtures
│
├── config/
│   ├── modules.yaml             # 模块配置
│   └── tools_extended.json      # 工具扩展配置
│
├── docker/
│   ├── Dockerfile（后端）
│   ├── Dockerfile.frontend
│   ├── nginx.conf / nginx-site.conf
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
│
└── .github/workflows/
    ├── ci.yml          # CI（后端测试、前端构建、配置检查）
    ├── security.yml    # 安全扫描（bandit、pip-audit、npm-audit）
    └── release.yml     # 发布流程
```

---

## 四、核心架构：P-E-R 框架

```
用户输入目标
      ↓
  PERAgent.run()
      ↓
┌─────────────────────────────────────┐
│           P-E-R 循环                 │
│                                     │
│  1. Planner（规划器）                │
│     ├── 分析目标                     │
│     ├── 生成子任务列表               │
│     └── 构建任务依赖图               │
│              ↓                      │
│  2. Executor（执行器）               │
│     ├── 调用安全工具（真实/模拟）     │
│     ├── 调用 Skill 技能             │
│     └── 收集执行结果                 │
│              ↓                      │
│  3. Reflector（反思器）              │
│     ├── 评估结果质量                 │
│     ├── 识别漏洞和发现               │
│     ├── 决定是否需要重规划           │
│     └── 生成下一步建议              │
│              ↓                      │
│     重复直到目标完成 或 达到最大轮次  │
└─────────────────────────────────────┘
      ↓
  生成报告
```

**关键参数**：
- 默认最大轮次：5（快速模式3，深度模式10）
- 支持用户实时干预（pause/resume/stop/追加指令）
- 支持 EventBus 广播给 TUI 界面

---

## 五、技能系统（27 个）

技能是比直接调用工具更高层的抽象，封装了完整的测试流程（payload 构造 → 发包 → 结果解析 → 漏洞判断）。

### 内置技能（14 个）
| 类别 | 技能 ID |
|------|---------|
| SQL 注入 | sqli_basic, sqli_union, sqli_time_blind |
| XSS | xss_reflected, xss_stored |
| 认证绕过 | auth_bypass_sql, auth_bruteforce |
| 信息泄露 | info_backup_files, info_sensitive_paths |
| RCE | rce_command_injection |
| LFI | lfi_basic |
| DVWA 专用 | dvwa_sqli, dvwa_xss, dvwa_bruteforce |

### 扩展技能（13 个）
| 技能 ID | 类型 |
|---------|---------|
| xxe_testing | Web漏洞 |
| ssrf_testing | Web漏洞 |
| file_upload_testing | Web漏洞 |
| ssti_testing | 注入类 |
| idor_testing | 访问控制 |
| csrf_testing | Web漏洞 |
| deserialization_testing | 反序列化 |
| nosql_injection | 注入类 |
| flag_detector | CTF辅助 |
| waf_detect | 指纹识别 |
| openssh_user_enum | 信息收集 |
| privesc_linux / privesc_windows | 权限提升 |

### 辅助工具
- **PayloadMutator**：Payload 变异器，生成 WAF 绕过变体
- **WAF_SIGNATURES**：15+ WAF 指纹库
- **FLAG_PATTERNS**：CTF Flag 检测正则

### OpenAI Function Calling 集成
```python
registry = get_skill_registry()
schemas = registry.get_openai_tools()  # 生成 Function Calling Schema
# P-E-R Agent 自动识别 skill_ 前缀工具调用
```

---

## 六、LLM 后端支持

```python
# 支持的后端（统一 LLMBackend 抽象）
openai_backend    # GPT-4o, GPT-4-turbo
anthropic_backend # Claude 3.5 Sonnet
ollama_backend    # 本地模型（llama3, mistral）
mock_backend      # 无 API Key 时的离线模式

# 多模型路由（按任务类型选最优/最便宜的模型）
router.py → 根据任务复杂度、成本预算自动选择
```

**环境变量配置**：
```env
DEEPSEEK_API_KEY=...      # 推荐（便宜、效果好）
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 七、API 端点概览

```
POST /api/v1/attack          # 发起渗透测试
GET  /api/v1/tools           # 列出可用工具
POST /api/v1/tools/execute   # 执行单个工具
GET  /api/v1/health          # 健康检查
GET  /api/v1/status          # 系统状态

POST /api/v1/auth/login      # 登录（速率限制：5次/分钟）
POST /api/v1/auth/register   # 注册

GET  /api/v1/skills          # 技能列表
POST /api/v1/skills/execute  # 执行技能

GET  /api/v1/reports         # 报告列表
POST /api/v1/reports         # 生成报告

GET  /api/v1/audit/events    # 审计日志（需认证）
GET  /api/v1/metrics         # Prometheus 指标
```

---

## 八、已完成的四个开发阶段

### Phase 1 — 安全加固（完成）
- 输入验证（SQL注入/XSS/命令注入/路径遍历检测）
- JWT 认证、RBAC 权限系统
- 审计日志系统

### Phase 2 — 工程基础设施（完成）
- LLMBackend 抽象层（统一多模型接口）
- EventBus 事件系统（组件间解耦通信）
- Session 用户干预历史
- 多模型路由与成本优化

### Phase 3 — 功能补全（完成）
- CLI/TUI 界面（Textual 富文本终端）
- 27 个渗透技能（内置 + 扩展）
- PayloadMutator、WAF 检测
- P-E-R 框架完整实现

### Phase 4 — 生产就绪（完成）
- 配置统一化（环境变量驱动，无硬编码密钥）
- JSON 结构化日志 + RequestId 追踪
- Docker 生产加固（Nginx TLS、HSTS、CSP）
- API 速率限制（滑动窗口，路径级别配置）
- CI/CD（后端测试、前端构建、安全扫描）

---

## 九、当前测试状态

```
单元测试（tests/unit/）：  134 passed, 0 failed
集成测试（tests/root_tests/）： 28 passed, 2 skipped, 0 failed
其他测试：                 14 passed, 14 skipped（需 Neo4j/API Key）

总计：176 passed, 16 skipped, 0 failed
代码覆盖率：19%（低于 30% 阈值，因为工具层需真实环境）
```

---

## 十、已知瓶颈与问题（请 GPT 帮分析）

这是我们目前感受到的瓶颈，希望得到架构建议：

### 1. AI 决策质量不稳定
- P-E-R 框架虽然实现了，但 Planner 生成的子任务图质量依赖 prompt 质量
- 相同目标不同轮次结果差异大，缺乏稳定的决策策略
- Reflector 的"是否需要重规划"判断逻辑较弱

### 2. 工具层与 AI 层耦合不清晰
- 有两套工具调用路径：直接调用 `tools/*.py` 和通过 `skills/*.py`
- 两者功能重叠，缺乏清晰的分层设计

### 3. 上下文窗口管理
- 长会话（10+ 轮）后 LLM 上下文溢出
- `learning_system.py` 有历史压缩逻辑但尚未完全集成进 P-E-R 循环

### 4. 真实工具执行不稳定
- 大量工具（nmap、sqlmap 等）需要安装在系统上
- 当前的"真实/模拟自动切换"逻辑使得测试结果不可预测
- 工具超时、错误处理不够健壮

### 5. 前端与后端实时通信
- 当前用 REST API 轮询，没有实现 WebSocket 实时推送
- `api/websocket.py` 存在但尚未整合进前端

### 6. 缺少评估基准
- 没有对 AI 决策效果的量化指标
- `benchmarking/` 目录有框架但尚未与实际数据集结合

---

## 十一、启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.development .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 或 OPENAI_API_KEY

# 启动后端（端口 5000）
python start.py --backend
# 或
python -m src.shared.backend.main --port 5000

# 启动前端（端口 5173）
cd frontend && npm run dev

# CLI 对话模式（无需启动服务）
python clawai.py
python clawai.py chat -t 192.168.1.1

# Docker 启动
docker-compose up -d

# 运行测试
pytest tests/unit/ -v
pytest tests/root_tests/ -v
```

---

## 十二、核心文件速查

| 想了解什么 | 看哪里 |
|-----------|--------|
| AI 决策循环 | `src/shared/backend/per/agent.py` |
| 任务规划逻辑 | `src/shared/backend/per/planner.py` |
| 工具执行逻辑 | `src/shared/backend/per/executor.py` |
| 结果评估逻辑 | `src/shared/backend/per/reflector.py` |
| 技能注册与执行 | `src/shared/backend/skills/registry.py` + `core.py` |
| 工具统一执行器 | `src/shared/backend/tools/unified_executor_final.py` |
| LLM 多模型路由 | `src/shared/backend/llm/router.py` |
| API 路由入口 | `src/shared/backend/main.py` |
| CLI 对话逻辑 | `src/cli/chat_cli.py` |
| 渗透流程定义 | `src/shared/backend/workflow/penetration_stages.py` |
