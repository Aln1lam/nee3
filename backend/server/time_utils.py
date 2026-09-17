"""Admin UI 时间与比赛窗口判断（datetime-local 默认为东八区本地时间）。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

# datetime-local 无时区字符串按管理员本地时区解释（默认 UTC+8）
ADMIN_TZ_OFFSET_HOURS = int(os.environ.get("NEPU_ADMIN_TZ_OFFSET_HOURS", "8"))


def utc_now_naive() -> datetime:
    return datetime.utcnow()


def parse_admin_datetime(value) -> Optional[datetime]:
    """
    解析管理端 datetime-local / ISO 字符串，统一存为 UTC naive。
    无时区的字符串视为管理员本地时间（默认东八区）。
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)

    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    # datetime-local：本地时间 → UTC
    return dt - timedelta(hours=ADMIN_TZ_OFFSET_HOURS)


def effective_start_utc(start_time: Optional[datetime]) -> Optional[datetime]:
    """将库内 start_time 转为 UTC naive 以便与 utcnow 比较。

    经 parse_admin_datetime 写入的 naive 时间已是 UTC，不再二次减时区偏移。
    仅当 NEPU_START_TIME_LEGACY_LOCAL=1 时，才把 naive 按管理员本地时区解释（旧库兼容）。
    """
    if start_time is None:
        return None
    if start_time.tzinfo is not None:
        return start_time.astimezone(timezone.utc).replace(tzinfo=None)
    if os.environ.get("NEPU_START_TIME_LEGACY_LOCAL", "").lower() in ("1", "true", "yes"):
        return start_time - timedelta(hours=ADMIN_TZ_OFFSET_HOURS)
    return start_time


def sync_game_status_if_due(game) -> bool:
    """已到开始时间的 not_started 赛事自动标记为 ongoing（写库由调用方 commit）。"""
    if not game or getattr(game, "status", None) != "not_started":
        return False
    start = effective_start_utc(getattr(game, "start_time", None))
    if start is None:
        return False
    if utc_now_naive() >= start:
        game.status = "ongoing"
        return True
    return False


def game_has_started(game) -> bool:
    """比赛是否已到可提交阶段（训练场恒为 True）。"""
    if not game:
        return False

    game_type = getattr(game, "game_type", None) or "official"
    if game_type in ("training", "practice"):
        return True

    status = getattr(game, "status", None) or "not_started"
    if status == "ongoing":
        return True

    start = effective_start_utc(getattr(game, "start_time", None))
    if start is None:
        return status == "ongoing"

    return utc_now_naive() >= start
