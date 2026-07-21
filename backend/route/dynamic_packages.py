# -*- coding: utf-8 -*-
"""动态附件包管理 API — 完整 CRUD（本地/对象存储）"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from backend.server.db_models import User, CtfChallenge, CtfDynamicPackage, db
from backend.services.storage import get_storage

bp = Blueprint("dynamic_packages", __name__)


def _require_staff():
    try:
        uid = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    user = User.query.get(uid)
    if not user:
        return None
    if getattr(user, "is_admin", False) or getattr(user, "is_moderator", False):
        return user
    return None


def _require_admin():
    try:
        uid = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    user = User.query.get(uid)
    if not user or not getattr(user, "is_admin", False):
        return None
    return user


@bp.get("/challenges/<int:challenge_id>/packages")
@jwt_required()
def list_packages(challenge_id):
    if not _require_staff():
        return jsonify({"code": 403, "msg": "无权访问", "data": []}), 403
    challenge = CtfChallenge.query.get(challenge_id)
    if not challenge:
        return jsonify({"code": 404, "msg": "题目不存在"}), 404
    rows = (
        CtfDynamicPackage.query.filter_by(challenge_id=challenge_id)
        .order_by(CtfDynamicPackage.variant_id.asc(), CtfDynamicPackage.id.asc())
        .all()
    )
    return jsonify({
        "code": 200,
        "msg": "ok",
        "data": [r.to_dict() for r in rows],
        "meta": {
            "challenge_id": challenge_id,
            "feature": "dynamic_packages",
            "status": "ready",
            "count": len(rows),
        },
    })


@bp.get("/statistics/package-distribution/<int:game_id>")
@jwt_required()
def package_distribution(game_id):
    if not _require_staff():
        return jsonify({"code": 403, "msg": "无权访问"}), 403
    challenges = CtfChallenge.query.filter_by(game_id=game_id).all()
    dist = []
    for ch in challenges:
        n = CtfDynamicPackage.query.filter_by(challenge_id=ch.id, is_active=True).count()
        if n or ch.challenge_type == 2:
            dist.append({
                "challenge_id": ch.id,
                "title": ch.title,
                "package_count": n,
                "challenge_type": ch.challenge_type,
            })
    return jsonify({
        "code": 200,
        "msg": "ok",
        "data": {"game_id": game_id, "distribution": dist, "status": "ready"},
    })


@bp.post("/challenges/<int:challenge_id>/upload")
@jwt_required()
def upload_packages(challenge_id):
    user = _require_admin()
    if not user:
        return jsonify({"code": 403, "msg": "无权访问（需管理员）"}), 403
    challenge = CtfChallenge.query.get(challenge_id)
    if not challenge:
        return jsonify({"code": 404, "msg": "题目不存在"}), 404
    if "file" not in request.files:
        return jsonify({"code": 400, "msg": "未找到文件字段 file"}), 400
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"code": 400, "msg": "文件名为空"}), 400
    filename = secure_filename(f.filename)
    if not filename.lower().endswith(".zip"):
        return jsonify({"code": 400, "msg": "仅支持 ZIP 文件"}), 400

    raw = f.read()
    if not raw:
        return jsonify({"code": 400, "msg": "空文件"}), 400
    if len(raw) > 80 * 1024 * 1024:
        return jsonify({"code": 400, "msg": "文件过大（上限 80MB）"}), 400

    from backend.services.zip_safety import ZipSafetyError, ZipLimits, validate_zip_bytes
    try:
        validate_zip_bytes(
            raw,
            limits=ZipLimits(
                max_compressed=80 * 1024 * 1024,
                max_uncompressed=200 * 1024 * 1024,
                max_files=500,
                max_single_file=80 * 1024 * 1024,
            ),
        )
    except ZipSafetyError as e:
        return jsonify({"code": 400, "msg": f"ZIP 不安全: {e}"}), 400

    file_hash = hashlib.sha256(raw).hexdigest()
    max_variant = (
        db.session.query(db.func.max(CtfDynamicPackage.variant_id))
        .filter_by(challenge_id=challenge_id)
        .scalar()
    )
    variant_id = int(max_variant or 0) + 1
    key = f"dynamic_packages/{challenge_id}/v{variant_id}_{file_hash[:12]}_{filename}"
    storage = get_storage()
    path, url = storage.save(key, raw, content_type="application/zip")

    pkg = CtfDynamicPackage(
        challenge_id=challenge_id,
        variant_id=variant_id,
        filename=filename,
        storage_key=key,
        file_hash=file_hash,
        file_size=len(raw),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.session.add(pkg)
    db.session.commit()
    data = pkg.to_dict()
    data["url"] = url
    data["path"] = path
    return jsonify({"code": 200, "msg": "上传成功", "data": data}), 200


@bp.put("/packages/<int:package_id>")
@jwt_required()
def update_package(package_id):
    if not _require_admin():
        return jsonify({"code": 403, "msg": "无权访问"}), 403
    pkg = CtfDynamicPackage.query.get(package_id)
    if not pkg:
        return jsonify({"code": 404, "msg": "附件包不存在"}), 404
    data = request.get_json(silent=True) or {}
    if "is_active" in data:
        pkg.is_active = bool(data.get("is_active"))
    if "variant_id" in data:
        try:
            pkg.variant_id = int(data.get("variant_id"))
        except (TypeError, ValueError):
            return jsonify({"code": 400, "msg": "variant_id 无效"}), 400
    if "filename" in data and data.get("filename"):
        pkg.filename = secure_filename(str(data["filename"])) or pkg.filename
    db.session.commit()
    return jsonify({"code": 200, "msg": "已更新", "data": pkg.to_dict()}), 200


@bp.delete("/packages/<int:package_id>")
@jwt_required()
def delete_package(package_id):
    if not _require_admin():
        return jsonify({"code": 403, "msg": "无权访问"}), 403
    pkg = CtfDynamicPackage.query.get(package_id)
    if not pkg:
        return jsonify({"code": 404, "msg": "附件包不存在"}), 404
    key = pkg.storage_key
    db.session.delete(pkg)
    db.session.commit()
    try:
        get_storage().delete(key)
    except Exception:
        pass
    return jsonify({"code": 200, "msg": "已删除", "data": {"id": package_id}}), 200


@bp.get("/packages/<int:package_id>/download")
@jwt_required()
def download_package(package_id):
    if not _require_staff():
        return jsonify({"code": 403, "msg": "无权访问"}), 403
    pkg = CtfDynamicPackage.query.get(package_id)
    if not pkg:
        return jsonify({"code": 404, "msg": "附件包不存在"}), 404
    storage = get_storage()
    abs_path = storage.absolute_path(pkg.storage_key)
    if abs_path and os.path.isfile(abs_path):
        return send_file(abs_path, as_attachment=True, download_name=pkg.filename)
    try:
        fh = storage.open(pkg.storage_key)
        return send_file(fh, as_attachment=True, download_name=pkg.filename, mimetype="application/zip")
    except Exception as e:
        return jsonify({"code": 404, "msg": f"文件不存在: {e}"}), 404
