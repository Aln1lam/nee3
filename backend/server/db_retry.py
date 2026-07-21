"""数据库事务工具 — 死锁/锁等待超时自动重试"""

import logging
import time
from typing import Callable, TypeVar

from sqlalchemy.exc import DBAPIError, OperationalError

logger = logging.getLogger(__name__)

T = TypeVar("T")

# MySQL: 1213 deadlock, 1205 lock wait timeout
_DEADLOCK_HINTS = ("1213", "1205", "deadlock", "lock wait timeout")


def is_deadlock_error(exc: BaseException) -> bool:
    msg = str(getattr(exc, "orig", exc)).lower()
    return any(hint in msg for hint in _DEADLOCK_HINTS)


def run_transaction_with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    base_delay: float = 0.05,
) -> T:
    """
    执行写事务并在 MySQL 死锁/锁超时时自动重试。

    fn 内应完成所有 ORM 变更，不要自行 commit；成功返回后由本函数 commit。
    失败时自动 rollback。
    """
    from backend.server.extensions import db

    last_exc: BaseException | None = None
    for attempt in range(max_retries):
        try:
            result = fn()
            db.session.commit()
            return result
        except (OperationalError, DBAPIError) as exc:
            db.session.rollback()
            last_exc = exc
            if not is_deadlock_error(exc) or attempt >= max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "DB deadlock/lock timeout, retry %s/%s in %.0fms: %s",
                attempt + 1,
                max_retries,
                delay * 1000,
                exc,
            )
            time.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("run_transaction_with_retry failed without exception")
