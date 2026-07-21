"""
速率限制器核心实现

提供令牌桶算法的速率限制功能
"""

import time
from collections import defaultdict
from typing import Dict, List


class RateLimiter:
    """
    简单的速率限制器（内存实现）
    
    工作原理：令牌桶算法
    - 每个时间窗口内有固定数量的令牌（请求额度）
    - 每个请求消耗一个令牌
    - 超过时间窗口的请求自动过期
    
    对于生产环境，建议使用 Redis 作为后端存储以支持分布式
    
    示例：
        >>> limiter = RateLimiter()
        >>> if limiter.is_allowed("user:123", max_requests=100, window_seconds=60):
        ...     process_request()
    """
    
    def __init__(self):
        """初始化限制器"""
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        检查请求是否超过限制
        
        Args:
            key: 限制键（如 IP 地址、用户 ID 等）
            max_requests: 时间窗口内的最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            True 表示允许请求，False 表示超过限制
        
        示例：
            >>> limiter.is_allowed("192.168.1.1", max_requests=100, window_seconds=60)
            True
        """
        now = time.time()
        cutoff = now - window_seconds
        
        # 清理过期的请求记录
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if timestamp > cutoff
        ]
        
        # 检查是否超过限制
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_remaining(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> int:
        """
        获取剩余请求次数
        
        Args:
            key: 限制键
            max_requests: 最大请求数
            window_seconds: 时间窗口
        
        Returns:
            剩余请求次数（最小为 0）
        
        示例：
            >>> limiter.get_remaining("user:123", 100, 60)
            87  # 还可以发起 87 个请求
        """
        now = time.time()
        cutoff = now - window_seconds
        
        valid_requests = [
            timestamp for timestamp in self.requests[key]
            if timestamp > cutoff
        ]
        
        return max(0, max_requests - len(valid_requests))
    
    def get_reset_time(
        self,
        key: str,
        window_seconds: int
    ) -> float:
        """
        获取限制重置的时间戳
        
        Args:
            key: 限制键
            window_seconds: 时间窗口
        
        Returns:
            限制将重置的时间戳（秒）
        
        示例：
            >>> reset_time = limiter.get_reset_time("user:123", 60)
            >>> time.sleep(reset_time - time.time())
        """
        if not self.requests[key]:
            return time.time()
        
        oldest_request = min(self.requests[key])
        return oldest_request + window_seconds
    
    def reset(self, key: str) -> None:
        """
        重置限制键
        
        适用于管理员手动解除限制
        
        Args:
            key: 限制键
        
        示例：
            >>> limiter.reset("user:123")  # 立即允许该用户发起请求
        """
        if key in self.requests:
            del self.requests[key]
    
    def reset_all(self) -> None:
        """重置所有限制键"""
        self.requests.clear()
    
    def get_stats(self, key: str, window_seconds: int) -> Dict:
        """
        获取限制统计信息
        
        Args:
            key: 限制键
            window_seconds: 时间窗口
        
        Returns:
            包含统计信息的字典
        """
        now = time.time()
        cutoff = now - window_seconds
        
        valid_requests = [
            timestamp for timestamp in self.requests[key]
            if timestamp > cutoff
        ]
        
        return {
            'key': key,
            'current_requests': len(valid_requests),
            'oldest_request': valid_requests[0] if valid_requests else None,
            'newest_request': valid_requests[-1] if valid_requests else None,
        }


# 全局速率限制器实例
rate_limiter = RateLimiter()
_redis_rate_limiter = None


def configure_redis_rate_limiter(redis_client) -> None:
    """配置 Redis 后端速率限制（应用启动时调用）"""
    global _redis_rate_limiter
    if redis_client:
        from .redis_rate_limiter import RedisRateLimiter
        _redis_rate_limiter = RedisRateLimiter(redis_client)
    else:
        _redis_rate_limiter = None


def get_active_limiter():
    """返回当前可用的速率限制器（优先 Redis）"""
    return _redis_rate_limiter or rate_limiter
