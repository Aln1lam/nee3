"""Captcha token 存储 — Redis 优先，内存降级"""

import json
import logging
import time

logger = logging.getLogger(__name__)

CAPTCHA_PREFIX = "captcha"
DEFAULT_TTL = 300


def _get_redis():
    try:
        from backend.services.redis_service import get_redis
        svc = get_redis()
        if svc and svc.is_available():
            return svc
    except Exception:
        pass
    return None


# 内存降级存储
_MEMORY_STORE = {}


def _memory_cleanup():
    now = time.time()
    expired = [k for k, v in _MEMORY_STORE.items() if v["expires"] < now]
    for k in expired:
        _MEMORY_STORE.pop(k, None)


def store_captcha(captcha_id: str, code: str, ttl: int = DEFAULT_TTL) -> None:
    svc = _get_redis()
    payload = {"code": code.upper(), "expires": time.time() + ttl}
    if svc:
        svc.set(f"{CAPTCHA_PREFIX}:{captcha_id}", json.dumps(payload), expiration=ttl)
    else:
        _memory_cleanup()
        _MEMORY_STORE[captcha_id] = payload


def pop_captcha(captcha_id: str):
    """取出并删除验证码，不存在或过期返回 None"""
    svc = _get_redis()
    if svc:
        key = f"{CAPTCHA_PREFIX}:{captcha_id}"
        raw = svc.get(key)
        svc.delete(key)
        if not raw:
            return None
        try:
            entry = json.loads(raw)
        except Exception:
            return None
        if entry.get("expires", 0) < time.time():
            return None
        return entry

    _memory_cleanup()
    return _MEMORY_STORE.pop(captcha_id, None)
