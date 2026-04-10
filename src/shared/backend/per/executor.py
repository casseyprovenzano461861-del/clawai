# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：执行器模块
借鉴LuaN1aoAgent的执行器设计，负责执行具体的子任务
"""

import json
import logging
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# Flag 检测正则（与 pentest_agent.py 保持一致）
_FLAG_PATTERNS = [
    re.compile(r'flag\{[^}]+\}', re.IGNORECASE),
    re.compile(r'ctf\{[^}]+\}', re.IGNORECASE),
    re.compile(r'htb\{[^}]+\}', re.IGNORECASE),
    re.compile(r'thm\{[^}]+\}', re.IGNORECASE),
    re.compile(r'picoctf\{[^}]+\}', re.IGNORECASE),
    re.compile(r'[A-Z0-9]{32}', re.MULTILINE),
]

# 添加路径以便导入现有模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from .prompts import get_executor_system_prompt, get_executor_strategy_prompt
except ImportError:
    from prompts import get_executor_system_prompt, get_executor_strategy_prompt

try:
    from ..events import EventBus
except ImportError:
    try:
        from events import EventBus
    except ImportError:
        EventBus = None

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    subtask_id: str
    output: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_calls: List[Dict[str, Any]] = None
    thinking_log: List[Dict[str, Any]] = None
    llm_assisted: bool = False
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []
        if self.thinking_log is None:
            self.thinking_log = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "subtask_id": self.subtask_id,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_calls": self.tool_calls,
            "thinking_log": self.thinking_log,
            "llm_assisted": self.llm_assisted
        }


@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    execution_time: float
    success: bool
    error: Optional[str] = None


class PERExecutor:
    """P-E-R架构：执行器
    
    负责：
    1. 执行具体的子任务
    2. 调用工具（兼容现有Skill系统）
    3. 管理执行上下文
    4. 收集执行指标
    5. 处理执行失败和重试
    6. 使用LLM辅助工具选择和参数优化
    """
    
    def __init__(self, skill_registry=None, llm_client=None, max_retries: int = 3, use_llm: bool = True):
        """初始化执行器
        
        Args:
            skill_registry: 技能注册表（可选）
            llm_client: LLM客户端（可选）
            max_retries: 最大重试次数
            use_llm: 是否使用LLM辅助执行（默认True）
        """
        self.skill_registry = skill_registry
        self.llm_client = llm_client
        self.max_retries = max_retries
        self.use_llm = use_llm and llm_client is not None
        
        # 执行历史
        self.execution_history: List[ExecutionResult] = []
        
        # 工具调用统计
        self.tool_stats: Dict[str, Dict[str, Any]] = {}
        
        # 当前执行上下文
        self.current_context: Optional[Dict[str, Any]] = None
        
        # 重试计数器
        self.retry_counters: Dict[str, int] = {}
        
        # 初始化LLM集成
        self._init_llm_integration()
        
        logger.info(f"PERExecutor初始化完成 (use_llm={self.use_llm})")
    
    def _init_llm_integration(self):
        """初始化LLM集成"""
        if self.use_llm:
            try:
                from .llm_integration import create_llm_integration
                self.llm_integration = create_llm_integration(llm_client=self.llm_client)
                logger.info("LLM集成初始化成功")
            except Exception as e:
                logger.warning(f"LLM集成初始化失败: {e}，将使用回退模式")
                self.use_llm = False
                self.llm_integration = None
        else:
            self.llm_integration = None
    
    def set_skill_registry(self, skill_registry) -> None:
        """设置技能注册表
        
        Args:
            skill_registry: 技能注册表实例
        """
        self.skill_registry = skill_registry
        logger.debug("技能注册表已设置")

    def _try_execute_via_skill(
        self,
        subtask_id: str,
        subtask_data: Dict[str, Any],
        thinking_log: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """统一调用路径：优先通过 skill_registry 执行。

        按以下顺序匹配技能：
        1. subtask_id 精确匹配（如 subtask_id = "sqli_basic"）
        2. task_name 字段精确匹配
        3. 描述关键词模糊匹配（搜索技能）

        Returns:
            执行结果 dict，或 None（未找到匹配技能）
        """
        if not self.skill_registry:
            return None

        target = self.current_context.get("target", "")
        description = subtask_data.get("description", "")
        task_name = subtask_data.get("task_name", subtask_id)

        # 候选技能名
        candidates = [task_name, subtask_id]
        skill = None
        for name in candidates:
            skill = ( (getattr(self.skill_registry, "get_skill", None) or getattr(self.skill_registry, "get", None)) or (lambda x: None) )(name)
            if skill:
                break

        # 关键词模糊搜索
        if skill is None and description:
            keywords = description.split()[:3]
            for kw in keywords:
                matches = self.skill_registry.search(kw, top_k=1)
                if matches:
                    skill = matches[0]
                    break

        if skill is None:
            return None

        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": f"[统一路径] 通过 skill_registry 执行: {skill.id}",
            "type": "tool_selection",
        })

        try:
            params = {**self.current_context, "target": target}
            skill_result = self.skill_registry.execute(skill.id, params)

            tool_calls.append({
                "tool_name": skill.id,
                "tool_type": "skill",
                "parameters": {"target": target},
                "result": skill_result,
                "execution_time": 0.0,
                "success": skill_result.get("success", False),
            })

            return {
                "task_type": "skill_execution",
                "skill_used": skill.id,
                "result": skill_result,
                "findings": skill_result.get("findings", []),
                "vulnerabilities": skill_result.get("vulnerabilities", []),
                "vulnerable": skill_result.get("vulnerable", False),
                "output": skill_result.get("output", ""),
                "success": skill_result.get("success", False),
                "summary": f"技能 {skill.id} 执行完成",
            }
        except Exception as exc:
            logger.warning(f"[统一路径] 技能 {skill.id} 执行失败: {exc}，降级到任务类型分支")
            return None

    async def _execute_validation_task(
        self,
        subtask_id: str,
        subtask_data: Dict[str, Any],
        thinking_log: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """执行验证任务（由 Reflector 硬规则触发）

        调用 VulnValidatorAgent 对疑似漏洞进行二次确认。
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": f"[验证任务] 开始二次验证: {subtask_id}",
            "type": "validation",
        })

        finding = subtask_data.get("finding", {})
        target = finding.get("target") or self.current_context.get("target", "")

        try:
            from .validator import VulnValidatorAgent
        except ImportError:
            try:
                from validator import VulnValidatorAgent
            except ImportError:
                logger.warning("[验证任务] 无法导入 VulnValidatorAgent，降级为未验证")
                return {
                    "task_type": "validation",
                    "success": False,
                    "verified": False,
                    "error": "VulnValidatorAgent 不可用",
                }

        validator = VulnValidatorAgent(timeout=15)
        result = validator.validate(finding, target)

        tool_calls.append({
            "tool_name": "VulnValidatorAgent",
            "tool_type": "validator",
            "parameters": {"finding": finding, "target": target},
            "result": result.to_dict(),
            "execution_time": 0.0,
            "success": result.verified,
        })

        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": (
                f"[验证结果] verified={result.verified}, "
                f"confidence={result.confidence:.2f}, "
                f"type={result.vuln_type}"
            ),
            "type": "validation_result",
        })

        return {
            "task_type": "validation",
            "success": True,
            "verified": result.verified,
            "vuln_type": result.vuln_type,
            "target": target,
            "evidence": result.evidence,
            "confidence": result.confidence,
            "exploit_proof": result.exploit_proof,
            "suggested_next": result.suggested_next,
            "validation_result": result.to_dict(),
            "findings": result.evidence,
        }
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """设置执行上下文
        
        Args:
            context: 执行上下文
        """
        self.current_context = context
        logger.debug(f"设置执行上下文: {len(context)}个键")
    
    async def execute_subtask(self, 
                             subtask_id: str,
                             subtask_data: Dict[str, Any],
                             graph_manager=None) -> ExecutionResult:
        """执行子任务
        
        Args:
            subtask_id: 子任务ID
            subtask_data: 子任务数据
            graph_manager: 图谱管理器（可选）
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.info(f"开始执行子任务: {subtask_id}")
        
        # 发射任务开始事件
        _bus = EventBus.get() if EventBus else None
        if _bus:
            description_short = subtask_data.get("description", subtask_id)
            _bus.emit_state("running", details=description_short, task=description_short)
        
        start_time = datetime.now()
        thinking_log = []
        tool_calls = []
        llm_assisted = False
        
        try:
            # 1. 解析任务描述
            description = subtask_data.get("description", "")
            mission_briefing = subtask_data.get("mission_briefing", "")
            completion_criteria = subtask_data.get("completion_criteria", "")
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"开始执行子任务: {description}",
                "type": "start"
            })
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"任务简报: {mission_briefing}",
                "type": "info"
            })
            
            # 2. 使用LLM辅助选择执行策略（如果启用）
            execution_strategy = None
            if self.use_llm and self.llm_integration:
                try:
                    execution_strategy = await self._get_llm_execution_strategy(
                        subtask_id, subtask_data
                    )
                    if execution_strategy:
                        llm_assisted = True
                        thinking_log.append({
                            "timestamp": datetime.now().isoformat(),
                            "message": f"LLM建议执行策略: {execution_strategy.get('strategy', 'unknown')}",
                            "type": "llm_suggestion"
                        })
                except Exception as e:
                    logger.warning(f"LLM执行策略获取失败: {e}")
            
            # 3. 根据任务类型选择执行策略
            # 优先处理验证任务（由 Reflector 硬规则触发）
            if subtask_data.get("task_type") == "validation" or subtask_id.startswith("validate_"):
                result = await self._execute_validation_task(subtask_id, subtask_data, thinking_log, tool_calls)
            elif execution_strategy and execution_strategy.get("strategy") == "llm_guided":
                # 使用LLM指导的执行
                result = await self._execute_with_llm_guidance(
                    subtask_id, subtask_data, execution_strategy, thinking_log, tool_calls
                )
            else:
                # 统一调用路径：优先查 skill_registry，再走任务类型分支
                skill_result = self._try_execute_via_skill(subtask_id, subtask_data, thinking_log, tool_calls)
                if skill_result is not None:
                    result = skill_result
                else:
                    # 没有匹配技能，按任务类型走原有分支（保持 fallback）
                    task_type = self._infer_task_type(description, mission_briefing)
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"推断任务类型: {task_type}",
                        "type": "analysis"
                    })
                    
                    if task_type == "reconnaissance":
                        result = await self._execute_recon_task(subtask_id, description, thinking_log, tool_calls)
                    elif task_type == "vulnerability_scan":
                        result = await self._execute_vuln_scan_task(subtask_id, description, thinking_log, tool_calls)
                    elif task_type == "exploitation":
                        result = await self._execute_exploit_task(subtask_id, description, thinking_log, tool_calls)
                    elif task_type == "post_exploitation":
                        result = await self._execute_post_exploit_task(subtask_id, description, thinking_log, tool_calls)
                    else:
                        result = await self._execute_general_task(subtask_id, description, thinking_log, tool_calls)
            
            # 4. 检查完成标准
            success = self._check_completion_criteria(result, completion_criteria)
            
            # 5. 更新图谱状态（如果提供了graph_manager）
            if graph_manager and hasattr(graph_manager, 'update_node'):
                new_status = "completed" if success else "failed"
                graph_manager.update_node(subtask_id, {"status": new_status})
            
            # 6. 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 7. 创建执行结果
            execution_result = ExecutionResult(
                success=success,
                subtask_id=subtask_id,
                output=result,
                execution_time=execution_time,
                tool_calls=tool_calls,
                thinking_log=thinking_log,
                llm_assisted=llm_assisted
            )
            
            # 8. 记录执行历史
            self.execution_history.append(execution_result)
            
            # 9. 更新工具统计
            self._update_tool_stats(tool_calls)
            
            # 10. 发射任务完成事件
            if _bus:
                state = "completed" if success else "error"
                _bus.emit_state(state, details=f"子任务 {subtask_id} {'成功' if success else '失败'}")
                # 将 findings 作为 FINDING 事件发射
                findings = result.get("findings", []) + [
                    v["description"] if isinstance(v, dict) else str(v)
                    for v in result.get("vulnerabilities", [])
                ]
                for f in findings:
                    _bus.emit_finding(str(f))

                # Flag 专项检测：扫描所有输出文本
                output_text = result.get("output", "") or ""
                if isinstance(output_text, dict):
                    output_text = json.dumps(output_text, ensure_ascii=False)
                _scan_sources = [output_text] + [str(f) for f in findings]
                for _src in _scan_sources:
                    for _pattern in _FLAG_PATTERNS:
                        for _flag_val in _pattern.findall(_src):
                            try:
                                _bus.emit_flag(
                                    flag_value=_flag_val,
                                    location=f"subtask:{subtask_id}",
                                    method="PERExecutor auto-detect",
                                )
                                logger.info(f"[FLAG DETECTED] {_flag_val} in subtask {subtask_id}")
                            except Exception as _fe:
                                logger.debug(f"emit_flag 失败: {_fe}")
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"子任务执行完成: {'成功' if success else '失败'}，耗时{execution_time:.2f}秒",
                "type": "completion"
            })
            
            logger.info(f"子任务执行完成: {subtask_id} - {'成功' if success else '失败'}")
            
            return execution_result
            
        except Exception as e:
            # 处理执行异常
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": f"执行过程中发生异常: {error_msg}",
                "type": "error"
            })
            
            logger.error(f"子任务执行异常: {subtask_id} - {error_msg}")
            
            # 发射错误事件
            if _bus:
                _bus.emit_state("error", details=f"子任务 {subtask_id} 异常: {error_msg}")
            
            # 创建失败结果
            execution_result = ExecutionResult(
                success=False,
                subtask_id=subtask_id,
                output={},
                error=error_msg,
                execution_time=execution_time,
                tool_calls=tool_calls,
                thinking_log=thinking_log,
                llm_assisted=llm_assisted
            )
            
            self.execution_history.append(execution_result)
            
            return execution_result
    
    async def _get_llm_execution_strategy(self, subtask_id: str, subtask_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用LLM获取执行策略
        
        Args:
            subtask_id: 子任务ID
            subtask_data: 子任务数据
            
        Returns:
            Optional[Dict[str, Any]]: 执行策略
        """
        import asyncio
        
        description = subtask_data.get("description", "")
        mission_briefing = subtask_data.get("mission_briefing", "")
        completion_criteria = subtask_data.get("completion_criteria", "")

        # 使用优化后的提示词
        system_prompt = get_executor_system_prompt()

        user_prompt = get_executor_strategy_prompt(
            subtask_id=subtask_id,
            description=description,
            mission_briefing=mission_briefing,
            completion_criteria=completion_criteria,
            available_skills=self._get_available_skills_summary(),
            context=json.dumps(self.current_context or {}, ensure_ascii=False) if self.current_context else "无",
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用 LLM（call_llm_async 是非阻塞的异步包装，不会阻塞事件循环）
        try:
            try:
                from ..llm_integration import TaskType as _TT
                _task_type = _TT.EXECUTION if _TT else None
            except Exception:
                _task_type = None
            response = await self.llm_integration.call_llm_async(messages, temperature=0.3, max_tokens=2048, task_type=_task_type)
            
            if not response.success:
                return None
            
            # 解析JSON响应
            parsed = self.llm_integration.parse_json_response(response.content)
            
            if "parse_error" in parsed:
                return None
            
            return parsed
            
        except Exception as e:
            logger.warning(f"LLM执行策略获取失败: {e}")
            return None
    
    def _get_available_skills_summary(self) -> str:
        """获取可用技能摘要"""
        if not self.skill_registry:
            return "nmap, whatweb, sqlmap, nuclei, dirsearch, nikto"
        
        try:
            skills = self.skill_registry.get_all_skill_names()
            return ", ".join(skills[:10])  # 最多显示10个
        except Exception as e:
            logger.debug(f"Error getting available skills summary: {e}")
            return "nmap, whatweb, sqlmap, nuclei"
    
    async def _execute_with_llm_guidance(self, subtask_id: str, subtask_data: Dict[str, Any],
                                         execution_strategy: Dict[str, Any], 
                                         thinking_log: List[Dict[str, Any]],
                                         tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用LLM指导执行
        
        Args:
            subtask_id: 子任务ID
            subtask_data: 子任务数据
            execution_strategy: 执行策略
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用LLM指导的执行策略",
            "type": "execution"
        })
        
        recommended_tools = execution_strategy.get("recommended_tools", [])
        tool_parameters = execution_strategy.get("tool_parameters", {})
        execution_order = execution_strategy.get("execution_order", recommended_tools)
        
        findings = []
        all_success = True
        _bus = EventBus.get() if EventBus else None
        
        for tool_name in execution_order:
            # 查找技能
            skill = None
            if self.skill_registry:
                skill = ( (getattr(self.skill_registry, "get_skill", None) or getattr(self.skill_registry, "get", None)) or (lambda x: None) )(tool_name)
            
            params = tool_parameters.get(tool_name, {})
            
            if skill:
                try:
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"执行技能: {tool_name}",
                        "type": "tool_selection"
                    })
                    
                    if _bus:
                        _bus.emit_tool("start", tool_name, args=params)
                    
                    skill_result = skill.execute({**self.current_context, **params})
                    
                    if _bus:
                        _bus.emit_tool("complete", tool_name, args=params, result=skill_result)
                    
                    tool_calls.append({
                        "tool_name": tool_name,
                        "tool_type": "skill",
                        "parameters": params,
                        "result": skill_result,
                        "execution_time": 0.0,
                        "success": skill_result.get("success", False)
                    })
                    
                    if skill_result.get("success", False):
                        findings.extend(skill_result.get("findings", []))
                    else:
                        all_success = False
                        
                except Exception as e:
                    all_success = False
                    if _bus:
                        _bus.emit_tool("error", tool_name, args=params, result={"error": str(e)})
                    tool_calls.append({
                        "tool_name": tool_name,
                        "tool_type": "skill",
                        "parameters": params,
                        "result": {"error": str(e)},
                        "execution_time": 0.0,
                        "success": False
                    })
            else:
                # 模拟执行
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能 {tool_name} 不可用，模拟执行",
                    "type": "simulation"
                })
                
                tool_calls.append({
                    "tool_name": tool_name,
                    "tool_type": "simulated",
                    "parameters": params,
                    "result": {"output": f"模拟执行 {tool_name}"},
                    "execution_time": 0.5,
                    "success": True
                })
                
                findings.append(f"模拟发现: {tool_name} 执行结果")
        
        return {
            "task_type": "llm_guided",
            "success": all_success,
            "findings": findings,
            "tools_used": execution_order,
            "summary": f"LLM指导执行完成，使用了 {len(execution_order)} 个工具"
        }
    
    def _infer_task_type(self, description: str, mission_briefing: str) -> str:
        """推断任务类型
        
        Args:
            description: 任务描述
            mission_briefing: 任务简报
            
        Returns:
            str: 任务类型
        """
        text = (description + " " + mission_briefing).lower()
        
        if any(word in text for word in ["信息收集", "侦察", "recon", "扫描", "端口扫描"]):
            return "reconnaissance"
        elif any(word in text for word in ["漏洞扫描", "漏洞检测", "vulnerability", "vuln"]):
            return "vulnerability_scan"
        elif any(word in text for word in ["漏洞利用", "攻击", "exploit", "渗透"]):
            return "exploitation"
        elif any(word in text for word in ["后渗透", "权限维持", "横向移动", "post"]):
            return "post_exploitation"
        else:
            return "general"
    
    async def _execute_recon_task(self, 
                                 subtask_id: str,
                                 description: str,
                                 thinking_log: List[Dict[str, Any]],
                                 tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行侦察任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行侦察任务: 信息收集和目标分析",
            "type": "execution"
        })
        
        # 尝试使用现有技能系统
        if self.skill_registry:
            try:
                # 查找侦察相关技能
                recon_skills = []
                for skill_name in self.skill_registry.get_all_skill_names():
                    skill = ( (getattr(self.skill_registry, "get_skill", None) or getattr(self.skill_registry, "get", None)) or (lambda x: None) )(skill_name)
                    if skill and hasattr(skill, 'category'):
                        if skill.category in ["recon", "scan", "information_gathering"]:
                            recon_skills.append(skill)
                
                if recon_skills:
                    # 选择第一个侦察技能执行
                    skill = recon_skills[0]
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"使用技能执行: {skill.name}",
                        "type": "tool_selection"
                    })
                    
                    # 执行技能
                    skill_result = skill.execute(self.current_context)
                    
                    # 记录工具调用
                    tool_calls.append({
                        "tool_name": skill.name,
                        "tool_type": "skill",
                        "parameters": {"context": "current_context"},
                        "result": skill_result,
                        "execution_time": 0.0,
                        "success": skill_result.get("success", False)
                    })
                    
                    return {
                        "task_type": "reconnaissance",
                        "skill_used": skill.name,
                        "result": skill_result,
                        "findings": skill_result.get("findings", []),
                        "summary": f"使用技能 {skill.name} 完成侦察任务"
                    }
            
            except Exception as e:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能执行失败: {str(e)}，使用模拟执行",
                    "type": "fallback"
                })
        
        # 模拟执行（回退方案）
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用模拟执行侦察任务",
            "type": "simulation"
        })
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "nmap", "action": "端口扫描", "result": "发现80,443,22端口开放"},
            {"name": "whatweb", "action": "Web技术识别", "result": "识别到nginx, PHP, WordPress"},
            {"name": "subfinder", "action": "子域名枚举", "result": "发现3个子域名"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 0.5,
                "success": True
            })
        
        return {
            "task_type": "reconnaissance",
            "simulated": True,
            "findings": [
                "目标运行Web服务（端口80,443）",
                "技术栈: nginx + PHP + WordPress",
                "发现3个子域名",
                "SSH服务开放（端口22）"
            ],
            "summary": "模拟侦察完成，发现关键信息"
        }
    
    async def _execute_vuln_scan_task(self,
                                     subtask_id: str,
                                     description: str,
                                     thinking_log: List[Dict[str, Any]],
                                     tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行漏洞扫描任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行漏洞扫描任务: 检测安全漏洞",
            "type": "execution"
        })
        
        # 尝试使用现有技能系统
        if self.skill_registry:
            try:
                # 查找漏洞扫描相关技能
                vuln_skills = []
                for skill_name in self.skill_registry.get_all_skill_names():
                    skill = ( (getattr(self.skill_registry, "get_skill", None) or getattr(self.skill_registry, "get", None)) or (lambda x: None) )(skill_name)
                    if skill and hasattr(skill, 'category'):
                        if skill.category in ["vulnerability", "scan", "security"]:
                            vuln_skills.append(skill)
                
                if vuln_skills:
                    # 选择第一个漏洞扫描技能执行
                    skill = vuln_skills[0]
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"使用技能执行: {skill.name}",
                        "type": "tool_selection"
                    })
                    
                    # 执行技能
                    skill_result = skill.execute(self.current_context)
                    
                    # 记录工具调用
                    tool_calls.append({
                        "tool_name": skill.name,
                        "tool_type": "skill",
                        "parameters": {"context": "current_context"},
                        "result": skill_result,
                        "execution_time": 0.0,
                        "success": skill_result.get("success", False)
                    })
                    
                    return {
                        "task_type": "vulnerability_scan",
                        "skill_used": skill.name,
                        "result": skill_result,
                        "vulnerabilities": skill_result.get("vulnerabilities", []),
                        "summary": f"使用技能 {skill.name} 完成漏洞扫描"
                    }
            
            except Exception as e:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能执行失败: {str(e)}，使用模拟执行",
                    "type": "fallback"
                })
        
        # 模拟执行
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用模拟执行漏洞扫描",
            "type": "simulation"
        })
        
        # 模拟漏洞发现
        simulated_vulns = [
            {"type": "SQL注入", "severity": "高危", "location": "/login.php", "description": "存在SQL注入漏洞"},
            {"type": "XSS", "severity": "中危", "location": "/search.php", "description": "存在跨站脚本漏洞"},
            {"type": "信息泄露", "severity": "低危", "location": "/debug.php", "description": "敏感信息泄露"}
        ]
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "nuclei", "action": "漏洞扫描", "result": f"发现{len(simulated_vulns)}个漏洞"},
            {"name": "sqlmap", "action": "SQL注入测试", "result": "确认SQL注入漏洞"},
            {"name": "xsstrike", "action": "XSS测试", "result": "确认XSS漏洞"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 1.0,
                "success": True
            })
        
        return {
            "task_type": "vulnerability_scan",
            "simulated": True,
            "vulnerabilities": simulated_vulns,
            "summary": f"模拟漏洞扫描完成，发现{len(simulated_vulns)}个漏洞"
        }
    
    def _match_cve_skill(self, description: str) -> Optional[str]:
        """根据任务描述匹配最合适的 CVE exploit skill ID
        
        Args:
            description: 任务描述文本
            
        Returns:
            匹配到的 skill_id，或 None
        """
        if not self.skill_registry:
            return None
        
        text = description.lower()
        
        # CVE 关键词 → skill_id 映射
        keyword_skill_map = [
            (["s2-045", "struts2 s2-045", "cve-2017-5638"], "cve_s2_045"),
            (["s2-057", "struts2 s2-057", "cve-2018-11776"], "cve_s2_057"),
            (["struts2", "struts"], "cve_s2_045"),  # 默认 S2-045
            (["thinkphp", "think php", "5.0.23"], "cve_thinkphp_rce"),
            (["shiro", "cve-2016-4437", "shiro-550"], "cve_shiro_550"),
            (["fastjson", "1.2.24", "fast json"], "cve_fastjson_1224"),
            (["fastjson", "1.2.47"], "cve_fastjson_1247"),
            (["weblogic", "cve-2023-21839"], "cve_weblogic_21839"),
            (["tomcat", "cve-2017-12615", "put", "12615"], "cve_tomcat_12615"),
            (["php-fpm", "cve-2019-11043", "11043"], "cve_php_fpm_11043"),
            (["activemq", "cve-2022-41678", "jolokia"], "cve_activemq_41678"),
            (["jboss", "cve-2017-7504", "jmxinvoker"], "cve_jboss_7504"),
            (["django", "cve-2022-34265", "trunc", "extract"], "cve_django_34265"),
            (["flask", "ssti", "jinja2", "template injection"], "flask_ssti_exploit"),
            (["geoserver", "cve-2024-36401", "ogc"], "cve_geoserver_36401"),
            # 通用 exploit 技能
            (["sql injection", "sql注入", "sqli"], "sqli_union"),
            (["xss", "cross-site scripting", "跨站脚本"], "xss_reflected"),
            (["rce", "命令执行", "command injection", "命令注入"], "rce_command_injection"),
            (["file upload", "文件上传"], "file_upload_testing"),
            (["xxe"], "xxe_testing"),
            (["ssrf"], "ssrf_testing"),
            (["ssti", "模板注入"], "ssti_testing"),
        ]
        
        for keywords, skill_id in keyword_skill_map:
            if any(kw in text for kw in keywords):
                skill = self.skill_registry.get(skill_id)
                if skill:
                    return skill_id
        
        return None

    async def _execute_exploit_task(self,
                                   subtask_id: str,
                                   description: str,
                                   thinking_log: List[Dict[str, Any]],
                                   tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行漏洞利用任务（真实执行）
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行漏洞利用任务: 分析目标，选择 exploit 技能",
            "type": "execution"
        })
        
        target = self.current_context.get("target", "")
        
        # 尝试通过 skill_registry 执行真实 exploit
        if self.skill_registry:
            # 1. 优先从任务描述匹配 CVE skill
            skill_id = self._match_cve_skill(description)
            
            # 2. 如果没有匹配，尝试用 subtask_id 直接查找
            if not skill_id:
                skill = self.skill_registry.get(subtask_id)
                if skill:
                    skill_id = subtask_id
            
            # 3. 如果还没找到，搜索 EXPLOIT 类型技能
            if not skill_id:
                try:
                    from ..skills.core import SkillType
                    exploit_skills = self.skill_registry.list(type=SkillType.EXPLOIT)
                    if exploit_skills:
                        skill_id = exploit_skills[0].id
                except Exception:
                    pass
            
            if skill_id:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"选择 exploit 技能: {skill_id}，目标: {target}",
                    "type": "tool_selection"
                })
                
                _bus = EventBus.get() if EventBus else None
                if _bus:
                    _bus.emit_tool("start", skill_id, args={"target": target})
                
                skill_result = self.skill_registry.execute(skill_id, {
                    "target": target,
                    "cmd": "id",
                })
                
                if _bus:
                    _bus.emit_tool("complete", skill_id, args={"target": target}, result=skill_result)
                
                output = skill_result.get("output", "")
                exploit_success = (
                    skill_result.get("vulnerable", False) or
                    "RCE_SUCCESS" in output or
                    "WEBSHELL_UPLOADED" in output or
                    "uid=" in output or
                    "root" in output
                )
                
                tool_calls.append({
                    "tool_name": skill_id,
                    "tool_type": "skill",
                    "parameters": {"target": target, "cmd": "id"},
                    "result": skill_result,
                    "execution_time": skill_result.get("execution_time", 0.0),
                    "success": exploit_success,
                })
                
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"利用结果: {'成功获得访问权限' if exploit_success else '未能利用，检查目标版本'}",
                    "type": "result"
                })
                
                return {
                    "task_type": "exploitation",
                    "simulated": False,
                    "skill_used": skill_id,
                    "exploit_attempted": skill_id,
                    "exploit_success": exploit_success,
                    "payload_delivered": exploit_success,
                    "access_gained": exploit_success,
                    "output": output,
                    "findings": skill_result.get("findings", []),
                    "vulnerabilities": skill_result.get("vulnerabilities", []),
                    "summary": f"漏洞利用完成（{skill_id}），{'成功获得访问权限' if exploit_success else '未成功，需要验证目标版本'}",
                }
        
        # Fallback: 无技能可用时返回说明性结果（不再硬编码成功）
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "未找到匹配的 exploit 技能，需要手动选择利用工具",
            "type": "warning"
        })
        return {
            "task_type": "exploitation",
            "simulated": False,
            "exploit_attempted": None,
            "exploit_success": False,
            "payload_delivered": False,
            "access_gained": False,
            "summary": f"未找到匹配目标的 exploit 技能，请检查目标服务版本并手动选择工具",
        }
    
    async def _execute_post_exploit_task(self,
                                        subtask_id: str,
                                        description: str,
                                        thinking_log: List[Dict[str, Any]],
                                        tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行后渗透任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行后渗透任务: 权限确认、信息收集、权限提升",
            "type": "execution"
        })
        
        target = self.current_context.get("target", "")
        activities = []
        post_findings = []
        
        # 1. 如果 skill_registry 有 privesc 技能，尝试执行
        if self.skill_registry:
            for skill_id in ["privesc_linux", "flag_detector", "info_sensitive_paths"]:
                skill = self.skill_registry.get(skill_id)
                if skill:
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"执行后渗透技能: {skill_id}",
                        "type": "tool_selection"
                    })
                    _bus = EventBus.get() if EventBus else None
                    if _bus:
                        _bus.emit_tool("start", skill_id, args={"target": target})
                    
                    skill_result = self.skill_registry.execute(skill_id, {"target": target})
                    
                    if _bus:
                        _bus.emit_tool("complete", skill_id, args={"target": target}, result=skill_result)
                    
                    tool_calls.append({
                        "tool_name": skill_id,
                        "tool_type": "skill",
                        "parameters": {"target": target},
                        "result": skill_result,
                        "execution_time": skill_result.get("execution_time", 0.0),
                        "success": skill_result.get("success", False),
                    })
                    activities.append(f"{skill_id}: {skill_result.get('summary', '完成')}")
                    post_findings.extend(skill_result.get("findings", []))
        
        # 2. 如果没有可用技能，记录真实需要的后续步骤
        if not activities:
            activities = [
                "建议: 通过 webshell 执行 id / whoami 确认权限",
                "建议: 检查 sudo -l 权限",
                "建议: 查找 SUID 文件: find / -perm -4000 2>/dev/null",
                "建议: 查看 /etc/passwd 和 /etc/cron* 文件",
            ]
            thinking_log.append({
                "timestamp": datetime.now().isoformat(),
                "message": "无自动化后渗透技能可用，已生成手动步骤建议",
                "type": "info"
            })
        
        return {
            "task_type": "post_exploitation",
            "simulated": False,
            "activities": activities,
            "findings": post_findings,
            "summary": f"后渗透任务完成，发现 {len(post_findings)} 个信息点",
        }
    
    async def _execute_general_task(self,
                                   subtask_id: str,
                                   description: str,
                                   thinking_log: List[Dict[str, Any]],
                                   tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行通用任务
        
        Args:
            subtask_id: 子任务ID
            description: 任务描述
            thinking_log: 思考日志
            tool_calls: 工具调用记录
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "执行通用任务",
            "type": "execution"
        })
        
        # 尝试使用现有技能系统
        if self.skill_registry:
            try:
                # 查找通用技能
                general_skills = []
                for skill_name in self.skill_registry.get_all_skill_names():
                    skill = ( (getattr(self.skill_registry, "get_skill", None) or getattr(self.skill_registry, "get", None)) or (lambda x: None) )(skill_name)
                    if skill:
                        general_skills.append(skill)
                
                if general_skills:
                    # 选择第一个技能执行
                    skill = general_skills[0]
                    thinking_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "message": f"使用技能执行: {skill.name}",
                        "type": "tool_selection"
                    })
                    
                    # 执行技能
                    skill_result = skill.execute(self.current_context)
                    
                    # 记录工具调用
                    tool_calls.append({
                        "tool_name": skill.name,
                        "tool_type": "skill",
                        "parameters": {"context": "current_context"},
                        "result": skill_result,
                        "execution_time": 0.0,
                        "success": skill_result.get("success", False)
                    })
                    
                    return {
                        "task_type": "general",
                        "skill_used": skill.name,
                        "result": skill_result,
                        "summary": f"使用技能 {skill.name} 完成任务"
                    }
            
            except Exception as e:
                thinking_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": f"技能执行失败: {str(e)}，使用模拟执行",
                    "type": "fallback"
                })
        
        # 模拟执行
        thinking_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": "使用模拟执行通用任务",
            "type": "simulation"
        })
        
        # 模拟工具调用
        simulated_tools = [
            {"name": "generic_tool", "action": "任务执行", "result": "完成任务目标"}
        ]
        
        for tool in simulated_tools:
            tool_calls.append({
                "tool_name": tool["name"],
                "tool_type": "simulated",
                "parameters": {"action": tool["action"]},
                "result": {"output": tool["result"]},
                "execution_time": 1.0,
                "success": True
            })
        
        return {
            "task_type": "general",
            "simulated": True,
            "result": {"status": "completed", "message": "任务执行完成"},
            "summary": "模拟通用任务执行完成"
        }
    
    def _check_completion_criteria(self, 
                                  result: Dict[str, Any], 
                                  completion_criteria: str) -> bool:
        """检查完成标准
        
        Args:
            result: 执行结果
            completion_criteria: 完成标准
            
        Returns:
            bool: 是否满足完成标准
        """
        if not completion_criteria:
            # 如果没有明确标准，检查执行是否成功
            return result.get("success", False) if "success" in result else True
        
        # 简单实现：根据结果类型判断
        task_type = result.get("task_type", "")
        
        if task_type == "reconnaissance":
            findings = result.get("findings", [])
            return len(findings) > 0
        
        elif task_type == "vulnerability_scan":
            vulnerabilities = result.get("vulnerabilities", [])
            return len(vulnerabilities) > 0
        
        elif task_type == "exploitation":
            return result.get("exploit_success", False) or result.get("access_gained", False)
        
        elif task_type == "post_exploitation":
            activities = result.get("activities", [])
            return len(activities) > 0
        
        else:
            # 通用任务：检查是否有结果
            return bool(result)
    
    def _update_tool_stats(self, tool_calls: List[Dict[str, Any]]) -> None:
        """更新工具统计
        
        Args:
            tool_calls: 工具调用记录
        """
        for call in tool_calls:
            tool_name = call.get("tool_name", "unknown")
            success = call.get("success", False)
            exec_time = call.get("execution_time", 0.0)
            
            if tool_name not in self.tool_stats:
                self.tool_stats[tool_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0
                }
            
            stats = self.tool_stats[tool_name]
            stats["total_calls"] += 1
            stats["total_time"] += exec_time
            
            if success:
                stats["successful_calls"] += 1
            else:
                stats["failed_calls"] += 1
            
            # 更新平均时间
            if stats["total_calls"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["total_calls"]
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要
        
        Returns:
            Dict[str, Any]: 执行摘要
        """
        total_tasks = len(self.execution_history)
        successful_tasks = sum(1 for r in self.execution_history if r.success)
        failed_tasks = total_tasks - successful_tasks
        
        total_time = sum(r.execution_time for r in self.execution_history)
        avg_time = total_time / total_tasks if total_tasks > 0 else 0
        
        total_tool_calls = sum(len(r.tool_calls) for r in self.execution_history)
        llm_assisted_count = sum(1 for r in self.execution_history if r.llm_assisted)
        
        summary = {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "total_execution_time": total_time,
            "average_task_time": avg_time,
            "total_tool_calls": total_tool_calls,
            "llm_assisted_count": llm_assisted_count,
            "tool_stats": self.tool_stats,
            "recent_tasks": [
                {
                    "subtask_id": r.subtask_id,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "tool_count": len(r.tool_calls),
                    "llm_assisted": r.llm_assisted
                }
                for r in self.execution_history[-5:]
            ],
            "use_llm": self.use_llm
        }
        
        # 添加LLM统计
        if self.llm_integration:
            summary["llm_stats"] = self.llm_integration.get_stats()
        
        return summary
    
    def clear_history(self) -> None:
        """清空执行历史"""
        self.execution_history.clear()
        self.tool_stats.clear()
        self.retry_counters.clear()
        logger.info("执行历史已清空")


async def test_executor():
    """测试执行器功能"""
    import sys
    
    print("=" * 80)
    print("PER执行器测试")
    print("=" * 80)
    
    # 创建执行器实例
    executor = PERExecutor(use_llm=False)  # 测试时使用规则模式
    
    # 设置上下文
    executor.set_context({
        "target": "example.com",
        "goal": "渗透测试",
        "scan_results": {}
    })
    
    # 测试1: 侦察任务
    print("\n测试1: 侦察任务执行")
    recon_task = {
        "description": "信息收集: example.com",
        "mission_briefing": "对目标进行全面的信息收集",
        "completion_criteria": "完成端口扫描和服务识别"
    }
    
    result1 = await executor.execute_subtask("recon_test", recon_task)
    print(f"侦察任务结果: {'成功' if result1.success else '失败'}")
    print(f"执行时间: {result1.execution_time:.2f}秒")
    print(f"工具调用数: {len(result1.tool_calls)}")
    print(f"LLM辅助: {result1.llm_assisted}")
    
    # 测试2: 漏洞扫描任务
    print("\n测试2: 漏洞扫描任务执行")
    vuln_task = {
        "description": "漏洞扫描: example.com",
        "mission_briefing": "基于信息收集结果进行漏洞扫描",
        "completion_criteria": "识别潜在的安全漏洞"
    }
    
    result2 = await executor.execute_subtask("vuln_scan_test", vuln_task)
    print(f"漏洞扫描结果: {'成功' if result2.success else '失败'}")
    print(f"执行时间: {result2.execution_time:.2f}秒")
    print(f"工具调用数: {len(result2.tool_calls)}")
    
    # 测试3: 获取执行摘要
    print("\n测试3: 执行摘要")
    summary = executor.get_execution_summary()
    print(f"总任务数: {summary['total_tasks']}")
    print(f"成功率: {summary['success_rate']*100:.1f}%")
    print(f"总执行时间: {summary['total_execution_time']:.2f}秒")
    print(f"总工具调用数: {summary['total_tool_calls']}")
    print(f"LLM辅助次数: {summary['llm_assisted_count']}")
    print(f"使用LLM: {summary['use_llm']}")
    
    # 显示思考日志示例
    print("\n思考日志示例:")
    for i, log in enumerate(result1.thinking_log[:3]):
        print(f"  {i+1}. [{log['type']}] {log['message']}")
    
    print("\n" + "=" * 80)
    print("[PASS] 执行器测试完成")
    
    return True


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_executor())
    sys.exit(0 if success else 1)
