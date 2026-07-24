"""CRUD 后统一失效 Redis 缓存"""

from __future__ import annotations

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
    """全站清榜（仅作兜底；正常路径应走按 game_id 失效）。"""
    rs = get_redis()
    if rs and rs.is_available():
        try:
            from backend.services.redis_service import ScoreboardCache
            _delete_pattern(f"{ScoreboardCache.CACHE_KEY_PREFIX}:*")
        except Exception as exc:
            logger.warning("Scoreboard cache invalidate failed: %s", exc)


def invalidate_scoreboard_cache_for_game(game_id: int) -> None:
    """只失效单场比赛的积分榜 + Timeline，避免多赛并行时雪崩重算。"""
    rs = get_redis()
    if not rs or not rs.is_available():
        return
    try:
        from backend.services.redis_service import ScoreboardCache
        ScoreboardCache.invalidate_scoreboard(rs, int(game_id))
    except Exception as exc:
        logger.warning("Scoreboard cache invalidate game=%s failed: %s", game_id, exc)


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


def mark_cache_dirty(session, *kinds: str, game_id: int | None = None) -> None:
    dirty = session.info.setdefault("cache_dirty", set())
    for kind in kinds:
        if kind == "scoreboard" and game_id is not None:
            dirty.add(f"scoreboard:{int(game_id)}")
        else:
            dirty.add(kind)


def flush_cache_dirty(session) -> None:
    dirty = session.info.pop("cache_dirty", None)
    if not dirty:
        return
    for kind in sorted(dirty):
        try:
            if kind.startswith("scoreboard:"):
                gid = int(kind.split(":", 1)[1])
                invalidate_scoreboard_cache_for_game(gid)
                logger.debug("Cache invalidated after commit: %s", kind)
                continue
            fn = INVALIDATORS.get(kind)
            if not fn:
                continue
            fn()
            logger.debug("Cache invalidated after commit: %s", kind)
        except Exception as exc:
            logger.warning("Cache invalidation %s failed: %s", kind, exc)


def clear_cache_dirty(session) -> None:
    session.info.pop("cache_dirty", None)
