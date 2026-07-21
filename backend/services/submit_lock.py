"""提交/血榜并发保护：挑战行锁 + Redis 可选锁。"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


def lock_challenge_row(challenge_id: int):
    """对题目行加 FOR UPDATE，串行化该题的正确提交与血榜写入。"""
    from backend.server.db_models import CtfChallenge

    return (
        CtfChallenge.query.filter_by(id=challenge_id)
        .with_for_update()
        .first()
    )


@contextmanager
def redis_submit_lock(challenge_id: int, owner_key: str, ttl: int = 15) -> Iterator[bool]:
    """
    Redis 分布式锁（fail-closed）。
    - True: 持锁成功，或当前无 Redis（仅依赖 DB 行锁）
    - False: 锁被占用，或 Redis 异常（拒绝提交，避免竞态）
    """
    lock_key = f"neepu:submit:lock:{challenge_id}:{owner_key}"
    redis = None
    token = None
    try:
        from backend.services.redis_service import get_redis
        import uuid

        svc = get_redis()
        if svc and svc.is_available():
            redis = svc.redis
            token = uuid.uuid4().hex
            ok = redis.set(lock_key, token, nx=True, ex=ttl)
            if not ok:
                yield False
                return
            yield True
            return
        # 无 Redis：退回仅 DB 行锁
        yield True
    except Exception as exc:
        logger.warning("redis submit lock failed closed: %s", exc)
        yield False
    finally:
        if redis and token:
            try:
                current = redis.get(lock_key)
                if current and (current.decode() if isinstance(current, bytes) else current) == token:
                    redis.delete(lock_key)
            except Exception:
                pass


def submission_owner_key(user) -> str:
    if user and getattr(user, "team_id", None):
        return f"t{user.team_id}"
    return f"u{getattr(user, 'id', 0)}"


def correct_submission_dedupe_key(challenge_id: int, user) -> Optional[str]:
    """正确提交去重键：同题同队（或同人）仅一条。错误提交为 None。"""
    if not user:
        return None
    if getattr(user, "team_id", None):
        return f"c{challenge_id}:t{user.team_id}"
    return f"c{challenge_id}:u{getattr(user, 'id', 0)}"
