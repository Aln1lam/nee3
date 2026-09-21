"""队伍相关服务 — 按赛事隔离队伍（每赛独立 team_id）"""

from __future__ import annotations

import re
import secrets
from typing import Optional

from backend.server.extensions import db
from backend.server.db_models import User, Team, CtfParticipation, CtfParticipatingUser


def _solo_team_name(user: User, game_id: Optional[int] = None) -> str:
    label = (user.nickname or user.username or f"用户{user.id}").strip()
    label = re.sub(r"\s+", "", label)[:32] or f"用户{user.id}"
    base = f"{label}·单人队"
    if game_id is not None:
        base = f"{base}·赛{game_id}"
    name = base
    n = 2
    while Team.query.filter_by(name=name).first():
        name = f"{base}#{n}"
        n += 1
    return name


def get_user_team_for_game(user_id: int, game_id: int) -> Optional[Team]:
    """用户在指定赛事中的队伍（以 CtfParticipatingUser 为准）。"""
    pu = (
        CtfParticipatingUser.query.filter_by(user_id=user_id, game_id=game_id)
        .order_by(CtfParticipatingUser.id.desc())
        .first()
    )
    if pu and pu.team_id:
        return Team.query.get(pu.team_id)
    return None


def resolve_team_for_game(user: Optional[User], game_id: int) -> Optional[Team]:
    """做题 / 容器 / 计分：优先赛事内队伍，训练场等可回落全局 team_id。"""
    if not user:
        return None
    scoped = get_user_team_for_game(user.id, game_id)
    if scoped:
        return scoped
    if user.team_id:
        part = CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first()
        if part:
            return Team.query.get(user.team_id)
    return None


def user_in_team_for_game(user_id: int, team_id: int, game_id: int) -> bool:
    return bool(
        CtfParticipatingUser.query.filter_by(
            user_id=user_id, game_id=game_id, team_id=team_id
        ).first()
    )


def ensure_user_has_team_for_game(
    user: User,
    game_id: int,
    *,
    solo_if_missing: bool = True,
) -> Optional[Team]:
    """
    确保用户在指定赛事中有队伍；无则创建赛事绑定单人队并写入参赛记录。
    不再依赖 User.team_id 作为跨赛唯一队伍。
    """
    if not user:
        return None

    existing = get_user_team_for_game(user.id, game_id)
    if existing:
        return existing

    if not solo_if_missing:
        return None

    team = Team(
        name=_solo_team_name(user, game_id),
        invite_code=secrets.token_urlsafe(16),
        game_id=game_id,
    )
    db.session.add(team)
    db.session.flush()

    participation = CtfParticipation.query.filter_by(game_id=game_id, team_id=team.id).first()
    if not participation:
        participation = CtfParticipation(
            game_id=game_id,
            team_id=team.id,
            status="confirmed",
        )
        db.session.add(participation)
        db.session.flush()

    db.session.add(
        CtfParticipatingUser(
            user_id=user.id,
            game_id=game_id,
            team_id=team.id,
            participation_id=participation.id,
        )
    )
    if not user.team_id:
        user.team_id = team.id
    db.session.add(user)
    db.session.flush()
    return team


def ensure_user_has_team(user: User, *, solo_if_missing: bool = True) -> Optional[Team]:
    """
    训练场 / 兼容：全局单人队（无 game_id）。
    正式赛事请使用 ensure_user_has_team_for_game。
    """
    if not user:
        return None

    if user.team_id:
        team = Team.query.get(user.team_id)
        if team:
            return team

    if not solo_if_missing:
        return None

    team = Team(name=_solo_team_name(user), invite_code=secrets.token_urlsafe(16))
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
    """用户是否已加入某场比赛。"""
    if CtfParticipatingUser.query.filter_by(user_id=user_id, game_id=game_id).first():
        return True
    user = User.query.get(user_id)
    if user and user.team_id:
        return bool(
            CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first()
        )
    return False
