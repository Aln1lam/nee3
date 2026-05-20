from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.server import extensions
from backend.server.db_models import (
    User, Team, CtfParticipation, CtfParticipatingUser, CtfScoreboard,
    CtfChallengeSubmission, CtfGameInstance, CtfSolves
)
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
    name = data.get("name")
    if not name:
        return {"msg": "missing name"}, 400
    if Team.query.filter_by(name=name).first():
        return {"msg": "name exists"}, 409
    
    # 创建团队
    invite = secrets.token_hex(4)
    team = Team(name=name, invite_code=invite)
    extensions.db.session.add(team)
    extensions.db.session.flush()  # 获取团队ID
    
    # ✓ 创建者自动加入团队
    user = _current_user()
    if user:
        user.team_id = team.id
        extensions.db.session.add(user)
    
    extensions.db.session.commit()
    
    return {
        "code": 200,
        "msg": "团队创建成功，您已自动加入",
        "data": {
            "team_id": team.id,
            "team_name": team.name,
            "invite_code": invite,
            "members": [{"id": user.id, "nickname": user.nickname}] if user else []
        }
    }, 201


@bp.post("/join")
@jwt_required()
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


@bp.get("/me")
@jwt_required()
def my_team():
    user = _current_user()
    if not user or not user.team:
        return {"team": None}
    team = user.team
    members = [{"id": u.id, "nickname": u.nickname, "email": u.email} for u in team.users]
    return {"id": team.id, "name": team.name, "invite_code": team.invite_code, "members": members}


@bp.get("/")
def list_teams():
    """列出所有已创建的战队（公共接口）"""
    teams = Team.query.order_by(Team.id.asc()).all()
    result = [{"id": t.id, "name": t.name} for t in teams]
    return {"teams": result}


@bp.get("/<int:team_id>")
def get_team(team_id):
    """获取指定战队的详细信息（包含成员）"""
    team = Team.query.get(team_id)
    if not team:
        return {"msg": "team not found"}, 404
    members = [{"id": u.id, "nickname": u.nickname, "email": u.email} for u in team.users]
    return {"id": team.id, "name": team.name, "invite_code": team.invite_code, "members": members}


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
    # 清理与队伍关联的数据，避免外键约束
    CtfParticipatingUser.query.filter_by(team_id=team_id).delete()
    CtfParticipation.query.filter_by(team_id=team_id).delete()
    CtfScoreboard.query.filter_by(team_id=team_id).delete()
    CtfChallengeSubmission.query.filter_by(team_id=team_id).update({"team_id": None})
    CtfGameInstance.query.filter_by(team_id=team_id).update({"team_id": None})
    CtfSolves.query.filter_by(team_id=team_id).update({"team_id": None})
    try:
        extensions.db.session.execute(text("DELETE FROM first_solve WHERE team_id = :team_id"), {"team_id": team_id})
    except Exception:
        # 忽略不存在的表或删除失败
        pass
    for u in list(team.users):
        u.team = None
    extensions.db.session.delete(team)
    extensions.db.session.commit()
    return {"msg": "deleted"}


@bp.delete('/admin')
@jwt_required()
def admin_delete_all():
    """管理员：删除所有队伍（解散）"""
    user = _current_user()
    if not user or not user.is_admin:
        return {"msg": "forbidden"}, 403
    teams = Team.query.all()
    count = 0
    for t in teams:
        # 清理与队伍关联的数据，避免外键约束
        CtfParticipatingUser.query.filter_by(team_id=t.id).delete()
        CtfParticipation.query.filter_by(team_id=t.id).delete()
        CtfScoreboard.query.filter_by(team_id=t.id).delete()
        CtfChallengeSubmission.query.filter_by(team_id=t.id).update({"team_id": None})
        CtfGameInstance.query.filter_by(team_id=t.id).update({"team_id": None})
        CtfSolves.query.filter_by(team_id=t.id).update({"team_id": None})
        try:
            extensions.db.session.execute(text("DELETE FROM first_solve WHERE team_id = :team_id"), {"team_id": t.id})
        except Exception:
            pass
        for u in list(t.users):
            u.team = None
        extensions.db.session.delete(t)
        count += 1
    extensions.db.session.commit()
    return {"deleted": count}