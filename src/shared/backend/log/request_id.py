"""
请求追踪中间件
为每个 HTTP 请求注入唯一的 request_id，支持请求级日志追踪
同时更新 Prometheus API 指标
"""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# 用于存储当前请求的 request_id（线程/协程安全）
try:
    from contextvars import ContextVar
    _request_id_var: ContextVar[str] = ContextVar("request_id", default="")
except ImportError:
    _request_id_var = None  # type: ignore

# 延迟导入 Prometheus 指标，避免循环依赖
_metrics_manager = None


def _get_metrics():
    """延迟获取 MetricsManager 实例"""
    global _metrics_manager
    if _metrics_manager is None:
        try:
            from ..observability.metrics import MetricsManager
            _metrics_manager = MetricsManager()
        except Exception:
            pass
    return _metrics_manager


def get_request_id() -> str:
    """获取当前请求的 request_id"""
    if _request_id_var is not None:
        return _request_id_var.get("")
    return ""


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    请求 ID 注入中间件

    - 如果请求头中含有 X-Request-ID，复用该值
    - 否则自动生成 UUID4
    - 将 request_id 写入响应头 X-Request-ID
    - 在日志中记录请求开始/结束及耗时
    - 同步更新 Prometheus 指标（如果可用）
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 优先复用客户端传入的 request_id（链路追踪场景）
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 设置到 ContextVar，便于业务代码中调用 get_request_id()
        token = None
        if _request_id_var is not None:
            token = _request_id_var.set(request_id)

        start_time = time.perf_counter()

        try:
            logger.info(
                "request_start",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else "unknown",
                }
            )

            response = await call_next(request)

            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = response.status_code

            logger.info(
                "request_end",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )

            # 更新 Prometheus 指标
            metrics = _get_metrics()
            if metrics:
                try:
                    endpoint = request.url.path
                    method = request.method
                    status = str(status_code)
                    duration_s = duration_ms / 1000.0

                    api_requests = metrics.get_metric("api_requests_total")
                    if api_requests:
                        api_requests.labels(
                            endpoint=endpoint, method=method, status=status
                        ).inc()

                    api_duration = metrics.get_metric("api_request_duration_seconds")
                    if api_duration:
                        api_duration.labels(
                            endpoint=endpoint, method=method
                        ).observe(duration_s)
                except Exception:
                    pass  # 指标更新失败不阻断请求

            # 将 request_id 写入响应头，便于客户端调试
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise

        finally:
            if _request_id_var is not None and token is not None:
                _request_id_var.reset(token)

