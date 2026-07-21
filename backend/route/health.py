"""健康检查与系统状态 API"""

from flask import Blueprint, jsonify, current_app
from backend.server import config

bp = Blueprint("health", __name__, url_prefix="/api/health")


@bp.route("/", methods=["GET"])
@bp.route("/live", methods=["GET"])
def liveness():
    """存活探针 — 进程正常运行即可"""
    return jsonify({"status": "ok", "service": "neepu-ctf"})


@bp.route("/ready", methods=["GET"])
def readiness():
    """就绪探针 — 检查数据库与 Redis"""
    checks = {"database": "unknown", "redis": "unknown"}
    overall = "ok"

    try:
        from sqlalchemy import text
        from backend.server import extensions
        extensions.db.session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        overall = "degraded"

    if config.settings.REDIS_ENABLED:
        try:
            from backend.services.redis_service import get_redis
            svc = get_redis()
            if svc and svc.is_available():
                checks["redis"] = svc.get_info()
            else:
                checks["redis"] = "unavailable"
                overall = "degraded"
        except Exception as e:
            checks["redis"] = f"error: {e}"
            overall = "degraded"
    else:
        checks["redis"] = "disabled"

    status_code = 200 if overall == "ok" else 503
    return jsonify({"status": overall, "checks": checks}), status_code
