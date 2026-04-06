"""
审计中间件
自动记录HTTP请求和响应的审计中间件
"""

import time
import uuid
from datetime import datetime
from typing import Optional, Callable
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..schemas import AuditActor, AuditResource, AuditEvent, AuditEventType, AuditEventSeverity, AuditEventStatus
from ..security.sensitive_data import get_sensitive_data_manager, redact_sensitive_data
from .manager import get_audit_manager


class AuditMiddleware(BaseHTTPMiddleware):
    """审计中间件，自动记录HTTP请求"""

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[list] = None,
        sensitive_headers: Optional[list] = None,
        max_body_size: int = 1024 * 10,  # 10KB
        log_successful_requests: bool = True,
        log_failed_requests: bool = True,
        log_sensitive_paths: bool = True
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static"
        ]
        self.sensitive_headers = sensitive_headers or [
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-access-token"
        ]
        self.max_body_size = max_body_size
        self.log_successful_requests = log_successful_requests
        self.log_failed_requests = log_failed_requests
        self.log_sensitive_paths = log_sensitive_paths

        # 敏感路径列表（这些路径的请求会被标记为敏感）
        self.sensitive_path_patterns = [
            "/auth/",
            "/login",
            "/logout",
            "/register",
            "/password",
            "/token",
            "/admin/",
            "/config/",
            "/users/",
            "/audit/",
            "/attack",
            "/tools/execute",
            "/scan/"
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        # 检查是否排除该路径
        if self._should_exclude(request.url.path):
            return await call_next(request)

        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 开始时间
        start_time = time.time()

        # 提取用户信息
        actor = await self._extract_actor(request)

        # 记录请求开始
        request_event = self._create_request_event(request, actor, request_id)
        audit_manager = get_audit_manager()
        audit_manager.log_event(request_event)

        try:
            # 处理请求
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            # 记录响应
            if self._should_log_response(response.status_code):
                response_event = self._create_response_event(
                    request, response, actor, request_id, duration_ms
                )
                audit_manager.log_event(response_event)

            return response

        except Exception as exc:
            # 记录异常
            duration_ms = int((time.time() - start_time) * 1000)
            error_event = self._create_error_event(
                request, exc, actor, request_id, duration_ms
            )
            audit_manager.log_event(error_event)
            raise

    def _should_exclude(self, path: str) -> bool:
        """检查是否应该排除该路径"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def _should_log_response(self, status_code: int) -> bool:
        """检查是否应该记录响应"""
        if status_code >= 400 and self.log_failed_requests:
            return True
        if status_code < 400 and self.log_successful_requests:
            return True
        return False

    async def _extract_actor(self, request: Request) -> AuditActor:
        """从请求中提取操作者信息"""
        # 尝试从请求中提取用户信息
        # TODO: 根据实际的认证系统调整
        user_id = None
        username = None
        role = None

        # 检查JWT令牌或其他认证信息
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 这里可以解码JWT令牌获取用户信息
            # 暂时使用占位符
            pass

        # 从session或cookie获取用户信息
        # ...

        return AuditActor(
            user_id=user_id,
            username=username or "anonymous",
            role=role or "guest",
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            session_id=request.cookies.get("session_id") or str(uuid.uuid4())
        )

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查X-Forwarded-For头部（如果通过代理）
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return x_forwarded_for.split(",")[0].strip()

        # 检查X-Real-IP头部
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip

        # 使用客户端地址
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    def _is_sensitive_path(self, path: str) -> bool:
        """检查是否为敏感路径"""
        for pattern in self.sensitive_path_patterns:
            if pattern in path:
                return True
        return False

    def _sanitize_headers(self, headers: dict) -> dict:
        """清理敏感头部信息"""
        sanitized = {}
        sensitive_data_manager = get_sensitive_data_manager()

        for key, value in headers.items():
            # 如果头部在敏感头部列表中，直接脱敏
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                # 否则，对头部值进行敏感信息检测和脱敏
                if isinstance(value, str):
                    # 脱敏字符串值中的敏感信息
                    sanitized_value = sensitive_data_manager.redact_text(
                        value,
                        f"audit.headers.{key}"
                    )
                    sanitized[key] = sanitized_value
                else:
                    # 非字符串值直接保留
                    sanitized[key] = value

        # 对整个头部字典进行深度脱敏（处理嵌套敏感信息）
        sanitized = sensitive_data_manager.redact_dict(
            sanitized,
            "audit.headers"
        )

        return sanitized

    async def _get_request_body(self, request: Request) -> Optional[str]:
        """获取请求体（限制大小并脱敏敏感信息）"""
        try:
            body = await request.body()
            if len(body) > self.max_body_size:
                return f"[TRUNCATED: {len(body)} bytes]"

            # 尝试解码为文本
            try:
                body_text = body.decode("utf-8")
                # 脱敏敏感信息
                sensitive_data_manager = get_sensitive_data_manager()
                redacted_body = sensitive_data_manager.redact_text(
                    body_text,
                    "audit.request.body"
                )
                return redacted_body
            except UnicodeDecodeError:
                # 二进制数据，无法脱敏
                return f"[BINARY: {len(body)} bytes]"

        except Exception:
            return None

    def _create_request_event(self, request: Request, actor: AuditActor, request_id: str) -> AuditEvent:
        """创建请求审计事件"""
        # 检查是否为敏感路径
        is_sensitive = self._is_sensitive_path(request.url.path)
        sensitive_data_manager = get_sensitive_data_manager()

        # 构建操作描述
        method = request.method
        path = request.url.path
        query = str(request.query_params)
        action = f"{method} {path}"
        if query and query != "":
            action += f"?{query}"

        # 构建事件详情
        details = {
            "method": method,
            "path": path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": actor.ip_address,
            "user_agent": actor.user_agent,
            "request_id": request_id
        }

        # 如果是敏感路径，添加请求体（如果可用）
        if is_sensitive:
            # 注意：这里在dispatch方法中会异步获取，简化处理
            details["body_available"] = True

        # 脱敏整个details字典中的敏感信息
        details = sensitive_data_manager.redact_dict(details, "audit.request.details")

        return AuditEvent(
            event_id=f"req_{request_id}",
            event_type=AuditEventType.SYSTEM_START,
            event_severity=AuditEventSeverity.INFO,
            event_status=AuditEventStatus.PENDING,
            actor=actor,
            resource=AuditResource(
                resource_type="http_request",
                resource_id=request_id,
                resource_path=path,
                resource_metadata={"method": method, "path": path}
            ),
            action=action,
            description=f"HTTP请求开始: {method} {path}",
            details=details,
            module="http",
            is_sensitive=is_sensitive,
            requires_review=is_sensitive,  # 敏感请求需要审核
            correlation_id=request_id
        )

    def _create_response_event(
        self,
        request: Request,
        response: Response,
        actor: AuditActor,
        request_id: str,
        duration_ms: int
    ) -> AuditEvent:
        """创建响应审计事件"""
        method = request.method
        path = request.url.path
        status_code = response.status_code
        sensitive_data_manager = get_sensitive_data_manager()

        # 确定事件状态和严重级别
        if status_code >= 400:
            event_status = AuditEventStatus.FAILURE
            event_severity = AuditEventSeverity.ERROR if status_code >= 500 else AuditEventSeverity.WARNING
        else:
            event_status = AuditEventStatus.SUCCESS
            event_severity = AuditEventSeverity.INFO

        # 检查是否为敏感路径
        is_sensitive = self._is_sensitive_path(path)

        # 构建操作描述
        action = f"{method} {path} -> {status_code}"

        # 构建事件详情
        details = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "headers": self._sanitize_headers(dict(response.headers)),
            "request_id": request_id
        }

        # 脱敏整个details字典中的敏感信息
        details = sensitive_data_manager.redact_dict(details, "audit.response.details")

        return AuditEvent(
            event_id=f"resp_{request_id}",
            event_type=AuditEventType.SYSTEM_STOP,
            event_severity=event_severity,
            event_status=event_status,
            actor=actor,
            resource=AuditResource(
                resource_type="http_response",
                resource_id=request_id,
                resource_path=path,
                resource_metadata={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms
                }
            ),
            action=action,
            description=f"HTTP请求完成: {method} {path} 状态码: {status_code} 耗时: {duration_ms}ms",
            details=details,
            module="http",
            is_sensitive=is_sensitive,
            requires_review=is_sensitive and status_code >= 400,  # 敏感路径的失败请求需要审核
            correlation_id=request_id,
            duration_ms=duration_ms
        )

    def _create_error_event(
        self,
        request: Request,
        exc: Exception,
        actor: AuditActor,
        request_id: str,
        duration_ms: int
    ) -> AuditEvent:
        """创建错误审计事件"""
        method = request.method
        path = request.url.path
        is_sensitive = self._is_sensitive_path(path)

        return AuditEvent(
            event_id=f"err_{request_id}",
            event_type=AuditEventType.SECURITY_INCIDENT,
            event_severity=AuditEventSeverity.ERROR,
            event_status=AuditEventStatus.FAILURE,
            actor=actor,
            resource=AuditResource(
                resource_type="http_error",
                resource_id=request_id,
                resource_path=path,
                resource_metadata={
                    "method": method,
                    "path": path,
                    "exception_type": type(exc).__name__
                }
            ),
            action=f"{method} {path} -> EXCEPTION",
            description=f"HTTP请求异常: {method} {path} 异常: {str(exc)}",
            details={
                "method": method,
                "path": path,
                "exception": str(exc),
                "exception_type": type(exc).__name__,
                "duration_ms": duration_ms,
                "request_id": request_id
            },
            module="http",
            is_sensitive=is_sensitive,
            requires_review=True,  # 所有异常都需要审核
            correlation_id=request_id,
            duration_ms=duration_ms
        )


def setup_audit_middleware(app: FastAPI):
    """设置审计中间件"""
    # 添加审计中间件
    app.add_middleware(
        AuditMiddleware,
        exclude_paths=[
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static"
        ]
    )

    # 添加审计API路由
    from .api import router as audit_router
    app.include_router(audit_router)

    # 添加请求ID到日志
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        # 确保有request_id
        if not hasattr(request.state, "request_id"):
            request.state.request_id = str(uuid.uuid4())
        return await call_next(request)

    return app