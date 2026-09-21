from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from backend.server import extensions
from backend.server.db_models import (
    User, Team, CtfParticipation, CtfParticipatingUser, CtfScoreboard,
    CtfChallengeSubmission, CtfGameInstance, CtfSolves, CtfChallenge, CtfGame,
    TeamSeasonStats, PcapCapture,
)
from backend.services.sensitive_words import assert_clean_team_name
from backend.services.team_service import (
    get_user_team_for_game,
    user_in_team_for_game,
    ensure_user_has_team_for_game,
)
from backend.middleware_refactored import rate_limit
from sqlalchemy import text
import secrets

bp = Blueprint("teams", __name__)


def _current_user():
    return User.query.get(int(get_jwt_identity()))


@bp.post("/")
@jwt_required()
def create_team():
    """创建战队 - 创建者自动加入"""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return {"msg": "missing name"}, 400

    ok, err = assert_clean_team_name(name)
    if not ok:
        return {"msg": err}, 400

    user = _current_user()
    if not user:
        return {"msg": "用户不存在"}, 401

    game_id = data.get("game_id")
    try:
        game_id = int(game_id) if game_id is not None else None
    except (TypeError, ValueError):
        game_id = None

    if game_id:
        if get_user_team_for_game(user.id, game_id):
            return {"msg": "您已在本赛事有队伍，请先离开当前队伍再创建"}, 409
        game = CtfGame.query.get(game_id)
        if not game:
            return {"msg": "赛事不存在"}, 404
    elif user.team_id:
        return {"msg": "您已在队伍中，请先离开当前队伍再创建新队伍"}, 409

    name_q = Team.query.filter_by(name=name)
    if game_id is not None:
        name_q = name_q.filter((Team.game_id == game_id) | Team.game_id.is_(None))
    if name_q.first():
        return {"msg": "队名已存在，请换一个名称"}, 409

    invite = secrets.token_urlsafe(16)
    school = (data.get("school") or "").strip() or None
    tag = (data.get("tag") or "").strip() or None
    if school and len(school) > 128:
        return {"msg": "所属组织过长（最多 128 字）"}, 400
    if tag and len(tag) > 64:
        return {"msg": "标签过长（最多 64 字）"}, 400
    team = Team(name=name, invite_code=invite, school=school, tag=tag, game_id=game_id)
    extensions.db.session.add(team)
    extensions.db.session.flush()

    if game_id:
        participation = CtfParticipation(
            game_id=game_id, team_id=team.id, status="confirmed",
        )
        extensions.db.session.add(participation)
        extensions.db.session.flush()
        extensions.db.session.add(CtfParticipatingUser(
            user_id=user.id,
            game_id=game_id,
            team_id=team.id,
            participation_id=participation.id,
        ))
    user.team_id = team.id
    extensions.db.session.add(user)
    extensions.db.session.commit()

    team_data = _team_dict(team, include_private=True)
    return {
        "code": 201,
        "msg": "团队创建成功，您已自动加入",
        "invite_code": invite,
        "data": {
            "team_id": team.id,
            "team_name": team.name,
            "invite_code": invite,
            "members": [{"id": user.id, "nickname": user.nickname}],
            "team": team_data,
        },
    }, 201


@bp.post("/join")
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60, error_message="加入队伍过于频繁，请稍后再试")
def join_team():
    """加入战队 - 使用邀请码"""
    data = request.get_json() or {}
    code = data.get("invite_code")
    
    if not code:
        return {
            "code": 400,
            "msg": "邀请码不能为空"
        }, 400
    
    team = Team.query.filter_by(invite_code=code).first()
    if not team:
        return {
            "code": 404,
            "msg": "邀请码无效或已过期"
        }, 404

    game_id = data.get("game_id")
    try:
        game_id = int(game_id) if game_id is not None else None
    except (TypeError, ValueError):
        game_id = None
    if game_id and team.game_id and team.game_id != game_id:
        return {"code": 400, "msg": "该邀请码不属于当前赛事"}, 400
    if game_id is None and team.game_id:
        game_id = team.game_id
    
    user = _current_user()
    if not user:
        return {
            "code": 401,
            "msg": "用户不存在"
        }, 401

    if game_id:
        if user_in_team_for_game(user.id, team.id, game_id):
            return {"code": 200, "msg": "您已在该团队中"}, 200
        existing = get_user_team_for_game(user.id, game_id)
        if existing and existing.id != team.id:
            return {
                "code": 409,
                "msg": f"您已在赛事队伍「{existing.name}」中，请先离开再加入其他队伍",
            }, 409
    elif user.team_id:
        if user.team_id == team.id:
            return {"code": 200, "msg": "您已在该团队中"}, 200
        return {
            "code": 409,
            "msg": f"您已在{user.team.name}中，无法同时加入多个团队",
        }, 409

    if game_id:
        participation = CtfParticipation.query.filter_by(
            game_id=game_id, team_id=team.id,
        ).first()
        if not participation:
            participation = CtfParticipation(
                game_id=game_id, team_id=team.id, status="confirmed",
            )
            extensions.db.session.add(participation)
            extensions.db.session.flush()
        extensions.db.session.add(CtfParticipatingUser(
            user_id=user.id,
            game_id=game_id,
            team_id=team.id,
            participation_id=participation.id,
        ))

    user.team_id = team.id
    extensions.db.session.add(user)
    extensions.db.session.commit()
    
    return {
        "code": 200,
        "msg": "加入团队成功",
        "data": {
            "team_id": team.id,
            "team_name": team.name,
            "members_count": len(team.users)
        }
    }, 200


def _team_dict(team, game_id=None, include_private=False):
    members = []
    for u in team.users:
        m = {
            "id": u.id,
            "nickname": u.nickname,
            "username": u.username,
            "school": u.school,
        }
        if include_private:
            m["email"] = u.email
        members.append(m)
    # 优先队伍自填组织；旧数据回落成员个人 school
    school = (getattr(team, "school", None) or "").strip() or None
    if not school:
        for m in members:
            if m.get("school"):
                school = m["school"]
                break
    data = {
        "id": team.id,
        "name": team.name,
        "members": members,
        "members_count": len(members),
        "school": school or "无组织",
        "tag": (getattr(team, "tag", None) or "") or "",
    }
    if include_private:
        data["invite_code"] = team.invite_code
    if game_id:
        part = CtfParticipation.query.filter_by(team_id=team.id, game_id=game_id).first()
        data["in_game"] = bool(part)
    return data


@bp.get("/me")
@jwt_required()
def my_team():
    user = _current_user()
    game_id = request.args.get("game_id", type=int)
    if not user:
        return {"team": None, "in_game": False}

    team = None
    if game_id:
        team = get_user_team_for_game(user.id, game_id)
    if not team and user.team:
        team = user.team

    if not team:
        return {"team": None, "in_game": False}

    in_game = True
    if game_id:
        pu = CtfParticipatingUser.query.filter_by(user_id=user.id, game_id=game_id).first()
        in_game = bool(pu)

    data = _team_dict(team, game_id, include_private=True)
    data["in_game"] = in_game
    return {"team": data, "in_game": in_game}


@bp.get("/")
@jwt_required()
def list_teams():
    """列出战队。未带 game_id 时仅返回公开摘要（无成员花名册）；
    带 game_id 时仅管理员可看完整参赛名单。
    """
    game_id = request.args.get("game_id", type=int)
    user = _current_user()
    if game_id:
        if not user or not user.is_admin:
            return {"code": 403, "msg": "公开队伍列表仅管理员可见", "teams": []}, 403
        parts = CtfParticipation.query.filter_by(game_id=game_id).all()
        team_ids = [p.team_id for p in parts if p.team_id]
        teams = Team.query.filter(Team.id.in_(team_ids)).order_by(Team.id.asc()).all() if team_ids else []
        result = [_team_dict(t, game_id) for t in teams]
        return {"teams": result}
    # 全站列表：仅摘要，防止未鉴权枚举成员
    teams = Team.query.order_by(Team.id.asc()).all()
    result = [
        {
            "id": t.id,
            "name": t.name,
            "members_count": len(t.users or []),
            "school": (getattr(t, "school", None) or "") or "无组织",
            "tag": (getattr(t, "tag", None) or "") or "",
        }
        for t in teams
    ]
    return {"teams": result}


@bp.get("/<int:team_id>")
@jwt_required()
def get_team(team_id):
    """获取指定战队详情：仅本队成员或管理员可见完整成员列表。"""
    user = _current_user()
    team = Team.query.get(team_id)
    if not team:
        return {"msg": "team not found"}, 404
    game_id = request.args.get("game_id", type=int)
    is_member = bool(user and user.team_id == team_id)
    is_admin = bool(user and user.is_admin)
    if not is_member and not is_admin:
        return {
            "id": team.id,
            "name": team.name,
            "members_count": len(team.users or []),
            "school": (getattr(team, "school", None) or "") or "无组织",
            "tag": (getattr(team, "tag", None) or "") or "",
        }
    return _team_dict(team, game_id, include_private=is_member or is_admin)


@bp.patch("/<int:team_id>")
@jwt_required()
def update_team(team_id):
    """更新队伍信息（仅队员可操作）"""
    user = _current_user()
    team = Team.query.get(team_id)
    if not team:
        return {"msg": "team not found"}, 404
    if not user or user.team_id != team_id:
        return {"msg": "forbidden"}, 403
    data = request.get_json() or {}
    if "name" in data and data["name"]:
        new_name = data["name"].strip()
        ok, err = assert_clean_team_name(new_name)
        if not ok:
            return {"msg": err}, 400
        existing = Team.query.filter(Team.name == new_name, Team.id != team_id).first()
        if existing:
            return {"msg": "队名已存在"}, 409
        team.name = new_name
    if "school" in data:
        school = (data.get("school") or "").strip()
        if len(school) > 128:
            return {"msg": "所属组织过长（最多 128 字）"}, 400
        team.school = school or None
    if "tag" in data:
        tag = (data.get("tag") or "").strip()
        if len(tag) > 64:
            return {"msg": "标签过长（最多 64 字）"}, 400
        team.tag = tag or None
    extensions.db.session.commit()
    return {"msg": "ok", "data": _team_dict(team, include_private=True)}


@bp.post("/<int:team_id>/leave")
@jwt_required()
def leave_team(team_id):
    """离开队伍（同步清理赛内参赛归属，避免计分错位）"""
    user = _current_user()
    if not user or user.team_id != team_id:
        return {"msg": "forbidden"}, 403
    _drop_user_game_membership(user.id)
    user.team_id = None
    extensions.db.session.add(user)
    extensions.db.session.commit()
    return {"msg": "已离开队伍"}


@bp.get("/<int:team_id>/solves")
def team_solves(team_id):
    """队伍解题时间线（含一二三血标记；points 为当前动态分+血奖）"""
    game_id = request.args.get("game_id", type=int)
    if not game_id:
        return {"msg": "missing game_id"}, 400
    team = Team.query.get(team_id)
    if not team:
        return {"msg": "team not found"}, 404
    rows = (
        CtfChallengeSubmission.query.filter_by(
            team_id=team_id, game_id=game_id, is_correct=True,
        )
        .order_by(CtfChallengeSubmission.submitted_at.asc())
        .all()
    )
    blood_rows = CtfSolves.query.filter_by(game_id=game_id, team_id=team_id).all()
    blood_by_ch = {
        int(b.challenge_id): int(b.blood_level)
        for b in blood_rows
        if b.blood_level is not None and int(b.blood_level) <= 2
    }
    blood_labels = ("一血", "二血", "三血")

    solves = []
    seen_ch = set()
    for r in rows:
        if r.challenge_id in seen_ch:
            continue
        seen_ch.add(r.challenge_id)
        ch = CtfChallenge.query.get(r.challenge_id)
        u = User.query.get(r.user_id)
        level = blood_by_ch.get(int(r.challenge_id))
        solves.append({
            "id": r.id,
            "challenge_id": r.challenge_id,
            "challenge_title": ch.title if ch else "未知题目",
            "nickname": u.nickname if u else "用户",
            "points": r.points_earned or (ch.points if ch else 0),
            "blood_level": level,
            "blood_label": blood_labels[level] if level is not None else None,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        })
    return {"solves": solves}


@bp.get("/<int:team_id>/score-timeline")
def team_score_timeline(team_id):
    """队伍积分走势：ret2shell Snapshot Replay（允许下挫，禁止累加 points_earned）。"""
    game_id = request.args.get("game_id", type=int)
    if not game_id:
        return {"msg": "missing game_id"}, 400

    from backend.services.scoring_service import ScoringService

    payload = ScoringService.get_timeline_cached(game_id, top_n=10)
    td = (payload.get("timeline_data") or {}).get(str(team_id))
    if not td:
        # 缓存 TopN 可能不含该队：强制全量重演一次
        payload = ScoringService.generate_gzctf_style_timeline(game_id, top_n=10_000)
        td = (payload.get("timeline_data") or {}).get(str(team_id))

    if not td:
        return {
            "timeline": [{"time": None, "points": 0}],
            "total": 0,
            "algorithm": payload.get("algorithm") or "ret2shell_history_replay",
        }

    timeline = [{"time": None, "points": 0}] + [
        {"time": p[0], "points": p[1], "challenge": None} for p in td
    ]
    return {
        "timeline": timeline,
        "total": int(td[-1][1] if td else 0),
        "algorithm": payload.get("algorithm") or "ret2shell_snapshot_replay",
    }


@bp.get('/admin')
@jwt_required()
def admin_list_teams():
    """管理员：列出队伍及成员；?game_id= 时仅该赛参赛队。"""
    user = _current_user()
    if not user or not user.is_admin:
        return {"msg": "forbidden"}, 403
    game_id = request.args.get("game_id", type=int)
    if game_id:
        parts = CtfParticipation.query.filter_by(game_id=game_id).all()
        team_ids = [p.team_id for p in parts if p.team_id]
        teams = (
            Team.query.filter(Team.id.in_(team_ids)).order_by(Team.id.asc()).all()
            if team_ids else []
        )
    else:
        teams = Team.query.order_by(Team.id.asc()).all()
    out = []
    for t in teams:
        members = [
            {
                "id": u.id,
                "nickname": u.nickname,
                "username": u.username,
                "email": u.email,
                "school": u.school,
            }
            for u in t.users
        ]
        row = {
            "id": t.id,
            "name": t.name,
            "invite_code": t.invite_code,
            "school": getattr(t, "school", None) or "无组织",
            "members": members,
            "members_count": len(members),
        }
        if game_id:
            row["game_id"] = game_id
            row["in_game"] = True
        out.append(row)
    return {"teams": out, "game_id": game_id}


def _ensure_team_participation(team_id, game_id):
    """保证队伍在比赛中有 participation 行，返回该行。"""
    part = CtfParticipation.query.filter_by(team_id=team_id, game_id=game_id).first()
    if part:
        return part
    part = CtfParticipation(team_id=team_id, game_id=game_id)
    extensions.db.session.add(part)
    extensions.db.session.flush()
    return part


def _sync_user_game_membership(user, new_team_id, game_id=None):
    """把选手的赛内参赛记录同步到新队伍。game_id 为空则同步其所有参赛赛。"""
    q = CtfParticipatingUser.query.filter_by(user_id=user.id)
    if game_id:
        q = q.filter_by(game_id=game_id)
    rows = q.all()
    for pu in rows:
        part = _ensure_team_participation(new_team_id, pu.game_id)
        pu.team_id = new_team_id
        pu.participation_id = part.id


def _drop_user_game_membership(user_id, game_id=None):
    q = CtfParticipatingUser.query.filter_by(user_id=user_id)
    if game_id:
        q = q.filter_by(game_id=game_id)
    q.delete(synchronize_session=False)


@bp.post('/admin/members/<int:user_id>/kick')
@jwt_required()
def admin_kick_member(user_id):
    """管理员：将选手移出当前队伍（可选仅清某赛参赛）。"""
    admin = _current_user()
    if not admin or not admin.is_admin:
        return {"msg": "forbidden"}, 403
    data = request.get_json() or {}
    game_id = data.get("game_id")
    if game_id is not None:
        try:
            game_id = int(game_id)
        except (TypeError, ValueError):
            return {"msg": "game_id 无效"}, 400

    target = User.query.get(user_id)
    if not target:
        return {"msg": "用户不存在"}, 404
    if not target.team_id:
        return {"msg": "该用户当前不在任何队伍"}, 400

    old_team_id = target.team_id
    try:
        if game_id:
            # 仅解除某场比赛报名；仍留在队伍里
            _drop_user_game_membership(target.id, game_id)
        else:
            _drop_user_game_membership(target.id, None)
            target.team_id = None
            extensions.db.session.add(target)
        extensions.db.session.commit()
        return {
            "code": 200,
            "msg": "已移出" if not game_id else "已取消该赛报名",
            "data": {"user_id": user_id, "old_team_id": old_team_id, "game_id": game_id},
        }
    except Exception as e:
        extensions.db.session.rollback()
        return {"msg": f"操作失败: {e}"}, 500


@bp.post('/admin/members/<int:user_id>/transfer')
@jwt_required()
def admin_transfer_member(user_id):
    """管理员：把选手转到另一支队伍（可按队伍 ID 或邀请码）。"""
    admin = _current_user()
    if not admin or not admin.is_admin:
        return {"msg": "forbidden"}, 403
    data = request.get_json() or {}
    target_team_id = data.get("team_id") or data.get("target_team_id")
    invite_code = (data.get("invite_code") or "").strip() or None
    game_id = data.get("game_id")
    if game_id is not None:
        try:
            game_id = int(game_id)
        except (TypeError, ValueError):
            return {"msg": "game_id 无效"}, 400

    target = User.query.get(user_id)
    if not target:
        return {"msg": "用户不存在"}, 404

    new_team = None
    if target_team_id is not None:
        try:
            new_team = Team.query.get(int(target_team_id))
        except (TypeError, ValueError):
            return {"msg": "team_id 无效"}, 400
    elif invite_code:
        new_team = Team.query.filter_by(invite_code=invite_code).first()
    else:
        return {"msg": "请提供目标 team_id 或 invite_code"}, 400

    if not new_team:
        return {"msg": "目标队伍不存在"}, 404
    if target.team_id == new_team.id:
        return {"msg": "用户已在该队伍中"}, 200

    old_team_id = target.team_id
    try:
        target.team_id = new_team.id
        extensions.db.session.add(target)
        _sync_user_game_membership(target, new_team.id, game_id)
        # 若指定了比赛且该队尚未参赛，确保报名
        if game_id:
            part = _ensure_team_participation(new_team.id, game_id)
            pu = CtfParticipatingUser.query.filter_by(user_id=target.id, game_id=game_id).first()
            if not pu:
                pu = CtfParticipatingUser(
                    user_id=target.id,
                    game_id=game_id,
                    team_id=new_team.id,
                    participation_id=part.id,
                )
                extensions.db.session.add(pu)
            else:
                pu.team_id = new_team.id
                pu.participation_id = part.id
        extensions.db.session.commit()
        return {
            "code": 200,
            "msg": f"已将用户转移到 {new_team.name}",
            "data": {
                "user_id": user_id,
                "old_team_id": old_team_id,
                "new_team_id": new_team.id,
                "new_team_name": new_team.name,
                "game_id": game_id,
            },
        }
    except Exception as e:
        extensions.db.session.rollback()
        return {"msg": f"转移失败: {e}"}, 500


def _cleanup_team_data(team_id):
    """清理队伍关联数据，避免外键约束导致删除失败"""
    CtfParticipatingUser.query.filter_by(team_id=team_id).delete()
    CtfParticipation.query.filter_by(team_id=team_id).delete()
    CtfScoreboard.query.filter_by(team_id=team_id).delete()
    CtfChallengeSubmission.query.filter_by(team_id=team_id).update({"team_id": None})
    CtfGameInstance.query.filter_by(team_id=team_id).update({"team_id": None})
    CtfSolves.query.filter_by(team_id=team_id).delete()
    TeamSeasonStats.query.filter_by(team_id=team_id).delete()
    PcapCapture.query.filter_by(team_id=team_id).delete()

    session = extensions.db.session
    for sql in (
        "DELETE FROM first_solve WHERE team_id = :team_id",
        "DELETE FROM scoreboard WHERE team_id = :team_id",
        "DELETE FROM user_participation WHERE team_id = :team_id",
        "DELETE FROM traffic_capture WHERE team_id = :team_id",
        "UPDATE game_submission SET team_id = NULL WHERE team_id = :team_id",
        "UPDATE challenge_submission SET team_id = NULL WHERE team_id = :team_id",
        "UPDATE game_instance SET team_id = NULL WHERE team_id = :team_id",
        "UPDATE participation SET team_id = NULL WHERE team_id = :team_id",
        "UPDATE package_assignment SET team_id = NULL WHERE team_id = :team_id",
        "UPDATE package_download_log SET team_id = NULL WHERE team_id = :team_id",
        "UPDATE container_log_snapshot SET team_id = NULL WHERE team_id = :team_id",
    ):
        try:
            session.execute(text(sql), {"team_id": team_id})
        except Exception:
            pass


@bp.delete('/admin/<int:team_id>')
@jwt_required()
def admin_delete_team(team_id):
    """管理员：删除指定队伍（解散）"""
    user = _current_user()
    if not user or not user.is_admin:
        return {"msg": "forbidden"}, 403
    team = Team.query.get(team_id)
    if not team:
        return {"msg": "team not found"}, 404
    try:
        _cleanup_team_data(team_id)
        for u in list(team.users):
            u.team = None
        extensions.db.session.delete(team)
        extensions.db.session.commit()
        return {"msg": "deleted"}
    except Exception as e:
        extensions.db.session.rollback()
        return {"msg": f"delete failed: {e}"}, 500


@bp.delete('/admin')
@jwt_required()
def admin_delete_all():
    """管理员：删除所有队伍（解散）"""
    user = _current_user()
    if not user or not user.is_admin:
        return {"msg": "forbidden"}, 403
    teams = Team.query.all()
    count = 0
    try:
        for t in teams:
            _cleanup_team_data(t.id)
            for u in list(t.users):
                u.team = None
            extensions.db.session.delete(t)
            count += 1
        extensions.db.session.commit()
        return {"deleted": count, "msg": "ok"}
    except Exception as e:
        extensions.db.session.rollback()
        return {"msg": f"delete failed: {e}", "deleted": 0}, 500