"""
速率限制模块
提供请求频率控制功能
"""

from .rate_limiter import RateLimiter, rate_limiter, get_active_limiter, configure_redis_rate_limiter
from .redis_rate_limiter import RedisRateLimiter
from .decorators import rate_limit, submission_rate_limit, login_rate_limit
from .strategies import RateLimitStrategy, TokenBucketStrategy

__all__ = [
    'RateLimiter',
    'RedisRateLimiter',
    'rate_limiter',
    'get_active_limiter',
    'configure_redis_rate_limiter',
    'rate_limit',
    'submission_rate_limit',
    'login_rate_limit',
    'RateLimitStrategy',
    'TokenBucketStrategy',
]
