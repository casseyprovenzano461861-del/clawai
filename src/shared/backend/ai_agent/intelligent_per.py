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
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """获取工具定义（包含技能）"""
        tools = [
            {"name": "nmap_scan", "description": "端口扫描，发现开放端口和服务", "category": "recon"},
            {"name": "whatweb_scan", "description": "Web技术栈识别", "category": "recon"},
            {"name": "nuclei_scan", "description": "基于模板的漏洞扫描", "category": "vuln"},
            {"name": "sqlmap_scan", "description": "SQL注入检测和利用", "category": "vuln"},
            {"name": "nikto_scan", "description": "Web服务器漏洞扫描", "category": "vuln"},
            {"name": "dirsearch_scan", "description": "目录和文件爆破", "category": "recon"},
            {"name": "httpx_probe", "description": "HTTP服务探测", "category": "recon"},
            {"name": "ffuf_scan", "description": "模糊测试，目录/DNS/子域名", "category": "recon"},
            {"name": "subfinder_scan", "description": "子域名发现", "category": "recon"},
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

## 信息缺口
{json.dumps(gaps_data, ensure_ascii=False, indent=2) if gaps_data else '需要发现目标的开放端口和服务'}
{rag_hint}
## 可用工具
{json.dumps([{"name": t["name"], "desc": t["description"]} for t in regular_tools], ensure_ascii=False, indent=2)}
{skills_hint}
## 任务
**重要：目标是 {target}，必须扫描这个目标！**

选择 1-2 个最需要执行的扫描任务（必须包含 target 参数）：
1. 如果是第一次迭代，优先执行 nmap_scan 发现端口
2. 如果已发现端口，根据服务选择后续扫描
3. 如果发现漏洞迹象，使用对应的 skill_xxx 技能
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
        """Planner 系统提示词"""
        return """你是一个专业的渗透测试规划专家。你的职责是:
1. 分析当前收集的信息
2. 识别信息缺口
3. 选择最合适的工具来填补缺口
4. 生成执行计划

渗透测试阶段:
1. 信息收集: nmap_scan, whatweb_scan, dirsearch_scan
2. 漏洞扫描: nuclei_scan, sqlmap_scan
3. 漏洞利用: 
   - skill_sqli_basic: SQL注入基础检测
   - skill_sqli_union: SQL注入UNION利用
   - skill_sqli_time_blind: SQL注入时间盲注检测
   - skill_xss_reflected: 反射型XSS检测
   - skill_auth_bypass_sql: SQL认证绕过
   - skill_auth_bruteforce: 认证暴力破解
   - skill_rce_command_injection: 命令注入检测
   - skill_lfi_basic: 本地文件包含检测
   - skill_dvwa_sqli: DVWA SQL注入利用
   - skill_dvwa_xss: DVWA XSS利用
   - skill_dvwa_bruteforce: DVWA暴力破解

重要规则:
- 第一次迭代执行信息收集 (nmap_scan, whatweb_scan)
- 发现Web应用后执行漏洞扫描 (nuclei_scan)
- 发现SQL注入迹象后使用 skill_sqli_* 技能
- 发现登录页面后尝试 skill_auth_bypass_sql 或 skill_auth_bruteforce
- 针对 DVWA 使用 skill_dvwa_* 系列技能
- 不要执行 get_tool_status 等管理工具
- 每次迭代选择 1-2 个工具执行"""
    
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
                    except:
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
        return """你是一个渗透测试结果分析专家。你的职责是:
1. 分析扫描结果，提取有价值的信息
2. 评估测试目标的完成度
3. 提出后续建议

分析原则:
- 关注开放的端口和服务
- 关注发现的漏洞和安全问题
- 评估风险等级
- 考虑是否需要深入测试

重要规则:
- 只有完成漏洞利用才算目标达成
- 发现Web应用后需要继续进行漏洞扫描
- 发现数据库端口后需要尝试SQL注入
- 发现登录页面后需要尝试暴力破解
- 不要轻易说目标达成或无需继续"""
    
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
            self.ctx.collected_info["ports"] = output.get("ports", [])
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
        
        if isinstance(output, dict):
            # 端口发现
            if "ports" in output:
                ports = output["ports"]
                if isinstance(ports, list) and len(ports) > 0:
                    findings.append({
                        "type": "open_ports",
                        "count": len(ports),
                        "ports": [p.get("port") for p in ports[:5]]
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
        """生成最终报告"""
        lines = [
            "# 渗透测试报告",
            "",
            f"**目标**: {self.ctx.target}",
            f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**迭代次数**: {self.ctx.iteration}",
            f"**RAG 查询次数**: {self.ctx.rag_queries}",
            f"**Token 消耗**: {self.ctx.budget_used}",
            "",
            "## 收集的信息",
            ""
        ]
        
        for key, value in self.ctx.collected_info.items():
            lines.append(f"- **{key}**: {json.dumps(value, ensure_ascii=False)[:200]}")
        
        lines.extend([
            "",
            "## 发现",
            ""
        ])
        
        if self.ctx.findings:
            for i, f in enumerate(self.ctx.findings[:10], 1):
                lines.append(f"{i}. {json.dumps(f, ensure_ascii=False)[:200]}")
        else:
            lines.append("暂无重要发现")
        
        return "\n".join(lines)
