"""
模块化系统基类
提供模块基类和模块管理器，用于构建模块化单体应用
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ModuleConfig(BaseModel):
    """模块配置模型"""
    name: str
    enabled: bool = True
    dependencies: List[str] = []
    config: Dict[str, Any] = {}


class BaseModule(ABC):
    """模块基类，所有模块都必须继承此类"""

    def __init__(self, config: ModuleConfig):
        """
        初始化模块

        Args:
            config: 模块配置
        """
        self.config = config
        self.name = config.name
        self.router = APIRouter()
        self._setup_complete = False
        self._dependencies_met = False

        # 设置模块特定的路由
        self._setup_routes()

    @abstractmethod
    def _setup_routes(self) -> None:
        """
        设置模块路由
        子类必须实现此方法，用于定义模块的API端点
        """
        pass

    def setup(self, dependencies: Dict[str, 'BaseModule'] = None) -> None:
        """
        初始化模块

        Args:
            dependencies: 依赖的模块字典 {module_name: module_instance}
        """
        if self._setup_complete:
            logger.warning(f"模块 {self.name} 已经初始化过")
            return

        logger.info(f"正在初始化模块: {self.name}")

        # 检查依赖是否满足
        if dependencies:
            missing_deps = [
                dep for dep in self.config.dependencies
                if dep not in dependencies
            ]
            if missing_deps:
                raise RuntimeError(
                    f"模块 {self.name} 缺少依赖: {missing_deps}"
                )

            # 保存依赖引用
            self.dependencies = dependencies
            self._dependencies_met = True

        try:
            # 执行模块特定的初始化
            self._initialize()
            self._setup_complete = True
            logger.info(f"模块 {self.name} 初始化完成")
        except Exception as e:
            logger.error(f"模块 {self.name} 初始化失败: {e}")
            raise

    def _initialize(self) -> None:
        """
        模块初始化逻辑
        子类可以覆盖此方法实现自定义初始化
        """
        pass

    def shutdown(self) -> None:
        """
        关闭模块，清理资源
        """
        if not self._setup_complete:
            return

        logger.info(f"正在关闭模块: {self.name}")
        try:
            self._cleanup()
            self._setup_complete = False
            logger.info(f"模块 {self.name} 已关闭")
        except Exception as e:
            logger.error(f"模块 {self.name} 关闭失败: {e}")
            raise

    def _cleanup(self) -> None:
        """
        模块清理逻辑
        子类可以覆盖此方法实现自定义清理
        """
        pass

    def get_router(self) -> APIRouter:
        """
        获取模块的路由器

        Returns:
            APIRouter: 模块的路由器
        """
        return self.router

    def health_check(self) -> Dict[str, Any]:
        """
        模块健康检查

        Returns:
            健康状态字典
        """
        return {
            "module": self.name,
            "status": "healthy" if self._setup_complete else "unhealthy",
            "dependencies_met": self._dependencies_met,
            "enabled": self.config.enabled,
        }

    def get_info(self) -> Dict[str, Any]:
        """
        获取模块信息

        Returns:
            模块信息字典
        """
        return {
            "name": self.name,
            "enabled": self.config.enabled,
            "dependencies": self.config.dependencies,
            "setup_complete": self._setup_complete,
            "dependencies_met": self._dependencies_met,
            "endpoints": self._get_endpoints_info(),
        }

    def _get_endpoints_info(self) -> List[Dict[str, Any]]:
        """
        获取模块端点信息

        Returns:
            端点信息列表
        """
        endpoints = []
        for route in self.router.routes:
            endpoint_info = {
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else [],
                "name": getattr(route, 'name', ''),
            }
            endpoints.append(endpoint_info)
        return endpoints


class ModuleManager:
    """模块管理器，管理所有模块的生命周期"""

    def __init__(self, app: FastAPI, prefixes: Optional[Dict[str, str]] = None):
        """
        初始化模块管理器

        Args:
            app: FastAPI应用实例
            prefixes: 模块路由前缀映射 {module_name: prefix}
        """
        self.app = app
        self.modules: Dict[str, BaseModule] = {}
        self.module_configs: Dict[str, ModuleConfig] = {}
        self.prefixes = prefixes or {}
        self._initialized = False

    def register_module(self, config: ModuleConfig, module_class: type) -> None:
        """
        注册模块

        Args:
            config: 模块配置
            module_class: 模块类（必须继承BaseModule）
        """
        if config.name in self.modules:
            raise ValueError(f"模块 {config.name} 已经注册")

        if not issubclass(module_class, BaseModule):
            raise TypeError(f"模块类必须继承自 BaseModule: {module_class}")

        # 创建模块实例
        module_instance = module_class(config)
        self.modules[config.name] = module_instance
        self.module_configs[config.name] = config

        logger.info(f"已注册模块: {config.name}")

    def register_modules(self, modules: Dict[str, BaseModule]) -> None:
        """
        批量注册模块实例

        Args:
            modules: 模块名称到模块实例的字典
        """
        for module_name, module_instance in modules.items():
            if module_name in self.modules:
                logger.warning(f"模块 {module_name} 已经注册，跳过")
                continue

            if not isinstance(module_instance, BaseModule):
                raise TypeError(f"模块实例必须继承自 BaseModule: {type(module_instance)}")

            # 从模块实例中提取配置
            config = ModuleConfig(
                name=module_name,
                enabled=module_instance.config.enabled,
                dependencies=module_instance.config.dependencies,
                config=module_instance.config.config
            )

            self.modules[module_name] = module_instance
            self.module_configs[module_name] = config
            logger.info(f"已批量注册模块: {module_name}")

    def setup_all(self) -> None:
        """
        初始化所有模块
        """
        if self._initialized:
            logger.warning("模块管理器已经初始化过")
            return

        logger.info("正在初始化所有模块")

        # 按依赖顺序排序模块
        sorted_modules = self._topological_sort()

        # 初始化模块
        initialized_modules = {}
        for module_name in sorted_modules:
            if module_name not in self.modules:
                continue

            module = self.modules[module_name]
            config = self.module_configs[module_name]

            if not config.enabled:
                logger.info(f"跳过禁用模块: {module_name}")
                continue

            # 收集依赖模块实例
            dependencies = {
                dep: initialized_modules[dep]
                for dep in config.dependencies
                if dep in initialized_modules
            }

            try:
                module.setup(dependencies)

                # 将模块路由器添加到主应用
                router = module.get_router()
                if router.routes:
                    # 使用配置的前缀，如果没有则使用默认
                    prefix = self.prefixes.get(module_name, f"/api/v1/{module_name}")
                    self.app.include_router(
                        router,
                        prefix=prefix,
                        tags=[module_name]
                    )

                initialized_modules[module_name] = module
                logger.info(f"模块 {module_name} 已添加到应用")
            except Exception as e:
                logger.error(f"模块 {module_name} 初始化失败: {e}")
                # 可以选择继续初始化其他模块或终止
                raise

        self._initialized = True
        logger.info(f"所有模块初始化完成，共 {len(initialized_modules)} 个模块")

    def initialize_all(self) -> None:
        """
        初始化所有模块（setup_all的别名，用于向后兼容）
        """
        self.setup_all()

    def _topological_sort(self) -> List[str]:
        """
        拓扑排序模块（考虑依赖关系）

        Returns:
            排序后的模块名称列表
        """
        # 构建依赖图
        graph = {name: set(config.dependencies)
                for name, config in self.module_configs.items()}

        # Kahn算法进行拓扑排序
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        # 找到入度为0的节点
        queue = [node for node in graph if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        # 检查是否有环
        if len(result) != len(graph):
            remaining = set(graph.keys()) - set(result)
            logger.warning(f"模块依赖图中可能存在环: {remaining}")
            # 将剩余的节点添加到结果末尾
            result.extend(list(remaining))

        return result

    def shutdown_all(self) -> None:
        """
        关闭所有模块
        """
        if not self._initialized:
            return

        logger.info("正在关闭所有模块")

        # 按依赖逆序关闭模块
        sorted_modules = self._topological_sort()
        sorted_modules.reverse()

        for module_name in sorted_modules:
            if module_name in self.modules:
                module = self.modules[module_name]
                try:
                    module.shutdown()
                except Exception as e:
                    logger.error(f"模块 {module_name} 关闭失败: {e}")

        self._initialized = False
        logger.info("所有模块已关闭")

    def get_module(self, name: str) -> Optional[BaseModule]:
        """
        获取模块实例

        Args:
            name: 模块名称

        Returns:
            模块实例，如果不存在则返回None
        """
        return self.modules.get(name)

    def get_all_modules_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有模块信息

        Returns:
            模块信息字典
        """
        return {
            name: module.get_info()
            for name, module in self.modules.items()
        }

    def health_check_all(self) -> Dict[str, Any]:
        """
        所有模块健康检查

        Returns:
            健康状态字典
        """
        health_status = {}
        all_healthy = True

        for name, module in self.modules.items():
            config = self.module_configs[name]
            if not config.enabled:
                continue

            module_health = module.health_check()
            health_status[name] = module_health

            if module_health["status"] != "healthy":
                all_healthy = False

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "modules": health_status,
            "total_modules": len(health_status),
            "healthy_modules": sum(1 for h in health_status.values()
                                  if h["status"] == "healthy"),
        }


# 导出常用类和函数
__all__ = [
    "ModuleConfig",
    "BaseModule",
    "ModuleManager",
]