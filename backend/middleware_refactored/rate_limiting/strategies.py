"""
速率限制策略

定义不同的限制策略，支持可扩展的限制配置
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple
import time


class RateLimitStrategy(ABC):
    """
    速率限制策略抽象基类
    
    所有限制策略都应继承此类并实现相应方法
    """
    
    @abstractmethod
    def is_allowed(self, key: str) -> bool:
        """检查请求是否被允许"""
        pass
    
    @abstractmethod
    def get_remaining(self, key: str) -> int:
        """获取剩余请求数"""
        pass
    
    @abstractmethod
    def reset(self, key: str) -> None:
        """重置限制"""
        pass


class TokenBucketStrategy(RateLimitStrategy):
    """
    令牌桶算法
    
    最常用的限制策略，适合大多数场景
    
    工作原理：
    1. 每个时间窗口开始时，桶中有 capacity 个令牌
    2. 每个请求消耗一个令牌
    3. 如果桶中没有令牌，请求被拒绝
    4. 超过时间窗口的请求记录自动过期
    """
    
    def __init__(self, capacity: int, refill_rate: float, window_seconds: int):
        """
        初始化令牌桶
        
        Args:
            capacity: 桶的容量（最大令牌数）
            refill_rate: 补充速率（令牌/秒）
            window_seconds: 时间窗口（秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.window_seconds = window_seconds
        self.buckets: Dict[str, Tuple[float, int]] = {}  # key -> (last_refill_time, tokens)
    
    def is_allowed(self, key: str) -> bool:
        """检查令牌是否可用"""
        now = time.time()
        
        if key not in self.buckets:
            self.buckets[key] = (now, self.capacity)
        
        last_refill, tokens = self.buckets[key]
        time_passed = now - last_refill
        
        # 补充令牌
        new_tokens = min(
            self.capacity,
            tokens + time_passed * self.refill_rate
        )
        
        if new_tokens >= 1:
            self.buckets[key] = (now, new_tokens - 1)
            return True
        
        return False
    
    def get_remaining(self, key: str) -> int:
        """获取剩余令牌数"""
        if key not in self.buckets:
            return self.capacity
        
        last_refill, tokens = self.buckets[key]
        time_passed = time.time() - last_refill
        
        new_tokens = min(
            self.capacity,
            tokens + time_passed * self.refill_rate
        )
        
        return int(new_tokens)
    
    def reset(self, key: str) -> None:
        """重置为满桶"""
        now = time.time()
        self.buckets[key] = (now, self.capacity)


class SlidingWindowStrategy(RateLimitStrategy):
    """
    滑动时间窗口算法
    
    更精确但更消耗资源，适合严格的限制要求
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        初始化滑动窗口
        
        Args:
            max_requests: 时间窗口内的最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str) -> bool:
        """检查请求是否在窗口内"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        if key not in self.requests:
            self.requests[key] = []
        
        # 清理过期请求
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if timestamp > cutoff
        ]
        
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_remaining(self, key: str) -> int:
        """获取剩余请求数"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        if key not in self.requests:
            return self.max_requests
        
        valid_requests = [
            t for t in self.requests[key]
            if t > cutoff
        ]
        
        return max(0, self.max_requests - len(valid_requests))
    
    def reset(self, key: str) -> None:
        """重置时间窗口"""
        if key in self.requests:
            del self.requests[key]


# 预定义的常用限制策略

def get_api_rate_limit_strategy() -> TokenBucketStrategy:
    """获取通用 API 限制策略：100 请求/分钟"""
    return TokenBucketStrategy(capacity=100, refill_rate=100/60, window_seconds=60)


def get_submission_rate_limit_strategy() -> TokenBucketStrategy:
    """获取提交限制策略：5 提交/分钟"""
    return TokenBucketStrategy(capacity=5, refill_rate=5/60, window_seconds=60)


def get_login_rate_limit_strategy() -> TokenBucketStrategy:
    """获取登录限制策略：5 尝试/分钟"""
    return TokenBucketStrategy(capacity=5, refill_rate=5/60, window_seconds=60)


def get_download_rate_limit_strategy() -> TokenBucketStrategy:
    """获取下载限制策略：3 下载/小时"""
    return TokenBucketStrategy(capacity=3, refill_rate=3/3600, window_seconds=3600)
