"""
CTF 完整功能 API 路由
包含：题目管理、排行榜、容器管理、权限控制、作弊检测等
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
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

bp = Blueprint("ctf_api", __name__, url_prefix="/api/ctf")


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
    """获取竞赛列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    games = CtfGame.query.order_by(CtfGame.start_time.desc()).paginate(
        page=page, per_page=per_page
    )
    
    items = []
    for g in games.items:
        dto = g.to_dict()

        # 题目数
        dto['challenge_count'] = CtfChallenge.query.filter_by(
            game_id=g.id,
            is_enabled=True
        ).count()

        # 参赛人数（公开=参赛用户，非公开=邀请码用户）
        if g.is_public:
            participation_count = CtfParticipatingUser.query.filter_by(
                game_id=g.id
            ).distinct(CtfParticipatingUser.user_id).count()
        else:
            participation_count = CtfUserInviteCode.query.filter_by(
                game_id=g.id
            ).distinct(CtfUserInviteCode.user_id).count()

        dto['participation_count'] = participation_count
        items.append(dto)

    result = {
        'total': games.total,
        'pages': games.pages,
        'current_page': page,
        'items': items
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
    
    # 如果用户已登录，获取其参赛状态
    if 'Authorization' in request.headers:
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
        except:
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
    
    # 检查用户是否加入了队伍
    if not user.team_id:
        return error_response("You must join a team first before participating in games", 403)
    
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
    """获取竞赛的所有分组"""
    divisions = CtfDivision.query.filter_by(game_id=game_id).all()
    
    result = [d.to_dict() for d in divisions]
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
        data = challenge.to_dict()
        
        # 添加解题统计
        solved_count = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge.id,
            is_correct=True
        ).count()
        
        # 计算当前分数
        current_score = ScoringService.calculate_dynamic_score(
            challenge.original_points,
            solved_count,
            challenge.min_score_rate,
            challenge.difficulty
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
    
    result = challenge.to_dict()
    
    # 添加提示
    hints = CtfChallengeHint.query.filter_by(challenge_id=challenge_id).all()
    result['hints'] = [h.to_dict() for h in hints]
    
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
    
    # 检查提交限制
    if challenge.submission_limit > 0:
        attempts = CtfChallengeSubmission.query.filter_by(
            user_id=user_id,
            challenge_id=challenge_id
        ).count()
        
        if attempts >= challenge.submission_limit:
            return error_response("Submission limit exceeded", 400)
    
    # 验证答案
    is_correct, status = FlagValidationService.validate_flag(
        answer,
        challenge_id,
        user_id,
        challenge.game_id
    )
    
    # 记录提交
    submission = CtfChallengeSubmission(
        user_id=user_id,
        team_id=user.team_id,
        challenge_id=challenge_id,
        game_id=challenge.game_id,
        answer=answer,
        is_correct=is_correct,
        status=status
    )
    
    if is_correct:
        # 计算分数
        solved_count = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge_id,
            is_correct=True
        ).count()
        
        score = ScoringService.calculate_dynamic_score(
            challenge.original_points,
            solved_count,
            challenge.min_score_rate,
            challenge.difficulty
        )
        
        # 检查是否获得血液奖励
        blood_level = ScoringService.record_first_solve(
            challenge.game_id,
            challenge_id,
            user_id,
            user.team_id
        )
        
        if blood_level is not None and not challenge.disable_blood_bonus:
            score_with_bonus, bonus_multiplier = ScoringService.calculate_blood_bonus(
                score, blood_level=blood_level
            )
            submission.points_earned = score_with_bonus
        else:
            submission.points_earned = score
        
        # 更新排行榜
        ScoringService.update_scoreboard(
            challenge.game_id,
            user_id,
            user.team_id
        )
        
        # 记录公告
        blood_names = ['一血', '二血', '三血']
        if blood_level is not None:
            notice = CtfGameNotice(
                game_id=challenge.game_id,
                notice_type=blood_level + 1,
                title=f"{blood_names[blood_level]} - {user.username} 解决了 {challenge.title}",
                content=f"用户 {user.username} 获得了{blood_names[blood_level]}"
            )
            db.session.add(notice)
        
        # 如果检测到作弊
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
                    similarity=similarity
                )
                db.session.add(cheat_info)
    
    db.session.add(submission)
    db.session.commit()
    
    result = submission.to_dict()
    result['message'] = {
        0: 'Correct!',
        1: 'Wrong answer',
        2: 'Already solved',
        3: 'Similar flag detected (possible cheating)'
    }.get(status, 'Unknown')
    
    return success_response(result)


# ======================== 排行榜 API ========================

@bp.route("/games/<int:game_id>/scoreboard", methods=["GET"])
def get_scoreboard(game_id):
    """获取完整排行榜 - Team-based"""
    game = CtfGame.query.get(game_id)
    if not game:
        return error_response("CtfGame not found", 404)
    
    # 从 CtfScoreboard 表直接获取排行榜数据（已按 Team 排行）
    scoreboards = CtfScoreboard.query.filter_by(game_id=game_id).order_by(
        CtfScoreboard.total_points.desc(),
        CtfScoreboard.last_submission_time.asc()
    ).all()
    
    # 为每个排行项计算排名和添加团队信息
    rankings = []
    for idx, sb in enumerate(scoreboards, 1):
        sb.rank = idx
        team = Team.query.get(sb.team_id)
        rankings.append({
            'rank': idx,
            'team_id': sb.team_id,
            'team_name': team.name if team else 'Unknown',
            'total_points': sb.total_points,
            'solved_challenges': sb.solved_challenges,
            'last_submission_time': sb.last_submission_time.isoformat() if sb.last_submission_time else None,
            'members_count': len(team.users) if team else 0,
        })
    
    db.session.commit()  # 保存排名更新
    
    return success_response({
        'rankings': rankings,
        'total': len(rankings)
    })


@bp.route("/games/<int:game_id>/scoreboard/user", methods=["GET"])
@jwt_required()
def get_user_scoreboard(game_id):
    """获取用户及其队伍在该竞赛的排行信息 - Team-based"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.team_id:
        return error_response("User or user's team not found", 404)
    
    scoreboard = CtfScoreboard.query.filter_by(
        game_id=game_id,
        team_id=user.team_id
    ).first()
    
    if not scoreboard:
        return error_response("Team not in this game yet", 404)
    
    # 获取团队参赛记录
    participation = CtfParticipation.query.filter_by(
        game_id=game_id,
        team_id=user.team_id
    ).first()
    
    return success_response({
        'team_id': user.team_id,
        'team_name': user.team.name if user.team else 'Unknown',
        'total_points': scoreboard.total_points,
        'solved_challenges': scoreboard.solved_challenges,
        'rank': scoreboard.rank,
        'last_submission_time': scoreboard.last_submission_time.isoformat() if scoreboard.last_submission_time else None,
        'status': participation.status if participation else 'unknown',
    })


# ======================== 容器管理 API ========================

@bp.route("/challenges/<int:challenge_id>/start-instance", methods=["POST"])
@jwt_required()
def start_container_instance(challenge_id):
    """启动容器实例（用于动态题目）"""
    user_id = get_jwt_identity()

    challenge = CtfChallenge.query.get(challenge_id)
    if not challenge:
        return error_response("Challenge not found", 404)

    # 检查是否支持容器
    if challenge.challenge_type not in [ChallengeCType.STATIC_CONTAINER, ChallengeCType.DYNAMIC_CONTAINER]:
        return error_response("Challenge does not support containers", 400)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    # 检查是否已有运行的实例
    existing = CtfGameInstance.query.filter_by(
        challenge_id=challenge_id,
        user_id=user_id,
        is_running=True
    ).first()

    if existing:
        # 返回现有实例
        return success_response({
            "instance_id": existing.id,
            "connection_url": existing.connection_url,
            "port": existing.port,
            "expires_at": existing.expires_at.isoformat() if existing.expires_at else None
        }, "Container already running")

    # 使用新的容器服务创建容器
    success, instance, msg = container_service.create_container(
        challenge=challenge,
        user=user,
        team=None,
        expire_hours=2
    )

    if not success:
        return error_response("Failed to create container", 500)

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
    """获取题目的所有提示"""
    user_id = get_jwt_identity()
    
    hints = CtfChallengeHint.query.filter_by(challenge_id=challenge_id).all()
    
    result = []
    for hint in hints:
        hint_data = hint.to_dict()
        
        # 检查用户是否已查看
        access = CtfUserHintAccess.query.filter_by(
            user_id=user_id,
            hint_id=hint.id
        ).first()
        
        hint_data['accessed'] = access is not None
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
            'container_ids': cleaned_ids
        }, f"Cleaned {cleaned_count} containers")


# ======================== 健康检查 ========================

@bp.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return success_response({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })
