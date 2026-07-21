"""SQLAlchemy 事件：CRUD 提交后自动失效 Redis 缓存"""

from sqlalchemy import event

from backend.server.extensions import db
from backend.server.db_models import (
    Article,
    CarouselSlide,
    MainAnnouncement,
    SystemConfig,
    CtfChallenge,
    CtfChallengeSubmission,
    CtfSolves,
    CtfGame,
)
from backend.server.cache_invalidation import mark_cache_dirty, flush_cache_dirty, clear_cache_dirty


def _bind(model, kind: str):
    def _listener(mapper, connection, target):
        mark_cache_dirty(db.session, kind)

    event.listen(model, "after_insert", _listener)
    event.listen(model, "after_update", _listener)
    event.listen(model, "after_delete", _listener)


def _bind_many(model, *kinds: str):
    def _listener(mapper, connection, target):
        mark_cache_dirty(db.session, *kinds)

    event.listen(model, "after_insert", _listener)
    event.listen(model, "after_update", _listener)
    event.listen(model, "after_delete", _listener)


_hooks_registered = False


def register_cache_hooks():
    global _hooks_registered
    if _hooks_registered:
        return
    _hooks_registered = True

    _bind(Article, "articles")
    _bind(CarouselSlide, "carousel")
    _bind(MainAnnouncement, "announcements")
    _bind(SystemConfig, "platform")
    _bind_many(CtfChallenge, "challenge", "scoreboard")
    _bind(CtfGame, "games")
    for model in (CtfChallengeSubmission, CtfSolves):
        _bind(model, "scoreboard")

    @event.listens_for(db.session.__class__, "after_commit")
    def _after_commit(session):
        flush_cache_dirty(session)

    @event.listens_for(db.session.__class__, "after_rollback")
    def _after_rollback(session):
        clear_cache_dirty(session)
