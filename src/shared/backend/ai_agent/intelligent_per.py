# -*- coding: utf-8 -*-
"""
真正的 P-E-R 自主模式（增强版）
AI 自己规划、执行、反思整个渗透测试流程

特点:
- Planner: AI 分析目标，生成执行计划（RAG增强、预算检查）
- Executor: AI 选择工具，执行扫描（工具知识查询）
- Reflector: AI 分析结果，决定下一步（漏洞利用知识、缺口重分析）
- 完全自主，深度集成智能特性
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# 延迟导入，避免循环依赖
_budget_manager_module = None

def _get_budget_phase():
    """延迟获取 BudgetPhase"""
    global _budget_manager_module
    if _budget_manager_module is None:
        try:
            from .budget_manager import BudgetPhase
            _budget_manager_module = BudgetPhase
        except ImportError:
            _budget_manager_module = None
    return _budget_manager_module


# 延迟导入 Skills 库
_skill_registry = None

def _get_skill_registry():
    """延迟获取 SkillRegistry"""
    global _skill_registry
    if _skill_registry is None:
        try:
            from ..skills import get_skill_registry
            _skill_registry = get_skill_registry()
        except ImportError:
            pass
    return _skill_registry


def _get_fingerprint_matches(findings: List[dict], target: str) -> list:
    """调用 fingerprint.py 的指纹匹配，返回 MatchResult 列表"""
    try:
        from ..skills.fingerprint import match_findings
        return match_findings(findings, base_target=target)
    except Exception as e:
        logger.debug(f"fingerprint match_findings 调用失败: {e}")
        return []


class PERPhase(Enum):
    """P-E-R 阶段"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """执行任务"""
    id: str
    name: str
    tool: str
    params: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Optional[Dict[str, Any]] = None
    priority: int = 0


@dataclass
class PERContext:
    """P-E-R 执行上下文"""
    target: str = ""
    goal: str = ""
    phase: PERPhase = PERPhase.IDLE
    iteration: int = 0
    max_iterations: int = 5
    
    # 计划
    plan: List[Task] = field(default_factory=list)
    current_task_index: int = 0
    
    # 收集的信息
    collected_info: Dict[str, Any] = field(default_factory=dict)
    
    # 发现的问题
    findings: List[Dict[str, Any]] = field(default_factory=list)
    
    # 执行历史
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 智能特性状态
    rag_queries: int = 0
    budget_used: int = 0


class IntelligentPERAgent:
    """智能 P-E-R Agent（增强版）
    
    完全由 LLM 驱动的自主渗透测试 Agent
    深度集成：RAG知识增强、Token预算管理、上下文缺口分析
    """
    
    def __init__(
        self,
        llm_client,
        tool_executor,
        context_analyzer=None,
        rag_client=None,
        budget_manager=None,
        max_iterations: int = 5
    ):
        """初始化
        
        Args:
            llm_client: LLM 客户端（AIAgentCore）
            tool_executor: 工具执行器
            context_analyzer: 上下文缺口分析器
            rag_client: RAG 知识服务客户端
            budget_manager: Token 预算管理器
            max_iterations: 最大迭代次数
        """
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.context_analyzer = context_analyzer
        self.rag_client = rag_client
        self.budget_manager = budget_manager
        self.max_iterations = max_iterations
        
        # 执行上下文
        self.ctx = PERContext(max_iterations=max_iterations)
        
        # 工具定义
        self.tools = self._get_tool_definitions()
        
        logger.info("IntelligentPERAgent (增强版) 初始化完成")
    
    # 所有工具定义（含描述），运行时按可用性过滤
    _ALL_TOOL_DEFS = [
        {"name": "nmap_scan",      "description": "端口扫描，发现开放端口和服务",     "category": "recon"},
        {"name": "whatweb_scan",   "description": "Web技术栈识别",                   "category": "recon"},
        {"name": "nuclei_scan",    "description": "基于模板的漏洞扫描",               "category": "vuln"},
        {"name": "sqlmap_scan",    "description": "SQL注入检测和利用",               "category": "vuln"},
        {"name": "nikto_scan",     "description": "Web服务器漏洞扫描",               "category": "vuln"},
        {"name": "dirsearch_scan", "description": "目录和文件爆破",                   "category": "recon"},
        {"name": "httpx_probe",    "description": "HTTP服务探测",                    "category": "recon"},
        {"name": "xsstrike_scan",  "description": "XSS漏洞检测",                     "category": "vuln"},
        {"name": "commix_scan",    "description": "命令注入检测",                     "category": "vuln"},
        {"name": "subfinder_scan", "description": "子域名发现",                       "category": "recon"},
    ]

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义，只保留真实可用的工具 + 所有技能"""
        # 获取可用工具集合
        available_set = set()
        try:
            from ..tools.unified_executor_final import UnifiedExecutor
            ex = UnifiedExecutor()
            avail_map = ex._check_tool_availability()
            available_set = {k for k, v in avail_map.items() if v}
        except Exception:
            pass

        # 工具名到 executor key 的映射
        tool_name_map = {
            "nmap_scan": "nmap",
            "whatweb_scan": "whatweb",
            "nuclei_scan": "nuclei",
            "sqlmap_scan": "sqlmap",
            "nikto_scan": "nikto",
            "dirsearch_scan": "dirsearch",
            "httpx_probe": "httpx",
            "xsstrike_scan": "xsstrike",
            "commix_scan": "commix",
            "subfinder_scan": "subfinder",
        }

        tools = [
            t for t in self._ALL_TOOL_DEFS
            if tool_name_map.get(t["name"], t["name"]) in available_set
        ]
        
        # 添加技能作为工具
        registry = _get_skill_registry()
        if registry:
            for skill in registry.list():
                tools.append({
                    "name": f"skill_{skill.id}",
                    "description": f"[SKILL][{skill.severity.upper()}] {skill.description}",
                    "category": skill.category.value,
                    "is_skill": True,
                    "skill_id": skill.id
                })
        
        return tools
    
    # ==================== 核心流程 ====================
    
    async def run(
        self,
        target: str,
        goal: str = None,
        mode: str = "full"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """运行自主渗透测试
        
        Args:
            target: 目标地址
            goal: 测试目标描述
            mode: 测试模式 (recon/vuln/full)
            
        Yields:
            执行事件
        """
        # 初始化上下文
        self.ctx = PERContext(
            target=target,
            goal=goal or f"对 {target} 进行安全评估",
            max_iterations=self.max_iterations
        )
        
        # 初始化预算管理器阶段
        if self.budget_manager:
            BudgetPhase = _get_budget_phase()
            if BudgetPhase:
                self.budget_manager.set_phase(BudgetPhase.RECONNAISSANCE)
        
        yield {
            "type": "start",
            "target": target,
            "goal": self.ctx.goal,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
            "features": {
                "rag_enabled": self.rag_client is not None,
                "budget_enabled": self.budget_manager is not None,
                "gap_analysis_enabled": self.context_analyzer is not None
            }
        }
        
        try:
            # P-E-R 循环
            while self.ctx.iteration < self.ctx.max_iterations:
                self.ctx.iteration += 1
                
                yield {"type": "iteration", "num": self.ctx.iteration, "max": self.ctx.max_iterations}
                
                # === PLANNER 阶段 ===
                self.ctx.phase = PERPhase.PLANNING
                yield {"type": "phase", "phase": "planning", "message": "AI 正在分析目标并生成计划..."}

                # 带心跳的 plan（防止 LLM 响应慢导致前端误判卡死）
                plan_task = asyncio.ensure_future(self._plan())
                plan_elapsed = 0
                while not plan_task.done():
                    await asyncio.sleep(8)
                    plan_elapsed += 8
                    if not plan_task.done():
                        yield {
                            "type": "message",
                            "text": f"AI 规划中… ({plan_elapsed}s)",
                            "msg_type": "info",
                        }
                if plan_task.cancelled():
                    plan_result = {"tasks": 0, "rag_context_used": False, "gaps_identified": 0}
                elif plan_task.exception() is not None:
                    logger.error(f"_plan 异常: {plan_task.exception()}")
                    plan_result = {"tasks": 0, "rag_context_used": False, "gaps_identified": 0}
                else:
                    plan_result = plan_task.result()

                yield {
                    "type": "plan", 
                    "tasks": [t.name for t in self.ctx.plan],
                    "rag_used": plan_result.get("rag_context_used", False),
                    "gaps_identified": plan_result.get("gaps_identified", 0)
                }
                
                # === EXECUTOR 阶段 ===
                self.ctx.phase = PERPhase.EXECUTING

                # 如果计划为空（所有工具都已执行），直接结束
                if not self.ctx.plan:
                    logger.info("计划为空（所有工具均已执行），提前结束循环")
                    self.ctx.phase = PERPhase.COMPLETED
                    break

                for i, task in enumerate(self.ctx.plan):
                    if task.status == "completed":
                        continue
                    
                    self.ctx.current_task_index = i
                    yield {"type": "task_start", "task": task.name, "index": i}
                    
                    # 执行任务（带心跳：每 8 秒推送一条进度消息，避免前端误判卡死）
                    async def _run_task_with_heartbeat(task=task):
                        return await self._execute_task(task)

                    task_coro = asyncio.ensure_future(_run_task_with_heartbeat())
                    elapsed = 0
                    while not task_coro.done():
                        await asyncio.sleep(8)
                        elapsed += 8
                        if not task_coro.done():
                            yield {
                                "type": "message",
                                "text": f"{task.name} 运行中… ({elapsed}s)",
                                "msg_type": "info",
                            }
                    if task_coro.cancelled():
                        result = {"success": False, "error": "cancelled"}
                    elif task_coro.exception() is not None:
                        result = {"success": False, "error": str(task_coro.exception())}
                    else:
                        result = task_coro.result()
                    
                    yield {
                        "type": "task_result",
                        "task": task.name,
                        "success": result.get("success", False),
                        "simulated": result.get("simulated", True),
                        "findings": self._extract_findings(result)
                    }
                    
                    # 更新收集的信息
                    self._update_collected_info(task, result)

                    # WordPress 检测 → 自动触发 wordpress_rce skill
                    if task.tool in ("nmap_scan", "whatweb_scan", "nikto_scan", "dirsearch_scan"):
                        await self._auto_detect_wordpress_per(task, result)
                
                # === 指纹分发：每轮执行完后，根据已知 findings 自动触发 CVE Skill ===
                fp_events = await self._run_fingerprint_dispatch()
                for ev in fp_events:
                    yield ev

                # === REFLECTOR 阶段 ===
                self.ctx.phase = PERPhase.REFLECTING
                yield {"type": "phase", "phase": "reflecting", "message": "AI 正在分析结果..."}

                # 带心跳的 reflect（同执行阶段，防止 LLM 阻塞导致前端卡住）
                reflect_task = asyncio.ensure_future(self._reflect())
                reflect_elapsed = 0
                while not reflect_task.done():
                    await asyncio.sleep(8)
                    reflect_elapsed += 8
                    if not reflect_task.done():
                        yield {
                            "type": "message",
                            "text": f"AI 反思分析中… ({reflect_elapsed}s)",
                            "msg_type": "info",
                        }
                if reflect_task.cancelled():
                    reflection = {"summary": "", "goal_achieved": False, "need_more_work": False, "new_gaps": 0, "exploit_knowledge_used": False}
                elif reflect_task.exception() is not None:
                    logger.error(f"_reflect 异常: {reflect_task.exception()}")
                    reflection = {"summary": "", "goal_achieved": False, "need_more_work": False, "new_gaps": 0, "exploit_knowledge_used": False}
                else:
                    reflection = reflect_task.result()

                yield {
                    "type": "reflection", 
                    "summary": reflection.get("summary", ""),
                    "exploit_knowledge_used": reflection.get("exploit_knowledge_used", False),
                    "new_gaps": reflection.get("new_gaps", 0)
                }
                
                # 检查是否完成
                if reflection.get("goal_achieved"):
                    self.ctx.phase = PERPhase.COMPLETED
                    break
                
                # 检查是否需要更多迭代
                if not reflection.get("need_more_work"):
                    self.ctx.phase = PERPhase.COMPLETED
                    break
        
        except Exception as e:
            logger.error(f"P-E-R 执行失败: {e}")
            self.ctx.phase = PERPhase.FAILED
            yield {"type": "error", "message": str(e)}
        
        # 生成最终报告
        self.ctx.phase = PERPhase.COMPLETED
        report = self._generate_report()
        
        # 获取预算摘要
        budget_summary = None
        if self.budget_manager:
            budget_summary = self.budget_manager.get_summary()
        
        yield {
            "type": "complete",
            "success": self.ctx.phase == PERPhase.COMPLETED,
            "iterations": self.ctx.iteration,
            "findings_count": len(self.ctx.findings),
            "rag_queries": self.ctx.rag_queries,
            "budget_used": self.ctx.budget_used,
            "budget_summary": budget_summary,
            "report": report
        }
    
    # ==================== PLANNER ====================
    
    async def _plan(self) -> Dict[str, Any]:
        """AI 规划执行任务（增强版）
        
        集成：
        - Token 预算检查
        - RAG 知识增强
        - 上下文缺口分析
        """
        
        # 1. 检查 Token 预算
        budget_status = None
        if self.budget_manager:
            remaining = self.budget_manager.get_remaining_budget()
            budget_status = self.budget_manager.get_summary()
            
            if remaining < 1000:
                logger.warning(f"Token 预算不足: 剩余 {remaining}")
                # 使用精简规划——选一个未执行过的工具，避免无限重复
                executed_tasks = {t['task'] for t in self.ctx.history}
                fallback_tool = None
                # 优先选未执行的普通工具，其次技能
                for candidate in ["nmap_scan", "nikto_scan", "gobuster_scan"]:
                    if candidate not in executed_tasks:
                        fallback_tool = candidate
                        break
                if not fallback_tool:
                    # 全部正常工具都执行过了，尝试技能
                    skill_candidates = [t["name"] for t in self.tools if t["name"] not in executed_tasks]
                    fallback_tool = skill_candidates[0] if skill_candidates else None
                if fallback_tool:
                    self.ctx.plan = [
                        Task(
                            id=f"minimal_{self.ctx.iteration}",
                            name=fallback_tool,
                            tool=fallback_tool,
                            params={"target": self.ctx.target},
                            priority=0
                        )
                    ]
                    return {"tasks": 1, "budget_limited": True}
                else:
                    # 所有工具都执行过了，直接结束
                    self.ctx.plan = []
                    return {"tasks": 0, "budget_limited": True, "all_done": True}
        
        # 2. 获取 RAG 上下文（增强规划）
        rag_context = ""
        rag_results = []
        if self.rag_client:
            try:
                # 查询相关的渗透测试方法
                rag_results = await self.rag_client.search(
                    query=f"如何对 {self.ctx.target} 进行渗透测试",
                    top_k=3,
                    category_filter="tool_guide"
                )
                if rag_results:
                    rag_context = "\n".join([
                        f"- {r.title}: {r.content[:200]}..."
                        for r in rag_results[:3]
                    ])
                    self.ctx.rag_queries += 1
                    logger.info(f"RAG 检索到 {len(rag_results)} 条相关知识")
            except Exception as e:
                logger.warning(f"RAG 检索失败: {e}")
        
        # 3. 分析上下文缺口
        gaps = []
        gap_result = None
        if self.context_analyzer:
            try:
                gap_result = self.context_analyzer.analyze(
                    user_input=self.ctx.goal,
                    context=self.ctx.collected_info,
                    task_phase=f"iteration_{self.ctx.iteration}"
                )
                gaps = gap_result.gaps if hasattr(gap_result, 'gaps') else []
                
                # 记录缺口分析结果
                if hasattr(gap_result, 'summary'):
                    logger.info(f"缺口分析: {gap_result.summary[:100]}")
            except Exception as e:
                logger.warning(f"上下文缺口分析失败: {e}")
        
        # 4. 构建增强的 Planner 提示词
        prompt = self._build_enhanced_planner_prompt(gaps, rag_context, budget_status)
        
        # 5. 调用 LLM 生成计划
        messages = [
            {"role": "system", "content": self._get_planner_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: self.llm_client.chat(messages, tools=self._get_tools_schema())),
            timeout=60
        )
        
        # 6. 记录 Token 消耗
        if self.budget_manager and hasattr(response, 'usage'):
            BudgetPhase = _get_budget_phase()
            if BudgetPhase:
                tokens_used = (
                    getattr(response.usage, 'prompt_tokens', 0) +
                    getattr(response.usage, 'completion_tokens', 0)
                )
                self.ctx.budget_used += tokens_used
                tool_calls_count = len(response.tool_calls) if (hasattr(response, 'tool_calls') and response.tool_calls) else 0
                self.budget_manager.record_usage(
                    input_tokens=getattr(response.usage, 'prompt_tokens', 0),
                    output_tokens=getattr(response.usage, 'completion_tokens', 0),
                    phase=BudgetPhase.RECONNAISSANCE,
                    tool_calls=tool_calls_count
                )
        
        # 7. 解析计划
        self.ctx.plan = self._parse_plan(response)
        
        return {
            "tasks": len(self.ctx.plan),
            "rag_context_used": len(rag_results) > 0,
            "gaps_identified": len(gaps)
        }
    
    def _build_enhanced_planner_prompt(
        self, 
        gaps: List, 
        rag_context: str,
        budget_status: Optional[Dict] = None
    ) -> str:
        """构建增强的 Planner 提示词（包含 RAG 上下文和技能）"""
        target = self.ctx.target
        iteration = self.ctx.iteration
        # 只保留最关键字段，压缩 prompt 大小避免 LLM 超时
        _ci = self.ctx.collected_info
        collected_slim = {
            "open_ports": _ci.get("open_ports", [])[:10],
            "services": _ci.get("services", {"http": True} if 80 in _ci.get("open_ports", []) else {}),
            "os": _ci.get("os", ""),
            "web_paths": _ci.get("web_paths", [])[:5],
        }
        collected = json.dumps(collected_slim, ensure_ascii=False)[:800]
        
        # 安全地序列化 gaps
        gaps_data = []
        for g in gaps:
            if hasattr(g, '__dict__'):
                gap_dict = {}
                for k, v in g.__dict__.items():
                    if hasattr(v, 'value'):  # Enum
                        gap_dict[k] = v.value
                    else:
                        gap_dict[k] = v
                gaps_data.append(gap_dict)
            else:
                gaps_data.append(str(g))
        
        # 构建预算提示
        budget_hint = ""
        if budget_status:
            remaining = budget_status.get("total_remaining", 0)
            utilization = budget_status.get("utilization_rate", 0) * 100
            budget_hint = f"\n**预算状态**: 剩余 {remaining} tokens ({utilization:.1f}% 已使用)"
        
        # 构建 RAG 上下文提示
        rag_hint = ""
        if rag_context:
            rag_hint = f"\n## 相关知识（来自知识库）\n{rag_context}\n"
        
        # 分离工具和技能（只取未执行过的，减少 prompt 体积）
        executed = {h['task'] for h in self.ctx.history}
        regular_tools = [t for t in self.tools if not t.get("is_skill") and t['name'] not in executed]
        skill_tools = [t for t in self.tools if t.get("is_skill") and t['name'] not in executed]
        
        # 构建技能列表（只列前 8 个未执行技能）
        skills_hint = ""
        if skill_tools:
            skills_list = "\n".join([
                f"- {s['name']}: {s['description']}" 
                for s in skill_tools[:8]
            ])
            skills_hint = f"""
## 可用技能（POC/Exploit，未执行）
{skills_list}

使用技能时，直接调用 skill_xxx，参数会自动填充。
"""
        
        prompt = f"""
## 当前状态
- 目标: {target}
- 迭代: {iteration}/{self.ctx.max_iterations}
- 已收集信息: {collected if collected != '{}' else '无'}{budget_hint}
- 已执行任务（**严禁重复**）: {', '.join(list({t['task'] for t in self.ctx.history})) or '无'}
- 剩余未执行工具数: {len([t for t in self.tools if t['name'] not in {h['task'] for h in self.ctx.history}])}

## 信息缺口
{json.dumps(gaps_data, ensure_ascii=False, indent=2) if gaps_data else '需要发现目标的开放端口和服务'}
{rag_hint}
## 可用工具（未执行）
{', '.join(t['name'] for t in regular_tools) or '（已全部执行）'}
{skills_hint}
## 任务
**重要：目标是 {target}，必须扫描这个目标！**

选择 1-2 个**严格未执行过**的任务（target 必须是 {target}）：
1. 第一次迭代：执行 nmap_scan
2. 已执行 nmap_scan：选技能检测目标 {target}（注意端口，如目标含端口号则优先测该端口）
3. 已失败的技能：**绝对不选**，换其他种类
4. 发现漏洞后：停止，不要继续
5. target 参数**必须**填写 {target}（不要改成 localhost 或其他地址）

⚠️ 警告：返回已在「已执行任务」列表中的任何任务将被系统自动丢弃，视为无效计划。

请以 JSON 格式返回计划:
{{
    "reasoning": "为什么选择这些任务",
    "tasks": [
        {{"tool": "nmap_scan", "params": {{"target": "{target}", "ports": "22,80,443"}}, "reason": "发现开放端口"}}
    ]
}}
"""
        return prompt
    
    def _get_planner_system_prompt(self) -> str:
        """Planner 系统提示词（动态注入可用工具列表）"""
        # 只列出真实可用的普通工具
        regular_tools = [t["name"] for t in self.tools if not t.get("is_skill")]
        tools_str = ", ".join(regular_tools) if regular_tools else "（无可用工具）"

        return f"""你是渗透测试规划专家。分析信息、选择未执行的工具、返回JSON计划。
可用扫描工具: {tools_str}
规则: 不重复执行已失败任务；每次选1-2个未执行任务；返回JSON格式。"""
    
    def _parse_plan(self, response) -> List[Task]:
        """解析 LLM 返回的计划"""
        tasks = []
        
        # 从 response 中提取工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for i, tc in enumerate(response.tool_calls):
                # OpenAI 格式: tc.function.name
                tool_name = tc.function.name if hasattr(tc, 'function') else getattr(tc, 'name', 'unknown')
                tool_args = {}
                if hasattr(tc, 'function') and hasattr(tc.function, 'arguments'):
                    try:
                        tool_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                    except Exception as e:
                        tool_args = {}
                elif hasattr(tc, 'arguments'):
                    tool_args = tc.arguments if isinstance(tc.arguments, dict) else {}
                
                tasks.append(Task(
                    id=f"task_{self.ctx.iteration}_{i}",
                    name=tool_name,
                    tool=tool_name,
                    params=tool_args,
                    priority=i
                ))
        
        # 如果没有工具调用，尝试从内容解析 JSON
        if not tasks and hasattr(response, 'content') and response.content:
            try:
                content = response.content
                # 提取 JSON
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                elif "{" in content:
                    json_str = content[content.index("{"):content.rindex("}")+1]
                else:
                    json_str = "{}"
                
                plan_data = json.loads(json_str)
                for i, t in enumerate(plan_data.get("tasks", [])):
                    tasks.append(Task(
                        id=f"task_{self.ctx.iteration}_{i}",
                        name=t.get("tool", "unknown"),
                        tool=t.get("tool", "unknown"),
                        params=t.get("params", {}),
                        priority=i
                    ))
            except Exception as e:
                logger.warning(f"解析计划失败: {e}")
        
        # ── 强制去重：过滤掉已在 history 中执行过的任务 ──
        executed_tasks = {t['task'] for t in self.ctx.history}
        if executed_tasks:
            filtered = [t for t in tasks if t.tool not in executed_tasks]
            if filtered:
                tasks = filtered
                logger.info(f"已过滤重复任务，剩余: {[t.tool for t in tasks]}")
            else:
                # 所有候选都执行过了——清空让默认逻辑选未执行任务
                logger.info("所有候选任务均已执行过，将选择新任务")
                tasks = []
        
        # 如果还是没有任务，从未执行过的工具中选一个
        if not tasks:
            # 优先从技能列表中选未执行过的
            skill_candidates = [
                t["name"] for t in self.tools
                if t["name"] not in executed_tasks
            ]
            if skill_candidates:
                next_tool = skill_candidates[0]
                logger.info(f"使用备用计划: {next_tool}")
                tasks = [
                    Task(
                        id=f"fallback_{self.ctx.iteration}",
                        name=next_tool,
                        tool=next_tool,
                        params={"target": self.ctx.target},
                        priority=0,
                    )
                ]
            else:
                # 所有工具都执行过了，直接终止（由 Reflector 判断 need_more_work）
                logger.info("所有工具均已执行完毕，返回空计划")
                tasks = []
        
        return tasks
    
    # ==================== EXECUTOR ====================
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """执行单个任务（增强版）
        
        集成：
        - RAG 工具知识查询
        - Token 预算更新
        - Skills 技能执行
        """
        task.status = "running"
        
        # 检查是否是技能调用
        is_skill = task.tool.startswith("skill_")
        skill_id = task.tool[6:] if is_skill else None
        
        # 执行前：查询工具使用知识
        tool_guide = ""
        if self.rag_client and not is_skill:
            try:
                guide_results = await self.rag_client.search_tool_guide(
                    tool_name=task.tool,
                    query="最佳实践",
                    top_k=2
                )
                if guide_results:
                    tool_guide = "\n".join([r.content[:300] if r.content else "" for r in guide_results])
                    self.ctx.rag_queries += 1
                    logger.debug(f"获取到 {task.tool} 的使用指南")
            except Exception as e:
                logger.debug(f"获取工具指南失败: {e}")
        
        try:
            # === 技能执行 ===
            if is_skill:
                registry = _get_skill_registry()
                if registry:
                    # 合并参数
                    skill_params = {**task.params}
                    if "target" not in skill_params:
                        skill_params["target"] = self.ctx.target
                    
                    # 确保 target 有 http:// 前缀（skill 需要完整 URL）
                    t = skill_params["target"]
                    if t and not t.startswith(("http://", "https://")):
                        skill_params["target"] = "http://" + t
                    
                    logger.info(f"执行技能: {skill_id} 参数: {skill_params}")
                    skill_result = registry.execute(skill_id, skill_params)
                    
                    task.result = skill_result
                    task.status = "completed" if skill_result.get("success") else "failed"
                    
                    # 如果技能发现漏洞，添加到发现列表
                    if skill_result.get("vulnerable"):
                        self.ctx.findings.append({
                            "type": skill_id,
                            "target": skill_params.get("target"),
                            "severity": self._get_skill_severity(skill_id),
                            "evidence": skill_result.get("evidence"),
                            "source": "skill"
                        })
                    
                    # 记录历史
                    self.ctx.history.append({
                        "iteration": self.ctx.iteration,
                        "task": task.name,
                        "params": task.params,
                        "result": skill_result,
                        "success": skill_result.get("success", False),
                        "simulated": False,
                        "is_skill": True,
                        "skill_id": skill_id
                    })
                    
                    return {
                        "success": skill_result.get("success", False),
                        "output": skill_result,
                        "simulated": False,
                        "is_skill": True,
                        "skill_id": skill_id,
                        "vulnerable": skill_result.get("vulnerable", False)
                    }
                else:
                    return {"success": False, "error": "Skills 库未初始化"}
            
            # === 常规工具执行 ===
            # 调用工具执行器
            result = await self.tool_executor(task.tool, task.params)
            
            task.result = result.output if hasattr(result, 'output') else result
            task.status = "completed" if result.success else "failed"
            
            # 记录历史（包含工具指南）
            self.ctx.history.append({
                "iteration": self.ctx.iteration,
                "task": task.name,
                "params": task.params,
                "result": task.result,
                "success": result.success if hasattr(result, 'success') else True,
                "simulated": result.simulated if hasattr(result, 'simulated') else True,
                "tool_guide_used": bool(tool_guide)
            })
            
            # 执行后：更新预算
            if self.budget_manager:
                # 估算 Token 消耗（基于输出大小）
                output_size = len(str(task.result))
                estimated_tokens = output_size // 4  # 粗略估算
                self.ctx.budget_used += estimated_tokens
                
                BudgetPhase = _get_budget_phase()
                if BudgetPhase:
                    self.budget_manager.record_usage(
                        input_tokens=0,  # 执行阶段主要是输出
                        output_tokens=estimated_tokens,
                        phase=BudgetPhase.RECONNAISSANCE,
                        tool_calls=1
                    )
            
            return {
                "success": result.success if hasattr(result, 'success') else True,
                "output": task.result,
                "simulated": result.simulated if hasattr(result, 'simulated') else True,
                "tool_guide": tool_guide[:200] if tool_guide else None
            }
            
        except Exception as e:
            task.status = "failed"
            task.result = {"error": str(e)}
            return {"success": False, "error": str(e)}
    
    def _get_skill_severity(self, skill_id: str) -> str:
        """获取技能的严重性等级"""
        registry = _get_skill_registry()
        if registry:
            skill = registry.get(skill_id)
            if skill:
                return skill.severity
        return "medium"
    
    # ==================== REFLECTOR ====================
    
    async def _reflect(self) -> Dict[str, Any]:
        """AI 反思执行结果（增强版）
        
        集成：
        - RAG 漏洞利用知识
        - 上下文缺口重新分析
        """
        
        # 查询漏洞利用知识
        exploit_knowledge = ""
        if self.rag_client and self.ctx.findings:
            try:
                for finding in self.ctx.findings[:3]:
                    vuln_type = finding.get("type", "")
                    if vuln_type:
                        results = await self.rag_client.search_exploit_method(
                            vuln_type=vuln_type,
                            top_k=2
                        )
                        if results:
                            exploit_knowledge += "\n" + "\n".join([
                                f"{r.title}: {r.content[:200] if r.content else ''}..." 
                                for r in results
                            ])
                
                if exploit_knowledge:
                    self.ctx.rag_queries += 1
                    logger.info("获取到漏洞利用知识")
            except Exception as e:
                logger.debug(f"获取漏洞利用知识失败: {e}")
        
        # 构建增强的 Reflector 提示词
        prompt = self._build_enhanced_reflector_prompt(exploit_knowledge)
        
        messages = [
            {"role": "system", "content": self._get_reflector_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: self.llm_client.chat(messages)),
            timeout=60
        )
        
        # 记录 Token 消耗
        if self.budget_manager and hasattr(response, 'usage'):
            BudgetPhase = _get_budget_phase()
            if BudgetPhase:
                tokens_used = (
                    getattr(response.usage, 'prompt_tokens', 0) +
                    getattr(response.usage, 'completion_tokens', 0)
                )
                self.ctx.budget_used += tokens_used
                self.budget_manager.record_usage(
                    input_tokens=getattr(response.usage, 'prompt_tokens', 0),
                    output_tokens=getattr(response.usage, 'completion_tokens', 0),
                    phase=BudgetPhase.REPORTING
                )
        
        # 解析反思结果
        content = response.content if hasattr(response, 'content') and response.content else str(response) if response else ""
        
        # 重新分析上下文缺口
        new_gaps = []
        if self.context_analyzer:
            try:
                updated_context = {
                    **self.ctx.collected_info,
                    "findings": self.ctx.findings
                }
                gap_result = self.context_analyzer.analyze(
                    user_input=self.ctx.goal,
                    context=updated_context,
                    task_phase=f"reflection_{self.ctx.iteration}"
                )
                new_gaps = gap_result.gaps if hasattr(gap_result, 'gaps') else []
                
                # 如果有新的高优先级缺口，建议继续
                high_priority_gaps = [g for g in new_gaps if hasattr(g, 'priority') and g.priority <= 2]
                if high_priority_gaps:
                    logger.info(f"发现 {len(high_priority_gaps)} 个高优先级缺口，建议继续")
            except Exception as e:
                logger.debug(f"反思阶段缺口分析失败: {e}")
        
        # 判断是否需要继续
        goal_achieved = False
        if content:
            positive_indicators = [
                "目标已达成", "测试已完成", "无需继续测试",
                "已完成所有", "成功获取", "漏洞已利用",
                "goal achieved", "testing complete"
            ]
            negative_indicators = [
                "目标未达成", "需要继续", "尚未完成", "未完成"
            ]
            has_positive = any(ind in content for ind in positive_indicators)
            has_negative = any(ind in content for ind in negative_indicators)
            if has_positive and not has_negative:
                goal_achieved = True

        # 执行了足够多的不同任务且无漏洞发现 → 自动结束
        executed_count = len({t['task'] for t in self.ctx.history})
        real_findings = len([f for f in self.ctx.findings if f.get('type') != 'open_ports'])
        available_tools_count = len(self.tools)

        # 终止条件（按优先级）：
        # 1. LLM 明确宣告完成
        # 2. 发现了漏洞 且 已迭代 2 轮以上
        # 3. 执行了所有可用工具
        # 4. 已执行任务数 >= min(可用工具数, 4) 且无新发现（最多4个工具无发现即停止）
        if real_findings > 0 and self.ctx.iteration >= 2:
            goal_achieved = True
        elif executed_count >= available_tools_count:
            goal_achieved = True
        elif executed_count >= min(available_tools_count, 4) and real_findings == 0:
            goal_achieved = True

        need_more = not goal_achieved and self.ctx.iteration < self.ctx.max_iterations
        # 注意：不允许 new_gaps 覆盖 goal_achieved=True 的决定

        return {
            "summary": content[:500],
            "goal_achieved": goal_achieved,
            "need_more_work": need_more,
            "new_gaps": len(new_gaps),
            "exploit_knowledge_used": bool(exploit_knowledge)
        }
    
    def _build_enhanced_reflector_prompt(self, exploit_knowledge: str = "") -> str:
        """构建增强的 Reflector 提示词"""
        # 压缩 reflect prompt：只保留最近 3 条历史和关键字段
        slim_history = [
            {"task": h["task"], "success": h.get("success", False), "findings": len(h.get("findings", []))}
            for h in self.ctx.history[-3:]
        ]
        history = json.dumps(slim_history, ensure_ascii=False)
        findings = json.dumps(self.ctx.findings[:5], ensure_ascii=False)[:600]
        
        exploit_hint = ""
        if exploit_knowledge:
            exploit_hint = f"\n## 漏洞利用参考\n{exploit_knowledge[:400]}\n"
        
        return f"""
## 执行历史
{history}

## 发现
{findings if findings != '[]' else '暂无发现'}{exploit_hint}
## 任务
1. 总结本次迭代的结果
2. 分析是否发现了有价值的信息
3. 判断目标是否已达成
4. 决定是否需要更多工作

请回答:
- 本次发现了什么
- 目标是否达成
- 是否需要继续
"""
    
    def _get_reflector_system_prompt(self) -> str:
        """Reflector 系统提示词"""
        executed = list({t["task"] for t in self.ctx.history})
        executed_str = ", ".join(executed) if executed else "无"
        findings_count = len([f for f in self.ctx.findings if f.get("type") != "open_ports"])
        return f"""你是一个渗透测试结果分析专家。你的职责是:
1. 分析扫描结果，提取有价值的信息
2. 评估测试目标的完成度
3. 提出后续建议

已执行任务（不要再建议重复执行这些）: {executed_str}
当前发现漏洞数量: {findings_count}

分析原则:
- 关注开放的端口和服务
- 关注发现的漏洞和安全问题
- 评估风险等级
- 已经失败的任务不要重复执行

目标达成标准（满足任意一条即可）:
- 发现了任意可确认的漏洞（CSRF/XSS/SQLi/RCE/LFI等）
- 完成了对目标的全面扫描且无新发现
- 已执行 3 次或以上任务且结果趋于重复

重要规则:
- 如果已经发现漏洞，说"目标已达成"，不要继续测试同一漏洞
- 如果某个工具连续失败 2 次，不要再建议使用它
- 不要建议重复执行 {executed_str} 中的任务"""
    
    # ==================== 辅助方法 ====================
    
    def _update_collected_info(self, task: Task, result: Dict[str, Any]):
        """更新收集的信息"""
        output = result.get("output", {})
        
        # 处理技能执行结果
        if result.get("is_skill"):
            skill_id = result.get("skill_id", "")
            if result.get("vulnerable"):
                # 技能发现漏洞
                self.ctx.collected_info[f"skill_{skill_id}"] = {
                    "vulnerable": True,
                    "evidence": output.get("evidence")
                }
            return
        
        if task.tool == "nmap_scan":
            ports = output.get("ports", [])
            self.ctx.collected_info["ports"] = ports
            self.ctx.collected_info["target"] = self.ctx.target
            # 提取版本字符串，供 fingerprint 匹配
            version_strings = []
            for p in ports:
                if isinstance(p, dict):
                    v = p.get("version", "") or p.get("service", "")
                    if v:
                        version_strings.append(v.lower())
            if version_strings:
                self.ctx.collected_info["nmap_versions"] = version_strings
        
        elif task.tool == "whatweb_scan":
            self.ctx.collected_info["technologies"] = output.get("technologies", [])
        
        elif task.tool == "nikto_scan":
            # 从 nikto raw_output 提取 Server 头和 title，供指纹匹配使用
            raw = result.get("raw_output", "") or result.get("output", {})
            if isinstance(raw, str):
                import re as _re
                m = _re.search(r"Server:\s*([^\r\n]+)", raw, _re.IGNORECASE)
                if m:
                    self.ctx.collected_info["server"] = m.group(1).strip().lower()
                m2 = _re.search(r"<title>([^<]+)</title>", raw, _re.IGNORECASE)
                if m2:
                    self.ctx.collected_info["http_title"] = m2.group(1).strip().lower()

        elif task.tool == "nuclei_scan":
            vulns = output.get("vulnerabilities", [])
            self.ctx.findings.extend(vulns)
        
        elif task.tool == "sqlmap_scan":
            if output.get("vulnerable"):
                self.ctx.findings.append({
                    "type": "sql_injection",
                    "target": task.params.get("target"),
                    "severity": "high"
                })
    
    async def _auto_detect_wordpress_per(self, task, result: Dict) -> None:
        """在 intelligent_per 中检测 WordPress 并直接执行 wordpress_rce skill"""
        if "wordpress_scan" in getattr(self, "_dispatched_wp", set()):
            return
        if not hasattr(self, "_dispatched_wp"):
            self._dispatched_wp = set()

        target = task.params.get("target", "")
        if not target:
            return

        # 主动 HTTP 探测 wp-login.php
        import urllib.request as _ur
        base_url = target if target.startswith("http") else f"http://{target}"
        wp_found = False
        try:
            _req = _ur.Request(base_url.rstrip("/") + "/wp-login.php")
            _req.add_header("User-Agent", "Mozilla/5.0")
            _resp = _ur.urlopen(_req, timeout=5)
            _body = _resp.read(2000).decode("utf-8", errors="ignore")
            if "WordPress" in _body or "wp-login" in _body or 'name="log"' in _body:
                wp_found = True
        except Exception:
            pass

        if not wp_found:
            return

        self._dispatched_wp.add("wordpress_scan")

        try:
            from src.shared.backend.skills.cve_exploit_skills import get_cve_exploit_skills
            from src.shared.backend.skills.core import SkillExecutor
            import asyncio as _asyncio

            skill_registry = {s.id: s for s in get_cve_exploit_skills()}
            if "wordpress_rce" not in skill_registry:
                return

            executor = SkillExecutor()
            wp_skill = skill_registry["wordpress_rce"]
            common_creds = [("admin", "qwerty"), ("admin", "admin"), ("admin", "password"),
                            ("admin", "wordpress"), ("admin", "admin123")]

            for user, pwd in common_creds:
                try:
                    rce_result = await _asyncio.wait_for(
                        _asyncio.to_thread(
                            executor.execute,
                            wp_skill,
                            {"target": base_url, "username": user, "password": pwd},
                        ),
                        timeout=30,
                    )
                    rce_output = rce_result.get("output", "") if isinstance(rce_result, dict) else str(rce_result)
                    if "LOGIN_SUCCESS" in rce_output or "RCE_CONFIRMED" in rce_output:
                        self.ctx.findings.append({
                            "type": "wordpress_rce",
                            "target": base_url,
                            "severity": "critical",
                            "evidence": f"WordPress RCE: {user}/{pwd} — {rce_output[:200]}",
                            "source": "wordpress_rce_skill",
                        })
                        break
                except Exception:
                    continue
        except Exception:
            pass

    async def _run_fingerprint_dispatch(self) -> List[Dict[str, Any]]:
        """根据当前 findings/collected_info 运行指纹匹配，自动触发 CVE Skills。
        
        返回需要 yield 给前端的事件列表。
        """
        events: List[Dict[str, Any]] = []
        if not hasattr(self, "_dispatched_fp"):
            self._dispatched_fp: set = set()

        # 构造用于 fingerprint 的 findings 格式
        fp_findings: List[dict] = list(self.ctx.findings)

        # 补充 nmap 端口信息
        ports = self.ctx.collected_info.get("ports", [])
        nmap_versions = self.ctx.collected_info.get("nmap_versions", [])
        if ports:
            enriched_ports = []
            for p in ports:
                ep = dict(p) if isinstance(p, dict) else {"port": p}
                if not ep.get("version") and nmap_versions:
                    ep["version"] = " ".join(nmap_versions)
                enriched_ports.append(ep)
            fp_findings.append({"type": "open_ports", "ports": enriched_ports})

        # 补充 HTTP 标题/服务器头
        http_title = self.ctx.collected_info.get("http_title", "")
        server_header = self.ctx.collected_info.get("server", "")

        # 如果还没有 HTTP 信息，对开放端口做快速 HTTP 探测
        if not http_title and not server_header and ports:
            http_title, server_header = await self._quick_http_probe(ports)
            if http_title:
                self.ctx.collected_info["http_title"] = http_title
            if server_header:
                self.ctx.collected_info["server"] = server_header

        if http_title or server_header:
            fp_findings.append({
                "type": "http_probe",
                "title": http_title,
                "server": server_header,
            })

        if not fp_findings:
            return events

        matches = _get_fingerprint_matches(fp_findings, self.ctx.target)
        registry = _get_skill_registry()

        for m in matches:
            if m.skill_id in self._dispatched_fp:
                continue
            if m.confidence < 0.35:
                continue

            self._dispatched_fp.add(m.skill_id)
            logger.info(f"指纹分发: {m.skill_id} (confidence={m.confidence:.2f}) → {m.target}")

            events.append({
                "type": "message",
                "text": f"[指纹匹配] {m.description} (置信度 {m.confidence:.0%}) → 触发 {m.skill_id}",
                "msg_type": "warning",
            })

            if registry is None:
                continue

            try:
                skill_result = await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda sid=m.skill_id, tgt=m.target: registry.execute(sid, {"target": tgt})
                )
                # 验证返回值是有效 dict
                if not skill_result or not isinstance(skill_result, dict):
                    logger.warning(f"CVE Skill {m.skill_id} 返回无效结果: {skill_result}")
                    continue
                vulnerable = skill_result.get("vulnerable", False)
                finding_entry = {
                    "type": "cve_skill",
                    "skill_id": m.skill_id,
                    "description": m.description,
                    "target": m.target,
                    "vulnerable": vulnerable,
                    "severity": "critical" if vulnerable else "info",
                    "output_preview": str(skill_result.get("output", ""))[:300],
                    "evidence": skill_result.get("evidence", ""),
                }
                self.ctx.findings.append(finding_entry)

                events.append({
                    "type": "finding",
                    "vuln_type": finding_entry.get("type"),  # 避免与事件 type 冲突
                    **{k: v for k, v in finding_entry.items() if k != "type"},
                })
                events.append({
                    "type": "message",
                    "text": f"{m.skill_id} → {'🔴 漏洞确认！' if vulnerable else '未发现漏洞'}",
                    "msg_type": "error" if vulnerable else "info",
                })
            except Exception as e:
                logger.warning(f"CVE Skill {m.skill_id} 执行失败: {e}")
                events.append({
                    "type": "message",
                    "text": f"{m.skill_id} 执行出错: {e}",
                    "msg_type": "warning",
                })

        return events

    async def _quick_http_probe(self, ports: List[dict]) -> tuple:
        """对开放端口快速 HTTP 探测，返回 (title, server_header)"""
        import urllib.request as _ur
        import urllib.error as _ue

        # 提取目标 host
        target = self.ctx.target
        parsed_host = target
        if "://" in target:
            parsed_host = target.split("://", 1)[1].split("/")[0]

        for p in ports:
            port_num = p.get("port") if isinstance(p, dict) else p
            if not port_num:
                continue
            for scheme in ("http", "https"):
                url = f"{scheme}://{parsed_host}:{port_num}/"
                try:
                    req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    resp = await asyncio.get_running_loop().run_in_executor(
                        None,
                        lambda u=url: _ur.urlopen(
                            _ur.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
                            timeout=5
                        )
                    )
                    body = resp.read(4096).decode("utf-8", errors="ignore")
                    server = resp.headers.get("Server", "").lower()
                    import re as _re
                    m = _re.search(r"<title>([^<]+)</title>", body, _re.IGNORECASE)
                    title = m.group(1).strip().lower() if m else ""
                    if server or title:
                        logger.info(f"HTTP 快速探测 {url}: server={server} title={title}")
                        return title, server
                except Exception:
                    continue
        return "", ""

    def _extract_findings(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从结果中提取发现"""
        findings = []
        output = result.get("output", {})
        
        # 技能执行结果：vulnerable=True 就是一个 finding
        if result.get("is_skill") and result.get("vulnerable"):
            skill_id = result.get("skill_id", "")
            findings.append({
                "type": skill_id,
                "severity": self._get_skill_severity(skill_id),
                "evidence": output.get("evidence", "") if isinstance(output, dict) else "",
                "target": self.ctx.target,
            })
            return findings
        
        if isinstance(output, dict):
            # 端口发现
            if "ports" in output:
                ports = output["ports"]
                if isinstance(ports, list) and len(ports) > 0:
                    findings.append({
                        "type": "open_ports",
                        "count": len(ports),
                        # 保留完整端口对象 {port, service, state}
                        "ports": ports if isinstance(ports[0], dict) else [{"port": p} for p in ports]
                    })
            
            # 漏洞发现
            if "vulnerabilities" in output:
                vulns = output["vulnerabilities"]
                if isinstance(vulns, list):
                    findings.extend(vulns)
        
        return findings
    
    def _get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取 OpenAI 格式的工具 Schema（包含技能）"""
        schemas = []
        
        # 基本工具 Schema
        try:
            from .tools.schemas import TOOL_SCHEMAS
            schemas.extend(TOOL_SCHEMAS)
        except ImportError:
            # 返回基本 Schema
            for t in self.tools:
                if t.get("is_skill"):
                    continue  # 技能单独处理
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "target": {"type": "string"}
                            },
                            "required": ["target"]
                        }
                    }
                })
        
        # 添加技能 Schema
        registry = _get_skill_registry()
        if registry:
            skill_schemas = registry.get_openai_tools()
            schemas.extend(skill_schemas)
        
        return schemas
    
    def _generate_report(self) -> str:
        """生成专业渗透测试报告"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        target = self.ctx.target

        # ── 基础数据字典 ──────────────────────────────────────
        SEV_CN = {
            "critical": "严重", "high": "高危",
            "medium": "中危", "low": "低危", "info": "信息",
        }
        SEV_EMOJI = {
            "critical": "🔴", "high": "🟠",
            "medium": "🟡", "low": "🔵", "info": "⚪",
        }
        TYPE_CN = {
            "csrf_testing":            "CSRF 跨站请求伪造",
            "sqli_basic":              "SQL 注入",
            "sqli_union":              "SQL 联合注入",
            "sqli_time_blind":         "SQL 时间盲注",
            "xss_reflected":           "反射型 XSS",
            "xss_stored":              "存储型 XSS",
            "auth_bypass_sql":         "SQL 认证绕过",
            "auth_bruteforce":         "暴力破解",
            "rce_command_injection":   "远程命令执行 (RCE)",
            "lfi_basic":               "本地文件包含 (LFI)",
            "xxe_testing":             "XML 外部实体注入 (XXE)",
            "ssrf_testing":            "服务器端请求伪造 (SSRF)",
            "file_upload_testing":     "文件上传漏洞",
            "idor_testing":            "越权访问 (IDOR)",
            "ssti_testing":            "服务端模板注入 (SSTI)",
            "deserialization_testing": "反序列化漏洞",
            "nosql_injection":         "NoSQL 注入",
            "waf_detect":              "WAF 检测",
            "cve_skill":               "CVE 漏洞利用",
            "wordpress_rce":           "WordPress RCE",
            "fuel_cms_rce":            "Fuel CMS RCE (CVE-2018-16763)",
            "jangow_full_pwn":         "Jangow 完整攻击链",
            "jangow_cmd_injection":    "Jangow 命令注入",
            "s2_045":                  "Apache Struts2 S2-045 (CVE-2017-5638)",
            "s2_057":                  "Apache Struts2 S2-057 (CVE-2018-11776)",
            "s2_061":                  "Apache Struts2 S2-061 (CVE-2020-17530)",
            "geoserver_rce":           "GeoServer RCE (CVE-2024-36401)",
            "activemq_rce":            "Apache ActiveMQ RCE (CVE-2023-46604)",
            "tomcat_rce":              "Apache Tomcat RCE",
            "cve_2017_16995":          "Linux eBPF 提权 (CVE-2017-16995)",
            "cve_2021_4034":           "PwnKit 提权 (CVE-2021-4034)",
            "privesc_linux":           "Linux 权限提升",
            "privesc_windows":         "Windows 权限提升",
            "openssh_user_enum":       "OpenSSH 用户枚举 (CVE-2018-15473)",
            "flag_detector":           "CTF Flag 捕获",
        }

        # CVSS 评分库（按漏洞类型）
        CVSS_SCORES = {
            "sqli_basic": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "sqli_union": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "sqli_time_blind": ("7.5", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
            "xss_reflected": ("6.1", "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N"),
            "xss_stored": ("8.8", "CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N"),
            "auth_bypass_sql": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "auth_bruteforce": ("7.5", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
            "rce_command_injection": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "lfi_basic": ("7.5", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"),
            "xxe_testing": ("8.2", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N"),
            "ssrf_testing": ("8.6", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N"),
            "file_upload_testing": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "idor_testing": ("6.5", "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N"),
            "ssti_testing": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "csrf_testing": ("6.5", "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:H/A:N"),
            "deserialization_testing": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "nosql_injection": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "fuel_cms_rce": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "wordpress_rce": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "jangow_cmd_injection": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "jangow_full_pwn": ("10.0", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"),
            "s2_045": ("10.0", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"),
            "s2_057": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "s2_061": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "geoserver_rce": ("9.8", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            "activemq_rce": ("10.0", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"),
            "cve_2017_16995": ("7.8", "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H"),
            "cve_2021_4034": ("7.8", "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H"),
        }

        # 漏洞描述库
        VULN_DESC = {
            "sqli_basic":              "目标存在 SQL 注入漏洞，攻击者可通过构造恶意 SQL 语句绕过认证、读取/修改数据库数据，严重时可获取操作系统权限。",
            "sqli_union":              "目标存在 SQL 联合注入漏洞，攻击者可利用 UNION 语句提取数据库全量数据，包括用户凭据、敏感业务数据等。",
            "sqli_time_blind":         "目标存在 SQL 时间盲注漏洞，攻击者虽无直接回显，但可通过响应时间差异逐字节枚举数据库内容。",
            "xss_reflected":           "目标存在反射型跨站脚本漏洞，攻击者可构造恶意链接，诱导受害者访问后在其浏览器中执行任意 JavaScript，劫持会话或窃取 Cookie。",
            "xss_stored":              "目标存在存储型跨站脚本漏洞，恶意脚本被持久化存储，每次页面加载时自动执行，影响所有访问该页面的用户。",
            "auth_bypass_sql":         "目标登录接口存在 SQL 注入认证绕过漏洞，攻击者可在无有效凭据的情况下直接以管理员身份登录系统。",
            "auth_bruteforce":         "目标认证接口缺乏暴力破解防护，攻击者可通过字典/枚举攻击获取有效账户凭据。",
            "rce_command_injection":   "目标存在命令注入漏洞，用户输入被拼接至系统命令执行，攻击者可在服务器上执行任意操作系统命令，获取完整系统控制权。",
            "lfi_basic":               "目标存在本地文件包含漏洞，攻击者可读取服务器任意文件（如 /etc/passwd、配置文件），结合日志注入可升级为 RCE。",
            "xxe_testing":             "目标 XML 解析器未禁用外部实体，攻击者可通过构造恶意 XML 读取内网文件、探测内网服务，严重时可触发 SSRF。",
            "ssrf_testing":            "目标存在服务器端请求伪造漏洞，攻击者可借助目标服务器访问内网资源、云服务元数据接口，可能导致内网横向渗透或凭据泄露。",
            "file_upload_testing":     "目标文件上传功能存在安全缺陷，未对上传文件类型和内容进行有效校验，攻击者可上传 WebShell 获取服务器控制权。",
            "idor_testing":            "目标存在越权访问漏洞，仅通过修改请求中的对象 ID 即可访问其他用户的数据，导致数据泄露或未授权操作。",
            "ssti_testing":            "目标模板引擎直接渲染用户输入，攻击者可注入模板表达式在服务端执行任意代码，危害等同于 RCE。",
            "csrf_testing":            "目标缺乏 CSRF 防护，攻击者可构造恶意页面，诱导已登录用户在不知情的情况下执行敏感操作（如转账、改密）。",
            "deserialization_testing": "目标存在不安全反序列化漏洞，攻击者可提交构造的序列化对象触发任意代码执行，危害极高。",
            "nosql_injection":         "目标存在 NoSQL 注入漏洞，攻击者可通过注入 NoSQL 操作符绕过认证或提取数据库内容。",
            "fuel_cms_rce":            "目标运行存在已知 RCE 漏洞的 Fuel CMS 1.4.1，攻击者可通过 CVE-2018-16763 漏洞无需认证直接在服务器执行任意命令。",
            "wordpress_rce":           "目标 WordPress 存在代码执行漏洞，攻击者可通过已知漏洞或主题/插件缺陷在服务器执行任意代码。",
            "jangow_cmd_injection":    "目标 busque.php 脚本将 GET 参数直接传入 system() 函数执行，攻击者无需认证可直接以 Web 服务账户权限执行任意 OS 命令。",
            "jangow_full_pwn":         "目标系统存在完整攻击链：Web 命令注入 (busque.php) → 凭据泄露 (WordPress config) → 内核提权 (CVE-2017-16995)，可从 0 权限实现完整系统控制。",
            "s2_045":                  "目标 Apache Struts2 存在 S2-045 漏洞 (CVE-2017-5638)，Content-Type 头中的 OGNL 表达式会被解析执行，可无需认证实现远程代码执行。",
            "activemq_rce":            "目标 Apache ActiveMQ 存在 CVE-2023-46604 漏洞，攻击者可通过 OpenWire 协议触发 ClassInfo 反序列化，实现无需认证的远程代码执行。",
            "cve_2021_4034":           "目标 Linux pkexec 存在 CVE-2021-4034 (PwnKit) 漏洞，本地低权限用户可通过利用该漏洞提升至 root 权限。",
            "cve_2017_16995":          "目标 Linux 内核存在 CVE-2017-16995 漏洞，eBPF 验证器存在越界写入缺陷，本地用户可提权至 root。",
        }

        # 攻击步骤库
        ATTACK_STEPS = {
            "sqli_basic":           ["发送含单引号的测试请求触发 SQL 错误", "确认注入点类型（字符型/数字型）", "使用 sqlmap 或手工提取数据库名、表名、数据"],
            "sqli_union":           ["探测列数（ORDER BY 或 UNION SELECT NULL...）", "找到可回显列", "UNION SELECT 提取目标数据"],
            "xss_reflected":        ["在参数中注入 <script>alert(1)</script> 验证", "构造窃取 Cookie 的 XSS Payload", "通过钓鱼链接投递至受害者"],
            "xss_stored":           ["找到持久化存储的输入点（评论/用户资料等）", "注入存储型 XSS Payload", "等待其他用户访问触发执行"],
            "auth_bypass_sql":      ["在用户名输入框输入 ' OR '1'='1", "密码随意填写，提交登录", "系统直接以管理员身份登录成功"],
            "rce_command_injection":["确认存在命令拼接的参数（如 ?cmd=whoami）", "注入分隔符执行额外命令（; id、&& id）", "反弹 Shell 获取交互式控制"],
            "lfi_basic":            ["测试路径遍历（../../../etc/passwd）", "确认可读文件范围", "尝试读取日志文件后配合日志投毒升级 RCE"],
            "fuel_cms_rce":         ["访问 /fuel/pages/select/?filter= 端点", "在 filter 参数中注入 PHP 代码（如 {{system('id')}}）", "验证命令执行结果", "部署反弹 Shell 或 WebShell"],
            "jangow_cmd_injection":  ["请求 /busque.php?buscar=id 验证 RCE", "读取 /var/www/html/wordpress/config.php 获取凭据", "利用数据库凭据切换用户", "利用内核漏洞提权至 root"],
            "s2_045":               ["构造包含 OGNL 表达式的 Content-Type 头", "发送 POST 请求至目标 URL", "验证服务端命令执行（${#_memberAccess...}）"],
            "activemq_rce":         ["连接目标 61616 端口（OpenWire 协议）", "发送构造的 ExceptionResponse 包触发类加载", "远程加载恶意 ClassPathXmlApplicationContext"],
            "cve_2021_4034":        ["上传 exploit.c 到目标机器", "编译并执行 PwnKit exploit", "验证 id 输出为 uid=0(root)"],
        }

        # 修复建议库（详细版）
        FIX_ADVICE = {
            "csrf_testing":            (
                "1. 在所有表单和 AJAX 请求中强制校验 CSRF Token（随机且与会话绑定）。\n"
                "2. 为敏感 Cookie 设置 `SameSite=Strict` 或 `SameSite=Lax` 属性。\n"
                "3. 验证请求来源 `Referer`/`Origin` 头（作为辅助防御）。\n"
                "参考：https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html"
            ),
            "sqli_basic":             (
                "1. **立即**：使用参数化查询（PreparedStatement）或 ORM 框架，禁止字符串拼接 SQL。\n"
                "2. 对所有用户输入进行类型校验和白名单过滤。\n"
                "3. 数据库账户遵循最小权限原则，Web 账号不应拥有 DROP/ALTER 权限。\n"
                "4. 部署 WAF 规则过滤 SQL 注入关键字（`UNION`、`SELECT`、`'` 等）。\n"
                "参考：https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
            ),
            "sqli_union":             (
                "1. 使用参数化查询/ORM，彻底消除 SQL 拼接。\n"
                "2. 限制数据库账户权限，禁止 `INFORMATION_SCHEMA` 访问。\n"
                "3. 部署 WAF 过滤 `UNION SELECT` 特征。"
            ),
            "sqli_time_blind":        (
                "1. 同 SQL 注入修复建议（参数化查询）。\n"
                "2. 设置数据库查询超时（`max_execution_time`），防止长时间占用。\n"
                "3. 监控异常慢查询并告警。"
            ),
            "xss_reflected":          (
                "1. 对所有输出内容进行 HTML 实体编码（`htmlspecialchars` / `escapeHtml`）。\n"
                "2. 配置 `Content-Security-Policy` 响应头，禁止内联脚本执行。\n"
                "3. 为敏感 Cookie 设置 `HttpOnly` 属性，防止脚本读取。\n"
                "参考：https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
            ),
            "xss_stored":             (
                "1. 存储前对用户输入进行严格过滤（白名单 HTML 标签）。\n"
                "2. 输出时进行上下文感知编码（HTML/JS/URL 编码）。\n"
                "3. 启用 CSP（`Content-Security-Policy: default-src 'self'`）。\n"
                "4. 定期扫描存储的用户内容。"
            ),
            "auth_bypass_sql":        (
                "1. **立即**：修复登录 SQL 查询，使用参数化查询。\n"
                "2. 不要将用户名/密码直接拼接至 SQL 语句。\n"
                "3. 使用成熟认证框架（如 Spring Security、Passport.js）。\n"
                "参考：https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication"
            ),
            "auth_bruteforce":        (
                "1. 连续失败 N 次后触发账户临时锁定（如 5 次失败锁定 15 分钟）。\n"
                "2. 登录接口加入图形验证码或 reCAPTCHA。\n"
                "3. 实施多因素认证（MFA/2FA）。\n"
                "4. 对登录接口进行速率限制（Rate Limiting）。"
            ),
            "rce_command_injection":  (
                "1. **立即**：避免将任何用户输入传入 `system()`、`exec()`、`shell_exec()` 等函数。\n"
                "2. 若必须调用系统命令，使用参数数组形式（如 Python `subprocess.run(['cmd', arg])`）。\n"
                "3. 对输入进行严格白名单校验，仅允许已知安全字符。\n"
                "4. 以最低权限账户运行 Web 服务进程。\n"
                "参考：https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
            ),
            "lfi_basic":              (
                "1. 禁止将用户输入直接用于文件路径。\n"
                "2. 使用白名单映射（如 `pages[home]='home.php'`）代替直接路径传递。\n"
                "3. 使用 `realpath()` 校验路径是否在允许目录内。\n"
                "4. 设置 `open_basedir` 限制 PHP 文件访问范围。"
            ),
            "xxe_testing":            (
                "1. 在 XML 解析器中禁用外部实体（`FEATURE_EXTERNAL_GENERAL_ENTITIES=false`）。\n"
                "2. 禁用 DOCTYPE 声明。\n"
                "3. 若不需要 XML，考虑改用 JSON 格式。\n"
                "参考：https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html"
            ),
            "ssrf_testing":           (
                "1. 对用户提供的 URL 进行白名单过滤，拒绝内网 IP 段（`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`169.254.0.0/16`）。\n"
                "2. 使用 DNS 解析后再次校验 IP 地址（防 DNS Rebinding）。\n"
                "3. 限制服务器出站网络请求权限。"
            ),
            "file_upload_testing":    (
                "1. 校验文件类型：同时检查 MIME 类型和文件魔术字节（不信任扩展名）。\n"
                "2. 上传后重命名文件，去除可执行属性。\n"
                "3. 将上传文件存储在 Web 根目录之外，通过应用层提供下载。\n"
                "4. 配置 Web 服务器禁止执行上传目录中的脚本。"
            ),
            "idor_testing":           (
                "1. **每次请求**都在服务端验证当前用户是否有权访问目标资源。\n"
                "2. 使用不可枚举的随机 UUID 替代顺序 ID。\n"
                "3. 不要在前端隐藏 ID 以为安全，应在后端强制鉴权。"
            ),
            "ssti_testing":           (
                "1. 避免将用户输入直接传入模板渲染函数。\n"
                "2. 在沙箱模式下运行模板引擎（如 Jinja2 sandbox）。\n"
                "3. 对用户输入进行严格过滤，禁止 `{{`、`{%` 等模板特殊字符。"
            ),
            "deserialization_testing": (
                "1. 避免反序列化不可信来源的数据。\n"
                "2. 使用加密签名（HMAC）验证序列化数据完整性。\n"
                "3. 升级存在已知反序列化漏洞的第三方库（如 Apache Commons Collections）。\n"
                "参考：https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html"
            ),
            "nosql_injection":        (
                "1. 对 NoSQL 操作符（`$where`、`$gt`、`$regex` 等）进行过滤和转义。\n"
                "2. 使用 ODM/ORM 层代替原始查询。\n"
                "3. 校验输入类型，拒绝意外的对象/数组类型输入。"
            ),
            "cve_skill":              (
                "1. **立即**：升级受影响组件至官方已修复版本。\n"
                "2. 参考对应 CVE 公告和厂商安全公告进行修复。\n"
                "3. 修复前在 WAF 中添加虚拟补丁规则阻断利用流量。\n"
                "4. 建立漏洞管理流程，定期扫描已知 CVE。"
            ),
            "wordpress_rce":          (
                "1. 更新 WordPress 核心及所有插件/主题至最新版本。\n"
                "2. 在 `wp-config.php` 中设置 `define('DISALLOW_FILE_EDIT', true);` 禁用主题编辑器。\n"
                "3. 管理员账户使用强密码并启用 2FA。\n"
                "4. 限制 `/wp-admin` 和 `/wp-login.php` 的访问 IP。"
            ),
            "fuel_cms_rce":           (
                "1. **立即升级** Fuel CMS 至 1.4.2 或更高版本（已修复 CVE-2018-16763）。\n"
                "2. 若无法立即升级，临时禁用 `/fuel/pages/select/` 路由或下线 CMS 管理入口。\n"
                "3. 在 WAF 中添加规则过滤 `filter` 参数中的 PHP 代码特征。\n"
                "参考：https://nvd.nist.gov/vuln/detail/CVE-2018-16763"
            ),
            "jangow_full_pwn":        (
                "1. **修复命令注入**：重写 busque.php，使用参数化方式或彻底删除该功能。\n"
                "2. **保护配置文件**：WordPress config.php 不应包含可从 Web 读取的明文数据库凭据。\n"
                "3. **升级内核**：将 Linux 内核升级至 4.4.0-92 或更高版本，修复 CVE-2017-16995。\n"
                "4. **最小权限**：Web 服务账户（www-data）不应能访问其他用户目录或系统敏感文件。"
            ),
            "jangow_cmd_injection":   (
                "1. **立即**：删除或重写 busque.php，禁止将 GET/POST 参数传入 system()。\n"
                "2. 若必须保留搜索功能，使用安全 API（如数据库全文检索）替代 OS 命令。\n"
                "3. 配置 Web 服务器 WAF 规则过滤常见命令注入特征（`;`、`|`、`$()`等）。"
            ),
            "s2_045":                 (
                "1. **立即升级** Apache Struts2 至 2.5.10.1 或更高版本。\n"
                "2. 如无法立即升级，配置 WAF 过滤 Content-Type 头中包含 `multipart/form-data` 时的 OGNL 表达式。\n"
                "3. 禁用不必要的 Struts2 插件（如 Jakarta Multipart）。\n"
                "参考：https://nvd.nist.gov/vuln/detail/CVE-2017-5638"
            ),
            "activemq_rce":           (
                "1. **立即升级** Apache ActiveMQ 至 5.15.16 / 5.16.7 / 5.17.6 / 5.18.3 或更高版本。\n"
                "2. 若无法立即升级，通过防火墙限制 61616 端口仅对可信 IP 开放。\n"
                "3. 禁用不必要的 OpenWire 协议支持。\n"
                "参考：https://nvd.nist.gov/vuln/detail/CVE-2023-46604"
            ),
            "cve_2021_4034":          (
                "1. 升级 polkit 至 0.120 或更高版本（已包含修复补丁）。\n"
                "2. 作为临时缓解：`chmod 0755 /usr/bin/pkexec` 移除 SUID 位。\n"
                "3. 使用 `rpm -q polkit` 或 `dpkg -l policykit-1` 确认版本。\n"
                "参考：https://nvd.nist.gov/vuln/detail/CVE-2021-4034"
            ),
            "cve_2017_16995":         (
                "1. 升级 Linux 内核至 4.14.11 / 4.9.75 / 4.4.109 或更高版本。\n"
                "2. 禁用非特权用户的 eBPF：`sysctl -w kernel.unprivileged_bpf_disabled=1`。\n"
                "参考：https://nvd.nist.gov/vuln/detail/CVE-2017-16995"
            ),
            "openssh_user_enum":      (
                "1. 升级 OpenSSH 至 7.8 或更高版本。\n"
                "2. 确保认证失败响应时间一致，防止基于时间的枚举。"
            ),
            "privesc_linux":          (
                "1. 定期使用 `linux-exploit-suggester` 扫描内核 CVE。\n"
                "2. 检查 SUID/SGID 文件：`find / -perm -4000 2>/dev/null`。\n"
                "3. 审查 sudo 配置，避免不必要的无密码权限。\n"
                "4. 及时更新系统补丁。"
            ),
        }

        # ── 整理端口 ──────────────────────────────────────────
        ports = self.ctx.collected_info.get("ports", [])
        port_lines = []
        for p in ports:
            if isinstance(p, dict):
                port_lines.append(
                    f"| {p.get('port','?')} | {p.get('service','未知')} | {p.get('state','open')} | {p.get('version','') or '-'} |"
                )
            else:
                port_lines.append(f"| {p} | - | open | - |")

        # ── 整理漏洞发现 ──────────────────────────────────────
        vuln_findings = [f for f in self.ctx.findings if f.get("type") != "open_ports"]

        # 风险评级
        sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in vuln_findings:
            s = f.get("severity", "info")
            sev_counts[s] = sev_counts.get(s, 0) + 1

        if sev_counts["critical"] > 0:
            risk_level = "严重 🔴"
            risk_desc  = "目标系统存在**严重漏洞**，攻击者可能已获取或能够轻易获取系统完整控制权，建议立即停止对外服务并进行应急修复。"
        elif sev_counts["high"] > 0:
            risk_level = "高危 🟠"
            risk_desc  = "目标系统存在**高危漏洞**，可能导致数据泄露、系统被控或服务中断，建议在 48 小时内完成修复。"
        elif sev_counts["medium"] > 0:
            risk_level = "中危 🟡"
            risk_desc  = "目标系统存在**中危漏洞**，存在一定安全风险，建议在 2 周内安排修复计划。"
        elif sev_counts["low"] > 0:
            risk_level = "低危 🔵"
            risk_desc  = "目标系统存在**低危漏洞**，风险较小，建议在版本迭代时修复。"
        else:
            risk_level = "安全 ✅"
            risk_desc  = "未发现明显安全漏洞，建议保持定期安全评估和漏洞扫描。"

        # 执行摘要关键发现
        key_findings = []
        for f in vuln_findings:
            ftype = f.get("type", "")
            _dk = f.get("skill_id", "") if ftype == "cve_skill" else ftype
            name_cn = TYPE_CN.get(_dk) or TYPE_CN.get(ftype) or (_dk or ftype).replace("_", " ").upper()
            sev = f.get("severity", "info")
            emoji = SEV_EMOJI.get(sev, "⚪")
            key_findings.append(f"{emoji} **{name_cn}** [{SEV_CN.get(sev, sev)}]")

        # ── 构建漏洞详情块 ────────────────────────────────────
        vuln_blocks = []
        for i, f in enumerate(vuln_findings, 1):
            ftype    = f.get("type", "unknown")
            sev      = f.get("severity", "info")
            skill_id = f.get("skill_id", "")
            _dk      = skill_id if ftype == "cve_skill" else ftype
            name_cn  = TYPE_CN.get(_dk) or TYPE_CN.get(ftype) or (_dk or ftype).replace("_", " ").upper()
            emoji    = SEV_EMOJI.get(sev, "⚪")
            sev_cn   = SEV_CN.get(sev, sev)

            # CVSS
            cvss_key = _dk or ftype
            cvss_info = CVSS_SCORES.get(cvss_key, CVSS_SCORES.get(ftype))
            if cvss_info:
                cvss_line = f"  - **CVSS 评分**: `{cvss_info[0]}` — `{cvss_info[1]}`"
            else:
                cvss_line = ""

            # 漏洞描述
            desc_key = _dk or ftype
            desc = VULN_DESC.get(desc_key) or VULN_DESC.get(ftype) or f.get("description") or "详细描述待补充。"

            # 证据（格式化为代码块）
            evidence = f.get("evidence") or ""
            ev_lines = [line.strip() for line in evidence.splitlines() if line.strip()]
            if ev_lines:
                ev_block = "```\n" + "\n".join(ev_lines) + "\n```"
            else:
                ev_block = "  *（无详细证据记录）*"

            # 攻击步骤
            steps_key = _dk or ftype
            steps = ATTACK_STEPS.get(steps_key) or ATTACK_STEPS.get(ftype)
            if steps:
                steps_block = "\n".join(f"  {j}. {s}" for j, s in enumerate(steps, 1))
            else:
                steps_block = "  参见漏洞描述。"

            block = (
                f"### {i}. {emoji} {name_cn}\n\n"
                f"| 字段 | 内容 |\n"
                f"|------|------|\n"
                f"| **严重程度** | {sev_cn} {emoji} |\n"
                f"| **目标** | `{f.get('target', target)}` |\n"
                f"| **漏洞类型** | `{ftype}` |\n"
            )
            if cvss_line:
                block += f"| **CVSS 评分** | `{cvss_info[0]}` |\n"
                block += f"| **CVSS 向量** | `{cvss_info[1]}` |\n"

            block += (
                f"\n**漏洞描述**\n\n"
                f"{desc}\n\n"
                f"**证据 / 输出**\n\n"
                f"{ev_block}\n\n"
                f"**利用步骤**\n\n"
                f"{steps_block}"
            )
            vuln_blocks.append(block)

        # ── 修复建议 ──────────────────────────────────────────
        advice_lines = []
        seen_advices = set()
        for f in vuln_findings:
            ftype    = f.get("type", "")
            skill_id = f.get("skill_id", "")
            advice_key = skill_id if (ftype == "cve_skill" and skill_id in FIX_ADVICE) else ftype
            if not advice_key or advice_key not in FIX_ADVICE:
                advice_key = "cve_skill" if ftype == "cve_skill" else ftype
            if advice_key in FIX_ADVICE and advice_key not in seen_advices:
                seen_advices.add(advice_key)
                _dk = skill_id if ftype == "cve_skill" else ftype
                name_cn = TYPE_CN.get(_dk) or TYPE_CN.get(ftype) or (_dk or ftype).replace("_", " ").title()
                sev = f.get("severity", "info")
                emoji = SEV_EMOJI.get(sev, "⚪")
                advice_lines.append(f"#### {emoji} {name_cn}\n\n{FIX_ADVICE[advice_key]}")

        # ── 执行过程 ──────────────────────────────────────────
        TASK_CN = {
            "nmap_scan":        "端口扫描 (nmap)",
            "nikto_scan":       "Web 漏洞扫描 (nikto)",
            "sqlmap_scan":      "SQL 注入扫描 (sqlmap)",
            "gobuster_scan":    "目录枚举 (gobuster)",
            "dirsearch_scan":   "目录枚举 (dirsearch)",
            "nuclei_scan":      "漏洞模板扫描 (nuclei)",
            "subfinder_scan":   "子域名枚举 (subfinder)",
            "hydra_bruteforce": "密码爆破 (hydra)",
        }
        seen_tasks: dict = {}
        for h in self.ctx.history:
            name = h.get("task", "unknown")
            seen_tasks[name] = h.get("success", False)

        task_lines = []
        for name, success in seen_tasks.items():
            display = TASK_CN.get(name, name)
            if name.startswith("skill_"):
                sid = name[6:]
                display = TYPE_CN.get(sid, sid.replace("_", " ").upper()) + " [Skill]"
            status = "✅ 成功" if success else "❌ 无发现"
            task_lines.append(f"| {display} | {status} |")

        # ── 拼装完整报告 ──────────────────────────────────────
        total_vulns = len(vuln_findings)
        sections = []

        # 封面信息
        sections.append(
            f"# 渗透测试安全评估报告\n\n"
            f"| 项目 | 详情 |\n"
            f"|------|------|\n"
            f"| **测试目标** | `{target}` |\n"
            f"| **报告生成时间** | {now} |\n"
            f"| **测试迭代轮次** | {self.ctx.iteration} 轮 |\n"
            f"| **发现漏洞总数** | {total_vulns} 项 |\n"
            f"| **整体风险等级** | {risk_level} |\n"
            f"| **报告生成工具** | ClawAI 自动化渗透测试系统 |"
        )

        # 执行摘要
        exec_summary_lines = [
            f"本次针对目标 `{target}` 的自动化渗透测试共执行 **{self.ctx.iteration} 轮**迭代，"
            f"共发现 **{total_vulns}** 项安全问题。",
            f"\n整体风险评级为 **{risk_level}**。{risk_desc}",
        ]
        if key_findings:
            exec_summary_lines.append("\n**关键发现**：\n\n" + "\n".join(f"- {kf}" for kf in key_findings))
        else:
            exec_summary_lines.append("\n未发现可利用漏洞，系统安全状况良好。")

        if sev_counts["critical"] + sev_counts["high"] > 0:
            exec_summary_lines.append(
                "\n> ⚠️ **风险提示**：本报告中发现的高危/严重漏洞已可被攻击者在真实环境中利用，"
                "建议安全团队立即跟进处理。"
            )

        sections.append(f"\n---\n\n## 一、执行摘要\n\n" + "\n".join(exec_summary_lines))

        # 风险分布
        sections.append(
            f"\n## 二、风险分布\n\n"
            f"{risk_desc}\n\n"
            f"| 严重程度 | 图示 | 数量 | 说明 |\n"
            f"|--------|------|------|------|\n"
            f"| 严重 | 🔴 | {sev_counts['critical']} | 可被直接利用，需立即处理 |\n"
            f"| 高危 | 🟠 | {sev_counts['high']} | 重大安全风险，建议 48h 内修复 |\n"
            f"| 中危 | 🟡 | {sev_counts['medium']} | 中等风险，建议近期修复 |\n"
            f"| 低危 | 🔵 | {sev_counts['low']} | 低风险，版本迭代时修复 |\n"
            f"| 信息 | ⚪ | {sev_counts['info']} | 信息收集，无直接危害 |"
        )

        # 开放端口
        sections.append(f"\n## 三、信息收集 / 开放端口")
        if port_lines:
            sections.append(
                "| 端口 | 服务 | 状态 | 版本 |\n"
                "|------|------|------|------|\n" +
                "\n".join(port_lines)
            )
        else:
            sections.append("  未发现开放端口信息（可能未执行端口扫描）。")

        # 漏洞详情
        sections.append(f"\n## 四、漏洞详情（共 {total_vulns} 项）")
        if vuln_blocks:
            sections.append("\n\n---\n\n".join(vuln_blocks))
        else:
            sections.append("  本次测试未发现明显安全漏洞。")

        # 修复建议
        sections.append(f"\n## 五、修复建议")
        if advice_lines:
            sections.append(
                "> 以下修复建议按发现漏洞优先级排列，建议优先处理严重/高危项目。\n\n" +
                "\n\n---\n\n".join(advice_lines)
            )
        else:
            sections.append(
                "  建议参考以下安全加固规范：\n\n"
                "  - [OWASP Top 10](https://owasp.org/www-project-top-ten/)\n"
                "  - [OWASP 测试指南](https://owasp.org/www-project-web-security-testing-guide/)\n"
                "  - 定期进行渗透测试和漏洞扫描"
            )

        # 执行过程
        sections.append(f"\n## 六、执行过程")
        if task_lines:
            sections.append(
                "| 任务 / 工具 | 执行结果 |\n"
                "|------------|----------|\n" +
                "\n".join(task_lines)
            )
        else:
            sections.append("  - 无执行记录")

        # 附录
        sections.append(
            f"\n## 七、附录\n\n"
            f"### 测试声明\n\n"
            f"本报告由 ClawAI 自动化渗透测试系统生成，仅用于授权安全评估目的。"
            f"所有测试活动均在授权范围内进行，测试结果仅反映测试时间点的安全状态。\n\n"
            f"### 参考标准\n\n"
            f"- OWASP Web Security Testing Guide v4.2\n"
            f"- CVE (Common Vulnerabilities and Exposures)\n"
            f"- CVSS v3.1 (Common Vulnerability Scoring System)\n"
            f"- NIST SP 800-115 Technical Guide to Information Security Testing\n\n"
            f"### 免责声明\n\n"
            f"本报告中描述的漏洞信息仅供授权的安全人员用于防御目的。"
            f"未经授权将本报告内容用于攻击目的，将承担相应法律责任。"
        )

        sections.append(f"\n---\n\n*本报告由 ClawAI 自动生成 · {now} · 请在安全环境中妥善保管*")

        return "\n\n".join(sections)
