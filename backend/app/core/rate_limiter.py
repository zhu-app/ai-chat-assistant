"""
简易内存速率限制器 — 基于滑动窗口，无需外部依赖。
"""

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


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

    def __init__(self, app, global_limit: int = 60, auth_limit: int = 10, window: int = 60) -> None:
        super().__init__(app)
        self.global_limiter = RateLimiter(max_requests=global_limit, window_seconds=window)
        self.auth_limiter = RateLimiter(max_requests=auth_limit, window_seconds=window)

    async def dispatch(self, request: Request, call_next):
        from fastapi.responses import JSONResponse

        client_ip = request.client.host if request.client else 'unknown'

        # 认证接口更严格限制
        if request.url.path in ('/api/auth/login', '/api/auth/register'):
            if not self.auth_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={'detail': '请求过于频繁，请稍后再试'},
                )
        elif request.url.path.startswith('/api/'):
            if not self.global_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={'detail': '请求过于频繁，请稍后再试'},
                )

        response = await call_next(request)
        return response
