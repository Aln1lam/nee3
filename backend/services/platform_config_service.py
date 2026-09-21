"""平台 UI 配置：DB(SystemConfig) 为真相源，代码 DEFAULT 为 fallback"""

import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict

from backend.server.platform_defaults import DEFAULT_INFO

JSON_CONFIG_KEYS = {
    "platform_nav": "nav",
    "platform_footer": "footer",
    "platform_loading_tips": "loading_tips",
    "platform_training_categories": "training_categories",
    "platform_challenge_categories": "challenge_categories",
}

TEXT_CONFIG_KEYS = {
    "platform_subtitle": "subtitle",
    "platform_tagline_link": "tagline_link",
    "platform_brand_desc": "brand_desc",
    "platform_training_welcome": "training_welcome",
}

SYSTEM_CONFIG_PUBLIC_KEYS = (
    "site_name",
    "site_description",
    "maintenance_message",
    "highlight_banner",
    "maintenance_mode",
    "allow_registration",
    "allow_teams",
    "allow_games",
    "require_email_verification",
    "captcha_required",
    "home_featured_game_id",
)

BOOL_SYSTEM_KEYS = (
    "maintenance_mode",
    "allow_registration",
    "allow_teams",
    "allow_games",
    "require_email_verification",
    "captcha_required",
)


def _parse_json_value(raw: str, fallback: Any) -> Any:
    if raw is None or raw == "":
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def get_default_platform_config() -> Dict[str, Any]:
    """返回可写入 SystemConfig 的默认 JSON 配置项。"""
    return {
        "platform_nav": DEFAULT_INFO["nav"],
        "platform_footer": DEFAULT_INFO["footer"],
        "platform_loading_tips": DEFAULT_INFO["loading_tips"],
        "platform_training_categories": DEFAULT_INFO["training_categories"],
        "platform_challenge_categories": DEFAULT_INFO["challenge_categories"],
        "platform_subtitle": DEFAULT_INFO["subtitle"],
        "platform_tagline_link": DEFAULT_INFO["tagline_link"],
        "platform_brand_desc": DEFAULT_INFO["brand_desc"],
        "platform_training_welcome": DEFAULT_INFO["training_welcome"],
    }


def seed_platform_config_defaults(app) -> None:
    """首次启动时将 UI 配置写入 SystemConfig（幂等）。"""
    from backend.server.extensions import db
    from backend.server.db_models import SystemConfig

    defaults = get_default_platform_config()
    with app.app_context():
        changed = False
        for key, value in defaults.items():
            if SystemConfig.query.filter_by(key=key).first():
                continue
            stored = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            db.session.add(SystemConfig(key=key, value=stored))
            changed = True
        if changed:
            db.session.commit()
            app.logger.info("Seeded platform UI config into SystemConfig")


def load_platform_ui_config() -> Dict[str, Any]:
    """从 SystemConfig 加载 UI 配置，缺失项回退 DEFAULT_INFO。"""
    from backend.server.db_models import SystemConfig

    info = deepcopy(DEFAULT_INFO)
    info["footer"] = deepcopy(DEFAULT_INFO["footer"])
    info["footer"]["copyright_years"] = f"2022-{datetime.now().year}"

    try:
        keys = list(JSON_CONFIG_KEYS.keys()) + list(TEXT_CONFIG_KEYS.keys())
        rows = SystemConfig.query.filter(SystemConfig.key.in_(keys)).all()
        by_key = {row.key: row.value for row in rows}
    except Exception:
        by_key = {}

    for config_key, info_key in JSON_CONFIG_KEYS.items():
        if config_key in by_key:
            info[info_key] = _parse_json_value(by_key[config_key], info[info_key])

    for config_key, info_key in TEXT_CONFIG_KEYS.items():
        if config_key in by_key and by_key[config_key] is not None:
            info[info_key] = by_key[config_key]

    return info


def _truthy(value) -> bool:
    return str(value or "").lower() in ("true", "1", "yes")


def _load_system_config() -> Dict[str, str]:
    from backend.server.db_models import SystemConfig

    try:
        rows = SystemConfig.query.filter(SystemConfig.key.in_(SYSTEM_CONFIG_PUBLIC_KEYS)).all()
        return {row.key: row.value for row in rows}
    except Exception:
        return {}


def load_public_platform_info() -> Dict[str, Any]:
    """合并 UI 配置与 SystemConfig，供公开 API 使用。"""
    info = load_platform_ui_config()
    cfg = _load_system_config()

    if cfg.get("site_name"):
        info["name"] = cfg["site_name"]
    if cfg.get("site_description"):
        info["site_description"] = cfg["site_description"]
    if cfg.get("maintenance_message"):
        info["maintenance_message"] = cfg["maintenance_message"]
    if cfg.get("highlight_banner"):
        info["highlight_banner"] = cfg["highlight_banner"]

    info["maintenance"] = _truthy(cfg.get("maintenance_mode"))
    info["captcha_required"] = _truthy(cfg.get("captcha_required"))
    info["require_email_verification"] = _truthy(cfg.get("require_email_verification"))
    info["features"] = {
        key: _truthy(cfg.get(key, "false" if key == "captcha_required" else "true"))
        for key in BOOL_SYSTEM_KEYS
        if key != "maintenance_mode"
    }

    if not info.get("brand_desc") and info.get("site_description"):
        info["brand_desc"] = info["site_description"]

    raw_featured = (cfg.get("home_featured_game_id") or "").strip()
    if raw_featured.isdigit():
        info["home_featured_game_id"] = int(raw_featured)

    # 兼容别名：训练场 welcome
    if info.get("training_welcome"):
        info["training_welcome_banner"] = info["training_welcome"]

    return info
