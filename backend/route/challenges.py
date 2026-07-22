"""
CTF 挑战题目相关的API路由 - 完整迁移
包含：Flag检查、排分、血液奖励、作弊检测、提示系统、流量捕获、容器管理
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from urllib.parse import urlparse
import threading
import logging
import docker
from backend.server.extensions import db
from backend.server.db_models import (
    User, Team, CtfGame, CtfChallenge, CtfChallengeSubmission,
    CtfGameInstance, CtfParticipatingUser, CtfScoreboard, CtfSolves,
    CtfCheatInfo, CtfChallengeHint, CtfUserHintAccess, CtfGameNotice,
    CtfHammerMessage,
)
from backend.services.scoring_service import (
    ScoringService, CheatDetectionService, FlagTemplateService
)
from backend.services.flag_generator import resolve_challenge_expected_flag
from backend.services.permission_service import PermissionService, GamePermission
from backend.services.team_service import ensure_user_has_team
from backend.middleware_refactored import submission_rate_limit, rate_limit
from backend.server.security_helpers import user_can_manage_instance
from backend.server.traffic_capture import TrafficCaptureManager

logger = logging.getLogger(__name__)

bp = Blueprint("challenges", __name__)


def _unique_solver_count(challenge_id):
    """唯一解出人数（按 user_id 去重）。"""
    from sqlalchemy import func
    return int(
        db.session.query(func.count(func.distinct(CtfChallengeSubmission.user_id)))
        .filter(
            CtfChallengeSubmission.challenge_id == challenge_id,
            CtfChallengeSubmission.is_correct.is_(True),
        )
        .scalar()
        or 0
    )


def _unique_solver_counts(challenge_ids):
    """批量统计多题唯一解出人数。"""
    if not challenge_ids:
        return {}
    from sqlalchemy import func
    rows = (
        db.session.query(
            CtfChallengeSubmission.challenge_id,
            func.count(func.distinct(CtfChallengeSubmission.user_id)),
        )
        .filter(
            CtfChallengeSubmission.challenge_id.in_(list(challenge_ids)),
            CtfChallengeSubmission.is_correct.is_(True),
        )
        .group_by(CtfChallengeSubmission.challenge_id)
        .all()
    )
    return {int(cid): int(cnt) for cid, cnt in rows}



def _challenge_supports_container(challenge) -> bool:
    """题目是否支持动态/静态容器环境。"""
    if not challenge:
        return False
    if getattr(challenge, "docker_image", None):
        return True
    try:
        ctype = int(getattr(challenge, "challenge_type", 0) or 0)
    except (TypeError, ValueError):
        ctype = 0
    return ctype in (1, 3)  # StaticContainer / DynamicContainer


def _attach_container_meta(data, challenge):
    """对齐前端：supports_container / needs_container / has_container(能力标记)。"""
    ok = _challenge_supports_container(challenge)
    data["supports_container"] = ok
    data["needs_container"] = ok
    # 注意：container-status 里的 has_container 表示「是否正在运行」；
    # 题目详情里用同名字段表示「是否支持容器」，并额外提供 supports_container。
    data["has_container"] = ok
    try:
        data["challenge_type"] = int(getattr(challenge, "challenge_type", 0) or 0)
    except (TypeError, ValueError):
        data["challenge_type"] = 0
    if getattr(challenge, "docker_image", None):
        data["docker_image"] = challenge.docker_image
    return data


def _attach_solve_stats(data, challenge_id, solves=None):
    """对齐前端字段：solves / solved_count / solves_count。"""
    if solves is None:
        solves = _unique_solver_count(challenge_id)
    solves = int(solves or 0)
    data["solves"] = solves
    data["solved_count"] = solves
    data["solves_count"] = solves
    return data



def _container_start_rate_key():
    try:
        return f"container_start:{get_jwt_identity()}"
    except Exception:
        return f"container_start:ip:{request.remote_addr}"


def _find_running_instance(challenge_id, user, user_id):
    """与 container_challenges 保持一致：有队伍按队伍，无队伍按用户。"""
    if user and user.team_id:
        return CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            team_id=user.team_id,
            is_running=True,
        ).first()
    return CtfGameInstance.query.filter_by(
        challenge_id=challenge_id,
        user_id=user_id,
        is_running=True,
    ).first()


def _is_training_game(game):
    if not game:
        return False
    return game.game_type in ("training", "practice") or game.status == "archived"


from backend.server.submit_audit import (
    request_client_ip as _request_client_ip,
    resolve_submit_duration_ms as _resolve_submit_duration_ms,
)
from backend.server.container_access import normalize_connection_url as _normalize_connection_url_impl


def _normalize_connection_url(instance, challenge=None):
    """使用公网主机 + 实例 port 修正 connection_url。"""
    return _normalize_connection_url_impl(instance, challenge=challenge)


# ======================== 获取题目列表 ========================

@bp.route("/games/<int:game_id>/challenges", methods=["GET"])
def get_game_challenges(game_id):
    """获取某个竞赛的所有挑战题目"""
    try:
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404

        challenges = CtfChallenge.query.filter_by(
            game_id=game_id, is_enabled=True
        ).all()

        counts = _unique_solver_counts([c.id for c in challenges])
        payload = []
        for c in challenges:
            item = c.to_public_dict()
            _attach_solve_stats(item, c.id, counts.get(c.id, 0))
            _attach_container_meta(item, c)
            payload.append(item)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": payload
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:challenge_id>", methods=["GET"])
@jwt_required()
def get_challenge_detail(challenge_id):
    """获取题目详情"""
    try:
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        try:
            uid_int = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"code": 401, "msg": "无效用户"}), 401

        if not user.is_admin and not PermissionService.check_challenge_permission(
            uid_int, challenge_id, GamePermission.VIEW_CHALLENGE
        ):
            return jsonify({"code": 403, "msg": "无权访问该题目"}), 403

        # 获取队伍的提交记录；无队伍时回退到个人
        if user and user.team_id:
            submissions = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge_id,
                team_id=user.team_id
            ).all()
        else:
            submissions = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge_id,
                user_id=user_id
            ).all()

        data = challenge.to_public_dict()
        if user and user.is_admin:
            data['flag'] = challenge.flag
            data['flag_template'] = challenge.flag_template
        include_answer = bool(user and user.is_admin)
        data['submissions'] = [
            s.to_dict() if include_answer else {k: v for k, v in s.to_dict().items() if k != 'answer'}
            for s in submissions
        ]
        data['submission_count'] = len(submissions)
        
        # 检查是否已解决
        solved = any(s.is_correct for s in submissions)
        data['is_solved'] = solved
        _attach_solve_stats(data, challenge_id)
        _attach_container_meta(data, challenge)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:challenge_id>/submissions", methods=["GET"])
@jwt_required()
def my_submissions(challenge_id):
    """当前用户在某题的提交列表"""
    try:
        uid = int(get_jwt_identity())
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        user = User.query.get(uid)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        if user.team_id:
            subs = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge_id,
                team_id=user.team_id,
            ).order_by(CtfChallengeSubmission.submitted_at.desc()).all()
        else:
            subs = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge_id,
                user_id=uid,
            ).order_by(CtfChallengeSubmission.submitted_at.desc()).all()

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "items": [
                    {
                        "id": s.id,
                        "correct": s.is_correct,
                        "created_at": s.submitted_at.isoformat() if s.submitted_at else None,
                    }
                    for s in subs
                ],
            },
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 提交Flag ========================

@bp.route("/<int:challenge_id>/submit", methods=["POST"])
@jwt_required()
@submission_rate_limit()
def submit_flag(challenge_id):
    """
    提交Flag - 完整迁移版本
    包含：
    - 答案验证
    - 动态分数计算
    - 血液奖励
    - 首解记录
    - 作弊检测
    - 排分更新
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        game = CtfGame.query.get(challenge.game_id)
        if not game:
            return jsonify({"code": 404, "msg": "比赛不存在"}), 404

        is_training = _is_training_game(game)

        if not is_training:
            team = ensure_user_has_team(user)
            if not team:
                return jsonify({
                    "code": 500,
                    "msg": "自动创建单人队失败"
                }), 500

        # ✓ 检查：用户是否加入了该比赛
        participation = CtfParticipatingUser.query.filter_by(
            user_id=user_id,
            game_id=game.id
        ).first()
        
        if not participation:
            return jsonify({
                "code": 403,
                "msg": "您未加入该比赛，请先加入比赛"
            }), 403

        # ✓ 检查：正式赛事需已开始；训练场永久开放
        if not is_training and datetime.utcnow() < game.start_time:
            return jsonify({
                "code": 403,
                "msg": "比赛还未开始，无法提交答案"
            }), 403

        if not is_training and game.archived_at is not None:
            return jsonify({
                "code": 403,
                "msg": "该比赛已归档，无法提交答案计分"
            }), 403

        data = request.get_json() or {}
        answer = (data.get("answer") or data.get("flag") or "").strip()
        
        if not answer:
            return jsonify({"code": 400, "msg": "答案不能为空"}), 400

        # 检查是否已经解决过（加题目行锁，防并发重复计分/抢血）
        from backend.services.submit_lock import (
            lock_challenge_row,
            redis_submit_lock,
            submission_owner_key,
            correct_submission_dedupe_key,
        )
        from backend.services.flag_redact import sanitize_submission_dict
        from sqlalchemy.exc import IntegrityError

        owner_key = submission_owner_key(user)
        with redis_submit_lock(challenge_id, owner_key) as got_lock:
            if not got_lock:
                return jsonify({"code": 429, "msg": "提交处理中，请稍候再试"}), 429

            locked = lock_challenge_row(challenge_id)
            if not locked:
                return jsonify({"code": 404, "msg": "题目不存在"}), 404
            challenge = locked

            # 提交次数限制放在锁内，避免 TOCTOU 超限
            if challenge.submission_limit > 0:
                submission_count = CtfChallengeSubmission.query.filter_by(
                    user_id=user_id,
                    challenge_id=challenge_id
                ).count()
                if submission_count >= challenge.submission_limit:
                    return jsonify({
                        "code": 429,
                        "msg": f"已达到提交限制（{challenge.submission_limit}次）"
                    }), 429

            solved_query = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge_id,
                is_correct=True
            )
            if user.team_id:
                solved_query = solved_query.filter_by(team_id=user.team_id)
            else:
                solved_query = solved_query.filter_by(user_id=user_id)
            solved = solved_query.with_for_update().first()

            if solved:
                return jsonify({
                    "code": 400,
                    "msg": "您已经解决过这个题目",
                    "data": {
                        "is_correct": True,
                        "submission": sanitize_submission_dict(solved.to_dict(), include_answer=False),
                    }
                }), 400

            running_instance = _find_running_instance(challenge_id, user, user_id)
            expected_flag = resolve_challenge_expected_flag(
                challenge, user, user_id, running_instance=running_instance,
            )

            is_correct = bool(expected_flag) and (answer.strip() == expected_flag)

            duration_ms = _resolve_submit_duration_ms(data, running_instance)
            client_ip = _request_client_ip()
            
            submission = CtfChallengeSubmission(
                user_id=user_id,
                team_id=user.team_id,
                challenge_id=challenge_id,
                game_id=challenge.game_id,
                answer=answer,
                is_correct=is_correct,
                points_earned=0,
                submitted_at=datetime.utcnow(),
                client_ip=client_ip,
                duration_ms=duration_ms,
                correct_dedupe_key=(
                    correct_submission_dedupe_key(challenge_id, user) if is_correct else None
                ),
            )

            db.session.add(submission)

            response_data = {
                "is_correct": is_correct,
                "submission": None,  # 提交后刷新
            }

            # 如果答案正确，执行排分逻辑
            if is_correct:
                if is_training:
                    # 训练场 / 练习 / 已归档：只记提交与固定分，不污染血榜、公告、正式积分、赛季
                    submission.points_earned = int(challenge.points or 0)
                    response_data['final_score'] = submission.points_earned
                    response_data['training_mode'] = True
                    response_data['blood_level'] = None
                else:
                    # 1. 获取该题目的已解题队伍数（用于动态分数计算）
                    accepted_count = CtfChallengeSubmission.query.filter_by(
                        challenge_id=challenge_id,
                        is_correct=True
                    ).count()

                    # 2. 计算动态分数
                    dynamic_score = ScoringService.calculate_dynamic_score(
                        challenge.points,
                        accepted_count + 1,  # 包括当前提交
                        min_score_rate=0.25,
                        difficulty=5.0
                    )

                    submission.points_earned = dynamic_score

                    # 3. 检查是否为首解/二解/三解
                    blood_level = ScoringService.record_first_solve(
                        game_id=challenge.game_id,
                        challenge_id=challenge_id,
                        user_id=user_id,
                        team_id=user.team_id
                    )

                    response_data['blood_level'] = blood_level

                    # 4. 计算血液奖励
                    if blood_level is not None:
                        bonus_score, multiplier = ScoringService.calculate_blood_bonus(
                            dynamic_score,
                            (50 << 20) | (30 << 10) | 10,  # 一血5% 二血3% 三血1%
                            blood_level
                        )
                        submission.points_earned = bonus_score
                        response_data['bonus_multiplier'] = multiplier
                        response_data['final_score'] = bonus_score

                        # 发送首血公告
                        blood_names = ["一血", "二血", "三血"]
                        notice = CtfGameNotice(
                            game_id=challenge.game_id,
                            notice_type=blood_level + 1,
                            title=f"{blood_names[blood_level]}! {user.username} 解决了 {challenge.title}",
                            content=f"恭喜 {user.username} 获得{blood_names[blood_level]}！"
                        )
                        db.session.add(notice)
                    else:
                        response_data['final_score'] = dynamic_score

                    # 5. 作弊检测
                    similar_users = CheatDetectionService.detect_similar_flags(
                        answer,
                        challenge_id,
                        user_id,
                        similarity_threshold=0.95
                    )

                    if similar_users:
                        for cheat_user_id, similarity in similar_users:
                            cheat_info = CtfCheatInfo(
                                game_id=challenge.game_id,
                                submission_id=submission.id,
                                source_user_id=user_id,
                                target_user_id=cheat_user_id,
                                similarity=similarity
                            )
                            db.session.add(cheat_info)
                        # 作弊信息仅写库，不回传相似用户数给选手

                    # 6. 更新排分表
                    ScoringService.update_scoreboard(
                        game_id=challenge.game_id,
                        user_id=user_id,
                        team_id=user.team_id
                    )

                    # 7. 更新赛季统计（如果比赛属于某个赛季）
                    from backend.services.season_stats_service import SeasonStatsService
                    try:
                        SeasonStatsService.trigger_on_challenge_solved(user_id, user.team_id, challenge.game_id)
                    except Exception as e:
                        # 赛季统计更新失败不影响主流程
                        import logging
                        logging.warning(f"赛季统计更新失败: {e}")

                # 8. Flag正确时，自动销毁对应的容器
                from flask import current_app
                _app = current_app._get_current_object()

                def destroy_container_async():
                    with _app.app_context():
                        try:
                            instance = CtfGameInstance.query.filter_by(
                                challenge_id=challenge_id,
                                team_id=user.team_id,
                                is_running=True
                            ).first()
                            
                            if instance and instance.container_id:
                                try:
                                    docker_client = docker.from_env()
                                    container = docker_client.containers.get(instance.container_id)
                                    container.stop(timeout=5)
                                    container.remove(force=True)
                                    logger.info(f"Container {instance.container_id[:12]} destroyed after correct flag")
                                except docker.errors.NotFound:
                                    logger.info(
                                        f"Container {instance.container_id[:12]} already gone after correct flag"
                                    )
                                except Exception as e:
                                    err = str(e).lower()
                                    if "no such container" in err or "404" in err:
                                        logger.info(
                                            f"Container {instance.container_id[:12]} already gone after correct flag"
                                        )
                                    else:
                                        logger.warning(f"Failed to destroy container after correct flag: {e}")
                                instance.is_running = False
                                db.session.commit()
                        except Exception as e:
                            logger.warning(f"destroy_container_async failed: {e}")

                if not is_training:
                    threading.Thread(target=destroy_container_async, daemon=True).start()

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify({
                    "code": 400,
                    "msg": "您已经解决过这个题目",
                    "data": {"is_correct": True},
                }), 400

            response_data['submission'] = sanitize_submission_dict(
                submission.to_dict(), include_answer=False,
            )
            # 提交事务后回传最新唯一解出人数，供前端即时刷新 solves
            solves_now = _unique_solver_count(challenge_id)
            response_data['solves'] = solves_now
            response_data['solved_count'] = solves_now
            response_data['solves_count'] = solves_now
            response_data['unique_solvers'] = solves_now

            return jsonify({
                "code": 200,
                "msg": "恭喜，答案正确！" if is_correct else "答案错误",
                "data": response_data,
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 排分相关API ========================

@bp.route("/games/<int:game_id>/scoreboard", methods=["GET"])
def get_scoreboard(game_id):
    """获取比赛实时排行榜"""
    try:
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "比赛不存在"}), 404

        rankings = ScoringService.calculate_rankings(game_id)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": rankings
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/games/<int:game_id>/first-solves", methods=["GET"])
def get_first_solves(game_id):
    """获取首解/二解/三解记录"""
    try:
        first_solves = CtfSolves.query.filter_by(game_id=game_id).all()
        user_ids = {fs.user_id for fs in first_solves if fs.user_id}
        team_ids = {fs.team_id for fs in first_solves if fs.team_id}
        challenge_ids = {fs.challenge_id for fs in first_solves if fs.challenge_id}
        users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
        teams = {t.id: t for t in Team.query.filter(Team.id.in_(team_ids)).all()} if team_ids else {}
        challenges = {
            c.id: c for c in CtfChallenge.query.filter(CtfChallenge.id.in_(challenge_ids)).all()
        } if challenge_ids else {}

        data = []
        for fs in first_solves:
            row = fs.to_dict()
            user = users.get(fs.user_id)
            team = teams.get(fs.team_id)
            challenge = challenges.get(fs.challenge_id)
            row['user_name'] = (user.nickname or user.username) if user else None
            row['team_name'] = team.name if team else None
            row['challenge_title'] = challenge.title if challenge else None
            data.append(row)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 提示系统 ========================

@bp.route("/<int:challenge_id>/hints", methods=["GET"])
@jwt_required()
def get_hints(challenge_id):
    """获取题目提示列表"""
    try:
        user_id = get_jwt_identity()
        
        hints = CtfChallengeHint.query.filter_by(challenge_id=challenge_id).all()

        # 标记已查看的提示
        user_accesses = CtfUserHintAccess.query.filter_by(user_id=user_id).all()
        accessed_hint_ids = {ua.hint_id for ua in user_accesses}

        hints_data = []
        for hint in hints:
            accessed = hint.id in accessed_hint_ids
            hint_dict = hint.to_dict(include_text=accessed)
            hint_dict['is_accessed'] = accessed
            hints_data.append(hint_dict)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": hints_data
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:hint_id>/access-hint", methods=["POST"])
@jwt_required()
def access_hint(hint_id):
    """查看题目提示"""
    try:
        user_id = get_jwt_identity()
        
        hint = CtfChallengeHint.query.get(hint_id)
        if not hint:
            return jsonify({"code": 404, "msg": "提示不存在"}), 404

        # 记录访问
        access = CtfUserHintAccess(user_id=user_id, hint_id=hint_id)
        db.session.add(access)

        # 扣分（如果配置了的话）
        if hint.penalty_points > 0:
            scoreboard = CtfScoreboard.query.filter_by(user_id=user_id).first()
            if scoreboard:
                scoreboard.total_points = max(0, scoreboard.total_points - hint.penalty_points)

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "hint": hint.to_dict(include_text=True),
                "penalty": hint.penalty_points
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 作弊检测 ========================

@bp.route("/games/<int:game_id>/cheat-info", methods=["GET"])
@jwt_required()
def get_cheat_info(game_id):
    """获取作弊检测信息 - 仅管理员可用"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权访问"}), 403

        cheat_infos = CtfCheatInfo.query.filter_by(game_id=game_id).all()

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": [ci.to_dict() for ci in cheat_infos]
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 容器相关 ========================

@bp.route("/<int:challenge_id>/container-status", methods=["GET"])
@jwt_required()
def get_container_status(challenge_id):
    """
    获取用户该题目的容器状态
    返回: 
    - no_container: 没有运行中的容器 (显示"开启容器"按钮)
    - running: 有运行中的容器 (显示"查看容器"按钮)
    - expired: 容器已过期 (自动销毁，显示"开启容器"按钮)
    """
    try:
        user_id = get_jwt_identity()
        # 处理user_id类型转换（可能是字符串）
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            pass
        
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404
        
        user = User.query.get(user_id)
        scope_team_id = user.team_id if user and user.team_id else None

        # 首先清理该队伍/用户所有过期的容器实例
        expired_query = CtfGameInstance.query.filter(
            CtfGameInstance.is_running == True,
            CtfGameInstance.expires_at < datetime.utcnow()
        )
        if scope_team_id:
            expired_instances = expired_query.filter(CtfGameInstance.team_id == scope_team_id).all()
        else:
            expired_instances = expired_query.filter(CtfGameInstance.user_id == user_id).all()
        
        for expired in expired_instances:
            if expired.container_id:
                try:
                    docker_client = docker.from_env()
                    container = docker_client.containers.get(expired.container_id)
                    container.stop(timeout=5)
                    container.remove(force=True)
                except:
                    pass
            expired.is_running = False
        
        if expired_instances:
            db.session.commit()
            logger.info(f"Marked {len(expired_instances)} expired containers as stopped for user {user_id}")
        
        # 查询运行中的容器：同队共享一个实例
        if scope_team_id:
            instance = CtfGameInstance.query.filter_by(
                challenge_id=challenge_id,
                team_id=scope_team_id,
                is_running=True
            ).first()
        else:
            instance = CtfGameInstance.query.filter_by(
                challenge_id=challenge_id,
                user_id=user_id,
                is_running=True
            ).first()
        
        if not instance:
            return jsonify({
                "code": 200,
                "data": {
                    "status": "no_container",
                    "has_container": False,
                    "message": "没有运行中的容器，可以开启"
                }
            }), 200
        
        # 检查是否已过期
        remaining_seconds = 0
        if instance.expires_at:
            remaining = (instance.expires_at - datetime.utcnow()).total_seconds()
            remaining_seconds = max(0, int(remaining))
            
            if remaining_seconds <= 0:
                # 自动销毁过期容器
                if instance.container_id:
                    try:
                        docker_client = docker.from_env()
                        container = docker_client.containers.get(instance.container_id)
                        container.stop(timeout=5)
                        container.remove(force=True)
                    except:
                        pass
                
                instance.is_running = False
                db.session.commit()
                
                return jsonify({
                    "code": 200,
                    "data": {
                        "status": "expired",
                        "has_container": False,
                        "message": "容器已过期，已自动销毁"
                    }
                }), 200
        
        # 与 Docker 实际状态对账：Exited/Dead/Missing 时勿再显示「运行中」
        if instance.container_id:
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                container.reload()
                if container.status != "running":
                    logger.warning(
                        "Instance %s docker status=%s, marking stopped",
                        instance.id,
                        container.status,
                    )
                    instance.is_running = False
                    db.session.commit()
                    return jsonify({
                        "code": 200,
                        "data": {
                            "status": "no_container",
                            "has_container": False,
                            "message": f"容器已停止（Docker: {container.status}），请重新启动",
                        },
                    }), 200
            except Exception as e:
                logger.warning("Instance %s docker check failed: %s", instance.id, e)
                instance.is_running = False
                db.session.commit()
                return jsonify({
                    "code": 200,
                    "data": {
                        "status": "no_container",
                        "has_container": False,
                        "message": "容器已不存在，请重新启动",
                    },
                }), 200

        # 容器正在运行
        normalized_url = _normalize_connection_url(instance, challenge=challenge)
        if normalized_url != (instance.connection_url or ""):
            logger.warning(
                f"Normalized instance {instance.id} connection_url from {instance.connection_url} to {normalized_url}"
            )
            instance.connection_url = normalized_url
            db.session.commit()

        return jsonify({
            "code": 200,
            "data": {
                "status": "running",
                "has_container": True,
                "instance_id": instance.id,
                "container_id": instance.container_id[:12] if instance.container_id else None,
                "connection_url": normalized_url,
                "created_at": instance.started_at.isoformat() if instance.started_at else None,
                "expires_at": instance.expires_at.isoformat() if instance.expires_at else None,
                "remaining_seconds": remaining_seconds,
                "message": f"容器正在运行，剩余{remaining_seconds}秒"
            }
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:challenge_id>/start-container", methods=["POST"])
@jwt_required()
@rate_limit(key_func=_container_start_rate_key, max_requests=8, window_seconds=60, error_message="启容器过于频繁，请稍后再试")
def start_container(challenge_id):
    """启动题目容器 - 支持流量捕获"""
    try:
        user_id = get_jwt_identity()
        # 处理user_id类型转换（可能是字符串）
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            pass
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401
        
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        if not user.is_admin and not PermissionService.check_challenge_permission(
            user_id, challenge_id, GamePermission.VIEW_CHALLENGE
        ):
            return jsonify({"code": 403, "msg": "无权启动该题目容器"}), 403

        if not challenge.docker_image:
            return jsonify({"code": 400, "msg": "该题目不支持容器（未配置镜像）"}), 400

        team = ensure_user_has_team(user)
        if not team:
            return jsonify({"code": 500, "msg": "自动创建单人队失败"}), 500

        # 检查是否已有运行中的实例：同队共享一个靶机（须与 Docker 实际状态对账）
        existing_instance = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            team_id=team.id,
            is_running=True
        ).first()

        if existing_instance:
            alive = False
            if existing_instance.container_id:
                try:
                    docker_client = docker.from_env()
                    container = docker_client.containers.get(existing_instance.container_id)
                    container.reload()
                    alive = container.status == "running"
                except Exception:
                    alive = False
            if alive:
                normalized_url = _normalize_connection_url(existing_instance, challenge=challenge)
                if normalized_url != (existing_instance.connection_url or ""):
                    existing_instance.connection_url = normalized_url
                    db.session.commit()
                return jsonify({
                    "code": 200,
                    "msg": "容器已启动",
                    "data": {
                        "instance_id": existing_instance.id,
                        "connection_url": normalized_url,
                        "port": existing_instance.port,
                        "expires_at": existing_instance.expires_at.isoformat() if existing_instance.expires_at else None
                    }
                }), 200
            # DB 仍标运行但 Docker 已挂：清掉后继续创建
            existing_instance.is_running = False
            db.session.commit()
            logger.warning(
                "Cleared ghost instance %s for challenge %s before restart",
                existing_instance.id,
                challenge_id,
            )

        from backend.services.instance_quota import check_can_start_new_instance
        ok_quota, quota_msg, _ = check_can_start_new_instance(user, team, challenge_id=challenge_id)
        if not ok_quota:
            return jsonify({"code": 429, "msg": quota_msg}), 429

        # 使用新的容器服务创建容器（Redis 可用时入队限并发）
        from backend.services.container_start_queue import create_container_queued, enqueue_container_start
        body = request.get_json(silent=True) or {}
        async_mode = str(
            request.args.get("async") or body.get("async") or ""
        ).lower() in ("1", "true", "yes")

        if async_mode:
            ok, job_id, msg, meta = enqueue_container_start(
                challenge=challenge, user=user, team=team, expire_hours=2,
            )
            if not ok:
                return jsonify({"code": 500, "msg": msg or "入队失败"}), 500
            if not job_id:
                # 同步完成（勿在函数内再 import CtfGameInstance，会遮蔽顶层导入导致 UnboundLocalError）
                inst = CtfGameInstance.query.get(meta.get("instance_id")) if meta.get("instance_id") else None
                if not inst:
                    return jsonify({"code": 500, "msg": "启动成功但实例丢失"}), 500
                return jsonify({
                    "code": 200,
                    "msg": msg,
                    "data": {
                        "queued": False,
                        "status": "done",
                        "instance_id": inst.id,
                        "connection_url": inst.connection_url,
                        "port": inst.port,
                        "expires_at": inst.expires_at.isoformat() if inst.expires_at else None,
                    },
                }), 200
            return jsonify({
                "code": 202,
                "msg": msg,
                "data": {
                    "queued": True,
                    "job_id": job_id,
                    "status": meta.get("status") or "queued",
                    "position": meta.get("position"),
                    "queue_length": meta.get("queue_length"),
                },
            }), 202

        success, instance, msg = create_container_queued(
            challenge=challenge,
            user=user,
            team=team,
            expire_hours=2
        )

        if not success:
            logger.error(f"Failed to create container for challenge {challenge_id}: {msg}")
            return jsonify({"code": 500, "msg": f"容器启动失败: {msg}"}), 500

        return jsonify({
            "code": 200,
            "msg": "容器启动成功",
            "data": {
                "instance_id": instance.id,
                "connection_url": instance.connection_url,
                "port": instance.port,
                "expires_at": instance.expires_at.isoformat() if instance.expires_at else None
            }
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/container-jobs/<job_id>", methods=["GET"])
@jwt_required()
def get_container_job(job_id):
    """查询异步启容器任务进度"""
    from backend.services.container_start_queue import get_job_status
    st = get_job_status(job_id)
    code = 200
    if st.get("status") == "unknown":
        code = 404
    return jsonify({"code": code if code != 404 else 404, "msg": st.get("msg") or "ok", "data": st}), (404 if code == 404 else 200)


@bp.route("/instances/<int:instance_id>/logs", methods=["GET"])
@jwt_required()
def get_instance_logs(instance_id):
    """容器日志（非交互 Shell；G42 MVP）"""
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"code": 401, "msg": "未登录"}), 401
    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 401, "msg": "用户不存在"}), 401
    inst = CtfGameInstance.query.get(instance_id)
    if not inst:
        return jsonify({"code": 404, "msg": "实例不存在"}), 404
    if not user_can_manage_instance(user, user_id, inst):
        return jsonify({"code": 403, "msg": "无权查看"}), 403
    if not user.is_admin and not getattr(user, "is_moderator", False):
        # 普通队员可读但脱敏；已在下方 redact
        pass
    tail = request.args.get("tail", 200, type=int)
    tail = max(1, min(tail or 200, 2000))
    from backend.services.container_service import container_service
    if not container_service.client or not inst.container_id:
        return jsonify({"code": 200, "msg": "无 Docker 客户端或容器 ID", "data": {"logs": "", "lines": []}}), 200
    try:
        container = container_service.client.containers.get(inst.container_id)
        text = container.logs(tail=tail).decode("utf-8", errors="replace")
        from backend.services.flag_redact import sanitize_log_lines, redact_flag_text
        lines = sanitize_log_lines(text.splitlines()[-tail:])
        return jsonify({"code": 200, "msg": "ok", "data": {"logs": "\n".join(lines), "lines": lines}}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 动态题目容器管理 ========================

@bp.route("/<int:challenge_id>/start-instance", methods=["POST"])
@jwt_required()
def start_challenge_instance(challenge_id):
    """兼容别名：转发到 start-container（含配额与资源限制）。"""
    return start_container(challenge_id)


@bp.route("/instances/<int:instance_id>/stop", methods=["POST"])
@jwt_required()
def stop_instance(instance_id):
    """停止/销毁容器实例 - 用户可以手动销毁自己的容器"""
    try:
        user_id = get_jwt_identity()
        
        # 处理user_id类型转换（可能是字符串）
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            pass
        
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"code": 404, "msg": "实例不存在"}), 404

        user = User.query.get(user_id)
        if not user_can_manage_instance(user, user_id, instance):
            logger.warning(f"Permission denied: user {user_id} cannot manage instance {instance_id}")
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        # 立即销毁容器（如果有Docker容器的话）；已不存在也视为成功
        if instance.container_id:
            try:
                import docker
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                container.stop(timeout=5)
                container.remove(force=True)
                logger.info(f"Container {instance.container_id[:12]} destroyed")
            except Exception as e:
                err = str(e).lower()
                if "no such container" in err or "404" in err or "not found" in err:
                    logger.info(
                        f"Container {instance.container_id[:12]} already gone on stop"
                    )
                else:
                    logger.warning(f"Failed to destroy Docker container: {e}")

        # 标记实例为已停止（幽灵 container_id 也必须清掉运行态）
        instance.is_running = False
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "容器已销毁",
            "data": instance.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/instances/<int:instance_id>/extend", methods=["POST"])
@jwt_required()
def extend_instance(instance_id):
    """延时容器过期时间 - 每次延时1小时"""
    try:
        user_id = get_jwt_identity()
        # 处理user_id类型转换（可能是字符串）
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            pass
        
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"code": 404, "msg": "实例不存在"}), 404

        if not user_can_manage_instance(User.query.get(user_id), user_id, instance):
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        if not instance.is_running:
            return jsonify({"code": 400, "msg": "实例已停止，无法延时"}), 400

        # 延时1小时，总时长上限 4 小时（与 /api/container/extend 一致）
        from datetime import timedelta
        if not instance.started_at:
            instance.started_at = datetime.utcnow()
        max_expire = instance.started_at + timedelta(hours=4)
        current_expires = instance.expires_at or datetime.utcnow()
        if current_expires >= max_expire:
            return jsonify({
                "code": 400,
                "msg": "已达到最大延期时间（最多可用4小时）"
            }), 400
        next_expires = current_expires + timedelta(hours=1)
        if next_expires > max_expire:
            next_expires = max_expire
        instance.expires_at = next_expires
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "容器已延时1小时",
            "data": {
                "instance_id": instance.id,
                "expires_at": instance.expires_at.isoformat() if instance.expires_at else None,
                "remaining_seconds": int((instance.expires_at - datetime.utcnow()).total_seconds()) if instance.expires_at else 0
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/instances/<int:instance_id>/status", methods=["GET"])
@jwt_required()
def get_instance_status(instance_id):
    """获取容器实例状态"""
    try:
        user_id = get_jwt_identity()
        # 处理user_id类型转换（可能是字符串）
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            pass
        
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"code": 404, "msg": "实例不存在"}), 404

        if instance.user_id != user_id:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        # 计算剩余时间
        remaining_seconds = 0
        status = "stopped"
        
        if instance.is_running:
            status = "running"
            if instance.expires_at:
                remaining = (instance.expires_at - datetime.utcnow()).total_seconds()
                remaining_seconds = max(0, int(remaining))
                
                # 如果已超期，自动销毁
                if remaining_seconds <= 0:
                    if instance.container_id:
                        try:
                            import docker
                            docker_client = docker.from_env()
                            container = docker_client.containers.get(instance.container_id)
                            container.stop(timeout=5)
                            container.remove(force=True)
                        except:
                            pass
                    instance.is_running = False
                    db.session.commit()
                    status = "expired"
                    remaining_seconds = 0

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "instance_id": instance.id,
                "challenge_id": instance.challenge_id,
                "status": status,
                "is_running": instance.is_running,
                "created_at": instance.started_at.isoformat() if instance.started_at else None,
                "expires_at": instance.expires_at.isoformat() if instance.expires_at else None,
                "remaining_seconds": remaining_seconds,
                "connection_url": instance.connection_url
            }
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 题目统计 ========================

@bp.route("/<int:challenge_id>/stats", methods=["GET"])
@jwt_required()
def get_challenge_stats(challenge_id):
    """获取题目统计信息 - 需参赛或管理员"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在"}), 401

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        if not user.is_admin and not PermissionService.check_challenge_permission(
            user_id, challenge_id, GamePermission.VIEW_CHALLENGE
        ):
            return jsonify({"code": 403, "msg": "无权访问"}), 403

        # 获取成功提交的用户
        correct_submissions = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge_id,
            is_correct=True
        ).all()

        # 获取唯一解题用户（同一用户只算一次）
        unique_solvers = len(set(s.user_id for s in correct_submissions))

        # 获取总提交数
        total_submissions = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge_id
        ).count()

        # 计算通过率
        solve_rate = "0%"
        if total_submissions > 0:
            rate = (len(correct_submissions) / total_submissions) * 100
            solve_rate = f"{rate:.1f}%"

        # 获取首解信息
        first_solve = CtfSolves.query.filter_by(
            challenge_id=challenge_id
        ).first()

        first_solver = None
        if first_solve:
            user = User.query.get(first_solve.user_id)
            if user:
                first_solver = {
                    "username": user.username,
                    "solved_at": first_solve.solved_at.isoformat() if first_solve.solved_at else None
                }

        user_solved = any(s.user_id == user_id for s in correct_submissions)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "unique_solvers": unique_solvers,
                "solves": unique_solvers,
                "solved_count": unique_solvers,
                "solves_count": unique_solvers,
                "total_submissions": total_submissions,
                "solve_rate": solve_rate,
                "first_solver": first_solver,
                "user_solved": user_solved,
            }
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 锤子反馈 ========================

@bp.route("/<int:challenge_id>/hammer", methods=["GET"])
@jwt_required()
def get_hammer_messages(challenge_id):
    """获取题目锤子消息列表"""
    try:
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        game = CtfGame.query.get(challenge.game_id)
        if game and _is_training_game(game):
            return jsonify({"code": 400, "msg": "训练场不支持锤子反馈"}), 400

        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or (not user.is_admin and not PermissionService.check_challenge_permission(
            user_id, challenge_id, GamePermission.VIEW_CHALLENGE
        )):
            return jsonify({"code": 403, "msg": "无权访问"}), 403

        rows = (
            CtfHammerMessage.query.filter_by(challenge_id=challenge_id)
            .order_by(CtfHammerMessage.created_at.asc())
            .limit(200)
            .all()
        )
        return jsonify({"code": 200, "data": [r.to_dict() for r in rows]}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/<int:challenge_id>/hammer", methods=["POST"])
@jwt_required()
def post_hammer_message(challenge_id):
    """发送锤子消息（选手提问 / 管理员回复）"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 404, "msg": "用户不存在"}), 404

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        game = CtfGame.query.get(challenge.game_id)
        if game and _is_training_game(game):
            return jsonify({"code": 400, "msg": "训练场不支持锤子反馈"}), 400

        if not user.is_admin and not PermissionService.check_challenge_permission(
            user_id, challenge_id, GamePermission.VIEW_CHALLENGE
        ):
            return jsonify({"code": 403, "msg": "无权访问"}), 403

        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content or len(content) > 2000:
            return jsonify({"code": 400, "msg": "消息内容无效（1-2000 字符）"}), 400

        is_staff = bool(user.is_admin) or bool(data.get("is_staff") and user.is_admin)
        row = CtfHammerMessage(
            challenge_id=challenge_id,
            game_id=challenge.game_id,
            user_id=user_id,
            content=content,
            is_staff=is_staff,
        )
        db.session.add(row)
        db.session.commit()
        return jsonify({"code": 200, "msg": "已发送", "data": row.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500
