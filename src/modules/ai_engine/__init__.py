"""
AI引擎模块
将原有的AI引擎微服务功能集成到模块化单体中
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import logging

from .. import BaseModule, ModuleConfig

logger = logging.getLogger(__name__)


class AIEngineConfig(BaseModel):
    """AI引擎配置"""
    llm_provider: str = "openai"
    default_model: str = "gpt-4"
    enabled: bool = True
    max_tokens: int = 4096
    temperature: float = 0.7


class AIModule(BaseModule):
    """AI引擎模块"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_config = AIEngineConfig(**config.config)
        self.llm_integrator = None
        self.skill_registry = None
        self.config_manager = None

    def _setup_routes(self) -> None:
        """设置AI引擎路由"""

        @self.router.get("/health")
        async def health_check():
            """AI引擎健康检查"""
            return {
                "service": "ai_engine",
                "status": "healthy" if self._setup_complete else "unhealthy",
                "config": self.ai_config.dict(),
                "llm_available": self.llm_integrator is not None
            }

        @self.router.get("/configs")
        async def get_llm_configs():
            """获取LLM配置列表"""
            if not self.config_manager:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI引擎未初始化"
                )

            try:
                configs = self.config_manager.list_configs()
                return {
                    "configs": configs,
                    "total": len(configs)
                }
            except Exception as e:
                logger.error(f"获取LLM配置失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"获取配置失败: {str(e)}"
                )

        @self.router.post("/analyze")
        async def analyze_target(analysis_request: Dict[str, Any]):
            """分析目标"""
            if not self.llm_integrator:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI引擎未初始化"
                )

            try:
                target = analysis_request.get("target", "")
                config_name = analysis_request.get("config", "default")

                result = await self.llm_integrator.analyze_target(
                    target=target,
                    config_name=config_name
                )
                return result
            except Exception as e:
                logger.error(f"目标分析失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"分析失败: {str(e)}"
                )

        @self.router.post("/generate-plan")
        async def generate_attack_plan(plan_request: Dict[str, Any]):
            """生成攻击计划"""
            if not self.llm_integrator:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI引擎未初始化"
                )

            try:
                target = plan_request.get("target", "")
                context = plan_request.get("context", {})
                config_name = plan_request.get("config", "default")

                result = await self.llm_integrator.plan_attack(
                    target=target,
                    context=context,
                    config_name=config_name
                )
                return result
            except Exception as e:
                logger.error(f"生成攻击计划失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"生成计划失败: {str(e)}"
                )

        @self.router.post("/execute-skill")
        async def execute_skill(skill_request: Dict[str, Any]):
            """执行AI技能"""
            if not self.skill_registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="技能系统未初始化"
                )

            try:
                skill_name = skill_request.get("skill_name", "")
                parameters = skill_request.get("parameters", {})

                # 这里需要实际的技能执行逻辑
                # 暂时返回模拟结果
                return {
                    "skill_executed": skill_name,
                    "parameters": parameters,
                    "result": f"技能 {skill_name} 执行成功",
                    "status": "completed"
                }
            except Exception as e:
                logger.error(f"执行技能失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"执行技能失败: {str(e)}"
                )

        @self.router.get("/skills")
        async def list_skills():
            """获取可用技能列表"""
            if not self.skill_registry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="技能系统未初始化"
                )

            try:
                # 这里需要实际的技能列表获取逻辑
                # 暂时返回模拟技能列表
                return {
                    "skills": [
                        {"name": "nmap_scan", "description": "执行Nmap扫描"},
                        {"name": "sql_injection_test", "description": "SQL注入测试"},
                        {"name": "xss_detection", "description": "XSS漏洞检测"},
                    ],
                    "total": 3
                }
            except Exception as e:
                logger.error(f"获取技能列表失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"获取技能列表失败: {str(e)}"
                )

    def _initialize(self) -> None:
        """初始化AI引擎模块"""
        logger.info(f"正在初始化AI引擎模块: {self.name}")

        # 初始化LLM集成器
        try:
            from src.ai_engine.llm_agent.integrations import get_integrator
            self.llm_integrator = get_integrator()
            logger.info("LLM集成器初始化成功")
        except ImportError as e:
            logger.warning(f"无法导入LLM集成器: {e}")
            self.llm_integrator = None

        # 初始化配置管理器
        try:
            from src.ai_engine.llm_agent.config_manager import LLMConfigManager
            self.config_manager = LLMConfigManager()
            logger.info("配置管理器初始化成功")
        except ImportError as e:
            logger.warning(f"无法导入配置管理器: {e}")
            self.config_manager = None

        # 初始化技能注册表
        try:
            from src.shared.backend.skills.skill_registry import SkillRegistry
            self.skill_registry = SkillRegistry()
            logger.info("技能注册表初始化成功")
        except ImportError as e:
            logger.warning(f"无法导入技能注册表: {e}")
            self.skill_registry = None

        logger.info(f"AI引擎模块 {self.name} 初始化完成")

    def _cleanup(self) -> None:
        """清理AI引擎模块资源"""
        logger.info(f"正在清理AI引擎模块: {self.name}")

        if self.llm_integrator:
            try:
                self.llm_integrator.cleanup()
            except Exception as e:
                logger.error(f"清理LLM集成器失败: {e}")

        logger.info(f"AI引擎模块 {self.name} 清理完成")


# 模块工厂函数
def create_module(config: ModuleConfig) -> AIModule:
    """创建AI引擎模块实例"""
    return AIModule(config)