"""
Prompt模板化管理器
借鉴 LuaN1aoAgent 的 Prompt 管理设计
支持 Jinja2 模板、多语言、缓存和版本控制
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape, TemplateError

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Prompt模板数据结构"""
    name: str
    template_path: str
    description: str = ""
    version: str = "1.0.0"
    language: str = "zh"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "template_path": self.template_path,
            "description": self.description,
            "version": self.version,
            "language": self.language,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class RenderedPrompt:
    """渲染后的Prompt结果"""
    content: str
    template_name: str
    variables: Dict[str, Any]
    token_estimate: int
    rendered_at: datetime = field(default_factory=datetime.now)
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.md5(self.content.encode()).hexdigest()[:8]


class PromptManager:
    """
    Prompt模板管理器
    
    功能：
    - Jinja2模板加载与渲染
    - 多语言支持（中/英）
    - 模板缓存
    - 变量验证
    - Token估算
    - 版本管理
    
    使用示例：
        manager = PromptManager(template_dir="prompts/templates")
        
        # 渲染模板
        prompt = manager.render("planner/planning", {
            "target": "example.com",
            "context": {...}
        })
    """
    
    def __init__(
        self,
        template_dir: Optional[str] = None,
        cache_enabled: bool = True,
        default_language: str = "zh",
        auto_reload: bool = False
    ):
        """
        初始化Prompt管理器
        
        Args:
            template_dir: 模板目录路径
            cache_enabled: 是否启用缓存
            default_language: 默认语言
            auto_reload: 是否自动重载模板（开发模式）
        """
        # 设置模板目录
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        self.template_dir = Path(template_dir)
        self.cache_enabled = cache_enabled
        self.default_language = default_language
        self.auto_reload = auto_reload
        
        # 初始化Jinja2环境
        self._init_jinja_env()
        
        # 模板缓存
        self._template_cache: Dict[str, Template] = {}
        
        # 模板元数据缓存
        self._metadata_cache: Dict[str, PromptTemplate] = {}
        
        # 加载模板元数据
        self._load_metadata()
        
        logger.info(f"PromptManager初始化完成，模板目录: {self.template_dir}")
    
    def _init_jinja_env(self):
        """初始化Jinja2环境"""
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"]
        )
        
        # 注册自定义过滤器
        self.env.filters.update({
            "tojson": self._filter_tojson,
            "datetime": self._filter_datetime,
            "default_if_none": self._filter_default_if_none,
            "truncate_middle": self._filter_truncate_middle,
            "format_list": self._filter_format_list,
            "indent": self._filter_indent,
        })
    
    # ==================== 自定义过滤器 ====================
    
    @staticmethod
    def _filter_tojson(value: Any, indent: int = 2) -> str:
        """JSON格式化过滤器"""
        return json.dumps(value, ensure_ascii=False, indent=indent, default=str)
    
    @staticmethod
    def _filter_datetime(value: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日期时间格式化过滤器"""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(format_str)
    
    @staticmethod
    def _filter_default_if_none(value: Any, default: Any = "") -> Any:
        """默认值过滤器"""
        return value if value is not None else default
    
    @staticmethod
    def _filter_truncate_middle(value: str, length: int = 100, separator: str = "...") -> str:
        """中间截断过滤器"""
        if len(value) <= length:
            return value
        half = (length - len(separator)) // 2
        return value[:half] + separator + value[-half:]
    
    @staticmethod
    def _filter_format_list(value: List[Any], separator: str = "\n") -> str:
        """列表格式化过滤器"""
        if not isinstance(value, list):
            return str(value)
        return separator.join(str(item) for item in value)
    
    @staticmethod
    def _filter_indent(value: str, width: int = 2, first: bool = False) -> str:
        """缩进过滤器"""
        lines = value.split("\n")
        prefix = " " * width
        if first:
            return "\n".join(prefix + line for line in lines)
        return "\n".join(prefix + line if i > 0 else line for i, line in enumerate(lines))
    
    # ==================== 模板加载与渲染 ====================
    
    def get_template(self, name: str, language: Optional[str] = None) -> Template:
        """
        获取模板对象
        
        Args:
            name: 模板名称（不含扩展名）
            language: 语言代码，为None时使用默认语言
            
        Returns:
            Jinja2 Template对象
        """
        language = language or self.default_language
        
        # 尝试获取特定语言版本
        template_name = f"{name}.{language}.jinja2"
        
        # 如果特定语言版本不存在，尝试默认版本
        if not self._template_exists(template_name):
            template_name = f"{name}.jinja2"
        
        # 检查缓存
        cache_key = f"{template_name}:{language}"
        if self.cache_enabled and cache_key in self._template_cache:
            if not self.auto_reload:
                return self._template_cache[cache_key]
        
        # 加载模板
        try:
            template = self.env.get_template(template_name)
            if self.cache_enabled:
                self._template_cache[cache_key] = template
            return template
        except Exception as e:
            logger.error(f"加载模板失败: {name}, 错误: {e}")
            raise TemplateNotFoundError(f"模板不存在: {name}")
    
    def _template_exists(self, template_name: str) -> bool:
        """检查模板文件是否存在"""
        template_path = self.template_dir / template_name
        return template_path.exists()
    
    def render(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        validate: bool = True
    ) -> RenderedPrompt:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            variables: 模板变量
            language: 语言代码
            validate: 是否验证变量
            
        Returns:
            RenderedPrompt对象
        """
        variables = variables or {}
        
        # 获取模板
        template = self.get_template(template_name, language)
        
        # 验证变量
        if validate:
            self._validate_variables(template_name, variables)
        
        try:
            # 渲染模板
            content = template.render(**variables)
            
            # 估算Token数量（简单估算：4字符≈1token）
            token_estimate = len(content) // 4
            
            return RenderedPrompt(
                content=content,
                template_name=template_name,
                variables=variables,
                token_estimate=token_estimate
            )
            
        except TemplateError as e:
            logger.error(f"模板渲染失败: {template_name}, 错误: {e}")
            raise PromptRenderError(f"模板渲染失败: {e}")
    
    def render_string(
        self,
        template_string: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        渲染字符串模板
        
        Args:
            template_string: 模板字符串
            variables: 模板变量
            
        Returns:
            渲染后的字符串
        """
        variables = variables or {}
        template = self.env.from_string(template_string)
        return template.render(**variables)
    
    # ==================== 变量验证 ====================
    
    def _validate_variables(self, template_name: str, variables: Dict[str, Any]) -> bool:
        """
        验证模板变量
        
        Args:
            template_name: 模板名称
            variables: 变量字典
            
        Returns:
            是否验证通过
        """
        # 获取模板所需的变量定义
        schema = self._get_template_schema(template_name)
        
        if not schema:
            return True
        
        # 检查必需变量
        required_vars = schema.get("required", [])
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            logger.warning(f"模板 {template_name} 缺少必需变量: {missing_vars}")
            # 不抛出异常，只记录警告
        
        return True
    
    def _get_template_schema(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板的变量Schema"""
        # 尝试从同名的schema文件加载
        schema_path = self.template_dir / f"{template_name}.schema.json"
        if schema_path.exists():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载模板Schema失败: {schema_path}, 错误: {e}")
        
        return None
    
    # ==================== 模板元数据管理 ====================
    
    def _load_metadata(self):
        """加载模板元数据"""
        metadata_path = self.template_dir / "metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for name, meta in data.items():
                    self._metadata_cache[name] = PromptTemplate(
                        name=name,
                        template_path=meta.get("template_path", f"{name}.jinja2"),
                        description=meta.get("description", ""),
                        version=meta.get("version", "1.0.0"),
                        language=meta.get("language", "zh"),
                        tags=meta.get("tags", [])
                    )
                
                logger.info(f"加载了 {len(self._metadata_cache)} 个模板元数据")
                
            except Exception as e:
                logger.warning(f"加载模板元数据失败: {e}")
    
    def save_metadata(self):
        """保存模板元数据"""
        metadata_path = self.template_dir / "metadata.json"
        
        data = {
            name: template.to_dict() 
            for name, template in self._metadata_cache.items()
        }
        
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"模板元数据已保存到: {metadata_path}")
        except Exception as e:
            logger.error(f"保存模板元数据失败: {e}")
    
    # ==================== 模板注册与管理 ====================
    
    def register_template(
        self,
        name: str,
        template_path: str,
        description: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None
    ):
        """
        注册新模板
        
        Args:
            name: 模板名称
            template_path: 模板路径
            description: 模板描述
            version: 版本号
            tags: 标签列表
        """
        self._metadata_cache[name] = PromptTemplate(
            name=name,
            template_path=template_path,
            description=description,
            version=version,
            tags=tags or []
        )
        
        logger.info(f"注册模板: {name}")
    
    def list_templates(self, tag: Optional[str] = None) -> List[PromptTemplate]:
        """
        列出所有模板
        
        Args:
            tag: 按标签过滤
            
        Returns:
            模板列表
        """
        templates = list(self._metadata_cache.values())
        
        if tag:
            templates = [t for t in templates if tag in t.tags]
        
        return templates
    
    def get_template_info(self, name: str) -> Optional[PromptTemplate]:
        """获取模板信息"""
        return self._metadata_cache.get(name)
    
    # ==================== 辅助方法 ====================
    
    def clear_cache(self):
        """清空模板缓存"""
        self._template_cache.clear()
        logger.info("模板缓存已清空")
    
    def reload(self):
        """重新加载所有模板"""
        self.clear_cache()
        self._load_metadata()
        logger.info("模板已重新加载")
    
    def get_template_content(self, name: str, language: Optional[str] = None) -> str:
        """获取模板原始内容"""
        template = self.get_template(name, language)
        return template.source


# ==================== 异常类 ====================

class PromptManagerError(Exception):
    """Prompt管理器基础异常"""
    pass


class TemplateNotFoundError(PromptManagerError):
    """模板不存在异常"""
    pass


class PromptRenderError(PromptManagerError):
    """Prompt渲染异常"""
    pass


class VariableValidationError(PromptManagerError):
    """变量验证异常"""
    pass


# ==================== 全局实例 ====================

_global_manager: Optional[PromptManager] = None


def get_prompt_manager(
    template_dir: Optional[str] = None,
    **kwargs
) -> PromptManager:
    """
    获取全局Prompt管理器实例
    
    Args:
        template_dir: 模板目录
        **kwargs: 其他参数
        
    Returns:
        PromptManager实例
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = PromptManager(template_dir=template_dir, **kwargs)
    
    return _global_manager


def render_prompt(
    template_name: str,
    variables: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None
) -> str:
    """
    快捷方法：渲染Prompt
    
    Args:
        template_name: 模板名称
        variables: 模板变量
        language: 语言
        
    Returns:
        渲染后的Prompt字符串
    """
    manager = get_prompt_manager()
    result = manager.render(template_name, variables, language)
    return result.content


# 导出
__all__ = [
    "PromptManager",
    "PromptTemplate",
    "RenderedPrompt",
    "PromptManagerError",
    "TemplateNotFoundError",
    "PromptRenderError",
    "VariableValidationError",
    "get_prompt_manager",
    "render_prompt",
]
