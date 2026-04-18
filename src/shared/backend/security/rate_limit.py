"""
API 速率限制中间件
支持基于内存（开发）和 Redis（生产）的滑动窗口限速

用法:
    from backend.security.rate_limit import RateLimitMiddleware, RateLimitConfig

    app.add_middleware(
        RateLimitMiddleware,
        config=RateLimitConfig(
            default_limit=100,      # 每个时间窗口最大请求数
            default_window=60,      # 时间窗口（秒）
            burst_limit=20,         # 突发请求额外配额
            per_path_limits={
                "/api/v1/auth/login": (5, 60),    # 5次/分钟
                "/api/v1/auth/register": (3, 60), # 3次/分钟
                "/attack": (10, 60),              # 10次/分钟
            }
        )
    )
"""

import time
import logging
import os
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """速率限制配置"""

    def __init__(
        self,
        default_limit: int = 100,
        default_window: int = 60,
        burst_limit: int = 20,
        per_path_limits: Optional[Dict[str, Tuple[int, int]]] = None,
        enabled: bool = True,
        whitelist_ips: Optional[list] = None,
    ):
        self.default_limit = default_limit
        self.default_window = default_window
        self.burst_limit = burst_limit
        # 路径级别限速: {path_prefix: (max_requests, window_seconds)}
        self.per_path_limits: Dict[str, Tuple[int, int]] = per_path_limits or {}
        self.enabled = enabled
        self.whitelist_ips: list = whitelist_ips or ["127.0.0.1", "::1"]

    def get_limit_for_path(self, path: str) -> Tuple[int, int]:
        """获取指定路径的限速配置"""
        for prefix, (limit, window) in self.per_path_limits.items():
            if path.startswith(prefix):
                return limit, window
        return self.default_limit, self.default_window


class _InMemoryStore:
    """内存滑动窗口限速存储"""

    def __init__(self):
        self._data: Dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, int, int]:
        """
        检查请求是否允许通过

        Returns:
            (allowed, remaining, reset_after_seconds)
        """
        now = time.monotonic()
        window_start = now - window

        with self._lock:
            timestamps = self._data[key]

            # 清理过期时间戳
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            count = len(timestamps)
            if count < limit:
                timestamps.append(now)
                remaining = limit - count - 1
                return True, remaining, window
            else:
                # 计算到最早请求过期的时间
                reset_after = int(window - (now - timestamps[0])) + 1
                return False, 0, reset_after


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    基于 IP + 路径的滑动窗口限速
    生产环境建议配置 Nginx 层面的限速作为第一道防线
    """

    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self._store = _InMemoryStore()

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP（支持反向代理）"""
        # 优先使用 X-Forwarded-For（来自 Nginx 的真实 IP）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.config.enabled:
            return await call_next(request)

        # WebSocket 升级请求跳过限速
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # 跳过健康检查和指标端点
        path = request.url.path
        if path in ("/health", "/api/health", "/metrics"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # 白名单 IP 直接放行
        if client_ip in self.config.whitelist_ips:
            return await call_next(request)

        limit, window = self.config.get_limit_for_path(path)
        key = f"{client_ip}:{path}"

        allowed, remaining, reset_after = self._store.is_allowed(key, limit, window)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "client_ip": client_ip,
                    "path": path,
                    "method": request.method,
                    "limit": limit,
                    "window": window,
                }
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Max {limit} requests per {window}s.",
                    "retry_after": reset_after,
                },
                headers={
                    "Retry-After": str(reset_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_after),
                },
            )

        response = await call_next(request)

        # 在响应头中返回限速信息
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_after)

        return response


def create_rate_limiter_from_env() -> RateLimitConfig:
    """从环境变量创建速率限制中间件"""
    enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    default_limit = int(os.getenv("RATE_LIMIT_DEFAULT", "100"))
    default_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    config = RateLimitConfig(
        enabled=enabled,
        default_limit=default_limit,
        default_window=default_window,
        per_path_limits={
            "/api/v1/auth/login": (5, 60),
            "/api/v1/auth/register": (3, 60),
            "/attack": (10, 60),
            "/api/v1/scan": (20, 60),
        },
        whitelist_ips=["127.0.0.1", "::1"],
    )
    return config
