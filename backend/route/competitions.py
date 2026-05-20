"""
CTF 竞赛/游戏相关的API路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from backend.server.extensions import db
from backend.server.db_models import (
    User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
    CtfParticipation, CtfParticipatingUser, CtfScoreboard, CtfDivision,
    CtfUserInviteCode
)

bp = Blueprint("competitions", __name__)


# ======================== 竞赛列表 ========================

@bp.route("/", methods=["GET"])
def get_games():
    """获取所有竞赛（包括公开和非公开）"""
    try:
        games = CtfGame.query.all()
        data = []
        for game in games:
            game_dict = game.to_dict()
            
            # 获取题目数量
            challenge_count = CtfChallenge.query.filter_by(
                game_id=game.id, is_enabled=True
            ).count()
            game_dict['challenge_count'] = challenge_count
            
            # 获取参赛人数
            if game.is_public:
                # 公开比赛：统计所有参赛用户
                participation_count = CtfParticipatingUser.query.filter_by(
                    game_id=game.id
                ).distinct(CtfParticipatingUser.user_id).count()
            else:
                # 非公开比赛：统计有邀请码的人数
                participation_count = CtfUserInviteCode.query.filter_by(
                    game_id=game.id
                ).distinct(CtfUserInviteCode.user_id).count()
            
            game_dict['participation_count'] = participation_count
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

        if not game.is_public:
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

@bp.route("/<int:game_id>/join", methods=["POST"])
@jwt_required()
def join_game(game_id):
    """用户加入竞赛 - 以队伍身份"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        # 用户必须先加入团队
        if not user.team_id:
            return jsonify({
                "code": 403,
                "msg": "请先加入团队"
            }), 403

        team_id = user.team_id
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

        if not user or not user.team_id:
            return jsonify({
                "code": 404,
                "msg": "您未参加过这个竞赛"
            }), 404

        team_id = user.team_id
        
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


@bp.route("/<int:game_id>/joined", methods=["GET"])
@jwt_required()
def is_joined(game_id):
    """返回当前用户的队伍是否已加入该竞赛"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.team_id:
            return jsonify({"joined": False}), 200

        part = CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first()
        return jsonify({"joined": bool(part)}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/debug/game/<int:game_id>", methods=["GET"])
def debug_game(game_id):
    """调试接口：查看该比赛的所有参赛数据"""
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
            users_in_div = CtfParticipatingUser.query.filter_by(
                game_id=game_id, division_id=d.id
            ).distinct(CtfParticipatingUser.user_id).count()
            div_list.append({
                "division_id": d.id,
                "name": d.name,
                "invite_code": d.invite_code,
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

        game = CtfGame(
            title=data.get("title"),
            start_time=datetime.fromisoformat(data.get("start_time")),
            end_time=datetime.fromisoformat(data.get("end_time")),
            is_public=data.get("is_public", True)
        )

        db.session.add(game)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "竞赛创建成功",
            "data": game.to_dict()
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
            game.start_time = datetime.fromisoformat(data["start_time"])
        if "end_time" in data:
            game.end_time = datetime.fromisoformat(data["end_time"])
        if "is_public" in data:
            game.is_public = data["is_public"]

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "竞赛更新成功",
            "data": game.to_dict()
        }), 200
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

        # 删除相关数据
        CtfChallenge.query.filter_by(game_id=game_id).delete()
        CtfParticipation.query.filter_by(game_id=game_id).delete()
        CtfScoreboard.query.filter_by(game_id=game_id).delete()
        CtfDivision.query.filter_by(game_id=game_id).delete()

        db.session.delete(game)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "竞赛已删除"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


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
        
        # 公开比赛：统计所有参赛用户人数
        if game.is_public:
            total_members = CtfParticipatingUser.query.filter_by(
                game_id=game_id
            ).distinct(CtfParticipatingUser.user_id).count()
            
            # 计算题目数
            challenge_count = CtfChallenge.query.filter_by(
                game_id=game_id, is_enabled=True
            ).count()
            
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
        
        # 非公开比赛：按分组（邀请码）统计有邀请码段的人数
        divisions = CtfDivision.query.filter_by(game_id=game_id).all()
        items = []
        
        # 获取任意一个分组的题目数（当作整个赛事的题目数）
        challenge_count = 0
        if divisions:
            challenge_count = CtfChallenge.query.filter_by(
                game_id=game_id, is_enabled=True
            ).count()
        
        for d in divisions:
            # 统计有此邀请码的人数
            member_count = CtfUserInviteCode.query.filter_by(
                game_id=game_id,
                division_id=d.id
            ).distinct(CtfUserInviteCode.user_id).count()
            
            dto = d.to_dict()
            dto["member_count"] = member_count
            dto["challenge_count"] = challenge_count
            items.append(dto)
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": items
        }), 200
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
        name = data.get("name")

        if not name:
            return jsonify({
                "code": 400,
                "msg": "分组名称不能为空"
            }), 400

        division = CtfDivision(
            game_id=game_id,
            name=name,
            invite_code=data.get("invite_code")
        )

        db.session.add(division)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "分组创建成功",
            "data": division.to_dict()
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
                "division": division.to_dict(),
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
            division.name = data["name"]
        if "invite_code" in data:
            division.invite_code = data["invite_code"]
        if "school_scope" in data:
            division.school_scope = data["school_scope"]
        if "description" in data:
            division.description = data["description"]

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "分组更新成功",
            "data": division.to_dict()
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
