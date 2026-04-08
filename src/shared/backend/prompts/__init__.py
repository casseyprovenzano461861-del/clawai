"""
Prompt模块
提供统一的Prompt模板管理功能
"""

from .manager import (
    PromptManager,
    PromptTemplate,
    RenderedPrompt,
    PromptManagerError,
    TemplateNotFoundError,
    PromptRenderError,
    VariableValidationError,
    get_prompt_manager,
    render_prompt,
)

from .service import (
    PromptService,
    get_prompt_service,
)

__all__ = [
    # Manager
    "PromptManager",
    "PromptTemplate",
    "RenderedPrompt",
    # Exceptions
    "PromptManagerError",
    "TemplateNotFoundError",
    "PromptRenderError",
    "VariableValidationError",
    # Functions
    "get_prompt_manager",
    "render_prompt",
    # Service
    "PromptService",
    "get_prompt_service",
]
