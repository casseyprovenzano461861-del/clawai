# -*- coding: utf-8 -*-
"""
PromptManager - 提示词模板管理系统
基于 Jinja2 的模板化管理，支持多语言和动态渲染
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

logger = logging.getLogger(__name__)


class PromptLanguage(Enum):
    """提示词语言"""
    ZH = "zh"  # 中文
    EN = "en"  # 英文


@dataclass
class PromptContext:
    """提示词上下文"""
    # 目标信息
    target: str = ""
    target_type: str = ""
    
    # 执行状态
    phase: str = "idle"
    iteration: int = 0
    max_iterations: int = 10
    
    # 发现信息
    findings: List[str] = field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    open_ports: List[Dict[str, Any]] = field(default_factory=list)
    
    # 工具信息
    available_tools: List[str] = field(default_factory=list)
    executed_tools: List[str] = field(default_factory=list)
    
    # 历史信息
    previous_commands: List[str] = field(default_factory=list)
    previous_results: List[str] = field(default_factory=list)
    
    # 压缩历史
    compressed_history: str = ""
    
    # 其他
    mode: str = "chat"
    additional_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target": self.target,
            "target_type": self.target_type,
            "phase": self.phase,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "findings": self.findings,
            "vulnerabilities": self.vulnerabilities,
            "open_ports": self.open_ports,
            "available_tools": self.available_tools,
            "executed_tools": self.executed_tools,
            "previous_commands": self.previous_commands,
            "previous_results": self.previous_results,
            "compressed_history": self.compressed_history,
            "mode": self.mode,
            **self.additional_context
        }


class PromptManager:
    """提示词管理器
    
    功能：
    1. Jinja2 模板化管理
    2. 多语言支持
    3. 动态渲染
    4. 模板继承和组合
    """
    
    def __init__(
        self,
        template_dir: str = None,
        language: PromptLanguage = PromptLanguage.ZH
    ):
        """初始化提示词管理器
        
        Args:
            template_dir: 模板目录路径
            language: 默认语言
        """
        self.language = language
        
        # 设置模板目录
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path(__file__).parent / "templates"
        
        # 初始化 Jinja2 环境
        if JINJA2_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True
            )
            self._load_templates()
        else:
            self.env = None
            logger.warning("Jinja2 未安装，使用静态提示词模式")
        
        # 缓存渲染后的提示词
        self._prompt_cache: Dict[str, str] = {}
        
        logger.info(f"PromptManager 初始化完成，语言: {language.value}")
    
    def _load_templates(self):
        """加载所有模板"""
        self.templates: Dict[str, Template] = {}
        
        # 定义要加载的模板
        template_names = [
            "system_prompt",
            "planner_template",
            "executor_template",
            "reflector_template",
            "tool_selection_guide",
            "vulnerability_testing_guide",
        ]
        
        for name in template_names:
            template_path = f"{self.language.value}/{name}.jinja2"
            try:
                self.templates[name] = self.env.get_template(template_path)
                logger.debug(f"加载模板: {name}")
            except Exception as e:
                logger.warning(f"加载模板失败 {name}: {e}")
    
    def render(self, template_name: str, context: PromptContext) -> str:
        """渲染模板
        
        Args:
            template_name: 模板名称
            context: 渲染上下文
            
        Returns:
            str: 渲染后的提示词
        """
        if self.env and template_name in self.templates:
            try:
                return self.templates[template_name].render(**context.to_dict())
            except Exception as e:
                logger.error(f"渲染模板失败 {template_name}: {e}")
                return self._get_fallback_prompt(template_name, context)
        
        return self._get_fallback_prompt(template_name, context)
    
    def get_system_prompt(self, context: PromptContext) -> str:
        """获取系统提示词"""
        return self.render("system_prompt", context)
    
    def get_planner_prompt(self, context: PromptContext) -> str:
        """获取规划器提示词"""
        return self.render("planner_template", context)
    
    def get_executor_prompt(self, context: PromptContext) -> str:
        """获取执行器提示词"""
        return self.render("executor_template", context)
    
    def get_reflector_prompt(self, context: PromptContext) -> str:
        """获取反思器提示词"""
        return self.render("reflector_template", context)
    
    def _get_fallback_prompt(self, template_name: str, context: PromptContext) -> str:
        """获取备用静态提示词"""
        fallbacks = {
            "system_prompt": self._get_default_system_prompt(context),
            "planner_template": self._get_default_planner_prompt(context),
            "executor_template": self._get_default_executor_prompt(context),
            "reflector_template": self._get_default_reflector_prompt(context),
        }
        return fallbacks.get(template_name, "")
    
    def _get_default_system_prompt(self, context: PromptContext) -> str:
        """默认系统提示词"""
        return f"""你是 ClawAI，一个专业的 AI 渗透测试助手。

## 当前上下文
- 目标: {context.target or '未设置'}
- 阶段: {context.phase}
- 已发现: {len(context.findings)} 项
- 漏洞数: {len(context.vulnerabilities)} 个

## 你的能力
- 信息收集工具: nmap_scan, whatweb_scan, subfinder_scan, dirsearch_scan
- 漏洞扫描工具: nuclei_scan, sqlmap_scan, nikto_scan
- 渗透测试流程: start_pentest, get_pentest_status

## 工作原则
1. 确保用户已获得测试授权
2. 高风险操作需要用户确认
3. 分析结果并提供专业建议
"""
    
    def _get_default_planner_prompt(self, context: PromptContext) -> str:
        """默认规划器提示词"""
        return f"""作为渗透测试规划器，你的任务是将高级目标分解为可执行的子任务。

## 当前目标
{context.target}

## 已有信息
- 阶段: {context.phase}
- 发现: {', '.join(context.findings[:5]) if context.findings else '无'}

## 可用工具
{', '.join(context.available_tools) if context.available_tools else 'nmap_scan, nuclei_scan, sqlmap_scan'}

请分析当前状态，生成下一步行动计划。
"""
    
    def _get_default_executor_prompt(self, context: PromptContext) -> str:
        """默认执行器提示词"""
        return f"""作为渗透测试执行器，你的任务是执行具体的子任务。

## 当前任务
{context.phase}

## 目标信息
{context.target}

## 执行历史
{context.compressed_history or '无'}

请选择合适的工具并生成执行命令。
"""
    
    def _get_default_reflector_prompt(self, context: PromptContext) -> str:
        """默认反思器提示词"""
        return f"""作为渗透测试反思器，你的任务是分析执行结果并提供洞察。

## 执行结果
待分析

## 目标
{context.target}

## 已发现
{', '.join(context.findings[:10]) if context.findings else '无'}

请分析结果，判断是否需要调整策略。
"""
    
    def set_language(self, language: PromptLanguage):
        """设置语言"""
        self.language = language
        if JINJA2_AVAILABLE:
            self._load_templates()
        logger.info(f"语言切换为: {language.value}")
    
    def register_template(self, name: str, template_content: str):
        """注册自定义模板
        
        Args:
            name: 模板名称
            template_content: 模板内容
        """
        if JINJA2_AVAILABLE:
            from jinja2 import Template
            self.templates[name] = Template(template_content)
            logger.info(f"注册自定义模板: {name}")


# ==================== 便捷函数 ====================

def create_prompt_manager(
    language: str = "zh",
    template_dir: str = None
) -> PromptManager:
    """创建提示词管理器
    
    Args:
        language: 语言代码 (zh/en)
        template_dir: 模板目录
        
    Returns:
        PromptManager: 管理器实例
    """
    lang_map = {
        "zh": PromptLanguage.ZH,
        "en": PromptLanguage.EN,
        "chinese": PromptLanguage.ZH,
        "english": PromptLanguage.EN
    }
    
    return PromptManager(
        template_dir=template_dir,
        language=lang_map.get(language.lower(), PromptLanguage.ZH)
    )


# ==================== 测试 ====================

def test_prompt_manager():
    """测试提示词管理器"""
    print("=" * 60)
    print("PromptManager 测试")
    print("=" * 60)
    
    manager = create_prompt_manager(language="zh")
    
    # 创建上下文
    context = PromptContext(
        target="example.com",
        phase="reconnaissance",
        findings=["开放端口 80", "运行 nginx"],
        vulnerabilities=[{"type": "SQL注入", "severity": "high"}]
    )
    
    # 测试系统提示词
    print("\n1. 系统提示词:")
    system_prompt = manager.get_system_prompt(context)
    print(system_prompt[:500] + "...")
    
    # 测试规划器提示词
    print("\n2. 规划器提示词:")
    planner_prompt = manager.get_planner_prompt(context)
    print(planner_prompt)
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_prompt_manager()
