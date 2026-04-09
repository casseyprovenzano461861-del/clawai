# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
P-E-R架构：反思器模块
借鉴LuaN1aoAgent的反思器设计，负责分析执行结果、提取经验教训
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# 添加路径以便导入现有模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from .prompts import (
        get_reflector_system_prompt,
        get_reflector_analysis_prompt,
        get_reflector_intelligence_prompt,
    )
except ImportError:
    from prompts import (
        get_reflector_system_prompt,
        get_reflector_analysis_prompt,
        get_reflector_intelligence_prompt,
    )

try:
    from ..events import EventBus
except ImportError:
    try:
        from events import EventBus
    except ImportError:
        EventBus = None

logger = logging.getLogger(__name__)


@dataclass
class ReflectionInsight:
    """反思洞察"""
    timestamp: str
    subtask_id: str
    normalized_status: str
    key_insight: str
    failure_pattern: Optional[str] = None
    full_reflection_report: Optional[Dict[str, Any]] = None
    llm_reflection_prompt: Optional[str] = None
    llm_reflection_response: Optional[str] = None


@dataclass
class AuditResult:
    """审计结果"""
    status: str  # goal_achieved, partial_success, failed, in_progress
    completion_check: str
    confidence: float = 0.0
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class PERReflector:
    """P-E-R架构：反思器
    
    负责：
    1. 分析执行结果，评估任务完成情况
    2. 提取关键发现和经验教训
    3. 识别失败模式和成功模式
    4. 生成情报摘要供规划器使用
    5. 维护反思历史，支持模式识别
    """
    
    def __init__(self, llm_client=None, use_llm: bool = True):
        """初始化反思器
        
        Args:
            llm_client: LLM客户端实例（可选）
            use_llm: 是否使用LLM进行反思（默认True）
        """
        self.llm_client = llm_client
        self.use_llm = use_llm and llm_client is not None
        
        # 反思历史
        self.reflection_log: List[ReflectionInsight] = []
        
        # 失败模式库
        self.failure_patterns: Dict[str, Dict[str, Any]] = {}
        
        # 成功模式库
        self.success_patterns: Dict[str, Dict[str, Any]] = {}
        
        # 压缩历史
        self.compressed_reflection_summary: Optional[str] = None
        self.compression_count: int = 0
        
        # 需要压缩标志
        self._needs_compression: bool = False
        
        # 初始化LLM集成
        self._init_llm_integration()
        
        logger.info(f"PERReflector初始化完成 (use_llm={self.use_llm})")
    
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
    
    # ------------------------------------------------------------------
    # 硬规则层：在 LLM 分析之前优先执行，确保关键场景稳定决策
    # ------------------------------------------------------------------

    def _apply_hard_rules(self, execution_result: Dict[str, Any]) -> Optional[str]:
        """硬规则快速判断，返回 hard_status 字符串，None 表示交给 LLM/规则分析。

        规则优先级（从高到低）：
        1. 工具执行失败             → "tool_failed"
        2. 发现漏洞（vuln_found）   → "vuln_found"
        3. 无新发现                 → "no_new_finding"
        4. 其他（有发现但未确认）   → None（继续常规分析）
        """
        success = execution_result.get("success", False)

        # 规则1：工具失败
        if not success:
            return "tool_failed"

        # 规则2：发现可疑漏洞（Skill 或工具已标记）
        if execution_result.get("vulnerable") or execution_result.get("vulnerabilities"):
            return "vuln_found"

        # 规则3：无任何新发现（findings 为空且没有有效输出）
        findings = execution_result.get("findings", [])
        output = execution_result.get("output", "")
        has_output = bool(output and len(str(output).strip()) > 20)
        if not findings and not has_output:
            return "no_new_finding"

        return None

    def _build_hard_rule_report(
        self,
        subtask_id: str,
        hard_status: str,
        execution_result: Dict[str, Any],
        subtask_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """根据硬规则状态构建反思报告"""
        task_type = execution_result.get("task_type", "unknown")
        description = subtask_data.get("description", "")

        if hard_status == "tool_failed":
            error = execution_result.get("error", "未知错误")
            audit_status = "failed"
            insight = f"工具执行失败: {error}。建议切换同类别备选工具或调整参数。"
            recommendations = ["切换备选工具", "检查工具安装状态", "调整超时/权限参数"]
            # 携带 hard_action 让 Planner 知道该做什么
            hard_action = "switch_tool"

        elif hard_status == "vuln_found":
            vuln_list = execution_result.get("vulnerabilities", [])
            vuln_info = vuln_list[0] if vuln_list else execution_result
            vuln_type = vuln_info.get("type", "unknown") if isinstance(vuln_info, dict) else "unknown"
            audit_status = "partial_success"
            insight = f"发现疑似漏洞（{vuln_type}），需要二次验证确认是否真实成立。"
            recommendations = ["触发验证任务", "保存 payload 和响应作为证据"]
            hard_action = "trigger_validation"

        else:  # no_new_finding
            audit_status = "partial_success"
            insight = "本轮扫描无新发现，自动变换 Payload 变体后重试。"
            recommendations = ["使用 PayloadMutator 生成变体", "尝试不同参数组合"]
            hard_action = "mutate_payload"

        return {
            "subtask_id": subtask_id,
            "description": description,
            "audit_result": {
                "status": audit_status,
                "completion_check": insight,
                "confidence": 0.85,
                "recommendations": recommendations,
            },
            "key_findings": execution_result.get("findings", []),
            "patterns": {"hard_rule_triggered": hard_status},
            "insight": insight,
            "hard_action": hard_action,
            "hard_status": hard_status,
            "timestamp": datetime.now().isoformat(),
            "execution_summary": self._summarize_execution(execution_result),
            "llm_analysis": False,
            "hard_rule": True,
        }

    async def analyze_execution_result(self,
                                subtask_id: str,
                                execution_result: Dict[str, Any],
                                subtask_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析执行结果
        
        Args:
            subtask_id: 子任务ID
            execution_result: 执行结果
            subtask_data: 子任务数据
            
        Returns:
            Dict[str, Any]: 反思结果
        """
        logger.info(f"分析执行结果: {subtask_id}")

        _bus = EventBus.get() if EventBus else None

        # ---- 硬规则优先判断 ----
        hard_status = self._apply_hard_rules(execution_result)
        if hard_status is not None:
            report = self._build_hard_rule_report(subtask_id, hard_status, execution_result, subtask_data)
            logger.info(f"[硬规则] {subtask_id}: {hard_status} -> hard_action={report.get('hard_action')}")
            if _bus:
                _bus.emit_message(f"[硬规则] {subtask_id}: {report['insight']}", msg_type="warning")
            # 记录反思
            self.reflection_log.append(ReflectionInsight(
                timestamp=report["timestamp"],
                subtask_id=subtask_id,
                normalized_status=report["audit_result"]["status"],
                key_insight=report["insight"],
                failure_pattern=hard_status if hard_status == "tool_failed" else None,
                full_reflection_report=report,
            ))
            return report

        # 如果使用LLM，尝试智能分析
        if self.use_llm and self.llm_integration:
            try:
                reflection_report = await self._analyze_with_llm(subtask_id, execution_result, subtask_data)
                if reflection_report:
                    logger.info(f"LLM反思完成: {subtask_id}")
                    if _bus:
                        insight = reflection_report.get("key_insight", "")
                        status = reflection_report.get("normalized_status", "")
                        msg_type = "success" if "success" in status.lower() else "warning"
                        _bus.emit_message(f"[反思] {subtask_id}: {insight}", msg_type=msg_type)
                    return reflection_report
            except Exception as e:
                logger.warning(f"LLM反思失败: {e}，使用回退模式")
        
        # 回退到基于规则的分析
        report = self._analyze_with_rules(subtask_id, execution_result, subtask_data)
        if _bus:
            insight = report.get("key_insight", "")
            _bus.emit_message(f"[反思] {subtask_id}: {insight}", msg_type="info")
        return report
    
    async def _analyze_with_llm(self, subtask_id: str, execution_result: Dict[str, Any],
                          subtask_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用LLM分析执行结果
        
        Args:
            subtask_id: 子任务ID
            execution_result: 执行结果
            subtask_data: 子任务数据
            
        Returns:
            Optional[Dict[str, Any]]: 反思报告
        """
        
        # 使用优化后的提示词
        system_prompt = get_reflector_system_prompt()

        user_prompt = get_reflector_analysis_prompt(
            subtask_id=subtask_id,
            description=subtask_data.get('description', 'N/A'),
            mission_briefing=subtask_data.get('mission_briefing', 'N/A'),
            completion_criteria=subtask_data.get('completion_criteria', 'N/A'),
            execution_result=json.dumps(execution_result, ensure_ascii=False, indent=2),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 异步调用 LLM
        try:
            from ..llm_integration import TaskType as _TT
            _task_type = _TT.REFLECTION if _TT else None
        except Exception:
            _task_type = None
        response = await self.llm_integration.call_llm_async(messages, temperature=0.5, max_tokens=4096, task_type=_task_type)
        
        if not response.success:
            logger.warning(f"LLM调用失败: {response.error}")
            return None
        
        # 解析JSON响应
        parsed = self.llm_integration.parse_json_response(response.content)
        
        if "parse_error" in parsed:
            logger.warning(f"LLM响应解析失败: {response.content[:200]}")
            return None
        
        # 构建完整的反思报告
        reflection_report = {
            "subtask_id": subtask_id,
            "description": subtask_data.get("description", ""),
            "audit_result": parsed.get("audit_result", {}),
            "key_findings": parsed.get("key_findings", []),
            "patterns": parsed.get("patterns", {}),
            "insight": parsed.get("insight", ""),
            "timestamp": datetime.now().isoformat(),
            "execution_summary": self._summarize_execution(execution_result),
            "llm_analysis": True
        }
        
        # 记录反思
        audit_result = parsed.get("audit_result", {})
        reflection_insight = ReflectionInsight(
            timestamp=datetime.now().isoformat(),
            subtask_id=subtask_id,
            normalized_status=audit_result.get("status", "unknown"),
            key_insight=parsed.get("insight", ""),
            failure_pattern=parsed.get("patterns", {}).get("failure_pattern"),
            full_reflection_report=reflection_report,
            llm_reflection_prompt=user_prompt,
            llm_reflection_response=response.content
        )
        
        self.reflection_log.append(reflection_insight)
        
        # 更新模式库
        self._update_pattern_libraries(parsed.get("patterns", {}), audit_result)
        
        # 检查是否需要压缩
        if len(self.reflection_log) > 15:
            self._needs_compression = True
        
        return reflection_report
    
    def _analyze_with_rules(self, subtask_id: str, execution_result: Dict[str, Any],
                            subtask_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用规则分析执行结果（回退模式）
        
        Args:
            subtask_id: 子任务ID
            execution_result: 执行结果
            subtask_data: 子任务数据
            
        Returns:
            Dict[str, Any]: 反思报告
        """
        # 1. 提取基本信息
        description = subtask_data.get("description", "")
        mission_briefing = subtask_data.get("mission_briefing", "")
        completion_criteria = subtask_data.get("completion_criteria", "")
        
        # 2. 评估任务完成情况
        audit_result = self._audit_task_completion(
            execution_result, 
            completion_criteria,
            mission_briefing
        )
        
        # 3. 提取关键发现
        key_findings = self._extract_key_findings(execution_result, subtask_data)
        
        # 4. 识别模式
        patterns = self._identify_patterns(execution_result, audit_result)
        
        # 5. 生成洞察
        insight = self._generate_insight(
            subtask_id,
            execution_result,
            audit_result,
            key_findings,
            patterns
        )
        
        # 6. 构建反思报告
        reflection_report = {
            "subtask_id": subtask_id,
            "description": description,
            "audit_result": audit_result.__dict__,
            "key_findings": key_findings,
            "patterns": patterns,
            "insight": insight,
            "timestamp": datetime.now().isoformat(),
            "execution_summary": self._summarize_execution(execution_result),
            "llm_analysis": False
        }
        
        # 7. 记录反思
        reflection_insight = ReflectionInsight(
            timestamp=datetime.now().isoformat(),
            subtask_id=subtask_id,
            normalized_status=audit_result.status,
            key_insight=insight,
            failure_pattern=patterns.get("failure_pattern"),
            full_reflection_report=reflection_report
        )
        
        self.reflection_log.append(reflection_insight)
        
        # 8. 更新模式库
        self._update_pattern_libraries(patterns, audit_result)
        
        # 9. 检查是否需要压缩
        if len(self.reflection_log) > 15:
            self._needs_compression = True
        
        logger.debug(f"反思完成: {subtask_id} - 状态: {audit_result.status}")
        
        return reflection_report
    
    def _audit_task_completion(self,
                              execution_result: Dict[str, Any],
                              completion_criteria: str,
                              mission_briefing: str) -> AuditResult:
        """审计任务完成情况
        
        Args:
            execution_result: 执行结果
            completion_criteria: 完成标准
            mission_briefing: 任务简报
            
        Returns:
            AuditResult: 审计结果
        """
        # 检查执行是否成功
        success = execution_result.get("success", False)
        error = execution_result.get("error")
        
        # 分析任务类型
        task_type = execution_result.get("task_type", "unknown")
        
        # 根据任务类型和结果评估完成情况
        if success:
            # 检查是否达成目标
            if task_type == "reconnaissance":
                findings = execution_result.get("findings", [])
                if findings:
                    return AuditResult(
                        status="goal_achieved",
                        completion_check="成功收集到目标信息",
                        confidence=0.9,
                        recommendations=["继续下一阶段任务"]
                    )
            
            elif task_type == "vulnerability_scan":
                vulnerabilities = execution_result.get("vulnerabilities", [])
                if vulnerabilities:
                    return AuditResult(
                        status="goal_achieved",
                        completion_check="成功识别到安全漏洞",
                        confidence=0.85,
                        recommendations=["准备漏洞利用"]
                    )
            
            elif task_type == "exploitation":
                access_gained = execution_result.get("access_gained", False)
                if access_gained:
                    return AuditResult(
                        status="goal_achieved",
                        completion_check="成功获得系统访问权限",
                        confidence=0.95,
                        recommendations=["进行后渗透活动"]
                    )
            
            elif task_type == "post_exploitation":
                activities = execution_result.get("activities", [])
                if activities:
                    return AuditResult(
                        status="goal_achieved",
                        completion_check="成功完成后渗透活动",
                        confidence=0.8,
                        recommendations=["整理攻击成果"]
                    )
            
            # 通用成功
            return AuditResult(
                status="partial_success",
                completion_check="任务执行成功，但需要进一步验证目标达成",
                confidence=0.7,
                recommendations=["验证任务目标是否完全达成"]
            )
        
        else:
            # 任务失败
            error_msg = error or "未知错误"
            
            # 分析失败原因
            failure_reason = self._analyze_failure_reason(execution_result, error_msg)
            
            return AuditResult(
                status="failed",
                completion_check=f"任务执行失败: {failure_reason}",
                confidence=0.3,
                recommendations=[
                    "检查目标可达性",
                    "验证工具配置",
                    "尝试替代方法"
                ]
            )
    
    def _analyze_failure_reason(self,
                               execution_result: Dict[str, Any],
                               error_msg: str) -> str:
        """分析失败原因
        
        Args:
            execution_result: 执行结果
            error_msg: 错误信息
            
        Returns:
            str: 失败原因分析
        """
        # 检查错误类型
        error_lower = error_msg.lower()
        
        if any(word in error_lower for word in ["timeout", "连接超时", "请求超时"]):
            return "网络连接超时，目标可能不可达或存在网络限制"
        
        elif any(word in error_lower for word in ["connection refused", "连接拒绝"]):
            return "连接被拒绝，目标服务可能未运行或存在防火墙限制"
        
        elif any(word in error_lower for word in ["permission denied", "权限拒绝"]):
            return "权限不足，需要提升权限或使用认证信息"
        
        elif any(word in error_lower for word in ["not found", "未找到", "404"]):
            return "资源未找到，目标可能不存在或路径错误"
        
        elif any(word in error_lower for word in ["tool not found", "工具未找到"]):
            return "所需工具未安装或配置错误"
        
        else:
            # 通用失败分析
            task_type = execution_result.get("task_type", "unknown")
            
            if task_type == "reconnaissance":
                return "信息收集失败，可能目标防护严密或网络环境复杂"
            elif task_type == "vulnerability_scan":
                return "漏洞扫描失败，可能目标已修复漏洞或扫描配置不当"
            elif task_type == "exploitation":
                return "漏洞利用失败，可能漏洞已修复或利用条件不满足"
            else:
                return f"任务执行失败: {error_msg}"
    
    def _extract_key_findings(self,
                             execution_result: Dict[str, Any],
                             subtask_data: Dict[str, Any]) -> List[str]:
        """提取关键发现
        
        Args:
            execution_result: 执行结果
            subtask_data: 子任务数据
            
        Returns:
            List[str]: 关键发现列表
        """
        findings = []
        
        # 从执行结果中提取发现
        task_type = execution_result.get("task_type", "")
        
        if task_type == "reconnaissance":
            recon_findings = execution_result.get("findings", [])
            for finding in recon_findings[:5]:
                if isinstance(finding, str):
                    findings.append(f"侦察发现: {finding}")
                elif isinstance(finding, dict):
                    text = finding.get("description") or finding.get("text") or str(finding)
                    findings.append(f"侦察发现: {text}")
        
        elif task_type == "vulnerability_scan":
            vulnerabilities = execution_result.get("vulnerabilities", [])
            for vuln in vulnerabilities[:3]:
                if isinstance(vuln, dict):
                    vuln_type = vuln.get("type", "未知漏洞")
                    severity = vuln.get("severity", "未知严重性")
                    location = vuln.get("location", "未知位置")
                    findings.append(f"漏洞发现: {severity}级{vuln_type}位于{location}")
                elif isinstance(vuln, str):
                    findings.append(f"漏洞发现: {vuln}")
        
        elif task_type == "exploitation":
            exploit_success = execution_result.get("exploit_success", False)
            access_gained = execution_result.get("access_gained", False)
            
            if exploit_success or access_gained:
                findings.append("漏洞利用成功，获得系统访问权限")
            else:
                findings.append("漏洞利用尝试失败")
        
        elif task_type == "post_exploitation":
            activities = execution_result.get("activities", [])
            for activity in activities[:3]:
                findings.append(f"后渗透活动: {activity}")
        
        # 添加通用发现
        if execution_result.get("simulated", False):
            findings.append("注意: 此任务使用模拟执行，实际结果可能不同")
        
        # 确保至少有一个发现
        if not findings:
            findings.append("未提取到关键发现")
        
        return findings
    
    def _identify_patterns(self,
                          execution_result: Dict[str, Any],
                          audit_result: AuditResult) -> Dict[str, Any]:
        """识别模式
        
        Args:
            execution_result: 执行结果
            audit_result: 审计结果
            
        Returns:
            Dict[str, Any]: 识别到的模式
        """
        patterns = {
            "success_pattern": None,
            "failure_pattern": None,
            "efficiency_pattern": None,
            "tool_usage_pattern": None
        }
        
        status = audit_result.status
        
        # 识别成功模式
        if status == "goal_achieved":
            task_type = execution_result.get("task_type", "")
            patterns["success_pattern"] = f"{task_type}_success"
            
            # 检查执行效率
            execution_time = execution_result.get("execution_time", 0)
            if execution_time < 5.0:
                patterns["efficiency_pattern"] = "fast_execution"
            elif execution_time > 30.0:
                patterns["efficiency_pattern"] = "slow_execution"
        
        # 识别失败模式
        elif status == "failed":
            error = execution_result.get("error", "")
            patterns["failure_pattern"] = self._categorize_failure(error)
        
        # 识别工具使用模式
        tool_calls = execution_result.get("tool_calls", [])
        if tool_calls:
            tool_names = [call.get("tool_name", "unknown") for call in tool_calls]
            unique_tools = set(tool_names)
            
            if len(unique_tools) == 1:
                patterns["tool_usage_pattern"] = "single_tool_focus"
            elif len(unique_tools) > 3:
                patterns["tool_usage_pattern"] = "multi_tool_coordination"
        
        return patterns
    
    def _categorize_failure(self, error_msg: str) -> str:
        """分类失败模式
        
        Args:
            error_msg: 错误信息
            
        Returns:
            str: 失败模式分类
        """
        error_lower = error_msg.lower()
        
        if any(word in error_lower for word in ["timeout", "超时"]):
            return "network_timeout"
        elif any(word in error_lower for word in ["connection", "连接"]):
            return "connection_failure"
        elif any(word in error_lower for word in ["permission", "权限"]):
            return "permission_denied"
        elif any(word in error_lower for word in ["tool", "工具"]):
            return "tool_failure"
        elif any(word in error_lower for word in ["resource", "资源"]):
            return "resource_unavailable"
        else:
            return "unknown_failure"
    
    def _generate_insight(self,
                         subtask_id: str,
                         execution_result: Dict[str, Any],
                         audit_result: AuditResult,
                         key_findings: List[str],
                         patterns: Dict[str, Any]) -> str:
        """生成洞察
        
        Args:
            subtask_id: 子任务ID
            execution_result: 执行结果
            audit_result: 审计结果
            key_findings: 关键发现
            patterns: 识别到的模式
            
        Returns:
            str: 洞察文本
        """
        status = audit_result.status
        task_type = execution_result.get("task_type", "unknown")
        
        if status == "goal_achieved":
            if task_type == "reconnaissance":
                return "成功完成目标侦察，获得了详细的目标画像，为后续攻击提供了坚实基础。"
            elif task_type == "vulnerability_scan":
                return "成功识别到关键安全漏洞，发现了可利用的攻击入口点。"
            elif task_type == "exploitation":
                return "成功利用漏洞获得系统访问权限，攻击链的关键环节已突破。"
            elif task_type == "post_exploitation":
                return "成功完成后渗透活动，巩固了访问权限并扩大了攻击成果。"
            else:
                return "任务成功完成，达到了预期目标。"
        
        elif status == "partial_success":
            return "任务部分成功，取得了进展但需要进一步优化或验证。"
        
        elif status == "failed":
            failure_pattern = patterns.get("failure_pattern", "unknown")
            
            if failure_pattern == "network_timeout":
                return "任务因网络超时失败，建议检查网络连接或调整超时设置。"
            elif failure_pattern == "connection_failure":
                return "任务因连接问题失败，目标可能不可达或存在网络限制。"
            elif failure_pattern == "permission_denied":
                return "任务因权限不足失败，需要提升权限或使用认证信息。"
            elif failure_pattern == "tool_failure":
                return "任务因工具问题失败，需要检查工具配置或尝试替代工具。"
            else:
                return "任务执行失败，需要分析具体原因并调整策略。"
        
        else:
            return "任务状态未知，需要进一步分析。"
    
    def _summarize_execution(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """总结执行情况
        
        Args:
            execution_result: 执行结果
            
        Returns:
            Dict[str, Any]: 执行摘要
        """
        return {
            "task_type": execution_result.get("task_type", "unknown"),
            "success": execution_result.get("success", False),
            "execution_time": execution_result.get("execution_time", 0),
            "tool_count": len(execution_result.get("tool_calls", [])),
            "simulated": execution_result.get("simulated", False),
            "key_output": list(execution_result.keys())
        }
    
    def _update_pattern_libraries(self,
                                 patterns: Dict[str, Any],
                                 audit_result: AuditResult) -> None:
        """更新模式库
        
        Args:
            patterns: 识别到的模式
            audit_result: 审计结果（AuditResult 对象或 dict）
        """
        # 兼容 AuditResult 对象和 dict 两种类型
        if isinstance(audit_result, dict):
            status = audit_result.get("status", "unknown")
        else:
            status = audit_result.status
        
        # 更新失败模式库
        failure_pattern = patterns.get("failure_pattern")
        if failure_pattern and status == "failed":
            if failure_pattern not in self.failure_patterns:
                self.failure_patterns[failure_pattern] = {
                    "count": 0,
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "common_causes": [],
                    "solutions": []
                }
            
            self.failure_patterns[failure_pattern]["count"] += 1
            self.failure_patterns[failure_pattern]["last_seen"] = datetime.now().isoformat()
        
        # 更新成功模式库
        success_pattern = patterns.get("success_pattern")
        if success_pattern and status == "goal_achieved":
            if success_pattern not in self.success_patterns:
                self.success_patterns[success_pattern] = {
                    "count": 0,
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "key_factors": [],
                    "replication_guidance": []
                }
            
            self.success_patterns[success_pattern]["count"] += 1
            self.success_patterns[success_pattern]["last_seen"] = datetime.now().isoformat()
    
    async def generate_intelligence_summary(self, 
                                     recent_reflections: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成情报摘要
        
        Args:
            recent_reflections: 最近的反思结果（可选）
            
        Returns:
            Dict[str, Any]: 情报摘要
        """
        if recent_reflections is None:
            # 使用最近的反思记录
            recent_reflections = []
            for insight in self.reflection_log[-10:]:
                if insight.full_reflection_report:
                    recent_reflections.append(insight.full_reflection_report)
        
        # 如果使用LLM且有足够的反思记录，尝试智能汇总
        if self.use_llm and self.llm_integration and len(recent_reflections) >= 2:
            try:
                summary = await self._generate_intelligence_with_llm(recent_reflections)
                if summary:
                    return summary
            except Exception as e:
                logger.warning(f"LLM情报汇总失败: {e}，使用回退模式")
        
        # 回退到基于规则的汇总
        return self._generate_intelligence_with_rules(recent_reflections)
    
    async def _generate_intelligence_with_llm(self, recent_reflections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """使用LLM生成情报摘要
        
        Args:
            recent_reflections: 最近的反思结果
            
        Returns:
            Optional[Dict[str, Any]]: 情报摘要
        """
        # 简化反思数据以避免 token 过多
        simplified_reflections = []
        for r in recent_reflections[-5:]:  # 只取最近5个
            simplified_reflections.append({
                "subtask_id": r.get("subtask_id"),
                "status": r.get("audit_result", {}).get("status"),
                "key_findings": r.get("key_findings", [])[:3],
                "insight": r.get("insight", "")[:200]
            })

        # 使用优化后的提示词
        system_prompt = get_reflector_system_prompt()

        user_prompt = get_reflector_intelligence_prompt(
            recent_reflections=json.dumps(simplified_reflections, ensure_ascii=False, indent=2),
            failure_patterns=json.dumps({k: v['count'] for k, v in self.failure_patterns.items()}, ensure_ascii=False),
            success_patterns=json.dumps({k: v['count'] for k, v in self.success_patterns.items()}, ensure_ascii=False),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 异步调用 LLM
        response = await self.llm_integration.call_llm_async(messages, temperature=0.5, max_tokens=4096)
        
        if not response.success:
            return None
        
        # 解析JSON响应
        parsed = self.llm_integration.parse_json_response(response.content)
        
        if "parse_error" in parsed:
            return None
        
        # 构建完整的情报摘要
        intelligence_summary = {
            "findings": parsed.get("findings", []),
            "audit_result": parsed.get("audit_result", {
                "status": "AGGREGATED",
                "completion_check": "汇总多个任务的审计结果",
                "confidence": 0.6
            }),
            "patterns_summary": parsed.get("patterns_summary", {
                "failure_patterns": {k: v["count"] for k, v in self.failure_patterns.items()},
                "success_patterns": {k: v["count"] for k, v in self.success_patterns.items()}
            }),
            "strategic_recommendations": parsed.get("strategic_recommendations", []),
            "reflection_count": len(recent_reflections),
            "timestamp": datetime.now().isoformat(),
            "llm_summary": True
        }
        
        return intelligence_summary
    
    def _generate_intelligence_with_rules(self, recent_reflections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用规则生成情报摘要（回退模式）
        
        Args:
            recent_reflections: 最近的反思结果
            
        Returns:
            Dict[str, Any]: 情报摘要
        """
        # 汇总关键发现
        all_findings = []
        for reflection in recent_reflections:
            findings = reflection.get("key_findings", [])
            all_findings.extend(findings)
        
        # 检查是否有目标达成
        goal_achieved = False
        completion_check = "汇总多个任务的审计结果"
        
        for reflection in recent_reflections:
            audit_result = reflection.get("audit_result", {})
            if audit_result.get("status") == "goal_achieved":
                goal_achieved = True
                completion_check = audit_result.get("completion_check", "目标已达成")
                break
        
        # 构建情报摘要
        # 聚合硬规则触发的 pending actions
        pending_validations = []
        payload_mutations = []
        tool_failures = []
        for reflection in recent_reflections:
            hard_action = reflection.get("hard_action")
            if hard_action == "trigger_validation":
                ex_summary = reflection.get("execution_summary", {})
                pending_validations.append({
                    "subtask_id": reflection.get("subtask_id"),
                    "vuln_info": ex_summary.get("vulnerabilities", reflection.get("key_findings", [])),
                })
            elif hard_action == "mutate_payload":
                payload_mutations.append(reflection.get("subtask_id"))
            elif hard_action == "switch_tool":
                tool_failures.append(reflection.get("subtask_id"))

        intelligence_summary = {
            "findings": all_findings[:20],
            "audit_result": {
                "status": "goal_achieved" if goal_achieved else "AGGREGATED",
                "completion_check": completion_check,
                "confidence": 0.8 if goal_achieved else 0.6
            },
            "patterns_summary": {
                "failure_patterns": {k: v["count"] for k, v in self.failure_patterns.items()},
                "success_patterns": {k: v["count"] for k, v in self.success_patterns.items()}
            },
            "strategic_recommendations": [],
            "reflection_count": len(recent_reflections),
            "timestamp": datetime.now().isoformat(),
            "llm_summary": False,
            # 硬规则聚合信息，供 Planner.dynamic_replan() 使用
            "pending_validations": pending_validations,
            "payload_mutations": payload_mutations,
            "tool_failures": tool_failures,
        }
        
        return intelligence_summary
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """获取反思摘要
        
        Returns:
            Dict[str, Any]: 反思摘要
        """
        total_reflections = len(self.reflection_log)
        
        # 统计状态分布
        status_counts = {}
        for insight in self.reflection_log:
            status = insight.normalized_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 获取最近洞察
        recent_insights = []
        for insight in self.reflection_log[-5:]:
            recent_insights.append({
                "subtask_id": insight.subtask_id,
                "status": insight.normalized_status,
                "insight": insight.key_insight[:100] + "..." if len(insight.key_insight) > 100 else insight.key_insight
            })
        
        summary = {
            "total_reflections": total_reflections,
            "status_distribution": status_counts,
            "failure_patterns_count": len(self.failure_patterns),
            "success_patterns_count": len(self.success_patterns),
            "compression_count": self.compression_count,
            "needs_compression": self._needs_compression,
            "recent_insights": recent_insights,
            "use_llm": self.use_llm
        }
        
        # 添加LLM统计
        if self.llm_integration:
            summary["llm_stats"] = self.llm_integration.get_stats()
        
        return summary
    
    def needs_compression(self) -> bool:
        """检查是否需要压缩
        
        Returns:
            bool: 是否需要压缩
        """
        return self._needs_compression
    
    def mark_compressed(self) -> None:
        """标记为已压缩"""
        self._needs_compression = False
    
    def clear_history(self) -> None:
        """清空反思历史"""
        self.reflection_log.clear()
        self.failure_patterns.clear()
        self.success_patterns.clear()
        self.compressed_reflection_summary = None
        self.compression_count = 0
        self._needs_compression = False
        logger.info("反思历史已清空")


async def test_reflector():
    """测试反思器功能"""
    import sys
    
    print("=" * 80)
    print("PER反思器测试")
    print("=" * 80)
    
    # 创建反思器实例
    reflector = PERReflector(use_llm=False)  # 测试时使用规则模式
    
    # 测试1: 成功任务反思
    print("\n测试1: 成功任务反思")
    success_result = {
        "success": True,
        "task_type": "reconnaissance",
        "findings": [
            "目标运行Web服务（端口80,443）",
            "技术栈: nginx + PHP + WordPress",
            "发现3个子域名"
        ],
        "execution_time": 3.5,
        "tool_calls": [
            {"tool_name": "nmap", "success": True},
            {"tool_name": "whatweb", "success": True}
        ]
    }
    
    success_task = {
        "description": "信息收集: example.com",
        "mission_briefing": "对目标进行全面的信息收集",
        "completion_criteria": "完成端口扫描和服务识别"
    }
    
    reflection1 = await reflector.analyze_execution_result("recon_success", success_result, success_task)
    print(f"反思结果状态: {reflection1['audit_result']['status']}")
    print(f"关键发现数: {len(reflection1['key_findings'])}")
    print(f"洞察: {reflection1['insight']}")
    print(f"使用LLM: {reflection1.get('llm_analysis', False)}")
    
    # 测试2: 失败任务反思
    print("\n测试2: 失败任务反思")
    failure_result = {
        "success": False,
        "error": "连接超时: 目标不可达",
        "task_type": "vulnerability_scan",
        "execution_time": 10.0,
        "tool_calls": [
            {"tool_name": "nuclei", "success": False}
        ]
    }
    
    failure_task = {
        "description": "漏洞扫描: example.com",
        "mission_briefing": "基于信息收集结果进行漏洞扫描",
        "completion_criteria": "识别潜在的安全漏洞"
    }
    
    reflection2 = await reflector.analyze_execution_result("vuln_scan_failed", failure_result, failure_task)
    print(f"反思结果状态: {reflection2['audit_result']['status']}")
    print(f"失败原因: {reflection2['audit_result']['completion_check']}")
    print(f"建议: {reflection2['audit_result']['recommendations']}")
    
    # 测试3: 生成情报摘要
    print("\n测试3: 生成情报摘要")
    intelligence = await reflector.generate_intelligence_summary([reflection1, reflection2])
    print(f"总发现数: {len(intelligence['findings'])}")
    print(f"审计状态: {intelligence['audit_result']['status']}")
    print(f"失败模式: {intelligence['patterns_summary']['failure_patterns']}")
    print(f"使用LLM: {intelligence.get('llm_summary', False)}")
    
    # 测试4: 获取反思摘要
    print("\n测试4: 反思摘要")
    summary = reflector.get_reflection_summary()
    print(f"总反思数: {summary['total_reflections']}")
    print(f"状态分布: {summary['status_distribution']}")
    print(f"失败模式数: {summary['failure_patterns_count']}")
    print(f"使用LLM: {summary['use_llm']}")
    
    print("\n" + "=" * 80)
    print("[PASS] 反思器测试完成")
    
    return True


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_reflector())
    sys.exit(0 if success else 1)
