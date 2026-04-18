# ClawAI 插件市场设计方案

**版本**：v1.0  
**日期**：2026-04-11  
**作者**：ClawAI 团队  

---

## 目录

1. [概述与背景](#1-概述与背景)
2. [架构设计](#2-架构设计)
3. [插件规范](#3-插件规范)
4. [插件生命周期](#4-插件生命周期)
5. [安全沙箱机制](#5-安全沙箱机制)
6. [Demo 插件说明](#6-demo-插件说明)
7. [开发者指南（快速开始）](#7-开发者指南快速开始)
8. [商业化路径](#8-商业化路径)
9. [技术路线图](#9-技术路线图)

---

## 1. 概述与背景

### 1.1 为什么需要插件市场

ClawAI 目前内置了 30+ 安全工具和 27 个技能（Skills），覆盖了常见渗透测试场景。但安全领域具有以下特点：

- **漏洞迭代快速**：新 CVE 每天涌现，核心工具无法及时跟进所有新漏洞
- **场景高度垂直**：不同目标（IoT/工控/云原生/移动端）需要专门工具
- **社区生态丰富**：大量优秀的开源工具和脚本散落在社区中，缺乏统一集成方式
- **AI 增强需求差异化**：不同用户对 AI 辅助的需求（报告风格、模型选择、语言）各不相同

插件市场通过**标准化的插件接口 + 去中心化的发布机制**，让社区贡献者能够以最小成本将工具、脚本和 AI 增强能力集成到 ClawAI 中。

### 1.2 核心目标

| 目标 | 说明 |
|------|------|
| **可扩展** | 任何人都能写插件，5 分钟内完成第一个插件 |
| **安全可信** | 权限声明 + 沙箱隔离，插件无法越权操作 |
| **开箱即用** | 官方 Demo 插件直接可运行，无需额外配置 |
| **AI 原生** | 插件可直接调用 ClawAI 的 LLM 客户端和 P-E-R 框架 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                   ClawAI 主系统                      │
│                                                      │
│  ┌──────────────┐   ┌──────────────────────────┐   │
│  │ Plugin Store  │   │     Plugin Runtime        │   │
│  │ (后端API)    │   │ ┌────────────────────┐   │   │
│  │              │◄──►│ │   PluginLoader     │   │   │
│  │ /api/v1/     │   │ │   plugin.json 解析  │   │   │
│  │  plugins     │   │ │   权限检查          │   │   │
│  └──────────────┘   │ └────────────────────┘   │   │
│          │          │ ┌────────────────────┐   │   │
│          │          │ │   SandboxContext    │   │   │
│  ┌───────▼──────┐   │ │   注入 LLM/HTTP/  │   │   │
│  │ Plugin       │   │ │   Finding API      │   │   │
│  │ Registry     │   │ └────────────────────┘   │   │
│  │ (内存/DB)    │   │ ┌────────────────────┐   │   │
│  └──────────────┘   │ │   Plugin Instance  │   │   │
│                     │ │   create_plugin()  │   │   │
│  ┌──────────────┐   │ │   .run()           │   │   │
│  │ Marketplace  │   │ └────────────────────┘   │   │
│  │ (GitHub/CDN) │   └──────────────────────────┘   │
│  └──────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

### 2.2 插件运行流程

```
用户点击"安装插件"
        │
        ▼
  下载 plugin.json + plugin.py
        │
        ▼
  权限检查（声明的 permissions 是否在白名单内）
        │ 通过
        ▼
  PluginLoader.load(plugin_dir)
        │
        ▼
  create_plugin(config) → Plugin 实例
        │
        ▼
  P-E-R 执行器调用 plugin.run(target, context)
        │
        ▼
  收集 Findings → 写入扫描结果
```

### 2.3 与 P-E-R 框架集成

插件被注册为 **Executor 工具**，通过工具名 `plugin:<plugin_id>` 调用：

```python
# Executor 自动识别 plugin: 前缀
tool_result = await executor.call_tool(
    tool_name="plugin:jwt_scanner",
    args={"target": "https://example.com", "config": {...}},
)
```

Planner 可以在任务图中引用插件，Reflector 会根据插件返回的 Findings 质量评估执行效果。

---

## 3. 插件规范

### 3.1 目录结构

```
my_plugin/
├── plugin.json       # 必须：插件元数据（见 3.2）
├── plugin.py         # 必须：插件实现（见 3.3）
├── README.md         # 推荐：使用说明
├── screenshot.png    # 推荐：插件界面截图（用于市场展示）
└── requirements.txt  # 可选：Python 依赖
```

### 3.2 plugin.json 字段说明

```jsonc
{
  // ── 必填 ──────────────────────────────────────────────
  "id": "my_plugin",                    // 唯一标识，lowercase + underscore
  "name": "My Plugin 显示名称",
  "version": "1.0.0",                   // 语义化版本
  "description": "一句话描述",
  "author": "作者名称",
  "license": "MIT",
  "category": "scanner",                // 见 3.4 分类列表
  "entry": "plugin.py",                 // 入口文件
  "min_clawai_version": "2.0.0",        // 最低兼容版本

  // ── 权限声明（必填）────────────────────────────────────
  "permissions": [
    "http:request",      // 发送 HTTP 请求
    "finding:report",    // 上报 Finding
    "llm:call",          // 调用 LLM
    "dns:listen",        // 监听 DNS 回调
    "network:callback",  // 网络回调监听
    "finding:read",      // 读取当前 Findings
    "finding:update",    // 修改 Finding 数据
    "skill:register",    // 注册新 Skill
    "file:read"          // 读取本地文件（限沙箱目录）
  ],

  // ── 可选 ──────────────────────────────────────────────
  "tags": ["web", "jwt", "authentication"],
  "icon": "🔐",
  "author_url": "https://github.com/...",
  "cve_references": ["CVE-2021-44228"],
  "config_schema": { ... },             // JSON Schema 定义配置项
  "screenshot": "screenshot.png",
  "readme": "README.md",
  "changelog": [...]
}
```

### 3.3 plugin.py 实现接口

```python
# 每个插件必须实现以下接口

class MyPlugin:
    plugin_id = "my_plugin"  # 与 plugin.json id 一致

    def __init__(self, config: dict = None):
        """初始化插件，接收用户配置"""
        self.config = config or {}

    def run(self, target: str, context: dict) -> list[dict]:
        """
        主执行函数
        
        Args:
            target:  扫描目标（URL/IP/域名）
            context: 执行上下文，包含：
                     - http_session:    可用于发送 HTTP 请求
                     - llm_client:      LLM 调用客户端
                     - findings:        当前已发现的漏洞列表
                     - cookies:         目标 Cookie
                     - http_responses:  历史 HTTP 响应
                     - tech_stack:      目标技术栈信息
                     - waf_detected:    检测到的 WAF 类型
        
        Returns:
            list of Finding dicts，格式见 3.5
        """
        findings = []
        # ... 实现扫描逻辑
        return findings

    def health_check(self) -> dict:
        """健康检查，返回 {"ok": bool, "message": str}"""
        return {"ok": True, "message": "ready"}


# 框架通过此函数创建插件实例
def create_plugin(config=None) -> MyPlugin:
    return MyPlugin(config=config)
```

### 3.4 插件分类

| 分类 | 标识 | 说明 |
|------|------|------|
| 扫描器 | `scanner` | 端口扫描、Web 扫描、漏洞扫描 |
| 漏洞利用 | `exploit` | 漏洞 PoC、认证绕过 |
| 信息收集 | `recon` | 子域名、OSINT、指纹 |
| 暴力破解 | `brute-force` | 密码破解、目录枚举 |
| 后渗透 | `post-exploit` | 权限提升、横向移动 |
| AI 增强 | `ai_enhanced` | LLM 辅助的智能功能 |
| 报告 | `reporting` | 报告生成、数据导出 |
| 代理 | `proxy` | 流量拦截、修改 |

### 3.5 Finding 标准格式

```python
{
    "type": str,          # 漏洞类型，如 "sqli" / "xss"
    "title": str,         # 漏洞标题（简洁）
    "severity": str,      # critical / high / medium / low / info
    "description": str,   # 漏洞详情说明
    "location": str,      # 漏洞位置（URL/参数/Header名）
    "evidence": str,      # 证据（请求/响应片段）
    "remediation": str,   # 修复建议
    "cve": str,           # CVE 编号（可选）
    "source": str,        # 来源，如 "plugin:jwt_scanner"
    "metadata": dict,     # 额外数据（插件自定义）
}
```

---

## 4. 插件生命周期

### 4.1 状态流转

```
available（市场可安装）
    │
    │ 用户点击安装
    ▼
installing（下载/依赖安装中）
    │
    │ 成功
    ▼
installed（已安装，待启用）
    │
    │ 启用
    ▼
active（运行中）◄────────────────────┐
    │                                │
    │ 禁用                            │ 重新启用
    ▼                                │
disabled（已禁用）──────────────────►┘
    │
    │ 卸载
    ▼
available
```

### 4.2 版本更新策略

- **自动更新**（默认开启）：ClawAI 每天检查已安装插件的新版本
- **手动更新**：用户可在插件详情页手动触发更新
- **版本锁定**：可在 `plugin.json` 中指定 `"pin_version": true` 阻止自动更新
- **回滚**：保留最近 2 个版本，支持一键回滚

### 4.3 配置持久化

插件配置存储在 `~/.clawai/plugin_configs/<plugin_id>.json`，重装后自动恢复。

---

## 5. 安全沙箱机制

### 5.1 权限模型

插件只能调用 `plugin.json` 中声明的权限。未声明的权限调用将被拦截并记录日志：

```python
# PermissionError 示例
# 插件声明了 ["http:request"] 但尝试读取文件
context.file_read("/etc/passwd")
# → PermissionError: plugin 'jwt_scanner' lacks 'file:read' permission
```

**权限级别**：

| 权限 | 风险 | 默认是否需要用户确认 |
|------|------|---------------------|
| `http:request` | 低 | 否 |
| `finding:report` | 低 | 否 |
| `llm:call` | 低 | 否（计入 token 消耗） |
| `finding:read/update` | 低 | 否 |
| `file:read` | 中 | 否（限沙箱目录） |
| `dns:listen` | 中 | 是 |
| `network:callback` | 中 | 是 |
| `skill:register` | 中 | 是 |
| `system:exec` | 高 | **禁止社区插件使用** |
| `file:write` | 高 | **禁止社区插件使用** |

### 5.2 沙箱上下文注入

框架为插件注入受限的上下文对象，替代直接的系统访问：

```python
# SandboxContext 提供的 API
context = {
    # HTTP 请求（自动附加授权头、限制目标范围）
    "http_session": SandboxHttpSession(target_scope=["example.com"]),

    # LLM 调用（记录 token 消耗，支持限速）
    "llm_client": SandboxLLMClient(rate_limit=10),

    # Finding 操作（隔离每次扫描的结果）
    "findings": FindingStore(scan_id=current_scan_id),

    # 只读的扫描上下文信息
    "target": "https://example.com",
    "tech_stack": "nginx/1.24 + PHP/8.1 + WordPress/6.4",
    "waf_detected": "cloudflare",
    "cookies": {"session": "abc123"},
    "http_responses": [...],  # 最近 50 条响应
}
```

### 5.3 插件代码审查

**社区插件**发布流程包含：
1. **自动静态扫描**：Bandit + Semgrep 检测危险 API 调用
2. **沙箱动态测试**：在隔离环境中运行插件，监控系统调用
3. **人工审核**（可选）：高权限插件需等待官方审核（预计 1-3 个工作日）

---

## 6. Demo 插件说明

以下三个 Demo 插件位于 `plugins/demo/`，可直接在 ClawAI 中安装使用。

### 6.1 JWT 安全检测器（`jwt_scanner`）

**文件**：`plugins/demo/jwt_scanner/`

**功能**：
- 自动从 HTTP 响应、Cookie、Authorization Header 中提取 JWT Token
- **alg:none 混淆检测**：检测服务端是否接受无签名 Token（CVE-2015-9235）
- **弱密钥破解**：使用内置 500+ 弱密钥字典尝试破解 HMAC 签名（HS256/HS384/HS512）
- **敏感信息扫描**：检测 Payload 中是否包含密码、密钥等敏感字段
- **过期校验检测**：检测缺少 `exp` 声明的 Token

**使用场景**：存在登录认证的 Web 应用，Token 鉴权 API

**权限要求**：`http:request`, `finding:report`

**示例输出**：
```
[critical] JWT 算法设置为 none（签名绕过）
  位置：Header:Authorization
  证据：alg=none  token=eyJhbGciOiJub25lIn0...
  修复：服务端强制校验 alg 字段，使用白名单限制允许算法
```

---

### 6.2 Log4Shell 漏洞检测（`log4shell_scanner`）

**文件**：`plugins/demo/log4shell_scanner/`

**覆盖 CVE**：CVE-2021-44228 / CVE-2021-45046 / CVE-2021-45105

**功能**：
- 内置 6 种 JNDI Payload 变体（含大小写混淆、嵌套表达式绕过）
- 内置轻量 HTTP 回调服务，无需外部 DNSLOG
- 向 7 个常见 HTTP Header 注入 Payload（User-Agent / X-Forwarded-For / Referer 等）
- 支持 CVE-2021-45046 变体检测

**使用场景**：任何使用 Java 技术栈的 Web 服务，特别是 2021 年底前部署的未更新服务

**权限要求**：`http:request`, `dns:listen`, `network:callback`, `finding:report`

**检测流程**：
```
1. 为每个 Payload 生成唯一 UUID 追踪 ID
2. 向目标所有 Header 并发注入 Payload（不阻塞 HTTP 响应）
3. 等待 15s 内置回调服务是否收到请求
4. 收到回调 → Critical 发现（确认存在 RCE）
5. 未收到但检测到 Java 特征 → Low 发现（建议手动复测）
```

---

### 6.3 AI 辅助 Payload 生成器（`ai_payload_gen`）

**文件**：`plugins/demo/ai_payload_gen/`

**功能**：
- 读取当前 Findings，自动识别需要增强的漏洞类型
- 调用 LLM（支持 GPT-4o / DeepSeek / Claude / 继承系统默认）
- 根据目标技术栈和 WAF 类型生成针对性 Payload 变体
- 支持 SQLi / XSS / SSTI / SSRF / RCE / LFI / XXE 等 10+ 类型
- 无 LLM 时自动回退到内置基础 Payload 库

**使用场景**：
- 发现漏洞后需要生成绕过 WAF 的 Payload 变体
- CTF 比赛中快速生成多种编码形式的 Payload
- 研究特定技术栈（如 Jinja2 SSTI）的利用 Payload

**权限要求**：`llm:call`, `finding:read`, `finding:update`, `skill:register`

**Context-Aware 模式示例**：
```
当前 Findings:
  - [high] SQL 注入 @ /login?id=1 (MySQL 5.7)

AI 生成输出（WAF: Cloudflare）:
  [1] 1/*!50000UNION*//*!50000SELECT*/NULL,NULL,NULL--
  [2] 1'/**/OR/**/1=1--
  [3] 1' OR '1'%3d'1
  [4] 1\' OR 1=1-- （宽字节绕过）
  [5] 1' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version())))--
```

---

## 7. 开发者指南（快速开始）

### 7.1 创建第一个插件（10 分钟）

```bash
# 克隆模板（Demo 插件作为参考）
cp -r plugins/demo/jwt_scanner plugins/my_plugin

# 修改 plugin.json
vi plugins/my_plugin/plugin.json   # 修改 id / name / description

# 实现 plugin.py
vi plugins/my_plugin/plugin.py     # 实现 run() 方法

# 本地测试
python -c "
from plugins.my_plugin.plugin import create_plugin
plugin = create_plugin()
print(plugin.health_check())
findings = plugin.run('http://localhost', {})
print(f'发现 {len(findings)} 个 Finding')
"
```

### 7.2 Plugin Context API 速查

```python
# HTTP 请求
resp = context["http_session"].get(url, headers={...}, timeout=10)
resp.status_code    # int
resp.text           # str
resp.headers        # dict

# 调用 LLM
result = context["llm_client"].chat(
    messages=[{"role": "user", "content": "..."}],
    temperature=0.7,
    max_tokens=512,
)
text = result["content"]   # str

# 报告 Finding（直接调用 API，无需 return）
context["findings"].add({
    "type": "my_vuln",
    "title": "...",
    "severity": "high",
    ...
})

# 读取已有 Findings
existing = context["findings"].list()   # list[dict]
```

### 7.3 发布到插件市场

1. 将插件上传到 GitHub（建议命名：`clawai-plugin-<id>`）
2. 在 README 中包含 `plugin.json` 的完整内容
3. 提交 PR 到 [ClawAI 插件索引库](https://github.com/clawai-demo/plugin-index)
4. 机器人自动运行静态扫描，通过后自动合并
5. 插件在 ClawAI 插件市场搜索中可见（约 5 分钟）

---

## 8. 商业化路径

### 8.1 插件类型与收费模型

| 类型 | 收费模型 | 示例 |
|------|----------|------|
| **免费开源** | 完全免费，MIT/Apache | Demo 三个插件、大多数社区插件 |
| **免费闭源** | 免费使用，不开放源码 | 商业工具的集成适配层 |
| **付费订阅** | 月费/年费，含更新和支持 | 高级 AI 增强插件、企业专属漏洞库 |
| **按调用计费** | 消耗 ClawAI Credits | LLM 密集型插件、大规模扫描插件 |
| **企业授权** | 私有部署 + 定制 | 面向企业的专项合规检测插件 |

### 8.2 收益分成

ClawAI 插件市场采用 **7:3 分成**：
- 插件开发者获得 **70%** 收益
- ClawAI 平台抽成 **30%**（含支付处理、安全审计、CDN 分发）

### 8.3 官方认证计划

达到以下标准的插件可申请「官方认证」徽章（提升曝光和信任度）：

- 代码开源 + MIT/Apache 许可
- 通过官方安全审计
- 提供完整测试用例（覆盖率 ≥ 80%）
- 在真实靶机（DVWA/Vulhub）上验证有效性
- 文档完整（README + 配置说明 + 使用截图）

---

## 9. 技术路线图

### Phase 1（当前）— 基础框架
- [x] 插件规范定义（plugin.json + plugin.py 接口）
- [x] 3 个 Demo 插件（jwt_scanner / log4shell_scanner / ai_payload_gen）
- [x] 后端 API 展示 Demo 插件（/api/v1/plugins）
- [x] 前端插件市场 UI（PluginManager 组件）
- [ ] PluginLoader 实现（从本地目录加载插件）
- [ ] 权限检查拦截层（SandboxContext）

### Phase 2（下一步）— 完整运行时
- [ ] 真实 PluginLoader：扫描 `plugins/` 目录，自动注册到 P-E-R Executor
- [ ] SandboxHttpSession / SandboxLLMClient 实现
- [ ] 插件热加载（修改插件后无需重启服务）
- [ ] 插件依赖管理（自动 `pip install -r requirements.txt`）
- [ ] `clawai.py plugin install/uninstall/list` CLI 命令

### Phase 3（社区生态）— 在线市场
- [ ] GitHub 插件索引库（`clawai-demo/plugin-index`）
- [ ] 自动化静态安全扫描 CI（Bandit + Semgrep）
- [ ] 前端市场搜索：支持从 GitHub 一键安装
- [ ] 插件评分和评论系统
- [ ] 插件版本自动更新通知

### Phase 4（商业化）— 变现
- [ ] 付费插件支付集成（微信支付/支付宝）
- [ ] ClawAI Credits 计费系统
- [ ] 企业私有插件仓库（Private Registry）
- [ ] 官方插件认证徽章审核流程

---

## 附录 A：Demo 插件文件结构

```
plugins/
└── demo/
    ├── jwt_scanner/
    │   ├── plugin.json     # 元数据：权限、配置 Schema、版本
    │   └── plugin.py       # 实现：alg:none / 弱密钥 / 敏感声明检测
    ├── log4shell_scanner/
    │   ├── plugin.json     # 元数据：CVE 引用、回调权限
    │   └── plugin.py       # 实现：JNDI 注入 + 内置 HTTP 回调
    └── ai_payload_gen/
        ├── plugin.json     # 元数据：LLM 权限、模型配置
        └── plugin.py       # 实现：WAF 感知 + LLM 生成 + 回退策略
```

## 附录 B：与现有技能库（Skills）的区别

| 维度 | Skills（技能库） | Plugins（插件） |
|------|-----------------|----------------|
| **来源** | 内置，随 ClawAI 发布 | 社区贡献，独立安装 |
| **更新** | 随主版本更新 | 独立版本，随时更新 |
| **权限** | 完整系统权限 | 声明式权限 + 沙箱 |
| **集成方式** | P-E-R 工具调用 | P-E-R 工具调用（`plugin:id`） |
| **适用场景** | 通用渗透流程 | 专项漏洞、特定工具、AI 增强 |
| **开发门槛** | 需修改核心代码 | 独立 `plugin.py` 文件即可 |
