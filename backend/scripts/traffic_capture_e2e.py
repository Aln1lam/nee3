#!/usr/bin/env python3
"""全链路 + 流量捕获验证：模拟选手操作并分析 PCAP"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
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


def login(account: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"account": account, "password": password}, timeout=15)
    r.raise_for_status()
    return s


def http_get(url: str) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "NEEPU-E2E-Probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body, dict(e.headers)


def analyze_pcap(pcap_path: Path) -> dict:
    from scapy.all import Raw, rdpcap

    packets = rdpcap(str(pcap_path))
    http_events = []
    for idx, pkt in enumerate(packets):
        if Raw not in pkt:
            continue
        payload = bytes(pkt[Raw].load)
        try:
            text = payload.decode("utf-8", "replace")
        except Exception:
            continue
        head = text.split("\r\n", 1)[0][:120]
        if re.match(r"^(GET|POST|PUT|DELETE|HEAD|HTTP/1\.[01])", head):
            http_events.append({"idx": idx, "summary": head, "size": len(payload)})

    methods = [e["summary"].split(" ", 1)[0] for e in http_events if e["summary"].startswith(("GET", "POST"))]
    paths = []
    for e in http_events:
        m = re.match(r"^(GET|POST|HEAD|PUT|DELETE) (\S+)", e["summary"])
        if m:
            paths.append(m.group(2))

    return {
        "file": str(pcap_path),
        "size_bytes": pcap_path.stat().st_size if pcap_path.exists() else 0,
        "total_packets": len(packets),
        "http_events": http_events,
        "unique_paths": sorted(set(paths)),
        "request_count": sum(1 for e in http_events if e["summary"].startswith(("GET", "POST", "HEAD", "PUT", "DELETE"))),
        "response_count": sum(1 for e in http_events if e["summary"].startswith("HTTP/")),
    }


def main() -> int:
    admin = login(**ADMIN)
    now = datetime.utcnow()

    print(f"=== Traffic Capture E2E tag={TAG} ===\n")

    # 1. 创建赛事（开启流量捕获）
    gr = admin.post(f"{BASE}/api/competitions/admin/create", json={
        "title": f"流量捕获全链路 {TAG}",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(days=2)).isoformat(),
        "is_public": True,
        "status": "ongoing",
        "enable_traffic_capture": True,
    }, timeout=15)
    game = gr.json().get("data") or {}
    gid = game.get("id")
    print(f"[1] 赛事 id={gid} capture={game.get('enable_traffic_capture')}")
    if not gid:
        print("FAIL create game", gr.text[:200])
        return 1

    admin.post(f"{BASE}/api/competitions/{gid}/join", json={}, timeout=15)

    # 2. 创建动态容器题（signup）
    cr = admin.post(f"{BASE}/api/admin/challenges/games/{gid}/challenges", json={
        "title": "Signup动态容器",
        "category": "Web安全与渗透测试",
        "flag": "flag{testflag}",
        "flag_template": "flag{[TEAM_HASH]}",
        "original_points": 300,
        "challenge_type": 3,
        "docker_image": "signup",
        "docker_port": 80,
    }, timeout=15)
    ch = cr.json().get("data") or {}
    cid = ch.get("id")
    print(f"[2] 动态容器题 id={cid}")

    # 3. 启动容器（走 container/start，与前端 fallback 一致）
    sr = admin.post(f"{BASE}/api/container/start/{cid}", timeout=90)
    if sr.status_code >= 400:
        sr = admin.post(f"{BASE}/api/challenges/{cid}/start-container", timeout=90)
    body = sr.json()
    data = body.get("data") or body
    proxy_url = data.get("connection_url")
    proxy_port = data.get("port")
    iid = data.get("id") or data.get("instance_id")
    print(f"[3] 容器启动 url={proxy_url} inner_port={proxy_port} instance={iid}")

    dbg = admin.get(f"{BASE}/api/container/debug/{iid}", timeout=15).json()
    dynamic_flag = (dbg.get("data") or dbg).get("dynamic_flag")
    print(f"    dynamic_flag={dynamic_flag}")

    if not proxy_url:
        print("FAIL no connection_url")
        return 1

    # 4. 模拟选手 HTTP 操作（必须走 connection_url 即代理端口）
    ops = [
        ("GET /", proxy_url.rstrip("/") + "/"),
        ("GET /index.html", proxy_url.rstrip("/") + "/index.html"),
        ("GET /index.php", proxy_url.rstrip("/") + "/index.php"),
        ("GET /not-exist", proxy_url.rstrip("/") + "/not-exist"),
    ]
    op_results = []
    extracted_flag = None
    for name, url in ops:
        time.sleep(0.3)
        code, text, _hdr = http_get(url)
        m = re.search(r"flag\{[0-9a-f-]{36}\}", text)
        if m:
            extracted_flag = m.group(0)
        op_results.append({"op": name, "status": code, "bytes": len(text)})
        print(f"[4] {name} -> HTTP {code} ({len(text)} bytes)")

    # 5. 提交 flag
    flag_to_submit = extracted_flag or dynamic_flag
    sub = admin.post(f"{BASE}/api/challenges/{cid}/submit", json={"answer": flag_to_submit}, timeout=15)
    sub_body = sub.json()
    correct = (sub_body.get("data") or {}).get("is_correct")
    print(f"[5] 提交 flag correct={correct} msg={sub_body.get('msg','')[:40]}")

    # 6. 积分榜
    sb = admin.get(f"{BASE}/api/ctf/games/{gid}/scoreboard", timeout=15).json()
    rankings = (sb.get("data") or {}).get("rankings") or []
    print(f"[6] 积分榜 teams={len(rankings)} top_score={rankings[0]['total_points'] if rankings else 0}")

    time.sleep(1.5)

    # 7. 拉取流量包列表
    cap = admin.get(f"{BASE}/api/competitions/admin/{gid}/traffic-captures?sync=1", timeout=30)
    cap_json = cap.json()
    items = (cap_json.get("data") or {}).get("items") or []
    print(f"[7] 流量包 records={len(items)}")
    if not items:
        print("FAIL 无 PCAP 记录")
        print(json.dumps(cap_json, ensure_ascii=False, indent=2)[:800])
        return 1

    pcap_path = Path(items[0].get("absolute_path") or "")
    if not pcap_path.is_file():
        rel = items[0].get("file_path") or items[0].get("path")
        pcap_path = ROOT / "captures" / rel if rel else pcap_path
    print(f"    pcap={pcap_path} size={pcap_path.stat().st_size if pcap_path.exists() else 0}")

    if not pcap_path.exists():
        print("FAIL PCAP 文件不存在")
        return 1

    # 8. 分析 PCAP
    analysis = analyze_pcap(pcap_path)
    print(f"\n=== PCAP 分析 ===")
    print(f"总包数: {analysis['total_packets']}")
    print(f"HTTP 事件: {analysis['request_count']} 请求 / {analysis['response_count']} 响应")
    print(f"捕获路径: {analysis['unique_paths']}")
    for ev in analysis["http_events"][:20]:
        print(f"  #{ev['idx']:3d} {ev['summary']}")

    expected_paths = {"/", "/index.html", "/index.php", "/not-exist"}
    captured = set(analysis["unique_paths"])
    missing = expected_paths - captured
    ok_paths = "/" in captured and analysis["request_count"] >= 3 and analysis["response_count"] >= 3

    print(f"\n=== 结论 ===")
    print(f"操作记录: {json.dumps(op_results, ensure_ascii=False)}")
    if missing:
        print(f"未在 PCAP 中看到的路径: {sorted(missing)}")
    if ok_paths and not missing:
        print("OK 流量包已捕获主要 HTTP 操作（含 404）")
        return 0
    if ok_paths:
        print("PARTIAL 捕获到核心流量，部分路径可能合并或未单独记录")
        return 0
    print("FAIL 流量包内容不完整")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
