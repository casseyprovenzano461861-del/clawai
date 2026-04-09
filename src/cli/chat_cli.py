#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawAI 对话式CLI核心模块
实现AI对话交互,意图识别,任务执行
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

from rich.console import Console
from rich.text import Text

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
    pass  # dotenv未安装,使用系统环境变量

try:
    from src.ai_engine.llm_agent.pentest_agent import ClawAIPentestAgent
    AGENT_AVAILABLE = True
except Exception as e:
    AGENT_AVAILABLE = False
    logging.warning(f"ClawAIPentestAgent 导入失败: {e}")

from src.cli.prompts.chat_system import CHAT_SYSTEM_PROMPT, INTENT_PROMPT
from src.cli.config import get_config

try:
    from src.shared.backend.events import EventBus, EventType, Event
    _EVENTBUS_AVAILABLE = True
except ImportError:
    _EVENTBUS_AVAILABLE = False

logger = logging.getLogger(__name__)
console = Console()


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
    # 用户干预历史:记录对话过程中用户发出的控制命令和临时指令
    interventions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str, metadata: Dict = None):
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def add_intervention(
        self,
        itype: str,
        content: str,
        agent_response: str = "",
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """记录一条用户干预

        Args:
            itype: 干预类型,如 "command"(pause/resume/stop)或 "input"(追加指令)
            content: 干预内容
            agent_response: Agent 对本次干预的响应(可为空,事后填写)
            metadata: 额外元数据

        Returns:
            新增的干预记录 dict(可供调用方事后更新 agent_response)
        """
        record: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "type": itype,
            "content": content,
            "agent_response": agent_response,
            "metadata": metadata or {},
        }
        self.interventions.append(record)
        self.updated_at = datetime.now()
        return record


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
        r'(?:目标|target|扫描|scan|测试|test)\s*[::]?\s*(https?://[^\s]+)',
        r'(https?://[^\s]+)',
        r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?::\d+)?)',
        r'(?:目标|target|扫描|scan|测试|test)\s*[::]?\s*([a-zA-Z0-9\-\.]+(?:\.\w+)?)',
        r'([a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+\.\w+)',
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

        # 4. 检查报告意图,同时提取期望格式
        for keyword in self.INTENT_KEYWORDS[Intent.REPORT]:
            if keyword in user_input_lower:
                fmt = "markdown"
                if "json" in user_input_lower:
                    fmt = "json"
                elif "html" in user_input_lower:
                    fmt = "html"
                return Intent.REPORT, {"fmt": fmt}

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

    # 扫描 Profile 配置
    SCAN_PROFILES = {
        "quick": {"max_iterations": 3, "skills": ["nmap", "whatweb"], "label": "快速扫描"},
        "standard": {"max_iterations": 5, "skills": ["nmap", "whatweb", "nuclei", "nikto"], "label": "标准扫描"},
        "deep": {"max_iterations": 10, "skills": ["nmap", "whatweb", "nuclei", "nikto", "sqlmap", "dirsearch"], "label": "深度扫描"},
    }

    def __init__(self, config: Dict[str, Any] = None):
        """初始化

        Args:
            config: 配置字典,包含LLM,代理等配置
        """
        self._cli_config = get_config()
        self.config = config or self._load_default_config()
        self.intent_recognizer = IntentRecognizer()
        self.session = Session(session_id=f"session_{int(time.time())}")
        self.agent = None
        self.running = False
        self._api_key_missing = False

        # 回调函数(旧接口,保持向下兼容)
        self.on_message: Optional[callable] = None
        self.on_tool_execution: Optional[callable] = None
        self.on_status_change: Optional[callable] = None

        # 订阅 EventBus,将事件转发到旧回调
        if _EVENTBUS_AVAILABLE:
            self._subscribe_eventbus()

        # 初始化代理
        self._init_agent()

    def _subscribe_eventbus(self) -> None:
        """订阅 EventBus,将 Agent 事件桥接到旧的回调属性,同时记录用户干预"""
        bus = EventBus.get()

        def _on_message(event: "Event") -> None:
            if self.on_message:
                text = event.data.get("text", "")
                msg_type = event.data.get("type", "info")
                self.on_message(text, msg_type)

        def _on_tool(event: "Event") -> None:
            if self.on_tool_execution:
                self.on_tool_execution(
                    event.data.get("name", ""),
                    event.data.get("status", ""),
                    event.data.get("result"),
                )

        def _on_state(event: "Event") -> None:
            if self.on_status_change:
                self.on_status_change(event.data.get("state", ""), event.data.get("details", ""))

        def _on_user_command(event: "Event") -> None:
            """收到 UI→Agent 命令事件时自动写入干预历史"""
            command = event.data.get("command", "")
            if command:
                self.session.add_intervention("command", command)
                self._autosave()

        def _on_user_input(event: "Event") -> None:
            """收到 UI→Agent 追加指令事件时自动写入干预历史"""
            text = event.data.get("text", "")
            if text:
                self.session.add_intervention("input", text)
                self._autosave()

        bus.subscribe(EventType.MESSAGE, _on_message)
        bus.subscribe(EventType.TOOL, _on_tool)
        bus.subscribe(EventType.STATE_CHANGED, _on_state)
        bus.subscribe(EventType.USER_COMMAND, _on_user_command)
        bus.subscribe(EventType.USER_INPUT, _on_user_input)

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
        except Exception as e:
            logger.debug(f"Failed to load .env: {e}")

        if AGENT_AVAILABLE:
            try:
                # 检查API密钥 — 兼容 dict 和 CLIConfig 两种 config 类型
                if isinstance(self.config, dict):
                    provider = self.config.get("llm", {}).get("provider", "deepseek")
                else:
                    provider = getattr(self.config, 'llm_provider', 'deepseek')

                api_key = os.getenv(f"{provider.upper()}_API_KEY", "")

                if not api_key and provider not in ["local", "mock"]:
                    logger.warning(f"未配置 {provider.upper()}_API_KEY,将使用模拟模式")
                    # 不放弃,而是回退到 mock provider,让 agent 完整初始化
                    if isinstance(self.config, dict):
                        import copy
                        self.config = copy.deepcopy(self.config)
                        self.config["llm"]["provider"] = "mock"
                    else:
                        self.config.set("llm_provider", "mock", persist=False)
                    provider = "mock"
                    self._api_key_missing = True
                else:
                    self._api_key_missing = False

                # 获取 tool_executor_url,兼容 CLIConfig 对象和 dict
                if isinstance(self.config, dict):
                    agent_config = self.config
                    te_url = self.config.get("tool_executor_url", "http://localhost:8082")
                else:
                    # CLIConfig → 转成 dict 给 pentest_agent (它期望 dict)
                    agent_config = {
                        "llm": {
                            "provider": provider,
                            "model_id": getattr(self.config, 'llm_model', 'deepseek-chat'),
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_new_tokens": 1024,
                            "prompt_chaining": True,
                        },
                        "agent": {
                            "new_observation_length_limit": 2000,
                            "timeout_duration": getattr(self.config, 'scan_timeout', 300) // 10,
                            "max_iterations": 10,
                            "use_skills": True,
                            "skill_selection_strategy": "hybrid",
                            "execution_mode": "local",
                        },
                        "per_planner": {"enabled": True, "output_mode": "default"},
                        "planner": {},  # 使用 pentest_agent 内置 prompt
                        "summarizer": {},
                        "skill_mapping": {},
                    }
                    te_url = getattr(self.config, 'tool_executor_url', 'http://localhost:8082')

                self.agent = ClawAIPentestAgent(
                    config=agent_config,
                    tool_executor_url=te_url
                )
                logger.info(f"ClawAIPentestAgent 初始化成功 (provider: {provider})")
            except Exception as e:
                logger.error(f"ClawAIPentestAgent 初始化失败: {e}")
                import traceback
                traceback.print_exc()
                self.agent = None
                self._api_key_missing = False
        else:
            logger.info("AI代理模块不可用,使用模拟模式")
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

        self._streamed = False  # 默认非流式,_general_chat 会设为 True

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
            return "再见!感谢使用 ClawAI."

        elif intent == Intent.HELP:
            return self._get_help_text()

        elif intent == Intent.SCAN:
            target = params.get("target")
            if target:
                self.session.target = target
                self.session.phase = "reconnaissance"
                profile = self._detect_scan_profile(user_input)
                # 用户未明确指定 profile 时,交互式选择
                if profile == "standard" and not any(
                    kw in user_input.lower() for kw in ["快速", "quick", "深度", "deep", "快扫", "全量", "完整", "标准"]
                ):
                    from rich.prompt import Prompt
                    console.print("\n[bold]选择扫描模式:[/]")
                    console.print("  [1] 快速扫描 (3轮: nmap + whatweb)")
                    console.print("  [2] 标准扫描 (5轮: nmap + whatweb + nuclei + nikto) [默认]")
                    console.print("  [3] 深度扫描 (10轮: 全工具)")
                    choice = Prompt.ask("请选择", choices=["1", "2", "3", ""], default="2")
                    profile_map = {"1": "quick", "2": "standard", "3": "deep"}
                    profile = profile_map.get(choice, "standard")
                return await self._execute_scan(target, profile=profile)
            else:
                return "请指定要扫描的目标.例如:扫描 example.com 或 快速扫描 192.168.1.1"

        elif intent == Intent.REPORT:
            return await self._generate_report(fmt=params.get("fmt", "markdown"))

        elif intent == Intent.QUERY:
            return self._get_status()

        elif intent == Intent.ANALYZE:
            return await self._analyze_findings()

        elif intent == Intent.EXPLOIT:
            from rich.prompt import Confirm
            if not Confirm.ask("[bold red]漏洞利用是高危操作,确认继续?[/]"):
                return "已取消漏洞利用操作."
            return await self._execute_exploit(params)

        elif intent == Intent.CONFIG:
            return self._handle_config(params)

        else:  # CHAT or UNKNOWN
            return await self._general_chat(user_input)

    async def _execute_scan(self, target: str, profile: str = "standard") -> str:
        """执行扫描任务,带进度条,暂停支持,EventBus事件和取消支持"""
        from src.cli.scan_state import ScanStateMachine, ScanState
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        from rich.table import Table

        scan = ScanStateMachine()
        self._scan_state = scan  # 暴露给外部 pause/resume 控制
        scan_config = self.SCAN_PROFILES.get(profile, self.SCAN_PROFILES["standard"])
        response_parts = []

        # EventBus: 扫描开始
        self._emit_event("STATE_CHANGED", {"state": "scanning", "target": target, "profile": profile})
        if self.on_status_change:
            self.on_status_change("scanning", f"正在扫描 {target}")

        if not self.agent:
            response_parts.append("\n[模拟模式] 正在执行端口扫描...")
            response_parts.append("\n发现开放端口: 22(SSH), 80(HTTP), 443(HTTPS)")
            response_parts.append("\n建议下一步: 对Web服务进行漏洞扫描")
            self.session.findings.append({"type": "simulated_scan", "target": target, "ports": [22, 80, 443]})
            self._scan_state = None
            return "\n".join(response_parts)

        try:
            if self._api_key_missing:
                console.print("[dim yellow]Mock 模式: 未配置 API Key,使用模拟响应演示完整流程[/]")

            max_iterations = scan_config["max_iterations"]
            scan_skills = scan_config["skills"]
            scan.start(target, max_iterations)

            console.print(f"开始扫描 {target} (最多 {max_iterations} 轮迭代)")
            console.print("按 Ctrl+C 可取消,输入 pause 暂停\n")

            results = {"target": target, "iterations": [], "final_summary": "", "status": "completed"}
            self.agent.reset()

            with Progress(
                SpinnerColumn(style="rgb(0,255,65)"),
                TextColumn("{task.description}", style="rgb(0,255,65)"),
                BarColumn(bar_width=30, style="rgb(0,255,65)", complete_style="rgb(0,255,65)", finished_style="rgb(0,255,65)"),
                TaskProgressColumn(style="rgb(0,255,65)"),
                console=console,
                transient=True,
            ) as progress:
                scan_task = progress.add_task(f"扫描 {target}", total=max_iterations)

                for iteration in range(max_iterations):
                    # 暂停检查
                    while scan.is_paused():
                        progress.update(scan_task, description=f"[暂停中] 输入 resume 继续...")
                        await asyncio.sleep(0.5)

                    # 规划阶段
                    scan.set_iteration(iteration + 1, "规划中")
                    progress.update(scan_task, description=f"[{iteration+1}/{max_iterations}] 规划中...")
                    self._emit_event("PROGRESS", {"iteration": iteration + 1, "phase": "planning"})

                    try:
                        planner_output, _, _ = await asyncio.wait_for(
                            self.agent.planner(target, None, scan_skills),
                            timeout=60,
                        )
                    except asyncio.TimeoutError:
                        console.print(f"[{iteration+1}/{max_iterations}] [dim]规划超时[/]")
                        break
                    except asyncio.CancelledError:
                        console.print(f"[{iteration+1}/{max_iterations}] [yellow]已取消[/]")
                        results["status"] = "cancelled"
                        break

                    command = self.agent.extract_command(planner_output)
                    if not command:
                        console.print(f"[{iteration+1}/{max_iterations}] [dim]无有效命令,结束扫描[/]")
                        break

                    tool_name = self.agent._identify_tool_from_command(command) or "cmd"

                    # 执行阶段
                    scan.set_iteration(iteration + 1, "执行中", tool_name)
                    progress.update(scan_task, description=f"[{iteration+1}/{max_iterations}] 执行 {tool_name}")
                    console.print(f"  [{iteration+1}/{max_iterations}] {tool_name}: {command[:80]}")

                    # EventBus: 工具开始
                    self._emit_tool_event("start", tool_name, {"command": command, "target": target})

                    try:
                        # 增加超时: nmap 等工具可能需要更长时间
                        exec_timeout = 300 if tool_name in ("nmap", "nuclei", "sqlmap", "nikto") else 120
                        command_output, execution_metadata = await asyncio.wait_for(
                            self.agent.execute_command(command, target),
                            timeout=exec_timeout,
                        )
                    except asyncio.TimeoutError:
                        console.print(f"  [yellow]命令执行超时 ({exec_timeout}s)[/]")
                        command_output = "执行超时"
                        execution_metadata = {"error": "timeout"}

                    # 检查工具执行器不可达
                    if execution_metadata.get("error") and "Connection" in str(execution_metadata.get("exception", "")):
                        console.print("  [red]工具执行服务不可达[/]")
                        results["status"] = "tool_executor_unavailable"
                        results["error"] = "工具执行服务不可达"
                        self._emit_tool_event("complete", tool_name, {"error": "unavailable"})
                        break

                    # 高亮关键发现
                    self._highlight_findings(command_output, tool_name)

                    output_preview = command_output[:120].replace("\n", " ").strip()
                    console.print(f"  [dim]{output_preview}[/]")

                    # EventBus: 工具完成
                    self._emit_tool_event("complete", tool_name, {
                        "output_preview": command_output[:200],
                        "success": not execution_metadata.get("error"),
                    })

                    # 更新观察
                    self.agent.new_observation = f"命令: {command}\n输出: {command_output}"
                    if len(self.agent.new_observation) > self.agent.new_observation_length_limit:
                        self.agent.new_observation = self.agent.new_observation[:self.agent.new_observation_length_limit] + " [截断]"

                    # 总结阶段
                    scan.set_iteration(iteration + 1, "总结中")
                    progress.update(scan_task, description=f"[{iteration+1}/{max_iterations}] 总结中")
                    summary, _, _ = await asyncio.to_thread(self.agent.summarizer)

                    # 保存迭代结果
                    results["iterations"].append({
                        "iteration": iteration + 1,
                        "command": command,
                        "command_output": command_output[:500],
                        "execution_metadata": execution_metadata,
                    })

                    self.session.findings.append({
                        "type": "tool_execution",
                        "command": command,
                        "output_preview": command_output[:200],
                    })

                    # 检查是否应该停止
                    try:
                        if self.agent._should_stop_iteration(command_output, summary, iteration):
                            console.print("[green]达到目标,停止扫描[/]")
                            results["status"] = "stopped_early"
                            break
                    except Exception:
                        pass  # _should_stop_iteration 可能不存在或出错

                    progress.advance(scan_task)

            # 最终总结
            results["final_summary"] = self.agent.summarized_history

            scan.transition(
                ScanState.COMPLETED if results["status"] not in ("failed", "tool_executor_unavailable")
                else ScanState.ERROR
            )

            if results.get("status") == "tool_executor_unavailable":
                response_parts.append(f"\n{results.get('error', '工具执行服务不可达')}")
                response_parts.append("\n提示: 请先启动后端服务 → python start.py --backend")
                self._scan_state = None
                return "\n".join(response_parts)

            # 扫描发现 — ASCII hacker 风格
            if self.session.findings:
                _GRN = "rgb(0,255,65)"
                _AMBER = "rgb(255,191,0)"
                _DIM = "rgb(80,110,80)"
                console.print()
                console.print(Text("    -- scan findings " + "-" * 43, style=_DIM))
                for i, f in enumerate(self.session.findings[-10:], 1):
                    ftype = f.get("type", "unknown")
                    detail = f.get("output_preview", f.get("command", ""))[:70]
                    console.print(Text(f"    [{i}] ", style=_DIM), Text(f"{ftype}", style=_AMBER), Text(f"  {detail}", style=""))
                console.print(Text("    " + "-" * 60, style=_DIM))

            response_parts.append(f"\n扫描完成.执行了 {len(results['iterations'])} 个步骤.")
            # 如果 summarizer 输出了有价值的内容，简要展示
            final_summary = results.get("final_summary", "")
            if final_summary and len(final_summary.strip()) > 10:
                # 只取前200字作为摘要，避免输出 LLM 生成的冗长内容
                summary_preview = final_summary.strip()[:200]
                console.print()
                console.print(Text("    -- summary " + "-" * 47, style="rgb(80,110,80)"))
                console.print(Text(f"    {summary_preview}", style="rgb(200,230,200)"))
                console.print(Text("    " + "-" * 60, style="rgb(80,110,80)"))

            # 扫描结果已通过 console.print 直接输出,返回空字符串避免重复显示
            response_parts = []
            self.session.phase = "scanning"
            self._autosave()

        except KeyboardInterrupt:
            console.print("\n扫描已取消")
            response_parts.append("\n扫描已取消.")
        except asyncio.CancelledError:
            response_parts.append("\n扫描已取消.")
        except Exception as e:
            logger.error(f"扫描执行失败: {e}")
            response_parts.append(f"\n扫描执行失败: {str(e)}")
        finally:
            self._scan_state = None

        return "\n".join(response_parts)

    async def _generate_report(self, fmt: str = "markdown") -> str:
        """生成报告并导出到文件"""
        if not self.session.findings:
            return "当前没有发现任何问题.请先执行扫描."

        try:
            from src.cli.exporter import export_session
            path = export_session(self.session, fmt=fmt)
            exported_hint = f"\n\n📄 报告已导出: `{path}`"
        except Exception as e:
            logger.warning(f"导出失败: {e}")
            exported_hint = ""

        report = f"""## 渗透测试报告

**目标**: {self.session.target or '未指定'}
**时间**: {self.session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**阶段**: {self.session.phase}
**发现数**: {len(self.session.findings)}

### 发现的问题

"""
        for i, finding in enumerate(self.session.findings, 1):
            report += f"{i}. {finding.get('type', '未知类型')}\n"
            if finding.get('command'):
                report += f"   命令: {finding['command']}\n"
            if finding.get('output_preview'):
                report += f"   输出: {finding['output_preview'][:100]}...\n"

        report += "\n### 建议\n"
        report += "1. 修复所有发现的安全漏洞\n"
        report += "2. 加强输入验证\n"
        report += "3. 定期进行安全审计\n"

        return report + exported_hint

    def _get_status(self) -> str:
        """获取当前状态"""
        return f"""当前状态:
- 目标: {self.session.target or '未设置'}
- 阶段: {self.session.phase}
- 发现: {len(self.session.findings)} 项
- 消息: {len(self.session.messages)} 条"""

    async def _analyze_findings(self) -> str:
        """AI 分析发现结果"""
        if not self.session.findings:
            return "当前没有发现数据可供分析.请先执行扫描."

        # 构建发现摘要
        findings_summary = "发现列表:\n"
        for i, finding in enumerate(self.session.findings, 1):
            findings_summary += f"{i}. [{finding.get('type', '未知')}] {finding.get('output_preview', finding.get('command', ''))[:100]}\n"

        if self.agent:
            messages = [
                {"role": "system", "content": "你是安全分析专家.根据渗透测试发现,评估风险等级,攻击路径和建议的修复措施.使用中文回复."},
                {"role": "user", "content": f"请分析以下渗透测试发现,给出风险评估和修复建议:\n\n{findings_summary}"},
            ]
            try:
                response, _, _ = await asyncio.to_thread(self.agent.generate_text, messages)
                return response
            except Exception as e:
                logger.error(f"AI 分析失败: {e}")

        # 回退:基础分析
        return findings_summary + "\n提示: 配置 API Key 后可获得 AI 驱动的深度分析"

    async def _execute_exploit(self, params: Dict[str, Any]) -> str:
        """执行漏洞利用(需确认)"""
        if not self.session.findings:
            return "当前没有发现可利用的漏洞.请先执行扫描."

        # 列出已有发现
        lines = ["已有发现,可尝试利用:", ""]
        for i, finding in enumerate(self.session.findings, 1):
            ftype = finding.get('type', '未知')
            preview = finding.get('output_preview', finding.get('command', ''))[:80]
            lines.append(f"  {i}. [{ftype}] {preview}")

        lines.append("")
        lines.append("安全提示: 漏洞利用需要明确授权.仅可在授权范围内执行.")
        lines.append("如需利用特定漏洞,请描述具体目标,例如: 利用 SQL 注入 http://target/page?id=1")

        return "\n".join(lines)

    def _handle_config(self, params: Dict[str, Any]) -> str:
        """处理配置命令"""
        from rich.table import Table

        provider = "mock"
        model_id = "mock-model"
        execution_mode = "local"

        if self.agent:
            provider = self.agent.provider
            model_id = self.agent.model_id
            execution_mode = self.agent.execution_mode

        api_key_status = "已配置" if not self._api_key_missing else "未配置"

        table = Table(title="当前配置", border_style="cyan", show_header=False)
        table.add_column("项", style="bold")
        table.add_column("值")
        table.add_row("LLM 提供商", provider)
        table.add_row("模型", model_id)
        table.add_row("API Key", api_key_status)
        table.add_row("执行模式", f"{execution_mode} (subprocess)")
        table.add_row("扫描深度", "standard")

        console.print(table)

        return "\n提示: 编辑 .env 文件修改配置,或设置环境变量 DEEPSEEK_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY"

    def _detect_scan_profile(self, user_input: str) -> str:
        """从用户输入中检测扫描 profile"""
        text = user_input.lower()
        if any(kw in text for kw in ["快速", "quick", "快扫"]):
            return "quick"
        if any(kw in text for kw in ["深度", "deep", "全量", "完整"]):
            return "deep"
        return "standard"

    async def _general_chat(self, user_input: str) -> str:
        """普通对话（支持工具调用）"""
        # 构建消息历史
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

        # 添加最近的对话历史
        for msg in self.session.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_input})

        if self.agent:
            try:
                # 尝试带工具调用的对话
                if self.agent.llm_client.get("type") in ("openai", "deepseek"):
                    return await self._chat_with_tools(messages)

                # 其他 provider: 流式普通对话
                from src.cli.spinner import AsyncSpinner, SpinnerMode
                from rich.live import Live

                # 阶段1: 显示 spinner 等待 LLM 首个 token
                spinner = AsyncSpinner(console)
                spinner.start(mode=SpinnerMode.REQUESTING)

                full_text = ""
                collected_tokens = []  # 用可变列表供闭包检查

                def _collect_tokens():
                    collected_tokens.extend(self.agent.generate_text_stream(messages))

                with Live(spinner.render_line(), console=console, refresh_per_second=8, vertical_overflow="visible") as live:
                    async def _spin():
                        while not collected_tokens:
                            live.update(spinner.render_line())
                            await asyncio.sleep(0.08)
                    spin_task = asyncio.create_task(_spin())
                    await asyncio.to_thread(_collect_tokens)
                    spin_task.cancel()

                spinner.stop()

                # 阶段2: 输出内容
                if collected_tokens:
                    for token in collected_tokens:
                        console.print(token, end="")
                        full_text += token
                    console.print()

                self._streamed = True
                return full_text
            except Exception as e:
                logger.error(f"LLM生成失败: {type(e).__name__}: {e}")

        # 模拟响应
        self._streamed = False
        return self._generate_mock_response(user_input)

    async def _chat_with_tools(self, messages: List[Dict[str, Any]]) -> str:
        """带工具调用的对话循环

        流程: LLM → tool_calls → 权限检查 → 执行工具 → tool_result → 再次调 LLM → 最终回复
        借鉴 cc-haha 的 query.ts 主循环
        """
        from src.cli.tools import get_tool_registry, ToolResult

        tool_registry = get_tool_registry()
        openai_tools = tool_registry.get_openai_schemas()
        client = self.agent.llm_client["client"]
        model_id = self.agent.model_id

        max_tool_rounds = 5  # 防止无限工具调用
        full_response = ""
        self._streamed = True

        for round_num in range(max_tool_rounds):
            # 流式调用 LLM (始终提供 tools,让 LLM 自行决定是否调用)
            try:
                stream = await asyncio.to_thread(
                    lambda: client.chat.completions.create(
                        model=model_id,
                        messages=messages,
                        tools=openai_tools,
                        temperature=self.agent.temperature,
                        max_tokens=self.agent.max_new_tokens,
                        stream=True,
                    )
                )
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                return f"AI 响应失败: {e}"

            # 流式输出文本 + 收集 tool_calls 增量
            # 阶段1: spinner 等待 → 阶段2: 纯文本流式输出
            from rich.live import Live
            from src.cli.spinner import AsyncSpinner, SpinnerMode

            text_parts: List[str] = []
            tool_calls_map: Dict[int, Dict] = {}  # index → {id, name, arguments}
            spinner_done = False

            # Spinner 阶段: 等待首个 token
            spinner = AsyncSpinner(console)
            spinner.start(mode=SpinnerMode.REQUESTING)

            with Live(spinner.render_line(), console=console, refresh_per_second=8, vertical_overflow="visible") as live:
                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue
                    if delta.content:
                        if not spinner_done:
                            # 第一个 token → 停止 spinner, 切换到文本流
                            spinner.stop()
                            spinner_done = True
                            live_text = Text("  > ", style="rgb(0,255,65)")
                        text_parts.append(delta.content)
                        live_text.append(delta.content)
                        live.update(live_text)
                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in tool_calls_map:
                                tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc_delta.id:
                                tool_calls_map[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls_map[idx]["name"] = tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls_map[idx]["arguments"] += tc_delta.function.arguments

            if not spinner_done:
                spinner.stop()

            # 如果没有工具调用,返回最终文本
            assistant_content = "".join(text_parts)
            if not tool_calls_map:
                if assistant_content:
                    console.print()
                return assistant_content

            # 有工具调用 — 显示 LLM 的文本部分
            if assistant_content:
                console.print()

            # 构造 assistant 消息 (含 tool_calls)
            tool_calls_list = []
            for idx in sorted(tool_calls_map.keys()):
                tc_info = tool_calls_map[idx]
                tool_calls_list.append({
                    "id": tc_info["id"],
                    "type": "function",
                    "function": {"name": tc_info["name"], "arguments": tc_info["arguments"]},
                })

            msg_dict = {"role": "assistant", "content": assistant_content or None}
            if tool_calls_list:
                msg_dict["tool_calls"] = tool_calls_list
            messages.append(msg_dict)

            # 逐个执行工具调用
            for tc_info in tool_calls_list:
                tool_name = tc_info["function"]["name"]
                tool_args_str = tc_info["function"]["arguments"]
                call_id = tc_info["id"]

                import json
                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                tool_def = tool_registry.lookup(tool_name)
                if not tool_def:
                    console.print(f"[red]未知工具: {tool_name}[/]")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": f"错误: 未知工具 {tool_name}",
                    })
                    continue

                # ── 权限检查 (黑客终端风格) ──
                if tool_def.is_dangerous:
                    display = tool_def.format_call_display(tool_args)
                    _GRN = "rgb(0,255,65)"
                    _AMBER = "rgb(255,191,0)"
                    _RED = "rgb(255,60,60)"
                    _DIM = "rgb(80,110,80)"
                    console.print(Text(f"    [!] DANGEROUS: ", style=_AMBER), Text(display, style=f"bold {_RED}"))
                    from rich.prompt import Confirm, Prompt
                    action = Prompt.ask(
                        "    execute?",
                        choices=["y", "n", "e"],
                        default="y",
                    )
                    if action == "n":
                        console.print(Text("    [-] rejected", style=_DIM))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": "用户拒绝了此工具调用",
                        })
                        continue
                    elif action == "e":
                        if tool_name == "bash":
                            new_cmd = Prompt.ask("    edit command", default=tool_args.get("command", ""))
                            tool_args["command"] = new_cmd
                        else:
                            console.print(Text("    [-] this tool cannot be edited", style=_DIM))

                # ── 执行工具 ──
                display = tool_def.format_call_display(tool_args)
                console.print(Text("    [+] ", style=_GRN), Text(display, style=""))

                # EventBus 通知
                if _EVENTBUS_AVAILABLE:
                    try:
                        bus = EventBus.get()
                        bus.emit_tool("start", tool_name, args=tool_args)
                    except Exception:
                        pass

                # 实时输出显示: Spinner → 纯输出
                from rich.live import Live
                from src.cli.spinner import AsyncSpinner, SpinnerMode

                tool_spinner = AsyncSpinner(console)
                tool_spinner.start(mode=SpinnerMode.TOOL_USE, verb=f"▶ {tool_name}")
                live_output = Text()
                output_started = False

                with Live(tool_spinner.render_line(), console=console, refresh_per_second=8, vertical_overflow="visible") as live:
                    def on_output(line: str):
                        nonlocal output_started
                        if not output_started:
                            tool_spinner.stop()
                            output_started = True
                        live_output.append(line + "\n")
                        live.update(live_output)

                    result: ToolResult = await tool_def.execute(tool_args, on_output=on_output)

                if not output_started:
                    tool_spinner.stop()

                # 结果
                _GRN = "rgb(0,255,65)"
                _RED = "rgb(255,60,60)"
                _DIM = "rgb(80,110,80)"
                if result.success:
                    console.print(Text(f"    [+] done {result.duration:.1f}s", style=_GRN))
                else:
                    console.print(Text(f"    [-] {result.error} ({result.duration:.1f}s)", style=_RED))

                # EventBus 通知
                if _EVENTBUS_AVAILABLE:
                    try:
                        bus = EventBus.get()
                        bus.emit_tool("complete", tool_name, result=result.to_dict())
                    except Exception:
                        pass

                # 记录发现
                if result.success and result.output:
                    self.session.findings.append({
                        "type": f"tool:{tool_name}",
                        "output_preview": result.output[:200],
                    })

                # 将 tool_result 加入历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result.to_text()[:4000],  # 截断防止超长
                })

            # 继续循环 — 将工具结果发回 LLM, 让它决定下一步

        # 超过最大轮数
        return "工具调用轮次已达上限,请继续描述你的需求。"

    def _generate_mock_response(self, user_input: str) -> str:
        """生成模拟响应"""
        if "你好" in user_input or "hello" in user_input.lower():
            return "你好!我是 ClawAI 渗透测试助手.我可以帮助你进行安全测试.请告诉我你要测试的目标."
        elif "什么" in user_input or "what" in user_input.lower():
            return "我是 ClawAI,一个专业的渗透测试AI助手.我可以执行端口扫描,漏洞检测,安全分析等任务."
        else:
            return "我理解了你的请求.请问你想对哪个目标进行测试?或者输入'帮助'查看我能做什么."

    def _get_help_text(self) -> str:
        """黑客终端风格帮助"""
        _GRN = "rgb(0,255,65)"
        _AMBER = "rgb(255,191,0)"
        _DIM = "rgb(80,110,80)"
        _MAG = "rgb(255,0,255)"

        console.print(Text("    -- help ----------------------------------------", style=_DIM))

        # 自然语言
        console.print(Text("    natural language:", style=_GRN))
        for cmd, desc in [
            ("scan <target>", "standard scan (5 rounds)"),
            ("quick scan <target>", "quick scan (3 rounds)"),
            ("deep scan <target>", "deep scan (10 rounds)"),
            ("analyze", "AI analysis of findings"),
            ("report", "generate report"),
        ]:
            console.print(Text(f"      {cmd}", style=_GRN), Text(f" -- {desc}", style=_DIM))

        console.print()
        # 工具命令
        console.print(Text("    tool commands:", style=_AMBER))
        for cmd, desc, warn in [
            ("/nmap <target>", "port scan", False),
            ("/nuclei <target>", "vuln scan", False),
            ("/sqlmap <url>", "SQL injection", True),
            ("/whatweb <target>", "web fingerprint", False),
            ("/bash <cmd>", "shell command", True),
            ("/grep <pattern>", "text search", False),
        ]:
            style = _AMBER if not warn else "rgb(255,60,60)"
            console.print(Text(f"      {cmd}", style=style), Text(f" -- {desc}", style=_DIM))

        console.print()
        # 控制
        console.print(Text("    control:", style=_MAG))
        for cmd, desc in [
            ("/pause | /resume | /stop", "scan control"),
            ("/session list", "session list"),
            ("/help", "this help"),
            ("/exit", "exit"),
            ("!command", "bash"),
        ]:
            console.print(Text(f"      {cmd}", style=_MAG), Text(f" -- {desc}", style=_DIM))

        console.print(Text("    -----------------------------------------------", style=_DIM))

        if self._api_key_missing:
            console.print(Text("    [!] MOCK MODE -- no API key configured", style=_AMBER))
            console.print(Text("        set DEEPSEEK_API_KEY in .env", style=_DIM))

        console.print()
        return ""

    def set_target(self, target: str):
        """设置目标"""
        self.session.target = target
        self.session.phase = "initialized"

    def record_intervention(
        self,
        itype: str,
        content: str,
        agent_response: str = "",
        metadata: Dict = None,
    ) -> Dict[str, Any]:
        """记录用户干预并自动保存会话

        供主循环在用户输入控制命令时直接调用.
        同时通过 EventBus 广播,让其他订阅者(TUI 等)也能感知.

        Args:
            itype: "command"(pause/resume/stop)或 "input"(追加指令)
            content: 干预内容
            agent_response: Agent 的响应(可事后更新)
            metadata: 额外元数据

        Returns:
            新增的干预记录 dict
        """
        record = self.session.add_intervention(itype, content, agent_response, metadata)
        self._autosave()
        # 同步广播到 EventBus,让其他订阅者感知
        if _EVENTBUS_AVAILABLE:
            bus = EventBus.get()
            if itype == "command":
                bus.emit_command(content)
            else:
                bus.emit_input(content)
        return record

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

    # ------------------------------------------------------------------
    # 会话持久化
    # ------------------------------------------------------------------

    def _emit_event(self, event_type_str: str, data: Dict[str, Any]) -> None:
        """安全发送 EventBus 事件"""
        if not _EVENTBUS_AVAILABLE:
            return
        try:
            bus = EventBus.get()
            event_type = getattr(EventType, event_type_str, None)
            if event_type:
                bus.emit(event_type, data)
        except Exception:
            pass

    def _emit_tool_event(self, status: str, tool_name: str, extra: Dict = None) -> None:
        """安全发送 TOOL 事件"""
        if not _EVENTBUS_AVAILABLE:
            return
        try:
            bus = EventBus.get()
            bus.emit_tool(status, tool_name, **(extra or {}))
        except Exception:
            pass

    def _highlight_findings(self, output: str, tool_name: str) -> None:
        """关键发现高亮 — 黑客终端风格"""
        import re
        _GRN = "rgb(0,255,65)"
        _RED = "rgb(255,60,60)"
        _AMBER = "rgb(255,191,0)"
        _DIM = "rgb(80,110,80)"

        if tool_name in ("nmap",) and "open" in output.lower():
            open_ports = re.findall(r'(\d+)/(?:tcp|udp)\s+open\s+(\S+)', output)
            if open_ports:
                ports_str = " | ".join(f"{p}/{s}" for p, s in open_ports[:10])
                console.print(Text(f"    [+] OPEN PORTS: ", style=_GRN), Text(ports_str, style=f"bold {_GRN}"))
                self._emit_event("FINDING", {
                    "type": "open_ports", "tool": tool_name,
                    "ports": [f"{p}/{s}" for p, s in open_ports],
                })

        if tool_name in ("nuclei",) and ("vulnerability" in output.lower() or "found" in output.lower()):
            vulns = re.findall(r'\[([^\]]+)\]\s+\[([^\]]+)\]\s+(.+?)(?:\n|$)', output)
            if vulns:
                for severity, template, detail in vulns[:5]:
                    color = {
                        "critical": _RED, "high": _RED,
                        "medium": _AMBER, "low": _GRN,
                        "info": _DIM,
                    }.get(severity.lower(), "white")
                    console.print(Text(f"    [!] [{severity}] {detail[:80]}", style=f"bold {color}"))
                self._emit_event("FINDING", {
                    "type": "vulnerability", "tool": tool_name, "count": len(vulns),
                })

        if tool_name in ("sqlmap",) and ("injectable" in output.lower() or "vulnerable" in output.lower()):
            console.print(Text("    [!] SQL INJECTION CONFIRMED", style=f"bold {_RED}"))
            self._emit_event("FINDING", {
                "type": "sql_injection", "tool": tool_name, "severity": "critical",
            })

    def _autosave(self):
        """在关键操作后自动保存会话"""
        try:
            from src.cli.session_store import SessionStore
            SessionStore().save(self.session)
        except Exception as e:
            logger.debug(f"会话自动保存失败(非致命): {e}")

    def save_session(self) -> bool:
        """手动保存当前会话,返回是否成功"""
        try:
            from src.cli.session_store import SessionStore
            return SessionStore().save(self.session)
        except Exception as e:
            logger.error(f"会话保存失败: {e}")
            return False

    def load_session(self, session_id: str) -> bool:
        """从持久化存储加载会话,返回是否成功"""
        try:
            from src.cli.session_store import SessionStore
            session = SessionStore().load_as_session(session_id)
            if session is not None:
                self.session = session
                logger.info(f"已加载会话: {session_id}")
                return True
        except Exception as e:
            logger.error(f"会话加载失败: {e}")
        return False

    @staticmethod
    def list_saved_sessions() -> List[Dict[str, Any]]:
        """返回所有已保存的会话摘要"""
        try:
            from src.cli.session_store import SessionStore
            return SessionStore().list_sessions()
        except Exception:
            return []


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
