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
    
    def __init__(self, llm_client=None):
        """初始化反思器
        
        Args:
            llm_client: LLM客户端实例（可选）
        """
        self.llm_client = llm_client
        
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
        
        logger.info("PERReflector初始化完成")
    
    def analyze_execution_result(self,
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
            "execution_summary": self._summarize_execution(execution_result)
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
        if len(self.reflection_log) > 15:  # 历史窗口大小
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
            for finding in recon_findings[:5]:  # 最多取5个关键发现
                if isinstance(finding, str):
                    findings.append(f"侦察发现: {finding}")
                elif isinstance(finding, dict):
                    # 尝试从字典中提取文本
                    text = finding.get("description") or finding.get("text") or str(finding)
                    findings.append(f"侦察发现: {text}")
        
        elif task_type == "vulnerability_scan":
            vulnerabilities = execution_result.get("vulnerabilities", [])
            for vuln in vulnerabilities[:3]:  # 最多取3个关键漏洞
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
            audit_result: 审计结果
        """
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
    
    def generate_intelligence_summary(self, 
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
            for insight in self.reflection_log[-10:]:  # 最近10个
                if insight.full_reflection_report:
                    recent_reflections.append(insight.full_reflection_report)
        
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
        intelligence_summary = {
            "findings": all_findings[:20],  # 最多20个发现
            "audit_result": {
                "status": "goal_achieved" if goal_achieved else "AGGREGATED",
                "completion_check": completion_check,
                "confidence": 0.8 if goal_achieved else 0.6
            },
            "patterns_summary": {
                "failure_patterns": {k: v["count"] for k, v in self.failure_patterns.items()},
                "success_patterns": {k: v["count"] for k, v in self.success_patterns.items()}
            },
            "reflection_count": len(recent_reflections),
            "timestamp": datetime.now().isoformat()
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
        
        return {
            "total_reflections": total_reflections,
            "status_distribution": status_counts,
            "failure_patterns_count": len(self.failure_patterns),
            "success_patterns_count": len(self.success_patterns),
            "compression_count": self.compression_count,
            "needs_compression": self._needs_compression,
            "recent_insights": recent_insights
        }
    
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


def test_reflector():
    """测试反思器功能"""
    import sys
    
    print("=" * 80)
    print("PER反思器测试")
    print("=" * 80)
    
    # 创建反思器实例
    reflector = PERReflector()
    
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
    
    reflection1 = reflector.analyze_execution_result("recon_success", success_result, success_task)
    print(f"反思结果状态: {reflection1['audit_result']['status']}")
    print(f"关键发现数: {len(reflection1['key_findings'])}")
    print(f"洞察: {reflection1['insight']}")
    
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
    
    reflection2 = reflector.analyze_execution_result("vuln_scan_failed", failure_result, failure_task)
    print(f"反思结果状态: {reflection2['audit_result']['status']}")
    print(f"失败原因: {reflection2['audit_result']['completion_check']}")
    print(f"建议: {reflection2['audit_result']['recommendations']}")
    
    # 测试3: 生成情报摘要
    print("\n测试3: 生成情报摘要")
    intelligence = reflector.generate_intelligence_summary([reflection1, reflection2])
    print(f"总发现数: {len(intelligence['findings'])}")
    print(f"审计状态: {intelligence['audit_result']['status']}")
    print(f"失败模式: {intelligence['patterns_summary']['failure_patterns']}")
    
    # 测试4: 获取反思摘要
    print("\n测试4: 反思摘要")
    summary = reflector.get_reflection_summary()
    print(f"总反思数: {summary['total_reflections']}")
    print(f"状态分布: {summary['status_distribution']}")
    print(f"失败模式数: {summary['failure_patterns_count']}")
    
    print("\n" + "=" * 80)
    print("[PASS] 反思器测试完成")
    
    return True


if __name__ == "__main__":
    success = test_reflector()
    sys.exit(0 if success else 1)
