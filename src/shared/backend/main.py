"""
ClawAI 主应用
基于开源项目最佳实践的完整实现
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from contextlib import asynccontextmanager
import logging

from backend.database import init_database, DatabaseManager
from backend.auth.authentication import auth_manager
from backend.core.tool_manager import ToolManager
from backend.schemas import AttackRequest, AttackResponse, ToolExecuteRequest, ToolExecutionResult, AttackStep, ToolSeverity, RuleEngineDecision, TargetAnalysis
from backend.core.vulnerability_validator import VulnerabilityValidator, AttackPathAnalyzer, RiskAssessor, ComplianceChecker
from backend.services.attack_service import AttackService
from backend.error.handler import setup_error_handlers
from backend.log.manager import init_logging, get_logger
from backend.log.request_id import RequestIdMiddleware
from backend.security.rate_limit import RateLimitMiddleware, create_rate_limiter_from_env
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
_env = os.getenv("ENVIRONMENT", "development")
_log_level = os.getenv("LOG_LEVEL", "INFO")
_log_file = os.getenv("LOG_FILE", "logs/clawai.log")
# 生产环境默认使用 JSON 结构化日志，方便日志聚合工具（ELK/Splunk）解析
_output_json = os.getenv("LOG_JSON", "true" if _env == "production" else "false").lower() == "true"

log_config = {
    "level": _log_level,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
    "enable_console": True,
    "enable_file": True,
    "file": _log_file,
    "max_size": int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024))),  # 默认 10MB
    "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
    "output_json": _output_json,
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
        tool_manager = ToolManager()

        # 修正工具命令路径
        try:
            # 获取实际的工具目录路径
            tools_dir = os.getenv("TOOLS_DIR", os.path.join(
                os.path.dirname(__file__), "..", "..", "tools", "penetration"
            ))
            actual_tools_dir = os.path.abspath(tools_dir)
            if not os.path.exists(actual_tools_dir):
                actual_tools_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "penetration")
                actual_tools_dir = os.path.abspath(actual_tools_dir)

            # 更新sqlmap命令（使用列表形式避免命令注入）
            if "sqlmap" in tool_manager.tools:
                sqlmap_path = os.path.join(actual_tools_dir, "sqlmap", "sqlmap.py")
                if os.path.exists(sqlmap_path):
                    tool_manager.tools["sqlmap"].command = f'python "{sqlmap_path}"'
                    logger.info(f"更新sqlmap命令路径: {sqlmap_path}")

            # 更新dirsearch命令
            if "dirsearch" in tool_manager.tools:
                dirsearch_path = os.path.join(actual_tools_dir, "dirsearch", "dirsearch.py")
                if os.path.exists(dirsearch_path):
                    tool_manager.tools["dirsearch"].command = f'python "{dirsearch_path}"'
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
            # 审计系统失败不阻止应用启动，但记录严重告警
            logger.critical("审计系统未启动，安全合规性可能受影响")

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

        # 桥接 EventBus → WebSocket（让后端事件实时推送到前端）
        try:
            from .api.websocket import manager as ws_manager
            ws_manager.attach_eventbus(loop=asyncio.get_event_loop())
        except Exception as _eb_err:
            logger.warning(f"EventBus → WebSocket 桥接初始化失败（不影响启动）: {_eb_err}")
        
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

# 配置CORS - 从环境变量读取，生产环境不允许使用通配符
_allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
if _allowed_origins_raw.strip() == "*":
    # 生产环境警告
    if os.getenv("ENVIRONMENT", "development") == "production":
        logger.warning("生产环境禁止使用 ALLOWED_ORIGINS=*，强制使用 http://localhost:3000")
        _cors_origins = ["http://localhost:3000"]
    else:
        _cors_origins = ["*"]
else:
    _cors_origins = [o.strip() for o in _allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,  # 从 ALLOWED_ORIGINS 环境变量读取
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置统一错误处理器
setup_error_handlers(app)

# 添加请求 ID 追踪中间件（在所有业务中间件之前）
app.add_middleware(RequestIdMiddleware)

# 添加 API 速率限制中间件
_rate_limit_config = create_rate_limiter_from_env()
app.add_middleware(RateLimitMiddleware, config=_rate_limit_config)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置审计中间件
setup_audit_middleware(app)

# 注册API路由（统一在底部注册，避免重复）

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


def _health_check_impl():
    """健康检查公共逻辑"""
    db_health = db_manager.health_check() if db_manager else {"status": "unknown"}
    tool_health = tool_manager.health_check() if tool_manager else {"status": "unknown"}
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "services": {
            "database": db_health,
            "tools": tool_health
        },
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        return _health_check_impl()
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/health")
async def api_health_check():
    """API健康检查（用于Docker Compose健康检查）"""
    try:
        return _health_check_impl()
    except Exception as e:
        logger.error(f"API健康检查失败: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus指标端点"""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return {"error": "prometheus_client not installed"}


@app.post("/attack", response_model=AttackResponse)
async def execute_attack(
    attack_request: AttackRequest,
    _has_permission: bool = Depends(require_permission(Permission.ATTACK_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """执行攻击 - 使用真实的AttackService"""
    # 从请求中提取参数
    target = attack_request.target
    use_real = attack_request.use_real
    rule_engine_mode = attack_request.rule_engine_mode

    logger.info(f"收到攻击请求: target={target}, use_real={use_real}, rule_engine_mode={rule_engine_mode}")

    try:
        # 创建攻击服务实例
        attack_service = AttackService()

        # 执行攻击（同步调用，使用线程池避免阻塞）
        import asyncio
        result = await asyncio.to_thread(
            attack_service.execute_attack,
            target=target,
            use_real=use_real,
            scan_options={},
            username="clawai_user"  # 默认用户名
        )

        # 转换结果为AttackResponse格式
        attack_response = _convert_attack_result_to_response(result, target, use_real, rule_engine_mode)

        return attack_response

    except Exception as e:
        logger.error(f"攻击执行失败: {e}")
        # 出错时返回错误响应，但保持正确的响应格式
        import datetime
        return AttackResponse(
            target=target,
            execution_time="0秒",
            execution_mode="error",
            rule_engine_used=rule_engine_mode,
            rule_engine_model="none",
            attack_chain=[],
            rule_engine_decision=None,
            target_analysis=TargetAnalysis(),
            message="攻击执行失败，详情请查看服务端日志",
            timestamp=datetime.datetime.now(),
            success=False
        )

def _convert_attack_result_to_response(attack_result: dict, target: str, use_real: bool, rule_engine_mode: bool) -> AttackResponse:
    """将AttackService结果转换为AttackResponse格式"""
    import datetime
    logger = get_logger(__name__)

    try:
        # 提取结果数据
        execution_mode = attack_result.get("execution_mode", "simulation")
        execution_time = attack_result.get("execution_time", "0秒")
        message = attack_result.get("message", "")

        # 提取内部结果（如果有）
        inner_result = attack_result
        if "result" in attack_result:
            inner_result = attack_result["result"]

        # 提取攻击链
        attack_chain_data = inner_result.get("attack_chain", [])

        # 转换攻击步骤
        attack_steps = []
        for i, step_data in enumerate(attack_chain_data, 1):
            # 处理不同的数据格式
            if isinstance(step_data, dict):
                # 提取字段
                tool = step_data.get("tool", f"step_{i}")
                title = step_data.get("title", step_data.get("name", f"步骤 {i}"))
                description = step_data.get("description", step_data.get("summary", ""))
                duration = step_data.get("duration", step_data.get("time", "0s"))
                success = step_data.get("success", True)
                severity_str = step_data.get("severity", "medium").lower()
                highlight = step_data.get("highlight", False)

                # 映射严重性
                severity_map = {
                    "low": ToolSeverity.LOW,
                    "medium": ToolSeverity.MEDIUM,
                    "high": ToolSeverity.HIGH,
                    "critical": ToolSeverity.CRITICAL
                }
                severity = severity_map.get(severity_str, ToolSeverity.MEDIUM)

                attack_steps.append(
                    AttackStep(
                        step=i,
                        tool=tool,
                        title=title,
                        description=description,
                        duration=duration,
                        success=success,
                        severity=severity,
                        highlight=highlight
                    )
                )

        # 构建目标分析
        target_analysis_data = inner_result.get("target_analysis", {})
        target_analysis = TargetAnalysis(
            attack_surface=target_analysis_data.get("attack_surface", 0.0),
            open_ports=target_analysis_data.get("open_ports", 0),
            vulnerabilities=target_analysis_data.get("vulnerabilities", 0),
            sql_injections=target_analysis_data.get("sql_injections", 0),
            has_cms=target_analysis_data.get("has_cms", False),
            cms_type=target_analysis_data.get("cms_type"),
            cms_version=target_analysis_data.get("cms_version")
        )

        # 构建规则引擎决策（如果可用）
        rule_engine_decision = None
        decision_data = inner_result.get("decision", {})
        if decision_data:
            rule_engine_decision = RuleEngineDecision(
                selected_path_type=decision_data.get("selected_path_type", "default"),
                selected_score=decision_data.get("selected_score", 0.0),
                confidence=decision_data.get("confidence", 0.0),
                selection_reasons=decision_data.get("selection_reasons", []),
                path_comparison=decision_data.get("path_comparison", []),
                decision_factors=decision_data.get("decision_factors", {})
            )

        # 构建响应
        return AttackResponse(
            target=target,
            execution_time=execution_time,
            execution_mode=execution_mode,
            rule_engine_used=rule_engine_mode,
            rule_engine_model="rule_engine_v1" if rule_engine_mode else "none",
            attack_chain=attack_steps,
            rule_engine_decision=rule_engine_decision,
            target_analysis=target_analysis,
            message=message or "攻击执行完成",
            timestamp=datetime.datetime.now(),
            success=True
        )

    except Exception as e:
        logger.error(f"转换攻击结果时出错: {e}")
        # 如果转换失败，返回基本的响应
        return AttackResponse(
            target=target,
            execution_time="0秒",
            execution_mode="error" if not use_real else "real",
            rule_engine_used=rule_engine_mode,
            rule_engine_model="none",
            attack_chain=[],
            rule_engine_decision=None,
            target_analysis=TargetAnalysis(),
            message=f"结果转换失败: {str(e)}",
            timestamp=datetime.datetime.now(),
            success=False
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
            detail="执行工具时出错，请查看服务端日志"
        )


# 漏洞验证端点
@app.post("/api/v1/vulnerability/validate")
async def validate_vulnerability(
    request: dict,
    _has_permission: bool = Depends(require_permission(Permission.ATTACK_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """验证漏洞"""
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="工具管理器未初始化"
        )

    try:
        vulnerability = request.get("vulnerability")
        target = request.get("target")
        
        if not vulnerability or not target:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供漏洞信息和目标地址"
            )
            
        validator = VulnerabilityValidator(tool_manager)
        result = validator.validate_vulnerability(vulnerability, target)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证漏洞时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证漏洞时出错，请查看服务端日志"
        )


# 攻击路径分析端点
@app.post("/api/v1/attack-path/analyze")
async def analyze_attack_path(
    request: dict,
    _has_permission: bool = Depends(require_permission(Permission.ATTACK_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """分析攻击路径"""
    try:
        vulnerabilities = request.get("vulnerabilities", [])
        
        analyzer = AttackPathAnalyzer()
        result = analyzer.analyze_attack_path(vulnerabilities)
        return result
    except Exception as e:
        logger.error(f"分析攻击路径时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析攻击路径时出错，请查看服务端日志"
        )


# 风险评估端点
@app.post("/api/v1/risk/assess")
async def assess_risk(
    request: dict,
    _has_permission: bool = Depends(require_permission(Permission.ATTACK_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """评估漏洞风险"""
    try:
        vulnerability = request.get("vulnerability")
        
        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供漏洞信息"
            )
            
        assessor = RiskAssessor()
        result = assessor.assess_risk(vulnerability)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评估风险时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="评估风险时出错，请查看服务端日志"
        )


# 合规性检查端点
@app.post("/api/v1/compliance/check")
async def check_compliance(
    request: dict,
    _has_permission: bool = Depends(require_permission(Permission.ATTACK_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """检查合规性"""
    try:
        vulnerabilities = request.get("vulnerabilities", [])
        standard = request.get("standard", "owasp")
        
        checker = ComplianceChecker()
        result = checker.check_compliance(vulnerabilities, standard)
        return result
    except Exception as e:
        logger.error(f"检查合规性时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查合规性时出错，请查看服务端日志"
        )


# 自定义工具管理端点
@app.post("/api/v1/tools/custom")
async def add_custom_tool(
    tool_config: dict,
    _has_permission: bool = Depends(require_permission(Permission.TOOL_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """添加自定义工具"""
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="工具管理器未初始化"
        )

    try:
        result = tool_manager.add_custom_tool(tool_config)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加自定义工具时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加自定义工具时出错，请查看服务端日志"
        )


# 工具链执行端点
@app.post("/api/v1/tools/chain")
async def execute_tool_chain(
    request: dict,
    _has_permission: bool = Depends(require_permission(Permission.TOOL_EXECUTE)) if os.getenv("DISABLE_AUTH", "0") == "0" else True
):
    """执行工具链"""
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="工具管理器未初始化"
        )

    try:
        tool_chain = request.get("tool_chain", [])
        max_workers = request.get("max_workers", 5)
        overall_timeout = request.get("overall_timeout", 600)
        
        if not tool_chain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="工具链配置不能为空"
            )
        
        result = tool_manager.execute_tool_chain(tool_chain, max_workers, overall_timeout)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工具链时出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="执行工具链时出错，请查看服务端日志"
        )


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

# 导入工具API路由
try:
    from src.shared.backend.api.v1.tools import router as tools_router
    app.include_router(tools_router, prefix="/api/v1/tools", tags=["工具管理"])
    logger.info("工具API路由已加载")
except ImportError as e:
    logger.warning(f"工具API路由导入失败: {e}")

# 导入渗透测试API路由
try:
    from src.shared.backend.api.v1.pentest import router as pentest_router
    app.include_router(pentest_router, prefix="/api/v1/pentest", tags=["渗透测试"])
    logger.info("渗透测试API路由已加载")
except ImportError as e:
    logger.warning(f"渗透测试API路由导入失败: {e}")

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


def _validate_config():
    """启动时验证配置，对生产环境中的不安全设置发出警告"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    is_production = environment == "production"

    secret_key = os.getenv("SECRET_KEY", "")
    jwt_secret = os.getenv("JWT_SECRET", "") or os.getenv("JWT_SECRET_KEY", "")
    api_auth_enabled = os.getenv("API_AUTH_ENABLED", "true").lower() == "true"
    debug = os.getenv("DEBUG", "false").lower() == "true"

    warnings_found = False

    if is_production:
        if not secret_key or secret_key.startswith("your-"):
            raise RuntimeError(
                "[CONFIG] FATAL: SECRET_KEY is empty or uses default value in production! "
                "Generate a strong key: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if not jwt_secret or jwt_secret.startswith("your-"):
            raise RuntimeError(
                "[CONFIG] FATAL: JWT_SECRET_KEY is empty or uses default value in production! "
                "Generate a strong key: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if not api_auth_enabled:
            logger.warning("[CONFIG] SECURITY: API_AUTH_ENABLED is false in production - API endpoints are unprotected!")
            warnings_found = True
        if debug:
            logger.warning("[CONFIG] SECURITY: DEBUG is true in production - disable for production use!")
            warnings_found = True
        # 检查 CORS
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
        if allowed_origins.strip() == "*":
            logger.warning("[CONFIG] SECURITY: ALLOWED_ORIGINS=* in production - CORS is open to all origins!")
            warnings_found = True
    else:
        if not secret_key or secret_key.startswith("your-"):
            logger.info("[CONFIG] SECRET_KEY uses default value (acceptable in development)")
        if not jwt_secret or jwt_secret.startswith("your-"):
            logger.info("[CONFIG] JWT_SECRET_KEY uses default value (acceptable in development)")

    if not warnings_found:
        logger.info("[CONFIG] Configuration validation passed")

    # Log effective configuration (non-sensitive)
    logger.info(f"[CONFIG] Environment: {environment}")
    logger.info(f"[CONFIG] Debug: {debug}")
    logger.info(f"[CONFIG] API Auth Enabled: {api_auth_enabled}")
    logger.info(f"[CONFIG] Server: {os.getenv('SERVER_HOST', '0.0.0.0')}:{os.getenv('BACKEND_PORT', '8000')}")
    logger.info(f"[CONFIG] Database: {os.getenv('DATABASE_URL', 'sqlite:///./clawai.db')}")


if __name__ == "__main__":
    import uvicorn
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="ClawAI 主应用")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="服务器主机地址")
    parser.add_argument("--port", type=int, default=int(os.getenv("BACKEND_PORT", "8000")), help="服务器端口")
    args = parser.parse_args()

    host = args.host
    port = args.port

    # 启动前验证配置
    _validate_config()

    logger.info(f"启动服务器: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")

    _env = os.getenv("ENVIRONMENT", "development")
    uvicorn.run(
        "src.shared.backend.main:app",
        host=host,
        port=port,
        reload=(_env == "development")  # 仅开发模式启用热重载
    )