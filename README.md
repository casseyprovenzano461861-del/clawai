# ClawAI - 基于大模型的自动化渗透测试系统

## 项目简介
ClawAI 是一个创新的基于大模型的自动化渗透测试系统，旨在提高安全测试的效率和准确性。该系统整合了先进的AI技术和安全工具，为用户提供了一种高效、全面的安全测试解决方案。

## 核心功能

### 1. 自动化渗透测试流程
- 支持完整的渗透测试生命周期：信息收集、漏洞扫描、漏洞利用、后渗透
- 智能规划测试步骤，自动执行测试任务
- 实时监控测试进度和结果

### 2. 智能工具选择和执行
- 集成 **63个** 安全工具和技能（36工具包 + 17 Schema + 27 Skills）
- 基于目标环境和测试阶段智能选择工具
- 支持并行执行和超时控制

### 3. 实时监控和可视化
- 3D攻击链路可视化
- 漏洞仪表盘
- 实时测试进度跟踪

### 4. 详细的测试报告生成
- 自动生成详细的测试报告
- 包含漏洞分析和修复建议
- 支持多种报告格式

### 5. 多平台支持
- 支持Windows和Linux双平台目标环境
- 支持Vulnhub和Vulhub的靶机环境
- 实现跨平台的工具执行机制

## 技术架构

### 前端
- React 应用，提供用户友好的界面
- Three.js 实现3D攻击链路可视化
- 响应式设计，支持不同设备

### 后端
- Python + FastAPI 框架，提供API服务
- SQLite 数据库，存储测试结果和配置
- 统一工具执行器，支持多种安全工具

### AI 核心
- 基于大模型的智能决策系统
- 支持GPT、Claude、DeepSeek等主流大模型
- 实现基于大模型的分析与决策机制

### 核心模块
- P-E-R 协作框架（Planner-Executor-Reflector）
- 统一工具执行器
- 智能AI编排器
- 技能库系统
- 量化指标计算
- 实时监控系统

## 安装指南

### 系统要求
- Python 3.8+
- Node.js 14+
- npm 6+

### 后端安装
1. 克隆项目仓库
   ```bash
   git clone https://github.com/ClawAI/ClawAI.git
   cd ClawAI
   ```

2. 创建虚拟环境并激活
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

4. 启动后端服务器
   ```bash
   python -m src.shared.backend.main --port 8080
   ```

### 前端安装
1. 进入前端目录
   ```bash
   cd frontend
   ```

2. 安装依赖
   ```bash
   npm install
   ```

3. 启动前端开发服务器
   ```bash
   npm run dev
   ```

4. 访问前端应用
   打开浏览器，访问 http://localhost:3000

## 使用说明

### 快速开始

```bash
# 1. 配置 API Key
echo "DEEPSEEK_API_KEY=sk-xxxxx" > .env

# 2. 一键启动
start.bat  # Windows
# ./start.sh  # Linux/Mac

# 3. 访问界面
# 前端: http://localhost:5173
# 后端: http://localhost:8080
```

### CLI 命令行

```bash
# AI 对话模式
python clawai.py

# 带目标的对话
python clawai.py chat -t http://example.com

# 快速扫描
python clawai.py scan 192.168.1.1

# 工具管理
python clawai.py tools list

# 服务状态
python clawai.py status
```

### Python API

```python
from src.shared.backend.skills import get_skill_registry

# 使用 Skills 库
registry = get_skill_registry()
result = registry.execute("sqli_basic", {
    "target": "http://example.com/page?id=1"
})
print(f"漏洞存在: {result['vulnerable']}")
```

### 详细文档

查看 [使用指南](docs/使用指南.md) 获取完整文档。

---

### 1. 目标配置
- 在前端界面输入目标地址（如 example.com）
- 点击「开始测试」按钮启动渗透测试

### 2. 测试监控
- 实时查看测试进度和阶段状态
- 查看发现的漏洞列表
- 监控系统状态

### 3. 报告查看
- 测试完成后，查看详细的测试报告
- 报告包含漏洞分析和修复建议

### 4. 3D攻击链路可视化
- 查看3D攻击链路图
- 点击节点查看详细信息
- 调整视角和旋转模式

## 工具集成

ClawAI 集成了以下安全工具：

### 网络扫描工具
- nmap - 网络映射与端口扫描
- masscan - 高速网络扫描
- rustscan - 快速端口扫描

### Web扫描工具
- nuclei - 基于模板的漏洞扫描
- gobuster - 目录和文件枚举
- dirsearch - Web路径扫描
- nikto - Web服务器安全扫描
- sqlmap - SQL注入检测
- xsstrike - XSS检测
- commix - 命令注入检测

### 信息收集工具
- amass - 子域名枚举
- subfinder - 子域名发现
- theharvester - 信息收集

### 密码破解工具
- hashcat - 密码哈希破解
- hydra - 密码暴力破解
- john - 密码破解

### 安全评估工具
- nikto - Web服务器安全扫描
- wafw00f - WAF检测

## 技术指标

ClawAI 提供以下技术指标的量化呈现：

- **漏洞检测率**：检测到的漏洞数量与实际漏洞数量的比率
- **误报率**：误报的漏洞数量与检测到的漏洞数量的比率
- **CVE覆盖度**：检测到的CVE漏洞数量与已知CVE漏洞数量的比率
- **攻击能效**：成功利用的漏洞数量与尝试利用的漏洞数量的比率
- **单目标测试时间**：完成单个目标测试所需的时间
- **并发处理能力**：同时处理多个测试任务的能力

## 项目亮点

1. **基于大模型的智能决策**：利用大模型的推理能力，智能选择测试策略和工具
2. **3D攻击链路可视化**：提供直观的攻击链路展示，帮助用户理解攻击过程
3. **统一工具执行器**：支持多种安全工具的统一执行和结果解析
4. **P-E-R 协作框架**：实现智能规划、执行和反思的协作机制
5. **技能库系统**：封装各类渗透技巧，供AI调用
6. **量化指标计算**：提供客观的技术指标评估

## 未来规划

1. **技术发展**：
   - 集成更多先进的AI模型
   - 支持更多安全工具和漏洞类型
   - 开发更智能的攻击链分析算法
   - 提供更丰富的可视化展示

2. **应用场景**：
   - 企业安全评估
   - 安全培训和教育
   - 漏洞研究和分析
   - 安全合规检查

## 联系方式

- 项目地址：https://github.com/ClawAI/ClawAI
- 联系邮箱：contact@clawai.com
- 技术支持：support@clawai.com

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。