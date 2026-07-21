#!/usr/bin/env python3
"""SQL 注入交互 + 流量捕获验证：POST/GET payload 是否进入 PCAP"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuAdmin2025!"}
TAG = datetime.utcnow().strftime("%m%d%H%M%S")

SQLI_PAYLOADS = [
    "admin' OR '1'='1",
    "1 OR 1=1",
    "1 UNION SELECT 1,note FROM secrets-- ",
]


def login(account: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"account": account, "password": password}, timeout=15)
    r.raise_for_status()
    return s


def http_get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "NEEPU-SQLi-E2E/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def http_post(url: str, data: dict[str, str]) -> tuple[int, str]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "User-Agent": "NEEPU-SQLi-E2E/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def extract_http_payloads(pcap_path: Path) -> dict:
    from scapy.all import Raw, rdpcap

    packets = rdpcap(str(pcap_path))
    events = []
    all_text = []
    for idx, pkt in enumerate(packets):
        if Raw not in pkt:
            continue
        payload = bytes(pkt[Raw].load)
        try:
            text = payload.decode("utf-8", "replace")
        except Exception:
            continue
        all_text.append(text)
        head = text.split("\r\n", 1)[0][:160]
        if re.match(r"^(GET|POST|PUT|DELETE|HEAD|HTTP/1\.[01])", head):
            events.append({"idx": idx, "summary": head, "size": len(payload), "body": text})

    joined = "\n".join(all_text)
    decoded = urllib.parse.unquote_plus(joined)
    found_payloads = []
    for p in SQLI_PAYLOADS:
        if p in joined or p in decoded:
            found_payloads.append(p)
        elif p.replace(" ", "") in joined.replace(" ", "") or p.replace(" ", "") in decoded.replace(" ", ""):
            found_payloads.append(p)
    has_post_login = "POST /login.php" in joined
    has_get_search = "GET /search.php" in joined
    has_username = "username=" in joined
    has_union = "UNION SELECT" in decoded.upper() or "union select" in decoded.lower()

    return {
        "file": str(pcap_path),
        "total_packets": len(packets),
        "http_events": events,
        "found_payloads": found_payloads,
        "has_post_login": has_post_login,
        "has_get_search": has_get_search,
        "has_username": has_username,
        "has_union": has_union,
        "sample_bodies": [e["body"][:500] for e in events[:8]],
    }


def main() -> int:
    admin = login(**ADMIN)
    now = datetime.utcnow()
    print(f"=== SQLi Traffic Capture E2E tag={TAG} ===\n")

    gr = admin.post(
        f"{BASE}/api/competitions/admin/create",
        json={
            "title": f"SQLi流量捕获 {TAG}",
            "start_time": (now - timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(days=2)).isoformat(),
            "is_public": True,
            "status": "ongoing",
            "enable_traffic_capture": True,
        },
        timeout=15,
    )
    game = gr.json().get("data") or {}
    gid = game.get("id")
    print(f"[1] 赛事 id={gid}")
    if not gid:
        print("FAIL", gr.text[:300])
        return 1

    admin.post(f"{BASE}/api/competitions/{gid}/join", json={}, timeout=15)

    cr = admin.post(
        f"{BASE}/api/admin/challenges/games/{gid}/challenges",
        json={
            "title": "SQLi动态容器",
            "category": "Web安全与渗透测试",
            "flag": "flag{testflag}",
            "flag_template": "flag{[TEAM_HASH]}",
            "original_points": 300,
            "challenge_type": 3,
            "docker_image": "sqli-simple",
            "docker_port": 80,
        },
        timeout=15,
    )
    ch = cr.json().get("data") or {}
    cid = ch.get("id")
    print(f"[2] 题目 id={cid}")

    sr = admin.post(f"{BASE}/api/container/start/{cid}", timeout=120)
    if sr.status_code >= 400:
        sr = admin.post(f"{BASE}/api/challenges/{cid}/start-container", timeout=120)
    data = sr.json().get("data") or sr.json()
    proxy_url = (data.get("connection_url") or "").rstrip("/")
    iid = data.get("id") or data.get("instance_id")
    print(f"[3] 容器 proxy={proxy_url} instance={iid}")
    if not proxy_url:
        print("FAIL no connection_url", sr.text[:400])
        return 1

    time.sleep(8)

    ops = []
    for attempt in range(5):
        code, text = http_get(f"{proxy_url}/")
        if code != 502:
            break
        time.sleep(3)
    ops.append(("GET /", code, len(text)))
    print(f"[4] GET / -> {code}")

    code, text = http_get(f"{proxy_url}/login.php")
    ops.append(("GET /login.php", code, len(text)))
    print(f"[4] GET /login.php -> {code}")

    code, text = http_post(
        f"{proxy_url}/login.php",
        {"username": "admin' OR '1'='1", "password": "x"},
    )
    ops.append(("POST /login.php SQLi", code, len(text)))
    print(f"[4] POST /login.php payload=admin' OR '1'='1 -> {code} ({len(text)} bytes)")
    if "Welcome" in text:
        print("    login bypass OK")

    code, text = http_get(f"{proxy_url}/search.php?id=1")
    ops.append(("GET /search.php?id=1", code, len(text)))
    print(f"[4] GET /search.php?id=1 -> {code}")

    q = urllib.parse.quote("1 UNION SELECT 1,note FROM secrets-- ")
    code, text = http_get(f"{proxy_url}/search.php?id={q}")
    ops.append(("GET /search.php UNION", code, len(text)))
    print(f"[4] GET /search.php UNION -> {code}")
    m = re.search(r"flag\{[0-9a-f-]{36}\}", text)
    if m:
        print(f"    extracted flag={m.group(0)}")

    time.sleep(2)

    cap = admin.get(f"{BASE}/api/competitions/admin/{gid}/traffic-captures?sync=1", timeout=30)
    items = (cap.json().get("data") or {}).get("items") or []
    print(f"[5] PCAP records={len(items)}")
    if not items:
        print("FAIL no PCAP")
        return 1

    pcap_path = Path(items[0].get("absolute_path") or "")
    if not pcap_path.is_file():
        rel = items[0].get("file_path") or items[0].get("path")
        pcap_path = ROOT / "captures" / rel
    print(f"    pcap={pcap_path} size={pcap_path.stat().st_size if pcap_path.exists() else 0}")

    analysis = extract_http_payloads(pcap_path)
    print("\n=== PCAP 分析 ===")
    print(f"总包数: {analysis['total_packets']}")
    print(f"HTTP 事件: {len(analysis['http_events'])}")
    for ev in analysis["http_events"]:
        print(f"  #{ev['idx']:3d} {ev['summary']}")
    print(f"POST /login.php: {analysis['has_post_login']}")
    print(f"GET /search.php: {analysis['has_get_search']}")
    print(f"username= 参数: {analysis['has_username']}")
    print(f"UNION SELECT: {analysis['has_union']}")
    print(f"命中 payload: {analysis['found_payloads']}")

    ok = (
        analysis["has_post_login"]
        and analysis["has_get_search"]
        and analysis["has_username"]
        and len(analysis["found_payloads"]) >= 1
    )
    print("\n=== 结论 ===")
    print(json.dumps(ops, ensure_ascii=False))
    if ok:
        print("OK SQL 注入交互流量已进入 PCAP（含 POST body 与 GET 参数）")
        return 0
    print("FAIL 交互流量未完整进入 PCAP")
    if analysis["sample_bodies"]:
        print("\n--- PCAP 样本 ---")
        for i, sample in enumerate(analysis["sample_bodies"][:3]):
            print(f"[sample {i}]\n{sample}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
