"""
CTF 完整功能 API 路由

当前仅保留：
- 排行榜 scoreboard(+timeline/user)
- notices / health / cleanup

列表、join、submit、hints、instance、题目详情等与 competitions/challenges 重叠的路径一律 410。
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
from backend.server.extensions import db
from backend.server.db_models import (
    User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
    CtfGameInstance, CtfParticipation, CtfScoreboard, CtfSolves,
    CtfCheatInfo, CtfChallengeHint, CtfUserHintAccess, CtfGameNotice,
    CtfDivision, CtfChallengeCategory, CtfParticipatingUser,
    CtfUserInviteCode
)
from backend.services.scoring_service import (
    ScoringService, CheatDetectionService, FlagTemplateService,
    PermissionService, FlagValidationService,
    AnswerResult, GamePermission, ChallengeCType
)
from backend.services.container_service import container_service
from backend.services.team_service import ensure_user_has_team
from backend.server.container_access import normalize_connection_url
from backend.middleware_refactored import submission_rate_limit, rate_limit
from backend.services.redis_service import get_redis, ScoreboardCache
from backend.server.db_retry import run_transaction_with_retry, is_deadlock_error
from sqlalchemy.exc import DBAPIError, OperationalError, IntegrityError

bp = Blueprint("ctf_api", __name__, url_prefix="/api/ctf")


def _ctf_overlapping_gone(successor: str, detail: str):
    resp = jsonify({
        "code": 410,
        "msg": detail,
        "successor": successor,
    })
    resp.status_code = 410
    resp.headers["Deprecation"] = "true"
    resp.headers["Link"] = f"<{successor}>; rel=\"successor-version\""
    resp.headers["X-Deprecated-Endpoint"] = successor
    return resp


@bp.before_request
def _retire_overlapping_ctf_routes():
    """
    仅保留排行榜 / notices / health / cleanup。
    列表、join、submit、hints、instance、题目详情等与 competitions/challenges 重叠的路径一律 410。
    """
    if request.method == "OPTIONS":
        return None
    path = request.path or ""
    if path.endswith("/health") or path.endswith("/cleanup/containers"):
        return None
    if "/scoreboard" in path:
        return None
    if "/notices" in path:
        return None
    if "/submit" in path or "/hints" in path or "start-instance" in path or "/instances/" in path:
        return _ctf_overlapping_gone(
            "/api/challenges/",
            "Gone: use /api/challenges/* for submit/hints/instances",
        )
    if "/challenges" in path:
        return _ctf_overlapping_gone(
            "/api/challenges/",
            "Gone: use /api/challenges/* for challenge APIs",
        )
    # /games 列表、详情、join、divisions 等
    return _ctf_overlapping_gone(
        "/api/competitions/",
        "Gone: use /api/competitions/* for game list/join/divisions",
    )


def _container_start_rate_key():
    try:
        return f"ctf:start:{get_jwt_identity()}"
    except Exception:
        return "ctf:start:anon"


# ======================== 工具函数 ========================

def error_response(message: str, code: int = 400):
    """返回错误响应"""
    return jsonify({"error": message, "code": code}), code


def success_response(data=None, message: str = "Success"):
    """返回成功响应"""
    return jsonify({"data": data, "message": message, "code": 0}), 200


@bp.before_request
def check_jwt():
    """在需要时检查JWT令牌"""
    pass


# ======================== 竞赛管理 API ========================

@bp.route("/games", methods=["GET"])
def list_games():
    """获取竞赛列表

    Query:
      include_ephemeral=1  — 包含 E2E/探针测试赛（管理端排查用；默认排除）
      game_type=official|training|practice  — 按类型过滤（可多值逗号分隔）
    """
    from backend.server.game_filters import is_ephemeral_test_game

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    include_ephemeral = str(request.args.get('include_ephemeral', '0')).lower() in (
        '1', 'true', 'yes',
    )
    game_type_raw = (request.args.get('game_type') or '').strip()
    game_types = [t.strip().lower() for t in game_type_raw.split(',') if t.strip()]

    all_games = CtfGame.query.order_by(CtfGame.start_time.desc()).all()
    if not include_ephemeral:
        all_games = [g for g in all_games if not is_ephemeral_test_game(g)]
    if game_types:
        all_games = [
            g for g in all_games
            if (getattr(g, 'game_type', None) or 'official').lower() in game_types
        ]

    total = len(all_games)
    pages = max(1, (total + per_page - 1) // per_page) if per_page else 1
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    slice_games = all_games[start:start + per_page]

    items = []
    for g in slice_games:
        dto = g.to_dict()
        dto['is_ephemeral'] = is_ephemeral_test_game(g)

        # 题目数
        dto['challenge_count'] = CtfChallenge.query.filter_by(
            game_id=g.id,
            is_enabled=True
        ).count()

        # 参赛人数（公开=参赛用户，非公开=邀请码用户）
        if g.is_public:
            participation_count = db.session.query(
                func.count(func.distinct(CtfParticipatingUser.user_id))
            ).filter_by(game_id=g.id).scalar() or 0
        else:
            participation_count = db.session.query(
                func.count(func.distinct(CtfUserInviteCode.user_id))
            ).filter_by(game_id=g.id).scalar() or 0

        dto['participation_count'] = participation_count
        items.append(dto)

    result = {
        'total': total,
        'pages': pages,
        'current_page': page,
        'items': items,
        'include_ephemeral': include_ephemeral,
        'game_type': game_type_raw or None,
    }

    return success_response(result)


@bp.route("/games/<int:game_id>", methods=["GET"])
def get_game_detail(game_id):
    """获取竞赛详情"""
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("CtfGame not found", 404)
    
    user_id = None
    user = None

    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id is not None:
            user = User.query.get(int(user_id))
    except Exception:
        pass
    
    result = game.to_dict()
    
    # 添加参赛者数量
    result['participation_count'] = CtfParticipation.query.filter_by(
        game_id=game_id
    ).count()
    
    # 添加题目数量
    result['challenge_count'] = CtfChallenge.query.filter_by(
        game_id=game_id,
        is_enabled=True
    ).count()
    
    # 如果用户已参加，添加其排行榜信息
    if user:
        user_participation = CtfParticipatingUser.query.filter_by(
            user_id=user_id,
            game_id=game_id
        ).first()

        if user_participation:
            result['user_participation'] = {
                'team_id': user_participation.team_id,
                'joined_at': user_participation.joined_at.isoformat() if user_participation.joined_at else None,
                'division_id': user_participation.division_id
            }

            scoreboard = CtfScoreboard.query.filter_by(
                game_id=game_id,
                team_id=user_participation.team_id
            ).first()

            if scoreboard:
                result['user_scoreboard'] = scoreboard.to_dict()
    
    return success_response(result)


@bp.route("/games/<int:game_id>/join", methods=["POST"])
@jwt_required()
def join_game(game_id):
    """加入竞赛 - 以队伍身份"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response("User not found", 404)

    team = ensure_user_has_team(user)
    if not team:
        return error_response("Failed to create solo team", 500)
    
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("CtfGame not found", 404)

    data = request.get_json() or {}
    invite_code = (data.get("invite_code") or "").strip()
    division_id = None
    
    # 检查时间
    now = datetime.utcnow()
    if now > game.end_time:
        return error_response("CtfGame has ended", 400)

    # 非公开比赛需要邀请码并记录分组
    if not game.is_public:
        if not invite_code:
            return error_response("该比赛需要邀请码才能参加", 400)

        division = CtfDivision.query.filter_by(game_id=game_id, invite_code=invite_code).first()
        if not division:
            return error_response("邀请码无效或已过期", 400)

        # 学校范围限制
        if division.school_scope:
            if division.school_scope == "高校":
                if user.identity not in ["student", "teacher"]:
                    return error_response("该赛道仅限高校师生参加", 403)
            elif division.school_scope != user.school:
                return error_response(f"该邀请码仅限 {division.school_scope} 的成员使用", 403)

        division_id = division.id
    
    # 检查队伍是否已参加该比赛
    existing_participation = CtfParticipation.query.filter_by(
        game_id=game_id,
        team_id=user.team_id
    ).first()
    
    if existing_participation:
        # 检查当前用户是否已作为该队伍的成员加入
        existing_user_participation = CtfParticipatingUser.query.filter_by(
            user_id=user_id,
            game_id=game_id,
            team_id=user.team_id,
            participation_id=existing_participation.id
        ).first()
        
        if existing_user_participation:
            return error_response("You have already joined this game with your team", 400)

        # 分组不一致则拒绝
        if existing_participation.division_id and division_id and existing_participation.division_id != division_id:
            return error_response("该队伍已加入其他分组", 409)

        # 之前没有分组时补写
        if division_id and not existing_participation.division_id:
            existing_participation.division_id = division_id
            CtfParticipatingUser.query.filter_by(
                game_id=game_id,
                team_id=user.team_id
            ).update({"division_id": division_id})
        
        # 添加用户到现有的队伍参赛记录
        user_participation = CtfParticipatingUser(
            user_id=user_id,
            game_id=game_id,
            team_id=user.team_id,
            participation_id=existing_participation.id,
            division_id=division_id
        )
    else:
        # 创建新的队伍参赛记录
        participation = CtfParticipation(
            game_id=game_id,
            team_id=user.team_id,
            status="confirmed",
            division_id=division_id
        )
        db.session.add(participation)
        db.session.flush()  # 获取新生成的 participation.id
        
        # 为该队伍的所有成员创建参赛记录
        for team_member in user.team.users:
            user_participation = CtfParticipatingUser(
                user_id=team_member.id,
                game_id=game_id,
                team_id=user.team_id,
                participation_id=participation.id,
                division_id=division_id
            )
            db.session.add(user_participation)
        
        # 创建排行榜记录
        scoreboard = CtfScoreboard(
            game_id=game_id,
            team_id=user.team_id,
            total_points=0,
            solved_challenges=0
        )
        db.session.add(scoreboard)

    # 记录邀请码使用（非公开比赛）
    if division_id:
        existing_code = CtfUserInviteCode.query.filter_by(
            user_id=user_id,
            game_id=game_id,
            division_id=division_id
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
    
    return success_response(
        {"team_id": user.team_id, "game_id": game_id},
        "Successfully joined game with your team"
    )


@bp.route("/games/<int:game_id>/divisions", methods=["GET"])
def list_divisions(game_id):
    """获取竞赛的所有分组（邀请码仅对管理员/已参赛用户可见）"""
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("Game not found", 404)

    divisions = CtfDivision.query.filter_by(game_id=game_id).all()

    can_see_invite = False
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid is not None:
            uid = int(uid)
            user = User.query.get(uid)
            if user and user.is_admin:
                can_see_invite = True
            elif CtfParticipatingUser.query.filter_by(user_id=uid, game_id=game_id).first():
                can_see_invite = True
    except Exception:
        can_see_invite = False

    result = [d.to_dict(include_invite=can_see_invite) for d in divisions]
    return success_response(result)


# ======================== 题目管理 API ========================

@bp.route("/games/<int:game_id>/challenges", methods=["GET"])
def list_challenges(game_id):
    """获取竞赛的所有题目"""
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("CtfGame not found", 404)
    
    challenges = CtfChallenge.query.filter_by(
        game_id=game_id,
        is_enabled=True
    ).all()
    
    result = []
    for challenge in challenges:
        data = challenge.to_public_dict()
        
        # 添加解题统计（唯一队伍数）
        solved_count = ScoringService.count_accepted_solvers(challenge.id)
        
        # 计算当前分数（使用题目自身衰减参数）
        current_score = ScoringService.challenge_base_dynamic_score(
            challenge, solved_count
        )
        
        data['solved_count'] = solved_count
        data['current_score'] = current_score
        
        result.append(data)
    
    return success_response({'items': result})


@bp.route("/challenges/<int:challenge_id>", methods=["GET"])
@jwt_required()
def get_challenge_detail(challenge_id):
    """获取题目详情"""
    user_id = get_jwt_identity()
    
    challenge = CtfChallenge.query.get(challenge_id)
    if not challenge:
        return error_response("Challenge not found", 404)
    
    # 检查权限
    if not PermissionService.check_game_permission(
        user_id, challenge.game_id, GamePermission.VIEW_CHALLENGE
    ):
        return error_response("Permission denied", 403)
    
    user = User.query.get(user_id)
    include_sensitive = bool(user and user.is_admin)
    result = challenge.to_dict() if include_sensitive else challenge.to_public_dict()
    
    # 添加提示（未购买不返回全文）
    hints = CtfChallengeHint.query.filter_by(challenge_id=challenge_id).all()
    accessed_ids = {
        a.hint_id
        for a in CtfUserHintAccess.query.filter_by(user_id=user_id).all()
    }
    hint_list = []
    for h in hints:
        accessed = include_sensitive or (h.id in accessed_ids)
        hd = h.to_dict(include_text=accessed)
        hd['accessed'] = h.id in accessed_ids
        hd['is_accessed'] = hd['accessed']
        hint_list.append(hd)
    result['hints'] = hint_list
    
    # 添加用户是否已解
    solved = CtfChallengeSubmission.query.filter_by(
        user_id=user_id,
        challenge_id=challenge_id,
        is_correct=True
    ).first()
    result['solved'] = solved is not None
    
    # 添加用户提交次数
    attempt_count = CtfChallengeSubmission.query.filter_by(
        user_id=user_id,
        challenge_id=challenge_id
    ).count()
    result['attempt_count'] = attempt_count
    
    return success_response(result)


# ======================== Flag 提交 API ========================

@bp.route("/challenges/<int:challenge_id>/submit", methods=["POST"])
@jwt_required()
@submission_rate_limit()
def submit_flag(challenge_id):
    """提交 Flag"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    answer = data.get('answer', '').strip()
    if not answer:
        return error_response("Answer cannot be empty", 400)
    
    challenge = CtfChallenge.query.get(challenge_id)
    if not challenge:
        return error_response("Challenge not found", 404)
    
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)
    
    # 检查权限
    if not PermissionService.has_submission_permission(user_id, challenge.game_id, challenge_id):
        return error_response("Permission denied", 403)
    
    # 验证答案并持久化（死锁时自动重试整个事务）
    def _persist_submission():
        from backend.services.submit_lock import (
            lock_challenge_row,
            submission_owner_key,
            redis_submit_lock,
            correct_submission_dedupe_key,
        )

        owner_key = submission_owner_key(user)
        with redis_submit_lock(challenge_id, owner_key) as got_lock:
            if not got_lock:
                raise RuntimeError("submit_busy")

            locked = lock_challenge_row(challenge_id)
            if not locked:
                return None, 1

            # 提交次数限制放在锁内
            if locked.submission_limit > 0:
                attempts = CtfChallengeSubmission.query.filter_by(
                    user_id=user_id,
                    challenge_id=challenge_id
                ).count()
                if attempts >= locked.submission_limit:
                    raise RuntimeError("submit_limit")

            is_correct, status = FlagValidationService.validate_flag(
                answer,
                challenge_id,
                user_id,
                challenge.game_id,
            )

            if status == 2:  # DUPLICATE
                return None, status

            submission = CtfChallengeSubmission(
                user_id=user_id,
                team_id=user.team_id,
                challenge_id=challenge_id,
                game_id=challenge.game_id,
                answer=answer,
                is_correct=is_correct,
                status=status,
                correct_dedupe_key=(
                    correct_submission_dedupe_key(challenge_id, user) if is_correct else None
                ),
            )

            if is_correct:
                blood_level = ScoringService.record_first_solve(
                    challenge.game_id,
                    challenge_id,
                    user_id,
                    user.team_id,
                )

                # 先落库当前正确提交，再按最新 accepted_count 全员回写衰减分
                db.session.add(submission)
                db.session.flush()

                ScoringService.recalculate_challenge_scores(challenge_id)
                db.session.refresh(submission)

                blood_names = ['一血', '二血', '三血']
                if blood_level is not None:
                    notice = CtfGameNotice(
                        game_id=challenge.game_id,
                        notice_type=blood_level + 1,
                        title=f"{blood_names[blood_level]} - {user.username} 解决了 {challenge.title}",
                        content=f"用户 {user.username} 获得了{blood_names[blood_level]}",
                    )
                    db.session.add(notice)

                if status == AnswerResult.CHEAT_DETECTED:
                    similar_users = CheatDetectionService.detect_similar_flags(
                        answer, challenge_id, user_id
                    )
                    for similar_user_id, similarity in similar_users:
                        cheat_info = CtfCheatInfo(
                            game_id=challenge.game_id,
                            submission_id=submission.id,
                            source_user_id=user_id,
                            target_user_id=similar_user_id,
                            similarity=similarity,
                        )
                        db.session.add(cheat_info)
                    return submission, status

                return submission, status

            db.session.add(submission)
            return submission, status

    try:
        submission, status = run_transaction_with_retry(_persist_submission)
    except RuntimeError as exc:
        if str(exc) == "submit_busy":
            return error_response("提交处理中，请稍候再试", 429)
        if str(exc) == "submit_limit":
            return error_response("Submission limit exceeded", 429)
        raise
    except IntegrityError:
        db.session.rollback()
        return error_response("Already solved", 400)
    except (OperationalError, DBAPIError) as exc:
        if is_deadlock_error(exc):
            return error_response("系统繁忙，请稍后重试", 503)
        raise

    if submission is None:
        return error_response(
            "Already solved" if status == 2 else "Submit failed",
            400 if status == 2 else 400,
        )

    rs = get_redis()
    if rs and rs.is_available():
        ScoreboardCache.invalidate_scoreboard(rs, challenge.game_id)
    
    from backend.services.flag_redact import sanitize_submission_dict
    result = sanitize_submission_dict(submission.to_dict(), include_answer=False)
    result['message'] = {
        0: 'Correct!',
        1: 'Wrong answer',
        2: 'Already solved',
        3: 'Correct!',  # 作弊记录仅写库，不向选手暴露
    }.get(status, 'Unknown')
    result['is_correct'] = bool(submission.is_correct)
    
    return success_response(result)


# ======================== 排行榜 API ========================

@bp.route("/games/<int:game_id>/scoreboard", methods=["GET"])
def get_scoreboard(game_id):
    """获取完整排行榜 - Team-based（批量预加载，避免 N+1）"""
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("CtfGame not found", 404)

    rs = get_redis()
    if rs and rs.is_available():
        cached = ScoreboardCache.get_cached_scoreboard(rs, game_id)
        if cached:
            resp = success_response(cached)
            resp[0].headers["X-Cache"] = "HIT"
            return resp

    # 预加载 team + members，避免逐行 Team.query.get / len(team.users)
    scoreboards = (
        CtfScoreboard.query.filter_by(game_id=game_id)
        .options(joinedload(CtfScoreboard.team).selectinload(Team.users))
        .order_by(
            CtfScoreboard.total_points.desc(),
            CtfScoreboard.last_submission_time.asc(),
        )
        .all()
    )

    # 缺 last_submission_time 时一次 GROUP BY 补齐，避免逐队 resolve_last_submission_time
    missing_team_ids = [
        sb.team_id for sb in scoreboards
        if sb.team_id and not sb.last_submission_time
    ]
    last_by_team = {}
    if missing_team_ids:
        rows = (
            db.session.query(
                CtfChallengeSubmission.team_id,
                func.max(CtfChallengeSubmission.submitted_at),
            )
            .filter(
                CtfChallengeSubmission.game_id == game_id,
                CtfChallengeSubmission.is_correct.is_(True),
                CtfChallengeSubmission.team_id.in_(missing_team_ids),
            )
            .group_by(CtfChallengeSubmission.team_id)
            .all()
        )
        last_by_team = {tid: ts for tid, ts in rows if tid}

    missing_user_ids = [
        sb.user_id for sb in scoreboards
        if not sb.team_id and sb.user_id and not sb.last_submission_time
    ]
    last_by_user = {}
    if missing_user_ids:
        rows = (
            db.session.query(
                CtfChallengeSubmission.user_id,
                func.max(CtfChallengeSubmission.submitted_at),
            )
            .filter(
                CtfChallengeSubmission.game_id == game_id,
                CtfChallengeSubmission.is_correct.is_(True),
                CtfChallengeSubmission.user_id.in_(missing_user_ids),
            )
            .group_by(CtfChallengeSubmission.user_id)
            .all()
        )
        last_by_user = {uid: ts for uid, ts in rows if uid}

    rankings = []
    for idx, sb in enumerate(scoreboards, 1):
        team = sb.team
        last_time = sb.last_submission_time
        if not last_time:
            if sb.team_id:
                last_time = last_by_team.get(sb.team_id)
            elif sb.user_id:
                last_time = last_by_user.get(sb.user_id)
        school = None
        motto = None
        members = []
        if team:
            school = getattr(team, 'school', None) or getattr(team, 'tag', None)
            motto = getattr(team, 'motto', None) or getattr(team, 'bio', None) or None
            members = list(team.users or [])
            if not school:
                for u in members:
                    if getattr(u, 'school', None):
                        school = u.school
                        break
        rankings.append({
            'rank': idx,
            'team_id': sb.team_id,
            'team_name': team.name if team else 'Unknown',
            'team_school': school or '无组织',
            'team_motto': motto or '',
            'total_points': sb.total_points,
            'solved_challenges': sb.solved_challenges,
            'last_submission_time': last_time.isoformat() if last_time else None,
            'members_count': len(members),
        })

    payload = {
        'rankings': rankings,
        'total': len(rankings)
    }
    if rs and rs.is_available():
        ScoreboardCache.cache_scoreboard(rs, game_id, payload)

    resp = success_response(payload)
    resp[0].headers["X-Cache"] = "MISS"
    return resp


@bp.route("/games/<int:game_id>/scoreboard/timeline", methods=["GET"])
def get_scoreboard_timeline(game_id):
    """GZCTF 式 Snapshot Replay 积分时间线（可下挫，带 Redis 快照缓存）"""
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("CtfGame not found", 404)

    payload = ScoringService.get_timeline_cached(game_id, top_n=10)
    resp = success_response(payload)
    try:
        resp[0].headers["X-Timeline-Cache"] = "HIT" if payload.get("from_cache") else "MISS"
        resp[0].headers["X-Timeline-Algo"] = str(payload.get("algorithm") or "")
    except Exception:
        pass
    return resp


@bp.route("/games/<int:game_id>/scoreboard/user", methods=["GET"])
@jwt_required()
def get_user_scoreboard(game_id):
    """获取用户及其队伍在该竞赛的排行信息 - Team-based"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    team = ensure_user_has_team(user)
    if not team:
        return error_response("Failed to create solo team", 500)
    
    scoreboard = CtfScoreboard.query.filter_by(
        game_id=game_id,
        team_id=team.id
    ).first()

    # 获取团队参赛记录（未参赛也不应 404，前端会当「暂无成绩」）
    participation = CtfParticipation.query.filter_by(
        game_id=game_id,
        team_id=team.id
    ).first()

    if not scoreboard:
        return success_response({
            'team_id': team.id,
            'team_name': team.name,
            'total_points': 0,
            'solved_challenges': 0,
            'rank': None,
            'last_submission_time': None,
            'status': participation.status if participation else 'not_joined',
            'joined': bool(participation),
        })

    team_rank = ScoringService.get_team_rank(game_id, team.id)

    return success_response({
        'team_id': team.id,
        'team_name': team.name,
        'total_points': scoreboard.total_points,
        'solved_challenges': scoreboard.solved_challenges,
        'rank': team_rank,
        'last_submission_time': scoreboard.last_submission_time.isoformat() if scoreboard.last_submission_time else None,
        'status': participation.status if participation else 'unknown',
        'joined': bool(participation),
    })


# ======================== 容器管理 API ========================

@bp.route("/challenges/<int:challenge_id>/start-instance", methods=["POST"])
@jwt_required()
@rate_limit(key_func=_container_start_rate_key, max_requests=8, window_seconds=60, error_message="启容器过于频繁，请稍后再试")
def start_container_instance(challenge_id):
    """启动容器实例（用于动态题目）"""
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        pass

    challenge = CtfChallenge.query.get(challenge_id)
    if not challenge:
        return error_response("Challenge not found", 404)

    # 检查是否支持容器
    if challenge.challenge_type not in [ChallengeCType.STATIC_CONTAINER, ChallengeCType.DYNAMIC_CONTAINER]:
        return error_response("Challenge does not support containers", 400)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    if not user.is_admin and not PermissionService.has_container_permission(
        user_id, challenge.game_id, challenge_id
    ):
        return error_response("Permission denied", 403)

    team = ensure_user_has_team(user)
    if not team:
        return error_response("Failed to create solo team", 500)

    # 检查是否已有运行的实例：同队共享一个靶机
    existing = CtfGameInstance.query.filter_by(
        challenge_id=challenge_id,
        team_id=team.id,
        is_running=True
    ).first()

    if existing:
        url = normalize_connection_url(existing, challenge=challenge)
        if url != (existing.connection_url or ""):
            existing.connection_url = url
            db.session.commit()
        return success_response({
            "instance_id": existing.id,
            "connection_url": url,
            "port": existing.port,
            "expires_at": existing.expires_at.isoformat() if existing.expires_at else None
        }, "Container already running")

    # 使用新的容器服务创建容器
    success, instance, msg = container_service.create_container(
        challenge=challenge,
        user=user,
        team=team,
        expire_hours=2
    )

    if not success:
        return error_response(msg or "Failed to create container", 500)

    return success_response({
        "instance_id": instance.id,
        "connection_url": instance.connection_url,
        "port": instance.port,
        "expires_at": instance.expires_at.isoformat() if instance.expires_at else None
    }, "Container started")


@bp.route("/instances/<int:instance_id>/stop", methods=["POST"])
@jwt_required()
def stop_container_instance(instance_id):
    """停止容器实例"""
    user_id = get_jwt_identity()
    
    instance = CtfGameInstance.query.get(instance_id)
    if not instance:
        return error_response("Instance not found", 404)
    
    # 检查权限
    if instance.user_id != user_id:
        return error_response("Permission denied", 403)
    
        success, msg = container_service.destroy_container(instance)
        if success:
            return success_response(None, "Container stopped")
        else:
            return error_response(msg, 500)


# ======================== 提示系统 API ========================

@bp.route("/challenges/<int:challenge_id>/hints", methods=["GET"])
@jwt_required()
def list_hints(challenge_id):
    """获取题目的所有提示（未访问不返回 hint_text）"""
    user_id = get_jwt_identity()
    
    hints = CtfChallengeHint.query.filter_by(challenge_id=challenge_id).all()
    
    result = []
    for hint in hints:
        access = CtfUserHintAccess.query.filter_by(
            user_id=user_id,
            hint_id=hint.id
        ).first()
        accessed = access is not None
        hint_data = hint.to_dict(include_text=accessed)
        hint_data['accessed'] = accessed
        hint_data['is_accessed'] = accessed
        result.append(hint_data)
    
    return success_response(result)


@bp.route("/hints/<int:hint_id>/access", methods=["POST"])
@jwt_required()
def access_hint(hint_id):
    """查看提示（记录访问）"""
    user_id = get_jwt_identity()
    
    hint = CtfChallengeHint.query.get(hint_id)
    if not hint:
        return error_response("Hint not found", 404)
    
    # 检查是否已查看
    existing = CtfUserHintAccess.query.filter_by(
        user_id=user_id,
        hint_id=hint_id
    ).first()
    
    if not existing:
        access = CtfUserHintAccess(
            user_id=user_id,
            hint_id=hint_id
        )
        db.session.add(access)
        db.session.commit()
    
    return success_response({
        'hint_text': hint.hint_text,
        'penalty_points': hint.penalty_points
    })


# ======================== 公告系统 API ========================

@bp.route("/games/<int:game_id>/notices", methods=["GET"])
def list_game_notices(game_id):
    """获取比赛公告"""
    notices = CtfGameNotice.query.filter_by(game_id=game_id).order_by(
        CtfGameNotice.created_at.desc()
    ).limit(50).all()
    
    result = [n.to_dict() for n in notices]
    return success_response(result)


# ======================== 检查和清理 API ========================

@bp.route("/cleanup/containers", methods=["POST"])
@jwt_required()
def cleanup_containers():
    """清理过期的容器（需要管理员权限）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return error_response("Permission denied", 403)

    cleaned_count, cleaned_ids = container_service.cleanup_expired_containers()

    return success_response({
        'cleaned': cleaned_count,
        'container_ids': cleaned_ids,
    }, f"Cleaned {cleaned_count} containers")


# ======================== 健康检查 ========================

@bp.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return success_response({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })
