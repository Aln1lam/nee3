#!/usr/bin/env python3
"""赛事全流程 API 探测 — 模拟用户点进比赛后的请求链"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
ACCOUNT = "neepu_admin"
PASSWORD = "NeepuAdmin2025!"


def login_session():
    s = requests.Session()
    r = s.post(
        f"{BASE}/api/auth/login",
        json={"account": ACCOUNT, "password": PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        raise SystemExit(f"LOGIN FAIL {r.status_code}: {r.text[:200]}")
    me = s.get(f"{BASE}/api/auth/me", timeout=10)
    if me.status_code != 200:
        raise SystemExit(f"/me FAIL {me.status_code}")
    return s, me.json()


def ok(status):
    return 200 <= status < 300


def probe(s, method, path, **kw):
    r = s.request(method, BASE + path, timeout=15, **kw)
    body = None
    if "json" in r.headers.get("content-type", ""):
        try:
            body = r.json()
        except Exception:
            body = None
    return r.status_code, body, r


def pick_game_with_challenges(s):
    r = s.get(f"{BASE}/api/competitions/?exclude_training=true", timeout=15)
    games = (r.json() or {}).get("data") or []
    best = None
    for g in games:
        gid = g["id"]
        cc = g.get("challenge_count") or 0
        if cc > 0:
            return g
        st, body, _ = probe(s, "GET", f"/api/challenges/games/{gid}/challenges")
        if ok(st):
            chs = body.get("data") if isinstance(body, dict) else body
            if isinstance(chs, list) and chs:
                g = dict(g)
                g["challenge_count"] = len(chs)
                return g
        if best is None:
            best = g
    return best or (games[0] if games else None)


def main():
    s, user = login_session()
    print(f"LOGIN OK user={user.get('nickname')} id={user.get('id')}\n")

    game = pick_game_with_challenges(s)
    if not game:
        print("NO GAMES")
        return
    gid = game["id"]
    print(f"GAME id={gid} title={game.get('title')!r} challenges={game.get('challenge_count')}\n")

    # 模拟前端各页面调用
    suites = [
        ("GamesHub / GameDetail", [
            ("GET", f"/api/competitions/{gid}"),
            ("GET", f"/api/competitions/{gid}/joined"),
            ("GET", "/api/teams/me"),
            ("POST", f"/api/competitions/{gid}/join", {}),
        ]),
        ("CTFCompetitions / challenges", [
            ("GET", f"/api/competitions/{gid}"),
            ("GET", f"/api/competitions/{gid}/joined"),
            ("GET", f"/api/ctf/games/{gid}/notices"),
            ("GET", f"/api/challenges/games/{gid}/challenges"),
            ("GET", "/api/teams/me", None, {"params": {"game_id": gid}}),
        ]),
        ("Legacy /api/games (compat)", [
            ("GET", "/api/games/"),
            ("GET", f"/api/games/{gid}/joined"),
            ("GET", f"/api/games/{gid}/challenges"),
            ("POST", f"/api/games/{gid}/join", {}),
        ]),
        ("Scoreboard", [
            ("GET", f"/api/games/{gid}/scoreboard"),
            ("GET", f"/api/ctf/games/{gid}/scoreboard"),
            ("GET", f"/api/ctf/games/{gid}/scoreboard/timeline"),
        ]),
        ("GameTeams", [
            ("GET", "/api/teams/me", None, {"params": {"game_id": gid}}),
            ("GET", "/api/teams/", None, {"params": {"game_id": gid}}),
            ("GET", f"/api/competitions/{gid}/divisions"),
        ]),
        ("GameAdmin", [
            ("GET", f"/api/competitions/{gid}"),
            ("GET", f"/api/challenges/games/{gid}/challenges"),
            ("GET", f"/api/ctf/games/{gid}/scoreboard"),
        ]),
    ]

    failed = []
    for suite_name, calls in suites:
        print(f"--- {suite_name} ---")
        for call in calls:
            method, path = call[0], call[1]
            payload = call[2] if len(call) > 2 else None
            extra = call[3] if len(call) > 3 else {}
            kw = dict(extra)
            if payload is not None:
                kw["json"] = payload
            st, body, _ = probe(s, method, path, **kw)
            mark = "OK" if ok(st) else "FAIL"
            hint = ""
            if isinstance(body, dict):
                hint = str(body.get("msg") or body.get("message") or body.get("error") or "")[:60]
                if "joined" in body:
                    hint += f" joined={body['joined']}"
                if "data" in body and isinstance(body["data"], list):
                    hint += f" data[{len(body['data'])}]"
                elif "items" in body:
                    hint += f" items[{len(body['items'])}]"
            print(f"  {mark} {st} {method} {path} {hint}")
            if not ok(st):
                failed.append((suite_name, st, method, path, hint))
        print()

    # 单题 API
    st, body, _ = probe(s, "GET", f"/api/challenges/games/{gid}/challenges")
    chs = []
    if ok(st) and isinstance(body, dict):
        chs = body.get("data") or []
    if chs:
        cid = chs[0]["id"]
        print(f"--- ChallengeDetail id={cid} ---")
        for method, path, payload in [
            ("GET", f"/api/challenges/{cid}", None),
            ("GET", f"/api/challenges/{cid}/stats", None),
            ("GET", f"/api/challenges/{cid}/hints", None),
            ("GET", f"/api/challenges/{cid}/container-status", None),
            ("GET", f"/api/challenges/{cid}/hammer", None),
            ("POST", f"/api/challenges/{cid}/submit", {"flag": "flag{test}"}),
        ]:
            kw = {"json": payload} if payload else {}
            st, body, _ = probe(s, method, path, **kw)
            mark = "OK" if ok(st) else "FAIL"
            hint = ""
            if isinstance(body, dict):
                hint = str(body.get("msg") or body.get("message") or "")[:50]
            print(f"  {mark} {st} {method} {path} {hint}")
            if not ok(st):
                failed.append(("ChallengeDetail", st, method, path, hint))
    else:
        print("--- ChallengeDetail: 该比赛无题目，跳过 ---")

    print(f"\n=== TOTAL FAIL {len(failed)} ===")
    for row in failed:
        print(" ", row)


if __name__ == "__main__":
    main()
