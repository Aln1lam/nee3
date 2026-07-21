#!/usr/bin/env python3
"""容器生命周期：销毁 / 1h 到期 / 延时续期"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import docker
import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuAdmin2025!"}
TAG = datetime.utcnow().strftime("%m%d%H%M%S")


def login(**cred) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=cred, timeout=15)
    r.raise_for_status()
    return s


def docker_exists(cid: str | None) -> bool:
    if not cid:
        return False
    try:
        docker.from_env().containers.get(cid)
        return True
    except docker.errors.NotFound:
        return False
    except Exception:
        return False


def create_game_and_challenge(admin: requests.Session) -> tuple[int, int]:
    now = datetime.utcnow()
    gr = admin.post(
        f"{BASE}/api/competitions/admin/create",
        json={
            "title": f"容器生命周期 {TAG}",
            "start_time": (now - timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(days=1)).isoformat(),
            "is_public": True,
            "status": "ongoing",
        },
        timeout=15,
    )
    gid = (gr.json().get("data") or {}).get("id")
    admin.post(f"{BASE}/api/competitions/{gid}/join", json={}, timeout=15)
    cr = admin.post(
        f"{BASE}/api/admin/challenges/games/{gid}/challenges",
        json={
            "title": "Signup容器生命周期",
            "category": "Web",
            "flag": "flag{testflag}",
            "flag_template": "flag{[TEAM_HASH]}",
            "original_points": 100,
            "challenge_type": 3,
            "docker_image": "signup",
            "docker_port": 80,
        },
        timeout=15,
    )
    cid = (cr.json().get("data") or {}).get("id")
    return gid, cid


def start_container(admin: requests.Session, cid: int) -> dict:
    for attempt in range(3):
        sr = admin.post(f"{BASE}/api/container/start/{cid}", timeout=120)
        if sr.status_code >= 400:
            sr = admin.post(f"{BASE}/api/challenges/{cid}/start-container", timeout=120)
        body = sr.json()
        if sr.status_code == 429:
            wait = (body.get("wait_seconds") or body.get("data", {}).get("wait_seconds") or 65)
            print(f"  启动限频，等待 {wait}s ...")
            time.sleep(wait + 2)
            continue
        sr.raise_for_status()
        return body.get("data") or body
    raise RuntimeError("start container failed after retries")


def test_manual_destroy(admin: requests.Session, cid: int) -> bool:
    print("\n=== [1] 手动销毁 ===")
    data = start_container(admin, cid)
    iid = data.get("id") or data.get("instance_id")
    cid_full = data.get("container_id")
    print(f"  启动 instance={iid} docker={str(cid_full)[:12] if cid_full else None}")
    assert docker_exists(cid_full), "容器应存在"

    r = admin.post(f"{BASE}/api/challenges/instances/{iid}/stop", timeout=30)
    print(f"  stop API -> {r.status_code} {r.json().get('msg') or r.json().get('message')}")
    if r.status_code != 200:
        return False

    time.sleep(1)
    gone = not docker_exists(cid_full)
    st = admin.get(f"{BASE}/api/challenges/{cid}/container-status", timeout=15).json()
    payload = st.get("data") or {}
    status = payload.get("status")
    has = payload.get("has_container")
    print(f"  docker 已删除: {gone}, 状态={status}, has_container={has}")
    return gone and (status in ("no_container", "expired") or has is False)


def test_extend(admin: requests.Session, cid: int) -> bool:
    print("\n=== [2] 延时 +1 小时 ===")
    data = start_container(admin, cid)
    iid = data.get("id") or data.get("instance_id")
    before = data.get("expires_at")
    print(f"  启动 instance={iid}, expires_at={before}")

    r = admin.post(f"{BASE}/api/challenges/instances/{iid}/extend", json={}, timeout=15)
    body = r.json()
    print(f"  extend API -> {r.status_code} {body.get('msg')}")
    if r.status_code != 200:
        return False

    after = (body.get("data") or {}).get("expires_at")
    remain = (body.get("data") or {}).get("remaining_seconds")
    print(f"  新 expires_at={after}, remaining_seconds={remain}")

    if not before or not after:
        return False
    delta = datetime.fromisoformat(after.replace("Z", "")) - datetime.fromisoformat(before.replace("Z", ""))
    ok = 3500 <= delta.total_seconds() <= 3700
    print(f"  延时时长 ~{int(delta.total_seconds())}s (期望 ~3600s): {'OK' if ok else 'FAIL'}")
    return ok


def test_auto_expire(admin: requests.Session, cid: int) -> bool:
    print("\n=== [3] 到期自动销毁（模拟过期） ===")
    from backend.server.extensions import db
    from backend.server.db_models import CtfGameInstance
    from backend.app import create_app

    data = start_container(admin, cid)
    iid = data.get("id") or data.get("instance_id")
    cid_full = data.get("container_id")
    print(f"  启动 instance={iid} docker={str(cid_full)[:12] if cid_full else None}")
    assert docker_exists(cid_full), "容器应存在"

    app = create_app()
    with app.app_context():
        inst = CtfGameInstance.query.get(iid)
        inst.expires_at = datetime.utcnow() - timedelta(minutes=5)
        db.session.commit()
        print(f"  DB 已将 expires_at 设为过去: {inst.expires_at.isoformat()}")

    st = admin.get(f"{BASE}/api/challenges/{cid}/container-status", timeout=15)
    body = st.json()
    payload = body.get("data") or {}
    print(f"  状态 API -> {payload.get('status') or payload.get('message')}")

    time.sleep(1)
    gone = not docker_exists(cid_full)
    print(f"  docker 已删除: {gone}")
    expired = payload.get("status") == "expired" or payload.get("has_container") is False
    return gone and expired


def main() -> int:
    print(f"=== Container Lifecycle E2E tag={TAG} ===")
    admin = login(**ADMIN)
    _, cid = create_game_and_challenge(admin)
    print(f"题目 id={cid}")

    results = {
        "destroy": test_manual_destroy(admin, cid),
        "extend": test_extend(admin, cid),
        "auto_expire": test_auto_expire(admin, cid),
    }
    print("\n=== 结论 ===")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
