"""队伍相关服务 — 含单人赛自动建队"""

from __future__ import annotations

import re
import secrets
from typing import Optional

from backend.server.extensions import db
from backend.server.db_models import User, Team, CtfParticipation, CtfParticipatingUser


def _solo_team_name(user: User) -> str:
    label = (user.nickname or user.username or f"用户{user.id}").strip()
    label = re.sub(r"\s+", "", label)[:32] or f"用户{user.id}"
    base = f"{label}·单人队"
    name = base
    n = 2
    while Team.query.filter_by(name=name).first():
        name = f"{base}#{n}"
        n += 1
    return name


def ensure_user_has_team(user: User, *, solo_if_missing: bool = True) -> Optional[Team]:
    """
    确保用户已归属某支队伍。无队伍且 solo_if_missing 时自动创建单人队。
    返回用户当前队伍；solo_if_missing=False 且无队伍时返回 None。
    """
    if not user:
        return None

    if user.team_id:
        team = Team.query.get(user.team_id)
        if team:
            return team

    if not solo_if_missing:
        return None

    team = Team(name=_solo_team_name(user), invite_code=secrets.token_hex(4))
    db.session.add(team)
    db.session.flush()

    user.team_id = team.id
    db.session.add(user)
    db.session.flush()
    return team


def repair_orphan_participations() -> int:
    """清理 team_id 为空的旧参赛记录（历史兼容）。"""
    fixed = 0
    orphans = CtfParticipation.query.filter(CtfParticipation.team_id.is_(None)).all()
    for part in orphans:
        CtfParticipatingUser.query.filter_by(participation_id=part.id).delete()
        db.session.delete(part)
        fixed += 1
    if fixed:
        db.session.commit()
    return fixed


def user_joined_game(user_id: int, game_id: int) -> bool:
    """用户是否已加入某场比赛（优先查个人参赛记录）。"""
    if CtfParticipatingUser.query.filter_by(user_id=user_id, game_id=game_id).first():
        return True
    user = User.query.get(user_id)
    if user and user.team_id:
        return bool(CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first())
    return False
