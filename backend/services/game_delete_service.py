# -*- coding: utf-8 -*-
"""竞赛硬删除：按外键依赖顺序清理子表。"""
from __future__ import annotations

from backend.server.extensions import db
from backend.server.db_models import (
    CtfGame,
    CtfChallenge,
    CtfChallengeSubmission,
    CtfChallengeHint,
    CtfUserHintAccess,
    CtfParticipation,
    CtfParticipatingUser,
    CtfScoreboard,
    CtfDivision,
    CtfUserInviteCode,
    CtfCheatInfo,
    CtfSolves,
    CtfGameNotice,
    CtfHammerMessage,
    CtfGameInstance,
    CtfDynamicPackage,
    CtfChallengeCategory,
    PcapCapture,
)


def purge_game(game_id: int) -> CtfGame | None:
    """删除竞赛及其全部关联数据。调用方负责 commit/rollback。"""
    game = CtfGame.query.get(game_id)
    if not game:
        return None

    challenge_ids = [
        row[0]
        for row in db.session.query(CtfChallenge.id).filter_by(game_id=game_id).all()
    ]

    # 依赖 submission 的记录
    CtfCheatInfo.query.filter_by(game_id=game_id).delete(synchronize_session=False)

    if challenge_ids:
        instance_ids = [
            row[0]
            for row in db.session.query(CtfGameInstance.id)
            .filter(CtfGameInstance.challenge_id.in_(challenge_ids))
            .all()
        ]
        if instance_ids:
            PcapCapture.query.filter(
                PcapCapture.instance_id.in_(instance_ids)
            ).delete(synchronize_session=False)
            PcapCapture.query.filter(
                PcapCapture.challenge_id.in_(challenge_ids)
            ).delete(synchronize_session=False)
            CtfGameInstance.query.filter(
                CtfGameInstance.id.in_(instance_ids)
            ).delete(synchronize_session=False)

        hint_ids = [
            row[0]
            for row in db.session.query(CtfChallengeHint.id)
            .filter(CtfChallengeHint.challenge_id.in_(challenge_ids))
            .all()
        ]
        if hint_ids:
            CtfUserHintAccess.query.filter(
                CtfUserHintAccess.hint_id.in_(hint_ids)
            ).delete(synchronize_session=False)
            CtfChallengeHint.query.filter(
                CtfChallengeHint.id.in_(hint_ids)
            ).delete(synchronize_session=False)

        CtfDynamicPackage.query.filter(
            CtfDynamicPackage.challenge_id.in_(challenge_ids)
        ).delete(synchronize_session=False)

        # 其它比赛题目若引用本赛题目，先断开
        CtfChallenge.query.filter(
            CtfChallenge.source_challenge_id.in_(challenge_ids)
        ).update(
            {CtfChallenge.source_challenge_id: None},
            synchronize_session=False,
        )

    CtfHammerMessage.query.filter_by(game_id=game_id).delete(synchronize_session=False)
    CtfSolves.query.filter_by(game_id=game_id).delete(synchronize_session=False)
    CtfChallengeSubmission.query.filter_by(game_id=game_id).delete(synchronize_session=False)
    CtfScoreboard.query.filter_by(game_id=game_id).delete(synchronize_session=False)
    CtfGameNotice.query.filter_by(game_id=game_id).delete(synchronize_session=False)
    CtfUserInviteCode.query.filter_by(game_id=game_id).delete(synchronize_session=False)

    # 必须先删参赛用户，再删 participation（外键 participation_id）
    # 同时按 game_id 与 participation_id 双清，避免脏数据漏删
    part_ids = [
        row[0]
        for row in db.session.query(CtfParticipation.id).filter_by(game_id=game_id).all()
    ]
    CtfParticipatingUser.query.filter_by(game_id=game_id).delete(synchronize_session=False)
    if part_ids:
        CtfParticipatingUser.query.filter(
            CtfParticipatingUser.participation_id.in_(part_ids)
        ).delete(synchronize_session=False)
    CtfParticipation.query.filter_by(game_id=game_id).delete(synchronize_session=False)

    CtfChallenge.query.filter_by(game_id=game_id).delete(synchronize_session=False)

    # 分类仅解绑，不删全局分类行
    CtfChallengeCategory.query.filter_by(game_id=game_id).update(
        {CtfChallengeCategory.game_id: None},
        synchronize_session=False,
    )

    CtfDivision.query.filter_by(game_id=game_id).delete(synchronize_session=False)

    db.session.delete(game)
    db.session.flush()
    return game
