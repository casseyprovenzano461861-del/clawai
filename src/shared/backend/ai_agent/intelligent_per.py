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
                
                plan_result = await self._plan()
                yield {
                    "type": "plan", 
                    "tasks": [t.name for t in self.ctx.plan],
                    "rag_used": plan_result.get("rag_context_used", False),
                    "gaps_identified": plan_result.get("gaps_identified", 0)
                }
                
                # === EXECUTOR 阶段 ===
                self.ctx.phase = PERPhase.EXECUTING
                
                for i, task in enumerate(self.ctx.plan):
                    if task.status == "completed":
                        continue
                    
                    self.ctx.current_task_index = i
                    yield {"type": "task_start", "task": task.name, "index": i}
                    
                    # 执行任务
                    result = await self._execute_task(task)
                    
                    yield {
                        "type": "task_result",
                        "task": task.name,
                        "success": result.get("success", False),
                        "simulated": result.get("simulated", True),
                        "findings": self._extract_findings(result)
                    }
                    
                    # 更新收集的信息
                    self._update_collected_info(task, result)
                
                # === REFLECTOR 阶段 ===
                self.ctx.phase = PERPhase.REFLECTING
                yield {"type": "phase", "phase": "reflecting", "message": "AI 正在分析结果..."}
                
                reflection = await self._reflect()
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
                # 使用精简规划
                self.ctx.plan = [
                    Task(
                        id=f"minimal_{self.ctx.iteration}",
                        name="nmap_scan",
                        tool="nmap_scan",
                        params={"target": self.ctx.target},
                        priority=0
                    )
                ]
                return {"tasks": 1, "budget_limited": True}
        
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
        
        response = self.llm_client.chat(messages, tools=self._get_tools_schema())
        
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
        collected = json.dumps(self.ctx.collected_info, indent=2, ensure_ascii=False)[:2000]
        
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
        
        # 分离工具和技能
        regular_tools = [t for t in self.tools if not t.get("is_skill")]
        skill_tools = [t for t in self.tools if t.get("is_skill")]
        
        # 构建技能列表
        skills_hint = ""
        if skill_tools:
            skills_list = "\n".join([
                f"- {s['name']}: {s['description']}" 
                for s in skill_tools[:10]
            ])
            skills_hint = f"""
## 可用技能（POC/Exploit）
{skills_list}

使用技能时，直接调用 skill_xxx，参数会自动填充。
"""
        
        prompt = f"""
## 当前状态
- 目标: {target}
- 迭代: {iteration}/{self.ctx.max_iterations}
- 已收集信息: {collected if collected != '{}' else '无'}{budget_hint}
- 已执行任务（**不要重复这些**）: {', '.join(list({t['task'] for t in self.ctx.history})) or '无'}

## 信息缺口
{json.dumps(gaps_data, ensure_ascii=False, indent=2) if gaps_data else '需要发现目标的开放端口和服务'}
{rag_hint}
## 可用工具
{json.dumps([{"name": t["name"], "desc": t["description"]} for t in regular_tools], ensure_ascii=False, indent=2)}
{skills_hint}
## 任务
**重要：目标是 {target}，必须扫描这个目标！**

选择 1-2 个**尚未执行过**的扫描任务（必须包含 target 参数）：
1. 如果是第一次迭代，优先执行 nmap_scan 发现端口
2. 如果已发现端口，根据服务选择**新的**漏洞检测技能
3. 如果某技能已失败，换其他技能，不要重试
4. 如果已发现漏洞，可以停止或补充其他类型检测
4. 每个任务必须指定 target 参数为 {target}

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

        return f"""你是一个专业的渗透测试规划专家。你的职责是:
1. 分析当前收集的信息
2. 识别信息缺口
3. 选择最合适的工具来填补缺口
4. 生成执行计划

当前可用的扫描工具（只能选这些，不要选其他工具）:
{tools_str}

可用的技能工具（skill_ 前缀）:
- skill_sqli_basic: SQL注入基础检测
- skill_sqli_union: SQL注入UNION利用
- skill_sqli_time_blind: SQL注入时间盲注
- skill_xss_reflected: 反射型XSS检测
- skill_xss_stored: 存储型XSS检测
- skill_auth_bypass_sql: SQL认证绕过
- skill_auth_bruteforce: 认证暴力破解
- skill_rce_command_injection: 命令注入检测
- skill_lfi_basic: 本地文件包含检测
- skill_csrf_testing: CSRF漏洞检测
- skill_xxe_testing: XXE漏洞检测
- skill_ssrf_testing: SSRF漏洞检测
- skill_file_upload_testing: 文件上传漏洞
- skill_idor_testing: IDOR越权检测
- skill_ssti_testing: 模板注入检测
- skill_dvwa_sqli: DVWA SQL注入
- skill_dvwa_xss: DVWA XSS
- skill_dvwa_bruteforce: DVWA暴力破解

重要规则:
- 只使用上面列出的可用工具，不要使用未列出的工具
- 第一次迭代优先执行 nmap_scan
- 发现Web应用后，使用 skill_* 技能进行漏洞检测
- 针对 DVWA 使用 skill_dvwa_* 系列技能
- 针对 pikachu 靶场优先测试: skill_csrf_testing, skill_xss_reflected, skill_sqli_basic
- **绝对不要重复执行已经执行过且失败的任务**
- 每次迭代选择 1-2 个【未执行过的】任务"""
    
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
        
        # 如果还是没有任务，使用默认计划
        if not tasks:
            logger.info("使用默认计划")
            tasks = [
                Task(id="default_1", name="nmap_scan", tool="nmap_scan", 
                     params={"target": self.ctx.target}, priority=0)
            ]
        
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
        
        response = self.llm_client.chat(messages)
        
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
        # 更准确的检测：只有在明确的肯定语境中才算达成
        goal_achieved = False
        if content:
            # 检查是否有明确的达成标志
            positive_indicators = [
                "目标已达成", "测试已完成", "无需继续测试",
                "已完成所有", "成功获取", "漏洞已利用"
            ]
            negative_indicators = [
                "目标未达成", "需要继续", "尚未完成", "未完成"
            ]
            
            has_positive = any(ind in content for ind in positive_indicators)
            has_negative = any(ind in content for ind in negative_indicators)
            
            # 只有没有否定词且有肯定词时才算达成
            if has_positive and not has_negative:
                goal_achieved = True
        
        need_more = not goal_achieved and self.ctx.iteration < self.ctx.max_iterations
        
        # 如果有高优先级缺口，继续工作
        if new_gaps and len([g for g in new_gaps if hasattr(g, 'priority') and g.priority <= 2]) > 0:
            need_more = True
        
        return {
            "summary": content[:500],
            "goal_achieved": goal_achieved,
            "need_more_work": need_more,
            "new_gaps": len(new_gaps),
            "exploit_knowledge_used": bool(exploit_knowledge)
        }
    
    def _build_enhanced_reflector_prompt(self, exploit_knowledge: str = "") -> str:
        """构建增强的 Reflector 提示词"""
        history = json.dumps(self.ctx.history[-5:], indent=2, ensure_ascii=False)[:3000]
        findings = json.dumps(self.ctx.findings, indent=2, ensure_ascii=False)[:1000]
        
        exploit_hint = ""
        if exploit_knowledge:
            exploit_hint = f"\n## 相关漏洞利用知识\n{exploit_knowledge[:1000]}\n"
        
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
        
        elif task.tool == "whatweb_scan":
            self.ctx.collected_info["technologies"] = output.get("technologies", [])
        
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
        """生成结构化可读报告"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        target = self.ctx.target

        # ── 整理端口 ──────────────────────────────────────────
        ports = self.ctx.collected_info.get("ports", [])
        port_lines = []
        for p in ports:
            if isinstance(p, dict):
                port_lines.append(
                    f"  - **{p.get('port')}**/{p.get('service','?')}  状态: {p.get('state','open')}"
                )
            else:
                port_lines.append(f"  - **{p}**")

        # ── 整理漏洞发现 ──────────────────────────────────────
        SEV_CN = {
            "critical": "严重", "high": "高危",
            "medium": "中危", "low": "低危", "info": "信息",
        }
        SEV_EMOJI = {
            "critical": "🔴", "high": "🟠",
            "medium": "🟡", "low": "🔵", "info": "⚪",
        }
        TYPE_CN = {
            "csrf_testing":           "CSRF 跨站请求伪造",
            "sqli_basic":             "SQL 注入",
            "sqli_union":             "SQL 联合注入",
            "sqli_time_blind":        "SQL 时间盲注",
            "xss_reflected":          "反射型 XSS",
            "xss_stored":             "存储型 XSS",
            "auth_bypass_sql":        "SQL 认证绕过",
            "auth_bruteforce":        "暴力破解",
            "rce_command_injection":  "远程命令执行 (RCE)",
            "lfi_basic":              "本地文件包含 (LFI)",
            "xxe_testing":            "XML 外部实体 (XXE)",
            "ssrf_testing":           "服务器端请求伪造 (SSRF)",
            "file_upload_testing":    "文件上传漏洞",
            "idor_testing":           "越权访问 (IDOR)",
            "ssti_testing":           "模板注入 (SSTI)",
            "deserialization_testing":"反序列化漏洞",
            "nosql_injection":        "NoSQL 注入",
            "waf_detect":             "WAF 检测",
        }

        vuln_findings = [f for f in self.ctx.findings if f.get("type") != "open_ports"]
        vuln_blocks = []
        for i, f in enumerate(vuln_findings, 1):
            ftype    = f.get("type", "unknown")
            sev      = f.get("severity", "info")
            name_cn  = TYPE_CN.get(ftype, ftype.replace("_", " ").upper())
            emoji    = SEV_EMOJI.get(sev, "⚪")
            sev_cn   = SEV_CN.get(sev, sev)
            evidence = f.get("evidence", "")
            # 把 evidence 里的换行整理成缩进列表
            ev_lines = []
            for line in evidence.splitlines():
                line = line.strip()
                if line:
                    ev_lines.append(f"    - {line}")
            ev_block = "\n".join(ev_lines) if ev_lines else "    - （无详细证据）"
            vuln_blocks.append(
                f"### {i}. {emoji} {name_cn}  [{sev_cn}]\n"
                f"  - **目标**: `{f.get('target', target)}`\n"
                f"  - **证据**:\n{ev_block}"
            )

        # ── 整理执行任务 ──────────────────────────────────────
        TASK_CN = {
            "nmap_scan":   "端口扫描 (nmap)",
            "nikto_scan":  "Web 漏洞扫描 (nikto)",
            "sqlmap_scan": "SQL 注入扫描 (sqlmap)",
        }
        seen_tasks = {}
        for h in self.ctx.history:
            name = h.get("task", "unknown")
            seen_tasks[name] = h.get("success", False)

        task_lines = []
        for name, success in seen_tasks.items():
            display = TASK_CN.get(name, name)
            if name.startswith("skill_"):
                skill_id = name[6:]
                display = TYPE_CN.get(skill_id, skill_id.replace("_", " ").upper()) + " 技能"
            status = "✅ 成功" if success else "❌ 无发现"
            task_lines.append(f"  - {display}  {status}")

        # ── 风险评级 ──────────────────────────────────────────
        sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in vuln_findings:
            s = f.get("severity", "info")
            sev_counts[s] = sev_counts.get(s, 0) + 1

        if sev_counts["critical"] > 0:
            risk_level, risk_desc = "严重 🔴", "存在严重漏洞，建议立即修复，可能被攻击者完全控制系统。"
        elif sev_counts["high"] > 0:
            risk_level, risk_desc = "高危 🟠", "存在高危漏洞，建议尽快修复，可能导致数据泄露或系统被控。"
        elif sev_counts["medium"] > 0:
            risk_level, risk_desc = "中危 🟡", "存在中危漏洞，建议在近期安排修复计划。"
        elif sev_counts["low"] > 0:
            risk_level, risk_desc = "低危 🔵", "存在低危漏洞，风险较小，建议在版本迭代时修复。"
        else:
            risk_level, risk_desc = "安全 ✅", "未发现明显漏洞，但建议保持定期安全评估。"

        # ── 修复建议 ──────────────────────────────────────────
        FIX_ADVICE = {
            "csrf_testing":           "在所有表单和 AJAX 请求中加入 CSRF Token 验证；使用 SameSite Cookie 属性。",
            "sqli_basic":             "使用参数化查询（Prepared Statement）替代字符串拼接；对用户输入进行严格过滤。",
            "sqli_union":             "使用 ORM 框架或参数化查询；限制数据库账户权限。",
            "sqli_time_blind":        "同 SQL 注入修复建议，另需设置合理的数据库查询超时。",
            "xss_reflected":          "对所有输出进行 HTML 实体编码；设置 Content-Security-Policy 响应头。",
            "xss_stored":             "存储前进行输入过滤，输出时进行 HTML 编码；启用 CSP。",
            "auth_bypass_sql":        "使用参数化查询处理登录逻辑；不要将用户输入直接拼接到 SQL。",
            "auth_bruteforce":        "启用账户锁定策略；增加验证码；使用多因素认证。",
            "rce_command_injection":  "避免将用户输入传入系统命令；使用白名单验证；使用安全 API 替代 shell 调用。",
            "lfi_basic":              "禁止用户控制文件路径参数；使用白名单限制可访问文件范围。",
            "xxe_testing":            "禁用 XML 解析器的外部实体功能（DTD/外部实体）。",
            "ssrf_testing":           "对内部 URL 请求进行白名单过滤；禁止访问内网 IP 段。",
            "file_upload_testing":    "验证文件类型和内容（MIME + 魔术字节）；上传后重命名并存储于 Web 根目录外。",
            "idor_testing":           "在服务端验证资源所有权；不要依赖前端隐藏 ID。",
            "ssti_testing":           "避免将用户输入直接渲染为模板；使用沙箱模板引擎。",
        }
        advice_lines = []
        for f in vuln_findings:
            ftype = f.get("type", "")
            if ftype in FIX_ADVICE:
                name_cn = TYPE_CN.get(ftype, ftype)
                advice_lines.append(f"- **{name_cn}**: {FIX_ADVICE[ftype]}")

        # ── 拼装完整报告 ──────────────────────────────────────
        sections = []
        sections.append(f"# 渗透测试报告\n")
        sections.append(
            f"| 项目 | 详情 |\n"
            f"|------|------|\n"
            f"| 目标 | `{target}` |\n"
            f"| 测试时间 | {now} |\n"
            f"| 迭代次数 | {self.ctx.iteration} 次 |\n"
            f"| 整体风险 | {risk_level} |"
        )

        sections.append(f"\n---\n\n## 一、开放端口")
        if port_lines:
            sections.append("\n".join(port_lines))
        else:
            sections.append("  - 未发现开放端口")

        sections.append(f"\n## 二、漏洞发现（共 {len(vuln_findings)} 项）")
        if vuln_blocks:
            sections.append("\n\n".join(vuln_blocks))
        else:
            sections.append("  未发现漏洞。")

        sections.append(f"\n## 三、风险评估\n\n{risk_desc}\n\n"
            f"| 严重程度 | 数量 |\n"
            f"|--------|------|\n"
            f"| 🔴 严重 | {sev_counts['critical']} |\n"
            f"| 🟠 高危 | {sev_counts['high']} |\n"
            f"| 🟡 中危 | {sev_counts['medium']} |\n"
            f"| 🔵 低危 | {sev_counts['low']} |\n"
            f"| ⚪ 信息 | {sev_counts['info']} |"
        )

        sections.append(f"\n## 四、修复建议")
        if advice_lines:
            sections.append("\n".join(advice_lines))
        else:
            sections.append("  无具体修复建议（未发现可利用漏洞）。")

        sections.append(f"\n## 五、执行过程")
        if task_lines:
            sections.append("\n".join(task_lines))
        else:
            sections.append("  - 无执行记录")

        sections.append(f"\n---\n*报告由 ClawAI 自动生成 · {now}*")

        return "\n\n".join(sections)
