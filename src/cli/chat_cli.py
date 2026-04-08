#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 对话式CLI核心模块
实现AI对话交互、意图识别、任务执行
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# 添加项目根目录到路径
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, _project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 查找.env文件 - 使用项目根目录
    env_path = os.path.join(_project_root, '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv未安装，使用系统环境变量

try:
    from src.ai_engine.llm_agent.pentest_agent import ClawAIPentestAgent
    AGENT_AVAILABLE = True
except Exception as e:
    AGENT_AVAILABLE = False
    logging.warning(f"ClawAIPentestAgent 导入失败: {e}")

from src.cli.prompts.chat_system import CHAT_SYSTEM_PROMPT, INTENT_PROMPT

logger = logging.getLogger(__name__)


class Intent(Enum):
    """用户意图类型"""
    SCAN = "scan"           # 扫描目标
    ANALYZE = "analyze"     # 分析数据
    EXPLOIT = "exploit"     # 漏洞利用
    REPORT = "report"       # 生成报告
    QUERY = "query"         # 查询状态
    CONFIG = "config"       # 配置设置
    HELP = "help"           # 请求帮助
    CHAT = "chat"           # 普通对话
    EXIT = "exit"           # 退出
    UNKNOWN = "unknown"     # 未知意图


@dataclass
class Message:
    """对话消息"""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Session:
    """会话信息"""
    session_id: str
    target: Optional[str] = None
    phase: str = "idle"
    findings: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str, metadata: Dict = None):
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg


class IntentRecognizer:
    """意图识别器"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        Intent.SCAN: ["扫描", "scan", "测试", "test", "探测", "detect", "检查", "check"],
        Intent.ANALYZE: ["分析", "analyze", "评估", "assess", "查看结果", "show result"],
        Intent.EXPLOIT: ["利用", "exploit", "攻击", "attack", "尝试", "try"],
        Intent.REPORT: ["报告", "report", "导出", "export", "总结", "summary"],
        Intent.QUERY: ["状态", "status", "进度", "progress", "发现", "finding", "端口", "port"],
        Intent.CONFIG: ["配置", "config", "设置", "setting", "切换", "switch"],
        Intent.HELP: ["帮助", "help", "怎么用", "how to", "命令", "command"],
        Intent.EXIT: ["退出", "exit", "quit", "bye", "再见"],
    }

    # 目标提取正则
    TARGET_PATTERNS = [
        r'(?:目标|target|扫描|scan|测试|test)\s*[:：]?\s*([a-zA-Z0-9\-\.]+)',
        r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})',
        r'(https?://[a-zA-Z0-9\-\.]+)',
        r'([a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+)',
    ]

    def __init__(self):
        import re
        self.re = re

    def recognize(self, user_input: str, context: Dict[str, Any] = None) -> Tuple[Intent, Dict[str, Any]]:
        """识别用户意图

        Returns:
            (intent, parameters) 意图类型和提取的参数
        """
        user_input_lower = user_input.lower()
        context = context or {}

        # 1. 检查退出意图
        for keyword in self.INTENT_KEYWORDS[Intent.EXIT]:
            if keyword in user_input_lower:
                return Intent.EXIT, {}

        # 2. 检查帮助意图
        for keyword in self.INTENT_KEYWORDS[Intent.HELP]:
            if keyword in user_input_lower:
                return Intent.HELP, {}

        # 3. 检查扫描意图
        for keyword in self.INTENT_KEYWORDS[Intent.SCAN]:
            if keyword in user_input_lower:
                target = self._extract_target(user_input) or context.get("target")
                return Intent.SCAN, {"target": target}

        # 4. 检查报告意图
        for keyword in self.INTENT_KEYWORDS[Intent.REPORT]:
            if keyword in user_input_lower:
                return Intent.REPORT, {}

        # 5. 检查查询意图
        for keyword in self.INTENT_KEYWORDS[Intent.QUERY]:
            if keyword in user_input_lower:
                return Intent.QUERY, {}

        # 6. 检查分析意图
        for keyword in self.INTENT_KEYWORDS[Intent.ANALYZE]:
            if keyword in user_input_lower:
                return Intent.ANALYZE, {}

        # 7. 检查利用意图
        for keyword in self.INTENT_KEYWORDS[Intent.EXPLOIT]:
            if keyword in user_input_lower:
                return Intent.EXPLOIT, {}

        # 8. 检查配置意图
        for keyword in self.INTENT_KEYWORDS[Intent.CONFIG]:
            if keyword in user_input_lower:
                return Intent.CONFIG, {}

        # 默认为普通对话
        return Intent.CHAT, {}

    def _extract_target(self, text: str) -> Optional[str]:
        """从文本中提取目标地址"""
        for pattern in self.TARGET_PATTERNS:
            match = self.re.search(pattern, text, self.re.IGNORECASE)
            if match:
                return match.group(1)
        return None


class ClawAIChatCLI:
    """ClawAI 对话式CLI核心类"""

    def __init__(self, config: Dict[str, Any] = None):
        """初始化

        Args:
            config: 配置字典，包含LLM、代理等配置
        """
        self.config = config or self._load_default_config()
        self.intent_recognizer = IntentRecognizer()
        self.session = Session(session_id=f"session_{int(time.time())}")
        self.agent = None
        self.running = False
        self._api_key_missing = False

        # 回调函数
        self.on_message: Optional[callable] = None
        self.on_tool_execution: Optional[callable] = None
        self.on_status_change: Optional[callable] = None

        # 初始化代理
        self._init_agent()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        config_path = os.path.join(
            _project_root,
            "src", "ai_engine", "configs", "clawai_pentest_agent.json"
        )

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")

        # 返回默认配置
        return {
            "llm": {
                "provider": "deepseek",
                "model_id": "deepseek-chat",
                "temperature": 0.7,
                "max_new_tokens": 1024
            },
            "agent": {
                "max_iterations": 10,
                "timeout_duration": 30
            }
        }

    def _init_agent(self):
        """初始化AI代理"""
        # 确保环境变量已加载
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(_project_root, '.env'))
        except:
            pass

        if AGENT_AVAILABLE:
            try:
                # 检查API密钥
                provider = self.config.get("llm", {}).get("provider", "deepseek")
                api_key = os.getenv(f"{provider.upper()}_API_KEY", "")

                if not api_key and provider not in ["local", "mock"]:
                    logger.warning(f"未配置 {provider.upper()}_API_KEY，将使用模拟模式")
                    self.agent = None
                    self._api_key_missing = True
                    return

                self.agent = ClawAIPentestAgent(
                    config=self.config,
                    tool_executor_url=self.config.get("tool_executor_url", "http://localhost:8082")
                )
                logger.info(f"ClawAIPentestAgent 初始化成功 (provider: {provider})")
                self._api_key_missing = False
            except Exception as e:
                logger.error(f"ClawAIPentestAgent 初始化失败: {e}")
                self.agent = None
                self._api_key_missing = False
        else:
            logger.info("AI代理模块不可用，使用模拟模式")
            self.agent = None
            self._api_key_missing = False

    async def chat(self, user_input: str) -> str:
        """处理用户输入并返回AI响应

        Args:
            user_input: 用户输入的文本

        Returns:
            AI响应文本
        """
        if not user_input.strip():
            return ""

        # 添加用户消息到会话
        self.session.add_message("user", user_input)

        # 构建上下文
        context = {
            "target": self.session.target,
            "phase": self.session.phase,
            "findings": self.session.findings
        }

        # 识别意图
        intent, params = self.intent_recognizer.recognize(user_input, context)
        logger.info(f"识别意图: {intent.value}, 参数: {params}")

        # 触发状态变化回调
        if self.on_status_change:
            self.on_status_change("processing", f"处理中: {intent.value}")

        # 根据意图处理
        response = await self._handle_intent(intent, params, user_input)

        # 添加AI响应到会话
        self.session.add_message("assistant", response, {"intent": intent.value})

        return response

    async def _handle_intent(self, intent: Intent, params: Dict[str, Any], user_input: str) -> str:
        """处理识别到的意图"""

        if intent == Intent.EXIT:
            self.running = False
            return "再见！感谢使用 ClawAI。"

        elif intent == Intent.HELP:
            return self._get_help_text()

        elif intent == Intent.SCAN:
            target = params.get("target")
            if target:
                self.session.target = target
                self.session.phase = "reconnaissance"
                return await self._execute_scan(target)
            else:
                return "请指定要扫描的目标。例如：扫描 example.com 或 测试 192.168.1.1"

        elif intent == Intent.REPORT:
            return await self._generate_report()

        elif intent == Intent.QUERY:
            return self._get_status()

        elif intent == Intent.ANALYZE:
            return await self._analyze_findings()

        elif intent == Intent.EXPLOIT:
            return await self._execute_exploit(params)

        elif intent == Intent.CONFIG:
            return "配置功能开发中..."

        else:  # CHAT or UNKNOWN
            return await self._general_chat(user_input)

    async def _execute_scan(self, target: str) -> str:
        """执行扫描任务"""
        response_parts = [f"好的，我将对 {target} 进行渗透测试。"]

        # 更新状态
        if self.on_status_change:
            self.on_status_change("scanning", f"正在扫描 {target}")

        if self.agent:
            try:
                # 使用代理执行
                response_parts.append("\n正在调用AI规划器，请稍候...")

                if self.on_tool_execution:
                    self.on_tool_execution("nmap", {"target": target}, "running")

                result = await self.agent.plan_and_execute(
                    target=target,
                    available_skills=["nmap", "whatweb", "nuclei", "nikto"]
                )

                if result.get("status") == "failed":
                    response_parts.append(f"\n执行失败: {result.get('error', '未知错误')}")
                    return "\n".join(response_parts)

                if self.on_tool_execution:
                    self.on_tool_execution("nmap", {"target": target}, "completed")

                # 更新发现
                for iteration in result.get("iterations", []):
                    if iteration.get("command"):
                        finding = {
                            "type": "tool_execution",
                            "command": iteration["command"],
                            "output_preview": iteration.get("command_output", "")[:200]
                        }
                        self.session.findings.append(finding)

                self.session.phase = "scanning"
                response_parts.append(f"\n扫描完成。执行了 {len(result.get('iterations', []))} 个步骤。")

                if result.get("final_summary"):
                    response_parts.append(f"\n\n总结：\n{result['final_summary'][:500]}")

            except Exception as e:
                logger.error(f"扫描执行失败: {e}")
                response_parts.append(f"\n扫描执行失败: {str(e)}")
        else:
            # 模拟模式
            response_parts.append("\n[模拟模式] 正在执行端口扫描...")
            response_parts.append(f"\n发现开放端口: 22(SSH), 80(HTTP), 443(HTTPS)")
            response_parts.append(f"\n建议下一步: 对Web服务进行漏洞扫描")

            self.session.findings.append({
                "type": "simulated_scan",
                "target": target,
                "ports": [22, 80, 443]
            })

        return "\n".join(response_parts)

    async def _generate_report(self) -> str:
        """生成报告"""
        if not self.session.findings:
            return "当前没有发现任何问题。请先执行扫描。"

        report = f"""## 渗透测试报告

**目标**: {self.session.target or '未指定'}
**时间**: {self.session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**阶段**: {self.session.phase}

### 发现的问题

"""
        for i, finding in enumerate(self.session.findings, 1):
            report += f"{i}. {finding.get('type', '未知类型')}\n"
            if finding.get('command'):
                report += f"   命令: {finding['command']}\n"

        report += "\n### 建议\n"
        report += "1. 修复所有发现的安全漏洞\n"
        report += "2. 加强输入验证\n"
        report += "3. 定期进行安全审计\n"

        return report

    def _get_status(self) -> str:
        """获取当前状态"""
        return f"""当前状态:
- 目标: {self.session.target or '未设置'}
- 阶段: {self.session.phase}
- 发现: {len(self.session.findings)} 项
- 消息: {len(self.session.messages)} 条"""

    async def _analyze_findings(self) -> str:
        """分析发现"""
        if not self.session.findings:
            return "当前没有发现数据可供分析。请先执行扫描。"

        analysis = "分析结果:\n\n"
        for i, finding in enumerate(self.session.findings, 1):
            analysis += f"{i}. {finding.get('type', '未知')}\n"

        return analysis

    async def _execute_exploit(self, params: Dict[str, Any]) -> str:
        """执行漏洞利用"""
        return "漏洞利用功能需要明确授权才能执行。请确认你有合法的授权。"

    async def _general_chat(self, user_input: str) -> str:
        """普通对话"""
        # 构建消息历史
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        # 添加最近的对话历史
        for msg in self.session.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_input})

        if self.agent:
            try:
                response, in_tokens, out_tokens = self.agent.generate_text(messages)
                return response
            except Exception as e:
                logger.error(f"LLM生成失败: {type(e).__name__}: {e}")

        # 模拟响应
        return self._generate_mock_response(user_input)

    def _generate_mock_response(self, user_input: str) -> str:
        """生成模拟响应"""
        if "你好" in user_input or "hello" in user_input.lower():
            return "你好！我是 ClawAI 渗透测试助手。我可以帮助你进行安全测试。请告诉我你要测试的目标。"
        elif "什么" in user_input or "what" in user_input.lower():
            return "我是 ClawAI，一个专业的渗透测试AI助手。我可以执行端口扫描、漏洞检测、安全分析等任务。"
        else:
            return "我理解了你的请求。请问你想对哪个目标进行测试？或者输入'帮助'查看我能做什么。"

    def _get_help_text(self) -> str:
        """获取帮助文本"""
        api_hint = ""
        if not self.agent:
            api_hint = """

### ⚠️ AI配置提示

当前运行在模拟模式。要启用完整AI功能，请配置API密钥：

1. 编辑 `.env` 文件，设置以下任一密钥：
   - DEEPSEEK_API_KEY=your_key  (推荐)
   - OPENAI_API_KEY=your_key
   - ANTHROPIC_API_KEY=your_key

2. 重启 ClawAI
"""

        return f"""## ClawAI 帮助

### 基本命令

- **扫描目标**: 扫描 example.com 或 测试 192.168.1.1
- **查看状态**: 状态 或 status
- **生成报告**: 报告 或 report
- **退出**: 退出 或 exit

### 支持的测试类型

1. 端口扫描 (nmap)
2. Web扫描 (nuclei, nikto)
3. 目录枚举 (gobuster, dirsearch)
4. 漏洞检测 (sqlmap, nuclei)
5. 信息收集 (whatweb, theharvester)

### 示例对话

> 扫描 example.com
> 检查是否有SQL注入
> 生成报告

### 快捷键 (TUI模式)

- Ctrl+C: 退出
- F1: 帮助
{api_hint}"""

    def set_target(self, target: str):
        """设置目标"""
        self.session.target = target
        self.session.phase = "initialized"

    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "session_id": self.session.session_id,
            "target": self.session.target,
            "phase": self.session.phase,
            "findings_count": len(self.session.findings),
            "messages_count": len(self.session.messages),
            "created_at": self.session.created_at.isoformat(),
            "updated_at": self.session.updated_at.isoformat()
        }


# 用于测试
if __name__ == "__main__":
    async def test_chat():
        cli = ClawAIChatCLI()
        print("ClawAI Chat CLI 测试")
        print("输入 'exit' 退出\n")

        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            response = await cli.chat(user_input)
            print(f"\nClawAI: {response}\n")

    asyncio.run(test_chat())
