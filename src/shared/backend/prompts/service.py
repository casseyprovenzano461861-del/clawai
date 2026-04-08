"""
Prompt渲染服务
提供便捷的Prompt渲染接口，集成到ClawAI系统
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .manager import (
    PromptManager,
    RenderedPrompt,
    get_prompt_manager,
    PromptRenderError
)

logger = logging.getLogger(__name__)


class PromptService:
    """
    Prompt渲染服务
    
    提供统一的Prompt渲染接口，支持：
    - 按场景渲染Prompt
    - 变量自动填充
    - 多语言支持
    - 缓存管理
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化Prompt服务
        
        Args:
            template_dir: 模板目录路径
        """
        self.manager = get_prompt_manager(template_dir=template_dir)
        
        # 默认变量（会在所有渲染中注入）
        self.default_vars: Dict[str, Any] = {
            "system_name": "ClawAI",
            "version": "2.0.0",
        }
    
    def set_default_vars(self, variables: Dict[str, Any]):
        """设置默认变量"""
        self.default_vars.update(variables)
    
    def render(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        include_defaults: bool = True
    ) -> RenderedPrompt:
        """
        渲染Prompt
        
        Args:
            template_name: 模板名称
            variables: 模板变量
            language: 语言代码
            include_defaults: 是否包含默认变量
            
        Returns:
            RenderedPrompt对象
        """
        # 合并变量
        final_vars = {}
        if include_defaults:
            final_vars.update(self.default_vars)
        if variables:
            final_vars.update(variables)
        
        return self.manager.render(template_name, final_vars, language)
    
    def render_planning_prompt(
        self,
        target: str,
        target_info: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        vulnerabilities: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> RenderedPrompt:
        """
        渲染攻击规划Prompt
        
        Args:
            target: 目标地址
            target_info: 目标信息
            context: 上下文信息
            vulnerabilities: 已知漏洞列表
            tools: 可用工具列表
            
        Returns:
            RenderedPrompt对象
        """
        variables = {
            "target": target,
            "target_info": target_info or {},
            "context": context or {},
            "vulnerabilities": vulnerabilities or [],
            "tools": tools or []
        }
        
        return self.render("planner/attack_planning", variables)
    
    def render_execution_prompt(
        self,
        tool_name: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None,
        tool_description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RenderedPrompt:
        """
        渲染工具执行Prompt
        
        Args:
            tool_name: 工具名称
            target: 目标地址
            parameters: 执行参数
            tool_description: 工具描述
            context: 执行上下文
            
        Returns:
            RenderedPrompt对象
        """
        variables = {
            "tool_name": tool_name,
            "target": target,
            "parameters": parameters or {},
            "tool_description": tool_description or "",
            "context": context or {}
        }
        
        return self.render("executor/tool_execution", variables)
    
    def render_verification_prompt(
        self,
        vulnerability: Dict[str, Any],
        target: str,
        target_context: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[Dict[str, Any]]] = None
    ) -> RenderedPrompt:
        """
        渲染漏洞验证Prompt
        
        Args:
            vulnerability: 漏洞信息
            target: 目标地址
            target_context: 目标上下文
            evidence: 已有证据
            
        Returns:
            RenderedPrompt对象
        """
        variables = {
            "vulnerability": vulnerability,
            "target": target,
            "target_context": target_context or {},
            "evidence": evidence or []
        }
        
        return self.render("analyzer/vulnerability_verification", variables)
    
    def render_analysis_prompt(
        self,
        target: str,
        results: Optional[List[Dict[str, Any]]] = None,
        all_findings: Optional[List[Dict[str, Any]]] = None,
        scan_time: Optional[str] = None,
        scan_type: Optional[str] = None
    ) -> RenderedPrompt:
        """
        渲染结果分析Prompt
        
        Args:
            target: 目标地址
            results: 扫描结果列表
            all_findings: 所有发现
            scan_time: 扫描时间
            scan_type: 扫描类型
            
        Returns:
            RenderedPrompt对象
        """
        variables = {
            "target": target,
            "results": results or [],
            "all_findings": all_findings or [],
            "scan_time": scan_time,
            "scan_type": scan_type
        }
        
        return self.render("analyzer/result_analysis", variables)
    
    def render_reflection_prompt(
        self,
        target: str,
        task_id: str,
        status: str,
        execution_steps: Optional[List[Dict[str, Any]]] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> RenderedPrompt:
        """
        渲染经验反思Prompt
        
        Args:
            target: 目标地址
            task_id: 任务ID
            status: 执行状态
            execution_steps: 执行步骤
            results: 结果数据
            
        Returns:
            RenderedPrompt对象
        """
        variables = {
            "target": target,
            "task_id": task_id,
            "status": status,
            "execution_steps": execution_steps or [],
            "results": results or {}
        }
        
        return self.render("reflector/reflection", variables)
    
    def render_report_prompt(
        self,
        target: str,
        title: Optional[str] = None,
        vulnerabilities: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        statistics: Optional[Dict[str, int]] = None,
        assessment_date: Optional[str] = None,
        assessment_type: Optional[str] = None
    ) -> RenderedPrompt:
        """
        渲染报告生成Prompt
        
        Args:
            target: 目标地址
            title: 报告标题
            vulnerabilities: 漏洞列表
            summary: 执行摘要
            statistics: 风险统计
            assessment_date: 评估日期
            assessment_type: 评估类型
            
        Returns:
            RenderedPrompt对象
        """
        variables = {
            "target": target,
            "title": title,
            "vulnerabilities": vulnerabilities or [],
            "summary": summary or {},
            "statistics": statistics or {},
            "assessment_date": assessment_date,
            "assessment_type": assessment_type
        }
        
        return self.render("report/generation", variables)
    
    def get_system_prompt(self, role: str, language: Optional[str] = None) -> str:
        """
        获取角色系统提示
        
        Args:
            role: 角色名称 (planner/executor/reflector)
            language: 语言代码
            
        Returns:
            系统提示字符串
        """
        template_map = {
            "planner": "planner/system_prompt",
            "executor": "executor/system_prompt",
            "reflector": "reflector/system_prompt"
        }
        
        template_name = template_map.get(role)
        if not template_name:
            raise ValueError(f"未知角色: {role}")
        
        result = self.render(template_name, language=language)
        return result.content
    
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用模板"""
        templates = self.manager.list_templates()
        return [t.to_dict() for t in templates]
    
    def clear_cache(self):
        """清空缓存"""
        self.manager.clear_cache()


# 全局服务实例
_prompt_service: Optional[PromptService] = None


def get_prompt_service(template_dir: Optional[str] = None) -> PromptService:
    """获取全局Prompt服务实例"""
    global _prompt_service
    
    if _prompt_service is None:
        _prompt_service = PromptService(template_dir=template_dir)
    
    return _prompt_service


__all__ = [
    "PromptService",
    "get_prompt_service"
]
