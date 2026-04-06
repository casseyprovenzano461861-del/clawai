"""
HackSynth集成管理器 - P1阶段核心组件
将Planner和Summarizer组合成完整的HackSynth架构
"""

import json
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from pydantic import BaseModel, Field

from .planner import HackSynthPlanner, PlanningContext, CommandSuggestion, PlanningPhase
from .summarizer import HackSynthSummarizer, SummaryContext, SummaryResult, SecurityFinding
from .llm_planner import LLMHackSynthPlanner
from .llm_summarizer import LLMHackSynthSummarizer

logger = logging.getLogger(__name__)


class HackSynthConfig(BaseModel):
    """HackSynth配置模型"""
    name: str = "hacksynth_default"
    description: str = "默认HackSynth配置"
    planner_config: Dict[str, Any] = Field(default_factory=dict)
    summarizer_config: Dict[str, Any] = Field(default_factory=dict)
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = Field(default=10, ge=1, le=50)
    timeout_per_command: int = Field(default=300, ge=10, le=3600)
    learning_enabled: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "name": "hacksynth_enhanced",
                "description": "增强版HackSynth配置",
                "planner_config": {
                    "learning_enabled": True,
                    "system_prompt": "你是一个渗透测试专家...",
                    "user_prompt": "基于以下上下文生成命令..."
                },
                "summarizer_config": {
                    "summary_system_prompt": "你是一个安全分析专家...",
                    "summary_user_prompt": "总结以下渗透测试结果..."
                },
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                "max_iterations": 15,
                "timeout_per_command": 180
            }
        }


class HackSynthIterationResult(BaseModel):
    """HackSynth迭代结果模型"""
    iteration: int
    timestamp: datetime = Field(default_factory=datetime.now)
    phase: PlanningPhase
    planner_context: PlanningContext
    command_suggestions: List[CommandSuggestion]
    selected_command: Optional[CommandSuggestion] = None
    command_executed: Optional[str] = None
    command_output: Optional[str] = None
    execution_success: Optional[bool] = None
    execution_time: Optional[float] = None
    summarizer_context: Optional[SummaryContext] = None
    summary_result: Optional[SummaryResult] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class HackSynthSessionResult(BaseModel):
    """HackSynth会话结果模型"""
    session_id: str
    target: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, stopped
    iterations: List[HackSynthIterationResult] = Field(default_factory=list)
    final_summary: Optional[str] = None
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)
    config_used: HackSynthConfig
    
    @property
    def duration(self) -> Optional[float]:
        """获取会话持续时间（秒）"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def iteration_count(self) -> int:
        """获取迭代次数"""
        return len(self.iterations)


class HackSynthManager:
    """HackSynth集成管理器"""
    
    def __init__(
        self,
        config: HackSynthConfig,
        llm_client=None,
        tool_executor=None,
        skill_registry=None
    ):
        """
        初始化HackSynth管理器
        
        Args:
            config: HackSynth配置
            llm_client: LLM客户端实例
            tool_executor: 工具执行器实例
            skill_registry: 技能注册表实例
        """
        self.config = config
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.skill_registry = skill_registry
        
        # 初始化组件
        self.planner: Optional[HackSynthPlanner] = None
        self.summarizer: Optional[HackSynthSummarizer] = None
        
        # 会话管理
        self.active_sessions: Dict[str, HackSynthSessionResult] = {}
        self.session_history: List[Dict[str, Any]] = []
        
        # 初始化组件
        self._initialize_components()
        
        logger.info(f"HackSynth管理器初始化完成: {config.name}")
    
    def _initialize_components(self):
        """初始化Planner和Summarizer组件"""
        # 初始化Planner
        planner_config = self.config.planner_config.copy()
        if self.config.llm_config:
            planner_config["llm"] = self.config.llm_config
        
        self.planner = LLMHackSynthPlanner(
            config=planner_config,
            llm_client=self.llm_client
        )
        
        # 初始化Summarizer
        summarizer_config = self.config.summarizer_config.copy()
        if self.config.llm_config:
            summarizer_config["llm"] = self.config.llm_config
        
        self.summarizer = LLMHackSynthSummarizer(
            config=summarizer_config,
            llm_client=self.llm_client
        )
        
        logger.info("Planner和Summarizer组件初始化完成")
    
    def create_session(
        self,
        target: str,
        target_type: str = "unknown",
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建新的HackSynth会话
        
        Args:
            target: 目标地址
            target_type: 目标类型
            initial_context: 初始上下文
            
        Returns:
            会话ID
        """
        import uuid
        import hashlib
        
        # 生成会话ID
        session_id = f"hacksynth_{hashlib.md5(f'{target}_{datetime.now().timestamp()}'.encode()).hexdigest()[:12]}"
        
        # 创建会话结果
        session = HackSynthSessionResult(
            session_id=session_id,
            target=target,
            start_time=datetime.now(),
            status="running",
            config_used=self.config
        )
        
        # 存储会话
        self.active_sessions[session_id] = session
        
        logger.info(f"创建HackSynth会话: {session_id}, 目标: {target}")
        return session_id
    
    async def run_session(
        self,
        session_id: str,
        available_tools: List[str] = None,
        initial_findings: List[SecurityFinding] = None,
        callback=None
    ) -> HackSynthSessionResult:
        """
        运行HackSynth会话
        
        Args:
            session_id: 会话ID
            available_tools: 可用工具列表
            initial_findings: 初始发现列表
            callback: 回调函数（每迭代调用）
            
        Returns:
            会话结果
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        logger.info(f"开始运行HackSynth会话: {session_id}, 目标: {session.target}")
        
        try:
            # 初始化上下文
            planning_context = PlanningContext(
                target=session.target,
                target_type="unknown",  # 可以从配置中获取
                current_phase=PlanningPhase.RECONNAISSANCE,
                discovered_services=[],
                open_ports=[],
                vulnerabilities_found=[],
                credentials_obtained=[],
                previous_commands=[],
                command_results={},
                constraints={}
            )
            
            # 设置可用工具
            if available_tools is None:
                available_tools = self._get_default_tools()
            
            # 运行迭代
            for iteration in range(self.config.max_iterations):
                logger.info(f"会话 {session_id} 第 {iteration + 1}/{self.config.max_iterations} 次迭代")
                
                # 执行单次迭代
                iteration_result = await self._run_iteration(
                    session_id=session_id,
                    iteration_number=iteration + 1,
                    planning_context=planning_context,
                    available_tools=available_tools
                )
                
                # 添加到会话
                session.iterations.append(iteration_result)
                
                # 更新规划上下文
                planning_context = self._update_planning_context(
                    planning_context, iteration_result
                )
                
                # 调用回调函数
                if callback:
                    try:
                        await callback(iteration_result)
                    except Exception as e:
                        logger.error(f"回调函数执行失败: {e}")
                
                # 检查是否应该停止
                if self._should_stop_session(iteration_result, session):
                    logger.info(f"会话 {session_id} 在第 {iteration + 1} 次迭代后停止")
                    session.status = "stopped"
                    break
            
            # 完成会话
            session.end_time = datetime.now()
            if session.status == "running":
                session.status = "completed"
            
            # 生成最终总结
            session.final_summary = self._generate_final_summary(session)
            
            # 计算统计信息
            self._calculate_session_statistics(session)
            
            # 移动到历史记录
            self._move_session_to_history(session_id)
            
            logger.info(f"HackSynth会话完成: {session_id}, 状态: {session.status}, 迭代: {session.iteration_count}")
            return session
            
        except Exception as e:
            logger.error(f"HackSynth会话运行失败: {e}")
            session.status = "failed"
            session.end_time = datetime.now()
            session.metrics["error"] = str(e)
            
            # 移动到历史记录
            self._move_session_to_history(session_id)
            
            return session
    
    async def _run_iteration(
        self,
        session_id: str,
        iteration_number: int,
        planning_context: PlanningContext,
        available_tools: List[str]
    ) -> HackSynthIterationResult:
        """执行单次迭代"""
        iteration_start = datetime.now()
        
        # 创建迭代结果
        iteration_result = HackSynthIterationResult(
            iteration=iteration_number,
            phase=planning_context.current_phase,
            planner_context=planning_context.copy()
        )
        
        try:
            # 1. Planner生成命令建议
            command_suggestions = await self.planner.generate_plan(
                context=planning_context,
                available_tools=available_tools,
                max_suggestions=3
            )
            
            iteration_result.command_suggestions = command_suggestions
            
            # 2. 选择最佳命令
            selected_command = self._select_best_command(command_suggestions, planning_context)
            iteration_result.selected_command = selected_command
            
            if not selected_command:
                logger.warning(f"迭代 {iteration_number} 未选择命令")
                iteration_result.metrics["no_command_selected"] = True
                return iteration_result
            
            # 3. 执行命令
            command_executed = selected_command.command
            iteration_result.command_executed = command_executed
            
            execution_result = await self._execute_command(
                command_executed,
                planning_context.target,
                timeout=self.config.timeout_per_command
            )
            
            iteration_result.command_output = execution_result["output"]
            iteration_result.execution_success = execution_result["success"]
            iteration_result.execution_time = execution_result["execution_time"]
            
            # 4. Summarizer总结结果
            summarizer_context = SummaryContext(
                target=planning_context.target,
                target_type=planning_context.target_type,
                phase=planning_context.current_phase.value,
                command_executed=command_executed,
                command_output=execution_result["output"],
                previous_summary=None  # 可以从前一次迭代获取
            )
            
            iteration_result.summarizer_context = summarizer_context
            
            summary_result = await self.summarizer.summarize(summarizer_context)
            iteration_result.summary_result = summary_result
            
            # 5. 更新指标
            iteration_duration = (datetime.now() - iteration_start).total_seconds()
            iteration_result.metrics.update({
                "iteration_duration": iteration_duration,
                "planner_suggestions_count": len(command_suggestions),
                "summarizer_findings_count": len(summary_result.key_findings),
                "execution_success": execution_result["success"]
            })
            
            logger.info(f"迭代 {iteration_number} 完成: 命令 '{command_executed[:50]}...', 发现 {len(summary_result.key_findings)} 个")
            
        except Exception as e:
            logger.error(f"迭代 {iteration_number} 执行失败: {e}")
            iteration_result.metrics["error"] = str(e)
            iteration_result.execution_success = False
        
        return iteration_result
    
    def _select_best_command(
        self,
        suggestions: List[CommandSuggestion],
        context: PlanningContext
    ) -> Optional[CommandSuggestion]:
        """选择最佳命令"""
        if not suggestions:
            return None
        
        # 简单选择策略：选择成功概率最高的命令
        best_suggestion = max(suggestions, key=lambda s: s.success_probability)
        
        # 考虑阶段匹配
        if best_suggestion.phase != context.current_phase:
            # 寻找阶段匹配的命令
            phase_matched = [s for s in suggestions if s.phase == context.current_phase]
            if phase_matched:
                best_suggestion = max(phase_matched, key=lambda s: s.success_probability)
        
        return best_suggestion
    
    async def _execute_command(
        self,
        command: str,
        target: str,
        timeout: int
    ) -> Dict[str, Any]:
        """执行命令"""
        execution_start = datetime.now()
        
        try:
            if self.tool_executor:
                # 使用工具执行器
                result = await self.tool_executor.execute(
                    command=command,
                    target=target,
                    timeout=timeout
                )
                
                execution_time = (datetime.now() - execution_start).total_seconds()
                
                return {
                    "success": result.get("success", False),
                    "output": result.get("output", ""),
                    "error": result.get("error"),
                    "execution_time": execution_time,
                    "method": "tool_executor"
                }
            else:
                # 模拟执行
                await asyncio.sleep(2)  # 模拟执行时间
                
                execution_time = (datetime.now() - execution_start).total_seconds()
                
                # 生成模拟输出
                mock_output = self._generate_mock_output(command, target)
                
                return {
                    "success": True,
                    "output": mock_output,
                    "execution_time": execution_time,
                    "method": "mock"
                }
                
        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            return {
                "success": False,
                "output": f"命令执行失败: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
                "method": "error"
            }
    
    def _generate_mock_output(self, command: str, target: str) -> str:
        """生成模拟输出"""
        command_lower = command.lower()
        
        if "nmap" in command_lower:
            return f"""Starting Nmap 7.94 scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Nmap scan report for {target}
Host is up (0.045s latency).
Not shown: 997 closed ports
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.9p1 Ubuntu 3ubuntu0.6
80/tcp   open  http       Apache httpd 2.4.52
443/tcp  open  ssl/https  Apache httpd 2.4.52
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 2.34 seconds"""
        
        elif "whatweb" in command_lower:
            return f"""http://{target} [200 OK] Apache[2.4.52], Country[RESERVED][ZZ], HTTPServer[Ubuntu Linux][Apache/2.4.52 (Ubuntu)], IP[127.0.0.1], Title[Test Page for the Apache HTTP Server on Ubuntu]"""
        
        elif "dirsearch" in command_lower:
            return f"""Extensions: php, html, js | HTTP method: GET | Threads: 50
Wordlist size: 6543

Target: http://{target}

[11:06:53] Starting: 
[11:06:55] 200 -    4KB - /index.html
[11:06:56] 200 -    2KB - /admin/
[11:06:57] 200 -    3KB - /login.php
[11:06:58] 403 -  292B - /server-status

Task Completed"""
        
        else:
            return f"命令执行完成: {command}\n目标: {target}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n状态: 成功"
    
    def _update_planning_context(
        self,
        context: PlanningContext,
        iteration_result: HackSynthIterationResult
    ) -> PlanningContext:
        """更新规划上下文"""
        # 创建新上下文（复制）
        new_context = context.copy()
        
        # 更新命令历史
        if iteration_result.command_executed:
            new_context.previous_commands.append(iteration_result.command_executed)
            
            # 更新命令结果
            if iteration_result.command_output:
                new_context.command_results[iteration_result.command_executed] = {
                    "output": iteration_result.command_output,
                    "success": iteration_result.execution_success,
                    "execution_time": iteration_result.execution_time
                }
        
        # 更新发现的服务和端口
        if iteration_result.summary_result:
            for finding in iteration_result.summary_result.key_findings:
                if finding.category == "service":
                    # 提取服务信息
                    service_match = re.search(r'(\d+)/tcp.*open.*(\w+)', finding.evidence, re.IGNORECASE)
                    if service_match:
                        port = int(service_match.group(1))
                        service = service_match.group(2)
                        
                        if port not in new_context.open_ports:
                            new_context.open_ports.append(port)
                        
                        service_info = f"{service} (port {port})"
                        if service_info not in new_context.discovered_services:
                            new_context.discovered_services.append(service_info)
                
                elif finding.category == "vulnerability":
                    if finding.title not in new_context.vulnerabilities_found:
                        new_context.vulnerabilities_found.append(finding.title)
                
                elif finding.category == "credential":
                    # 提取凭证信息
                    cred_match = re.search(r'(username|password|user|pass)[:\s]+([^\s]+)', finding.evidence, re.IGNORECASE)
                    if cred_match:
                        cred_type = cred_match.group(1).lower()
                        cred_value = cred_match.group(2)
                        
                        credential = {
                            "type": cred_type,
                            "value": cred_value,
                            "source": finding.title,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        new_context.credentials_obtained.append(credential)
        
        # 更新当前阶段
        if iteration_result.summary_result and iteration_result.summary_result.next_phase_recommendation:
            try:
                new_context.current_phase = PlanningPhase(iteration_result.summary_result.next_phase_recommendation)
            except ValueError:
                # 如果推荐阶段无效，使用Planner的决策
                new_context.current_phase = self.planner.determine_next_phase(new_context)
        else:
            # 使用Planner决定下一个阶段
            new_context.current_phase = self.planner.determine_next_phase(new_context)
        
        # 更新约束（基于发现）
        if new_context.vulnerabilities_found:
            new_context.constraints["has_vulnerabilities"] = True
            new_context.constraints["vulnerability_count"] = len(new_context.vulnerabilities_found)
        
        if new_context.credentials_obtained:
            new_context.constraints["has_credentials"] = True
            new_context.constraints["credential_count"] = len(new_context.credentials_obtained)
        
        logger.debug(f"规划上下文已更新: 阶段={new_context.current_phase}, 服务={len(new_context.discovered_services)}, 漏洞={len(new_context.vulnerabilities_found)}")
        
        return new_context
    
    def _get_default_tools(self) -> List[str]:
        """获取默认工具列表"""
        default_tools = [
            "nmap",
            "whatweb",
            "dirsearch",
            "nikto",
            "nuclei",
            "sqlmap",
            "hydra",
            "metasploit"
        ]
        
        # 如果有技能注册表，获取可用工具
        if self.skill_registry:
            try:
                available_skills = self.skill_registry.get_available_skills()
                if available_skills:
                    return available_skills
            except Exception as e:
                logger.warning(f"从技能注册表获取工具失败: {e}")
        
        return default_tools
    
    def _should_stop_session(
        self,
        iteration_result: HackSynthIterationResult,
        session: HackSynthSessionResult
    ) -> bool:
        """判断是否应该停止会话"""
        # 1. 达到最大迭代次数
        if session.iteration_count >= self.config.max_iterations:
            logger.info(f"达到最大迭代次数: {self.config.max_iterations}")
            return True
        
        # 2. 命令执行失败
        if iteration_result.execution_success is False:
            logger.warning(f"命令执行失败，考虑停止会话")
            # 连续失败3次则停止
            recent_failures = 0
            for i in range(min(3, len(session.iterations))):
                if session.iterations[-(i+1)].execution_success is False:
                    recent_failures += 1
            
            if recent_failures >= 3:
                logger.info("连续3次命令执行失败，停止会话")
                return True
        
        # 3. 发现关键漏洞
        if iteration_result.summary_result:
            critical_findings = [
                f for f in iteration_result.summary_result.key_findings
                if f.severity in ["critical", "high"]
            ]
            
            if critical_findings:
                logger.info(f"发现 {len(critical_findings)} 个关键漏洞，考虑停止会话")
                # 如果已经获得系统访问权限，可以停止
                for finding in critical_findings:
                    if "shell" in finding.title.lower() or "access" in finding.title.lower():
                        logger.info("获得系统访问权限，停止会话")
                        return True
        
        # 4. 阶段完成
        if iteration_result.phase == PlanningPhase.POST_EXPLOITATION:
            logger.info("达到后渗透阶段，考虑停止会话")
            # 在后渗透阶段执行了足够多的命令后停止
            post_exploitation_commands = 0
            for iter_result in session.iterations:
                if iter_result.phase == PlanningPhase.POST_EXPLOITATION:
                    post_exploitation_commands += 1
            
            if post_exploitation_commands >= 3:
                logger.info("后渗透阶段执行了3个命令，停止会话")
                return True
        
        # 5. 用户定义的停止条件
        if hasattr(self, 'custom_stop_condition'):
            try:
                if self.custom_stop_condition(iteration_result, session):
                    logger.info("自定义停止条件满足，停止会话")
                    return True
            except Exception as e:
                logger.error(f"自定义停止条件检查失败: {e}")
        
        return False
    
    def _generate_final_summary(self, session: HackSynthSessionResult) -> str:
        """生成会话最终总结"""
        if not session.iterations:
            return "会话未执行任何迭代"
        
        # 收集所有发现
        all_findings = []
        for iteration in session.iterations:
            if iteration.summary_result:
                all_findings.extend(iteration.summary_result.key_findings)
        
        # 统计发现
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        category_counts = {}
        
        for finding in all_findings:
            severity = finding.severity.value
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            category = finding.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 生成总结
        summary_lines = [
            f"HackSynth会话总结 - {session.session_id}",
            f"目标: {session.target}",
            f"状态: {session.status}",
            f"持续时间: {session.duration:.1f}秒" if session.duration else "持续时间: 未知",
            f"迭代次数: {session.iteration_count}",
            "",
            "发现统计:",
            f"  严重(Critical): {severity_counts['critical']}",
            f"  高(High): {severity_counts['high']}",
            f"  中(Medium): {severity_counts['medium']}",
            f"  低(Low): {severity_counts['low']}",
            f"  信息(Info): {severity_counts['info']}",
            f"  总计: {len(all_findings)}",
            "",
            "类别分布:"
        ]
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            summary_lines.append(f"  {category}: {count}")
        
        # 添加关键发现
        critical_findings = [f for f in all_findings if f.severity in ["critical", "high"]]
        if critical_findings:
            summary_lines.extend([
                "",
                "关键发现:"
            ])
            
            for i, finding in enumerate(critical_findings[:5], 1):  # 最多显示5个
                summary_lines.append(f"  {i}. {finding.title} ({finding.severity.value})")
                summary_lines.append(f"     影响: {finding.impact}")
                summary_lines.append(f"     修复建议: {finding.remediation}")
        
        # 添加执行统计
        successful_commands = sum(1 for i in session.iterations if i.execution_success is True)
        failed_commands = sum(1 for i in session.iterations if i.execution_success is False)
        
        summary_lines.extend([
            "",
            "执行统计:",
            f"  成功命令: {successful_commands}",
            f"  失败命令: {failed_commands}",
            f"  成功率: {successful_commands/session.iteration_count*100:.1f}%" if session.iteration_count > 0 else "  成功率: N/A"
        ])
        
        # 添加建议
        summary_lines.extend([
            "",
            "建议:"
        ])
        
        if critical_findings:
            summary_lines.append("  - 立即修复关键和高严重性漏洞")
            summary_lines.append("  - 实施适当的访问控制和监控")
        
        if failed_commands > successful_commands:
            summary_lines.append("  - 命令执行成功率较低，建议检查工具配置和网络连接")
        
        if len(all_findings) == 0:
            summary_lines.append("  - 未发现安全问题，建议进行更深入的测试")
        
        return "\n".join(summary_lines)
    
    def _calculate_session_statistics(self, session: HackSynthSessionResult):
        """计算会话统计信息"""
        if not session.iterations:
            return
        
        # 收集所有发现
        all_findings = []
        for iteration in session.iterations:
            if iteration.summary_result:
                all_findings.extend(iteration.summary_result.key_findings)
        
        # 计算统计
        session.total_findings = len(all_findings)
        session.critical_findings = len([f for f in all_findings if f.severity == "critical"])
        session.high_findings = len([f for f in all_findings if f.severity == "high"])
        
        # 计算命令执行统计
        successful_commands = sum(1 for i in session.iterations if i.execution_success is True)
        failed_commands = sum(1 for i in session.iterations if i.execution_success is False)
        
        # 计算阶段分布
        phase_distribution = {}
        for iteration in session.iterations:
            phase = iteration.phase.value
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        
        # 计算工具使用统计
        tool_usage = {}
        for iteration in session.iterations:
            if iteration.selected_command:
                tool = iteration.selected_command.tool
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        # 更新会话指标
        session.metrics.update({
            "total_findings": session.total_findings,
            "critical_findings": session.critical_findings,
            "high_findings": session.high_findings,
            "successful_commands": successful_commands,
            "failed_commands": failed_commands,
            "success_rate": successful_commands / session.iteration_count if session.iteration_count > 0 else 0,
            "phase_distribution": phase_distribution,
            "tool_usage": tool_usage,
            "average_iteration_duration": sum(i.metrics.get("iteration_duration", 0) for i in session.iterations) / session.iteration_count if session.iteration_count > 0 else 0
        })
        
        logger.debug(f"会话统计计算完成: 发现={session.total_findings}, 关键={session.critical_findings}, 高={session.high_findings}")
    
    def _move_session_to_history(self, session_id: str):
        """将会话移动到历史记录"""
        if session_id not in self.active_sessions:
            logger.warning(f"尝试移动不存在的会话到历史记录: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        
        # 创建历史记录条目
        history_entry = {
            "session_id": session.session_id,
            "target": session.target,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "status": session.status,
            "duration": session.duration,
            "iteration_count": session.iteration_count,
            "total_findings": session.total_findings,
            "critical_findings": session.critical_findings,
            "high_findings": session.high_findings,
            "metrics_summary": {
                "success_rate": session.metrics.get("success_rate", 0),
                "average_iteration_duration": session.metrics.get("average_iteration_duration", 0)
            }
        }
        
        # 添加到历史记录
        self.session_history.append(history_entry)
        
        # 从活动会话中移除
        del self.active_sessions[session_id]
        
        # 限制历史记录大小
        if len(self.session_history) > 100:
            self.session_history = self.session_history[-100:]
        
        logger.info(f"会话已移动到历史记录: {session_id}, 历史记录总数: {len(self.session_history)}")
    
    def get_session(self, session_id: str) -> Optional[HackSynthSessionResult]:
        """获取会话"""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[HackSynthSessionResult]:
        """获取所有活动会话"""
        return list(self.active_sessions.values())
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取会话历史记录"""
        return self.session_history[-limit:] if self.session_history else []
    
    def stop_session(self, session_id: str) -> bool:
        """停止会话"""
        if session_id not in self.active_sessions:
            logger.warning(f"尝试停止不存在的会话: {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        session.status = "stopped"
        session.end_time = datetime.now()
        
        # 生成最终总结
        session.final_summary = self._generate_final_summary(session)
        
        # 计算统计信息
        self._calculate_session_statistics(session)
        
        # 移动到历史记录
        self._move_session_to_history(session_id)
        
        logger.info(f"会话已手动停止: {session_id}")
        return True
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        total_sessions = len(self.session_history) + len(self.active_sessions)
        completed_sessions = len([s for s in self.session_history if s.get("status") == "completed"])
        failed_sessions = len([s for s in self.session_history if s.get("status") == "failed"])
        
        # 计算总发现数
        total_findings = sum(s.get("total_findings", 0) for s in self.session_history)
        total_critical = sum(s.get("critical_findings", 0) for s in self.session_history)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": len(self.active_sessions),
            "historical_sessions": len(self.session_history),
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "total_findings": total_findings,
            "total_critical_findings": total_critical,
            "planner_statistics": self.planner.get_planning_statistics() if self.planner else {},
            "summarizer_statistics": self.summarizer.get_summary_statistics() if self.summarizer else {}
        }
    
    def export_session_report(self, session_id: str, format: str = "json") -> Optional[str]:
        """导出会话报告"""
        session = None
        
        # 查找会话
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            # 在历史记录中查找
            for history_entry in self.session_history:
                if history_entry.get("session_id") == session_id:
                    # 重新创建会话对象（简化版）
                    session_data = {
                        "session_id": history_entry["session_id"],
                        "target": history_entry["target"],
                        "start_time": datetime.fromisoformat(history_entry["start_time"]),
                        "end_time": datetime.fromisoformat(history_entry["end_time"]) if history_entry["end_time"] else None,
                        "status": history_entry["status"],
                        "iterations": [],  # 历史记录中没有迭代详情
                        "final_summary": f"历史会话报告 - {history_entry['session_id']}",
                        "total_findings": history_entry.get("total_findings", 0),
                        "critical_findings": history_entry.get("critical_findings", 0),
                        "high_findings": history_entry.get("high_findings", 0),
                        "metrics": history_entry.get("metrics_summary", {}),
                        "config_used": self.config
                    }
                    session = HackSynthSessionResult(**session_data)
                    break
        
        if not session:
            logger.error(f"会话不存在: {session_id}")
            return None
        
        try:
            if format == "json":
                # 转换为可序列化的字典
                session_dict = session.dict()
                session_dict["start_time"] = session.start_time.isoformat()
                if session.end_time:
                    session_dict["end_time"] = session.end_time.isoformat()
                
                # 处理迭代
                for i, iteration in enumerate(session_dict["iterations"]):
                    iteration["timestamp"] = iteration["timestamp"].isoformat()
                    if iteration.get("planner_context"):
                        iteration["planner_context"]["current_phase"] = iteration["planner_context"]["current_phase"].value
                
                return json.dumps(session_dict, indent=2, ensure_ascii=False)
            
            elif format == "text":
                return session.final_summary or self._generate_final_summary(session)
            
            elif format == "markdown":
                # 生成Markdown报告
                md_lines = [
                    f"# HackSynth渗透测试报告",
                    f"",
                    f"**会话ID**: `{session.session_id}`",
                    f"**目标**: `{session.target}`",
                    f"**状态**: {session.status}",
                    f"**开始时间**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"**结束时间**: {session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else '进行中'}",
                    f"**持续时间**: {session.duration:.1f}秒" if session.duration else "**持续时间**: 进行中",
                    f"**迭代次数**: {session.iteration_count}",
                    f"",
                    f"## 发现统计",
                    f"",
                    f"- **总发现数**: {session.total_findings}",
                    f"- **关键发现**: {session.critical_findings}",
                    f"- **高严重性发现**: {session.high_findings}",
                    f"",
                    f"## 执行统计",
                    f"",
                ]
                
                if session.metrics:
                    success_rate = session.metrics.get("success_rate", 0)
                    md_lines.append(f"- **命令成功率**: {success_rate*100:.1f}%")
                    
                    if "phase_distribution" in session.metrics:
                        md_lines.append(f"- **阶段分布**:")
                        for phase, count in session.metrics["phase_distribution"].items():
                            md_lines.append(f"  - {phase}: {count}次")
                
                md_lines.extend([
                    f"",
                    f"## 详细总结",
                    f"",
                    f"```",
                    session.final_summary or self._generate_final_summary(session),
                    f"```",
                    f"",
                    f"## 配置信息",
                    f"",
                    f"- **配置名称**: {session.config_used.name}",
                    f"- **最大迭代次数**: {session.config_used.max_iterations}",
                    f"- **命令超时时间**: {session.config_used.timeout_per_command}秒",
                    f"",
                    f"---",
                    f"",
                    f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                    f"*HackSynth版本: 1.0.0*"
                ])
                
                return "\n".join(md_lines)
            
            else:
                logger.error(f"不支持的导出格式: {format}")
                return None
                
        except Exception as e:
            logger.error(f"导出会话报告失败: {e}")
            return None
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理旧会话"""
        if not self.session_history:
            return
        
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        initial_count = len(self.session_history)
        
        # 过滤掉过期的会话
        self.session_history = [
            entry for entry in self.session_history
            if datetime.fromisoformat(entry["start_time"]).timestamp() > cutoff_time
        ]
        
        removed_count = initial_count - len(self.session_history)
        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 个超过 {max_age_hours} 小时的旧会话")
    
    def reset(self):
        """重置管理器"""
        # 停止所有活动会话
        for session_id in list(self.active_sessions.keys()):
            self.stop_session(session_id)
        
        # 清空历史记录
        self.session_history.clear()
        
        # 重置组件
        if self.planner:
            self.planner.planning_history.clear()
        
        if self.summarizer:
            self.summarizer.summary_history.clear()
        
        logger.info("HackSynth管理器已重置")
    
    def __str__(self) -> str:
        """字符串表示"""
        stats = self.get_manager_statistics()
        return (
            f"HackSynthManager(name={self.config.name}, "
            f"active_sessions={stats['active_sessions']}, "
            f"total_sessions={stats['total_sessions']}, "
            f"total_findings={stats['total_findings']})"
        )
    
    def __repr__(self) -> str:
        """详细表示"""
        return f"<HackSynthManager config={self.config.name}>"
