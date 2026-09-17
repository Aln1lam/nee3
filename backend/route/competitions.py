"""
CTF 竞赛/游戏相关的API路由
"""
import secrets
from flask import Blueprint, request, jsonify, send_file, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, verify_jwt_in_request
from datetime import datetime
from sqlalchemy import func, or_
from backend.server.extensions import db
from backend.server.db_models import (
    User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
    CtfParticipation, CtfParticipatingUser, CtfScoreboard, CtfDivision,
    CtfUserInviteCode, CtfCheatInfo,
)
from backend.server.game_filters import is_ephemeral_test_game
from backend.services.traffic_capture_service import TrafficCaptureService
from backend.services.team_service import ensure_user_has_team, user_joined_game
from backend.services.game_delete_service import purge_game

bp = Blueprint("competitions", __name__)


# ======================== 竞赛列表 ========================

def _is_training_game(game):
    return game.game_type in ("training", "practice") or game.status == "archived"


def _current_user_id():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        return int(uid) if uid is not None else None
    except Exception:
        return None


def _require_admin_user():
    uid = get_jwt_identity()
    user = User.query.get(int(uid)) if uid is not None else None
    if not user or not user.is_admin:
        return None, (jsonify({"code": 403, "msg": "无权操作"}), 403)
    return user, None


def _require_staff_user():
    """管理员或协管"""
    uid = get_jwt_identity()
    user = User.query.get(int(uid)) if uid is not None else None
    if not user or not (user.is_admin or getattr(user, "is_moderator", False)):
        return None, (jsonify({"code": 403, "msg": "需要管理员或协管权限"}), 403)
    return user, None


def _can_view_game(game, user_id=None):
    if game.is_public:
        return True
    if _is_training_game(game):
        return True
    if user_id:
        user = User.query.get(user_id)
        if user and user.is_admin:
            return True
        joined = CtfParticipatingUser.query.filter_by(
            user_id=user_id, game_id=game.id
        ).first()
        if joined:
            return True
    return False


def _gen_unique_invite_code(length=16):
    """生成全局唯一的分组邀请码（默认 16 位）。"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(12):
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        if not CtfDivision.query.filter_by(invite_code=code).first():
            return code
    return secrets.token_hex(8).upper()  # 16 hex chars fallback


def _ensure_campus_invite_division(game):
    """非公开赛：保证至少有一个带邀请码的分组，供学生端报名使用。"""
    if not game or game.is_public:
        return None

    with_code = (
        CtfDivision.query.filter_by(game_id=game.id)
        .filter(CtfDivision.invite_code.isnot(None))
        .filter(CtfDivision.invite_code != "")
        .order_by(CtfDivision.id.asc())
        .first()
    )
    if with_code:
        return with_code

    bare = (
        CtfDivision.query.filter_by(game_id=game.id)
        .order_by(CtfDivision.id.asc())
        .first()
    )
    if bare:
        bare.invite_code = _gen_unique_invite_code()
        if not (bare.name or "").strip():
            bare.name = "校内赛道"
        db.session.flush()
        return bare

    div = CtfDivision(
        game_id=game.id,
        name="校内赛道",
        invite_code=_gen_unique_invite_code(),
        description="校内赛报名邀请码（创建非公开赛时自动生成）",
        sort_order=0,
    )
    db.session.add(div)
    db.session.flush()
    return div


def _campus_invite_payload(game):
    """管理员可见：非公开赛的邀请码列表。"""
    if not game or game.is_public:
        return [], None
    rows = (
        CtfDivision.query.filter_by(game_id=game.id)
        .order_by(CtfDivision.sort_order.asc(), CtfDivision.id.asc())
        .all()
    )
    codes = []
    for d in rows:
        code = (d.invite_code or "").strip()
        if not code:
            continue
        codes.append({
            "division_id": d.id,
            "name": d.name,
            "invite_code": code,
        })
    primary = codes[0]["invite_code"] if codes else None
    return codes, primary


def _attach_admin_invite_fields(game_dict, game):
    codes, primary = _campus_invite_payload(game)
    game_dict["campus_invite_codes"] = codes
    game_dict["primary_invite_code"] = primary
    return game_dict


@bp.route("/", methods=["GET"])
def get_games():
    """获取所有竞赛（包括公开和非公开）

    查询参数:
    - game_type: official | training | practice | archived
    - exclude_training: true 时排除训练/练习场
    - include_ephemeral: true 时保留 E2E/探针临时赛（默认对学生端隐藏）
    """
    try:
        game_type = (request.args.get("game_type") or "").strip().lower()
        exclude_training = request.args.get("exclude_training", "").lower() in ("true", "1", "yes")
        include_ephemeral = request.args.get("include_ephemeral", "").lower() in ("true", "1", "yes")

        query = CtfGame.query
        if game_type == "official":
            query = query.filter(
                CtfGame.game_type == "official",
                CtfGame.status != "archived",
            )
        elif game_type in ("training", "practice"):
            query = query.filter(CtfGame.game_type.in_(["training", "practice"]))
        elif game_type == "archived":
            query = query.filter(CtfGame.status == "archived")
        elif exclude_training:
            query = query.filter(
                ~CtfGame.game_type.in_(["training", "practice"]),
                CtfGame.status != "archived",
            )

        games = query.order_by(CtfGame.start_time.desc()).all()
        user_id = _current_user_id()
        is_admin = False
        if user_id:
            admin_user = User.query.get(user_id)
            is_admin = bool(admin_user and admin_user.is_admin)
        if not include_ephemeral:
            games = [g for g in games if not is_ephemeral_test_game(g)]

        # Batch counts — avoid N+1 when listing many competitions
        game_ids = [g.id for g in games]
        challenge_counts = {}
        participation_counts = {}
        if game_ids:
            challenge_counts = dict(
                db.session.query(CtfChallenge.game_id, func.count(CtfChallenge.id))
                .filter(CtfChallenge.game_id.in_(game_ids), CtfChallenge.is_enabled.is_(True))
                .group_by(CtfChallenge.game_id)
                .all()
            )
            participation_counts = dict(
                db.session.query(
                    CtfParticipatingUser.game_id,
                    func.count(func.distinct(CtfParticipatingUser.user_id)),
                )
                .filter(CtfParticipatingUser.game_id.in_(game_ids))
                .group_by(CtfParticipatingUser.game_id)
                .all()
            )

        data = []
        for game in games:
            if not _can_view_game(game, user_id):
                continue
            game_dict = game.to_dict()
            game_dict['challenge_count'] = int(challenge_counts.get(game.id, 0))
            game_dict['participation_count'] = int(participation_counts.get(game.id, 0))
            # 管理端需要直接看到校内邀请码（非公开赛）
            if is_admin and not game.is_public:
                _attach_admin_invite_fields(game_dict, game)
            data.append(game_dict)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:game_id>", methods=["GET"])
def get_game(game_id):
    """获取竞赛详情"""
    try:
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        if not _can_view_game(game, _current_user_id()):
            return jsonify({"code": 403, "msg": "竞赛不公开"}), 403

        data = game.to_dict()
        
        # 获取题目数量
        challenge_count = CtfChallenge.query.filter_by(
            game_id=game_id, is_enabled=True
        ).count()
        data['challenge_count'] = challenge_count

        # 获取参赛队伍数
        participation_count = CtfParticipation.query.filter_by(
            game_id=game_id
        ).count()
        data['participation_count'] = participation_count

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 竞赛参赛 ========================

@bp.route("/<int:game_id>/training-join", methods=["POST"])
@jwt_required()
def training_join(game_id):
    """训练场自动加入 — 无队伍时自动创建单人队"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "练习场不存在"}), 404

        if not _is_training_game(game):
            return jsonify({"code": 400, "msg": "该比赛不是训练/练习场"}), 400

        team = ensure_user_has_team(user)
        if not team:
            return jsonify({"code": 500, "msg": "创建单人队伍失败"}), 500
        team_id = team.id

        existing = CtfParticipatingUser.query.filter_by(
            user_id=user_id, game_id=game_id
        ).first()
        if existing:
            return jsonify({"code": 200, "msg": "已加入", "data": {"game_id": game_id}}), 200

        participation = CtfParticipation.query.filter_by(
            game_id=game_id, team_id=team_id
        ).first()
        if not participation:
            participation = CtfParticipation(
                game_id=game_id,
                team_id=team_id,
                status="confirmed",
            )
            db.session.add(participation)
            db.session.flush()

            for member in team.users:
                db.session.add(CtfParticipatingUser(
                    user_id=member.id,
                    game_id=game_id,
                    team_id=team_id,
                    participation_id=participation.id,
                ))

            db.session.add(CtfScoreboard(
                game_id=game_id,
                team_id=team_id,
                total_points=0,
                solved_challenges=0,
            ))
        else:
            user_part = CtfParticipatingUser.query.filter_by(
                user_id=user_id, game_id=game_id, team_id=team_id
            ).first()
            if not user_part:
                db.session.add(CtfParticipatingUser(
                    user_id=user_id,
                    game_id=game_id,
                    team_id=team_id,
                    participation_id=participation.id,
                ))

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "加入练习场成功",
            "data": {"game_id": game_id},
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:game_id>/join", methods=["POST"])
@jwt_required()
def join_game(game_id):
    """用户加入竞赛 - 以队伍身份"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        team = ensure_user_has_team(user)
        if not team:
            return jsonify({"code": 500, "msg": "创建单人队伍失败"}), 500

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        team_id = team.id
        data = request.get_json() or {}
        invite_code = (data.get("invite_code") or "").strip()
        division_id = None
        division_name = None

        # 非公开比赛需要邀请码并记录分组
        if not game.is_public:
            if not invite_code:
                return jsonify({"code": 400, "msg": "该比赛需要邀请码才能参加"}), 400

            division = CtfDivision.query.filter_by(game_id=game_id, invite_code=invite_code).first()
            if not division:
                return jsonify({"code": 400, "msg": "邀请码无效或已过期"}), 400

            # 学校范围限制
            if division.school_scope:
                if division.school_scope == "高校":
                    if user.identity not in ["student", "teacher"]:
                        return jsonify({"code": 403, "msg": "该赛道仅限高校师生参加"}), 403
                elif division.school_scope != user.school:
                    return jsonify({"code": 403, "msg": f"该邀请码仅限 {division.school_scope} 的成员使用"}), 403

            division_id = division.id
            division_name = division.name
        
        # 检查团队是否已经参加
        existing = CtfParticipation.query.filter_by(
            team_id=team_id,
            game_id=game_id
        ).first()

        if existing:
            # 如果已加入但分组不一致，拒绝
            if existing.division_id and division_id and existing.division_id != division_id:
                return jsonify({"code": 409, "msg": "该队伍已加入其他分组"}), 409

            # 已加入但此前未设置分组，补写分组信息
            if division_id and not existing.division_id:
                existing.division_id = division_id
                CtfParticipatingUser.query.filter_by(
                    game_id=game_id,
                    team_id=team_id
                ).update({"division_id": division_id})

            # 检查当前用户是否已经在 CtfParticipatingUser 中
            user_part = CtfParticipatingUser.query.filter_by(
                user_id=user_id, game_id=game_id, team_id=team_id
            ).first()
            if not user_part:
                user_part = CtfParticipatingUser(
                    user_id=user_id, game_id=game_id, team_id=team_id, participation_id=existing.id, division_id=division_id
                )
                db.session.add(user_part)

            # 记录邀请码使用
            if division_id:
                existing_code = CtfUserInviteCode.query.filter_by(
                    user_id=user_id, game_id=game_id, division_id=division_id
                ).first()
                if not existing_code:
                    invite_code_record = CtfUserInviteCode(
                        user_id=user_id,
                        game_id=game_id,
                        division_id=division_id,
                        invite_code_used=invite_code,
                        verified_at=datetime.utcnow()
                    )
                    db.session.add(invite_code_record)
            db.session.commit()
            return jsonify({
                "code": 200,
                "msg": "您所在的团队已经参加过这个竞赛",
                "division_id": existing.division_id,
                "division_name": division_name
            }), 200

        # 创建团队级参赛记录
        p = CtfParticipation(team_id=team_id, game_id=game_id, division_id=division_id, status="confirmed")
        db.session.add(p)
        db.session.flush()  # 获取参赛记录 ID
        
        # 为该团队的所有成员创建用户参赛记录
        team = Team.query.get(team_id)
        for team_member in team.users:
            user_part = CtfParticipatingUser(
                user_id=team_member.id, game_id=game_id, team_id=team_id, participation_id=p.id, division_id=division_id
            )
            db.session.add(user_part)

        # 记录邀请码使用
        if division_id:
            existing_code = CtfUserInviteCode.query.filter_by(
                user_id=user_id, game_id=game_id, division_id=division_id
            ).first()
            if not existing_code:
                invite_code_record = CtfUserInviteCode(
                    user_id=user_id,
                    game_id=game_id,
                    division_id=division_id,
                    invite_code_used=invite_code,
                    verified_at=datetime.utcnow()
                )
                db.session.add(invite_code_record)
        
        # 创建排行榜记录
        scoreboard = CtfScoreboard(
            game_id=game_id,
            team_id=team_id,
            total_points=0,
            solved_challenges=0
        )
        db.session.add(scoreboard)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "加入成功",
            "data": p.to_dict(),
            "division_id": division_id,
            "division_name": division_name
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:game_id>/leave", methods=["POST"])
@jwt_required()
def leave_game(game_id):
    """用户退出竞赛"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "code": 404,
                "msg": "您未参加过这个竞赛"
            }), 404

        user_part = CtfParticipatingUser.query.filter_by(
            user_id=user_id, game_id=game_id
        ).first()
        if not user_part:
            team = ensure_user_has_team(user, solo_if_missing=False)
            if not team:
                return jsonify({
                    "code": 404,
                    "msg": "您未参加过这个竞赛"
                }), 404
            team_id = team.id
        else:
            team_id = user_part.team_id
        
        # 查找团队的参赛记录
        participation = CtfParticipation.query.filter_by(
            team_id=team_id,
            game_id=game_id
        ).first()

        if not participation:
            return jsonify({
                "code": 404,
                "msg": "您所在的团队未参加过这个竞赛"
            }), 404

        # 删除所有团队成员的用户参赛记录
        CtfParticipatingUser.query.filter_by(
            participation_id=participation.id
        ).delete()
        
        # 删除团队的参赛记录
        db.session.delete(participation)
        
        # 删除排行榜记录
        CtfScoreboard.query.filter_by(
            team_id=team_id,
            game_id=game_id
        ).delete()

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "已退出竞赛"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/my", methods=["GET"])
@jwt_required()
def my_games():
    """获取当前用户已加入的竞赛 ID 列表"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        game_ids = set()
        if user.team_id:
            team_parts = CtfParticipation.query.filter_by(team_id=user.team_id).all()
            game_ids.update(p.game_id for p in team_parts)

        user_parts = CtfParticipatingUser.query.filter_by(user_id=user_id).all()
        game_ids.update(p.game_id for p in user_parts)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": [{"game_id": gid} for gid in sorted(game_ids)],
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:game_id>/joined", methods=["GET"])
@jwt_required()
def is_joined(game_id):
    """返回当前用户的队伍是否已加入该竞赛"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"joined": False}), 200

        return jsonify({"joined": user_joined_game(user_id, game_id)}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/debug/game/<int:game_id>", methods=["GET"])
@jwt_required()
def debug_game(game_id):
    """调试接口：仅 DEBUG + 管理员可用；不返回邀请码"""
    from flask import current_app
    if not current_app.config.get('DEBUG', False):
        return jsonify({"error": "not allowed"}), 403
    try:
        uid = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"error": "unauthorized"}), 401
    admin = User.query.get(uid)
    if not admin or not admin.is_admin:
        return jsonify({"error": "admin required"}), 403
    try:
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"error": f"Game {game_id} not found"}), 404
        
        parts = CtfParticipation.query.filter_by(game_id=game_id).all()
        part_list = []
        for p in parts:
            users = CtfParticipatingUser.query.filter_by(participation_id=p.id).all()
            part_list.append({
                "participation_id": p.id,
                "team_id": p.team_id,
                "division_id": p.division_id,
                "user_count": len(users),
                "users": [u.user_id for u in users]
            })
        
        divisions = CtfDivision.query.filter_by(game_id=game_id).all()
        div_list = []
        for d in divisions:
            users_in_div = db.session.query(
                func.count(func.distinct(CtfParticipatingUser.user_id))
            ).filter_by(game_id=game_id, division_id=d.id).scalar() or 0
            div_list.append({
                "division_id": d.id,
                "name": d.name,
                "member_count": users_in_div
            })
        
        return jsonify({
            "game": {
                "id": game.id,
                "title": game.title,
                "is_public": game.is_public,
                "start_time": game.start_time.isoformat() if game.start_time else None,
                "end_time": game.end_time.isoformat() if game.end_time else None
            },
            "game_id": game_id,
            "participations": part_list,
            "divisions": div_list
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================== 竞赛管理（管理员） ========================

@bp.route("/admin/create", methods=["POST"])
@jwt_required()
def create_game():
    """创建竞赛"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        data = request.get_json() or {}
        
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "msg": f"缺少必要字段: {field}"
                }), 400

        start_raw = data.get("start_time")
        end_raw = data.get("end_time")
        if isinstance(start_raw, str) and start_raw.endswith("Z"):
            start_raw = start_raw.replace("Z", "+00:00")
        if isinstance(end_raw, str) and end_raw.endswith("Z"):
            end_raw = end_raw.replace("Z", "+00:00")

        game_type = data.get("game_type", "official")
        game = CtfGame(
            title=data.get("title"),
            start_time=datetime.fromisoformat(start_raw),
            end_time=datetime.fromisoformat(end_raw),
            is_public=data.get("is_public", True),
            game_type=game_type,
            status="ongoing" if game_type in ("training", "practice") else data.get("status", "not_started"),
            description=data.get("description"),
            summary=data.get("summary"),
            poster_url=data.get("poster_url"),
            enable_traffic_capture=bool(data.get("enable_traffic_capture", False)),
        )

        db.session.add(game)
        db.session.flush()

        # 非公开赛自动生成校内邀请码分组，避免管理员建完赛却拿不到码
        invite_div = _ensure_campus_invite_division(game)
        db.session.commit()

        payload = game.to_dict()
        if not game.is_public:
            _attach_admin_invite_fields(payload, game)
            if invite_div and invite_div.invite_code:
                payload["primary_invite_code"] = invite_div.invite_code

        return jsonify({
            "code": 200,
            "msg": "竞赛创建成功" + (
                f"（校内邀请码：{payload.get('primary_invite_code')}）"
                if payload.get("primary_invite_code") else ""
            ),
            "data": payload
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/update", methods=["PUT"])
@jwt_required()
def update_game(game_id):
    """更新竞赛信息"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        data = request.get_json() or {}

        if "title" in data:
            game.title = data["title"]
        if "start_time" in data:
            start_raw = data["start_time"]
            if isinstance(start_raw, str) and start_raw.endswith("Z"):
                start_raw = start_raw.replace("Z", "+00:00")
            game.start_time = datetime.fromisoformat(start_raw)
        if "end_time" in data:
            end_raw = data["end_time"]
            if isinstance(end_raw, str) and end_raw.endswith("Z"):
                end_raw = end_raw.replace("Z", "+00:00")
            game.end_time = datetime.fromisoformat(end_raw)
        if "is_public" in data:
            game.is_public = data["is_public"]
        if "description" in data:
            game.description = data["description"]
        if "summary" in data:
            game.summary = data["summary"]
        if "poster_url" in data:
            game.poster_url = data["poster_url"]
        if "enable_traffic_capture" in data:
            game.enable_traffic_capture = bool(data["enable_traffic_capture"])
        if "game_type" in data:
            game.game_type = data["game_type"]
        if "status" in data:
            game.status = data["status"]

        from backend.server.time_utils import sync_game_status_if_due
        sync_game_status_if_due(game)

        # 改为非公开时，自动补齐邀请码
        invite_div = _ensure_campus_invite_division(game)
        db.session.commit()

        payload = game.to_dict()
        if not game.is_public:
            _attach_admin_invite_fields(payload, game)
            if invite_div and invite_div.invite_code:
                payload["primary_invite_code"] = invite_div.invite_code

        return jsonify({
            "code": 200,
            "msg": "竞赛更新成功",
            "data": payload
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "msg": str(e)
        }), 500


@bp.route("/admin/<int:game_id>/ensure-campus-invite", methods=["POST"])
@jwt_required()
def ensure_campus_invite(game_id):
    """为已有非公开赛补生成校内邀请码（若尚无）。"""
    try:
        user, err = _require_admin_user()
        if err:
            return err

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404
        if game.is_public:
            return jsonify({"code": 400, "msg": "公开竞赛无需邀请码"}), 400

        div = _ensure_campus_invite_division(game)
        db.session.commit()
        payload = game.to_dict()
        _attach_admin_invite_fields(payload, game)
        if div and div.invite_code:
            payload["primary_invite_code"] = div.invite_code

        return jsonify({
            "code": 200,
            "msg": f"校内邀请码：{payload.get('primary_invite_code') or '未生成'}",
            "data": payload
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/archive", methods=["POST"])
@jwt_required()
def archive_game_admin(game_id):
    """归档竞赛（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404
        if game.archived_at is not None:
            return jsonify({"code": 400, "msg": "该竞赛已是归档状态"}), 400

        game.archived_at = datetime.utcnow()
        game.status = "archived"
        db.session.commit()
        return jsonify({"code": 200, "msg": "竞赛已归档", "data": game.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/delete", methods=["DELETE"])
@jwt_required()
def delete_game(game_id):
    """删除竞赛"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        # 按外键依赖顺序清理参赛/提交/题目等，再删竞赛本身
        purge_game(game_id)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "竞赛已删除"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/stats", methods=["GET"])
@jwt_required()
def admin_game_stats(game_id):
    """竞赛统计（管理端主路径；原 /api/admin/games/<id>/stats）"""
    _, err = _require_staff_user()
    if err:
        return err

    game = CtfGame.query.get(game_id)
    if not game:
        return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

    participant_count = db.session.query(
        func.count(func.distinct(CtfParticipatingUser.user_id))
    ).filter_by(game_id=game_id).scalar() or 0
    team_count = CtfParticipation.query.filter_by(game_id=game_id).count()
    challenge_count = CtfChallenge.query.filter_by(game_id=game_id).count()

    challenge_ids = db.session.query(CtfChallenge.id).filter_by(game_id=game_id)
    total_submissions = CtfChallengeSubmission.query.filter(
        CtfChallengeSubmission.challenge_id.in_(challenge_ids)
    ).count()
    correct_submissions = CtfChallengeSubmission.query.filter(
        CtfChallengeSubmission.challenge_id.in_(challenge_ids),
        or_(
            CtfChallengeSubmission.is_correct.is_(True),
            CtfChallengeSubmission.status == 0,
        ),
    ).count()
    cheat_pending = CtfCheatInfo.query.filter_by(game_id=game_id, status="pending").count()
    cheat_confirmed = CtfCheatInfo.query.filter_by(game_id=game_id, status="confirmed").count()

    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "game": {
                "id": game.id,
                "title": game.title,
                "start_time": game.start_time.isoformat() if game.start_time else None,
                "end_time": game.end_time.isoformat() if game.end_time else None,
            },
            "statistics": {
                "participation_count": participant_count,
                "participant_count": participant_count,
                "team_count": team_count,
                "challenge_count": challenge_count,
                "total_submissions": total_submissions,
                "correct_submissions": correct_submissions,
                "cheat_count": cheat_confirmed,
                "cheat_pending": cheat_pending,
                "cheat_confirmed": cheat_confirmed,
                "correct_rate": round(
                    (correct_submissions / total_submissions * 100) if total_submissions > 0 else 0,
                    2,
                ),
            },
        },
    }), 200


@bp.route("/admin/<int:game_id>/export-scoreboard", methods=["GET"])
@jwt_required()
def admin_export_scoreboard(game_id):
    """导出排行榜 CSV（管理端主路径；原 /api/admin/games/<id>/export-scoreboard）"""
    import csv
    from io import StringIO

    _, err = _require_staff_user()
    if err:
        return err

    game = CtfGame.query.get(game_id)
    if not game:
        return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

    scoreboards = CtfScoreboard.query.filter_by(game_id=game_id).order_by(
        CtfScoreboard.total_points.desc(),
        CtfScoreboard.last_submission_time.asc(),
    ).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["排名", "队伍ID", "队伍名称", "总分", "解题数", "最后提交时间", "赛道ID"])
    for idx, sb in enumerate(scoreboards, 1):
        team = Team.query.get(sb.team_id) if sb.team_id else None
        name = team.name if team else (f"用户#{sb.user_id}" if sb.user_id else "Unknown")
        last = sb.last_submission_time.isoformat() if sb.last_submission_time else ""
        writer.writerow([
            idx,
            sb.team_id or "",
            name,
            sb.total_points or 0,
            sb.solved_challenges or 0,
            last,
            sb.division_id or "",
        ])

    payload = "\ufeff" + output.getvalue()
    safe_title = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (game.title or "game"))[:40]
    filename = f"scoreboard_{game_id}_{safe_title}.csv"
    return Response(
        payload,
        status=200,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Row-Count": str(len(scoreboards)),
        },
    )


@bp.route("/admin/<int:game_id>", methods=["DELETE"])
@jwt_required()
def delete_game_alt(game_id):
    """删除竞赛（替代路由）"""
    return delete_game(game_id)


# ======================== 竞赛分组 ========================

@bp.route("/<int:game_id>/divisions", methods=["GET"])
def get_divisions(game_id):
    """获取竞赛分组列表与成员统计"""
    try:
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "比赛不存在"}), 404
        
        challenge_count = CtfChallenge.query.filter_by(
            game_id=game_id, is_enabled=True
        ).count()

        # 有真实赛道时始终返回 DB 行（管理端建/改/删后要能回读；公开赛也可配邀请码赛道）
        divisions = CtfDivision.query.filter_by(game_id=game_id).order_by(
            CtfDivision.sort_order.asc(), CtfDivision.id.asc()
        ).all()
        if divisions:
            items = []
            for d in divisions:
                invite_cnt = db.session.query(
                    func.count(func.distinct(CtfUserInviteCode.user_id))
                ).filter_by(game_id=game_id, division_id=d.id).scalar() or 0
                part_cnt = db.session.query(
                    func.count(func.distinct(CtfParticipatingUser.user_id))
                ).filter_by(game_id=game_id, division_id=d.id).scalar() or 0
                dto = d.to_dict(include_invite=True)
                dto["member_count"] = max(invite_cnt, part_cnt)
                dto["challenge_count"] = challenge_count
                items.append(dto)
            return jsonify({"code": 200, "msg": "获取成功", "data": items}), 200

        # 公开赛且无赛道：选手侧聚合视图
        if game.is_public:
            total_members = db.session.query(
                func.count(func.distinct(CtfParticipatingUser.user_id))
            ).filter_by(game_id=game_id).scalar() or 0
            return jsonify({
                "code": 200,
                "msg": "获取成功",
                "data": [{
                    "id": -1,
                    "game_id": game_id,
                    "name": "所有参赛者",
                    "invite_code": None,
                    "member_count": total_members,
                    "challenge_count": challenge_count,
                    "is_public": True
                }]
            }), 200

        return jsonify({"code": 200, "msg": "获取成功", "data": []}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/divisions/create", methods=["POST"])
@jwt_required()
def create_division(game_id):
    """创建分组"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        data = request.get_json() or {}
        name = (data.get("name") or "").strip()

        if not name:
            return jsonify({
                "code": 400,
                "msg": "分组名称不能为空"
            }), 400

        invite_code = data.get("invite_code")
        if isinstance(invite_code, str):
            invite_code = invite_code.strip() or None
        school_scope = data.get("school_scope")
        if isinstance(school_scope, str):
            school_scope = school_scope.strip() or None
        description = data.get("description")
        if isinstance(description, str):
            description = description.strip() or None

        if invite_code:
            clash = CtfDivision.query.filter_by(invite_code=invite_code).first()
            if clash:
                return jsonify({"code": 400, "msg": "邀请码已被占用"}), 400

        division = CtfDivision(
            game_id=game_id,
            name=name,
            invite_code=invite_code,
            school_scope=school_scope,
            description=description,
        )

        db.session.add(division)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "分组创建成功",
            "data": division.to_dict(include_invite=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/divisions/<int:division_id>/members", methods=["GET"])
@jwt_required()
def get_division_members(game_id, division_id):
    """获取分组（邀请码）的成员列表"""
    try:
        from backend.server.db_models import CtfUserInviteCode
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        division = CtfDivision.query.filter_by(
            game_id=game_id,
            id=division_id
        ).first()

        if not division:
            return jsonify({"code": 404, "msg": "分组不存在"}), 404

        # 查询使用过该邀请码的用户
        members = db.session.query(User, CtfUserInviteCode).join(
            CtfUserInviteCode, User.id == CtfUserInviteCode.user_id
        ).filter(
            CtfUserInviteCode.game_id == game_id,
            CtfUserInviteCode.division_id == division_id
        ).all()

        member_map = {}
        for u, record in members:
            member_map[u.id] = {
                "user_id": u.id,
                "nickname": u.nickname,
                "email": u.email,
                "invite_code_used": record.invite_code_used,
                "verified_at": record.verified_at.isoformat() if record.verified_at else None,
                "joined_at": record.created_at.isoformat() if record.created_at else None
            }

        # 兼容：如果没有邀请码记录，回退到参赛成员记录
        if not member_map:
            fallback = db.session.query(User, CtfParticipatingUser).join(
                CtfParticipatingUser, User.id == CtfParticipatingUser.user_id
            ).filter(
                CtfParticipatingUser.game_id == game_id,
                CtfParticipatingUser.division_id == division_id
            ).all()
            for u, record in fallback:
                member_map[u.id] = {
                    "user_id": u.id,
                    "nickname": u.nickname,
                    "email": u.email,
                    "invite_code_used": None,
                    "verified_at": None,
                    "joined_at": record.joined_at.isoformat() if record.joined_at else None
                }

        member_list = list(member_map.values())

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "division": division.to_dict(include_invite=True),
                "members": member_list,
                "count": len(member_list)
            }
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/divisions/<int:division_id>", methods=["PUT"])
@jwt_required()
def update_division(game_id, division_id):
    """更新分组信息"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        division = CtfDivision.query.filter_by(
            game_id=game_id,
            id=division_id
        ).first()

        if not division:
            return jsonify({"code": 404, "msg": "分组不存在"}), 404

        data = request.get_json() or {}

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                return jsonify({"code": 400, "msg": "分组名称不能为空"}), 400
            division.name = name
        if "invite_code" in data:
            invite_code = data.get("invite_code")
            if isinstance(invite_code, str):
                invite_code = invite_code.strip() or None
            if invite_code:
                clash = CtfDivision.query.filter(
                    CtfDivision.invite_code == invite_code,
                    CtfDivision.id != division.id,
                ).first()
                if clash:
                    return jsonify({"code": 400, "msg": "邀请码已被占用"}), 400
            division.invite_code = invite_code
        if "school_scope" in data:
            school_scope = data.get("school_scope")
            if isinstance(school_scope, str):
                school_scope = school_scope.strip() or None
            division.school_scope = school_scope
        if "description" in data:
            description = data.get("description")
            if isinstance(description, str):
                description = description.strip() or None
            division.description = description

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "分组更新成功",
            "data": division.to_dict(include_invite=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/<int:game_id>/divisions/<int:division_id>", methods=["DELETE"])
@jwt_required()
def delete_division(game_id, division_id):
    """删除分组"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({
                "code": 403,
                "msg": "无权操作"
            }), 403

        division = CtfDivision.query.filter_by(
            game_id=game_id,
            id=division_id
        ).first()

        if not division:
            return jsonify({"code": 404, "msg": "分组不存在"}), 404

        db.session.delete(division)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "分组已删除"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 流量包捕获 ========================


@bp.route("/admin/<int:game_id>/traffic-captures", methods=["GET"])
@jwt_required()
def list_traffic_captures(game_id):
    """列出某场比赛的流量包（目录 + 数据库联调）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        sync = request.args.get("sync", "1") not in ("0", "false", "no")
        data = TrafficCaptureService.list_game_captures(game_id, sync=sync)
        data["game"] = {
            "id": game.id,
            "title": game.title,
            "enable_traffic_capture": bool(game.enable_traffic_capture),
        }
        return jsonify({"code": 200, "msg": "ok", "data": data}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/traffic-captures/<int:capture_id>/download", methods=["GET"])
@jwt_required()
def download_traffic_capture(capture_id):
    """下载 PCAP 文件"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        rec, full_path, err = TrafficCaptureService.get_capture_for_download(capture_id)
        if err:
            return jsonify({"code": 404, "msg": err}), 404

        filename = full_path.name
        return send_file(
            full_path,
            mimetype="application/vnd.tcpdump.pcap",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/admin/traffic-captures/<int:capture_id>", methods=["DELETE"])
@jwt_required()
def delete_traffic_capture(capture_id):
    """删除数据库记录及 captures/ 目录中的 PCAP 文件"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        ok, msg = TrafficCaptureService.delete_capture(capture_id)
        if not ok:
            return jsonify({"code": 404, "msg": msg}), 404
        return jsonify({"code": 200, "msg": msg}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500
