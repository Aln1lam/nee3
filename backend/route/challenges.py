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
    CtfCheatInfo, CtfChallengeHint, CtfUserHintAccess, CtfGameNotice
)
from backend.services.scoring_service import (
    ScoringService, CheatDetectionService, FlagTemplateService
)
from backend.services.container_service import container_service
from backend.server.traffic_capture import TrafficCaptureManager

logger = logging.getLogger(__name__)

bp = Blueprint("challenges", __name__)


def _normalize_connection_url(instance):
    """使用实例port修正connection_url，避免历史脏数据导致端口不一致。"""
    if not instance:
        return ""

    current_url = instance.connection_url or ""
    if not instance.port:
        return current_url

    expected_port = str(instance.port)
    if not current_url:
        return f"http://localhost:{expected_port}"

    try:
        parsed = urlparse(current_url)
        scheme = parsed.scheme or "http"
        host = parsed.hostname or "localhost"
        actual_port = str(parsed.port) if parsed.port else ""
        path = parsed.path or ""
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""

        if actual_port != expected_port:
            return f"{scheme}://{host}:{expected_port}{path}{query}{fragment}"

        return current_url
    except Exception:
        return current_url


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

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": [c.to_dict() for c in challenges]
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
        
        # 获取用户的提交记录
        submissions = CtfChallengeSubmission.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id
        ).all()

        data = challenge.to_dict()
        data['submissions'] = [s.to_dict() for s in submissions]
        data['submission_count'] = len(submissions)
        
        # 检查是否已解决
        solved = any(s.is_correct for s in submissions)
        data['is_solved'] = solved

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 提交Flag ========================

@bp.route("/<int:challenge_id>/submit", methods=["POST"])
@jwt_required()
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

        # ✓ 检查：用户必须有队伍
        if not user.team_id:
            return jsonify({
                "code": 403,
                "msg": "必须加入队伍才能参与比赛"
            }), 403

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

        game = CtfGame.query.get(challenge.game_id)
        if not game:
            return jsonify({"code": 404, "msg": "比赛不存在"}), 404

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

        # ✓ 检查：比赛是否已开始（只有已开始的比赛才能提交）
        if datetime.utcnow() < game.start_time:
            return jsonify({
                "code": 403,
                "msg": "比赛还未开始，无法提交答案"
            }), 403

        if game.archived_at is not None:
            return jsonify({
                "code": 403,
                "msg": "该比赛已归档，无法提交答案计分"
            }), 403

        data = request.get_json() or {}
        answer = data.get("answer", "").strip()
        
        if not answer:
            return jsonify({"code": 400, "msg": "答案不能为空"}), 400

        # 检查提交次数限制
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

        # 检查是否已经解决过
        solved = CtfChallengeSubmission.query.filter_by(
            user_id=user_id,
            challenge_id=challenge_id,
            is_correct=True
        ).first()

        if solved:
            return jsonify({
                "code": 400,
                "msg": "您已经解决过这个题目",
                "data": {
                    "is_correct": True,
                    "submission": solved.to_dict()
                }
            }), 400

        # 检查答案
        is_correct = (answer.strip() == challenge.flag.strip())
        
        submission = CtfChallengeSubmission(
            user_id=user_id,
            team_id=user.team_id,
            challenge_id=challenge_id,
            game_id=challenge.game_id,
            answer=answer,
            is_correct=is_correct,
            points_earned=0,
            submitted_at=datetime.utcnow()
        )

        db.session.add(submission)

        response_data = {
            "is_correct": is_correct,
            "submission": submission.to_dict()
        }

        # 如果答案正确，执行排分逻辑
        if is_correct:
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
                response_data['cheat_warning'] = f"检测到与{len(similar_users)}个用户的Flag相似"

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
            def destroy_container_async():
                try:
                    instance = CtfGameInstance.query.filter_by(
                        challenge_id=challenge_id,
                        user_id=user_id,
                        is_running=True
                    ).first()
                    
                    if instance and instance.container_id:
                        try:
                            docker_client = docker.from_env()
                            container = docker_client.containers.get(instance.container_id)
                            container.stop(timeout=5)
                            container.remove(force=True)
                            logger.info(f"Container {instance.container_id[:12]} destroyed after correct flag")
                        except Exception as e:
                            logger.warning(f"Failed to destroy container: {e}")
                        
                        # 更新数据库
                        instance.is_running = False
                        db.session.commit()
                except Exception as e:
                    logger.error(f"Error in destroy_container_async: {e}")
            
            # 后台销毁容器（不阻塞响应）
            thread = threading.Thread(target=destroy_container_async, daemon=True)
            thread.start()

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "恭喜！答案正确！" if is_correct else "答案错误",
            "data": response_data
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

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": [fs.to_dict() for fs in first_solves]
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
            hint_dict = hint.to_dict()
            hint_dict['is_accessed'] = hint.id in accessed_hint_ids
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
                "hint": hint.to_dict(),
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
        
        # 首先清理用户所有过期的容器实例
        expired_instances = CtfGameInstance.query.filter(
            CtfGameInstance.user_id == user_id,
            CtfGameInstance.is_running == True,
            CtfGameInstance.expires_at < datetime.utcnow()
        ).all()
        
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
        
        # 查询运行中的容器
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
        
        # 容器正在运行
        normalized_url = _normalize_connection_url(instance)
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

        if not challenge.docker_image:
            return jsonify({"code": 400, "msg": "该题目不支持容器（未配置镜像）"}), 400

        # 检查是否已有运行中的实例
        existing_instance = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id,
            is_running=True
        ).first()

        if existing_instance:
            normalized_url = _normalize_connection_url(existing_instance)
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

        # 使用新的容器服务创建容器
        success, instance, msg = container_service.create_container(
            challenge=challenge,
            user=user,
            team=None,
            expire_hours=2
        )

        if not success:
            logger.error(f"Failed to create container for challenge {challenge_id}: {msg}")
            return jsonify({"code": 500, "msg": f"容器启动失败: {msg}"}), 500

        # 流量捕获集成：如果题目启用了流量捕获，后台启动流量代理
        if challenge.enable_traffic_capture and instance.port:
            def start_traffic_capture():
                try:
                    manager = TrafficCaptureManager()
                    result = manager.start_capture(
                        container_id=instance.container_id or instance.id,
                        instance_id=instance.id,
                        user_id=user.id,
                        challenge_id=challenge_id,
                        target_port=instance.port,  # 容器实际映射的端口
                        team_id=user.team_id,
                        enable_traffic_capture=True,
                        duration_seconds=7200,  # 2小时
                        challenge_name=challenge.title
                    )
                    
                    # 如果代理启动成功，更新instance的connection_url为代理端口
                    if result.get("status") == "started":
                        proxy_port = result.get("proxy_port")
                        instance.connection_url = f"http://localhost:{proxy_port}"
                        db.session.commit()
                        logger.info(f"Updated instance {instance.id} connection_url to proxy: {instance.connection_url}")
                    
                    logger.info(f"Traffic capture started for instance {instance.id}: {result}")
                except Exception as e:
                    logger.error(f"Failed to start traffic capture: {e}")
            
            # 在后台线程中启动流量捕获（不阻塞API响应）
            thread = threading.Thread(target=start_traffic_capture, daemon=True)
            thread.start()

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


# ======================== 动态题目容器管理 ========================

@bp.route("/<int:challenge_id>/start-instance", methods=["POST"])
@jwt_required()
def start_challenge_instance(challenge_id):
    """启动动态题目容器实例 - 1小时过期，可延时，可销毁"""
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

        # 检查是否已有运行中的实例
        existing_instance = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id,
            is_running=True
        ).first()

        if existing_instance:
            return jsonify({
                "code": 400,
                "msg": "已有运行中的实例",
                "data": existing_instance.to_dict()
            }), 400

        # 创建新实例记录 - 设置1小时过期
        from datetime import timedelta
        instance = CtfGameInstance(
            challenge_id=challenge_id,
            user_id=user_id,
            team_id=user.team_id,
            container_image=challenge.docker_image if hasattr(challenge, 'docker_image') else challenge.container_image,
            is_running=True,
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)  # 初始过期时间为1小时
        )

        db.session.add(instance)
        db.session.commit()

        # 流量捕获集成：如果题目启用了流量捕获，后台启动捕获
        if challenge.enable_traffic_capture and instance.container_id:
            def start_traffic_capture():
                try:
                    manager = TrafficCaptureManager()
                    result = manager.start_capture(
                        container_id=instance.container_id,
                        instance_id=instance.id,
                        user_id=user_id,
                        challenge_id=challenge_id,
                        enable_traffic_capture=True,
                        duration_seconds=3600,  # 1小时
                        challenge_name=challenge.title
                    )
                    logger.info(f"Traffic capture started for instance {instance.id}: {result}")
                except Exception as e:
                    logger.error(f"Failed to start traffic capture: {e}")
            
            # 在后台线程中启动流量捕获（不阻塞API响应）
            thread = threading.Thread(target=start_traffic_capture, daemon=True)
            thread.start()

        return jsonify({
            "code": 200,
            "msg": "实例启动成功" if instance.container_id else "实例启动中...",
            "data": instance.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


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

        # 调试：返回权限检查信息
        permission_check = {
            "instance_user_id": instance.user_id,
            "jwt_user_id": user_id,
            "instance_user_id_type": str(type(instance.user_id)),
            "jwt_user_id_type": str(type(user_id)),
            "equal": instance.user_id == user_id
        }
        
        if instance.user_id != user_id:
            logger.warning(f"Permission denied: {user_id} != {instance.user_id}")
            return jsonify({"code": 403, "msg": "无权操作", "debug": permission_check}), 403

        # 立即销毁容器（如果有Docker容器的话）
        if instance.container_id:
            try:
                import docker
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                container.stop(timeout=5)
                container.remove(force=True)
                logger.info(f"Container {instance.container_id[:12]} destroyed")
            except Exception as e:
                logger.warning(f"Failed to destroy Docker container: {e}")

        # 标记实例为已停止
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

        if instance.user_id != user_id:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        if not instance.is_running:
            return jsonify({"code": 400, "msg": "实例已停止，无法延时"}), 400

        # 延时1小时
        from datetime import timedelta
        current_expires = instance.expires_at or datetime.utcnow()
        instance.expires_at = current_expires + timedelta(hours=1)
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
def get_challenge_stats(challenge_id):
    """获取题目统计信息 - 解决人数、通过率等"""
    try:
        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404

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

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": {
                "unique_solvers": unique_solvers,
                "total_submissions": total_submissions,
                "solve_rate": solve_rate,
                "first_solver": first_solver
            }
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500
