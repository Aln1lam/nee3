# -*- coding: utf-8 -*-
"""Live API联调：S1 P0 关键路径（需本机后端 + MySQL）。"""
import sys
import requests

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuAdmin2025!"}

def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=10)
    print("login", r.status_code, r.text[:200])
    r.raise_for_status()
    token = r.json().get("access_token") or (r.json().get("data") or {}).get("access_token")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"

    # B05/F03 dynamic packages stub
    r = s.get(f"{BASE}/api/admin/dynamic-packages/challenges/1/packages", timeout=10)
    print("dyn_pkg", r.status_code, r.text[:300])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("meta", {}).get("status") == "stub"
    assert body.get("data") == []

    r = s.post(f"{BASE}/api/admin/dynamic-packages/challenges/1/upload", timeout=10)
    print("dyn_upload", r.status_code, r.text[:200])
    assert r.status_code == 501

    # B04 sensitive team name — create may fail for other reasons; check rejection msg
    r = s.post(f"{BASE}/api/teams/", json={"name": "官方战队", "game_id": 1}, timeout=10)
    print("team_bad", r.status_code, r.text[:300])
    assert r.status_code == 400, r.text
    msg = (r.json() or {}).get("msg") or ""
    assert "不允许" in msg or "敏感" in msg, msg

    # B01 routes exist
    r = s.get(f"{BASE}/api/challenges/1/container-status", timeout=10)
    print("container_status", r.status_code, r.text[:200])
    assert r.status_code != 404

    r = s.get(f"{BASE}/api/platform/instances", timeout=10)
    print("instances", r.status_code, r.text[:200])
    assert r.status_code in (200, 401, 403)

    # B03 rate limit decorators present — smoke one submit without crashing
    r = s.post(f"{BASE}/api/challenges/1/submit", json={"flag": "flag{x}"}, timeout=10)
    print("submit", r.status_code, r.text[:200])
    assert r.status_code != 404

    print("LIVE_OK")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("LIVE_FAIL", e)
        sys.exit(1)
