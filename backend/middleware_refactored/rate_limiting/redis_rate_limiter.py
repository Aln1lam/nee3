"""
基于 Redis 的分布式速率限制器

使用固定窗口计数器，支持多进程/多实例部署
"""

import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Redis 固定窗口速率限制器"""

    KEY_PREFIX = "ratelimit"

    def __init__(self, redis_client):
        self.redis = redis_client

    def _window_key(self, key: str, window_seconds: int) -> str:
        window_id = int(time.time()) // window_seconds
        return f"{self.KEY_PREFIX}:{key}:{window_seconds}:{window_id}"

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        if not self.redis:
            return True
        try:
            redis_key = self._window_key(key, window_seconds)
            pipe = self.redis.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window_seconds + 1)
            current, _ = pipe.execute()
            return int(current) <= max_requests
        except Exception as e:
            logger.warning(f"Redis rate limit check failed, denying request: {e}")
            return False

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        if not self.redis:
            return max_requests
        try:
            redis_key = self._window_key(key, window_seconds)
            current = self.redis.get(redis_key)
            used = int(current) if current else 0
            return max(0, max_requests - used)
        except Exception:
            return max_requests

    def get_reset_time(self, key: str, window_seconds: int) -> float:
        now = time.time()
        window_id = int(now) // window_seconds
        return (window_id + 1) * window_seconds

    def reset(self, key: str) -> None:
        if not self.redis:
            return
        try:
            pattern = f"{self.KEY_PREFIX}:{key}:*"
            for k in self.redis.scan_iter(match=pattern, count=100):
                self.redis.delete(k)
        except Exception as e:
            logger.warning(f"Redis rate limit reset failed: {e}")

    def reset_all(self) -> None:
        if not self.redis:
            return
        try:
            for k in self.redis.scan_iter(match=f"{self.KEY_PREFIX}:*", count=200):
                self.redis.delete(k)
        except Exception as e:
            logger.warning(f"Redis rate limit reset_all failed: {e}")

    def get_stats(self, key: str, window_seconds: int) -> Dict:
        remaining = self.get_remaining(key, 100, window_seconds)
        return {
            'key': key,
            'backend': 'redis',
            'remaining_estimate': remaining,
        }
