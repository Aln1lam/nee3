"""
Redis API 响应缓存

对只读 GET 接口缓存 JSON 响应，减轻数据库压力
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Callable, Optional

from flask import request, make_response

logger = logging.getLogger(__name__)

CACHE_PREFIX = "api_cache"


def _get_redis():
    try:
        from backend.services.redis_service import get_redis
        return get_redis()
    except Exception:
        return None


def _cache_key(prefix: str, *parts) -> str:
    raw = ":".join(str(p) for p in parts)
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{CACHE_PREFIX}:{prefix}:{digest}"


def cache_response(prefix: str, ttl: int = 60, vary_by_user: bool = False):
    """
    缓存 GET 请求的 JSON 响应

    Args:
        prefix: 缓存命名空间（如 scoreboard、platform_info）
        ttl: 过期秒数
        vary_by_user: 是否按 JWT 用户区分缓存
    """

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method != "GET":
                return fn(*args, **kwargs)

            redis_svc = _get_redis()
            user_part = ""
            if vary_by_user:
                try:
                    from flask_jwt_extended import get_jwt_identity
                    uid = get_jwt_identity()
                    user_part = f":user:{uid or 'anon'}"
                except Exception:
                    user_part = ":user:anon"

            query_part = request.query_string.decode() if request.query_string else ""
            path_part = request.path
            key = _cache_key(prefix, path_part, query_part, user_part, *kwargs.values())

            if redis_svc and redis_svc.is_available():
                cached = redis_svc.get(key)
                if cached:
                    try:
                        payload = json.loads(cached)
                        resp = make_response(payload["body"], payload["status"])
                        for hk, hv in payload.get("headers", {}).items():
                            resp.headers[hk] = hv
                        resp.headers["X-Cache"] = "HIT"
                        return resp
                    except Exception:
                        pass

            result = fn(*args, **kwargs)

            if redis_svc and redis_svc.is_available() and isinstance(result, tuple):
                body, status = result[0], result[1]
                headers = {}
                if hasattr(body, "get_json"):
                    serializable_body = body.get_json()
                elif isinstance(body, dict):
                    serializable_body = body
                else:
                    serializable_body = str(body)
                try:
                    redis_svc.set(
                        key,
                        json.dumps({"body": serializable_body, "status": status, "headers": headers}),
                        expiration=ttl,
                    )
                except Exception as e:
                    logger.debug(f"Cache store failed: {e}")
                if hasattr(result[0], "headers"):
                    result[0].headers["X-Cache"] = "MISS"
            elif redis_svc and redis_svc.is_available():
                try:
                    if hasattr(result, "get_json"):
                        body_data = result.get_json()
                        status = result.status_code
                    else:
                        body_data = result
                        status = 200
                    redis_svc.set(
                        key,
                        json.dumps({"body": body_data, "status": status, "headers": {}}),
                        expiration=ttl,
                    )
                    if hasattr(result, "headers"):
                        result.headers["X-Cache"] = "MISS"
                except Exception:
                    pass

            return result

        return wrapper

    return decorator


def invalidate_cache_prefix(prefix: str) -> int:
    """清除某命名空间下所有 API 缓存"""
    redis_svc = _get_redis()
    if not redis_svc or not redis_svc.is_available():
        return 0
    return redis_svc.delete_pattern(f"{CACHE_PREFIX}:{prefix}:*")
