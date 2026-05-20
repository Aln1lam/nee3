from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.server import extensions
from backend.server.db_models import CtfGame, User, Team
from backend.server.db_models import CtfParticipation, CtfParticipatingUser, CtfScoreboard
from backend.server.audit_log import log_create, log_view, log_update, log_delete
from flask import make_response

bp = Blueprint("games", __name__)


@bp.get("/")
def list_games():
    games = CtfGame.query.all()
    return {"items": [g.to_dict() for g in games]}


@bp.get("/<int:game_id>/divisions")
def get_game_divisions(game_id):
    """获取比赛的赛道列表（仅非公开比赛）"""
    from backend.server.db_models import CtfDivision
    
    game = CtfGame.query.get_or_404(game_id)
    
    # 公开比赛不需要显示赛道
    if game.is_public:
        return {"items": [], "is_public": True}
    
    # 非公开比赛，返回所有赛道
    divisions = CtfDivision.query.filter_by(game_id=game_id).order_by(CtfDivision.sort_order).all()
    
    return {
        "items": [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "school_scope": d.school_scope,
                "invite_code": d.invite_code  # 注意：生产环境不应该直接返回邀请码
            } for d in divisions
        ],
        "is_public": False
    }


@bp.get("/<int:game_id>/scoreboard")
def scoreboard(game_id):
    """获取比赛排行榜
    
    支持参数:
    - division_id: 可选，按赛道过滤排行榜
    """
    from backend.server.db_models import CtfChallenge, CtfChallengeSubmission
    
    division_id = request.args.get('division_id', type=int)
    
    # 使用 CtfScoreboard 表直接查询
    query = CtfScoreboard.query.filter_by(game_id=game_id)
    
    if division_id:
        # 按赛道过滤
        query = query.filter_by(division_id=division_id)
    
    scoreboards = query.order_by(
        CtfScoreboard.total_points.desc(),
        CtfScoreboard.last_submission_time.asc()
    ).all()
    
    items = []
    for idx, sb in enumerate(scoreboards, 1):
        team_data = sb.team.to_dict() if sb.team else None
        items.append({
            "rank": idx,
            "team_id": sb.team_id,
            "team": team_data,
            "total_points": sb.total_points,
            "solved_challenges": sb.solved_challenges,
            "last_submission_time": sb.last_submission_time.isoformat() if sb.last_submission_time else None,
            "division_id": sb.division_id
        })
    
    return {"items": items, "total": len(items)}


@bp.get("/<int:game_id>/challenges")
def list_challenges(game_id):
    items = Challenge.query.filter_by(game_id=game_id).all()
    return {"items": [{"id": c.id, "title": c.title, "score": c.score} for c in items]}


@bp.post("/challenges/<int:cid>/submit")
@jwt_required()
def submit_flag(cid):
    uid = int(get_jwt_identity())
    data = request.get_json() or {}
    flag = data.get("flag")
    if not flag:
        return {"msg": "missing flag"}, 400
    challenge = Challenge.query.get_or_404(cid)
    # verify that the submitting user's team has joined the game that the challenge belongs to
    game_id = challenge.game_id
    user = User.query.get(uid)
    if not user or not user.team_id:
        return {"msg": "must be in a team to submit"}, 403
    
    part = CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first()
    if not part:
        return {"msg": "not participating in this game"}, 403
    correct = flag.strip() == challenge.flag
    sub = Submission(user_id=uid, challenge_id=cid, flag_submitted=flag, is_correct=correct)
    extensions.db.session.add(sub)
    extensions.db.session.commit()
    try:
        log_create('submission', sub.id, f'challenge:{cid}', meta={'correct': correct})
    except Exception:
        pass
    return {"correct": correct}


@bp.post("/<int:game_id>/join")
@jwt_required()
def join_game(game_id):
    """Current user's team joins the game (creates a CtfParticipation at team level)."""
    uid = int(get_jwt_identity())
    game = CtfGame.query.get_or_404(game_id)
    data = request.get_json() or {}
    invite_code = data.get('invite_code', '').strip()
    
    # 🔴 检查：比赛已归档，不能加入
    if game.archived_at is not None:
        return {
            "code": 403,
            "msg": "该比赛已归档，无法加入。"
        }, 403
    
    # ✓ 检查：比赛已开始，不能加入
    if datetime.utcnow() >= game.start_time:
        return {
            "code": 403,
            "msg": "比赛已开始，无法加入。只能在比赛开始前加入。"
        }, 403
    
    # require user to be in a team before joining (team-centric behavior)
    user = User.query.get(uid)
    if not user:
        return {"msg": "user not found"}, 404
    if not user.team_id:
        return {"msg": "You must join a team first"}, 403

    team_id = user.team_id
    division_id = None
    
    # 🔴 核心逻辑：公开 vs 非公开比赛
    if not game.is_public:
        # 非公开比赛：必须提供邀请码
        if not invite_code:
            return {
                "code": 400,
                "msg": "该比赛需要邀请码才能参加"
            }, 400
        
        # 验证邀请码并获取对应的 division
        from backend.server.db_models import CtfDivision, CtfUserInviteCode
        division = CtfDivision.query.filter_by(
            game_id=game_id,
            invite_code=invite_code
        ).first()
        
        if not division:
            return {
                "code": 400,
                "msg": "邀请码无效或已过期"
            }, 400
        
        # 验证邀请码的学校范围限制（如果有）
        if division.school_scope:
            # 如果设置了学校范围，检查用户学校是否匹配
            if division.school_scope == "高校":
                # 只允许学生参加
                if user.identity not in ["student", "teacher"]:
                    return {
                        "code": 403,
                        "msg": "该赛道仅限高校师生参加"
                    }, 403
            elif division.school_scope != user.school:
                # 特定学校赛道，必须是该学校的
                return {
                    "code": 403,
                    "msg": f"该邀请码仅限 {division.school_scope} 的成员使用"
                }, 403
        
        division_id = division.id
        
        # 记录用户使用的邀请码
        existing_code = CtfUserInviteCode.query.filter_by(
            user_id=uid,
            game_id=game_id,
            division_id=division_id
        ).first()
        
        if not existing_code:
            invite_code_record = CtfUserInviteCode(
                user_id=uid,
                game_id=game_id,
                division_id=division_id,
                invite_code_used=invite_code,
                verified_at=datetime.utcnow()
            )
            extensions.db.session.add(invite_code_record)
    else:
        # 公开比赛：不需要邀请码，所有人平等参加（division_id = None）
        pass
    
    # check if team already joined this game
    existing = CtfParticipation.query.filter_by(team_id=team_id, game_id=game_id).first()
    if existing:
        # Check if current user is already in CtfParticipatingUser
        user_part = CtfParticipatingUser.query.filter_by(
            user_id=uid, game_id=game_id, team_id=team_id
        ).first()
        if not user_part:
            user_part = CtfParticipatingUser(
                user_id=uid, game_id=game_id, team_id=team_id, 
                participation_id=existing.id, division_id=division_id
            )
            extensions.db.session.add(user_part)
            extensions.db.session.commit()
        return {"msg": "already joined", "division_id": division_id}, 200

    # Create team-level participation
    p = CtfParticipation(team_id=team_id, game_id=game_id, division_id=division_id, status="confirmed")
    extensions.db.session.add(p)
    extensions.db.session.flush()  # Get p.id
    
    # Add all team members to CtfParticipatingUser
    team = Team.query.get(team_id)
    for team_member in team.users:
        user_part = CtfParticipatingUser(
            user_id=team_member.id, game_id=game_id, team_id=team_id, 
            participation_id=p.id, division_id=division_id
        )
        extensions.db.session.add(user_part)
    
    # Create team scoreboard entry
    scoreboard = CtfScoreboard(team_id=team_id, game_id=game_id, division_id=division_id)
    extensions.db.session.add(scoreboard)
    extensions.db.session.commit()
    
    return {
        "msg": "joined", 
        "participation_id": p.id, 
        "team_id": team_id,
        "division_id": division_id,
        "division_name": CtfDivision.query.get(division_id).name if division_id else None
    }


@bp.post("/<int:game_id>/leave")
@jwt_required()
def leave_game(game_id):
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.team_id:
        return {"msg": "user not in team"}, 404
    
    p = CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first()
    if not p:
        return {"msg": "not participating"}, 404
    
    # Remove all team members from CtfParticipatingUser
    CtfParticipatingUser.query.filter_by(
        team_id=user.team_id, game_id=game_id
    ).delete()
    # Remove team-level participation
    extensions.db.session.delete(p)
    extensions.db.session.commit()
    return {"msg": "left"}


@bp.get("/<int:game_id>/participants")
def list_participants(game_id):
    parts = CtfParticipation.query.filter_by(game_id=game_id).all()
    items = []
    for p in parts:
        team = Team.query.get(p.team_id)
        # Count members in this team's participation
        user_parts = CtfParticipatingUser.query.filter_by(
            team_id=p.team_id, game_id=game_id
        ).all()
        items.append({
            "id": p.id, 
            "team_id": p.team_id, 
            "team_name": team.name if team else None,
            "members_count": len(user_parts),
            "status": p.status if hasattr(p, 'status') else "confirmed",
            "joined_at": p.joined_at.isoformat() if p.joined_at else None
        })
    return {"items": items}


@bp.get("/<int:game_id>/joined")
@jwt_required()
def is_joined(game_id):
    """Return whether current user's team has joined the given game."""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.team_id:
        return {"joined": False}
    
    part = CtfParticipation.query.filter_by(team_id=user.team_id, game_id=game_id).first()
    return {"joined": bool(part)}


@bp.post("/")
@jwt_required()
def create_game():
    """创建比赛（简单版，不做权限校验），便于前端联调。"""
    data = request.get_json() or {}
    title = data.get("title")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    if not all([title, start_time, end_time]):
        return {"msg": "missing fields"}, 400
    g = CtfGame(
        title=title,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        is_public=True,
    )
    extensions.db.session.add(g)
    extensions.db.session.commit()
    return {"id": g.id, "title": g.title}, 201


@bp.post("/<int:game_id>/challenges")
@jwt_required()
def create_challenge(game_id):
    """创建题目（简单版，不做权限校验），便于前端联调。"""
    data = request.get_json() or {}
    title = data.get("title")
    flag = data.get("flag")
    score = data.get("score", 100)
    content = data.get("content", "")
    if not all([title, flag]):
        return {"msg": "missing fields"}, 400
    ch = Challenge(game_id=game_id, title=title, flag=flag, score=score, content=content)
    extensions.db.session.add(ch)
    extensions.db.session.commit()
    return {"id": ch.id, "title": ch.title}, 201


@bp.get("/challenges/<int:cid>/submissions")
@jwt_required()
def my_submissions(cid):
    """当前用户在某题的提交列表"""
    uid = int(get_jwt_identity())
    subs = Submission.query.filter_by(challenge_id=cid, user_id=uid).all()
    try:
        log_view('submission', None, f'challenge:{cid}',)
    except Exception:
        pass
    return {
        "items": [
            {
                "id": s.id,
                "flag": s.flag_submitted,
                "correct": s.is_correct,
                "created_at": s.created_at.isoformat(),
            }
            for s in subs
        ]
    }


@bp.post("/seed")
def seed_sample():
    """快速生成一个示例比赛和两道题（无需鉴权，用于本地联调）"""
    if CtfGame.query.first():
        return {"msg": "already seeded"}, 200
    g = CtfGame(
        title="Sample CTF",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        is_public=True,
    )
    extensions.db.session.add(g)
    extensions.db.session.commit()
    challenges = [
        Challenge(game_id=g.id, title="hello", flag="flag{hello}", score=100, content="Welcome"),
        Challenge(game_id=g.id, title="world", flag="flag{world}", score=200, content="Have fun"),
    ]
    extensions.db.session.add_all(challenges)
    extensions.db.session.commit()
    # --- create sample users, teams and participations for easy testing ---
    # create users
    u1 = User(email="alice@example.com", nickname="alice")
    u1.set_password("password")
    u2 = User(email="bob@example.com", nickname="bob")
    u2.set_password("password")

    # create teams
    t1 = Team(name="RedTeam", invite_code="inv-red")
    t2 = Team(name="BlueTeam", invite_code="inv-blue")

    extensions.db.session.add_all([u1, u2, t1, t2])
    extensions.db.session.commit()

    # assign users to teams
    u1.team = t1
    u2.team = t2

    # create participations linking users (via participation entries)
    p1 = CtfParticipation(user_id=u1.id, game_id=g.id, role="player")
    p2 = CtfParticipation(user_id=u2.id, game_id=g.id, role="player")

    extensions.db.session.add_all([p1, p2])
    extensions.db.session.commit()

    return {"game_id": g.id, "challenge_ids": [c.id for c in challenges], "users": [u1.id, u2.id], "teams": [t1.id, t2.id], "participations": [p1.id, p2.id]}