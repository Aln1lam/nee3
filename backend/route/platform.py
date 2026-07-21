"""
平台公开信息 API — 供前端动态加载平台配置
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import func

from backend.services.cache_aside import (
    read_through,
    PLATFORM_INFO_KEY,
    KEY_BULLETINS_PUBLIC,
    KEY_TRAINING_SIDEBAR,
    TTL_PLATFORM_INFO,
    TTL_BULLETINS,
    TTL_TRAINING_SIDEBAR,
)
from backend.services.wiki_nav_service import build_wiki_nav_from_db
from backend.services.platform_config_service import load_public_platform_info
from backend.server.platform_defaults import DEFAULT_INFO

bp = Blueprint("platform", __name__, url_prefix="/api/platform")

PLATFORM_VERSION = "1.0.0"


def _build_platform_info():
    info = load_public_platform_info()
    info["wiki_sidebar"] = build_wiki_nav_from_db(wiki_only=True)
    return info


@bp.route("/info", methods=["GET"])
def platform_info():
    info, hit = read_through(PLATFORM_INFO_KEY, TTL_PLATFORM_INFO, _build_platform_info)
    resp = jsonify(info)
    resp.headers["X-Cache"] = "HIT" if hit else "MISS"
    return resp


@bp.route("/version", methods=["GET"])
def platform_version():
    return jsonify({
        "version": PLATFORM_VERSION,
        "backend": "neepu-ctf",
        "timestamp": datetime.utcnow().isoformat(),
    })


@bp.route("/bulletins", methods=["GET"])
def public_bulletins():
    """公开公告列表（无需登录）"""

    def _load():
        try:
            from backend.server.db_models import MainAnnouncement
            rows = (
                MainAnnouncement.query.filter_by(is_active=True)
                .order_by(MainAnnouncement.created_at.desc())
                .limit(50)
                .all()
            )
            return {"code": 200, "msg": "ok", "data": [r.to_dict() for r in rows]}
        except Exception:
            return {"code": 200, "msg": "ok", "data": []}

    payload, hit = read_through(KEY_BULLETINS_PUBLIC, TTL_BULLETINS, _load)
    resp = jsonify(payload)
    resp.headers["X-Cache"] = "HIT" if hit else "MISS"
    return resp


@bp.route("/bulletins/<int:bulletin_id>", methods=["GET"])
def bulletin_detail(bulletin_id):
    """公告详情"""
    try:
        from backend.server.db_models import MainAnnouncement
        row = MainAnnouncement.query.filter_by(id=bulletin_id, is_active=True).first()
        if not row:
            return jsonify({"msg": "公告不存在"}), 404
        return jsonify({"data": row.to_dict()})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


def _load_training_sidebar():
    from backend.server.db_models import CtfGame, CtfChallenge

    training = CtfGame.query.filter(
        CtfGame.game_type.in_(["training", "practice"])
    ).order_by(CtfGame.start_time.desc()).all()
    archived = CtfGame.query.filter_by(status="archived").order_by(
        CtfGame.start_time.desc()
    ).limit(20).all()

    def _with_count(games):
        result = []
        for g in games:
            d = g.to_dict()
            d["challenge_count"] = CtfChallenge.query.filter_by(
                game_id=g.id, is_enabled=True
            ).count()
            result.append(d)
        return result

    sidebar = [
        {
            "group": "训练",
            "items": [
                {
                    "id": g["id"],
                    "title": g["title"],
                    "icon": "🏋️",
                    "challenge_count": g["challenge_count"],
                }
                for g in _with_count(training)
            ],
        },
        {
            "group": "归档赛事",
            "items": [
                {
                    "id": g["id"],
                    "title": g["title"],
                    "icon": "📦",
                    "challenge_count": g["challenge_count"],
                }
                for g in _with_count(archived)
            ],
        },
    ]
    if not sidebar[0]["items"] and not training:
        sidebar[0]["items"] = []
    return {
        "code": 200,
        "msg": "ok",
        "sidebar": sidebar,
        "training": _with_count(training),
        "archived": _with_count(archived),
    }


@bp.route("/training/sidebar", methods=["GET"])
def training_sidebar():
    """训练场侧边栏数据"""
    try:
        payload, hit = read_through(
            KEY_TRAINING_SIDEBAR,
            TTL_TRAINING_SIDEBAR,
            _load_training_sidebar,
        )
        resp = jsonify(payload)
        resp.headers["X-Cache"] = "HIT" if hit else "MISS"
        return resp
    except Exception as e:
        return jsonify({
            "code": 200,
            "msg": "ok",
            "sidebar": DEFAULT_INFO["training_categories"],
            "training": [],
            "archived": [],
            "error": str(e),
        }), 200


@bp.route("/instances", methods=["GET"])
@jwt_required()
def my_instances():
    """当前用户运行中的容器实例"""
    try:
        from backend.server.db_models import CtfGameInstance
        user_id = get_jwt_identity()
        from backend.server.db_models import CtfChallenge
        from backend.server.container_access import normalize_connection_url
        rows = (
            CtfGameInstance.query.filter_by(user_id=int(user_id), is_running=True)
            .order_by(CtfGameInstance.started_at.desc())
            .limit(20)
            .all()
        )
        data = []
        for r in rows:
            d = r.to_dict()
            ch = CtfChallenge.query.get(r.challenge_id)
            if ch:
                d["challenge_title"] = ch.title
                d["game_id"] = ch.game_id
                d["connection_url"] = normalize_connection_url(r, challenge=ch)
            if d.get("expires_at"):
                try:
                    exp = datetime.fromisoformat(d["expires_at"].replace("Z", ""))
                    d["remaining_seconds"] = max(0, int((exp - datetime.utcnow()).total_seconds()))
                except Exception:
                    d["remaining_seconds"] = None
            data.append(d)
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"data": [], "error": str(e)}), 200
