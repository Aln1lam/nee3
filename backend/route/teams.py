from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.server import extensions
from backend.server.db_models import (
    User, Team, CtfParticipation, CtfParticipatingUser, CtfScoreboard,
    CtfChallengeSubmission, CtfGameInstance, CtfSolves, CtfChallenge, CtfGame,
    TeamSeasonStats, PcapCapture,
)
from backend.services.sensitive_words import assert_clean_team_name
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
    if user.team_id:
        return {"msg": "您已在队伍中，请先离开当前队伍再创建新队伍"}, 409

    if Team.query.filter_by(name=name).first():
        return {"msg": "队名已存在，请换一个名称"}, 409

    # ~22 chars URL-safe，远高于旧 token_hex(4)
    invite = secrets.token_urlsafe(16)
    team = Team(name=name, invite_code=invite)
    extensions.db.session.add(team)
    extensions.db.session.flush()

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
    
    user = _current_user()
    if not user:
        return {
            "code": 401,
            "msg": "用户不存在"
        }, 401
    
    # 检查用户是否已经在某个团队中
    if user.team_id:
        if user.team_id == team.id:
            return {
                "code": 200,
                "msg": "您已在该团队中"
            }, 200
        else:
            return {
                "code": 409,
                "msg": f"您已在{user.team.name}中，无法同时加入多个团队"
            }, 409
    
    # 加入团队
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
    school = None
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
    if not user or not user.team:
        return {"team": None, "in_game": False}

    team = user.team
    in_game = True
    if game_id:
        part = CtfParticipation.query.filter_by(team_id=team.id, game_id=game_id).first()
        pu = CtfParticipatingUser.query.filter_by(user_id=user.id, game_id=game_id).first()
        in_game = bool(part or pu)

    data = _team_dict(team, game_id, include_private=True)
    data["in_game"] = in_game
    return {"team": data, "in_game": in_game}


@bp.get("/")
def list_teams():
    """列出战队；?game_id= 时仅返回参赛队伍"""
    game_id = request.args.get("game_id", type=int)
    if game_id:
        parts = CtfParticipation.query.filter_by(game_id=game_id).all()
        team_ids = [p.team_id for p in parts if p.team_id]
        teams = Team.query.filter(Team.id.in_(team_ids)).order_by(Team.id.asc()).all() if team_ids else []
        result = [_team_dict(t, game_id) for t in teams]
        return {"teams": result}
    teams = Team.query.order_by(Team.id.asc()).all()
    result = [_team_dict(t) for t in teams]
    return {"teams": result}


@bp.get("/<int:team_id>")
def get_team(team_id):
    """获取指定战队的详细信息（包含成员）"""
    team = Team.query.get(team_id)
    if not team:
        return {"msg": "team not found"}, 404
    game_id = request.args.get("game_id", type=int)
    return _team_dict(team, game_id)


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
    extensions.db.session.commit()
    return {"msg": "ok", "data": _team_dict(team, include_private=True)}


@bp.post("/<int:team_id>/leave")
@jwt_required()
def leave_team(team_id):
    """离开队伍"""
    user = _current_user()
    if not user or user.team_id != team_id:
        return {"msg": "forbidden"}, 403
    user.team_id = None
    extensions.db.session.add(user)
    extensions.db.session.commit()
    return {"msg": "已离开队伍"}


@bp.get("/<int:team_id>/solves")
def team_solves(team_id):
    """队伍解题时间线"""
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
    solves = []
    for r in rows:
        ch = CtfChallenge.query.get(r.challenge_id)
        u = User.query.get(r.user_id)
        solves.append({
            "id": r.id,
            "challenge_id": r.challenge_id,
            "challenge_title": ch.title if ch else "未知题目",
            "nickname": u.nickname if u else "用户",
            "points": r.points_earned or (ch.points if ch else 0),
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        })
    return {"solves": solves}


@bp.get("/<int:team_id>/score-timeline")
def team_score_timeline(team_id):
    """队伍累计得分曲线数据"""
    game_id = request.args.get("game_id", type=int)
    if not game_id:
        return {"msg": "missing game_id"}, 400
    rows = (
        CtfChallengeSubmission.query.filter_by(
            team_id=team_id, game_id=game_id, is_correct=True,
        )
        .order_by(CtfChallengeSubmission.submitted_at.asc())
        .all()
    )
    points = 0
    timeline = [{"time": None, "points": 0}]
    for r in rows:
        ch = CtfChallenge.query.get(r.challenge_id)
        earned = r.points_earned or (ch.points if ch else 0)
        points += earned
        timeline.append({
            "time": r.submitted_at.isoformat() if r.submitted_at else None,
            "points": points,
            "challenge": ch.title if ch else None,
        })
    return {"timeline": timeline, "total": points}


@bp.get('/admin')
@jwt_required()
def admin_list_teams():
    """管理员：列出所有队伍及成员"""
    user = _current_user()
    if not user or not user.is_admin:
        return {"msg": "forbidden"}, 403
    teams = Team.query.order_by(Team.id.asc()).all()
    out = []
    for t in teams:
        members = [{"id": u.id, "nickname": u.nickname, "email": u.email} for u in t.users]
        out.append({"id": t.id, "name": t.name, "invite_code": t.invite_code, "members": members})
    return {"teams": out}


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