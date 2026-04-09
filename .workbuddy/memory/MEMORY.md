# MEMORY.md - 长期记忆

## 项目：ClawAI

**类型：** 基于大模型的自动化渗透测试系统

**技术栈：**
- 后端：Python 3.8+、FastAPI、SQLite、Uvicorn
- 前端：React、Three.js（3D可视化）、Vite（端口 5173）
- AI核心：支持 GPT / Claude / DeepSeek 等大模型
- 后端端口：8080（开发），前端端口：5173

**核心架构：**
- P-E-R 框架（Planner 规划器 → Executor 执行器 → Reflector 反思器）
- 统一工具执行器（ToolManager）
- 技能库系统（Skills）
- RBAC 权限管理
- 审计系统

**关键目录：**
- `src/shared/backend/` — 主后端代码，包含所有业务逻辑
- `src/shared/backend/main.py` — FastAPI 应用入口
- `src/shared/backend/per/` — P-E-R 框架（planner/executor/reflector）
- `src/shared/backend/tools/` — 工具封装层
- `tools/penetration/` — 第三方安全工具源码（sqlmap、dirsearch、nmap 等）
- `frontend/src/` — React 前端代码
- `config/` — YAML 配置文件

**集成的安全工具（部分）：**
nmap、masscan、rustscan、nuclei、gobuster、dirsearch、nikto、sqlmap、xsstrike、commix、amass、subfinder、theHarvester、hashcat、hydra、john、wafw00f、impacket、exploitdb 等

**启动方式：**
- Windows: `start.bat`
- 后端: `python -m src.shared.backend.main --port 8080`
- 前端: `cd frontend && npm run dev`

**最后更新：** 2026-04-08
