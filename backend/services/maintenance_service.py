"""维护模式：读取 SystemConfig 并在请求层拦截非管理员访问"""

from __future__ import annotations

import time
from typing import Tuple

_CACHE = {"at": 0.0, "enabled": False, "message": "系统正在维护中，请稍后再试"}
_TTL_SECONDS = 2

_EXEMPT_PREFIXES = (
    "/api/platform/info",
    "/api/platform/version",
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/verify-email",
    "/api/auth/resend-verification",
    "/api/captcha",
)


def invalidate_maintenance_cache() -> None:
    _CACHE["at"] = 0.0


def get_maintenance_state() -> Tuple[bool, str]:
    now = time.time()
    if now - _CACHE["at"] < _TTL_SECONDS:
        return _CACHE["enabled"], _CACHE["message"]

    enabled = False
    message = "系统正在维护中，请稍后再试"
    try:
        from backend.server.db_models import SystemConfig

        rows = SystemConfig.query.filter(
            SystemConfig.key.in_(("maintenance_mode", "maintenance_message"))
        ).all()
        by_key = {row.key: row.value for row in rows}
        enabled = str(by_key.get("maintenance_mode", "")).lower() in ("true", "1", "yes")
        if by_key.get("maintenance_message"):
            message = by_key["maintenance_message"]
    except Exception:
        pass

    _CACHE["enabled"] = enabled
    _CACHE["message"] = message
    _CACHE["at"] = now
    return enabled, message


def is_exempt_path(path: str) -> bool:
    if not path:
        return False
    if path.startswith("/static/") and not path.startswith("/static/uploads/"):
        return True
    return any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)


def current_user_is_admin() -> bool:
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from backend.server.db_models import User

        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if not user_id:
            return False
        user = User.query.get(int(user_id))
        return bool(user and user.is_admin)
    except Exception:
        return False
