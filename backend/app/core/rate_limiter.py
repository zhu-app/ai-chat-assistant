"""
简易内存速率限制器 — 基于滑动窗口，无需外部依赖。
"""

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimiter:
    """基于滑动窗口的内存速率限制器。"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_key: str) -> bool:
        now = time.monotonic()
        window_start = now - self.window_seconds
        timestamps = self._clients[client_key]
        while timestamps and timestamps[0] < window_start:
            timestamps.pop(0)
        if len(timestamps) >= self.max_requests:
            return False
        timestamps.append(now)
        return True

    def cleanup(self) -> None:
        now = time.monotonic()
        window_start = now - self.window_seconds
        for key in list(self._clients.keys()):
            self._clients[key] = [t for t in self._clients[key] if t >= window_start]
            if not self._clients[key]:
                del self._clients[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 速率限制中间件。"""

    def __init__(
        self,
        app,
        global_limit: int | None = None,
        auth_limit: int | None = None,
        window: int = 60,
    ) -> None:
        super().__init__(app)
        global_limit = global_limit if global_limit is not None else settings.rate_limit_requests_per_minute
        auth_limit = auth_limit if auth_limit is not None else settings.auth_rate_limit_requests_per_minute
        self.global_limiter = RateLimiter(max_requests=global_limit, window_seconds=window)
        self.auth_limiter = RateLimiter(max_requests=auth_limit, window_seconds=window)
        self._last_cleanup = time.monotonic()

    def _cleanup_if_due(self) -> None:
        now = time.monotonic()
        if now - self._last_cleanup < self.global_limiter.window_seconds:
            return
        self.global_limiter.cleanup()
        self.auth_limiter.cleanup()
        self._last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        from fastapi.responses import JSONResponse

        # Docker deployment only exposes the backend through Nginx, which overwrites
        # X-Real-IP with the connecting client's address.
        client_ip = request.headers.get('x-real-ip') or (request.client.host if request.client else 'unknown')
        self._cleanup_if_due()

        # 认证接口更严格限制
        if request.url.path in ('/api/auth/login', '/api/auth/register', '/api/auth/guest'):
            if not self.auth_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={'detail': '请求过于频繁，请稍后再试'},
                    headers={'Retry-After': str(self.auth_limiter.window_seconds)},
                )
        elif request.url.path.startswith('/api/'):
            if not self.global_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={'detail': '请求过于频繁，请稍后再试'},
                    headers={'Retry-After': str(self.global_limiter.window_seconds)},
                )

        response = await call_next(request)
        return response
