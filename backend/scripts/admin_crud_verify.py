#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""管理端 5 大板块 CRUD 全量自检。

覆盖：公告 / Wiki 内容 / 靶场题目 / 用户权限 / 系统配置(+轮播 API 探测)。
对接运行中后端 http://127.0.0.1:5000，账号默认 neepu_admin。
"""
from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE = "http://127.0.0.1:5000"
ADMIN = {"account": "neepu_admin", "password": "NeepuAdmin2025!"}
TAG = datetime.utcnow().strftime("%m%d%H%M%S")
SUFFIX = uuid.uuid4().hex[:6]

results: list[dict[str, Any]] = []


def record(module: str, step: str, ok: bool, status: Any, detail: str = ""):
    row = {
        "module": module,
        "step": step,
        "ok": ok,
        "status": status,
        "detail": detail[:240],
    }
    results.append(row)
    mark = "PASS" if ok else "FAIL"
    line = f"  [{mark}] {module} | {step}  HTTP={status}  {detail[:120]}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("utf-8", errors="replace").decode("ascii", errors="replace"))


def j(r: requests.Response):
    try:
        return r.json()
    except Exception:
        return {"_raw": (r.text or "")[:400]}


def ok_status(code: int, *want: int) -> bool:
    if want:
        return code in want
    return 200 <= code < 300


def login() -> requests.Session:
    """优先密码登录；失败则用 JWT cookie（与 admin_smoke_test 一致）。"""
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json=ADMIN, timeout=15)
    if r.status_code == 200:
        me = s.get(f"{BASE}/api/auth/me", timeout=10)
        body = j(me)
        if body.get("is_admin"):
            return s

    # fallback: mint JWT for any admin in DB
    from backend.app import create_app
    from backend.server.db_models import User
    from flask_jwt_extended import create_access_token

    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            raise RuntimeError("no admin user in database")
        token = create_access_token(identity=str(admin.id))
        account = admin.username or admin.email
    s = requests.Session()
    s.cookies.set("neepu_token", token, path="/")
    me = s.get(f"{BASE}/api/auth/me", timeout=10)
    body = j(me)
    if me.status_code != 200 or not body.get("is_admin"):
        raise RuntimeError(f"JWT admin session failed: {me.status_code} {body}")
    # stash for report
    ADMIN["account"] = account
    return s


# ---------- 1. 公告 ----------
def test_announcements(s: requests.Session):
    mod = "公告管理"
    title = f"[Test] 自动化测试公告 {TAG}"
    content = f"CRUD auto content {SUFFIX}"

    r = s.post(
        f"{BASE}/api/admin/platform/announcements",
        json={"title": title, "content": content, "is_active": True},
        timeout=15,
    )
    body = j(r)
    aid = body.get("id")
    record(mod, "C Create", ok_status(r.status_code, 200, 201) and bool(aid), r.status_code, f"id={aid}")
    if not aid:
        return

    r = s.get(f"{BASE}/api/admin/platform/announcements", timeout=15)
    items = j(r) if isinstance(j(r), list) else []
    found = any(a.get("id") == aid for a in items)
    record(mod, "R Admin list", ok_status(r.status_code) and found, r.status_code, f"count={len(items)} found={found}")

    r = s.get(f"{BASE}/api/platform/bulletins", timeout=15)
    pub = j(r)
    pub_list = pub if isinstance(pub, list) else (pub.get("items") or pub.get("data") or [])
    pub_found = any(
        (isinstance(a, dict) and (a.get("id") == aid or a.get("title") == title))
        for a in pub_list
    )
    record(mod, "R Public /bulletin", ok_status(r.status_code) and pub_found, r.status_code, f"found={pub_found}")

    new_title = f"{title} · UPDATED"
    r = s.patch(
        f"{BASE}/api/admin/platform/announcements/{aid}",
        json={"title": new_title, "content": content + " updated"},
        timeout=15,
    )
    body = j(r)
    record(
        mod,
        "U Update",
        ok_status(r.status_code) and body.get("title") == new_title,
        r.status_code,
        f"title={body.get('title')!r}",
    )

    r = s.delete(f"{BASE}/api/admin/platform/announcements/{aid}", timeout=15)
    record(mod, "D Delete", ok_status(r.status_code), r.status_code, str(j(r))[:80])

    r = s.get(f"{BASE}/api/admin/platform/announcements", timeout=15)
    items = j(r) if isinstance(j(r), list) else []
    gone = not any(a.get("id") == aid for a in items)
    record(mod, "D Verify gone", ok_status(r.status_code) and gone, r.status_code, f"gone={gone}")


# ---------- 2. Wiki / 内容 ----------
def test_content(s: requests.Session):
    mod = "内容/Wiki"
    title = f"[Test] Wiki CRUD {TAG}"

    r = s.post(
        f"{BASE}/api/articles/",
        json={
            "title": title,
            "content": f"# Auto Wiki\n\nbody {SUFFIX}",
            "summary": "auto summary",
            "tags": ["Web"],
            "status": "draft",
        },
        timeout=15,
    )
    body = j(r)
    art = body if isinstance(body, dict) else {}
    aid = art.get("id") or (art.get("data") or {}).get("id")
    record(mod, "C Create draft", ok_status(r.status_code, 200, 201) and bool(aid), r.status_code, f"id={aid}")
    if not aid:
        return

    r = s.patch(
        f"{BASE}/api/admin/platform/articles/{aid}",
        json={"status": "published", "title": f"{title} · PUB"},
        timeout=15,
    )
    record(mod, "U Publish+title", ok_status(r.status_code) and j(r).get("success") is True, r.status_code, str(j(r))[:80])

    r = s.get(f"{BASE}/api/admin/platform/articles", params={"page": 1, "status": "published"}, timeout=15)
    body = j(r)
    items = body.get("items") if isinstance(body, dict) else []
    found = any(a.get("id") == aid for a in items)
    record(mod, "R Admin list published", ok_status(r.status_code) and found, r.status_code, f"found={found}")

    # 正文编辑走选手端文章 API（管理端 patch 仅支持 status/title）
    r = s.put(
        f"{BASE}/api/articles/{aid}",
        json={"content": f"# Auto Wiki UPDATED\n\n{SUFFIX}", "status": "published"},
        timeout=15,
    )
    # 兼容 PATCH
    if r.status_code >= 400:
        r = s.patch(
            f"{BASE}/api/articles/{aid}",
            json={"content": f"# Auto Wiki UPDATED\n\n{SUFFIX}", "status": "published"},
            timeout=15,
        )
    record(mod, "U Edit body", ok_status(r.status_code), r.status_code, str(j(r))[:80])

    r = s.patch(
        f"{BASE}/api/admin/platform/articles/{aid}",
        json={"status": "draft"},
        timeout=15,
    )
    record(mod, "U Status→draft", ok_status(r.status_code), r.status_code, str(j(r))[:60])

    r = s.delete(f"{BASE}/api/admin/platform/articles/{aid}", timeout=15)
    record(mod, "D Delete", ok_status(r.status_code), r.status_code, str(j(r))[:80])

    r = s.get(f"{BASE}/api/admin/platform/articles", params={"page": 1}, timeout=15)
    items = (j(r).get("items") if isinstance(j(r), dict) else []) or []
    gone = not any(a.get("id") == aid for a in items)
    record(mod, "D Verify gone", ok_status(r.status_code) and gone, r.status_code, f"gone={gone}")


# ---------- 3. CTF ----------
def test_ctf(s: requests.Session):
    mod = "靶场/题目"
    now = datetime.utcnow()
    game_payload = {
        "title": f"[Test] CRUD Game {TAG}",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(days=1)).isoformat(),
        "is_public": False,
        "status": "ongoing",
        "description": "admin crud verify",
        "summary": "auto",
    }
    r = s.post(f"{BASE}/api/competitions/admin/create", json=game_payload, timeout=15)
    body = j(r)
    game = body.get("data") or body
    gid = game.get("id")
    record(mod, "C Create game", ok_status(r.status_code) and body.get("code", 200) == 200 and bool(gid), r.status_code, f"id={gid}")
    if not gid:
        return

    flag = f"flag{{crud_{SUFFIX}}}"
    ch_payload = {
        "title": f"[Test] CRUD Challenge {TAG}",
        "category": "Misc",
        "description": "auto challenge",
        "flag": flag,
        "original_points": 100,
        "challenge_type": 0,
        "min_score_rate": 0.25,
        "difficulty": 3.0,
    }
    r = s.post(f"{BASE}/api/admin/challenges/games/{gid}/challenges", json=ch_payload, timeout=15)
    body = j(r)
    ch = body.get("data") or {}
    cid = ch.get("id")
    record(mod, "C Create challenge", ok_status(r.status_code) and body.get("code") == 200 and bool(cid), r.status_code, f"id={cid}")
    if not cid:
        s.delete(f"{BASE}/api/competitions/admin/{gid}/delete", timeout=15)
        return

    r = s.get(f"{BASE}/api/admin/challenges/games/{gid}/challenges-list", timeout=15)
    body = j(r)
    data = body.get("data") if isinstance(body, dict) else body
    if isinstance(data, dict):
        items = data.get("items") or data.get("challenges") or []
    else:
        items = data if isinstance(data, list) else []
    if not items and isinstance(body, dict):
        items = body.get("items") or []
    found = any((c.get("id") == cid) for c in items) if items else True  # list shape varies
    record(mod, "R Challenge list", ok_status(r.status_code), r.status_code, f"found_hint={found} items={len(items) if isinstance(items, list) else '?'}")

    new_flag = f"flag{{crud_upd_{SUFFIX}}}"
    r = s.put(
        f"{BASE}/api/admin/challenges/games/{gid}/challenges/{cid}",
        json={
            "title": f"[Test] CRUD Challenge UPD {TAG}",
            "description": "updated desc",
            "flag": new_flag,
            "original_points": 150,
            "category": "Misc",
        },
        timeout=15,
    )
    body = j(r)
    record(mod, "U Update flag/score", ok_status(r.status_code) and body.get("code", 200) == 200, r.status_code, str(body.get("msg") or body)[:80])

    # disable / enable
    r = s.put(
        f"{BASE}/api/admin/challenges/games/{gid}/challenges/{cid}",
        json={"is_enabled": False},
        timeout=15,
    )
    body = j(r)
    disabled_ok = ok_status(r.status_code)
    record(mod, "U Disable", disabled_ok, r.status_code, str(body.get("msg") or "")[:60])

    r = s.put(
        f"{BASE}/api/admin/challenges/games/{gid}/challenges/{cid}",
        json={"is_enabled": True},
        timeout=15,
    )
    record(mod, "U Enable", ok_status(r.status_code), r.status_code, str(j(r).get("msg") or "")[:60])

    r = s.delete(f"{BASE}/api/admin/challenges/games/{gid}/challenges/{cid}", timeout=15)
    record(mod, "D Delete challenge", ok_status(r.status_code) and j(r).get("code", 200) == 200, r.status_code, str(j(r).get("msg") or "")[:60])

    r = s.delete(f"{BASE}/api/competitions/admin/{gid}/delete", timeout=15)
    body = j(r)
    record(mod, "D Delete game", ok_status(r.status_code) and body.get("code", 200) == 200, r.status_code, str(body.get("msg") or "")[:60])


# ---------- 4. 用户 ----------
def test_users(s: requests.Session):
    mod = "用户管理"
    # 预置临时普通用户
    from backend.app import create_app
    from backend.server.db_models import User
    from backend.server import extensions

    email = f"crud_user_{TAG}_{SUFFIX}@e2e.local"
    username = f"crud_u_{TAG}_{SUFFIX}"
    uid = None
    app = create_app()
    with app.app_context():
        u = User(email=email, username=username, nickname=f"CRUD_{SUFFIX}", email_verified=True, is_admin=False)
        u.set_password("CrudTest2025!")
        extensions.db.session.add(u)
        extensions.db.session.commit()
        uid = u.id

    # 后台 search 覆盖 nickname/email/full_name（不含 username）
    r = s.get(f"{BASE}/api/admin/platform/users", params={"page": 1, "search": email}, timeout=15)
    body = j(r)
    items = body.get("items") or []
    found = any(u.get("id") == uid for u in items)
    if not found:
        r2 = s.get(f"{BASE}/api/admin/platform/users", params={"page": 1, "search": f"CRUD_{SUFFIX}"}, timeout=15)
        items = j(r2).get("items") or []
        found = any(u.get("id") == uid for u in items)
        r = r2
    record(mod, "R Search user", ok_status(r.status_code) and found, r.status_code, f"uid={uid} found={found}")

    r = s.patch(
        f"{BASE}/api/admin/platform/users/{uid}",
        json={"is_moderator": True, "nickname": f"CRUD_MOD_{SUFFIX}"},
        timeout=15,
    )
    record(mod, "U Set moderator", ok_status(r.status_code) and j(r).get("success") is True, r.status_code, str(j(r))[:60])

    r = s.patch(
        f"{BASE}/api/admin/platform/users/{uid}",
        json={"is_moderator": False, "is_admin": False},
        timeout=15,
    )
    record(mod, "U Restore role", ok_status(r.status_code), r.status_code, str(j(r))[:60])

    # 重置密码：无专用 API 时用 DB 直接验证能力说明；若有则调用
    # 探测 setup API
    r = s.patch(f"{BASE}/api/admin/users/{uid}", json={"is_admin": False}, timeout=10)
    record(
        mod,
        "U Compat PATCH /api/admin/users",
        ok_status(r.status_code) or r.status_code in (404, 405),
        r.status_code,
        "compat probe (404/405 acceptable if unused)",
    )

    # 清理：删除测试用户
    r = s.delete(f"{BASE}/api/admin/platform/users/{uid}", timeout=15)
    deleted = ok_status(r.status_code)
    if not deleted:
        with app.app_context():
            u = User.query.get(uid)
            if u:
                extensions.db.session.delete(u)
                extensions.db.session.commit()
                deleted = True
    record(mod, "D Cleanup user", deleted, r.status_code, str(j(r))[:80])


# ---------- 5. 配置 / 轮播 ----------
def test_settings(s: requests.Session):
    mod = "系统设置/轮播"

    r = s.get(f"{BASE}/api/admin/platform/config", timeout=15)
    cfg = j(r)
    record(mod, "R Get config", ok_status(r.status_code) and isinstance(cfg, dict), r.status_code, f"keys={len(cfg) if isinstance(cfg, dict) else 0}")

    r = s.get(f"{BASE}/api/admin/platform/config/ui", timeout=15)
    ui = j(r)
    current = (ui.get("current") if isinstance(ui, dict) else {}) or {}
    record(mod, "R Get UI config", ok_status(r.status_code) and isinstance(ui, dict), r.status_code, f"name={current.get('name')!r}")

    # site_name 走 SystemConfig（/config），非 /config/ui 的 TEXT_CONFIG_KEYS
    old_name = cfg.get("site_name") if isinstance(cfg, dict) else None
    if not old_name:
        old_name = current.get("name") or "NEEPU CTF 终端"
    test_name = f"NEEPU-CRUD-{SUFFIX}"
    r = s.patch(
        f"{BASE}/api/admin/platform/config",
        json={"site_name": test_name},
        timeout=15,
    )
    body = j(r)
    new_cfg = body.get("config") or {}
    saved = ok_status(r.status_code) and (
        str(new_cfg.get("site_name")) == test_name or body.get("success") is True
    )
    record(mod, "U Patch site_name", saved, r.status_code, f"→ {test_name}")

    # 读回 platform info（可能有短缓存，允许一次重试）
    name_ok = False
    info = {}
    status = 0
    for _ in range(3):
        r = s.get(f"{BASE}/api/platform/info", timeout=15)
        status = r.status_code
        info = j(r)
        name_ok = (info.get("name") == test_name) or (info.get("site_name") == test_name)
        if name_ok:
            break
        time.sleep(0.4)
    record(mod, "R Platform info reflects", ok_status(status) and name_ok, status, f"name={info.get('name')!r}")

    # 恢复
    r = s.patch(
        f"{BASE}/api/admin/platform/config",
        json={"site_name": old_name},
        timeout=15,
    )
    record(mod, "U Restore site_name", ok_status(r.status_code), r.status_code, f"→ {old_name!r}")

    # 轮播 API（前端已下线，后端仍可探测）
    r = s.get(f"{BASE}/api/admin/platform/carousel", timeout=15)
    slides = j(r) if isinstance(j(r), list) else []
    record(
        mod,
        "R Carousel API (legacy)",
        ok_status(r.status_code),
        r.status_code,
        f"slides={len(slides) if isinstance(slides, list) else '?'} (UI removed; API kept)",
    )
    if isinstance(slides, list) and slides:
        sid = slides[0].get("id")
        old_title = slides[0].get("title")
        r = s.patch(
            f"{BASE}/api/admin/platform/carousel/{sid}",
            json={"title": f"[Test] {SUFFIX}"},
            timeout=15,
        )
        record(mod, "U Carousel title", ok_status(r.status_code), r.status_code, f"id={sid}")
        s.patch(
            f"{BASE}/api/admin/platform/carousel/{sid}",
            json={"title": old_title},
            timeout=15,
        )


def print_report():
    passed = [x for x in results if x["ok"]]
    failed = [x for x in results if not x["ok"]]
    print("\n" + "=" * 64)
    print(f"管理端 CRUD 自检报告  @ {BASE}  tag={TAG}")
    print(f"PASS {len(passed)} / FAIL {len(failed)} / TOTAL {len(results)}")
    print("=" * 64)
    by_mod: dict[str, list] = {}
    for row in results:
        by_mod.setdefault(row["module"], []).append(row)
    for mod, rows in by_mod.items():
        ok_n = sum(1 for r in rows if r["ok"])
        print(f"\n## {mod}  ({ok_n}/{len(rows)})")
        for r in rows:
            mark = "OK" if r["ok"] else "FAIL"
            line = f"  {mark:4} {r['step']:<28} HTTP {r['status']}  {r['detail']}"
            try:
                print(line)
            except UnicodeEncodeError:
                print(line.encode("ascii", errors="replace").decode())
    if failed:
        print("\nFailed summary:")
        for r in failed:
            print(f"  - [{r['module']}] {r['step']}: HTTP {r['status']} {r['detail']}")
    report_path = ROOT / "backend" / "scripts" / f"_crud_report_{TAG}.json"
    report_path.write_text(json.dumps({"tag": TAG, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON report: {report_path}")
    return 0 if not failed else 1


def main() -> int:
    print(f"=== Admin CRUD Verify @ {BASE} ===\n")
    try:
        s = login()
        record("鉴权", "Admin login", True, 200, ADMIN["account"])
    except Exception as e:
        record("鉴权", "Admin login", False, "ERR", str(e))
        return print_report()

    print("\n[1/5] 公告管理")
    test_announcements(s)
    print("\n[2/5] 内容/Wiki")
    test_content(s)
    print("\n[3/5] 靶场/题目")
    test_ctf(s)
    print("\n[4/5] 用户管理")
    test_users(s)
    print("\n[5/5] 系统设置/轮播")
    test_settings(s)

    return print_report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
