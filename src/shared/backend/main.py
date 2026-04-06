"""
ClawAI 主应用
基于开源项目最佳实践的完整实现
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from backend.database import init_database, DatabaseManager
from backend.auth.authentication import auth_manager
from backend.core.tool_manager import ToolManager
from backend.schemas import AttackRequest, AttackResponse, ToolExecuteRequest, ToolExecutionResult
from backend.error.handler import setup_error_handlers
from backend.log.manager import init_logging, get_logger
from backend.audit import init_audit_system, setup_audit_middleware
from backend.auth.rbac import Permission, rbac_manager
from backend.auth.fastapi_permissions import require_permission, require_authentication, get_current_user

# 模块系统
try:
    from modules import ModuleManager, ModuleConfig
    MODULES_AVAILABLE = True
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"模块系统导入失败: {e}")
    MODULES_AVAILABLE = False

# 初始化统一日志系统
log_config = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "enable_console": True,
    "enable_file": True,
    "file": "logs/clawai.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "output_json": False,
}

# 初始化日志管理器
init_logging(log_config)
logger = get_logger(__name__)

# 全局变量
db_manager: DatabaseManager = None
tool_manager: ToolManager = None
module_manager = None  # 模块管理器
# RBAC管理器已经在backend.auth.rbac中初始化


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global db_manager, tool_manager, module_manager
    
    # 启动时
    logger.info("启动 ClawAI 应用...")
    
    try:
        # 初始化数据库
        database_url = os.getenv("DATABASE_URL", "sqlite:///./clawai.db")
        db_manager = init_database(database_url)
        
        # 创建数据库表
        if os.getenv("ENVIRONMENT", "development") == "development":
            db_manager.create_tables()
        
        # 初始化工具管理器
        tools_dir = os.getenv("TOOLS_DIR", "./tools")
        tool_manager = ToolManager(tools_dir)

        # 修正工具命令路径
        try:
            # 获取实际的工具目录路径（如果TOOLS_DIR是相对路径）
            actual_tools_dir = os.path.abspath(tools_dir)
            if not os.path.exists(actual_tools_dir):
                actual_tools_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "penetration")
                actual_tools_dir = os.path.abspath(actual_tools_dir)

            # 更新sqlmap命令
            if "sqlmap" in tool_manager.tools:
                sqlmap_path = os.path.join(actual_tools_dir, "sqlmap", "sqlmap.py")
                if os.path.exists(sqlmap_path):
                    tool_manager.tools["sqlmap"].command = f'python {sqlmap_path}'
                    logger.info(f"更新sqlmap命令路径: {sqlmap_path}")

            # 更新dirsearch命令
            if "dirsearch" in tool_manager.tools:
                dirsearch_path = os.path.join(actual_tools_dir, "dirsearch", "dirsearch.py")
                if os.path.exists(dirsearch_path):
                    tool_manager.tools["dirsearch"].command = f'python {dirsearch_path}'
                    logger.info(f"更新dirsearch命令路径: {dirsearch_path}")

            # 更新其他工具命令（如果有特定路径需求）
            for tool_name in ["nikto", "nmap"]:
                if tool_name in tool_manager.tools:
                    # 这些工具通常在PATH中，保持原样
                    pass

        except Exception as e:
            logger.warning(f"修正工具路径时出错（不影响启动）: {e}")

        # 初始化审计系统
        try:
            audit_storage_dir = os.getenv("AUDIT_STORAGE_DIR", "logs/audit")
            audit_manager = init_audit_system()
            logger.info(f"审计系统初始化完成，存储目录: {audit_storage_dir}")
        except Exception as e:
            logger.error(f"审计系统初始化失败: {e}")
            # 审计系统失败不应阻止应用启动
            raise  # 但为了安全，暂时抛出异常

        # 初始化模块系统
        logger.info(f"模块系统可用性: {MODULES_AVAILABLE}")
        if MODULES_AVAILABLE:
            try:
                import yaml
                from pathlib import Path

                # 加载模块配置
                modules_config_path = os.getenv("MODULES_CONFIG_PATH", "config/modules.yaml")
                modules_config_file = Path(modules_config_path)

                if modules_config_file.exists():
                    with open(modules_config_file, 'r', encoding='utf-8') as f:
                        modules_config = yaml.safe_load(f)
                else:
                    logger.warning(f"模块配置文件不存在，使用默认配置: {modules_config_path}")
                    modules_config = {
                        "modules": {
                            "ai_engine": {"enabled": True, "config": {}, "dependencies": []},
                            "data_service": {"enabled": True, "config": {}, "dependencies": []},
                            "tool_executor": {"enabled": True, "config": {}, "dependencies": []}
                        },
                        "routing": {
                            "prefixes": {
                                "ai_engine": "/api/v1/ai",
                                "data_service": "/api/v1/data",
                                "tool_executor": "/api/v1/tools"
                            }
                        }
                    }

                # 获取路由前缀配置
                routing_config = modules_config.get("routing", {})
                prefixes = routing_config.get("prefixes", {})

                # 创建模块管理器，传入前缀配置
                module_manager = ModuleManager(app, prefixes=prefixes)

                # 动态导入和注册模块
                module_registry = {}
                for module_name, module_info in modules_config.get("modules", {}).items():
                    if not module_info.get("enabled", True):
                        logger.info(f"模块 {module_name} 已禁用，跳过")
                        continue

                    try:
                        # 动态导入模块
                        module_import_path = f"modules.{module_name}"
                        module = __import__(module_import_path, fromlist=['create_module'])

                        # 创建模块配置
                        module_config = ModuleConfig(
                            name=module_name,
                            enabled=module_info.get("enabled", True),
                            dependencies=module_info.get("dependencies", []),
                            config=module_info.get("config", {})
                        )

                        # 创建模块实例
                        module_instance = module.create_module(module_config)

                        # 注册模块
                        module_registry[module_name] = module_instance
                        logger.info(f"模块 {module_name} 加载成功")

                    except ImportError as e:
                        logger.error(f"导入模块 {module_name} 失败: {e}")
                    except Exception as e:
                        logger.error(f"创建模块 {module_name} 失败: {e}")

                # 批量注册模块并初始化
                if module_registry:
                    module_manager.register_modules(module_registry)
                    module_manager.initialize_all()
                    logger.info(f"模块系统初始化完成，加载了 {len(module_registry)} 个模块")
                else:
                    logger.warning("没有模块可加载")

            except Exception as e:
                logger.error(f"模块系统初始化失败: {e}")
                # 模块系统失败不应阻止应用启动
                module_manager = None
        else:
            logger.warning("模块系统不可用，跳过模块初始化")

        # 初始化RBAC系统并加载配置
        try:
            rbac_config_path = os.getenv("RBAC_CONFIG_PATH", "config/rbac.json")
            if os.path.exists(rbac_config_path):
                if rbac_manager.load_from_file(rbac_config_path):
                    logger.info(f"RBAC配置已从文件加载: {rbac_config_path}")
                else:
                    logger.warning(f"RBAC配置文件加载失败，使用默认配置: {rbac_config_path}")
                    # 初始化默认角色分配
                    rbac_manager.initialize_default_assignments()
            else:
                logger.info(f"RBAC配置文件不存在，使用默认配置: {rbac_config_path}")
                # 初始化默认角色分配
                rbac_manager.initialize_default_assignments()

                # 尝试保存默认配置到文件
                try:
                    os.makedirs(os.path.dirname(rbac_config_path), exist_ok=True)
                    if rbac_manager.save_to_file(rbac_config_path):
                        logger.info(f"默认RBAC配置已保存到文件: {rbac_config_path}")
                    else:
                        logger.warning(f"保存RBAC配置文件失败: {rbac_config_path}")
                except Exception as save_error:
                    logger.warning(f"保存RBAC配置文件时出错: {save_error}")
        except Exception as e:
            logger.error(f"RBAC系统初始化失败: {e}")
            # RBAC失败不应阻止应用启动，但会降低安全性
            # 继续使用内存中的默认配置

        logger.info("应用初始化完成")
        
        yield
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    
    finally:
        # 关闭时
        logger.info("关闭 ClawAI 应用...")

        # 保存RBAC配置
        try:
            rbac_config_path = os.getenv("RBAC_CONFIG_PATH", "config/rbac.json")
            if rbac_manager.save_to_file(rbac_config_path):
                logger.info(f"RBAC配置已保存到文件: {rbac_config_path}")
            else:
                logger.warning(f"保存RBAC配置文件失败: {rbac_config_path}")
        except Exception as e:
            logger.error(f"保存RBAC配置时出错: {e}")

        # 关闭模块系统
        if module_manager:
            try:
                module_manager.shutdown_all()
                logger.info("模块系统已关闭")
            except Exception as e:
                logger.error(f"关闭模块系统时出错: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="ClawAI - 智能安全评估系统",
    description="基于AI的自动化渗透测试平台，借鉴开源项目最佳实践",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置统一错误处理器
setup_error_handlers(app)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置审计中间件
setup_audit_middleware(app)


# 基础健康检查
@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "ClawAI",
        "version": "2.0.0",
        "description": "智能安全评估系统",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库
        db_health = db_manager.health_check() if db_manager else {"status": "unknown"}
        
        # 检查工具管理器
        tool_health = tool_manager.health_check() if tool_manager else {"status": "unknown"}
        
        return {
            "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
            "services": {
                "database": db_health,
                "tools": tool_health
            },
            "version": "2.0.0"
        }
    
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/tools")
async def get_tools(
    _has_permission: bool = Depends(require_permission(Permission.TOOL_READ))
):
    """获取可用工具列表"""
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="工具管理器未初始化"
        )
    
    tools = tool_manager.get_available_tools()
    categories = tool_manager.get_tool_categories()
    
    return {
        "tools": tools,
        "categories": categories,
        "count": len(tools)
    }


@app.get("/tools/health")
async def get_tools_health(
    _has_permission: bool = Depends(require_permission(Permission.TOOL_READ))
):
    """获取工具健康状态"""
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="工具管理器未初始化"
        )

    return tool_manager.health_check()


@app.post("/attack", response_model=AttackResponse)
async def execute_attack(
    attack_request: AttackRequest,
    _has_permission: bool = Depends(require_permission(Permission.ATTACK_EXECUTE))
):
    """执行攻击（模拟端点，供前端集成使用）"""
    # 从请求中提取参数
    target = attack_request.target
    use_real = attack_request.use_real
    rule_engine_mode = attack_request.rule_engine_mode

    logger.info(f"收到攻击请求: target={target}, use_real={use_real}, rule_engine_mode={rule_engine_mode}")

    # 模拟响应数据，匹配前端期望的格式
    import datetime

    mock_attack_chain = [
        {
            "step": 1,
            "tool": "nmap",
            "title": "网络侦察",
            "description": f"发现目标 {target} 的80, 443, 3306端口开放",
            "duration": "2.3s",
            "success": True,
            "severity": "low",
            "highlight": False
        },
        {
            "step": 2,
            "tool": "whatweb",
            "title": "指纹识别",
            "description": "识别为 WordPress 5.8 + PHP 7.4 + Apache 2.4",
            "duration": "1.8s",
            "success": True,
            "severity": "medium",
            "highlight": False
        },
        {
            "step": 3,
            "tool": "nuclei",
            "title": "漏洞扫描",
            "description": "发现 WordPress RCE 漏洞 (CVE-2023-1234)",
            "duration": "4.2s",
            "success": True,
            "severity": "critical",
            "highlight": True
        },
        {
            "step": 4,
            "tool": "exploit",
            "title": "漏洞利用",
            "description": "成功执行远程代码，获取 WebShell 访问权限",
            "duration": "3.5s",
            "success": True,
            "severity": "critical",
            "highlight": True
        },
        {
            "step": 5,
            "tool": "post",
            "title": "后渗透",
            "description": "建立持久化后门，进行横向移动和数据收集",
            "duration": "6.1s",
            "success": True,
            "severity": "high",
            "highlight": False
        }
    ]

    # 构建Pydantic响应对象
    from backend.schemas import AttackStep, ToolSeverity, RuleEngineDecision, TargetAnalysis

    # 转换攻击步骤
    attack_steps = []
    for i, step_data in enumerate(mock_attack_chain, 1):
        severity_map = {
            "low": ToolSeverity.LOW,
            "medium": ToolSeverity.MEDIUM,
            "high": ToolSeverity.HIGH,
            "critical": ToolSeverity.CRITICAL
        }
        attack_steps.append(
            AttackStep(
                step=step_data["step"],
                tool=step_data["tool"],
                title=step_data["title"],
                description=step_data["description"],
                duration=step_data["duration"],
                success=step_data["success"],
                severity=severity_map.get(step_data["severity"], ToolSeverity.MEDIUM),
                highlight=step_data.get("highlight", False)
            )
        )

    # 构建规则引擎决策
    rule_engine_decision = RuleEngineDecision(
        selected_path_type="rce_attack",
        selected_score=8.5,
        confidence=0.92,
        selection_reasons=[
            "规则引擎评分最高 (8.5分)",
            "漏洞严重性: critical",
            "攻击成功率: 85%",
            "可直接获取系统控制权",
            "攻击效果立竿见影"
        ],
        path_comparison=[
            {"path_type": "sql_injection", "score": 7.2, "score_difference": 1.3, "main_reason": "评分低1.3分"},
            {"path_type": "cms_exploit", "score": 6.8, "score_difference": 1.7, "main_reason": "评分低1.7分"}
        ],
        decision_factors={
            "exploitability": 9.2,
            "detection_risk": 2.1,
            "success_rate": 0.85,
            "time_efficiency": 7.8,
            "resource_cost": 6.5
        }
    )

    # 构建目标分析
    target_analysis = TargetAnalysis(
        attack_surface=7.8,
        open_ports=3,
        vulnerabilities=2,
        sql_injections=0,
        has_cms=True,
        cms_type="WordPress",
        cms_version="5.8"
    )

    # 返回AttackResponse对象
    return AttackResponse(
        target=target,
        execution_time="15.3秒",
        execution_mode="real" if use_real else "simulation",
        rule_engine_used=rule_engine_mode,
        rule_engine_model="rule_engine_v1" if rule_engine_mode else "none",
        attack_chain=attack_steps,
        rule_engine_decision=rule_engine_decision,
        target_analysis=target_analysis,
        message="攻击执行成功（模拟数据）",
        timestamp=datetime.datetime.now()
    )


@app.post("/tools/execute", response_model=ToolExecutionResult)
async def execute_tool(
    request: ToolExecuteRequest,
    _has_permission: bool = Depends(require_permission(Permission.TOOL_EXECUTE))
):
    """执行单个工具（真实执行）"""
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="工具管理器未初始化"
        )

    tool_name = request.tool
    target = request.target
    parameters = request.parameters

    if not tool_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供工具名称"
        )

    if not target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供目标地址"
        )

    try:
        logger.info(f"执行工具请求: tool={tool_name}, target={target}, parameters={parameters}")

        # 执行工具
        result = tool_manager.execute_tool(tool_name, target, **parameters)

        # 记录执行结果
        if result.get("success"):
            logger.info(f"工具执行成功: {tool_name}, 目标: {target}")
        else:
            logger.warning(f"工具执行失败: {tool_name}, 错误: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"执行工具时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行工具时出错: {str(e)}"
        )


# 导入API路由
# 注意：这里需要根据实际的路由文件进行导入
# 暂时使用占位符

# 导入审计API路由
try:
    from backend.audit import audit_router
    # 审计路由已在setup_audit_middleware中注册，避免重复
    # app.include_router(audit_router, prefix="/audit", tags=["审计管理"])
    logger.info("审计API路由已加载")
except ImportError as e:
    logger.warning(f"审计API路由导入失败: {e}")

# 导入RBAC API路由
try:
    from backend.api.v1.rbac import router as rbac_router
    app.include_router(rbac_router, tags=["RBAC管理"])
    logger.info("RBAC API路由已加载")
except ImportError as e:
    logger.warning(f"RBAC API路由导入失败: {e}")

# 导入认证API路由
try:
    from backend.api.v1.auth_fastapi import router as auth_router
    app.include_router(auth_router, tags=["认证管理"])
    logger.info("认证API路由已加载")
except ImportError as e:
    logger.warning(f"认证API路由导入失败: {e}")

# 导入报告API路由
try:
    from backend.api.v1.reports_fastapi import router as reports_router
    app.include_router(reports_router, tags=["报告管理"])
    logger.info("报告API路由已加载")
except ImportError as e:
    logger.warning(f"报告API路由导入失败: {e}")

# 导入监控API路由
try:
    from backend.api.v1.monitor import router as monitor_router, handle_monitor_websocket
    app.include_router(monitor_router, tags=["实时监控"])
    logger.info("监控API路由已加载")

    # 注册WebSocket端点
    from fastapi import WebSocket
    @app.websocket("/ws/monitor")
    async def websocket_monitor(websocket: WebSocket):
        await handle_monitor_websocket(websocket)

except ImportError as e:
    logger.warning(f"监控API路由导入失败: {e}")

# 导入插件管理API路由
try:
    from backend.api.v1.plugins import router as plugins_router
    app.include_router(plugins_router, tags=["插件管理"])
    logger.info("插件管理API路由已加载")
except ImportError as e:
    logger.warning(f"插件管理API路由导入失败: {e}")

# 导入技能库API路由
try:
    from backend.api.v1.skills import router as skills_router
    app.include_router(skills_router, tags=["技能库"])
    logger.info("技能库API路由已加载")
except ImportError as e:
    logger.warning(f"技能库API路由导入失败: {e}")

# 导入知识图谱API路由
try:
    from backend.api.knowledge_graph_fastapi import router as knowledge_graph_router
    app.include_router(knowledge_graph_router)
    logger.info("知识图谱API路由已加载（Neo4j集成版）")
except ImportError as e:
    logger.warning(f"知识图谱API路由导入失败: {e}")
    # 回退到内联定义（兼容性）
    from fastapi import APIRouter, HTTPException, Query
    from typing import Optional
    from datetime import datetime

    knowledge_graph_router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["知识图谱"])

    # 模拟知识图谱数据（简化版，回退方案）
    KNOWLEDGE_GRAPH_DATA = {
        "nodes": [
            {
                "id": "target-1",
                "label": "目标服务器",
                "type": "server",
                "properties": {"ip": "192.168.1.100", "os": "Linux", "status": "在线"},
                "position": {"x": 300, "y": 200},
                "color": "#3b82f6"
            }
        ],
        "edges": []
    }

    @knowledge_graph_router.get("/graph")
    async def get_knowledge_graph():
        return {
            "success": True,
            "data": KNOWLEDGE_GRAPH_DATA,
            "metadata": {
                "node_count": len(KNOWLEDGE_GRAPH_DATA["nodes"]),
                "edge_count": len(KNOWLEDGE_GRAPH_DATA["edges"]),
                "timestamp": datetime.now().isoformat()
            }
        }

    @knowledge_graph_router.get("/health")
    async def knowledge_graph_health():
        return {
            "status": "healthy",
            "service": "knowledge-graph-api",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }

    @knowledge_graph_router.get("/stats")
    async def get_graph_stats():
        return {
            "success": True,
            "data": {
                "total_nodes": len(KNOWLEDGE_GRAPH_DATA["nodes"]),
                "total_edges": len(KNOWLEDGE_GRAPH_DATA["edges"]),
                "node_types": ["server"],
                "timestamp": datetime.now().isoformat()
            }
        }

    app.include_router(knowledge_graph_router)
    logger.info("知识图谱API路由已加载（回退到模拟数据）")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"启动服务器: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True  # 开发模式
    )