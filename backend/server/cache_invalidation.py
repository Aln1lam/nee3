"""CRUD 后统一失效 Redis 缓存"""

import logging

from backend.services.cache_aside import (
    PLATFORM_INFO_KEY,
    KEY_WIKI_NAV,
    KEY_CAROUSEL,
    KEY_BULLETINS_PUBLIC,
    KEY_ARTICLES_PUBLIC_PREFIX,
    KEY_TRAINING_SIDEBAR,
    cache_delete,
    cache_delete_pattern,
    invalidate_articles_public_cache,
    invalidate_carousel_read_cache,
    invalidate_bulletins_read_cache,
    invalidate_platform_read_cache,
    invalidate_training_sidebar_cache,
)
from backend.services.redis_service import get_redis

logger = logging.getLogger(__name__)


def _delete_key(key: str) -> None:
    cache_delete(key)


def _delete_pattern(pattern: str) -> int:
    return cache_delete_pattern(pattern)


def _invalidate_api_cache(prefix: str) -> int:
    try:
        from backend.middleware_refactored.caching.redis_response_cache import invalidate_cache_prefix
        return invalidate_cache_prefix(prefix)
    except Exception as exc:
        logger.warning("API cache invalidate %s failed: %s", prefix, exc)
        return 0


def invalidate_platform_info_cache() -> None:
    invalidate_platform_read_cache()


def invalidate_external_events_cache() -> None:
    _delete_pattern("external_events:*")


def invalidate_articles_cache() -> None:
    invalidate_platform_read_cache()
    invalidate_articles_public_cache()
    _invalidate_api_cache("articles")
    _invalidate_api_cache("wiki")


def invalidate_carousel_cache() -> None:
    invalidate_carousel_read_cache()
    _invalidate_api_cache("carousel")


def invalidate_announcements_cache() -> None:
    invalidate_bulletins_read_cache()
    _invalidate_api_cache("announcements")
    _invalidate_api_cache("bulletins")


def invalidate_system_config_cache() -> None:
    invalidate_platform_read_cache()


def invalidate_scoreboard_cache() -> None:
    rs = get_redis()
    if rs and rs.is_available():
        try:
            from backend.services.redis_service import ScoreboardCache
            _delete_pattern(f"{ScoreboardCache.CACHE_KEY_PREFIX}:*")
        except Exception as exc:
            logger.warning("Scoreboard cache invalidate failed: %s", exc)


def invalidate_challenge_cache() -> None:
    _delete_pattern("challenge:*")
    _invalidate_api_cache("challenge")


def invalidate_games_cache() -> None:
    invalidate_training_sidebar_cache()


INVALIDATORS = {
    "articles": invalidate_articles_cache,
    "carousel": invalidate_carousel_cache,
    "announcements": invalidate_announcements_cache,
    "platform": invalidate_system_config_cache,
    "scoreboard": invalidate_scoreboard_cache,
    "challenge": invalidate_challenge_cache,
    "games": invalidate_games_cache,
}


def mark_cache_dirty(session, *kinds: str) -> None:
    dirty = session.info.setdefault("cache_dirty", set())
    dirty.update(kinds)


def flush_cache_dirty(session) -> None:
    dirty = session.info.pop("cache_dirty", None)
    if not dirty:
        return
    for kind in sorted(dirty):
        fn = INVALIDATORS.get(kind)
        if not fn:
            continue
        try:
            fn()
            logger.debug("Cache invalidated after commit: %s", kind)
        except Exception as exc:
            logger.warning("Cache invalidation %s failed: %s", kind, exc)


def clear_cache_dirty(session) -> None:
    session.info.pop("cache_dirty", None)
