import unittest
from unittest.mock import patch

from app.core.rate_limiter import RateLimitMiddleware


class RateLimitMiddlewareTestCase(unittest.TestCase):
    def test_uses_configured_limits(self):
        with patch('app.core.rate_limiter.settings.rate_limit_requests_per_minute', 7), patch(
            'app.core.rate_limiter.settings.auth_rate_limit_requests_per_minute', 3
        ):
            middleware = RateLimitMiddleware(app=lambda scope, receive, send: None)
        self.assertEqual(middleware.global_limiter.max_requests, 7)
        self.assertEqual(middleware.auth_limiter.max_requests, 3)

    def test_removes_expired_client_entries(self):
        middleware = RateLimitMiddleware(app=lambda scope, receive, send: None, window=60)
        middleware.global_limiter._clients['old-client'] = [0.0]
        middleware.auth_limiter._clients['old-client'] = [0.0]
        middleware._last_cleanup = 0.0
        with patch('app.core.rate_limiter.time.monotonic', return_value=120.0):
            middleware._cleanup_if_due()
        self.assertNotIn('old-client', middleware.global_limiter._clients)
        self.assertNotIn('old-client', middleware.auth_limiter._clients)


if __name__ == '__main__':
    unittest.main()
