"""
遗留蓝图 /api/games — 已全部下线（410）。

继任路径：
- 赛事列表 / join / leave / divisions → /api/competitions/*
- Flag 提交 / 提示 / 容器 → /api/challenges/*
- 排行榜（含 timeline/user）→ /api/ctf/games/<id>/scoreboard*
"""
from flask import Blueprint, jsonify

bp = Blueprint("games", __name__)

_SUCCESSORS = {
    "list/join/leave/divisions": "/api/competitions/*",
    "submit/hints/instances": "/api/challenges/*",
    "scoreboard": "/api/ctf/games/<id>/scoreboard",
}


def _gone():
    resp = jsonify({
        "code": 410,
        "msg": "Gone: /api/games is retired",
        "successors": _SUCCESSORS,
    })
    resp.status_code = 410
    resp.headers["Deprecation"] = "true"
    resp.headers["Link"] = '</api/competitions/>; rel="successor-version"'
    resp.headers["X-Deprecated-Endpoint"] = "/api/competitions/*|/api/challenges/*|/api/ctf/*"
    return resp


@bp.route("/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@bp.route("/<path:subpath>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def legacy_games_gone(subpath=""):
    return _gone()
