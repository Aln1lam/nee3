"""管理端 API 冒烟测试 — 对接运行中的后端 (127.0.0.1:5000)

路由契约与 frontend/src/services/admin/{platform,ctf}.js 对齐。
/api/admin/games* 为遗留路径，新代码应使用 /api/competitions/admin/*。
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app
from backend.server.db_models import User, CtfGame
from flask_jwt_extended import create_access_token

BASE = "http://127.0.0.1:5000"


def admin_session():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("ERROR: no admin user")
            sys.exit(1)
        token = create_access_token(identity=str(admin.id))
        game = CtfGame.query.order_by(CtfGame.id.desc()).first()
        game_id = game.id if game else 0
    s = requests.Session()
    s.cookies.set("neepu_token", token, path="/")
    return s, game_id


def probe(session, method, path, expect_deprecation=False, expect_status=None):
    url = BASE + path
    try:
        r = session.request(method, url, timeout=10)
        body = r.json() if "application/json" in r.headers.get("content-type", "") else {}
        if expect_status is not None:
            ok = r.status_code == expect_status
        else:
            ok = 200 <= r.status_code < 300
        hint = ""
        if isinstance(body, dict):
            hint = body.get("msg") or body.get("error") or body.get("message") or ""
        elif isinstance(body, list):
            hint = f"{len(body)} items"
        if expect_deprecation and r.headers.get("Deprecation") != "true":
            ok = False
            hint = (hint + " missing Deprecation header").strip()
        return {"method": method, "path": path, "status": r.status_code, "ok": ok, "hint": str(hint)}
    except Exception as e:
        return {"method": method, "path": path, "status": "ERR", "ok": False, "hint": str(e)}


def main():
    session, game_id = admin_session()
    tests = [
        ("GET", "/api/admin/platform/dashboard"),
        ("GET", "/api/admin/platform/stats/articles-distribution"),
        ("GET", "/api/admin/platform/users?page=1"),
        ("GET", "/api/admin/platform/articles?page=1"),
        ("GET", "/api/admin/platform/carousel"),
        ("GET", "/api/admin/platform/announcements"),
        ("GET", "/api/admin/platform/logs?page=1&per_page=10"),
        ("GET", "/api/admin/platform/logs/stats"),
        ("GET", "/api/admin/platform/logs/months"),
        ("GET", "/api/admin/platform/config"),
        ("GET", "/api/admin/platform/config/ui"),
        ("GET", "/api/admin/platform/env"),
        ("GET", "/api/admin/cheat-detection?page=1&per_page=10"),
        ("GET", "/api/admin/first-solves?page=1&per_page=10"),
        ("GET", "/api/admin/games", {"expect_status": 410, "expect_deprecation": True}),
        ("GET", "/api/games/", {"expect_status": 410, "expect_deprecation": True}),
        ("GET", "/api/ctf/games?per_page=10", {"expect_status": 410, "expect_deprecation": True}),
        ("GET", "/api/competitions/?per_page=10"),
        ("GET", "/api/teams/admin"),
        ("GET", f"/api/admin/first-solves?game_id={game_id}"),
        ("GET", f"/api/competitions/admin/{game_id}/traffic-captures?sync=0"),
        ("GET", f"/api/competitions/admin/{game_id}/stats"),
        ("GET", f"/api/challenges/games/{game_id}/challenges"),
        ("GET", f"/api/ctf/games/{game_id}/scoreboard"),
        # 已知错误路径（应 404，用于回归）
        ("GET", f"/api/ctf/games/{game_id}/first-solves"),
    ]

    passed, failed, expected_fail = [], [], []
    for item in tests:
        method, path = item[0], item[1]
        opts = item[2] if len(item) > 2 else {}
        row = probe(
            session,
            method,
            path,
            expect_deprecation=opts.get("expect_deprecation", False),
            expect_status=opts.get("expect_status"),
        )
        if "/first-solves" in path and "ctf/games" in path:
            (expected_fail if row["status"] in (404, 410) else failed).append(row)
            continue
        (passed if row["ok"] else failed).append(row)

    print(f"\n=== Admin smoke test @ {BASE} (game_id={game_id}) ===")
    print(f"PASS {len(passed)} / FAIL {len(failed)} / EXPECTED_FAIL {len(expected_fail)} / TOTAL {len(tests)}\n")
    for row in passed:
        print(f"  OK   {row['status']} {row['method']} {row['path']}")
    for row in expected_fail:
        print(f"  EXP  {row['status']} {row['method']} {row['path']}  (legacy broken path)")
    for row in failed:
        print(f"  FAIL {row['status']} {row['method']} {row['path']}  {row['hint'][:80]}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
