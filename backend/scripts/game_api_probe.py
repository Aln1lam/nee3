#!/usr/bin/env python3
"""探测赛事详情页相关 API 状态"""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from flask_jwt_extended import create_access_token

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import create_app
from backend.server.db_models import User

BASE = "http://127.0.0.1:5000"


def auth_session():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            raise SystemExit("no admin user")
        token = create_access_token(identity=str(admin.id))
    s = requests.Session()
    s.cookies.set("neepu_token", token, path="/")
    return s, admin.id


def main():
    s, uid = auth_session()
    print(f"AUTH cookie session uid={uid}\n")

    r = s.get(f"{BASE}/api/competitions/?exclude_training=true", timeout=10)
    body = r.json()
    games = body.get("data") or []
    print(f"GAMES count={len(games)}")
    if not games:
        return

    gid = games[0]["id"]
    title = games[0].get("title")
    print(f"PROBE game_id={gid} title={title!r}\n")

    paths = [
        ("GET", f"/api/competitions/{gid}"),
        ("GET", f"/api/competitions/{gid}/joined"),
        ("GET", "/api/competitions/my"),
        ("POST", f"/api/competitions/{gid}/join", {}),
        ("GET", f"/api/ctf/games/{gid}/notices"),
        ("GET", f"/api/ctf/games/{gid}/challenges"),
        ("GET", f"/api/challenges/games/{gid}/challenges"),
        ("GET", f"/api/games/{gid}/challenges"),
        ("GET", f"/api/games/{gid}/scoreboard"),
        ("GET", f"/api/ctf/games/{gid}/scoreboard"),
        ("GET", "/api/teams/me"),
        ("GET", f"/api/teams/me?game_id={gid}"),
        ("GET", f"/api/teams/?game_id={gid}"),
        ("GET", f"/api/competitions/{gid}/divisions"),
    ]

    failed = []
    for item in paths:
        method, path = item[0], item[1]
        payload = item[2] if len(item) > 2 else None
        kw = {"timeout": 10}
        if payload is not None:
            kw["json"] = payload
        resp = s.request(method, BASE + path, **kw)
        hint = summarize(resp)
        mark = "OK" if 200 <= resp.status_code < 300 else "FAIL"
        print(f"{mark:4} {resp.status_code} {method:4} {path}")
        if hint:
            print(f"      {hint}")
        if mark == "FAIL":
            failed.append((resp.status_code, method, path, hint))

    r = s.get(f"{BASE}/api/challenges/games/{gid}/challenges", timeout=10)
    if r.ok:
        data = r.json()
        chs = data if isinstance(data, list) else data.get("data") or data.get("items") or []
        if chs:
            cid = chs[0].get("id")
            print(f"\nCHALLENGE probe id={cid}")
            for method, path in [
                ("GET", f"/api/challenges/{cid}"),
                ("GET", f"/api/challenges/{cid}/stats"),
                ("GET", f"/api/challenges/{cid}/hints"),
                ("GET", f"/api/challenges/{cid}/container-status"),
                ("GET", f"/api/challenges/{cid}/hammer"),
            ]:
                resp = s.request(method, BASE + path, timeout=10)
                mark = "OK" if 200 <= resp.status_code < 300 else "FAIL"
                print(f"{mark:4} {resp.status_code} {method:4} {path}  {summarize(resp)}")
                if mark == "FAIL":
                    failed.append((resp.status_code, method, path, summarize(resp)))

    print(f"\n=== FAILED {len(failed)} ===")
    for row in failed:
        print(" ", row)


def summarize(resp):
    ct = resp.headers.get("content-type", "")
    if "json" not in ct:
        return resp.text[:80]
    try:
        body = resp.json()
    except Exception:
        return resp.text[:80]
    if isinstance(body, dict):
        parts = []
        for k in ("msg", "message", "error", "code", "joined"):
            if k in body and body[k] is not None:
                parts.append(f"{k}={body[k]!r}")
        if "data" in body:
            d = body["data"]
            if isinstance(d, list):
                parts.append(f"data[{len(d)}]")
            elif isinstance(d, dict):
                parts.append(f"data.keys={list(d.keys())[:6]}")
        if "items" in body:
            parts.append(f"items[{len(body['items'])}]")
        return " ".join(parts)[:120]
    if isinstance(body, list):
        return f"list[{len(body)}]"
    return str(body)[:80]


if __name__ == "__main__":
    main()

