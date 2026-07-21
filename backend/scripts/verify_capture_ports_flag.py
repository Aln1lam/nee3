#!/usr/bin/env python3
"""验证：端口 10000-20000、UUID flag、流量捕获"""
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
TAG = datetime.utcnow().strftime("%H%M%S")


def main():
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"account": "neepu_admin", "password": "NeepuAdmin2025!"})
    assert r.status_code == 200, r.text

    now = datetime.utcnow()
    gr = s.post(f"{BASE}/api/competitions/admin/create", json={
        "title": f"CaptureTest {TAG}",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(days=1)).isoformat(),
        "is_public": True,
        "status": "ongoing",
        "enable_traffic_capture": True,
    })
    gid = gr.json()["data"]["id"]
    print("game", gid, "capture=", gr.json()["data"].get("enable_traffic_capture"))

    cr = s.post(f"{BASE}/api/admin/challenges/games/{gid}/challenges", json={
        "title": "DynCapture",
        "category": "Web安全与渗透测试",
        "flag": "flag{testflag}",
        "flag_template": "flag{[TEAM_HASH]}",
        "original_points": 200,
        "challenge_type": 3,
        "docker_image": "signup",
        "docker_port": 80,
    })
    cid = cr.json()["data"]["id"]
    print("challenge", cid)

    s.post(f"{BASE}/api/competitions/{gid}/join", json={})
    sr = s.post(f"{BASE}/api/container/start/{cid}", timeout=90)
    print("start", sr.status_code, sr.text[:300])
    data = sr.json().get("data") or {}
    port = data.get("port")
    url = data.get("connection_url", "")
    print("port", port, "url", url)
    assert 10000 <= int(port) <= 20000, f"port out of range: {port}"

    iid = data.get("id") or data.get("instance_id")
    dbg = s.get(f"{BASE}/api/container/debug/{iid}").json()
    flag = (dbg.get("data") or dbg).get("dynamic_flag")
    print("flag", flag)
    assert re.fullmatch(r"flag\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}", flag), flag

    cap = s.get(f"{BASE}/api/competitions/admin/{gid}/traffic-captures?sync=1")
    print("captures", cap.status_code, cap.text[:400])
    items = (cap.json().get("data") or {}).get("captures") or cap.json().get("data") or []
    assert items, "no pcap records"
    print("OK all checks passed")


if __name__ == "__main__":
    main()
