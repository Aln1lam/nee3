#!/usr/bin/env python3
"""完整赛事链路 E2E：创建赛事/题目 → 报名 → 静态附件/容器/动态容器 → 提交 → 积分榜/一二三血"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuAdmin2025!"}
TAG = datetime.utcnow().strftime("%m%d%H%M%S")
DOCKER_IMAGE = "signup:latest"
SIGNUP_DIR = ROOT / "docker_templates" / "signup"
SIGNUP_FLAG_TEMPLATE = "flag{[TEAM_HASH]}"

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = ""):
    results.append((name, ok, detail))
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def login(account: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"account": account, "password": password}, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"login {account} -> {r.status_code} {r.text[:200]}")
    return s


def j(r: requests.Response):
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text[:300]}


def ensure_test_users(app) -> list[dict]:
    from backend.server.extensions import db
    from backend.server.db_models import User

    users = []
    with app.app_context():
        for i in range(1, 4):
            email = f"e2e_blood_{TAG}_{i}@test.local"
            username = f"e2e_blood_{TAG}_{i}"
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(email=email, username=username, nickname=f"E2E{i}", email_verified=True)
                u.set_password("E2eTest2025!")
                db.session.add(u)
            else:
                u.set_password("E2eTest2025!")
                u.username = username
            db.session.commit()
            users.append({"id": u.id, "email": email, "username": username, "password": "E2eTest2025!"})
    return users


def main() -> int:
    from backend.app import create_app
    from backend.server.db_models import CtfGame, CtfSolves, CtfGameNotice

    app = create_app()
    blood_users = ensure_test_users(app)
    print(f"=== Full Competition E2E @ {BASE} tag={TAG} ===\n")

    admin = login(**ADMIN)
    me = admin.get(f"{BASE}/api/auth/me", timeout=10).json()
    record("Admin 登录", True, f"{me.get('nickname')} id={me.get('id')}")

    # --- 1. 创建赛事 ---
    now = datetime.utcnow()
    game_payload = {
        "title": f"E2E 全链路测试 {TAG}",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(days=3)).isoformat(),
        "is_public": True,
        "status": "ongoing",
        "description": "自动化全链路探针",
        "summary": "静态/动态/容器/一二三血",
    }
    r = admin.post(f"{BASE}/api/competitions/admin/create", json=game_payload, timeout=15)
    body = j(r)
    ok = r.status_code == 200 and body.get("code") == 200
    game = body.get("data") or {}
    gid = game.get("id")
    record("创建赛事", ok, f"id={gid} title={game.get('title')!r}")
    if not ok or not gid:
        return 1

    flags = {
        "static": f"flag{{static_{TAG}}}",
        "static_container": f"flag{{static_ctr_{TAG}}}",
        "signup_placeholder": "flag{testflag}",
        "dynamic_container_tpl": SIGNUP_FLAG_TEMPLATE,
        "blood": f"flag{{blood_{TAG}}}",
    }

    challenges_spec = [
        ("静态附件题", 0, flags["static"], None, 100),
        ("静态容器题", 1, flags["static_container"], DOCKER_IMAGE, 200),
        ("动态附件题", 2, flags["signup_placeholder"], None, 150),
        ("动态容器题", 3, flags["signup_placeholder"], DOCKER_IMAGE, 250),
        ("一二三血题", 0, flags["blood"], None, 500),
    ]

    ch_map: dict[str, dict] = {}
    for title, ctype, flag, image, pts in challenges_spec:
        payload = {
            "title": title,
            "category": "Web安全与渗透测试",
            "description": f"E2E {title}",
            "flag": flag,
            "original_points": pts,
            "challenge_type": ctype,
            "min_score_rate": 0.25,
            "difficulty": 5.0,
        }
        if ctype in (1, 3):
            payload["docker_image"] = (image or DOCKER_IMAGE).split(":")[0]
            payload["docker_port"] = 80
        if ctype in (2, 3):
            payload["flag_template"] = SIGNUP_FLAG_TEMPLATE

        r = admin.post(f"{BASE}/api/admin/challenges/games/{gid}/challenges", json=payload, timeout=15)
        body = j(r)
        ok = r.status_code == 200 and body.get("code") == 200
        ch = body.get("data") or {}
        key = title.replace("题", "")
        ch_map[key] = ch
        record(f"创建题目: {title}", ok, f"id={ch.get('id')} type={ctype} pts={pts}")

    static_ch = ch_map.get("静态附件")
    if static_ch and static_ch.get("id"):
        cid = static_ch["id"]
        content = io.BytesIO(f"E2E attachment content {TAG}\nflag hint: {flags['static']}\n".encode())
        files = {"file": (f"e2e_{TAG}.txt", content, "text/plain")}
        r = admin.post(
            f"{BASE}/api/admin/challenges/games/{gid}/challenges/{cid}/attachments",
            files=files,
            timeout=15,
        )
        body = j(r)
        ok = r.status_code == 200 and body.get("code") == 200
        att_id = (body.get("data") or {}).get("attachment_id")
        record("上传静态附件", ok, f"attachment_id={att_id}")

    dyn_att = ch_map.get("动态附件")
    if dyn_att and dyn_att.get("id"):
        cid = dyn_att["id"]
        signup_html = (SIGNUP_DIR / "index.html").read_bytes()
        files = {"file": (f"signup_{TAG}.html", io.BytesIO(signup_html), "text/html")}
        r = admin.post(
            f"{BASE}/api/admin/challenges/games/{gid}/challenges/{cid}/attachments",
            files=files,
            timeout=15,
        )
        body = j(r)
        ok = r.status_code == 200 and body.get("code") == 200
        att_id = (body.get("data") or {}).get("attachment_id")
        record("上传 signup 动态附件", ok, f"attachment_id={att_id}")

    # --- 2. 用户报名 ---
    sessions = []
    for u in blood_users:
        s = login(u["email"], u["password"])
        r = s.post(f"{BASE}/api/competitions/{gid}/join", json={}, timeout=15)
        body = j(r)
        joined = r.status_code == 200 and body.get("code") == 200
        record(f"用户报名 {u['username']}", joined, body.get("msg", "")[:60])
        sessions.append((u, s))

    # Admin 也报名（用于容器测试）
    r = admin.post(f"{BASE}/api/competitions/{gid}/join", json={}, timeout=15)
    record("Admin 报名", r.status_code == 200, j(r).get("msg", "")[:60])

    # --- 3. 列表/详情 ---
    r = admin.get(f"{BASE}/api/challenges/games/{gid}/challenges", timeout=15)
    chs = (j(r).get("data") or [])
    record("题目列表", r.status_code == 200 and len(chs) >= 5, f"count={len(chs)}")

    # --- 4. 静态附件：下载 + 提交 ---
    if static_ch and static_ch.get("id"):
        cid = static_ch["id"]
        r = admin.get(f"{BASE}/api/challenges/{cid}", timeout=15)
        detail = (j(r).get("data") or {})
        att_id = detail.get("attachment_id")
        if att_id:
            r2 = admin.get(f"{BASE}/api/resources/{att_id}/content", timeout=15)
            record("下载静态附件", r2.status_code == 200, f"bytes={len(r2.content)}")
        r3 = admin.post(f"{BASE}/api/challenges/{cid}/submit", json={"flag": flags["static"]}, timeout=15)
        b3 = j(r3)
        correct = (b3.get("data") or {}).get("is_correct")
        record("提交静态附件 Flag", r3.status_code == 200 and correct, str(b3.get("msg", ""))[:50])

    # --- 5. 静态容器 ---
    static_ctr = ch_map.get("静态容器")
    if static_ctr and static_ctr.get("id"):
        cid = static_ctr["id"]
        r = admin.post(f"{BASE}/api/challenges/{cid}/start-container", timeout=90)
        if r.status_code >= 400:
            r = admin.post(f"{BASE}/api/container/start/{cid}", timeout=90)
        b = j(r)
        started = r.status_code == 200 and (b.get("code") == 200 or b.get("success"))
        inst = (b.get("data") or {})
        record("启动静态容器", started, f"port={inst.get('port')} url={str(inst.get('connection_url',''))[:40]}")

        r2 = admin.get(f"{BASE}/api/challenges/{cid}/container-status", timeout=15)
        st = (j(r2).get("data") or {}).get("status")
        record("容器状态查询", r2.status_code == 200, f"status={st}")

        r3 = admin.post(f"{BASE}/api/challenges/{cid}/submit", json={"answer": flags["static_container"]}, timeout=15)
        b3 = j(r3)
        record("提交静态容器 Flag", (b3.get("data") or {}).get("is_correct") is True, b3.get("msg", "")[:50])

    # --- 6. 动态容器 ---
    dyn_ctr = ch_map.get("动态容器")
    dynamic_flag = None
    if dyn_ctr and dyn_ctr.get("id"):
        cid = dyn_ctr["id"]
        r = admin.post(f"{BASE}/api/container/start/{cid}", timeout=90)
        b = j(r)
        inst_data = b.get("data") or {}
        iid = inst_data.get("instance_id") or inst_data.get("id")
        started = bool(iid) or r.status_code == 200
        record("启动动态容器(signup)", started, f"instance_id={iid}")

        if iid:
            r_dbg = admin.get(f"{BASE}/api/container/debug/{iid}", timeout=15)
            dbg = (j(r_dbg).get("data") or j(r_dbg))
            dynamic_flag = dbg.get("dynamic_flag") or (dbg.get("instance") or {}).get("dynamic_flag")
            record("读取 dynamic_flag", bool(dynamic_flag), (dynamic_flag or "")[:60])

        if dynamic_flag:
            r3 = admin.post(f"{BASE}/api/challenges/{cid}/submit", json={"flag": dynamic_flag}, timeout=15)
            b3 = j(r3)
            record("提交动态容器 Flag", (b3.get("data") or {}).get("is_correct") is True, b3.get("msg", "")[:50])

    # --- 7. 动态附件（signup 模板：下载个性化 HTML → 提取 flag → 提交）---
    if dyn_att and dyn_att.get("id"):
        cid = dyn_att["id"]
        r = admin.get(f"{BASE}/api/challenges/{cid}", timeout=15)
        att_id = (j(r).get("data") or {}).get("attachment_id")
        extracted_flag = None
        if att_id:
            r_dl = admin.get(f"{BASE}/api/resources/{att_id}/content", timeout=15)
            body_text = r_dl.text if r_dl.status_code == 200 else ""
            m = re.search(r"flag\{[^}]+\}", body_text)
            extracted_flag = m.group(0) if m else None
            has_placeholder = "flag{testflag}" in body_text
            record(
                "下载 signup 动态附件",
                r_dl.status_code == 200 and extracted_flag and not has_placeholder,
                f"flag={extracted_flag}",
            )
        if extracted_flag:
            r_sub = admin.post(f"{BASE}/api/challenges/{cid}/submit", json={"answer": extracted_flag}, timeout=15)
            b = j(r_sub)
            ok = (b.get("data") or {}).get("is_correct") is True
            record("提交动态附件 Flag", ok, b.get("msg", "")[:80])
        else:
            record("提交动态附件 Flag", False, "未能从附件提取 flag")

    # --- 8. 一二三血 ---
    blood_ch = ch_map.get("一二三血")
    blood_levels = []
    if blood_ch and blood_ch.get("id"):
        cid = blood_ch["id"]
        for idx, (u, s) in enumerate(sessions):
            r = s.post(f"{BASE}/api/challenges/{cid}/submit", json={"flag": flags["blood"]}, timeout=15)
            b = j(r)
            data = b.get("data") or {}
            level = data.get("blood_level")
            correct = data.get("is_correct")
            if correct and level is not None:
                blood_levels.append((u["username"], level))
            record(
                f"血榜提交 #{idx+1} {u['username']}",
                correct,
                f"blood_level={level} score={data.get('final_score') or data.get('points_earned')}",
            )
            time.sleep(0.3)

        with app.app_context():
            solves = CtfSolves.query.filter_by(challenge_id=cid).order_by(CtfSolves.blood_level).all()
            solve_info = [(s.blood_level, s.user_id, s.team_id) for s in solves]
            notices = CtfGameNotice.query.filter_by(game_id=gid).filter(CtfGameNotice.notice_type.in_([1, 2, 3])).all()
            record("一二三血记录", len(solves) >= 3, f"solves={solve_info}")
            record("血榜公告", len(notices) >= 3, f"notices={len(notices)}")

    # --- 9. 积分榜 ---
    r = admin.get(f"{BASE}/api/ctf/games/{gid}/scoreboard", timeout=15)
    sb = j(r)
    rankings = (sb.get("data") or {}).get("rankings") or sb.get("rankings") or []
    record("积分榜", r.status_code == 200 and len(rankings) > 0, f"teams={len(rankings)} top={rankings[0] if rankings else {}}")

    r2 = admin.get(f"{BASE}/api/ctf/games/{gid}/scoreboard/timeline", timeout=15)
    tl = j(r2)
    events = (tl.get("data") or {}).get("events") or tl.get("events") or []
    record("积分时间线", r2.status_code == 200, f"events={len(events)}")

    r3 = admin.get(f"{BASE}/api/ctf/games/{gid}/notices", timeout=15)
    notices = (j(r3).get("data") or [])
    record("赛事公告", r3.status_code == 200, f"count={len(notices)}")

    # --- 汇总 ---
    fails = [x for x in results if not x[1]]
    print(f"\n=== SUMMARY game_id={gid} PASS={len(results)-len(fails)} FAIL={len(fails)} ===")
    for name, ok, detail in results:
        if not ok:
            print(f"  FAIL {name}: {detail}")

    meta = {
        "game_id": gid,
        "tag": TAG,
        "blood_levels": blood_levels,
        "rankings": rankings[:5],
        "frontend_url": f"http://localhost:5174/games/{gid}",
    }
    print("\n--- META ---")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
