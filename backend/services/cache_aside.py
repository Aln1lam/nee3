"""
Cache-Aside 读穿缓存层

原则（与架构约定一致）：
- MySQL：持久化真相源，所有业务数据最终落盘
- Redis：内存加速层，只存可重建的读缓存 + 天然过期的临时数据（验证码等）
- 读：先 Redis，未命中再查 MySQL 并回填
- 写：先 MySQL commit，再失效相关 Redis key
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# --- 命名空间 ---
CACHE_PREFIX = "cache"

# 平台聚合信息（兼容历史 key）
PLATFORM_INFO_KEY = "platform:info"

# 公开读接口 key
KEY_WIKI_NAV = f"{CACHE_PREFIX}:wiki-nav"
KEY_CAROUSEL = f"{CACHE_PREFIX}:carousel:v2"
KEY_BULLETINS_PUBLIC = f"{CACHE_PREFIX}:bulletins:public"
KEY_ARTICLES_PUBLIC_PREFIX = f"{CACHE_PREFIX}:articles:public"
KEY_TRAINING_SIDEBAR = f"{CACHE_PREFIX}:training:sidebar"

# 外部代理（第三方数据，非 MySQL）
KEY_EXTERNAL_EVENTS_PREFIX = "external_events"

# --- TTL（秒）---
TTL_PLATFORM_INFO = 120
TTL_WIKI_NAV = 120
TTL_CAROUSEL = 180
TTL_BULLETINS = 120
TTL_ARTICLES = 90
TTL_TRAINING_SIDEBAR = 180
TTL_EXTERNAL_EVENTS = 1800


def _redis():
    try:
        from backend.services.redis_service import get_redis
        svc = get_redis()
        if svc and svc.is_available():
            return svc
    except Exception:
        pass
    return None


def cache_get(key: str) -> Optional[Any]:
    rs = _redis()
    if not rs:
        return None
    try:
        return rs.get_json(key)
    except Exception as exc:
        logger.debug("cache_get %s failed: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int) -> None:
    rs = _redis()
    if not rs:
        return
    try:
        rs.set_json(key, value, ttl)
    except Exception as exc:
        logger.warning("cache_set %s failed: %s", key, exc)


def cache_delete(key: str) -> None:
    rs = _redis()
    if not rs:
        return
    try:
        rs.delete(key)
    except Exception as exc:
        logger.warning("cache_delete %s failed: %s", key, exc)


def cache_delete_pattern(pattern: str) -> int:
    rs = _redis()
    if not rs:
        return 0
    try:
        return rs.delete_pattern(pattern)
    except Exception as exc:
        logger.warning("cache_delete_pattern %s failed: %s", pattern, exc)
        return 0


def read_through(key: str, ttl: int, loader: Callable[[], Any]) -> Any:
    """Cache-Aside：先读 Redis，未命中则 loader 查库并回填。"""
    cached = cache_get(key)
    if cached is not None:
        return cached, True

    value = loader()
    cache_set(key, value, ttl)
    return value, False


def articles_public_cache_key(page: int, per_page: int) -> str:
    return f"{KEY_ARTICLES_PUBLIC_PREFIX}:p{page}:n{per_page}"


def invalidate_articles_public_cache() -> None:
    cache_delete_pattern(f"{KEY_ARTICLES_PUBLIC_PREFIX}:*")
    cache_delete(KEY_WIKI_NAV)


def invalidate_carousel_read_cache() -> None:
    cache_delete(KEY_CAROUSEL)


def invalidate_bulletins_read_cache() -> None:
    cache_delete(KEY_BULLETINS_PUBLIC)


def invalidate_platform_read_cache() -> None:
    cache_delete(PLATFORM_INFO_KEY)


def invalidate_training_sidebar_cache() -> None:
    cache_delete(KEY_TRAINING_SIDEBAR)


def warm_public_cache(app) -> None:
    """启动预热：将高频公开读接口加载进 Redis，减少首屏冷启动打库。"""
    with app.app_context():
        warmed = []

        try:
            from backend.route.platform import _build_platform_info
            cache_set(PLATFORM_INFO_KEY, _build_platform_info(), TTL_PLATFORM_INFO)
            warmed.append(PLATFORM_INFO_KEY)
        except Exception as exc:
            logger.warning("warm platform:info failed: %s", exc)

        try:
            from backend.services.wiki_nav_service import build_wiki_nav_from_db
            cache_set(KEY_WIKI_NAV, build_wiki_nav_from_db(wiki_only=True), TTL_WIKI_NAV)
            warmed.append(KEY_WIKI_NAV)
        except Exception as exc:
            logger.warning("warm wiki-nav failed: %s", exc)

        try:
            from backend.services.carousel_service import load_public_carousel_slides
            cache_set(KEY_CAROUSEL, load_public_carousel_slides(sanitize=True), TTL_CAROUSEL)
            warmed.append(KEY_CAROUSEL)
        except Exception as exc:
            logger.warning("warm carousel failed: %s", exc)

        try:
            from backend.server.db_models import MainAnnouncement
            rows = (
                MainAnnouncement.query.filter_by(is_active=True)
                .order_by(MainAnnouncement.created_at.desc())
                .limit(50)
                .all()
            )
            payload = {"code": 200, "msg": "ok", "data": [r.to_dict() for r in rows]}
            cache_set(KEY_BULLETINS_PUBLIC, payload, TTL_BULLETINS)
            warmed.append(KEY_BULLETINS_PUBLIC)
        except Exception as exc:
            logger.warning("warm bulletins failed: %s", exc)

        try:
            from backend.route.articles import load_public_articles_page
            cache_set(
                articles_public_cache_key(1, 50),
                load_public_articles_page(page=1, per_page=50),
                TTL_ARTICLES,
            )
            warmed.append(f"{KEY_ARTICLES_PUBLIC_PREFIX}:p1:n50")
        except Exception as exc:
            logger.warning("warm articles failed: %s", exc)

        try:
            from backend.route.platform import _load_training_sidebar
            cache_set(KEY_TRAINING_SIDEBAR, _load_training_sidebar(), TTL_TRAINING_SIDEBAR)
            warmed.append(KEY_TRAINING_SIDEBAR)
        except Exception as exc:
            logger.warning("warm training sidebar failed: %s", exc)

        if warmed:
            app.logger.info("Cache pre-warm completed: %s", ", ".join(warmed))
