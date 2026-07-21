"""
Redis 缓存服务
用于：排行榜缓存、题目缓存、用户数据缓存、会话管理、实时通知队列
"""

import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from functools import wraps
import redis

logger = logging.getLogger(__name__)


class RedisService:
    """Redis 缓存服务"""

    _pool: Optional[redis.ConnectionPool] = None

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True,
        max_connections: int = 50,
    ):
        try:
            if RedisService._pool is None:
                RedisService._pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=decode_responses,
                    max_connections=max_connections,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30,
                )
            self.redis = redis.Redis(connection_pool=RedisService._pool)
            self.redis.ping()
            logger.info(f"Redis connected to {host}:{port}/db={db}")
            self.is_connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            self.redis = None
    
    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        if not self.is_connected:
            return False
        
        try:
            self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self.is_available():
            return None
        
        try:
            return self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(self, key: str, value: str, expiration: int = 3600) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expiration: 过期时间（秒），0 表示不过期
        
        Returns:
            是否成功
        """
        if not self.is_available():
            return False
        
        try:
            if expiration > 0:
                self.redis.setex(key, expiration, value)
            else:
                self.redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available():
            return False
        
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键（使用 SCAN 避免阻塞）"""
        if not self.is_available():
            return 0

        try:
            deleted = 0
            for key in self.redis.scan_iter(match=pattern, count=200):
                self.redis.delete(key)
                deleted += 1
            return deleted
        except Exception as e:
            logger.error(f"Redis DELETE PATTERN error: {e}")
            return 0

    def setex_json(self, key: str, ttl: int, value: Dict) -> bool:
        """原子设置 JSON 并指定 TTL"""
        return self.set_json(key, value, expiration=ttl)

    def get_info(self) -> Dict:
        """获取 Redis 运行信息（用于健康检查）"""
        if not self.is_available():
            return {"status": "unavailable"}
        try:
            info = self.redis.info(section="memory")
            return {
                "status": "ok",
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": self.redis.info("clients").get("connected_clients"),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_json(self, key: str) -> Optional[Dict]:
        """获取 JSON 缓存值"""
        value = self.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except Exception as e:
            logger.error(f"JSON decode error: {e}")
            return None
    
    def set_json(self, key: str, value: Dict, expiration: int = 3600) -> bool:
        """设置 JSON 缓存值"""
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, expiration)
        except Exception as e:
            logger.error(f"JSON encode error: {e}")
            return False
    
    def increment(self, key: str, delta: int = 1) -> Optional[int]:
        """原子性增加值"""
        if not self.is_available():
            return None
        
        try:
            return self.redis.incrby(key, delta)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return None
    
    def lpush(self, key: str, *values) -> int:
        """推送值到列表左端"""
        if not self.is_available():
            return 0
        
        try:
            return self.redis.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH error: {e}")
            return 0
    
    def rpop(self, key: str) -> Optional[str]:
        """从列表右端弹出值"""
        if not self.is_available():
            return None
        
        try:
            return self.redis.rpop(key)
        except Exception as e:
            logger.error(f"Redis RPOP error: {e}")
            return None
    
    def llen(self, key: str) -> int:
        """获取列表长度"""
        if not self.is_available():
            return 0
        
        try:
            return self.redis.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN error: {e}")
            return 0
    
    def lrange(self, key: str, start: int = 0, stop: int = -1) -> List[str]:
        """获取列表范围内的值"""
        if not self.is_available():
            return []
        
        try:
            return self.redis.lrange(key, start, stop)
        except Exception as e:
            logger.error(f"Redis LRANGE error: {e}")
            return []
    
    def sadd(self, key: str, *members) -> int:
        """添加成员到集合"""
        if not self.is_available():
            return 0
        
        try:
            return self.redis.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis SADD error: {e}")
            return 0
    
    def smembers(self, key: str) -> set:
        """获取集合的所有成员"""
        if not self.is_available():
            return set()
        
        try:
            return self.redis.smembers(key)
        except Exception as e:
            logger.error(f"Redis SMEMBERS error: {e}")
            return set()


# ======================== 特定缓存操作 ========================

class ScoreboardCache:
    """排行榜缓存"""
    
    CACHE_KEY_PREFIX = "scoreboard"
    CACHE_EXPIRATION = 300  # 5分钟
    
    @staticmethod
    def get_cache_key(game_id: int, team_id: Optional[int] = None) -> str:
        """生成缓存键"""
        if team_id:
            return f"{ScoreboardCache.CACHE_KEY_PREFIX}:{game_id}:team:{team_id}"
        return f"{ScoreboardCache.CACHE_KEY_PREFIX}:{game_id}:all"
    
    @staticmethod
    def cache_scoreboard(redis_service: RedisService, game_id: int, scoreboard_data: Dict) -> bool:
        """缓存排行榜数据"""
        key = ScoreboardCache.get_cache_key(game_id)
        return redis_service.set_json(key, scoreboard_data, ScoreboardCache.CACHE_EXPIRATION)
    
    @staticmethod
    def get_cached_scoreboard(redis_service: RedisService, game_id: int) -> Optional[Dict]:
        """获取缓存的排行榜数据"""
        key = ScoreboardCache.get_cache_key(game_id)
        return redis_service.get_json(key)
    
    @staticmethod
    def invalidate_scoreboard(redis_service: RedisService, game_id: int) -> bool:
        """清除排行榜缓存"""
        pattern = f"{ScoreboardCache.CACHE_KEY_PREFIX}:{game_id}:*"
        redis_service.delete_pattern(pattern)
        return True


class ChallengeCache:
    """题目缓存"""
    
    CACHE_KEY_PREFIX = "challenge"
    CACHE_EXPIRATION = 600  # 10分钟
    
    @staticmethod
    def get_cache_key(challenge_id: int) -> str:
        """生成缓存键"""
        return f"{ChallengeCache.CACHE_KEY_PREFIX}:{challenge_id}"
    
    @staticmethod
    def cache_challenge(redis_service: RedisService, challenge_id: int, challenge_data: Dict) -> bool:
        """缓存题目数据"""
        key = ChallengeCache.get_cache_key(challenge_id)
        return redis_service.set_json(key, challenge_data, ChallengeCache.CACHE_EXPIRATION)
    
    @staticmethod
    def get_cached_challenge(redis_service: RedisService, challenge_id: int) -> Optional[Dict]:
        """获取缓存的题目数据"""
        key = ChallengeCache.get_cache_key(challenge_id)
        return redis_service.get_json(key)
    
    @staticmethod
    def invalidate_challenge(redis_service: RedisService, challenge_id: int) -> bool:
        """清除题目缓存"""
        key = ChallengeCache.get_cache_key(challenge_id)
        redis_service.delete(key)
        return True


class UserSessionCache:
    """用户会话缓存"""
    
    CACHE_KEY_PREFIX = "session"
    CACHE_EXPIRATION = 86400  # 24小时
    
    @staticmethod
    def get_cache_key(user_id: int) -> str:
        """生成缓存键"""
        return f"{UserSessionCache.CACHE_KEY_PREFIX}:{user_id}"
    
    @staticmethod
    def cache_user_data(redis_service: RedisService, user_id: int, user_data: Dict) -> bool:
        """缓存用户数据"""
        key = UserSessionCache.get_cache_key(user_id)
        return redis_service.set_json(key, user_data, UserSessionCache.CACHE_EXPIRATION)
    
    @staticmethod
    def get_cached_user(redis_service: RedisService, user_id: int) -> Optional[Dict]:
        """获取缓存的用户数据"""
        key = UserSessionCache.get_cache_key(user_id)
        return redis_service.get_json(key)
    
    @staticmethod
    def invalidate_user(redis_service: RedisService, user_id: int) -> bool:
        """清除用户缓存"""
        key = UserSessionCache.get_cache_key(user_id)
        redis_service.delete(key)
        return True


class NotificationQueue:
    """实时通知队列"""
    
    QUEUE_KEY_PREFIX = "notifications"
    
    @staticmethod
    def get_queue_key(game_id: int) -> str:
        """生成队列键"""
        return f"{NotificationQueue.QUEUE_KEY_PREFIX}:{game_id}"
    
    @staticmethod
    def push_notification(redis_service: RedisService, game_id: int, notification: Dict) -> bool:
        """推送通知到队列"""
        queue_key = NotificationQueue.get_queue_key(game_id)
        notification['timestamp'] = datetime.utcnow().isoformat()
        json_str = json.dumps(notification)
        return redis_service.lpush(queue_key, json_str) > 0
    
    @staticmethod
    def get_notifications(redis_service: RedisService, game_id: int, limit: int = 100) -> List[Dict]:
        """获取通知列表"""
        queue_key = NotificationQueue.get_queue_key(game_id)
        notifications = redis_service.lrange(queue_key, 0, limit - 1)
        
        result = []
        for notif_str in notifications:
            try:
                result.append(json.loads(notif_str))
            except Exception as e:
                logger.error(f"Failed to parse notification: {e}")
        
        return result
    
    @staticmethod
    def clear_notifications(redis_service: RedisService, game_id: int) -> bool:
        """清除所有通知"""
        queue_key = NotificationQueue.get_queue_key(game_id)
        redis_service.delete(queue_key)
        return True


# ======================== 缓存装饰器 ========================

def cache_result(expiration: int = 3600, key_prefix: str = ""):
    """缓存函数结果的装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix or func.__name__}:{str(args)}:{str(kwargs)}"
            svc = get_redis()
            if svc and svc.is_available():
                cached = svc.get(cache_key)
                if cached:
                    try:
                        return json.loads(cached)
                    except Exception:
                        pass

            result = func(*args, **kwargs)

            if svc and svc.is_available():
                try:
                    svc.set(cache_key, json.dumps(result, default=str), expiration)
                except Exception:
                    pass

            return result

        return wrapper

    return decorator


# 全局服务实例
redis_service: Optional[RedisService] = None


def get_redis() -> Optional[RedisService]:
    """获取全局 Redis 服务实例"""
    return redis_service


def initialize_redis(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
) -> RedisService:
    """初始化全局 Redis 服务"""
    global redis_service
    redis_service = RedisService(host=host, port=port, db=db, password=password)
    return redis_service
