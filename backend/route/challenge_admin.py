"""
CTF 题目管理接口 - 仅管理员可用
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from backend.server.extensions import db
from backend.services.scoring_service import ScoringService
from backend.server.db_models import (
    User, CtfGame, CtfChallenge, CtfChallengeCategory
)

bp = Blueprint("challenge_admin", __name__)


# ======================== 题目分类管理 ========================

@bp.route("/categories", methods=["GET"])
def get_categories():
    """获取所有题目分类"""
    try:
        categories = CtfChallengeCategory.query.all()
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": [c.to_dict() for c in categories]
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/categories", methods=["POST"])
@jwt_required()
def create_category():
    """创建题目分类"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        # 使用force=True允许任何形式的JSON请求
        data = request.get_json(force=True) if request.content_length else {}
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"code": 400, "msg": "分类名称不能为空"}), 400
        
        # 检查是否已存在
        existing = CtfChallengeCategory.query.filter_by(name=name).first()
        if existing:
            return jsonify({"code": 400, "msg": "分类已存在"}), 400
        
        category = CtfChallengeCategory(name=name)
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "分类创建成功",
            "data": category.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


# ======================== 题目管理 ========================

@bp.route("/games/<int:game_id>/challenges", methods=["POST"])
@jwt_required()
def create_challenge(game_id):
    """为竞赛创建题目"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404
        
        # 支持FormData和JSON两种格式
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json(force=True) if request.content_length else {}
        else:
            # 从FormData或表单数据中获取
            data = request.form.to_dict() if request.form else {}
            # 如果data为空，尝试解析JSON
            if not data and request.content_length:
                try:
                    data = request.get_json(force=True)
                except:
                    data = {}
        
        # 验证必要字段（注意：前端发送的是original_points）
        # 兼容 original_points / points / score
        points_value = data.get("original_points") or data.get("points") or data.get("score")
        required_fields = ["title", "category", "flag"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"code": 400, "msg": f"缺少必要字段: {field}"}), 400
        if not points_value:
            return jsonify({"code": 400, "msg": "缺少必要字段: 分值"}), 400
        
        challenge = CtfChallenge(
            game_id=game_id,
            title=data.get("title", "").strip(),
            category=data.get("category", "").strip(),
            description=data.get("description", ""),
            flag=data.get("flag", "").strip(),
            flag_template=data.get("flag_template", "").strip() or None,
            original_points=int(points_value),
            # 必须使用请求体中的真实衰减配置（仅缺省时才用默认）
            min_score_rate=float(data["min_score_rate"]) if data.get("min_score_rate") is not None and str(data.get("min_score_rate")) != "" else 0.25,
            difficulty=float(data["difficulty"]) if data.get("difficulty") is not None and str(data.get("difficulty")) != "" else 10.0,
            docker_image=data.get("docker_image") or None,
            docker_port=int(data.get("docker_port", 80)) if data.get("docker_port") else 80,
            challenge_type=int(data.get("challenge_type", 0)) if data.get("challenge_type") else 0,
            submission_limit=int(data.get("submission_limit", 0)) if data.get("submission_limit") else 0,
            disable_blood_bonus=bool(data.get("disable_blood_bonus", False)),
            cpu_count=int(data.get("cpu_count", 1)) if data.get("cpu_count") else 1,
            memory_limit=int(data.get("memory_limit", 256)) if data.get("memory_limit") else 256,
            storage_limit=int(data.get("storage_limit", 1024)) if data.get("storage_limit") else 1024,
            network_mode=(data.get("network_mode") or "Open").strip() or "Open",
            enable_traffic_capture=bool(data.get("enable_traffic_capture", False)),
            is_enabled=True
        )
        
        db.session.add(challenge)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "题目创建成功",
            "data": challenge.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error creating challenge: {error_msg}")
        return jsonify({"code": 500, "msg": str(e), "error": error_msg}), 500


@bp.route("/games/<int:game_id>/challenges/<int:challenge_id>", methods=["GET"])
@jwt_required()
def get_challenge_detail(game_id, challenge_id):
    """获取题目详情（管理员）"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        challenge = CtfChallenge.query.filter_by(
            id=challenge_id, game_id=game_id
        ).first()
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": challenge.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/games/<int:game_id>/challenges/<int:challenge_id>", methods=["PUT"])
@jwt_required()
def update_challenge(game_id, challenge_id):
    """更新题目"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        challenge = CtfChallenge.query.filter_by(
            id=challenge_id, game_id=game_id
        ).first()
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404
        
        # 支持FormData和JSON两种格式
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json(force=True) if request.content_length else {}
        else:
            # 从FormData或表单数据中获取
            data = request.form.to_dict() if request.form else {}
            # 如果data为空，尝试解析JSON
            if not data and request.content_length:
                try:
                    data = request.get_json(force=True)
                except:
                    data = {}
        
        # 更新字段
        if "title" in data and data["title"].strip():
            challenge.title = data["title"].strip()
        
        if "description" in data:
            challenge.description = data.get("description", "")
        
        if "flag" in data and data["flag"].strip():
            challenge.flag = data["flag"].strip()

        if "flag_template" in data:
            challenge.flag_template = data["flag_template"].strip() or None
        
        # 兼容 original_points / points / score
        scoring_changed = False
        if "original_points" in data or "points" in data or "score" in data:
            points_val = data.get("original_points", data.get("points", data.get("score")))
            if points_val is not None and str(points_val) != "":
                new_pts = int(points_val)
                if new_pts != challenge.original_points:
                    scoring_changed = True
                challenge.original_points = new_pts

        if "min_score_rate" in data and data.get("min_score_rate") is not None and str(data.get("min_score_rate")) != "":
            new_rate = float(data.get("min_score_rate"))
            if float(challenge.min_score_rate or 0) != new_rate:
                scoring_changed = True
            challenge.min_score_rate = new_rate

        if "difficulty" in data and data.get("difficulty") is not None and str(data.get("difficulty")) != "":
            new_diff = float(data.get("difficulty"))
            if float(challenge.difficulty or 0) != new_diff:
                scoring_changed = True
            challenge.difficulty = new_diff
        
        if "category" in data:
            challenge.category = data.get("category", "").strip()
        
        if "docker_image" in data:
            challenge.docker_image = data.get("docker_image")
        
        if "docker_port" in data:
            challenge.docker_port = int(data.get("docker_port", 80)) if data.get("docker_port") else 80
        
        if "challenge_type" in data:
            challenge.challenge_type = int(data.get("challenge_type", 0)) if data.get("challenge_type") else 0
        
        if "submission_limit" in data:
            challenge.submission_limit = int(data.get("submission_limit", 0)) if data.get("submission_limit") else 0
        
        if "disable_blood_bonus" in data:
            challenge.disable_blood_bonus = bool(data.get("disable_blood_bonus", False))
        
        if "cpu_count" in data:
            challenge.cpu_count = int(data.get("cpu_count", 1)) if data.get("cpu_count") else 1
        
        if "memory_limit" in data:
            challenge.memory_limit = int(data.get("memory_limit", 256)) if data.get("memory_limit") else 256

        if "storage_limit" in data:
            challenge.storage_limit = int(data.get("storage_limit", 1024)) if data.get("storage_limit") else 1024

        if "network_mode" in data:
            challenge.network_mode = (data.get("network_mode") or "Open").strip() or "Open"

        if "enable_traffic_capture" in data:
            val = data.get("enable_traffic_capture")
            if isinstance(val, str):
                challenge.enable_traffic_capture = val.strip().lower() in ("1", "true", "yes", "on")
            else:
                challenge.enable_traffic_capture = bool(val)
        
        if "is_enabled" in data:
            challenge.is_enabled = bool(data.get("is_enabled", True))

        db.session.flush()
        # 衰减参数变更：立即回写该题所有已解队伍 points_earned + scoreboard
        if scoring_changed:
            ScoringService.recalculate_challenge_scores(challenge_id)

        db.session.commit()
        
        return jsonify({
            "code": 200,
            "msg": "题目更新成功",
            "data": challenge.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/games/<int:game_id>/challenges/<int:challenge_id>", methods=["DELETE"])
@jwt_required()
def delete_challenge(game_id, challenge_id):
    """删除题目"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        challenge = CtfChallenge.query.filter_by(
            id=challenge_id, game_id=game_id
        ).first()
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404
        
        db.session.delete(challenge)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "题目删除成功"
        }), 200
    except Exception as e:
        db.session.rollback()
        err = str(getattr(e, "orig", e))
        if "1451" in err or "foreign key constraint" in err.lower():
            return jsonify({"code": 409, "msg": "题目存在关联数据，无法删除"}), 409
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/games/<int:game_id>/challenges-list", methods=["GET"])
@jwt_required()
def get_admin_challenges(game_id):
    """管理员获取竞赛的所有题目（包括禁用的）"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        game = CtfGame.query.get(game_id)
        if not game:
            return jsonify({"code": 404, "msg": "竞赛不存在"}), 404
        
        challenges = CtfChallenge.query.filter_by(game_id=game_id).all()
        
        # 构建返回数据，使用 try-catch 捕获单个题目的序列化错误
        data = []
        for c in challenges:
            try:
                data.append(c.to_dict())
            except Exception as e:
                # 如果某个题目序列化失败，返回基本信息
                data.append({
                    'id': c.id,
                    'game_id': c.game_id,
                    'title': c.title,
                    'error': str(e)
                })
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": data
        }), 200
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in get_admin_challenges: {error_msg}")
        return jsonify({"code": 500, "msg": str(e), "error": error_msg}), 500


@bp.route("/games/<int:game_id>/challenges-stats", methods=["GET"])
@jwt_required()
def get_challenges_stats(game_id):
    """获取竞赛所有题目的统计信息"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        challenges = CtfChallenge.query.filter_by(game_id=game_id).all()
        
        stats = []
        for challenge in challenges:
            from backend.server.db_models import CtfChallengeSubmission
            
            total_submissions = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge.id
            ).count()
            
            correct_submissions = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge.id, is_correct=True
            ).count()
            
            unique_solvers = db.session.query(
                db.func.count(db.func.distinct(CtfChallengeSubmission.user_id))
            ).filter_by(challenge_id=challenge.id, is_correct=True).scalar() or 0
            
            stats.append({
                **challenge.to_dict(),
                "total_submissions": total_submissions,
                "correct_submissions": correct_submissions,
                "unique_solvers": unique_solvers,
                "solve_rate": f"{(correct_submissions/total_submissions*100):.1f}%" if total_submissions > 0 else "0%"
            })
        
        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route("/games/<int:game_id>/challenges/<int:challenge_id>/attachments", methods=["POST"])
@jwt_required()
def upload_challenge_attachment(game_id, challenge_id):
    """上传题目附件"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({"code": 403, "msg": "无权操作"}), 403
        
        challenge = CtfChallenge.query.filter_by(
            id=challenge_id, game_id=game_id
        ).first()
        if not challenge:
            return jsonify({"code": 404, "msg": "题目不存在"}), 404
        
        # 获取上传的文件
        if 'file' not in request.files:
            return jsonify({"code": 400, "msg": "未找到文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"code": 400, "msg": "文件名为空"}), 400
        
        # 保存文件到存储
        import os
        import mimetypes
        import hashlib
        from werkzeug.utils import secure_filename
        from flask import current_app
        
        try:
            # 确保上传目录存在
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            
            # 避免文件名冲突
            dest = os.path.join(upload_dir, filename)
            base, file_ext = os.path.splitext(filename)
            i = 1
            while os.path.exists(dest):
                filename = f"{base}_{i}{file_ext}"
                dest = os.path.join(upload_dir, filename)
                i += 1
            
            # 保存文件
            raw = file.read()
            if not raw:
                return jsonify({"code": 400, "msg": "空文件"}), 400
            if len(raw) > 20 * 1024 * 1024:
                return jsonify({"code": 400, "msg": "文件过大（上限 20MB）"}), 400
            if filename.lower().endswith(".zip"):
                from backend.services.zip_safety import ZipSafetyError, validate_zip_bytes
                try:
                    validate_zip_bytes(raw)
                except ZipSafetyError as e:
                    return jsonify({"code": 400, "msg": f"ZIP 不安全: {e}"}), 400
            with open(dest, "wb") as fh:
                fh.write(raw)
            
            # 获取文件信息
            url = f"/static/uploads/{filename}"
            size = os.path.getsize(dest)
            mime_type, _ = mimetypes.guess_type(dest)
            
            # 创建 FileResource 记录
            from backend.server.db_models import FileResource
            resource = FileResource(
                filename=filename,
                path=dest,
                url=url,
                mime_type=mime_type,
                size=size,
                uploader_id=user_id
            )
            db.session.add(resource)
            db.session.flush()
            
            # 更新题目附件 ID
            challenge.attachment_id = resource.id
            db.session.commit()
            
            return jsonify({
                "code": 200,
                "msg": "附件上传成功",
                "data": {
                    "attachment_id": resource.id,
                    "filename": resource.filename,
                    "url": resource.url
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"code": 500, "msg": f"文件上传失败: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500
