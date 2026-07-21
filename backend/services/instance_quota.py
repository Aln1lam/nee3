"""动态容器实例配额：单人/单队同时 running 上限。"""
from __future__ import annotations

import os
from typing import Optional, Tuple

from backend.server.db_models import CtfGameInstance, User, Team


def max_running_instances() -> int:
    return max(1, int(os.environ.get("NEPU_MAX_RUNNING_INSTANCES", "2")))


def count_running_instances(user: User, team: Optional[Team] = None, *, for_update: bool = False) -> int:
    if team is not None and getattr(team, "id", None):
        q = CtfGameInstance.query.filter_by(team_id=team.id, is_running=True)
    elif user and getattr(user, "team_id", None):
        q = CtfGameInstance.query.filter_by(team_id=user.team_id, is_running=True)
    else:
        q = CtfGameInstance.query.filter_by(user_id=user.id, is_running=True)
    if for_update:
        q = q.with_for_update()
    return q.count()


def check_can_start_new_instance(
    user: User,
    team: Optional[Team] = None,
    *,
    challenge_id: Optional[int] = None,
    for_update: bool = True,
) -> Tuple[bool, str, Optional[CtfGameInstance]]:
    """
    若同题已有 running 实例，返回 (True, msg, existing) 表示应复用。
    若配额已满且需新开，返回 (False, msg, None)。
    否则 (True, '', None) 允许新建。

    for_update=True 时对队伍/用户当前 running 行加锁，降低并发超配额风险。
    """
    # 先锁住该主体全部 running 行，再判断同题复用与配额
    if for_update:
        if team is not None and getattr(team, "id", None):
            CtfGameInstance.query.filter_by(team_id=team.id, is_running=True).with_for_update().all()
        elif user and getattr(user, "team_id", None):
            CtfGameInstance.query.filter_by(team_id=user.team_id, is_running=True).with_for_update().all()
        else:
            CtfGameInstance.query.filter_by(user_id=user.id, is_running=True).with_for_update().all()

    if challenge_id is not None:
        q = CtfGameInstance.query.filter_by(challenge_id=challenge_id, is_running=True)
        if team is not None and getattr(team, "id", None):
            existing = q.filter_by(team_id=team.id).first()
        elif user and user.team_id:
            existing = q.filter_by(team_id=user.team_id).first()
        else:
            existing = q.filter_by(user_id=user.id).first()
        if existing:
            return True, "已有运行中的实例", existing

    limit = max_running_instances()
    running = count_running_instances(user, team, for_update=False)
    if running >= limit:
        return False, f"同时运行的容器已达上限（{limit}），请先销毁后再启动", None
    return True, "", None
